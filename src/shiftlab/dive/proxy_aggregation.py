"""Predictable online aggregation of bounded decision-loss proxies."""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


class PredictableProxyHedge:
    """Exponentially aggregate proxy experts using queried, IPW squared losses.

    Before each event, ``weights`` depend only on labels observed previously. A
    caller forms the current proxy as their convex combination, processes the
    outcome if queried, and then calls :meth:`observe` to update weights for the
    next event. Since each expert and the mixture are bounded by ``bound``, the
    prediction-powered correction has the same global support guarantee as any
    other pre-outcome proxy. This class does not itself establish a monitor's
    null or handle delayed labels; callers must update only when feedback arrives.
    """

    def __init__(
        self,
        *,
        n_experts: int,
        bound: float,
        min_propensity: float,
        learning_rate: float | None = None,
    ) -> None:
        if isinstance(n_experts, bool) or not isinstance(n_experts, int) or n_experts < 1:
            raise ValueError("n_experts must be a positive integer")
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(min_propensity) or not 0 < min_propensity <= 1:
            raise ValueError("min_propensity must lie in (0, 1]")
        eta = min_propensity / 2 if learning_rate is None else learning_rate
        if not np.isfinite(eta) or not 0 < eta <= min_propensity:
            raise ValueError("learning_rate must lie in (0, min_propensity]")
        self.n_experts = n_experts
        self.bound = float(bound)
        self.min_propensity = float(min_propensity)
        self.learning_rate = float(eta)
        self._log_weights = np.full(n_experts, -np.log(n_experts), dtype=float)
        self.n_updates = 0

    @property
    def weights(self) -> np.ndarray:
        """Return a copy of the predictable, normalized expert weights."""
        return np.exp(self._log_weights)

    def predict(self, expert_values: np.ndarray) -> float:
        """Combine pre-outcome expert predictions with current weights."""
        values = self._validate_experts(expert_values)
        return float(np.dot(self.weights, values))

    def observe(
        self,
        expert_values: np.ndarray,
        observed_value: float,
        propensity: float,
    ) -> None:
        """Update after a queried label arrives using an IPW squared-loss vector."""
        values = self._validate_experts(expert_values)
        if not np.isfinite(observed_value) or abs(observed_value) > self.bound + 1e-12:
            raise ValueError("observed_value must be finite and inside the proxy bound")
        if not np.isfinite(propensity) or propensity < self.min_propensity or propensity > 1:
            raise ValueError("propensity must lie in [min_propensity, 1]")
        losses = ((observed_value - values) / (2 * self.bound)) ** 2
        ipw_losses = losses / propensity
        if np.any(ipw_losses > 1 / self.min_propensity + 1e-12):
            raise RuntimeError("importance-weighted expert loss exceeded its bound")
        self._log_weights -= self.learning_rate * ipw_losses
        self._log_weights -= logsumexp(self._log_weights)
        self.n_updates += 1

    def _validate_experts(self, expert_values: np.ndarray) -> np.ndarray:
        values = np.asarray(expert_values, dtype=float).reshape(-1)
        if values.shape != (self.n_experts,) or not np.isfinite(values).all():
            raise ValueError("expert_values must be finite and match n_experts")
        if np.any(np.abs(values) > self.bound + 1e-12):
            raise ValueError("expert predictions must lie inside the proxy bound")
        return values
