"""Bounded credentialed JSON acquisition. Secret-bearing URLs and echoes never enter artifacts."""

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

import requests

from ..provenance import sha256, utc_now, write_json


def required_key(variable: str) -> str:
    key = os.environ.get(variable)
    if not key:
        raise RuntimeError(
            f"Set {variable} in your local environment; do not place API keys in YAML or Git"
        )
    return key


def reject_secrets(config):
    if isinstance(config, dict):
        for key, value in config.items():
            if key.lower() in ["api_key", "apikey", "authorization", "token", "password"]:
                raise ValueError("Credentials belong in environment variables, not configuration")
            reject_secrets(value)
    elif isinstance(config, list):
        for value in config:
            reject_secrets(value)


def scrub(value, secret):
    if isinstance(value, dict):
        return {
            k: (
                "[REDACTED]"
                if k.lower() in ["api_key", "apikey", "authorization", "token"]
                else scrub(v, secret)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [scrub(v, secret) for v in value]
    return value.replace(secret, "[REDACTED]") if isinstance(value, str) and secret else value


def snapshot_pages(
    endpoint: str,
    public_params: dict,
    key: str,
    destination: Path,
    rows_key: tuple[str, ...],
    total_key: tuple[str, ...],
    *,
    page_size=5000,
    max_records=20000,
    refresh=False,
    retries=3,
):
    """Return a verified, reusable immutable sanitized response snapshot with complete pagination.

    Responses can echo credentials. We checksum publisher bytes but persist only scrubbed JSON;
    receipt explicitly distinguishes original-response and stored-file hashes. No URL with the
    key is recorded or propagated through network exception messages.
    """
    identity = hashlib.sha256(
        json.dumps({"url": endpoint, "params": public_params}, sort_keys=True).encode()
    ).hexdigest()[:20]
    query_root = destination / identity
    cached = sorted(query_root.glob("*/receipt.json"))
    if cached and not refresh:
        receipt = json.loads(cached[-1].read_text())
        pages = []
        for name, digest in receipt["files"].items():
            path = cached[-1].parent / name
            if sha256(path) != digest:
                raise ValueError("Cached API snapshot checksum mismatch")
            pages.append(path)
        return pages, cached[-1]
    version = query_root / (utc_now().replace(":", "-") + "-" + uuid.uuid4().hex[:8])
    version.mkdir(parents=True)
    offset, total, pages, original_hashes = 0, None, [], {}
    while total is None or offset < total:
        params = {
            **public_params,
            "api_key": key,
            "offset": offset,
            "length": page_size,
            "limit": page_size,
        }
        # API-specific lengths: EIA uses length, FRED uses limit.
        params.pop("limit" if "eia.gov" in endpoint else "length")
        payload = None
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, params=params, timeout=(15, 90))
                if response.status_code in [429, 500, 502, 503, 504] and attempt + 1 < retries:
                    time.sleep(min(2**attempt, 4))
                    continue
                if not response.ok:
                    raise RuntimeError(
                        f"API acquisition failed with HTTP {response.status_code}: {endpoint} (credential-bearing URL withheld)"
                    )
                original = hashlib.sha256(response.content).hexdigest()
                payload = scrub(response.json(), key)
                break
            except requests.RequestException:
                if attempt + 1 == retries:
                    raise RuntimeError(
                        f"API acquisition could not reach {endpoint}; credentials withheld"
                    ) from None
                time.sleep(min(2**attempt, 4))
        if payload is None:
            raise RuntimeError("API returned no payload after retries")
        rows = payload
        for key_part in rows_key:
            rows = rows[key_part]
        count = payload
        for key_part in total_key:
            count = count[key_part]
        if not isinstance(rows, list):
            raise TypeError("Expected a list of observations")
        if total is None:
            total = int(count)
            if total > max_records:
                raise ValueError(
                    f"API query has {total} rows, exceeding max_records={max_records}; narrow the date/domain selection"
                )
        elif int(count) != total:
            raise ValueError(
                "API row count changed during pagination; narrow query and retry with a new snapshot"
            )
        if not rows and offset < total:
            raise ValueError("Truncated API pagination")
        if len(rows) > page_size or offset + len(rows) > max_records:
            raise ValueError("API page exceeds requested bounds")
        path = version / f"page-{offset:08d}.json"
        write_json(path, payload)
        pages.append(path)
        original_hashes[path.name] = original
        offset += len(rows)
        if total == 0:
            break
    receipt = version / "receipt.json"
    write_json(
        receipt,
        {
            "url": endpoint,
            "parameters": public_params,
            "retrieved_at": utc_now(),
            "rows": offset,
            "files": {path.name: sha256(path) for path in pages},
            "original_response_sha256": original_hashes,
            "stored_payload": "credential-scrubbed JSON; publisher bytes not retained",
        },
    )
    return pages, receipt
