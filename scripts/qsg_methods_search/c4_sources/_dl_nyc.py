"""Shared streaming downloader for the NYC Open Data modules (idempotent, writes a receipt)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import requests


def download(url: str, params: dict, out: Path) -> None:
    if out.exists():
        return
    h = hashlib.sha256()
    n = 0
    tmp = out.with_suffix(out.suffix + ".part")
    with requests.get(url, params=params, timeout=1200, stream=True) as r:
        r.raise_for_status()
        final = r.url
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                h.update(chunk)
                n += len(chunk)
    tmp.replace(out)
    (out.parent / f"{out.name}.receipt.json").write_text(
        json.dumps(
            {
                "url": final,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": n,
                "sha256": h.hexdigest(),
            },
            indent=1,
        )
    )
