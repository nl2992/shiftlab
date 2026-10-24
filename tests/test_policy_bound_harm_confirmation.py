from __future__ import annotations

import json

import pandas as pd

from scripts.analyze_policy_bound_harm_confirmation import (
    holm_adjust,
    paired_detection_pvalue,
    wilson_interval,
)
from scripts.run_policy_bound_harm_confirmation import (
    CALIBRATION_METHODS,
    CALIBRATION_SCENARIOS,
    calibration_passes,
)


def write_calibration_summary(path, familywise_uppers):
    rows = [
        {
            "scenario": scenario,
            "method": method,
            "monitor": "fixed_mixture",
            "primary_familywise_95_upper": upper,
        }
        for (scenario, method), upper in zip(
            [
                (scenario, method)
                for scenario in CALIBRATION_SCENARIOS
                for method in CALIBRATION_METHODS
            ],
            familywise_uppers,
            strict=True,
        )
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    report_dir = path.parents[1] / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "policy_bound_null_calibration.md").write_text(
        "The calibration criterion is **PASS**.", encoding="utf-8"
    )
    config = {
        "seeds": 500,
        "seed_offset": 54_000_000,
        "common_eprocess_bound": False,
        "scenario_subset": list(CALIBRATION_SCENARIOS),
        "method_subset": list(CALIBRATION_METHODS),
    }
    manifest = {"configuration": config, "resolved_device": "cuda"}
    (report_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_calibration_gate_requires_all_ten_primary_cells(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(summary_dir / "policy_bound_null_calibration.csv", [0.04] * 10)
    assert calibration_passes(calibration)


def test_calibration_gate_rejects_failed_or_incomplete_cells(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(
        summary_dir / "policy_bound_null_calibration.csv", [0.04] * 9 + [0.05]
    )
    assert not calibration_passes(calibration)
    assert not calibration_passes(tmp_path / "missing")


def test_calibration_gate_rejects_duplicate_or_missing_primary_cell(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    path = summary_dir / "policy_bound_null_calibration.csv"
    write_calibration_summary(path, [0.04] * 10)
    summary = pd.read_csv(path)
    summary.loc[9, ["scenario", "method"]] = summary.loc[0, ["scenario", "method"]].to_numpy()
    summary.to_csv(path, index=False)
    assert not calibration_passes(calibration)


def test_holm_adjustment_preserves_order_and_is_monotone():
    assert holm_adjust([0.01, 0.04, 0.03, 0.002]) == [0.03, 0.06, 0.06, 0.008]


def test_one_sided_paired_test_uses_only_discordant_seed_pairs():
    assert paired_detection_pvalue(0, 0) == 1.0
    assert paired_detection_pvalue(8, 0) < 0.01
    assert paired_detection_pvalue(0, 8) == 1.0


def test_wilson_interval_contains_the_observed_rate():
    low, high = wilson_interval(14, 40)
    assert low < 14 / 40 < high
