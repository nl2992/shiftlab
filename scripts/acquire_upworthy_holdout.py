"""Acquire only the frozen Upworthy holdout file from the official OSF node."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

import requests

ROOT = Path(__file__).resolve().parents[1]
OSF_FILE_API = "https://api.osf.io/v2/files/608ff68c5533b4028ee21eb8/"
EXPECTED_NAME = "upworthy-archive-holdout-packages-03.12.2020.csv"
EXPECTED_SIZE = 14_174_776
EXPECTED_SHA256 = "93832660b831aca16bbe314c60dba4a6815b0a5f9cdded1217671cfbfa5186ea"
TARGET = ROOT / "data/raw/upworthy" / EXPECTED_NAME
MANIFEST = ROOT / "data/reports/upworthy_holdout_acquisition_manifest.json"
PROTOCOL = ROOT / "papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md"
RUNNER = ROOT / "scripts/evaluate_upworthy_policy.py"
IMPLEMENTATION = ROOT / "src/shiftlab/dive/upworthy_policy_selection.py"
PROTOCOL_SHA256 = "a8b6bb74a627674b9b007023bea562991eff78d3a5fa017931e73a146b82715f"
RUNNER_SHA256 = "825c86069c26db326a623234e475d1c3f4548506e328344317d973ec09771a50"
IMPLEMENTATION_SHA256 = "f5004163bb7eed139d943c2e4167215f177a71be8d6ef98f475bfb00edb2fb62"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acquire() -> dict[str, object]:
    if TARGET.exists() or MANIFEST.exists():
        raise FileExistsError("Holdout file or manifest already exists; refusing overwrite")
    if sha256(PROTOCOL) != PROTOCOL_SHA256:
        raise ValueError("Frozen holdout protocol has changed")
    if sha256(RUNNER) != RUNNER_SHA256 or sha256(IMPLEMENTATION) != IMPLEMENTATION_SHA256:
        raise ValueError("Frozen evaluation runner or policy implementation has changed")
    response = requests.get(
        OSF_FILE_API, headers={"Accept": "application/vnd.api+json"}, timeout=30
    )
    response.raise_for_status()
    data = response.json()["data"]
    attrs = data["attributes"]
    actual_hash = attrs["extra"]["hashes"]["sha256"]
    if (
        attrs["name"] != EXPECTED_NAME
        or int(attrs["size"]) != EXPECTED_SIZE
        or actual_hash != EXPECTED_SHA256
    ):
        raise ValueError("Official OSF holdout file metadata differs from the frozen protocol")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    partial = TARGET.with_suffix(TARGET.suffix + ".partial")
    digest = hashlib.sha256()
    total = 0
    with urlopen(data["links"]["download"], timeout=120) as remote, partial.open("wb") as local:
        while block := remote.read(1024 * 1024):
            total += len(block)
            digest.update(block)
            local.write(block)
    downloaded_hash = digest.hexdigest()
    if total != EXPECTED_SIZE or downloaded_hash != EXPECTED_SHA256:
        partial.unlink(missing_ok=True)
        raise ValueError(
            f"Holdout download integrity failure: bytes={total}, sha256={downloaded_hash}"
        )
    partial.replace(TARGET)
    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "dataset": "Upworthy Research Archive",
        "partition": "official holdout",
        "source_url": "https://osf.io/jd64p/",
        "osf_node": "jd64p",
        "osf_file_id": data["id"],
        "filename": TARGET.name,
        "bytes": total,
        "sha256": downloaded_hash,
        "license": "CC BY 4.0",
        "acquired_at_utc": datetime.now(UTC).isoformat(),
        "protocol": "papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md",
        "protocol_sha256": PROTOCOL_SHA256,
        "evaluation_runner_sha256": RUNNER_SHA256,
        "policy_implementation_sha256": IMPLEMENTATION_SHA256,
        "acquisition_script_sha256": sha256(Path(__file__).resolve()),
        "data_opened_after_protocol_freeze": True,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(acquire(), indent=2))


if __name__ == "__main__":
    main()
