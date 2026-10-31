"""Matched-constraint threshold calibration: P(any alarm by T) = alpha on a declared null generator."""

from __future__ import annotations

import numpy as np

from .feedback import LabelQueue
from .monitors import Target, nominal_log_threshold  # noqa: F401 (re-exported)


def null_maxima(monitor_factory, null_generator, feedback, n_cal: int, seed: int) -> np.ndarray:
    """Per-episode max over the horizon of the monitor statistic on null data (monitor alone; with
    Setting-A labels the monitor input does not depend on actions)."""
    batch, _ = null_generator.generate(seed, n_cal, feedback, null=True)
    mon = monitor_factory(n_cal)
    queue, target = LabelQueue(batch, feedback.d), Target(mon.target, n_cal, mon.cal)
    mx = np.full(n_cal, -np.inf)
    for s in range(batch.T):
        x, v = target.transform(queue.at(s))
        mon.update(x, v)
        mx = np.maximum(mx, mon.statistic)
    return mx


def calibrate_threshold(
    monitor_factory,
    null_generator,
    feedback,
    alpha: float = 0.05,
    n_cal: int = 2000,
    seed_base: int = 5_000_000,
) -> float:
    """(1-alpha) 'higher' quantile of the null max statistic, so P(max > thr) <= alpha (alarm = stat > thr)."""
    mx = null_maxima(monitor_factory, null_generator, feedback, n_cal, seed_base)
    return float(np.quantile(mx, 1.0 - alpha, method="higher"))
