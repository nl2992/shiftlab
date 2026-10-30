"""Fetch the official research dataset; archive integrity only, no outcome scoring."""

import hashlib
import json
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip"


def main():
    raw = ROOT / "outputs/exhaustive_evaluation/gas_source/uci224.zip"
    manifest = ROOT / "docs/exhaustive_evaluation/gas_source_manifest.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    if not raw.exists():
        with urllib.request.urlopen(URL, timeout=30) as response:
            data = response.read(20_000_001)
        if len(data) > 20_000_000:
            raise ValueError("archive exceeds registered 20 MB fetch cap")
        raw.write_bytes(data)
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    if manifest.exists():
        assert json.loads(manifest.read_text())["sha256"] == digest
        print("Existing source hash verified")
        return
    with zipfile.ZipFile(raw) as archive:
        assert archive.testzip() is None
        batches = [n for n in archive.namelist() if n.lower().endswith(".dat")]
        assert len(batches) == 10
        members = [{"name": n, "bytes": archive.getinfo(n).file_size} for n in batches]
    record = {
        "url": URL,
        "doi": "10.24432/C5RP6W",
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "bytes": raw.stat().st_size,
        "sha256": digest,
        "archive_members": members,
        "integrity": "ZIP CRC checks pass",
        "source_roles": "source-ordered batches; within-batch time and label release unverified",
        "license": "UCI current page CC BY 4.0; original text research-only; retain research-only use pending clarification",
        "prior_exposure": "documented in papers/shiftguard_unified/gas_sensor_candidate_protocol.md and real_data_development_results.md",
        "fresh_confirmation_eligible": False,
        "outcomes_analyzed": False,
        "next_use": "existing adapter and frozen historical protocol reproduction or explicitly exploratory source-ordered stress test",
    }
    manifest.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(
        "Downloaded official Gas Sensor archive:",
        record["bytes"],
        "bytes; 10 batch files; CRC pass; no outcomes scored",
    )


if __name__ == "__main__":
    main()
