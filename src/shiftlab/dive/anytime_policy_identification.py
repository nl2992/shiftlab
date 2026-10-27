"""Anytime-valid identification of a finite policy class from logged data.

Independent implementation of the candidate-set construction in Molitor
(2026), using the LIL confidence sequence in Waudby-Smith et al. (2024).
The API separates doubly robust pseudo-outcomes, one-sided value bounds, and
the finite-class elimination rule so each component can be audited.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def bounded_dr_pseudo_outcomes(
    actions: NDArray[np.integer],
    rewards: FloatArray,
    logging_probabilities: FloatArray,
    target_policies: FloatArray,
    reward_predictions: FloatArray,
    truncation: float,
) -> tuple[FloatArray, FloatArray]:
    """Return lower and mirrored upper DR pseudo-outcomes for every policy.

    ``target_policies`` may have shape ``(M, A)`` or ``(T, M, A)``. The
    action-specific importance ratio is used when integrating the truncated
    reward model over target actions. This is essential for the conditional
    mean cancellation in the published construction.
    """
    action = np.asarray(actions, dtype=np.int64)
    reward = np.asarray(rewards, dtype=np.float64)
    h = np.asarray(logging_probabilities, dtype=np.float64)
    pi = np.asarray(target_policies, dtype=np.float64)
    rhat = np.asarray(reward_predictions, dtype=np.float64)

    if action.ndim != 1 or reward.shape != action.shape:
        raise ValueError("actions and rewards must be same-length vectors")
    n = len(action)
    if h.ndim != 2 or h.shape[0] != n:
        raise ValueError("logging_probabilities must have shape (T, A)")
    n_actions = h.shape[1]
    if rhat.shape != h.shape:
        raise ValueError("reward_predictions must have shape (T, A)")
    if pi.ndim == 2:
        if pi.shape[1] != n_actions:
            raise ValueError("target policy action dimension does not match logger")
        pi = np.broadcast_to(pi[None, :, :], (n, *pi.shape))
    elif pi.ndim != 3 or pi.shape[0] != n or pi.shape[2] != n_actions:
        raise ValueError("target_policies must have shape (M, A) or (T, M, A)")
    if not np.isfinite(truncation) or truncation < 0:
        raise ValueError("truncation must be finite and nonnegative")
    if np.any(~np.isfinite(h)) or np.any(h < 0) or not np.allclose(h.sum(-1), 1):
        raise ValueError("logging probabilities must be finite distributions")
    if np.any(~np.isfinite(pi)) or np.any(pi < 0) or not np.allclose(pi.sum(-1), 1):
        raise ValueError("target policies must be finite distributions")
    if np.any(~np.isfinite(reward)) or np.any((reward < 0) | (reward > 1)):
        raise ValueError("rewards must lie in [0, 1]")
    if np.any(~np.isfinite(rhat)) or np.any((rhat < 0) | (rhat > 1)):
        raise ValueError("reward predictions must lie in [0, 1]")
    if np.any((action < 0) | (action >= n_actions)):
        raise ValueError("action index is outside the logged action space")

    rows = np.arange(n)
    h_observed = h[rows, action]
    if np.any(h_observed <= 0):
        raise ValueError("observed actions must have positive logging probability")
    unsupported = (pi > 0) & (h[:, None, :] <= 0)
    if np.any(unsupported):
        raise ValueError("target policy is not supported by the logger")

    weight_by_action = np.divide(
        pi,
        h[:, None, :],
        out=np.zeros_like(pi),
        where=h[:, None, :] > 0,
    )
    weight_observed = weight_by_action[rows, :, action]
    cap_by_action = np.divide(
        truncation,
        weight_by_action,
        out=np.full_like(weight_by_action, np.inf),
        where=weight_by_action > 0,
    )
    cap_observed = np.divide(
        truncation,
        weight_observed,
        out=np.full_like(weight_observed, np.inf),
        where=weight_observed > 0,
    )

    model_lower = np.minimum(rhat[:, None, :], cap_by_action)
    model_upper = np.minimum(1.0 - rhat[:, None, :], cap_by_action)
    integrated_lower = np.sum(pi * model_lower, axis=-1)
    integrated_upper = np.sum(pi * model_upper, axis=-1)
    rhat_observed = rhat[rows, action][:, None]

    lower = (
        weight_observed * (reward[:, None] - np.minimum(rhat_observed, cap_observed))
        + integrated_lower
    )
    upper = (
        weight_observed * ((1.0 - reward[:, None]) - np.minimum(1.0 - rhat_observed, cap_observed))
        + integrated_upper
    )
    return lower, upper


def lil_value_bounds(
    pseudo_outcomes: FloatArray,
    alpha: float,
    truncation: float,
    *,
    initial_mean: float | None = None,
) -> FloatArray:
    """Compute the paper's one-sided LIL confidence bound at every time.

    With lower pseudo-outcomes this returns lower bounds for policy value.
    With mirrored upper pseudo-outcomes it returns lower bounds for the
    complementary value, to be transformed as ``1 - result``.
    """
    phi = np.asarray(pseudo_outcomes, dtype=np.float64)
    if phi.ndim != 1 or len(phi) == 0 or np.any(~np.isfinite(phi)):
        raise ValueError("pseudo_outcomes must be a nonempty finite vector")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    if not np.isfinite(truncation) or truncation < 0:
        raise ValueError("truncation must be finite and nonnegative")
    if np.any(phi < -truncation - 1e-12):
        raise ValueError("pseudo_outcomes violate the required lower bound -truncation")

    scale = 1.0 + truncation
    cap = 1.0 / scale
    xi = phi / scale
    t = np.arange(1, len(phi) + 1, dtype=np.float64)
    running_mean = np.minimum(np.cumsum(xi) / t, cap)
    lagged_mean = np.empty_like(xi)
    lagged_mean[0] = cap / 2.0 if initial_mean is None else initial_mean
    if not 0 <= lagged_mean[0] <= cap:
        raise ValueError("initial_mean must lie in [0, 1/(1+truncation)]")
    lagged_mean[1:] = running_mean[:-1]
    variance = np.maximum(np.cumsum((xi - lagged_mean) ** 2), 1.0)
    ell = 2.0 * np.log(np.log(variance) + 1.0) + np.log(1.65 / alpha)
    correction = np.sqrt(2.13 * ell * variance + 1.76 * ell**2) / t + 1.33 * ell / t
    return np.maximum(scale * (np.cumsum(xi) / t - correction), 0.0)


def optimal_policy_set(lower: FloatArray, upper: FloatArray) -> BoolArray:
    """Return the policies not ruled out by simultaneous value bounds."""
    lower_array = np.asarray(lower, dtype=np.float64)
    upper_array = np.asarray(upper, dtype=np.float64)
    if lower_array.ndim != 2 or upper_array.shape != lower_array.shape:
        raise ValueError("lower and upper must have the same shape (M, T)")
    if lower_array.shape[0] == 0 or lower_array.shape[1] == 0:
        raise ValueError("at least one policy and one time point are required")
    if np.any(~np.isfinite(lower_array)) or np.any(~np.isfinite(upper_array)):
        raise ValueError("bounds must be finite")
    return upper_array >= np.max(lower_array, axis=0, keepdims=True)


def optimal_policy_stopping_time(lower: FloatArray, upper: FloatArray) -> int:
    """Return the first strict unique-policy separation time, or ``T+1``."""
    lower_array = np.asarray(lower, dtype=np.float64)
    upper_array = np.asarray(upper, dtype=np.float64)
    if lower_array.ndim != 2 or upper_array.shape != lower_array.shape:
        raise ValueError("lower and upper must have the same shape (M, T)")
    m, horizon = lower_array.shape
    if m == 0 or horizon == 0:
        raise ValueError("at least one policy and one time point are required")
    if np.any(~np.isfinite(lower_array)) or np.any(~np.isfinite(upper_array)):
        raise ValueError("bounds must be finite")
    if m == 1:
        return horizon + 1
    for t in range(horizon):
        for policy in range(m):
            other_upper = np.max(np.delete(upper_array[:, t], policy))
            if lower_array[policy, t] > other_upper:
                return t + 1
    return horizon + 1
