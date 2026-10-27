"""Small design helpers for stratified paired-harm monitoring.

These helpers construct fixed allocations and binary outcome mixtures. They
do not implement a stream, an allocation optimizer, or a monitoring procedure.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def pilot_alpha_weights(counts: ArrayLike) -> dict[str, NDArray[np.float64]]:
    """Return equal, smoothed-volume, and smoothed-rare-stratum weights.

    ``counts`` is a finite, nonnegative integer vector from a pilot sample.
    Every returned vector is strictly positive and sums to one. The formulas
    reduce exactly to the existing two-stratum allocations when K is two.
    """
    raw_counts = np.asarray(counts)
    if raw_counts.ndim != 1 or raw_counts.size == 0:
        raise ValueError("counts must be a nonempty one-dimensional vector")
    try:
        numeric_counts = raw_counts.astype(np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("counts must be finite nonnegative integers") from exc
    if (
        not np.all(np.isfinite(numeric_counts))
        or np.any(numeric_counts < 0)
        or np.any(numeric_counts != np.floor(numeric_counts))
        or numeric_counts.sum() <= 0
        or not np.isfinite(numeric_counts.sum())
    ):
        raise ValueError("counts must be finite nonnegative integers with positive sum")

    n_strata = numeric_counts.size
    volume = (numeric_counts + 0.5) / (numeric_counts.sum() + 0.5 * n_strata)
    rare = 1.0 / (numeric_counts + 0.5)
    rare /= rare.sum()
    return {
        "equal_alpha": np.full(n_strata, 1.0 / n_strata),
        "volume_weighted_alpha": volume,
        "rare_protected_alpha": rare,
    }


def null_centered_means(
    action: ArrayLike,
    reference_action: ArrayLike,
    epsilon: ArrayLike,
) -> NDArray[np.float64]:
    """Return centered null means: zero on disagreements, ``-epsilon`` on ties."""
    action_array = np.asarray(action)
    reference_array = np.asarray(reference_action)
    epsilon_array = np.asarray(epsilon, dtype=np.float64)
    if not np.all(np.isfinite(epsilon_array)):
        raise ValueError("epsilon must be finite")
    if not np.all(np.isin(action_array, (0, 1))) or not np.all(np.isin(reference_array, (0, 1))):
        raise ValueError("actions must be binary")
    try:
        action_b, reference_b, epsilon_b = np.broadcast_arrays(
            action_array, reference_array, epsilon_array
        )
    except ValueError as exc:
        raise ValueError("action, reference_action, and epsilon must broadcast") from exc
    return np.where(action_b != reference_b, 0.0, -epsilon_b).astype(np.float64)


def binary_outcome_probability(
    action: ArrayLike,
    reference_action: ArrayLike,
    false_negative_cost: ArrayLike,
    false_positive_cost: ArrayLike,
    epsilon: ArrayLike,
    centered_mean: ArrayLike,
) -> NDArray[np.float64]:
    """Solve for ``P(Y=1)`` yielding a requested centered paired-cost mean.

    For binary actions ``a`` and ``b``, the uncentered paired cost is
    ``z0 = fp * (a-b)`` for ``Y=0`` and ``z1 = fn * (b-a)`` for ``Y=1``.
    The centered score is paired cost minus ``epsilon``; hence
    ``p = (epsilon + centered_mean - z0) / (z1-z0)``. Infeasible targets are
    rejected. For agreement (or any zero denominator), the score is constant,
    so the target must equal ``-epsilon`` and this helper returns ``p=0.5``.

    Values within 1e-12 of the [0, 1] probability interval are clipped to its
    endpoint to absorb floating-point roundoff; farther-out values are rejected.
    """
    action_array = np.asarray(action)
    reference_array = np.asarray(reference_action)
    fn_array = np.asarray(false_negative_cost, dtype=np.float64)
    fp_array = np.asarray(false_positive_cost, dtype=np.float64)
    epsilon_array = np.asarray(epsilon, dtype=np.float64)
    mean_array = np.asarray(centered_mean, dtype=np.float64)
    if not np.all(np.isin(action_array, (0, 1))) or not np.all(np.isin(reference_array, (0, 1))):
        raise ValueError("actions must be binary")
    for name, values in (
        ("false_negative_cost", fn_array),
        ("false_positive_cost", fp_array),
        ("epsilon", epsilon_array),
        ("centered_mean", mean_array),
    ):
        if not np.all(np.isfinite(values)):
            raise ValueError(f"{name} must be finite")
    if np.any(fn_array < 0) or np.any(fp_array < 0):
        raise ValueError("costs must be nonnegative")
    action_array = action_array.astype(np.float64, copy=False)
    reference_array = reference_array.astype(np.float64, copy=False)
    try:
        action_b, reference_b, fn_b, fp_b, epsilon_b, mean_b = np.broadcast_arrays(
            action_array, reference_array, fn_array, fp_array, epsilon_array, mean_array
        )
    except ValueError as exc:
        raise ValueError("all inputs must be broadcast-compatible") from exc

    z0 = fp_b * (action_b - reference_b)
    z1 = fn_b * (reference_b - action_b)
    denominator = z1 - z0
    numerator = epsilon_b + mean_b - z0
    probability = np.full(numerator.shape, 0.5, dtype=np.float64)
    informative = denominator != 0
    constant_score = ~informative
    if np.any(np.abs(numerator[constant_score]) > 1e-12):
        raise ValueError("requested centered mean is infeasible for a constant paired cost")
    probability[informative] = numerator[informative] / denominator[informative]
    tolerance = 1e-12
    if np.any(probability < -tolerance) or np.any(probability > 1.0 + tolerance):
        raise ValueError("requested centered mean implies an infeasible outcome probability")
    return np.clip(probability, 0.0, 1.0)
