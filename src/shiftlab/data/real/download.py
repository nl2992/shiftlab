"""Resumable bounded HTTP downloads; never silently overwrite an established payload."""

import os
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = destination.with_suffix(destination.suffix + ".receipt.json")
    if destination.exists():
        import json

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
    for attempt in range(retries):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            with requests.get(url, headers=headers, stream=True, timeout=(15, 90)) as response:
                response.raise_for_status()
                resume = offset > 0 and response.status_code == 206
                if resume and not response.headers.get("Content-Range", "").startswith(
                    f"bytes {offset}-"
                ):
                    raise ValueError("Invalid Content-Range")
                if not resume:
                    offset = 0
                with partial.open("ab" if resume else "wb") as handle:
                    count = offset
                    for block in response.iter_content(1024 * 1024):
                        count += len(block)
                        if count > max_bytes:
                            raise ValueError(
                                f"Download exceeds {max_bytes} bytes; increase explicit budget"
                            )
                        handle.write(block)
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
                },
            )
            return destination
        except (requests.RequestException, OSError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(2**attempt, 4))
    raise RuntimeError("Unreachable download state")
