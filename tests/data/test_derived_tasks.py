import numpy as np
import pytest

from shiftlab.data.decision_tasks import bounded_position, multiclass_action, selective_action
from shiftlab.data.tasks import TASKS, forecast_task, multi_step_forecast_task, quantile_loss


def test_missing_classification_targets_remain_missing():
    values = np.array([1.0, 2.0, 3.0, np.nan, 5.0, 6.0])
    for task in ["binary", "exceedance", "rare_event", "multiclass"]:
        _, y, _, outcome = forecast_task(values, lookback=2, task=task, class_boundaries=[2.0, 4.0])
        assert np.isnan(y[outcome == 3]).all()


def test_derived_tasks_use_only_past_features():
    original = np.arange(20, dtype=float)
    changed = original.copy()
    changed[12:] += 1000
    for task in TASKS:
        X, _y, t, label = forecast_task(
            original, horizon=2, lookback=3, task=task, class_boundaries=[5, 10]
        )
        if task == "multi_step":
            assert np.array_equal(label, t[:, None] + np.arange(1, 3))
            continue
        other, _, _, _ = forecast_task(
            changed, horizon=2, lookback=3, task=task, class_boundaries=[5, 10]
        )
        assert np.array_equal(X[t < 12], other[t < 12])
        assert (label == t + 2).all()
    _, magnitude, _, _ = forecast_task(original, lookback=3, task="rare_magnitude", threshold=10)
    assert np.array_equal(magnitude, np.maximum(original[3:] - 10, 0))


def test_multi_step_forecasts_have_past_only_features_horizon_indices_and_masks():
    values = np.arange(20, dtype=float)
    values[8] = np.nan
    X, targets, origins, outcome_indices = multi_step_forecast_task(values, horizon=3, lookback=4)
    assert TASKS["multi_step"].kind == "regression"
    assert targets.shape == (len(origins), 3)
    assert outcome_indices.shape == targets.shape
    assert np.array_equal(outcome_indices, origins[:, None] + np.arange(1, 4))
    assert np.array_equal(np.isfinite(targets), outcome_indices != 8)
    assert np.array_equal(
        X[origins < 8], np.stack([values[i - 3 : i + 1] for i in origins[origins < 8]])
    )
    changed = values.copy()
    changed[12:] += 1000
    other_X, _, other_origins, _ = multi_step_forecast_task(changed, horizon=3, lookback=4)
    assert np.array_equal(X[origins < 12], other_X[other_origins < 12], equal_nan=True)


def test_multi_step_task_rejects_invalid_horizon_and_short_series():
    with pytest.raises(ValueError, match="positive integers"):
        multi_step_forecast_task(np.arange(10), horizon=True)
    with pytest.raises(ValueError, match="Insufficient series"):
        multi_step_forecast_task(np.arange(6), horizon=3, lookback=4)


def test_cost_sensitive_and_bounded_actions():
    assert multiclass_action([[0.2, 0.7, 0.1]], [[0, 2, 1], [3, 0, 1], [2, 2, 0]]).tolist() == [1]
    assert bounded_position([2, -2, 0.2], [1, 1, 1], bound=0.5).tolist() == [0.5, -0.5, 0.2]
    assert selective_action([0.01, 0.5, 0.99], 0.2).tolist() == [0, -1, 1]
    assert quantile_loss([1.0, -1.0], [0.0, 0.0], 0.9).tolist() == pytest.approx([0.9, 0.1])
    with pytest.raises(ValueError):
        multiclass_action([[0.2, 0.3]], [[0, 1], [1, 0]])
