"""Independently recompute the Upworthy week-cluster interval from per-test rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "shift-research-starter"
    / "outputs"
    / "shiftguard_unified"
    / "real_data_development"
    / "upworthy_policy_v1"
)
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "UPWORTHY_WEEK_BOOTSTRAP.json"


def run() -> dict[str, object]:
    with (SOURCE / "per_test_metrics.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    by_week: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_week.setdefault(row["test_week"], []).append(row)
    weeks = list(by_week)
    counts = np.array([len(by_week[week]) for week in weeks], dtype=np.float64)
    fields = ("delta_ctr", "selected_ctr", "uniform_reference_ctr")
    sums = {
        field: np.array(
            [sum(float(row[field]) for row in by_week[week]) for week in weeks], dtype=np.float64
        )
        for field in fields
    }
    rng = np.random.default_rng(20261026)
    draws = rng.integers(0, len(weeks), size=(10_000, len(weeks)))
    denom = counts[draws].sum(axis=1)
    boot = {field: sums[field][draws].sum(axis=1) / denom for field in fields}
    result = {
        "week_clusters": len(weeks),
        "bootstrap_replicates": len(draws),
        "seed": 20261026,
        "delta_ci_95": [float(x) for x in np.quantile(boot["delta_ctr"], [0.025, 0.975])],
        "delta_one_sided_lower_95": float(np.quantile(boot["delta_ctr"], 0.05)),
        "selected_ctr_ci_95": [float(x) for x in np.quantile(boot["selected_ctr"], [0.025, 0.975])],
        "uniform_ctr_ci_95": [
            float(x) for x in np.quantile(boot["uniform_reference_ctr"], [0.025, 0.975])
        ],
    }
    expected = summary["protocol"]["bootstrap"]
    for key, value in result.items():
        if isinstance(value, list):
            if not np.allclose(value, expected[key], rtol=0, atol=1e-15):
                raise AssertionError(f"Bootstrap mismatch: {key}")
        elif abs(value - expected[key]) > 1e-15:
            raise AssertionError(f"Bootstrap mismatch: {key}")
    return {
        "scope": "Independent week-resampling arithmetic on archived per-test rows; no raw-data/model replay",
        "archived_summary_reconciled": True,
        "result": result,
    }


if __name__ == "__main__":
    output = run()
    DEST.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output["result"])
