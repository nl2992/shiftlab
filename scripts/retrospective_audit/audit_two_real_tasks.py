"""Verify archived EIA and Upworthy aggregate results without raw-data replay."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT.parent / "shift-research-starter" / "outputs" / "shiftguard_unified"
EIA = ORIGINAL / "independent_real_data" / "eia_2026_v1"
UPWORTHY = ORIGINAL / "real_data_development" / "upworthy_policy_v1"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "TWO_REAL_TASK_AGGREGATES.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def run() -> dict[str, object]:
    eia_manifest = json.loads((EIA / "manifest.json").read_text(encoding="utf-8"))
    eia_bad = [
        name
        for name, expected in eia_manifest["outputs_sha256"].items()
        if sha256(EIA / name) != expected
    ]
    if eia_bad:
        raise AssertionError(f"EIA output hash mismatch: {eia_bad}")
    eia_rows = read_csv(EIA / "summary.csv")
    eia_groups = {}
    for row in eia_rows:
        key = (row["domain_id"], int(row["delay_hours"]))
        eia_groups.setdefault(key, {})[row["policy"]] = row
    for (domain, delay), policies in eia_groups.items():
        if set(policies) != {"frozen", "weekly", "monthly", "error_trigger"}:
            raise AssertionError(f"Incomplete EIA policy set: {domain}/{delay}")
        baseline = policies["frozen"]
        for name in ("weekly", "monthly", "error_trigger"):
            if not (
                float(policies[name]["rmse"]) < float(baseline["rmse"])
                and float(policies[name]["mae"]) < float(baseline["mae"])
            ):
                raise AssertionError(
                    f"EIA adaptive policy did not improve: {domain}/{delay}/{name}"
                )
    eia_intervals = read_csv(EIA / "paired_block_intervals.csv")
    if len(eia_intervals) != 54:
        raise AssertionError("Incomplete EIA contrast panel")
    rmse_intervals_below_zero = 0
    for row in eia_intervals:
        policies = eia_groups[(row["domain_id"], int(row["delay_hours"]))]
        name = row["policy"]
        metric = row["metric"]
        actual = float(policies[name][metric]) - float(policies["frozen"][metric])
        if abs(actual - float(row["point_difference"])) > 1e-9:
            raise AssertionError(f"EIA contrast mismatch: {row}")
        if metric == "rmse" and float(row["ci_97_5"]) < 0:
            rmse_intervals_below_zero += 1

    up_manifest = json.loads((UPWORTHY / "manifest.json").read_text(encoding="utf-8"))
    up_bad = [
        name
        for name, expected in up_manifest["outputs"].items()
        if sha256(UPWORTHY / name) != expected
    ]
    if up_bad:
        raise AssertionError(f"Upworthy output hash mismatch: {up_bad}")
    summary = json.loads((UPWORTHY / "summary.json").read_text(encoding="utf-8"))
    per_test = read_csv(UPWORTHY / "per_test_metrics.csv")
    n = len(per_test)
    mean = sum(float(row["delta_ctr"]) for row in per_test) / n
    selected = sum(float(row["selected_ctr"]) for row in per_test) / n
    uniform = sum(float(row["uniform_reference_ctr"]) for row in per_test) / n
    result = summary["results"]
    if (
        n != result["eligible_tests"]
        or sum(int(row["n_arms"]) for row in per_test) != result["eligible_arms"]
    ):
        raise AssertionError("Upworthy coverage mismatch")
    if any(
        abs(actual - expected) > 1e-12
        for actual, expected in (
            (mean, result["equal_test_delta_ctr"]),
            (selected, result["equal_test_selected_ctr"]),
            (uniform, result["equal_test_uniform_ctr"]),
        )
    ):
        raise AssertionError("Upworthy aggregate mismatch")
    return {
        "scope": "Archived output hash and aggregate arithmetic only; raw data/model replay not performed",
        "eia": {
            "output_hashes_checked": len(eia_manifest["outputs_sha256"]),
            "summary_rows": len(eia_rows),
            "domain_delay_groups": len(eia_groups),
            "all_adaptive_rmse_and_mae_below_frozen": True,
            "paired_interval_rows": len(eia_intervals),
            "rmse_intervals_below_zero": rmse_intervals_below_zero,
            "group_test_counts": {
                f"{domain}/{delay}": int(policies["frozen"]["test_n"])
                for (domain, delay), policies in eia_groups.items()
            },
        },
        "upworthy": {
            "output_hashes_checked": len(up_manifest["outputs"]),
            "eligible_tests": n,
            "eligible_arms": result["eligible_arms"],
            "equal_test_delta_ctr": mean,
            "equal_test_selected_ctr": selected,
            "equal_test_uniform_ctr": uniform,
            "week_cluster_interval_from_archived_summary": summary["protocol"]["bootstrap"][
                "delta_ci_95"
            ],
        },
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["eia"], result["upworthy"])
