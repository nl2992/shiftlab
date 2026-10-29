"""Validate and deduplicate the preserved T=8, delay-two run artifact."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/risk_preserving_approx/t8_delay2_calendar_v1.json"
EXECUTED = ROOT / "docs/risk_preserving_approx/t8_delay2_calendar_executed_source_v1.txt"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_delay2_calendar_deduplicated_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    if sha(EXECUTED) != original["runner_sha256"]:
        raise ValueError("preserved executed source does not match recorded runner hash")
    groups: dict[tuple[str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for row in original["cells"]:
        key = (row["transition"], tuple(row["emissions"]))
        groups[key].append(row)
    corrected = []
    for key, rows in sorted(groups.items()):
        if len(rows) != 42 or any(row != rows[0] for row in rows[1:]):
            raise ValueError(f"unexpected duplicate pattern for {key}: {len(rows)} rows")
        if len(rows[0]["calendars"]) != 42:
            raise ValueError(f"calendar count mismatch for {key}")
        corrected.append(rows[0])
    if len(corrected) != 6 or any(row["status"] != "completed" for row in corrected):
        raise ValueError("expected six fully completed cells")
    payload = {
        "correction": "deduplicate identical final cell objects serialized once per calendar",
        "source_artifact_sha256": sha(SOURCE),
        "executed_runner_sha256": sha(EXECUTED),
        "correction_script_sha256": sha(Path(__file__)),
        "registered_protocol_sha256": original["protocol_sha256"],
        "source_hashes": original["source_hashes"],
        "duplicate_pattern_verified": True,
        "repeated_entries_per_cell": 42,
        "cells": corrected,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corrected_cells": len(corrected), "output": OUTPUT.name}))


if __name__ == "__main__":
    main()
