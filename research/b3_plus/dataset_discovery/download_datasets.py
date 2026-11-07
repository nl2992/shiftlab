"""Download candidate datasets into ``_raw/<dataset_id>/`` and record sha256 in the registry.

Raw data never enters Git (``_raw/.gitignore`` is ``*``). river datasets download on demand into
``$RIVER_DATA``; OpenML datasets by id through ``sklearn.datasets.fetch_openml``. Large downloads
(> ``--max-mb``, default 1500) are refused unless ``--allow-large``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dataset_sources as ds  # noqa: E402
import registry as reg  # noqa: E402


def ensure_gitignore() -> None:
    g = ds.RAW / ".gitignore"
    ds.RAW.mkdir(parents=True, exist_ok=True)
    if not g.exists():
        g.write_text("*\n!.gitignore\n", encoding="utf-8")


def download_one(dataset_id: str, registry: dict | None = None, reg_path=reg.REGISTRY_PATH,
                 max_mb: int = 1500, allow_large: bool = False) -> dict:
    ensure_gitignore()
    registry = registry if registry is not None else reg.load(reg_path)
    entry = reg.get(registry, dataset_id)
    if entry["status"] == "NOT_RUN":
        raise SystemExit(f"{dataset_id} is NOT_RUN: {entry['status_reason']}")
    d = ds.raw_dir(dataset_id)
    if dataset_id in ds.RIVER_CLASSES:
        size = ds.river_declared_size(dataset_id)
        entry["declared_download_bytes"] = size
        if size and size > max_mb * 1_000_000 and not allow_large:
            raise SystemExit(f"{dataset_id}: {size / 1e6:.0f} MB exceeds --max-mb {max_mb}")
        ds.download_river(dataset_id)
    elif dataset_id in ds.DIRECT:
        ds.download_direct(dataset_id)
    elif entry.get("openml_did"):
        ds.download_openml(dataset_id, entry["openml_did"])
    else:
        raise SystemExit(f"{dataset_id}: no download route")
    entry["files"] = ds.hash_dir(d)
    if not entry["files"]:  # file ships inside the river package (e.g. Phishing)
        pth = ds.download_river(dataset_id)
        entry["files"] = {f"river-package:{pth.name}": {"bytes": pth.stat().st_size,
                                                        "sha256": ds.sha256_file(pth)}}
    reg.stamp(entry, "downloaded_at_utc")
    if reg_path is not None:
        reg.save(registry, reg_path)
    return entry["files"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset_ids", nargs="+")
    ap.add_argument("--max-mb", type=int, default=1500)
    ap.add_argument("--allow-large", action="store_true")
    a = ap.parse_args(argv)
    for did in a.dataset_ids:
        files = download_one(did, max_mb=a.max_mb, allow_large=a.allow_large)
        for k, v in files.items():
            print(f"{did}: {k} {v['bytes']} bytes sha256={v['sha256']}")


if __name__ == "__main__":
    main()
