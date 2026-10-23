"""Predictable label-query policies with calibration-only budget tuning."""

from __future__ import annotations

from typing import ClassVar

import numpy as np


class AdaptiveQueryPolicy:
    """Uniform, entropy, variance, cost-aware variance, and decision-value policies.

    The multiplier is calibrated on a pre-monitor validation slice to match expected
    label spend ``target_rate * mean(label_costs)`` and then held fixed. Query probabilities
    use current covariates and past-fitted models only. Spend can change after covariate shift;
    callers should log realized costs and propensities.
    """

    METHODS: ClassVar[set[str]] = {
        "uniform",
        "uncertainty",
        "variance",
        "cost_variance",
        "decision_value",
    }

    def __init__(
        self,
        method: str,
        *,
        target_rate: float = 0.1,
        q_min: float = 0.05,
        q_max: float = 0.8,
        decision_temperature: float = 0.25,
        variance_power: float = 0.5,
    ):
        if method not in self.METHODS:
            raise ValueError(f"method must be one of {sorted(self.METHODS)}")
        if not 0 < target_rate <= 1:
            raise ValueError("target_rate must lie in (0, 1]")
        if not 0 < q_min <= target_rate <= q_max <= 1:
            raise ValueError("require 0 < q_min <= target_rate <= q_max <= 1")
        if not np.isfinite(decision_temperature) or decision_temperature <= 0:
            raise ValueError("decision_temperature must be finite and positive")
        if not np.isfinite(variance_power) or not 0 <= variance_power <= 1:
            raise ValueError("variance_power must be finite and lie in [0, 1]")
        self.method = method
        self.target_rate = float(target_rate)
        self.q_min = float(q_min)
        self.q_max = float(q_max)
        self.decision_temperature = float(decision_temperature)
        self.variance_power = float(variance_power)
        self.multiplier: float | None = None

    def fit_multiplier(
        self,
        *,
        proxy: np.ndarray,
        residual_second_moment: np.ndarray,
        uncertainty: np.ndarray,
        label_costs: np.ndarray | None = None,
    ) -> AdaptiveQueryPolicy:
        costs = self._costs(label_costs, len(np.asarray(proxy).reshape(-1)))
        scores = self._scores(proxy, residual_second_moment, uncertainty, costs)
        if self.method == "uniform":
            self.multiplier = self.target_rate
            return self
        low, high = 0.0, self.q_max / max(float(scores.min()), 1e-12)
        target_spend = self.target_rate * float(costs.mean())
        for _ in range(80):
            middle = (low + high) / 2
            spend = np.mean(np.clip(middle * scores, self.q_min, self.q_max) * costs)
            if spend < target_spend:
                low = middle
            else:
                high = middle
        self.multiplier = (low + high) / 2
        return self

    def probabilities(
        self,
        *,
        proxy: np.ndarray,
        residual_second_moment: np.ndarray,
        uncertainty: np.ndarray,
        label_costs: np.ndarray | None = None,
    ) -> np.ndarray:
        if self.multiplier is None:
            raise RuntimeError("fit_multiplier must be called on pre-monitor validation data")
        costs = self._costs(label_costs, len(np.asarray(proxy).reshape(-1)))
        scores = self._scores(proxy, residual_second_moment, uncertainty, costs)
        if self.method == "uniform":
            return np.full(len(scores), self.target_rate)
        return np.clip(self.multiplier * scores, self.q_min, self.q_max)

    @staticmethod
    def _costs(label_costs: np.ndarray | None, size: int) -> np.ndarray:
        if label_costs is None:
            return np.ones(size, dtype=float)
        costs = np.asarray(label_costs, dtype=float).reshape(-1)
        if len(costs) != size or not np.isfinite(costs).all() or np.any(costs <= 0):
            raise ValueError("label costs must be finite, positive, and match the score inputs")
        return costs

    def _scores(
        self,
        proxy: np.ndarray,
        residual_second_moment: np.ndarray,
        uncertainty: np.ndarray,
        label_costs: np.ndarray,
    ) -> np.ndarray:
        proxy = np.asarray(proxy, dtype=float).reshape(-1)
        variance = np.asarray(residual_second_moment, dtype=float).reshape(-1)
        uncertainty = np.asarray(uncertainty, dtype=float).reshape(-1)
        if len(proxy) == 0 or not (len(proxy) == len(variance) == len(uncertainty)):
            raise ValueError("query score inputs must have the same nonzero length")
        if not all(np.isfinite(v).all() for v in (proxy, variance, uncertainty)):
            raise ValueError("query score inputs must be finite")
        if np.any(variance < 0) or np.any(uncertainty < 0):
            raise ValueError("variance and uncertainty scores must be nonnegative")
        if self.method == "uniform":
            return np.ones(len(proxy))
        if self.method == "uncertainty":
            scores = uncertainty
        elif self.method == "variance":
            scores = variance**self.variance_power
        elif self.method == "cost_variance":
            if np.any(label_costs <= 0) or not np.isfinite(label_costs).all():
                raise ValueError("label costs must be finite and strictly positive")
            # Lagrange optimum for minimizing E[(1/q - 1) v] subject to E[k q] = budget.
            scores = np.sqrt(variance / label_costs)
        else:
            # Heuristic value score: prioritize residual uncertainty near the harm margin.
            scores = np.sqrt(variance) * np.exp(-np.abs(proxy) / self.decision_temperature)
        return np.maximum(scores, 1e-12)


def mix_with_uniform(
    adaptive_probabilities: np.ndarray,
    *,
    target_rate: float,
    mixture_weight: float,
) -> np.ndarray:
    """Shrink an adaptive query design toward a fixed-rate uniform design.

    If the adaptive probabilities average to ``target_rate`` on validation and lie in
    ``[q_min, q_max]``, the mixture's expected query-rate deviation under any shifted
    feature distribution is at most ``mixture_weight * max(target_rate-q_min,
    q_max-target_rate)``. The uniform component also raises the global propensity floor.
    """
    probabilities = np.asarray(adaptive_probabilities, dtype=float).reshape(-1)
    if len(probabilities) == 0 or not np.isfinite(probabilities).all():
        raise ValueError("adaptive_probabilities must be nonempty and finite")
    if np.any((probabilities <= 0) | (probabilities > 1)):
        raise ValueError("adaptive probabilities must lie in (0, 1]")
    if not np.isfinite(target_rate) or not 0 < target_rate <= 1:
        raise ValueError("target_rate must lie in (0, 1]")
    if not np.isfinite(mixture_weight) or not 0 <= mixture_weight <= 1:
        raise ValueError("mixture_weight must lie in [0, 1]")
    return (1 - mixture_weight) * target_rate + mixture_weight * probabilities


def expected_rate_drift_bound(
    *, target_rate: float, mixture_weight: float, q_min: float, q_max: float
) -> float:
    """Worst-case shift in mean propensity from a uniform/adaptive mixture."""
    if not 0 < q_min <= target_rate <= q_max <= 1:
        raise ValueError("require 0 < q_min <= target_rate <= q_max <= 1")
    if not np.isfinite(mixture_weight) or not 0 <= mixture_weight <= 1:
        raise ValueError("mixture_weight must lie in [0, 1]")
    return float(mixture_weight * max(target_rate - q_min, q_max - target_rate))


def cost_neutral_propensities(
    label_costs: np.ndarray,
    *,
    budget_per_event: float,
    q_min: float,
    q_max: float,
) -> np.ndarray:
    """Return q0(k)=budget_per_event/k, requiring no propensity clipping.

    For every event with known cost k, this design spends exactly
    ``k * q0(k) == budget_per_event`` in conditional expectation. The budget must be
    feasible for every supplied cost under the requested propensity bounds.
    """
    costs = np.asarray(label_costs, dtype=float).reshape(-1)
    if len(costs) == 0 or not np.isfinite(costs).all() or np.any(costs <= 0):
        raise ValueError("label costs must be finite, positive, and nonempty")
    if not np.isfinite(budget_per_event) or budget_per_event <= 0:
        raise ValueError("budget_per_event must be finite and positive")
    if not 0 < q_min <= q_max <= 1:
        raise ValueError("require 0 < q_min <= q_max <= 1")
    probabilities = budget_per_event / costs
    if np.any(probabilities < q_min) or np.any(probabilities > q_max):
        raise ValueError("per-event spend target is infeasible under the propensity bounds")
    return probabilities


def mix_with_cost_neutral(
    adaptive_probabilities: np.ndarray,
    label_costs: np.ndarray,
    *,
    budget_per_event: float,
    mixture_weight: float,
    q_min: float,
    q_max: float,
) -> np.ndarray:
    """Shrink an adaptive design toward exact per-event expected-spend propensities."""
    adaptive = np.asarray(adaptive_probabilities, dtype=float).reshape(-1)
    costs = np.asarray(label_costs, dtype=float).reshape(-1)
    if len(adaptive) != len(costs) or len(adaptive) == 0:
        raise ValueError("adaptive probabilities and label costs must have equal nonzero length")
    if not np.isfinite(adaptive).all() or np.any((adaptive < q_min) | (adaptive > q_max)):
        raise ValueError("adaptive probabilities must be finite and within propensity bounds")
    if not np.isfinite(mixture_weight) or not 0 <= mixture_weight <= 1:
        raise ValueError("mixture_weight must lie in [0, 1]")
    neutral = cost_neutral_propensities(
        costs, budget_per_event=budget_per_event, q_min=q_min, q_max=q_max
    )
    return (1 - mixture_weight) * neutral + mixture_weight * adaptive


def expected_cost_drift_bound(
    *,
    budget_per_event: float,
    mixture_weight: float,
    cost_min: float,
    cost_max: float,
    q_min: float,
    q_max: float,
) -> float:
    """Bound expected spend drift for the cost-neutral/adaptive mixture.

    Assumes the neutral branch is feasible and all deployment costs lie in
    ``[cost_min, cost_max]`` while the adaptive propensity lies in ``[q_min,q_max]``.
    """
    if not np.isfinite(budget_per_event) or budget_per_event <= 0:
        raise ValueError("budget_per_event must be finite and positive")
    if not np.isfinite(cost_min) or not np.isfinite(cost_max) or not 0 < cost_min <= cost_max:
        raise ValueError("require finite 0 < cost_min <= cost_max")
    if not 0 < q_min <= q_max <= 1:
        raise ValueError("require 0 < q_min <= q_max <= 1")
    if budget_per_event / cost_max < q_min or budget_per_event / cost_min > q_max:
        raise ValueError("per-event spend target is infeasible under the propensity bounds")
    if not np.isfinite(mixture_weight) or not 0 <= mixture_weight <= 1:
        raise ValueError("mixture_weight must lie in [0, 1]")
    return float(
        mixture_weight
        * max(
            abs(cost_min * q_min - budget_per_event),
            abs(cost_max * q_max - budget_per_event),
        )
    )


def cost_mixture_weight_for_tolerance(
    *,
    budget_per_event: float,
    drift_tolerance: float,
    cost_min: float,
    cost_max: float,
    q_min: float,
    q_max: float,
) -> float:
    """Choose the largest adaptive-mixture weight satisfying a spend-drift bound."""
    if not np.isfinite(drift_tolerance) or drift_tolerance < 0:
        raise ValueError("drift_tolerance must be finite and nonnegative")
    full_adaptive_bound = expected_cost_drift_bound(
        budget_per_event=budget_per_event,
        mixture_weight=1.0,
        cost_min=cost_min,
        cost_max=cost_max,
        q_min=q_min,
        q_max=q_max,
    )
    if full_adaptive_bound == 0:
        return 1.0
    return float(min(1.0, drift_tolerance / full_adaptive_bound))
