"""Reject malformed or shifted fields in the audit's master claim ledger."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/retrospective_audit_2026_11_01/03_CLAIM_MASTER_LEDGER.csv"
REQUIRED = {
    "claim_id",
    "topic",
    "source_path",
    "source_commit",
    "original_verdict",
    "corrected_scope",
    "proposed_verdict",
    "reviewer",
    "artifact_links",
    "status",
}
STATUSES = {"NOT_YET_AUDITED", "INCONCLUSIVE", "SUPPORTED", "REFUTED", "SUPERSEDED"}


def validate(path: Path = LEDGER) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader)
        if len(header) != len(set(header)) or not REQUIRED.issubset(header):
            raise ValueError("duplicate or missing ledger header")
        seen: set[str] = set()
        count = 0
        for line, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise ValueError(f"line {line}: expected {len(header)} fields, got {len(row)}")
            record = dict(zip(header, row, strict=True))
            if not record["claim_id"] or record["claim_id"] in seen:
                raise ValueError(f"line {line}: blank or duplicate claim ID")
            seen.add(record["claim_id"])
            if record["status"] not in STATUSES:
                raise ValueError(f"line {line}: invalid status {record['status']!r}")
            if not record["source_path"] or not record["reviewer"]:
                raise ValueError(f"line {line}: missing source or reviewer")
            count += 1
    if count == 0:
        raise ValueError("empty claim ledger")
    return count


if __name__ == "__main__":
    print(f"{validate()} structurally valid claim rows")
