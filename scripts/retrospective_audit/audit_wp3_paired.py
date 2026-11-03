"""Recompute WP3 paired prescreen comparisons from archived path rows."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from recompute_wp3 import SOURCE, run

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "WP3_PAIRED_COMPARATOR_AUDIT.json"
CANDIDATE = ("optional_candidate", "fixed1", "sr")
EXCLUDED_ARMS = {"full_feedback", "optional_candidate"}


def flag(value: str) -> bool:
    if value not in {"True", "False"}:
        raise ValueError(f"invalid Boolean: {value!r}")
    return value == "True"


def avg(rows: list[dict[str, str]], column: str) -> float:
    return sum(float(row[column]) for row in rows) / len(rows)


def check_close(expected: float, recorded: str, label: str) -> None:
    if abs(expected - float(recorded)) > 1e-9:
        raise ValueError(f"paired table mismatch: {label}")


def exact_two_point_bootstrap_interval(differences: list[int]) -> list[float]:
    """Exact percentile limits for paired {-1,0} empirical resampling."""
    if set(differences) != {-1, 0}:
        raise ValueError("this exact bootstrap formula requires both -1 and 0 differences")
    n = len(differences)
    p = differences.count(-1) / n
    distribution = sorted(
        (-k / n, math.comb(n, k) * p**k * (1 - p) ** (n - k)) for k in range(n + 1)
    )
    limits = []
    for target in (0.025, 0.975):
        cumulative = 0.0
        for value, mass in distribution:
            cumulative += mass
            if cumulative >= target:
                limits.append(value)
                break
    return limits


def run_paired(source: Path = SOURCE) -> dict[str, object]:
    full_panel = run(source)
    groups: dict[tuple[float, float, str, str, str], dict[int, dict[str, str]]] = defaultdict(dict)
    for index in range(40):
        with (source / f"path_{index:02d}.csv").open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                key = (
                    float(row["onset_fraction"]),
                    float(row["budget_rate"]),
                    row["arm"],
                    row["engine"],
                    row["detector"],
                )
                seed = int(row["seed"])
                if seed in groups[key]:
                    raise ValueError(f"duplicate key/seed: {key}/{seed}")
                groups[key][seed] = row

    compared = {
        key
        for key, group in groups.items()
        if key[2] not in EXCLUDED_ARMS
        and all(flag(row["same_null_harm_comparator"]) for row in group.values())
    }
    paired_path = source / "analysis" / "paired.csv"
    with paired_path.open(newline="", encoding="utf-8") as stream:
        paired_rows = list(csv.DictReader(stream))
    expected = {
        (
            float(row["onset_fraction"]),
            float(row["budget_rate"]),
            row["incumbent_arm"],
            row["incumbent_engine"],
            row["incumbent_detector"],
        )
        for row in paired_rows
    }
    if expected != compared or len(expected) != len(paired_rows):
        raise ValueError(
            "archived paired table omits or duplicates an eligible same-null comparator"
        )

    by_cell: dict[tuple[float, float], list[dict[str, object]]] = defaultdict(list)
    for archived in paired_rows:
        key = (
            float(archived["onset_fraction"]),
            float(archived["budget_rate"]),
            archived["incumbent_arm"],
            archived["incumbent_engine"],
            archived["incumbent_detector"],
        )
        candidate = groups[(*key[:2], *CANDIDATE)]
        incumbent = groups[key]
        if set(candidate) != set(incumbent):
            raise ValueError(f"paired seeds differ: {key}")
        c = [candidate[seed] for seed in sorted(candidate)]
        i = [incumbent[seed] for seed in sorted(incumbent)]
        if any(
            abs(float(x["budget"]) - float(y["budget"])) > 1e-9 for x, y in zip(c, i, strict=True)
        ):
            raise ValueError(f"paired hard budget differs: {key}")
        c_rate = sum(flag(row["detected"]) for row in c) / len(c)
        i_rate = sum(flag(row["detected"]) for row in i) / len(i)
        c_delay, i_delay = avg(c, "delay_censored"), avg(i, "delay_censored")
        c_labels, i_labels = avg(c, "labels"), avg(i, "labels")
        c_dollars, i_dollars = avg(c, "dollars"), avg(i, "dollars")
        values = {
            "candidate_detection_rate": c_rate,
            "incumbent_detection_rate": i_rate,
            "detection_difference": c_rate - i_rate,
            "candidate_mean_delay_censored": c_delay,
            "incumbent_mean_delay_censored": i_delay,
            "delay_ratio_incumbent_over_candidate": i_delay / c_delay,
            "candidate_mean_labels": c_labels,
            "incumbent_mean_labels": i_labels,
            "mean_labels_difference": c_labels - i_labels,
            "candidate_mean_dollars": c_dollars,
            "incumbent_mean_dollars": i_dollars,
            "mean_dollars_difference": c_dollars - i_dollars,
        }
        for name, value in values.items():
            check_close(value, archived[name], f"{key}/{name}")
        resources = c_labels <= i_labels + 1e-9 and c_dollars <= i_dollars + 1e-9
        primary = key[:2] == (0.75, 0.05)
        detection_pass = c_rate - i_rate >= (0.10 if primary else -0.03) - 1e-12
        delay_pass = i_delay / c_delay >= 1.5 - 1e-12 if primary else None
        passed = resources and (detection_pass or bool(delay_pass))
        for name, value in (
            ("resources_pass", resources),
            ("detection_margin_pass", detection_pass),
            ("passes_comparison", passed),
        ):
            if flag(archived[name]) != value:
                raise ValueError(f"paired gate flag mismatch: {key}/{name}")
        if primary and flag(archived["delay_margin_pass"]) != delay_pass:
            raise ValueError(f"paired delay gate flag mismatch: {key}")
        by_cell[key[:2]].append(
            {
                "arm": key[2],
                "engine": key[3],
                "detector": key[4],
                "detections": round(i_rate * len(i)),
                "mean_delay_censored": i_delay,
                "mean_labels": i_labels,
                "mean_dollars": i_dollars,
                "candidate_passes_comparison": passed,
            }
        )

    cells = []
    for key in sorted(by_cell):
        options = by_cell[key]
        cells.append(
            {
                "onset_fraction": key[0],
                "budget_rate": key[1],
                "comparators": len(options),
                "candidate_passes": sum(
                    bool(row["candidate_passes_comparison"]) for row in options
                ),
                "candidate_fails": sum(not row["candidate_passes_comparison"] for row in options),
            }
        )
    primary = by_cell[(0.75, 0.05)]
    best_detection = max(int(row["detections"]) for row in primary)
    top = [row for row in primary if row["detections"] == best_detection]
    top_by_delay = min(top, key=lambda row: float(row["mean_delay_censored"]))
    candidate = groups[(0.75, 0.05, *CANDIDATE)]
    incumbent = groups[
        (
            0.75,
            0.05,
            str(top_by_delay["arm"]),
            str(top_by_delay["engine"]),
            str(top_by_delay["detector"]),
        )
    ]
    primary_differences = [
        int(flag(candidate[seed]["detected"])) - int(flag(incumbent[seed]["detected"]))
        for seed in sorted(candidate)
    ]
    return {
        "status": "ARCHIVED_EXPOSED_RETROSPECTIVE_ONLY",
        "full_panel_sha256": full_panel["source_manifest_sha256"],
        "paired_csv_sha256": hashlib.sha256(paired_path.read_bytes()).hexdigest(),
        "paired_rows_checked": len(paired_rows),
        "paired_numeric_or_gate_mismatches": 0,
        "cells": cells,
        "primary_best_detection_count": best_detection,
        "primary_tied_best_detection_comparators": len(top),
        "primary_fastest_among_best_detection": top_by_delay,
        "primary_selected_pair_differences": {
            "minus_one": primary_differences.count(-1),
            "zero": primary_differences.count(0),
        },
        "primary_selected_pair_exact_empirical_bootstrap_percentiles": exact_two_point_bootstrap_interval(
            primary_differences
        ),
        "limitations": "Exact bootstrap percentiles condition on an observed selected pair and are not selection-adjusted. No source event replay or comparator-registration review. Best observed comparator is exploratory within an exposed 20-seed panel.",
    }


if __name__ == "__main__":
    result = run_paired()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['paired_rows_checked']} paired comparisons checked; zero numeric/gate mismatches"
    )
