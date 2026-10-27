import numpy as np

from shiftlab.dive.cara_retraining import (
    periodic_schedule,
    threshold_schedule,
    tune_periodic,
    tune_threshold,
)
from shiftlab.dive.drift_retraining import replay_drift_schedule


def test_threshold_and_cumulative_threshold_update_only_from_current_score() -> None:
    scores = np.zeros((4, 4), dtype=np.float64)
    scores[0, 1:] = [0.4, 0.2, 0.2]
    scores[1, 2:] = [0.2, 0.2]
    scores[2, 3] = 0.1

    direct, observed = threshold_schedule(
        scores, initial_model=0, periods=range(1, 4), threshold=0.3
    )
    cumulative, _ = threshold_schedule(
        scores, initial_model=0, periods=range(1, 4), threshold=0.3, cumulative=True
    )

    assert direct == [1, 1, 1]
    assert cumulative == [1, 1, 3]
    assert observed == [0.4, 0.2, 0.2]


def test_offline_tuners_choose_within_supplied_periods() -> None:
    losses = np.full((5, 5), np.nan)
    losses[np.triu_indices(5)] = 0.8
    losses[1, 1:] = 0.1
    losses[3, 3:] = 0.2
    scores = np.full((5, 5), np.nan)
    scores[np.triu_indices(5)] = 0.0
    scores[0, 1:] = [0.5, 0.5, 0.5, 0.5]
    scores[1, 2:] = 0.0
    scores[2, 3:] = 0.0
    scores[3, 4] = 0.0

    threshold, objective, _ = tune_threshold(scores, losses, alpha=0.0, offline_periods=range(1, 4))
    period, offset, periodic_objective, _ = tune_periodic(
        losses, alpha=0.0, offline_periods=range(1, 4)
    )

    assert threshold < 0.5
    assert objective < 1.0
    assert period >= 1
    assert 0 <= offset < period
    assert periodic_objective < 1.0


def test_periodic_schedule_uses_absolute_period_clock() -> None:
    schedule = periodic_schedule(
        initial_model=6,
        periods=range(7, 11),
        period=3,
        offset=1,
    )
    assert schedule == [7, 7, 7, 10]


def test_drift_replay_uses_only_active_model_feedback_and_forces_frozen_start() -> None:
    class Detector:
        drift_detected = False

        def update(self, value: float) -> None:
            self.drift_detected = value >= 0.9

    losses = {
        (0, 1): [0.2],
        (0, 2): [0.3],
        (0, 3): [0.9],
        (3, 4): [0.1],
        (3, 5): [0.1],
        (6, 6): [0.2],
        (6, 7): [0.1],
        (6, 8): [0.9],
        (8, 9): [0.1],
    }

    models, alarms, counts = replay_drift_schedule(
        Detector(), losses, initial_model_period=6, online_start_period=7
    )

    assert models == [6, 8, 8]
    assert alarms == [False, True, False]
    assert counts == [1, 1, 1]
