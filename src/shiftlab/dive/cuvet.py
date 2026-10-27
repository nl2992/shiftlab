"""Power-law cost-constrained allocation and an explicit CUVET-style tree.

The bucket-level mCUV allocation follows the paper. The empirical tree uses
arm means and quantile split candidates; the latter is a ShiftLab adaptation
because the paper leaves its candidate-split generator unspecified.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import numpy as np


@dataclass(frozen=True)
class PowerLawBucket:
    """Expected total value and cost at reference treatment alpha=1."""

    value_at_one: float
    cost_at_one: float
    value_elasticity: float
    cost_elasticity: float

    def __post_init__(self) -> None:
        values = (
            self.value_at_one,
            self.cost_at_one,
            self.value_elasticity,
            self.cost_elasticity,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("Power-law bucket parameters must be finite")
        if self.value_at_one <= 0 or self.cost_at_one <= 0:
            raise ValueError("Reference value and cost must be positive")
        if self.value_elasticity <= 0:
            raise ValueError("Value elasticity must be positive")
        if self.cost_elasticity <= self.value_elasticity:
            raise ValueError("Cost elasticity must exceed value elasticity")

    def value(self, alpha: float) -> float:
        if alpha <= 0 or not isfinite(alpha):
            raise ValueError("Treatment multiplier alpha must be finite and positive")
        return self.value_at_one * alpha**self.value_elasticity

    def cost(self, alpha: float) -> float:
        if alpha <= 0 or not isfinite(alpha):
            raise ValueError("Treatment multiplier alpha must be finite and positive")
        return self.cost_at_one * alpha**self.cost_elasticity

    def marginal_cost_per_value(self, alpha: float) -> float:
        """Return dc/dv at alpha, as defined in the CUVET paper."""
        return (
            self.cost_elasticity
            * self.cost_at_one
            / (self.value_elasticity * self.value_at_one)
            * alpha ** (self.cost_elasticity - self.value_elasticity)
        )


@dataclass(frozen=True)
class Allocation:
    multipliers: tuple[float, ...]
    values: tuple[float, ...]
    costs: tuple[float, ...]
    shadow_price: float

    @property
    def total_value(self) -> float:
        return float(sum(self.values))

    @property
    def total_cost(self) -> float:
        return float(sum(self.costs))


@dataclass
class _TreeNode:
    curve: PowerLawBucket
    alpha: float
    feature: int | None = None
    threshold: float | None = None
    left: _TreeNode | None = None
    right: _TreeNode | None = None


def fit_power_law_bucket(
    arms: np.ndarray,
    values: np.ndarray,
    costs: np.ndarray,
    *,
    population_size: int,
    minimum_per_arm: int = 20,
) -> PowerLawBucket:
    """Fit bucket response curves by OLS on log arm-specific sample means.

    Multiplying the fitted per-observation mean at alpha=1 by the bucket
    population size gives the expected bucket total. This mean-based fit
    accommodates unequal arm counts; it is valid causally only under the
    source's randomized-assignment and complete-observation assumptions.
    """
    arms = np.asarray(arms, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    costs = np.asarray(costs, dtype=np.float64)
    if not (arms.ndim == values.ndim == costs.ndim == 1):
        raise ValueError("arms, values, and costs must be one-dimensional")
    if not (len(arms) == len(values) == len(costs)):
        raise ValueError("arms, values, and costs must have equal lengths")
    if population_size != len(arms) or population_size < 1:
        raise ValueError("population_size must equal the nonempty sample length")
    if minimum_per_arm < 2:
        raise ValueError("minimum_per_arm must be at least two")
    if not (np.isfinite(arms).all() and np.isfinite(values).all() and np.isfinite(costs).all()):
        raise ValueError("All treatment and outcome values must be finite")
    treatment_levels = np.asarray([0.8, 0.9, 1.0, 1.1, 1.2], dtype=np.float64)
    level_indices = np.abs(arms[:, None] - treatment_levels[None, :]).argmin(axis=1)
    if np.any(np.abs(arms - treatment_levels[level_indices]) > 1e-8):
        raise ValueError("arms must belong to {0.8, 0.9, 1.0, 1.1, 1.2}")
    counts = np.bincount(level_indices, minlength=len(treatment_levels))
    if np.any(counts < minimum_per_arm):
        raise ValueError("Each treatment arm needs minimum_per_arm observations")

    value_sums = np.bincount(level_indices, weights=values, minlength=len(treatment_levels))
    cost_sums = np.bincount(level_indices, weights=costs, minlength=len(treatment_levels))
    value_means = value_sums / counts
    cost_means = cost_sums / counts
    if np.any(value_means <= 0) or np.any(cost_means <= 0):
        raise ValueError("Each treatment arm must have positive mean value and cost")
    log_alpha = np.log(treatment_levels)
    log_mean_value = np.log(value_means)
    log_mean_cost = np.log(cost_means)
    value_slope, value_intercept = np.polyfit(log_alpha, log_mean_value, deg=1)
    cost_slope, cost_intercept = np.polyfit(log_alpha, log_mean_cost, deg=1)
    return PowerLawBucket(
        value_at_one=float(np.exp(value_intercept) * population_size),
        cost_at_one=float(np.exp(cost_intercept) * population_size),
        value_elasticity=float(value_slope),
        cost_elasticity=float(cost_slope),
    )


class CuvetQuantileTree:
    """Greedy tree adaptation using quantile-grid split candidates.

    The tree fits response curves separately for each treatment arm and uses
    the source mCUV allocator to score two-child splits. Quantile thresholds,
    mean-based elasticity fitting, and treatment levels are explicit model
    choices; this is not a claim of reproducing the original implementation.
    """

    def __init__(
        self,
        *,
        max_depth: int = 2,
        candidate_count: int = 16,
        min_samples_leaf: int = 2_000,
        min_samples_per_arm: int = 20,
        alpha_bounds: tuple[float, float] | None = (0.8, 1.2),
        minimum_gain: float = 1e-9,
    ) -> None:
        if max_depth < 0:
            raise ValueError("max_depth must be nonnegative")
        if candidate_count < 1:
            raise ValueError("candidate_count must be positive")
        if min_samples_leaf < 1 or min_samples_per_arm < 2:
            raise ValueError("sample thresholds are invalid")
        if minimum_gain < 0 or not isfinite(minimum_gain):
            raise ValueError("minimum_gain must be finite and nonnegative")
        self.max_depth = max_depth
        self.candidate_count = candidate_count
        self.min_samples_leaf = min_samples_leaf
        self.min_samples_per_arm = min_samples_per_arm
        self.alpha_bounds = alpha_bounds
        self.minimum_gain = minimum_gain
        self._root: _TreeNode | None = None
        self.n_features_in_: int | None = None

    def fit(
        self,
        features: np.ndarray,
        arms: np.ndarray,
        values: np.ndarray,
        costs: np.ndarray,
    ) -> CuvetQuantileTree:
        features = np.asarray(features, dtype=np.float64)
        arms = np.asarray(arms, dtype=np.float64)
        values = np.asarray(values, dtype=np.float64)
        costs = np.asarray(costs, dtype=np.float64)
        if features.ndim != 2 or features.shape[1] < 1:
            raise ValueError("features must be a nonempty two-dimensional matrix")
        if not np.isfinite(features).all():
            raise ValueError("features must be finite")
        if any(len(array) != len(features) for array in (arms, values, costs)):
            raise ValueError("features and response arrays must have equal lengths")
        root_curve = fit_power_law_bucket(
            arms,
            values,
            costs,
            population_size=len(features),
            minimum_per_arm=self.min_samples_per_arm,
        )
        self.n_features_in_ = features.shape[1]
        self._root = self._grow(features, arms, values, costs, root_curve, 1.0, depth=0)
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._root is None or self.n_features_in_ is None:
            raise RuntimeError("fit must be called before predict")
        features = np.asarray(features, dtype=np.float64)
        if features.ndim != 2 or features.shape[1] != self.n_features_in_:
            raise ValueError("features have an incompatible shape")
        if not np.isfinite(features).all():
            raise ValueError("features must be finite")
        result = np.empty(len(features), dtype=np.float64)
        pending = [(self._root, np.arange(len(features), dtype=np.int64))]
        while pending:
            node, indices = pending.pop()
            if node.feature is None:
                result[indices] = node.alpha
                continue
            assert node.threshold is not None and node.left is not None and node.right is not None
            left_mask = features[indices, node.feature] <= node.threshold
            pending.append((node.left, indices[left_mask]))
            pending.append((node.right, indices[~left_mask]))
        return result

    def _grow(
        self,
        features: np.ndarray,
        arms: np.ndarray,
        values: np.ndarray,
        costs: np.ndarray,
        curve: PowerLawBucket,
        alpha: float,
        *,
        depth: int,
    ) -> _TreeNode:
        node = _TreeNode(curve=curve, alpha=alpha)
        if depth >= self.max_depth or len(features) < 2 * self.min_samples_leaf:
            return node

        thresholds = np.linspace(0.05, 0.95, self.candidate_count + 2)[1:-1]
        best_gain = self.minimum_gain
        best_choice: (
            tuple[int, float, np.ndarray, PowerLawBucket, PowerLawBucket, Allocation] | None
        ) = None
        budget = curve.cost(alpha)

        for feature in range(features.shape[1]):
            candidates = np.unique(np.quantile(features[:, feature], thresholds))
            for split in candidates:
                left_mask = features[:, feature] <= split
                n_left = int(left_mask.sum())
                n_right = len(features) - n_left
                if min(n_left, n_right) < self.min_samples_leaf:
                    continue
                try:
                    left_curve = fit_power_law_bucket(
                        arms[left_mask],
                        values[left_mask],
                        costs[left_mask],
                        population_size=n_left,
                        minimum_per_arm=self.min_samples_per_arm,
                    )
                    right_curve = fit_power_law_bucket(
                        arms[~left_mask],
                        values[~left_mask],
                        costs[~left_mask],
                        population_size=n_right,
                        minimum_per_arm=self.min_samples_per_arm,
                    )
                    allocation = allocate_marginal_cost_equalization(
                        [left_curve, right_curve],
                        budget,
                        alpha_bounds=self.alpha_bounds,
                    )
                except ValueError:
                    continue
                gain = allocation.total_value - curve.value(alpha)
                if gain > best_gain:
                    best_gain = gain
                    best_choice = (
                        feature,
                        float(split),
                        left_mask,
                        left_curve,
                        right_curve,
                        allocation,
                    )

        if best_choice is None:
            return node
        feature, split, left_mask, left_curve, right_curve, allocation = best_choice
        node.feature = feature
        node.threshold = split
        node.left = self._grow(
            features[left_mask],
            arms[left_mask],
            values[left_mask],
            costs[left_mask],
            left_curve,
            allocation.multipliers[0],
            depth=depth + 1,
        )
        node.right = self._grow(
            features[~left_mask],
            arms[~left_mask],
            values[~left_mask],
            costs[~left_mask],
            right_curve,
            allocation.multipliers[1],
            depth=depth + 1,
        )
        return node


def allocate_marginal_cost_equalization(
    buckets: Sequence[PowerLawBucket],
    budget: float,
    *,
    alpha_bounds: tuple[float, float] | None = None,
    tolerance: float = 1e-10,
    max_iterations: int = 256,
) -> Allocation:
    """Maximize modeled total value under a total cost budget.

    The unclipped solution equalizes each bucket's marginal cost per unit
    value. With ``alpha_bounds``, multipliers are projected to those bounds
    and the common shadow price is found by monotone bisection.
    """
    if not buckets:
        raise ValueError("At least one bucket is required")
    if not isfinite(budget) or budget <= 0:
        raise ValueError("Budget must be finite and positive")
    if tolerance <= 0 or max_iterations < 1:
        raise ValueError("Solver tolerance and iteration count must be positive")

    if alpha_bounds is not None:
        lower, upper = alpha_bounds
        if not (isfinite(lower) and isfinite(upper) and 0 < lower < upper):
            raise ValueError("alpha_bounds must be finite, positive, and increasing")
        min_cost = sum(bucket.cost(lower) for bucket in buckets)
        max_cost = sum(bucket.cost(upper) for bucket in buckets)
        if budget < min_cost - tolerance or budget > max_cost + tolerance:
            raise ValueError("Budget is infeasible under the requested alpha bounds")
    else:
        lower, upper = 0.0, float("inf")

    marginal_at_one = np.asarray(
        [bucket.marginal_cost_per_value(1.0) for bucket in buckets], dtype=np.float64
    )
    exponents = np.asarray(
        [1.0 / (bucket.cost_elasticity - bucket.value_elasticity) for bucket in buckets],
        dtype=np.float64,
    )

    def multipliers_at(shadow_price: float) -> np.ndarray:
        alpha = (shadow_price / marginal_at_one) ** exponents
        if alpha_bounds is not None:
            alpha = np.clip(alpha, lower, upper)
        return alpha

    def cost_at(shadow_price: float) -> float:
        alpha = multipliers_at(shadow_price)
        return float(
            sum(
                bucket.cost_at_one * a**bucket.cost_elasticity
                for bucket, a in zip(buckets, alpha, strict=True)
            )
        )

    low = 0.0
    high = max(1.0, float(np.max(marginal_at_one)))
    if alpha_bounds is None:
        while cost_at(high) < budget:
            high *= 2.0
            if not isfinite(high):
                raise ArithmeticError("Could not bracket the allocation shadow price")
    else:
        gaps = np.asarray(
            [bucket.cost_elasticity - bucket.value_elasticity for bucket in buckets],
            dtype=np.float64,
        )
        low = float(np.min(marginal_at_one * lower**gaps))
        high = float(np.max(marginal_at_one * upper**gaps))

    for _ in range(max_iterations):
        midpoint = (low + high) / 2.0
        if cost_at(midpoint) < budget:
            low = midpoint
        else:
            high = midpoint
        if high - low <= tolerance * max(1.0, high):
            break
    shadow_price = (low + high) / 2.0
    alpha = multipliers_at(shadow_price)
    values = tuple(bucket.value(float(a)) for bucket, a in zip(buckets, alpha, strict=True))
    costs = tuple(bucket.cost(float(a)) for bucket, a in zip(buckets, alpha, strict=True))
    return Allocation(
        multipliers=tuple(float(a) for a in alpha),
        values=values,
        costs=costs,
        shadow_price=shadow_price,
    )
