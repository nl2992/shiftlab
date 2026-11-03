"""Independently reconcile archived WP3 path rows for two registered arms.

This is a retrospective arithmetic/integrity check, not a fresh confirmation.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "shift-research-starter" / "outputs" / "data_efficient_prescreen_20"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "WP3_PATH_RECOMPUTATION.json"
ARMS = {("optional_candidate", "fixed1", "sr"), ("optional_temporal", "fixed1", "started")}
SEEDS = set(range(59_000_000, 59_000_020))
HORIZON = 2400


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flag(value: str) -> bool:
    if value not in {"True", "False"}:
        raise ValueError(f"invalid Boolean: {value!r}")
    return value == "True"


def mean(rows: list[dict[str, str]], field: str) -> float:
    return sum(float(row[field]) for row in rows) / len(rows)


def run(source: Path = SOURCE) -> dict[str, object]:
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hashes = manifest["outputs_sha256"]
    if len([name for name in expected_hashes if name.startswith("path_")]) != 40:
        raise ValueError("run manifest does not list 40 path files")
    for name, expected in expected_hashes.items():
        actual = sha256(source / name)
        if actual != expected:
            raise ValueError(f"manifest hash mismatch: {name}")

    rows: list[dict[str, str]] = []
    for index in range(40):
        with (source / f"path_{index:02d}.csv").open(newline="", encoding="utf-8") as stream:
            rows.extend(csv.DictReader(stream))
    if len(rows) != 39_200 or len(rows) != int(manifest["rows"]):
        raise ValueError("raw path row count disagrees with registered panel/manifest")

    groups: dict[tuple[float, float, str, str, str], list[dict[str, str]]] = defaultdict(list)
    selected: dict[tuple[float, float, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        arm = (row["arm"], row["engine"], row["detector"])
        onset = float(row["onset_fraction"])
        budget_rate = float(row["budget_rate"])
        onset_index = round(onset * HORIZON)
        alarm = float(row["first_alarm"]) if row["first_alarm"] else None
        if alarm is not None and (not 0 <= alarm < HORIZON or not alarm.is_integer()):
            raise ValueError("invalid zero-based alarm index")
        detected = alarm is not None and alarm >= onset_index
        delay = (alarm - onset_index) if detected else (HORIZON - onset_index)
        if detected != flag(row["detected"]) or abs(delay - float(row["delay_censored"])) > 1e-9:
            raise ValueError("detection/delay does not match alarm and registered onset")
        if row["budget"] and float(row["dollars"]) > float(row["budget"]) + 1e-8:
            raise ValueError("hard budget exceeded")
        key = (onset, budget_rate, *arm)
        groups[key].append(row)
        if arm in ARMS:
            if not flag(row["same_null_harm_comparator"]):
                raise ValueError("selected arm is not registered same-null comparator")
            selected[key].append(row)

    expected_cells = {(onset, budget) for onset in (0.5, 0.75) for budget in (0.02, 0.05, 0.1, 0.2)}
    if set(selected) != {(onset, budget, *arm) for onset, budget in expected_cells for arm in ARMS}:
        raise ValueError("selected arm/cell coverage incomplete")

    with (source / "analysis" / "summary.csv").open(newline="", encoding="utf-8") as stream:
        summaries = {
            (
                float(row["onset_fraction"]),
                float(row["budget_rate"]),
                row["arm"],
                row["engine"],
                row["detector"],
            ): row
            for row in csv.DictReader(stream)
        }
    if set(groups) != set(summaries):
        raise ValueError("raw panel and archived summary have different arm/cell keys")
    for key, group in groups.items():
        if {int(row["seed"]) for row in group} != SEEDS or len(group) != len(SEEDS):
            raise ValueError(f"full-panel seed block missing or duplicated: {key}")
        archived = summaries[key]
        if len(group) != int(archived["streams"]):
            raise ValueError(f"archived stream count mismatch: {key}")
        if len({row["same_null_harm_comparator"] for row in group}) != 1:
            raise ValueError(f"same-null flag varies within arm/cell: {key}")
        if flag(group[0]["same_null_harm_comparator"]) != flag(
            archived["same_null_harm_comparator"]
        ):
            raise ValueError(f"same-null flag mismatch: {key}")
        values = {
            "detections": sum(flag(row["detected"]) for row in group),
            "mean_delay_censored": mean(group, "delay_censored"),
            "mean_labels": mean(group, "labels"),
            "mean_dollars": mean(group, "dollars"),
        }
        if all(row["budget"] for row in group):
            values["mean_budget"] = mean(group, "budget")
        elif any(row["budget"] for row in group) or archived["mean_budget"]:
            raise ValueError(f"mixed or missing budget value: {key}")
        for name, value in values.items():
            if abs(value - float(archived[name])) > 1e-9:
                raise ValueError(f"archived full-panel summary mismatch for {key} {name}")
        if abs(values["detections"] / len(group) - float(archived["detection_rate"])) > 1e-12:
            raise ValueError(f"archived detection rate mismatch: {key}")

    output_rows = []
    for key in sorted(selected):
        group = selected[key]
        if {int(row["seed"]) for row in group} != SEEDS or len(group) != len(SEEDS):
            raise ValueError(f"seed block missing or duplicated: {key}")
        archived = summaries[key]
        values = {
            "detections": sum(flag(row["detected"]) for row in group),
            "mean_delay_censored": mean(group, "delay_censored"),
            "mean_labels": mean(group, "labels"),
            "mean_dollars": mean(group, "dollars"),
            "mean_budget": mean(group, "budget"),
        }
        for name, value in values.items():
            if abs(value - float(archived[name])) > 1e-9:
                raise ValueError(f"archived summary mismatch for {key} {name}")
        output_rows.append(
            {
                "onset_fraction": key[0],
                "budget_rate": key[1],
                "arm": key[2],
                "engine": key[3],
                "detector": key[4],
                "seeds": len(group),
                **values,
            }
        )

    return {
        "status": "ARCHIVED_EXPOSED_RETROSPECTIVE_ONLY",
        "source_manifest_sha256": sha256(manifest_path),
        "source_commit_claimed_by_manifest": manifest["git_head"],
        "path_files_hashed": 40,
        "raw_rows": len(rows),
        "full_panel_arm_cells": len(groups),
        "full_panel_summary_mismatches": 0,
        "selected_arm_cells": len(output_rows),
        "summary_mismatches": 0,
        "budget_violations_selected_arms": 0,
        "rows": output_rows,
        "limitations": "All arm/cell raw row aggregates checked, but no independent replay of monitoring decisions, bootstrap, comparator registration, or source path generation; no fresh validity/power claim.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['raw_rows']} rows; {result['full_panel_arm_cells']} arm/cells; zero summary mismatches"
    )
