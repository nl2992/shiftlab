"""Restore flat CriteoPrivateAd GitHub release assets to their source layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from shiftlab.data.provenance import write_json

REPOSITORY = "criteo/CriteoPrivateAd"
DATASET_URL = f"https://huggingface.co/datasets/{REPOSITORY}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inbox", type=Path, required=True, help="Flat directory downloaded from release"
    )
    parser.add_argument("--root", type=Path, default=Path("data/raw/criteo_privatead"))
    args = parser.parse_args()
    manifest = json.loads((args.inbox / "source_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("dataset") != "criteo/CriteoPrivateAd":
        raise ValueError("Unexpected source manifest dataset")
    if len({Path(item["local_path"]).name for item in manifest["files"]}) != len(manifest["files"]):
        raise ValueError("Manifest contains colliding release asset basenames")

    for index, item in enumerate(manifest["files"], start=1):
        source = args.inbox / Path(item["local_path"]).name
        if not source.is_file() or source.stat().st_size != item["size"]:
            raise ValueError(f"Missing or wrong-sized release asset: {source.name}")
        if sha256(source) != item["sha256"]:
            raise ValueError(f"Checksum mismatch for release asset: {source.name}")
        destination = args.root / item["local_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)
        url = f"{DATASET_URL}/resolve/{manifest['revision']}/{quote(item['path'], safe='/')}?download=true"
        write_json(
            destination.with_suffix(destination.suffix + ".receipt.json"),
            {
                "url": url,
                "sha256": item["sha256"],
                "downloaded_at": datetime.now(UTC).isoformat(),
                "bytes": item["size"],
                "publisher_checksum_verified": True,
                "etag": None,
                "last_modified": None,
            },
        )
        if index % 20 == 0 or index == len(manifest["files"]):
            print(f"Restored {index}/{len(manifest['files'])} files", flush=True)

    (args.root / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
