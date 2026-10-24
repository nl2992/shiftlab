import numpy as np
import pytest

from shiftlab.dive.eprocess import BoundedMeanEProcess, PredictableBoundMeanEProcess
from shiftlab.dive.predictable_bound_replay import first_crossing, replay_mixture_log_e


def test_fixed_bound_replay_matches_online_mixture_process():
    values = np.array([-0.2, 0.1, 0.3, -0.05, 0.4])
    process = BoundedMeanEProcess(bound=1.0, alpha=0.1)
    online = np.array([process.update(float(value)) for value in values])
    replay = replay_mixture_log_e(values, 1.0, alpha=0.1)
    np.testing.assert_allclose(replay, online, rtol=0, atol=1e-14)


def test_history_predictable_bounds_replay_online_process():
    values = np.array([-0.1, 0.2, -0.05, 0.3])
    bounds = np.array([1.0, 0.8, 0.7, 0.6])
    process = PredictableBoundMeanEProcess(alpha=0.05)
    online = np.array(
        [process.update(float(value), bound=float(bound)) for value, bound in zip(values, bounds)]
    )
    replay = replay_mixture_log_e(values, bounds, alpha=0.05)
    np.testing.assert_allclose(replay, online, rtol=0, atol=1e-14)


def test_replay_rejects_increment_outside_declared_bound():
    with pytest.raises(ValueError, match="outside"):
        replay_mixture_log_e(np.array([1.1]), 1.0, alpha=0.05)


def test_first_crossing_is_zero_based_or_none():
    assert first_crossing(np.array([0.0, 2.0, 3.0]), alpha=0.1) == 2
    assert first_crossing(np.array([0.0, 1.0]), alpha=0.05) is None
