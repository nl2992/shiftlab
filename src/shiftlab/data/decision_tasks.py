"""Artificial research utilities, never asserted to be application ground truth."""

import numpy as np


def binary_action(probability, false_negative=5.0, false_positive=1.0):
    if np.any(np.asarray(false_negative) <= 0) or np.any(np.asarray(false_positive) <= 0):
        raise ValueError("Costs must be positive")
    return np.asarray(probability) >= np.asarray(false_positive) / (
        np.asarray(false_positive) + false_negative
    )


def binary_risk(action, probability, false_negative=5.0, false_positive=1.0):
    return np.where(
        action,
        false_positive * (1 - np.asarray(probability)),
        false_negative * np.asarray(probability),
    )


def capacity_allocation(probabilities, capacity: int):
    if not 0 <= capacity <= len(probabilities):
        raise ValueError("Capacity outside [0,n]")
    result = np.zeros(len(probabilities), dtype=bool)
    if capacity:
        result[np.argsort(probabilities)[-capacity:]] = True
    return result


def selective_action(probabilities, abstention_cost=0.2):
    p = np.asarray(probabilities)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)) or abstention_cost < 0:
        raise ValueError("Probabilities must lie in [0,1] and abstention cost must be nonnegative")
    action = (p >= 0.5).astype(int)
    return np.where(np.minimum(p, 1 - p) > abstention_cost, -1, action)


def multiclass_action(probabilities, cost_matrix):
    """Finite action class: cost_matrix[true_class, action]; utilities are externally specified."""
    p = np.asarray(probabilities, dtype=float)
    cost = np.asarray(cost_matrix, dtype=float)
    if (
        p.ndim != 2
        or cost.shape != (p.shape[1], p.shape[1])
        or not np.isfinite(p).all()
        or not np.isfinite(cost).all()
    ):
        raise ValueError("Need finite class-probability rows and a matching cost matrix")
    if np.any(p < 0) or not np.allclose(p.sum(axis=1), 1) or np.any(cost < 0):
        raise ValueError("Probabilities must sum to one and costs must be nonnegative")
    return np.argmin(p @ cost, axis=1)


def bounded_position(mean, variance, risk_aversion=1.0, bound=1.0):
    """Artificial mean-variance decision: maximize a*mean - .5*risk_aversion*a^2*variance.

    This imposed research objective does not include market microstructure, liquidity or
    realistic trading costs and must not be presented as application-grounded financial utility.
    """
    mean, variance = np.asarray(mean, dtype=float), np.asarray(variance, dtype=float)
    if (
        not np.isfinite(mean).all()
        or not np.isfinite(variance).all()
        or np.any(variance <= 0)
        or risk_aversion <= 0
        or bound < 0
    ):
        raise ValueError(
            "Finite means, positive variances/risk aversion and nonnegative bound required"
        )
    return np.clip(mean / (risk_aversion * variance), -bound, bound)
