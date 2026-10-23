from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_harm_confirmation.py"
SPEC = importlib.util.spec_from_file_location("harm_confirmation_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _metrics() -> pd.DataFrame:
    rows = []
    for scenario in MODULE.SCENARIOS:
        for seed in range(200):
            rows.append(
                {
                    "scenario": scenario,
                    "seed": seed,
                    "method": "uniform_proxy",
                    "material_harm": True,
                    "harm_reached_before_budget_stop": True,
                    "budget_respected": True,
                    "single_e_detected": seed < 100,
                    "single_e_delay": 20 if seed < 100 else float("nan"),
                    "variance_adaptive_detected": seed < 90,
                    "variance_adaptive_delay": 22 if seed < 90 else float("nan"),
                    "pm_eb_detected": seed < 10,
                    "pm_eb_delay": 25 if seed < 10 else float("nan"),
                    "realized_label_spend": 50.0,
                    "hard_budget": 60.0,
                    "labels_queried": 30,
                    "monitor_fraction_processed": 0.9,
                }
            )
    return pd.DataFrame(rows)


def test_confirmation_reports_rates_and_holm_adjusted_paired_tests() -> None:
    summary, paired = MODULE.analyze(_metrics())
    fixed = summary.loc[
        summary.scenario.eq("boundary_local_harm") & summary.monitor.eq("fixed_mixture")
    ].iloc[0]
    assert fixed.detections == 100
    assert fixed.detection_rate == pytest.approx(0.5)
    assert fixed.harm_onsets_reached == 200
    assert fixed.median_delay_given_detection == 20
    assert len(paired) == 4
    assert (paired.holm_adjusted_p_four_tests >= paired.mcnemar_exact_two_sided_p).all()


def test_confirmation_rejects_unreached_harm_onset() -> None:
    data = _metrics()
    data.loc[0, "harm_reached_before_budget_stop"] = False
    with pytest.raises(ValueError, match="onset was not reached"):
        MODULE.analyze(data)
