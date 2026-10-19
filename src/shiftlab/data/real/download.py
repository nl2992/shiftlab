"""Resumable bounded HTTP downloads; never silently overwrite an established payload."""

import json
import os
import re
import time
from pathlib import Path

import requests

from ..provenance import sha256, utc_now, write_json


def download(
    url: str,
    destination: Path,
    expected_sha256: str | None = None,
    max_bytes: int = 250_000_000,
    retries: int = 3,
) -> Path:
    if max_bytes <= 0 or retries < 1:
        raise ValueError("Require positive byte budget and at least one attempt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = destination.with_suffix(destination.suffix + ".receipt.json")
    if destination.exists():
        if not receipt.exists():
            raise ValueError(
                "Existing payload has no receipt; import explicitly rather than overwrite"
            )
        prior = json.loads(receipt.read_text())
        if prior["url"] != url or sha256(destination) != prior["sha256"]:
            raise ValueError("Existing raw version differs or is corrupt")
        if expected_sha256 and prior["sha256"].lower() != expected_sha256.lower():
            raise ValueError("Checksum mismatch")
        return destination
    partial = destination.with_suffix(destination.suffix + ".part")
    resume_receipt = partial.with_suffix(partial.suffix + ".json")
    for attempt in range(retries):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            prior_resume = json.loads(resume_receipt.read_text()) if resume_receipt.exists() else {}
            etag = prior_resume.get("etag") if prior_resume.get("url") == url else None
            # Without a strong source validator (or a final publisher digest), old
            # partial bytes cannot safely be combined with a new response.
            if offset and not (etag or expected_sha256):
                offset = 0
            if offset > max_bytes:
                raise ValueError("Partial download exceeds configured byte budget")
            headers = {"Accept-Encoding": "identity"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
                if etag:
                    headers["If-Range"] = etag
            with requests.get(url, headers=headers, stream=True, timeout=(15, 90)) as response:
                response.raise_for_status()
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise ValueError("Encoded response prevents safe byte-range accounting")
                resume = offset > 0 and response.status_code == 206
                source_etag = response.headers.get("ETag")
                strong_etag = (
                    source_etag if source_etag and not source_etag.startswith("W/") else None
                )
                total = None
                if response.status_code == 206:
                    match = re.fullmatch(
                        r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", "")
                    )
                    if not resume or not match:
                        raise ValueError("Unexpected or invalid Content-Range")
                    first, last, total = map(int, match.groups())
                    if first != offset or last != total - 1 or last < first:
                        raise ValueError("Incomplete or inconsistent Content-Range")
                    if etag and strong_etag != etag:
                        raise ValueError("Source validator changed during resumed download")
                if not resume:
                    offset = 0
                length = response.headers.get("Content-Length")
                expected_length = int(length) if length is not None else None
                if expected_length is not None:
                    if expected_length < 0:
                        raise ValueError("Invalid Content-Length")
                    if total is not None and offset + expected_length != total:
                        raise ValueError("Content-Length disagrees with Content-Range")
                    total = offset + expected_length
                if total is not None and total > max_bytes:
                    raise ValueError(
                        f"Download exceeds {max_bytes} bytes; increase explicit budget"
                    )
                write_json(resume_receipt, {"url": url, "etag": strong_etag})
                with partial.open("ab" if resume else "wb") as handle:
                    count = offset
                    for block in response.iter_content(1024 * 1024):
                        count += len(block)
                        if count > max_bytes:
                            raise ValueError(
                                f"Download exceeds {max_bytes} bytes; increase explicit budget"
                            )
                        handle.write(block)
                if total is not None and count != total:
                    raise requests.RequestException("Truncated source response")
            digest = sha256(partial)
            if expected_sha256 and digest.lower() != expected_sha256.lower():
                partial.unlink()
                raise ValueError("Checksum mismatch")
            os.replace(partial, destination)
            write_json(
                receipt,
                {
                    "url": url,
                    "sha256": digest,
                    "downloaded_at": utc_now(),
                    "bytes": count,
                    "publisher_checksum_verified": expected_sha256 is not None,
                    "etag": strong_etag,
                    "last_modified": response.headers.get("Last-Modified"),
                },
            )
            resume_receipt.unlink(missing_ok=True)
            return destination
        except (requests.RequestException, OSError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(2**attempt, 4))
    raise RuntimeError("Unreachable download state")
