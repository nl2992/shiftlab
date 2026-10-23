"""Simple monitoring baselines and a bounded full-feedback excess-cost e-process."""

from dataclasses import dataclass
from math import ceil, isfinite, log

import numpy as np


def rbf_gamma(reference: np.ndarray) -> float:
    """Return a fixed inverse-median-distance RBF bandwidth from reference data only."""
    x = np.asarray(reference, dtype=float)
    if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("reference must be a finite 2D array with at least two rows")
    squared = np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)
    distances = squared[np.triu_indices(len(x), k=1)]
    median = float(np.median(distances[distances > 0])) if np.any(distances > 0) else 0.0
    if median <= 0:
        raise ValueError("reference must contain at least two distinct rows")
    return 1.0 / median


def rbf_mmd_squared(reference: np.ndarray, current: np.ndarray, gamma: float) -> float:
    """Unbiased two-sample RBF MMD-squared statistic; not an anytime-valid test."""
    x, y = np.asarray(reference, dtype=float), np.asarray(current, dtype=float)
    if (
        x.ndim != 2
        or y.ndim != 2
        or x.shape[1] != y.shape[1]
        or min(len(x), len(y)) < 2
        or not np.isfinite(x).all()
        or not np.isfinite(y).all()
        or not isfinite(gamma)
        or gamma <= 0
    ):
        raise ValueError("MMD inputs must be finite compatible matrices and gamma must be positive")

    def kernel(a, b):
        squared = np.maximum(
            np.sum(a * a, axis=1)[:, None] + np.sum(b * b, axis=1)[None, :] - 2 * a @ b.T,
            0.0,
        )
        return np.exp(-gamma * squared)

    xx, yy, xy = kernel(x, x), kernel(y, y), kernel(x, y)
    np.fill_diagonal(xx, 0.0)
    np.fill_diagonal(yy, 0.0)
    return float(
        xx.sum() / (len(x) * (len(x) - 1)) + yy.sum() / (len(y) * (len(y) - 1)) - 2 * xy.mean()
    )


def one_sided_cusum(values, *, baseline_mean: float, baseline_scale: float, slack: float):
    """Standardized upward CUSUM. Thresholds require separate null calibration."""
    x = np.asarray(values, dtype=float)
    if (
        x.ndim != 1
        or not np.isfinite(x).all()
        or not isfinite(baseline_mean)
        or not isfinite(baseline_scale)
        or baseline_scale <= 0
        or not isfinite(slack)
        or slack < 0
    ):
        raise ValueError("CUSUM needs finite values, positive baseline scale and nonnegative slack")
    result = np.empty(len(x), dtype=float)
    statistic = 0.0
    for index, value in enumerate(x):
        statistic = max(0.0, statistic + (value - baseline_mean) / baseline_scale - slack)
        result[index] = statistic
    return result


def conformal_upper_threshold(null_maxima, alpha: float) -> float:
    """Finite-sample rank threshold from independent null runs, with an infinite tail if needed."""
    maxima = np.asarray(null_maxima, dtype=float)
    if maxima.ndim != 1 or not len(maxima) or not np.isfinite(maxima).all() or not 0 < alpha < 1:
        raise ValueError("null maxima and alpha must be finite, nonempty, and valid")
    rank = ceil((len(maxima) + 1) * (1 - alpha))
    if rank > len(maxima):
        return float("inf")
    return float(np.sort(maxima, kind="stable")[rank - 1])


@dataclass
class HoeffdingExcessEProcess:
    """Mixture e-process for a bounded paired-cost null with complete feedback.

    If each action and its reference loss are chosen before the outcome, the observed contrast
    C_t = cost(action_t,Y_t)-cost(reference_t,Y_t) lies in [lower, upper], and
    E[C_t | F_{t-1}] <= epsilon for every t, Hoeffding's lemma makes each fixed-lambda process
    exp(sum(lambda*(C_t-epsilon) - lambda^2*(upper-lower)^2/8)) a nonnegative supermartingale.
    A fixed mixture remains an e-process, so Ville's inequality controls the probability of ever
    crossing 1/alpha. This does not handle unlogged selective outcomes, unbounded costs, invalid
    counterfactual losses, or a null that holds only on average over time.
    """

    epsilon: float = 0.0
    alpha: float = 0.05
    lower: float = -5.0
    upper: float = 5.0
    lambdas: tuple[float, ...] = (0.002, 0.005, 0.01, 0.02, 0.05, 0.1)

    def __post_init__(self):
        if (
            not all(isfinite(value) for value in (self.epsilon, self.alpha, self.lower, self.upper))
            or not 0 < self.alpha < 1
            or self.lower >= self.upper
            or not self.lambdas
            or any(not isfinite(value) or value <= 0 for value in self.lambdas)
        ):
            raise ValueError("Invalid e-process parameters")
        self._log_wealth = np.zeros(len(self.lambdas), dtype=float)
        self.n_observations = 0

    def update(self, excess_cost: float) -> float:
        if not isfinite(excess_cost) or not self.lower <= excess_cost <= self.upper:
            raise ValueError("Observed paired excess cost is outside the declared bounded range")
        z = excess_cost - self.epsilon
        lambdas = np.asarray(self.lambdas, dtype=float)
        span = self.upper - self.lower
        self._log_wealth += lambdas * z - lambdas**2 * span**2 / 8
        self.n_observations += 1
        log_sum = float(np.logaddexp.reduce(self._log_wealth))
        return log_sum - log(len(lambdas))

    @property
    def log_evalue(self) -> float:
        return float(np.logaddexp.reduce(self._log_wealth) - log(len(self.lambdas)))

    @property
    def alarm(self) -> bool:
        return self.log_evalue >= log(1 / self.alpha)
