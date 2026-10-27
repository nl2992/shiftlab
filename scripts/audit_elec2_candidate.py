"""Aggregate-only integrity audit for the public OpenML ELEC2 ARFF file."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

OPENML_MD5 = "8ca97867d960ae029ae3a9ac2c923d34"
EXPECTED_COLUMNS = 9
EXPECTED_ATTRIBUTES = [
    "date",
    "day",
    "period",
    "nswprice",
    "nswdemand",
    "vicprice",
    "vicdemand",
    "transfer",
    "class",
]
EXPECTED_ROWS = 45_312


def audit(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    rows: list[list[str]] = []
    attributes: list[str] = []
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if line.lower().startswith("@attribute "):
            attributes.append(line.split(maxsplit=2)[1].strip("\"'"))
            continue
        if line.startswith("@"):
            continue
        row = [part.strip() for part in line.split(",")]
        if len(row) != EXPECTED_COLUMNS:
            raise ValueError(f"Expected {EXPECTED_COLUMNS} fields, got {len(row)}")
        rows.append(row)
    if not rows:
        raise ValueError("No ARFF data rows found")
    if [name.lower() for name in attributes] != EXPECTED_ATTRIBUTES:
        raise ValueError(f"Unexpected ARFF attributes: {attributes}")
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(rows)}")
    actual_md5 = hashlib.md5(raw).hexdigest()
    if actual_md5 != OPENML_MD5:
        raise ValueError(f"OpenML MD5 mismatch: {actual_md5}")

    date_period_positions: dict[tuple[str, str], list[int]] = defaultdict(list)
    label_counts: Counter[str] = Counter()
    invalid_numeric_cells = 0
    adjacent_date_decreases = 0
    adjacent_same_dates = 0
    period_resets = 0
    for index, row in enumerate(rows):
        label_counts[row[8]] += 1
        date_period_positions[(row[0], row[2])].append(index)
        for value in row[:8]:
            try:
                invalid_numeric_cells += not math.isfinite(float(value))
            except ValueError:
                invalid_numeric_cells += 1
        if index:
            previous = rows[index - 1]
            adjacent_date_decreases += float(row[0]) < float(previous[0])
            adjacent_same_dates += float(row[0]) == float(previous[0])
            period_resets += float(row[2]) < float(previous[2])

    duplicate_groups = {
        key: positions for key, positions in date_period_positions.items() if len(positions) > 1
    }
    return {
        "path_name": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "md5": actual_md5,
        "openml_md5_matches": True,
        "rows": len(rows),
        "columns": EXPECTED_COLUMNS,
        "labels": dict(label_counts),
        "date_unique_values": len({row[0] for row in rows}),
        "date_min": min(float(row[0]) for row in rows),
        "date_max": max(float(row[0]) for row in rows),
        "period_unique_values": len({row[2] for row in rows}),
        "duplicate_date_period_groups": len(duplicate_groups),
        "duplicate_date_period_excess_rows": sum(
            len(positions) - 1 for positions in duplicate_groups.values()
        ),
        "duplicate_date_period_group_examples": [
            {"date": key[0], "period": key[1], "row_indices": positions}
            for key, positions in list(duplicate_groups.items())[:3]
        ],
        "adjacent_date_decreases_in_file_order": adjacent_date_decreases,
        "adjacent_rows_with_same_date": adjacent_same_dates,
        "period_resets_in_file_order": period_resets,
        "invalid_or_nonfinite_numeric_cells": invalid_numeric_cells,
        "first_row": rows[0],
        "last_row": rows[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("arff", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.arff)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
