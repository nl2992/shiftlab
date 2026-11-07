"""Acquire and checksum EIA-930 six-month files; does not read or score outcomes."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data/raw/eia930_f8_2026_confirmation_20261107"
BASE = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles"
PERIODS = (
    "2024_Jan_Jun",
    "2024_Jul_Dec",
    "2025_Jan_Jun",
    "2025_Jul_Dec",
    "2026_Jan_Jun",
    "2026_Jul_Dec",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for period in PERIODS:
        name = f"EIA930_BALANCE_{period}.csv"
        path = OUT / name
        request = urllib.request.Request(
            f"{BASE}/{name}", headers={"User-Agent": "ShiftLab-research/1.0"}
        )
        with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as out:
            while chunk := response.read(1 << 20):
                out.write(chunk)
            headers = dict(response.headers.items())
        files.append(
            {
                "url": f"{BASE}/{name}",
                "file": name,
                "bytes": path.stat().st_size,
                "sha256": digest(path),
                "last_modified": headers.get("Last-Modified"),
                "etag": headers.get("ETag"),
            }
        )
    manifest = {
        "source": "official EIA-930 six-month balance files",
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "files": files,
        "inspection_scope": "download and checksum only; no row values or outcomes read",
    }
    (OUT / "source_receipt.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
