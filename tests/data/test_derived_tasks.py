import numpy as np
import pytest

from shiftlab.data.decision_tasks import (
    binary_action,
    binary_risk,
    bounded_position,
    capacity_allocation,
    multiclass_action,
    selective_action,
)
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


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"horizon": True}, "positive integers"),
        ({"horizon": 1.5}, "positive integers"),
        ({"lookback": False}, "positive integers"),
        ({"lookback": 2.5}, "positive integers"),
        ({"horizon": 8}, "Insufficient series"),
    ],
)
def test_scalar_forecast_task_rejects_invalid_window_parameters(kwargs, message):
    with pytest.raises(ValueError, match=message):
        forecast_task(np.arange(10.0), **kwargs)


def test_scalar_forecast_task_requires_one_dimensional_values():
    with pytest.raises(ValueError, match="one-dimensional"):
        forecast_task(np.zeros((10, 2)))


@pytest.mark.parametrize("builder", [forecast_task, multi_step_forecast_task])
def test_forecast_builders_reject_infinite_observations(builder):
    values = np.arange(12.0)
    values[6] = np.inf
    with pytest.raises(ValueError, match="finite or missing"):
        builder(values)


@pytest.mark.parametrize("task", ["binary", "exceedance", "rare_event", "rare_magnitude"])
@pytest.mark.parametrize("threshold", [np.nan, np.inf, -np.inf])
def test_threshold_tasks_reject_nonfinite_thresholds(task, threshold):
    with pytest.raises(ValueError, match="threshold must be finite"):
        forecast_task(np.arange(20.0), task=task, threshold=threshold)


def test_unknown_forecast_task_fails_before_building_windows():
    with pytest.raises(ValueError, match="Unknown forecast task"):
        forecast_task(np.arange(10.0), task="unknown")


def test_cost_sensitive_and_bounded_actions():
    assert multiclass_action([[0.2, 0.7, 0.1]], [[0, 2, 1], [3, 0, 1], [2, 2, 0]]).tolist() == [1]
    assert bounded_position([2, -2, 0.2], [1, 1, 1], bound=0.5).tolist() == [0.5, -0.5, 0.2]
    assert selective_action([0.01, 0.5, 0.99], 0.2).tolist() == [0, -1, 1]
    assert quantile_loss([1.0, -1.0], [0.0, 0.0], 0.9).tolist() == pytest.approx([0.9, 0.1])
    with pytest.raises(ValueError):
        multiclass_action([[0.2, 0.3]], [[0, 1], [1, 0]])


@pytest.mark.parametrize("probabilities", [[0.2, np.nan], [0.2, np.inf], [-0.1, 0.9], [0.2, 1.1]])
def test_capacity_allocation_rejects_invalid_probabilities(probabilities):
    with pytest.raises(ValueError, match="finite vector in \\[0,1\\]"):
        capacity_allocation(probabilities, 1)


@pytest.mark.parametrize("capacity", [True, 1.5, np.nan, np.inf, -1, 3])
def test_capacity_allocation_rejects_invalid_capacity(capacity):
    with pytest.raises((TypeError, ValueError)):
        capacity_allocation([0.2, 0.8], capacity)


def test_capacity_allocation_is_stable_when_probabilities_tie():
    assert capacity_allocation([0.8, 0.8, 0.2], 1).tolist() == [True, False, False]


@pytest.mark.parametrize("cost", [np.nan, np.inf, -np.inf, -0.1, [0.2]])
def test_selective_action_rejects_invalid_abstention_cost(cost):
    with pytest.raises(ValueError, match="abstention cost"):
        selective_action([0.2, 0.8], cost)


@pytest.mark.parametrize(
    ("risk_aversion", "bound"),
    [(np.nan, 1), (np.inf, 1), (0, 1), (1, np.nan), (1, np.inf), (1, -1), ([1], 1), (1, [1])],
)
def test_bounded_position_rejects_invalid_scalar_parameters(risk_aversion, bound):
    with pytest.raises(ValueError):
        bounded_position([0.5], [1], risk_aversion=risk_aversion, bound=bound)


@pytest.mark.parametrize("probability", [np.nan, np.inf, -np.inf, -0.01, 1.01])
def test_binary_decisions_reject_invalid_probabilities(probability):
    with pytest.raises(ValueError, match="Probabilities must lie in \\[0,1\\]"):
        binary_action(probability)
    with pytest.raises(ValueError, match="Probabilities must lie in \\[0,1\\]"):
        binary_risk(False, probability)


@pytest.mark.parametrize("cost", [np.nan, np.inf, -np.inf, 0.0, -1.0])
@pytest.mark.parametrize("cost_name", ["false_negative", "false_positive"])
def test_binary_decisions_reject_invalid_costs(cost_name, cost):
    with pytest.raises(ValueError, match="costs must be finite and positive"):
        binary_action(0.5, **{cost_name: cost})
    with pytest.raises(ValueError, match="costs must be finite and positive"):
        binary_risk(False, 0.5, **{cost_name: cost})


def test_binary_risk_rejects_nonbinary_actions():
    with pytest.raises(ValueError, match="Actions must contain only"):
        binary_risk([0, 2], [0.2, 0.8])


def test_binary_action_threshold_is_stable_for_large_finite_costs():
    assert binary_action(0.5, false_negative=1e308, false_positive=1e308)
    assert not binary_action(0.49, false_negative=1e308, false_positive=1e308)
