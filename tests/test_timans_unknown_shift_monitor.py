import numpy as np
import pytest

from scripts.reproduce_timans_risk_monitor_paired_cost import _timans_logs


@pytest.mark.parametrize("rule", ("approx_grapa", "grapa"))
def test_timans_monitor_is_zero_at_threshold(rule: str) -> None:
    score = np.full(160, 0.5)
    np.testing.assert_array_equal(_timans_logs(score, rule=rule), np.zeros_like(score))


@pytest.mark.parametrize("rule", ("approx_grapa", "grapa"))
def test_timans_monitor_prefix_does_not_depend_on_future_scores(rule: str) -> None:
    score = np.linspace(0.05, 0.95, 180)
    changed = score.copy()
    changed[120:] = changed[120:][::-1]
    original_log = _timans_logs(score, rule=rule)
    changed_log = _timans_logs(changed, rule=rule)
    np.testing.assert_array_equal(original_log[:120], changed_log[:120])


@pytest.mark.parametrize("score", (np.array([]), np.array([0.2, np.nan]), np.array([-0.1, 0.5])))
def test_timans_monitor_rejects_invalid_scores(score: np.ndarray) -> None:
    with pytest.raises(ValueError):
        _timans_logs(score, rule="approx_grapa")
