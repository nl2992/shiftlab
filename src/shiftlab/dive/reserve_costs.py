"""Imposed reserve-procurement costs for the EIA paired decision task (research costs, not tariffs)."""

from __future__ import annotations

import numpy as np

COST_SHORTFALL = 5.0
COST_OVER_PROCUREMENT = 1.0
TAU_QUANTILE = 0.90


def reserve_actions(prediction: np.ndarray, tau: float) -> np.ndarray:
    """Procure reserve (1) when forecast demand exceeds the frozen threshold."""
    values = np.asarray(prediction, dtype=float)
    if not np.isfinite(values).all() or not np.isfinite(tau):
        raise ValueError("predictions and tau must be finite")
    return (values > tau).astype(np.int8)


def decision_cost(action: np.ndarray, demand: np.ndarray, tau: float) -> np.ndarray:
    """Shortfall costs 5 when demand exceeds tau unprocured; idle reserve costs 1."""
    acts = np.asarray(action)
    outcome = np.asarray(demand, dtype=float)
    if acts.shape != outcome.shape or not np.isin(acts, (0, 1)).all():
        raise ValueError("actions must be binary and match demand")
    if not np.isfinite(outcome).all() or not np.isfinite(tau):
        raise ValueError("demand and tau must be finite")
    high = outcome > tau
    return np.where(
        acts == 1, np.where(high, 0.0, COST_OVER_PROCUREMENT), np.where(high, COST_SHORTFALL, 0.0)
    )


def paired_cost(
    deployed_action: np.ndarray, reference_action: np.ndarray, demand: np.ndarray, tau: float
) -> np.ndarray:
    """Z = c(deployed) - c(reference); zero whenever the actions agree (Assumption L)."""
    return decision_cost(deployed_action, demand, tau) - decision_cost(
        reference_action, demand, tau
    )
