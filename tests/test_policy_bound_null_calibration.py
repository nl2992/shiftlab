from __future__ import annotations

import pytest

from scripts.analyze_policy_bound_null_calibration import clopper_pearson_upper, wilson_interval


def test_zero_event_simultaneous_upper_bound_is_below_calibration_target() -> None:
    upper = clopper_pearson_upper(0, 500, confidence=1 - 0.05 / 10)
    assert 0 < upper < 0.05


def test_pointwise_zero_event_upper_matches_closed_form() -> None:
    upper = clopper_pearson_upper(0, 500)
    assert upper == pytest.approx(1 - 0.05 ** (1 / 500))


def test_wilson_interval_covers_observed_rate_and_rejects_invalid_counts() -> None:
    low, high = wilson_interval(3, 500)
    assert low < 3 / 500 < high
    with pytest.raises(ValueError):
        wilson_interval(501, 500)
