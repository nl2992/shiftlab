"""Download and verify the complete pinned CriteoPrivateAd Hugging Face snapshot.

The source is large (approximately 31.7 GiB). Files remain under the ignored
data/raw tree; the script writes a checksum inventory for cross-device access.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import pyarrow.parquet as pq
import requests

from shiftlab.data.provenance import write_json
from shiftlab.data.real.download import download

REPOSITORY = "criteo/CriteoPrivateAd"
REVISION = "343645889b157f104ac23d0d07afa6a18115eb30"
DATASET_URL = f"https://huggingface.co/datasets/{REPOSITORY}"
API_URL = f"https://huggingface.co/api/datasets/{REPOSITORY}/tree/{REVISION}"
EXPECTED_LICENSE = "cc-by-sa-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
PAPER_URL = "https://arxiv.org/abs/2502.12103"
REQUIRED_COLUMNS = {
    "id",
    "user_id",
    "display_order",
    "sale_delay_after_display_array",
    "click_delay_after_display_array",
    "landed_click_delay_after_display_array",
    "is_visit",
    "nb_sales",
    "is_clicked",
    "is_click_landed",
    "publisher_id",
}


def list_files() -> list[dict]:
    """Return the revision-pinned data file metadata from the Hub tree API."""
    url = f"{API_URL}?recursive=true&expand=true&limit=100"
    files: list[dict] = []
    while url:
        response = requests.get(url, timeout=(15, 90))
        response.raise_for_status()
        for item in response.json():
            if item.get("type") != "file" or not item.get("path", "").startswith("data/"):
                continue
            lfs = item.get("lfs") or {}
            digest = lfs.get("oid")
            size = int(lfs.get("size", item.get("size", 0)))
            if not digest or len(digest) != 64 or size < 1:
                raise ValueError(f"Missing SHA-256/size metadata for {item.get('path')!r}")
            files.append({"path": item["path"], "size": size, "sha256": digest})
        url = response.links.get("next", {}).get("url")
    if not files:
        raise ValueError("Pinned dataset revision contains no data files")
    return sorted(files, key=lambda item: item["path"])


def check_repository_metadata() -> dict:
    response = requests.get(
        f"https://huggingface.co/api/datasets/{REPOSITORY}/revision/{REVISION}", timeout=30
    )
    response.raise_for_status()
    info = response.json()
    card = info.get("cardData") or {}
    if info.get("sha") != REVISION:
        raise ValueError(f"Pinned revision mismatch: expected {REVISION}, got {info.get('sha')}")
    if card.get("license") != EXPECTED_LICENSE:
        raise ValueError(f"Unexpected dataset license metadata: {card.get('license')!r}")
    return {"revision": info["sha"], "license": card["license"]}


def fetch_one(item: dict, root: Path, max_file_bytes: int) -> dict:
    relative = Path(item["path"])
    destination = root / relative
    if item["size"] > max_file_bytes:
        raise ValueError(
            f"{item['path']} is {item['size']} bytes, above --max-file-bytes={max_file_bytes}"
        )
    url = f"{DATASET_URL}/resolve/{REVISION}/{quote(item['path'], safe='/')}?download=true"
    download(url, destination, expected_sha256=item["sha256"], max_bytes=max_file_bytes)
    if destination.stat().st_size != item["size"]:
        raise ValueError(f"Downloaded size mismatch for {item['path']}")
    return {**item, "local_path": str(relative), "verified": True}


def inspect_parquet(files: list[dict], root: Path) -> dict:
    """Verify partition layout and Parquet metadata without reading row values."""
    rows_by_day: dict[str, int] = {}
    schemas: set[bytes] = set()
    total_rows = 0
    empty_files = 0
    for item in files:
        path = root / item["local_path"]
        parquet = pq.ParquetFile(path)
        schema = parquet.schema_arrow
        missing = REQUIRED_COLUMNS - set(schema.names)
        if missing:
            raise ValueError(f"{path.name} lacks required columns: {sorted(missing)}")
        schemas.add(schema.serialize().to_pybytes())
        count = parquet.metadata.num_rows
        total_rows += count
        empty_files += int(count == 0)
        parts = Path(item["local_path"]).parts
        if len(parts) < 3 or not parts[1].startswith("day_int="):
            raise ValueError(f"Unexpected day partition path: {item['local_path']}")
        day = parts[1].split("=", 1)[1]
        rows_by_day[day] = rows_by_day.get(day, 0) + count
    if set(rows_by_day) != {str(day) for day in range(1, 31)}:
        raise ValueError("CriteoPrivateAd snapshot must contain all 30 day partitions")
    if len(schemas) != 1 or total_rows <= 0 or any(count <= 0 for count in rows_by_day.values()):
        raise ValueError("Parquet schema or day partition row-count validation failed")
    return {
        "row_count": total_rows,
        "empty_parquet_files": empty_files,
        "day_partition_count": len(rows_by_day),
        "rows_by_day_int": {key: rows_by_day[key] for key in sorted(rows_by_day, key=int)},
        "schema_count": len(schemas),
        "required_event_and_identity_columns": sorted(REQUIRED_COLUMNS),
        "verification": "Parquet metadata only; no record values read",
    }


def acquire(root: Path, *, workers: int, max_total_bytes: int, max_file_bytes: int) -> dict:
    if workers < 1 or max_total_bytes < 1 or max_file_bytes < 1:
        raise ValueError("Worker and byte limits must be positive")
    metadata = check_repository_metadata()
    files = list_files()
    total_bytes = sum(item["size"] for item in files)
    if total_bytes > max_total_bytes:
        raise ValueError(
            f"Complete source requires {total_bytes} bytes, above --max-total-bytes={max_total_bytes}"
        )
    if any(item["size"] > max_file_bytes for item in files):
        raise ValueError("At least one file exceeds --max-file-bytes")

    root.mkdir(parents=True, exist_ok=True)
    completed: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_one, item, root, max_file_bytes) for item in files]
        for index, future in enumerate(as_completed(futures), start=1):
            completed.append(future.result())
            if index % 10 == 0 or index == len(futures):
                fetched = sum(item["size"] for item in completed)
                print(
                    f"verified {index}/{len(futures)} files; {fetched:,}/{total_bytes:,} bytes",
                    flush=True,
                )

    completed.sort(key=lambda item: item["path"])
    parquet_validation = inspect_parquet(completed, root)
    report = {
        "dataset": REPOSITORY,
        "source_url": DATASET_URL,
        "license_url": LICENSE_URL,
        "citation": "Sebbar et al. (2025), CriteoPrivateAds: A Real-World Bidding Dataset to Design Private Advertising Systems, arXiv:2502.12103.",
        "paper_url": PAPER_URL,
        "revision": metadata["revision"],
        "license": metadata["license"],
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "file_count": len(completed),
        "total_bytes": total_bytes,
        "total_gib": round(total_bytes / (1024**3), 3),
        "verified_files": len(completed),
        "parquet_validation": parquet_validation,
        "files": completed,
        "notes": [
            "File bytes are checked against the Hugging Face Git LFS SHA-256 and size metadata.",
            "Criteo documents 100M impressions over 30 days and click/sale event delays in minutes.",
            "This is a CriteoPrivateAd source, distinct from the unavailable 90-day Sponsored Search archive.",
        ],
    }
    write_json(root / "source_manifest.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw/criteo_privatead"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-total-bytes", type=int, default=40_000_000_000)
    parser.add_argument("--max-file-bytes", type=int, default=1_500_000_000)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    metadata = check_repository_metadata()
    files = list_files()
    total_bytes = sum(item["size"] for item in files)
    if args.plan_only:
        print(
            json.dumps(
                {
                    "dataset": REPOSITORY,
                    "revision": metadata["revision"],
                    "license": metadata["license"],
                    "files": len(files),
                    "bytes": total_bytes,
                    "gib": round(total_bytes / (1024**3), 3),
                    "days": len({item["path"].split("/", 2)[1] for item in files}),
                },
                indent=2,
            )
        )
        return
    result = acquire(
        args.root,
        workers=args.workers,
        max_total_bytes=args.max_total_bytes,
        max_file_bytes=args.max_file_bytes,
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("dataset", "revision", "file_count", "total_bytes", "verified_files")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
