"""Audit retained publisher bytes referenced by immutable dataset manifests."""

import argparse
import json
from pathlib import Path

from shiftlab.data.provenance import sha256, write_json


def audit(root: Path) -> dict:
    rows = []
    for pointer_path in sorted((root / "manifests").glob("*.json")):
        pointer = json.loads(pointer_path.read_text())
        for source_path, expected in pointer.get("raw_checksums", {}).items():
            path = Path(source_path)
            exists = path.is_file()
            actual = sha256(path) if exists else None
            rows.append(
                {
                    "dataset": pointer["dataset"],
                    "version": pointer["version"],
                    # Avoid recording machine-specific absolute paths in the shared report.
                    "raw_file": path.name,
                    "status": "verified"
                    if actual == expected
                    else "missing"
                    if not exists
                    else "mismatch",
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                }
            )
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("verified", "missing", "mismatch")
    }
    return {
        "scope": "Raw source files currently retained at manifest-recorded paths",
        "n_references": len(rows),
        "counts": counts,
        "records": rows,
        "interpretation": (
            "Missing means the historical manifest retains a checksum but its raw file is absent; "
            "it is not evidence of a changed source. Mismatch indicates present bytes differ."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data"))
    args = parser.parse_args()
    result = audit(args.root)
    output = args.root / "reports" / "raw_provenance_audit.json"
    write_json(output, result)
    print(json.dumps({"output": str(output), "counts": result["counts"]}, indent=2))
    if result["counts"]["mismatch"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
