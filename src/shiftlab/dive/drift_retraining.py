"""Mature-feedback replay helpers for drift-triggered retraining baselines."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def replay_drift_schedule(
    detector: Any,
    losses_by_model_period: Mapping[tuple[int, int], Sequence[float]],
    *,
    input_transform: Callable[[float], float | int] = float,
    initial_model_period: int,
    online_start_period: int,
) -> tuple[list[int], list[bool], list[int]]:
    """Warm a detector on prior mature feedback, then replay online periods.

    `losses_by_model_period[(i, t)]` contains losses of model `i` on period
    `t`'s feedback, and may contain only feedback available by that period's
    decision boundary. The model selected on an alarm is the model trained for
    that period. The declared online incumbent is installed at the end of the
    warm-up period while preserving detector state.
    """
    if initial_model_period < 1 or online_start_period <= initial_model_period:
        raise ValueError("online period must follow a positive warm-up model period")
    incumbent = 0
    model_schedule: list[int] = []
    alarms: list[bool] = []
    processed: list[int] = []
    final_period = max((period for _, period in losses_by_model_period), default=-1)
    if final_period < online_start_period:
        raise ValueError("loss stream does not reach the first online period")
    for period in range(1, final_period + 1):
        detected = False
        count = 0
        for loss in losses_by_model_period.get((incumbent, period), ()):
            detector.update(input_transform(float(loss)))
            detected = detected or bool(detector.drift_detected)
            count += 1
        if detected:
            incumbent = period
        if period == initial_model_period:
            incumbent = initial_model_period
        if period >= online_start_period:
            model_schedule.append(incumbent)
            alarms.append(detected)
            processed.append(count)
    return model_schedule, alarms, processed
