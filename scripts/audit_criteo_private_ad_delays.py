"""Aggregate-only streaming audit of CriteoPrivateAds labels and delays.

The report contains counts and delay summaries only. It never writes source
records, identifiers, or feature values. Scan the pinned snapshot only after
``audit_criteo_private_ad_snapshot.py`` passes.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

OUTCOMES = {
    "click": ("is_clicked", "click_delay_after_display_array"),
    "landed_click": ("is_click_landed", "landed_click_delay_after_display_array"),
    "sale": (None, "sale_delay_after_display_array"),
}


def _empty_stats() -> dict[str, Any]:
    return {
        "rows": 0,
        "positive_rows": 0,
        "rows_with_any_delay": 0,
        "positive_rows_with_any_delay": 0,
        "positive_rows_without_delay": 0,
        "delay_values": 0,
        "negative_delay_values": 0,
        "negative_value_counts": Counter(),
        "min_delay_value": None,
        "max_delay_value": None,
        "negative_entries_on_positive_rows": 0,
        "negative_entries_on_nonpositive_rows": 0,
    }


def _update_delay_stats(stats: dict[str, Any], labels: np.ndarray, delays: Any) -> None:
    lengths = pc.fill_null(pc.list_value_length(delays), 0).to_numpy(zero_copy_only=False)
    present = lengths > 0
    positive = labels > 0
    stats["rows"] += int(labels.size)
    stats["positive_rows"] += int(positive.sum())
    stats["rows_with_any_delay"] += int(present.sum())
    stats["positive_rows_with_any_delay"] += int((positive & present).sum())
    stats["positive_rows_without_delay"] += int((positive & ~present).sum())

    flat_array = pc.list_flatten(delays)
    parent_array = pc.list_parent_indices(delays)
    valid_values = pc.invert(pc.is_null(flat_array))
    flat = pc.filter(flat_array, valid_values).to_numpy(zero_copy_only=False)
    parents = pc.filter(parent_array, valid_values).to_numpy(zero_copy_only=False)
    if flat.size == 0:
        return
    stats["delay_values"] += int(flat.size)
    batch_min = int(flat.min())
    batch_max = int(flat.max())
    current_min = stats["min_delay_value"]
    current_max = stats["max_delay_value"]
    stats["min_delay_value"] = batch_min if current_min is None else min(current_min, batch_min)
    stats["max_delay_value"] = batch_max if current_max is None else max(current_max, batch_max)

    negative_positions = np.flatnonzero(flat < 0)
    if negative_positions.size:
        stats["negative_delay_values"] += int(negative_positions.size)
        negative_values, negative_counts = np.unique(flat[negative_positions], return_counts=True)
        stats["negative_value_counts"].update(
            {
                int(value): int(count)
                for value, count in zip(negative_values, negative_counts, strict=True)
            }
        )
        is_positive_entry = positive[parents[negative_positions]]
        stats["negative_entries_on_positive_rows"] += int(is_positive_entry.sum())
        stats["negative_entries_on_nonpositive_rows"] += int((~is_positive_entry).sum())


def audit_delays(root: Path, batch_size: int = 32768) -> dict[str, Any]:
    root = root.resolve()
    manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))
    expected_rows_by_day = manifest["parquet_validation"]["rows_by_day_int"]
    stats_by_outcome = {name: _empty_stats() for name in OUTCOMES}
    rows_by_day: Counter[int] = Counter()
    positive_by_day: dict[str, dict[str, int]] = {}
    scanned_files = 0
    current_day: int | None = None

    required_columns = {
        "is_clicked",
        "is_click_landed",
        "is_visit",
        "nb_sales",
        "click_delay_after_display_array",
        "landed_click_delay_after_display_array",
        "sale_delay_after_display_array",
    }
    for item in manifest["files"]:
        path = root / item["local_path"]
        if not path.is_file() or path.stat().st_size != int(item["size"]):
            raise ValueError(f"Snapshot file missing or size mismatch: {item['path']}")
        parquet = pq.ParquetFile(path)
        if not required_columns.issubset(parquet.schema_arrow.names):
            raise ValueError(f"Required label/delay fields missing in {item['path']}")
        day = int(path.parent.name.split("=", maxsplit=1)[1])
        if day != current_day:
            print(f"aggregate-only scan entering day_int={day}", file=sys.stderr, flush=True)
            current_day = day
        for batch in parquet.iter_batches(batch_size=batch_size, columns=sorted(required_columns)):
            columns = {
                name: batch.column(batch.schema.get_field_index(name)) for name in required_columns
            }
            click = pc.fill_null(columns["is_clicked"], 0).to_numpy(zero_copy_only=False)
            landed = pc.fill_null(columns["is_click_landed"], 0).to_numpy(zero_copy_only=False)
            sale = (
                (columns["is_visit"].to_numpy(zero_copy_only=False) > 0)
                & (columns["nb_sales"].to_numpy(zero_copy_only=False) > 0)
            ).astype(np.int8)
            _update_delay_stats(
                stats_by_outcome["click"], click, columns["click_delay_after_display_array"]
            )
            _update_delay_stats(
                stats_by_outcome["landed_click"],
                landed,
                columns["landed_click_delay_after_display_array"],
            )
            _update_delay_stats(
                stats_by_outcome["sale"], sale, columns["sale_delay_after_display_array"]
            )
            rows_by_day[day] += batch.num_rows
            day_counts = positive_by_day.setdefault(
                str(day), {"rows": 0, "clicks": 0, "landed_clicks": 0, "sales": 0}
            )
            day_counts["rows"] += batch.num_rows
            day_counts["clicks"] += int((click > 0).sum())
            day_counts["landed_clicks"] += int((landed > 0).sum())
            day_counts["sales"] += int(sale.sum())
        scanned_files += 1

    day_counts_match = {
        str(day): rows_by_day.get(int(day), 0) == int(expected)
        for day, expected in expected_rows_by_day.items()
    }
    normalized = {}
    for outcome, stats in stats_by_outcome.items():
        row = dict(stats)
        row["negative_value_counts"] = dict(sorted(row["negative_value_counts"].items()))
        row["observed_positive_rate"] = (
            stats["positive_rows"] / stats["rows"] if stats["rows"] else None
        )
        normalized[outcome] = row

    return {
        "audit": "CriteoPrivateAds aggregate-only label/delay audit",
        "dataset": manifest.get("dataset"),
        "revision": manifest.get("revision"),
        "license": manifest.get("license"),
        "source_manifest_file_count": int(manifest["file_count"]),
        "scanned_files": scanned_files,
        "rows_scanned": int(sum(rows_by_day.values())),
        "records_retained": 0,
        "rows_by_day": dict(sorted(rows_by_day.items())),
        "expected_rows_by_day_match": day_counts_match,
        "label_and_delay_summary": normalized,
        "day_label_counts": dict(sorted(positive_by_day.items(), key=lambda pair: int(pair[0]))),
        "source_documentation_unit_note": (
            "Publisher docs say minutes; paper example also gives 24*3600 seconds. "
            "This report does not resolve the discrepancy or interpret negative values."
        ),
        "validation": "passed"
        if scanned_files == int(manifest["file_count"]) and all(day_counts_match.values())
        else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw/criteo_privatead"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/reports/criteo_privatead_delay_audit.json")
    )
    parser.add_argument("--batch-size", type=int, default=32768)
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    result = audit_delays(args.root, batch_size=args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "validation": result["validation"],
                "revision": result["revision"],
                "scanned_files": result["scanned_files"],
                "rows_scanned": result["rows_scanned"],
                "label_and_delay_summary": result["label_and_delay_summary"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["validation"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
