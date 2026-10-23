from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_null_calibration_results.py"
SPEC = importlib.util.spec_from_file_location("null_calibration_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_zero_event_exact_upper_bound_is_finite_and_positive() -> None:
    upper = MODULE.clopper_pearson_upper(0, 2000)
    assert upper == pytest.approx(0.0014967, abs=1e-6)


def test_zero_event_wilson_interval_clips_floating_point_lower_endpoint() -> None:
    assert MODULE.wilson_interval(0, 2000) == pytest.approx((0.0, 0.00191705), abs=1e-7)


def test_summary_requires_each_registered_null_block() -> None:
    data = pd.DataFrame(
        {
            "scenario": ["stationary"] * 2000,
            "method": ["uniform_proxy"] * 2000,
            "population_null_control": [True] * 2000,
            "budget_respected": [True] * 2000,
            "single_e_false_escalation": [False] * 2000,
            "variance_adaptive_false_escalation": [False] * 2000,
            "pm_eb_false_escalation": [False] * 2000,
            "realized_label_spend": [10.0] * 2000,
            "hard_budget": [10.0] * 2000,
            "labels_queried": [1] * 2000,
            "monitor_fraction_processed": [1.0] * 2000,
            "sample_path_material_harm": [False] * 2000,
        }
    )
    with pytest.raises(ValueError, match="benign_nuisance"):
        MODULE.summarize(data)


def test_diagnostic_figure_accepts_zero_event_confidence_interval(tmp_path: Path) -> None:
    diag_path = Path(__file__).resolve().parents[1] / "scripts/diagnose_hard_budget_monitors.py"
    diag_spec = importlib.util.spec_from_file_location("hard_budget_diagnostic", diag_path)
    assert diag_spec is not None and diag_spec.loader is not None
    diag = importlib.util.module_from_spec(diag_spec)
    diag_spec.loader.exec_module(diag)
    summary = pd.DataFrame(
        {
            "scenario": ["stationary"] * 3,
            "method": ["uniform_proxy"] * 3,
            "monitor": [
                "fixed_mixture",
                "predictable_variance",
                "predictable_empirical_bernstein",
            ],
            "null_streams": [2000] * 3,
            "false_escalation_rate": [0.0] * 3,
            "false_wilson_low": [1e-19] * 3,
            "false_wilson_high": [0.00192] * 3,
        }
    )
    (tmp_path / "figures").mkdir()
    output = diag.write_figure(summary, tmp_path)
    assert output.is_file()
