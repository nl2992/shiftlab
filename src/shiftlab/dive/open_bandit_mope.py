"""Small deterministic helpers for the registered OBD/MOPE replay."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float64]


def choose_best_item(
    item_ids: IntArray,
    positions: IntArray,
    clicks: IntArray,
    *,
    target_position: int = 1,
    n_items: int = 80,
) -> tuple[int, IntArray, FloatArray]:
    """Select the highest training click-rate item; ties go to the lowest ID."""
    item_ids = np.asarray(item_ids, dtype=np.int64)
    positions = np.asarray(positions, dtype=np.int64)
    clicks = np.asarray(clicks, dtype=np.int64)
    if item_ids.ndim != 1 or positions.ndim != 1 or clicks.ndim != 1:
        raise ValueError("item_ids, positions, and clicks must be one-dimensional")
    if not (len(item_ids) == len(positions) == len(clicks)) or len(item_ids) == 0:
        raise ValueError("training arrays must have equal, nonzero lengths")
    if n_items <= 0 or target_position not in (1, 2, 3):
        raise ValueError("n_items must be positive and target_position must be 1, 2, or 3")
    if np.any((item_ids < 0) | (item_ids >= n_items)):
        raise ValueError("item IDs are outside the declared action set")
    if np.any(~np.isin(positions, [1, 2, 3])):
        raise ValueError("positions must be one of 1, 2, or 3")
    if np.any(~np.isin(clicks, [0, 1])):
        raise ValueError("clicks must be binary")

    mask = positions == target_position
    if not mask.any():
        raise ValueError("training data contain no rows at the target position")
    counts = np.bincount(item_ids[mask], minlength=n_items).astype(np.int64)
    click_totals = np.bincount(
        item_ids[mask], weights=clicks[mask].astype(np.float64), minlength=n_items
    ).astype(np.float64)
    if np.any(counts == 0):
        raise ValueError("every target action must have training support")
    rates = click_totals / counts
    return int(np.argmax(rates)), counts, click_totals


def build_mope_stream(
    item_ids: IntArray,
    clicks: IntArray,
    propensities: FloatArray,
    *,
    target_item: int,
    n_items: int = 80,
) -> tuple[FloatArray, FloatArray]:
    """Build `(importance ratio, reward)` and candidate-minus-logger scores."""
    item_ids = np.asarray(item_ids, dtype=np.int64)
    clicks = np.asarray(clicks, dtype=np.int64)
    propensities = np.asarray(propensities, dtype=np.float64)
    if item_ids.ndim != 1 or clicks.ndim != 1 or propensities.ndim != 1:
        raise ValueError("evaluation arrays must be one-dimensional")
    if not (len(item_ids) == len(clicks) == len(propensities)) or len(item_ids) == 0:
        raise ValueError("evaluation arrays must have equal, nonzero lengths")
    if not 0 <= target_item < n_items:
        raise ValueError("target_item is outside the declared action set")
    if np.any((item_ids < 0) | (item_ids >= n_items)):
        raise ValueError("item IDs are outside the declared action set")
    if np.any(~np.isin(clicks, [0, 1])):
        raise ValueError("clicks must be binary")
    expected_propensity = 1.0 / n_items
    if not np.allclose(propensities, expected_propensity, rtol=0.0, atol=1e-12):
        raise ValueError("Random logger propensities do not match the declared 1/n action design")

    reward = clicks.astype(np.float64)
    weight = (item_ids == target_item).astype(np.float64) / expected_propensity
    return np.column_stack((weight, reward)), weight * reward - reward


def fixed_horizon_hoeffding_lower(scores: FloatArray, *, alpha: float, range_width: float) -> float:
    """One-sided Hoeffding lower bound for a fixed sample size and known range."""
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or scores.size == 0 or not np.isfinite(scores).all():
        raise ValueError("scores must be a nonempty finite vector")
    if not 0.0 < alpha < 1.0 or range_width <= 0.0:
        raise ValueError("alpha must be in (0, 1) and range_width must be positive")
    return float(scores.mean() - range_width * np.sqrt(np.log(1.0 / alpha) / (2.0 * scores.size)))


def validate_mope_path(lower: FloatArray, upper: FloatArray, expected_length: int) -> IntArray:
    """Validate reference MOPE path shape/order and return empty-set indices."""
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    if lower.shape != (expected_length,) or upper.shape != (expected_length,):
        raise ValueError("MOPE confidence paths have an unexpected length")
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise ValueError("MOPE confidence paths contain non-finite values")
    if np.any(np.diff(lower) < -1e-9) or np.any(np.diff(upper) > 1e-9):
        raise ValueError("MOPE confidence paths are not nested monotonically")
    return np.flatnonzero(lower > upper + 1e-9)
