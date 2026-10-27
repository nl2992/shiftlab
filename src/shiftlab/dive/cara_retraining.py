"""Small, testable CARA threshold-policy helpers.

These helpers implement the published threshold/cumulative-threshold/periodic
schedule rules. The EIA-specific staleness score is deliberately computed by
the experiment runner because its feature and feedback contract is task-specific.
"""

from __future__ import annotations

import numpy as np


def _offline_objective(
    scores: np.ndarray,
    losses: np.ndarray,
    *,
    alpha: float,
    periods: range,
    threshold: float,
    cumulative: bool,
) -> tuple[float, int]:
    incumbent = periods.start - 1
    accumulated = 0.0
    updates = 0
    objective = 0.0
    for period in periods:
        score = float(scores[incumbent, period])
        if not np.isfinite(score):
            objective += float(losses[incumbent, period])
            continue
        accumulated = accumulated + score if cumulative else score
        if accumulated > threshold:
            incumbent = period
            accumulated = 0.0
            updates += 1
        objective += float(losses[incumbent, period]) + alpha * (
            incumbent == period and period > periods.start - 1
        )
    return objective, updates


def tune_threshold(
    scores: np.ndarray,
    losses: np.ndarray,
    *,
    alpha: float,
    offline_periods: range,
    cumulative: bool = False,
) -> tuple[float, float, int]:
    """Select CARA-T/CT threshold using only the supplied offline periods."""
    critical_values = [
        float(scores[i, t])
        for t in offline_periods
        for i in range(offline_periods.start - 1, t)
        if np.isfinite(scores[i, t])
    ]
    if cumulative:
        # Include every contiguous active-model score sum that can change the
        # offline cumulative-threshold schedule.
        for model_index in range(offline_periods.start - 1, offline_periods.stop - 1):
            for start in range(max(offline_periods.start, model_index + 1), offline_periods.stop):
                total = 0.0
                for stop in range(start, offline_periods.stop):
                    value = scores[model_index, stop]
                    if not np.isfinite(value):
                        break
                    total += float(value)
                    critical_values.append(total)
    lower_sides = [float(np.nextafter(value, -np.inf)) for value in critical_values]
    candidates = np.unique(np.asarray([-np.inf, np.inf, *critical_values, *lower_sides]))
    choices = [
        (
            *_offline_objective(
                scores,
                losses,
                alpha=alpha,
                periods=offline_periods,
                threshold=float(threshold),
                cumulative=cumulative,
            ),
            float(threshold),
        )
        for threshold in candidates
    ]
    objective, updates, threshold = min(choices, key=lambda row: (row[0], row[1], row[2]))
    return threshold, objective, updates


def tune_periodic(
    losses: np.ndarray,
    *,
    alpha: float,
    offline_periods: range,
) -> tuple[int, int, float, int]:
    """Fit a periodic schedule on offline replay periods only."""
    best: tuple[float, int, int, int] | None = None
    for period in range(1, max(2, len(offline_periods) + 2)):
        for offset in range(period):
            incumbent = offline_periods.start - 1
            objective = 0.0
            updates = 0
            for t in offline_periods:
                if t % period == offset:
                    incumbent = t
                    updates += 1
                objective += float(losses[incumbent, t]) + alpha * int(t % period == offset)
            row = (objective, updates, period, offset)
            if best is None or row < best:
                best = row
    assert best is not None
    return best[2], best[3], best[0], best[1]


def threshold_schedule(
    scores: np.ndarray,
    *,
    initial_model: int,
    periods: range,
    threshold: float,
    cumulative: bool = False,
) -> tuple[list[int], list[float]]:
    """Replay CARA-T or CARA-CT using the score available at each period."""
    incumbent = initial_model
    accumulated = 0.0
    models: list[int] = []
    observed_scores: list[float] = []
    for period in periods:
        score = float(scores[incumbent, period])
        observed_scores.append(score)
        if not np.isfinite(score):
            models.append(incumbent)
            continue
        accumulated = accumulated + score if cumulative else score
        if accumulated > threshold:
            incumbent = period
            accumulated = 0.0
        models.append(incumbent)
    return models, observed_scores


def periodic_schedule(
    *,
    initial_model: int,
    periods: range,
    period: int,
    offset: int,
) -> list[int]:
    """Replay a calendar-period schedule learned on the offline block."""
    if period < 1 or not 0 <= offset < period:
        raise ValueError("period must be positive and offset must lie in [0, period)")
    incumbent = initial_model
    models: list[int] = []
    for t in periods:
        if t % period == offset:
            incumbent = t
        models.append(incumbent)
    return models
