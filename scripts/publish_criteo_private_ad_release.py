"""Upload the verified CriteoPrivateAd snapshot to a private GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_one(tag: str, repo: str, path: Path) -> None:
    subprocess.run(
        ["gh", "release", "upload", tag, str(path.resolve()), "--repo", repo],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw/criteo_privatead"))
    parser.add_argument("--repo", default="nl2992/shiftlab")
    parser.add_argument("--tag", default="data-2026-10-22")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 12:
        parser.error("--workers must be from 1 to 12")

    manifest_path = args.root / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset") != "criteo/CriteoPrivateAd":
        raise ValueError("Unexpected source manifest dataset")
    files = manifest["files"]
    names = [Path(item["local_path"]).name for item in files]
    if len(set(names)) != len(names):
        raise ValueError("Release assets would have colliding basenames")
    assets = {}
    for item in files:
        path = args.root / item["local_path"]
        if not item.get("verified") or not path.is_file():
            raise ValueError(f"Missing or unverified file: {item['local_path']}")
        if path.stat().st_size != item["size"]:
            raise ValueError(f"Size changed after verification: {item['local_path']}")
        if sha256(path) != item["sha256"]:
            raise ValueError(f"Checksum changed after acquisition: {item['local_path']}")
        assets[path.name] = (path, item["size"], item["sha256"])
    manifest_hash = sha256(manifest_path)
    assets[manifest_path.name] = (manifest_path, manifest_path.stat().st_size, manifest_hash)

    existing_result = subprocess.run(
        ["gh", "release", "view", args.tag, "--repo", args.repo, "--json", "assets"],
        check=True,
        capture_output=True,
        text=True,
    )
    existing = {item["name"]: item for item in json.loads(existing_result.stdout)["assets"]}
    pending = []
    for name, (path, size, digest) in assets.items():
        remote = existing.get(name)
        if remote is None:
            pending.append(path)
            continue
        if remote.get("state") != "uploaded":
            subprocess.run(
                ["gh", "release", "delete-asset", args.tag, name, "--repo", args.repo, "--yes"],
                check=True,
            )
            pending.append(path)
            continue
        remote_digest = (remote.get("digest") or "").removeprefix("sha256:")
        if remote.get("size") != size or remote_digest != digest:
            raise ValueError(
                f"A different release asset already exists as {name}; refusing overwrite"
            )
    if not pending:
        print("All CriteoPrivateAd files and manifest already match the private release.")
        return

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(upload_one, args.tag, args.repo, path) for path in pending]
        for index, future in enumerate(as_completed(futures), start=1):
            future.result()
            if index % 8 == 0 or index == len(futures):
                print(f"Uploaded {index}/{len(pending)} pending release assets", flush=True)


if __name__ == "__main__":
    main()
