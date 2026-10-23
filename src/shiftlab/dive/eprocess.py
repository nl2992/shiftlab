"""Bounded betting processes for conditional-mean harm nulls."""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


class BoundedMeanEProcess:
    """Mixture e-process for E[X_t | history] <= 0 and known |X_t| <= bound.

    Each component multiplies by ``1 + stake * X_t / bound`` for a fixed stake in
    (0, 1] and a fixed bound. The mixture controls the probability of ever crossing
    1/alpha under the stated conditional-mean null. This class does not validate
    that the user's data satisfy that null or filtration.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float = 0.05,
        stakes: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8),
        weights: tuple[float, ...] | None = None,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not 0 < alpha < 1:
            raise ValueError("alpha must lie in (0, 1)")
        if not stakes or any(not np.isfinite(s) or not 0 < s <= 1 for s in stakes):
            raise ValueError("stakes must be a nonempty collection in (0, 1]")
        if weights is None:
            weights_array = np.full(len(stakes), 1 / len(stakes), dtype=float)
        else:
            weights_array = np.asarray(weights, dtype=float)
            if (
                weights_array.shape != (len(stakes),)
                or not np.isfinite(weights_array).all()
                or np.any(weights_array <= 0)
                or not np.isclose(weights_array.sum(), 1.0)
            ):
                raise ValueError("weights must be positive, sum to one, and match stakes")
        self.bound = float(bound)
        self.alpha = float(alpha)
        self.stakes = np.asarray(stakes, dtype=float)
        self.weights = weights_array
        self.log_wealth = np.zeros(len(stakes), dtype=float)
        self.n_updates = 0

    @property
    def log_e_value(self) -> float:
        return float(logsumexp(self.log_wealth + np.log(self.weights)))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        factors = 1 + self.stakes * (value / self.bound)
        self.log_wealth += np.log(factors)
        self.n_updates += 1
        return self.log_e_value


class StartedMixtureEProcess:
    """A prespecified mixture of e-processes started at fixed stream positions.

    Processes are 1 before their start and evolve afterward. A fixed convex mixture
    retains Ville validity and can respond to a recent harmful regime without an
    uncontrolled sequence of test restarts.
    """

    def __init__(self, *, bound: float, alpha: float, starts: tuple[int, ...]):
        if not starts or any(isinstance(s, bool) or s < 0 for s in starts):
            raise ValueError("starts must be a nonempty collection of nonnegative integers")
        if tuple(sorted(set(starts))) != starts:
            raise ValueError("starts must be strictly increasing")
        self.starts = starts
        self.processes = [BoundedMeanEProcess(bound=bound, alpha=alpha) for _ in starts]
        self.time = 0

    @property
    def log_e_value(self) -> float:
        logs = np.asarray(
            [
                p.log_e_value if self.time >= start else 0.0
                for start, p in zip(self.starts, self.processes, strict=True)
            ]
        )
        return float(logsumexp(logs) - np.log(len(logs)))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.processes[0].alpha)

    def update(self, value: float) -> float:
        for start, process in zip(self.starts, self.processes, strict=True):
            if self.time >= start:
                process.update(value)
        self.time += 1
        return self.log_e_value
