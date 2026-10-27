import numpy as np
import pandas as pd
import pytest

from scripts.analyze_gated_monitor_comparison import calibrate, exact_upper, paired_bootstrap


def test_zero_alarm_exact_upper_matches_closed_form_with_family_correction():
    assert exact_upper(0, 2000, 8) == pytest.approx(1 - (0.05 / 8) ** (1 / 2000))
    assert exact_upper(2000, 2000, 8) == 1.0


def test_paired_bootstrap_preserves_pairing_and_nonpositive_denominator_is_not_a_ratio():
    baseline = np.array([1, 2, 4, 8], dtype=float)
    difference = paired_bootstrap(baseline + 0.25, baseline)
    assert difference["estimate"] == 0.25
    assert difference["lower_97p5_one_sided"] == 0.25
    ratio = paired_bootstrap(2 * baseline, baseline, ratio=True)
    assert ratio["estimate"] == 2.0
    assert ratio["lower_97p5_one_sided"] == 2.0
    assert paired_bootstrap(baseline, -baseline, ratio=True)["estimate"] is None


def test_unstable_positive_mean_bootstrap_denominator_cannot_pass_a_ratio_gate():
    result = paired_bootstrap([1.0, 1.0], [-0.99, 1.0], ratio=True)
    assert result["estimate"] > 0
    assert result["lower_97p5_one_sided"] is None
    assert not result["uncertainty_defined"]


def test_incomplete_calibration_is_rejected_before_a_gate_decision():
    frame = pd.DataFrame(
        {
            "arm": ["gated_ht_paced"],
            "scenario": ["stationary"],
            "budget_rate": [0.2],
            "seed": [58500000],
            "false_alarm": [False],
        }
    )
    with pytest.raises(ValueError, match="seed block"):
        calibrate(frame)
