"""Audit the pinned CriteoPrivateAds snapshot from Parquet metadata only.

This deliberately reads no impression records. It verifies the local files
against the saved source manifest, checks every Parquet footer/schema, and
reconciles row counts with the acquisition-time metadata audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_snapshot(root: Path, verify_sha256: bool = False) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", [])
    if not files:
        raise ValueError("source_manifest.json contains no data-file entries")

    missing: list[str] = []
    size_mismatch: list[dict[str, Any]] = []
    invalid_source_hash: list[str] = []
    hash_mismatch: list[str] = []
    hashes_checked = 0
    bad_parquet: list[dict[str, str]] = []
    schemas: Counter[str] = Counter()
    rows_by_day: Counter[int] = Counter()
    empty_files = 0
    total_bytes = 0
    total_rows = 0
    column_names: set[str] | None = None

    for entry in files:
        relative = Path(entry["local_path"])
        path = (root / relative).resolve()
        if root not in path.parents:
            raise ValueError(f"manifest path escapes snapshot root: {relative}")
        if not path.is_file():
            missing.append(entry["path"])
            continue

        actual_size = path.stat().st_size
        total_bytes += actual_size
        if actual_size != int(entry["size"]):
            size_mismatch.append(
                {"path": entry["path"], "expected": int(entry["size"]), "actual": actual_size}
            )
        source_hash = str(entry.get("sha256", ""))
        if len(source_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in source_hash.lower()
        ):
            invalid_source_hash.append(entry["path"])
        elif verify_sha256:
            hashes_checked += 1
            if sha256_file(path).lower() != source_hash.lower():
                hash_mismatch.append(entry["path"])

        try:
            parquet = pq.ParquetFile(path)
            schema = parquet.schema_arrow
            fingerprint = hashlib.sha256(schema.serialize().to_pybytes()).hexdigest()
            schemas[fingerprint] += 1
            rows = int(parquet.metadata.num_rows)
            total_rows += rows
            day_part = path.parent.name
            if not day_part.startswith("day_int="):
                raise ValueError(f"unexpected partition directory {day_part!r}")
            day = int(day_part.split("=", maxsplit=1)[1])
            rows_by_day[day] += rows
            if rows == 0:
                empty_files += 1
            names = set(schema.names)
            column_names = names if column_names is None else column_names
            if names != column_names:
                bad_parquet.append({"path": entry["path"], "error": "schema columns differ"})
        except (OSError, ValueError, pa.ArrowException) as exc:
            bad_parquet.append({"path": entry["path"], "error": f"{type(exc).__name__}: {exc}"})

    expected = manifest.get("parquet_validation", {})
    expected_rows = expected.get("row_count")
    expected_days = expected.get("rows_by_day_int", {})
    day_rows_match = {
        str(day): rows_by_day.get(int(day), 0) == int(count) for day, count in expected_days.items()
    }
    expected_files = int(manifest.get("file_count", -1))
    valid = (
        len(files) == expected_files
        and len(missing) == 0
        and len(size_mismatch) == 0
        and len(invalid_source_hash) == 0
        and len(hash_mismatch) == 0
        and len(bad_parquet) == 0
        and len(schemas) == 1
        and len(rows_by_day) == int(expected.get("day_partition_count", -1))
        and (expected_rows is None or total_rows == int(expected_rows))
        and all(day_rows_match.values())
        and total_bytes == int(manifest.get("total_bytes", -1))
    )
    return {
        "audit": "CriteoPrivateAds local snapshot structural audit",
        "records_read": 0,
        "metadata_only": True,
        "dataset": manifest.get("dataset"),
        "revision": manifest.get("revision"),
        "license": manifest.get("license"),
        "source_manifest_sha256": sha256_file(manifest_path),
        "manifest_file_count": len(files),
        "expected_file_count": expected_files,
        "present_file_count": len(files) - len(missing),
        "missing_files": missing,
        "size_mismatch": size_mismatch,
        "invalid_source_hash_entries": invalid_source_hash,
        "sha256_recomputed": verify_sha256,
        "sha256_files_checked": hashes_checked,
        "sha256_mismatch": hash_mismatch,
        "parquet_errors": bad_parquet,
        "unique_schema_count": len(schemas),
        "schema_fingerprints": dict(schemas),
        "column_count": len(column_names or []),
        "row_count_from_parquet_metadata": total_rows,
        "expected_row_count": expected_rows,
        "empty_parquet_file_count": empty_files,
        "day_partition_count": len(rows_by_day),
        "rows_by_day_int": dict(sorted(rows_by_day.items())),
        "day_row_count_matches": day_rows_match,
        "total_bytes": total_bytes,
        "validation": "passed" if valid else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw/criteo_privatead"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/reports/criteo_privatead_snapshot_audit.json"),
    )
    parser.add_argument(
        "--verify-sha256",
        action="store_true",
        help="recompute all publisher hashes (reads the full 31.7 GiB snapshot; writes no data copy)",
    )
    args = parser.parse_args()
    report = audit_snapshot(args.root, verify_sha256=args.verify_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "validation",
                    "revision",
                    "manifest_file_count",
                    "row_count_from_parquet_metadata",
                    "unique_schema_count",
                    "day_partition_count",
                    "empty_parquet_file_count",
                    "sha256_recomputed",
                    "sha256_files_checked",
                    "total_bytes",
                )
            },
            sort_keys=True,
        )
    )
    return 0 if report["validation"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
