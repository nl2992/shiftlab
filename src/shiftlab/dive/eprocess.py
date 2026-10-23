"""Bounded betting processes for conditional-mean harm nulls."""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


def bounded_betting_factors(
    values: np.ndarray, bounds: np.ndarray, stakes: np.ndarray
) -> np.ndarray:
    """Return betting factors for predictable event-specific bounds.

    If ``bound_t`` is known before ``value_t`` and the conditional-mean null holds
    after conditioning on the information used to choose it, each factor has
    conditional expectation at most one. Callers are responsible for that
    filtration condition; this helper checks only numerical boundedness.
    """
    observed = np.asarray(values, dtype=float)
    scale = np.asarray(bounds, dtype=float)
    bets = np.asarray(stakes, dtype=float)
    if observed.ndim != 1 or scale.shape != observed.shape:
        raise ValueError("values and bounds must be matching one-dimensional arrays")
    if bets.ndim != 1 or not len(bets) or np.any(~np.isfinite(bets)):
        raise ValueError("stakes must be a nonempty finite one-dimensional array")
    if np.any((bets <= 0) | (bets > 1)):
        raise ValueError("stakes must lie in (0, 1]")
    if np.any(~np.isfinite(observed)) or np.any(~np.isfinite(scale)) or np.any(scale <= 0):
        raise ValueError("values must be finite and bounds finite and positive")
    if np.any(np.abs(observed) > scale + 1e-12):
        raise ValueError("observed value is outside the declared bounded range")
    factors = 1 + observed[:, None] * bets[None, :] / scale[:, None]
    if np.any(factors <= 0):
        raise ValueError("betting factors must be positive")
    return factors


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


class PredictableVarianceAdaptiveEProcess:
    """One-sided plug-in Kelly e-process for globally bounded mean gains.

    The stake at time ``t`` is the positive part of a smoothed estimate of the
    normalized mean divided by its smoothed second moment, clipped below one.
    It is computed before observing the current value. Under
    ``E[value_t | history] <= 0`` and ``|value_t| <= bound``, every factor
    ``1 + stake_t * value_t / bound`` is nonnegative with conditional
    expectation at most one. The predictable stake therefore preserves
    anytime validity while responding to the observed scale and direction of
    past gains. The Kelly approximation motivates power; it is not needed for
    the validity argument and is not a novelty claim.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float = 0.05,
        prior_strength: float = 4.0,
        prior_mean: float = 0.05,
        prior_second_moment: float = 0.25,
        max_stake: float = 0.5,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if not np.isfinite(prior_strength) or prior_strength <= 0:
            raise ValueError("prior_strength must be finite and positive")
        if not np.isfinite(prior_mean) or not 0 <= prior_mean < 1:
            raise ValueError("prior_mean must lie in [0, 1)")
        if not np.isfinite(prior_second_moment) or not 0 < prior_second_moment <= 1:
            raise ValueError("prior_second_moment must lie in (0, 1]")
        if not np.isfinite(max_stake) or not 0 < max_stake < 1:
            raise ValueError("max_stake must lie strictly between zero and one")
        self.bound = float(bound)
        self.alpha = float(alpha)
        self.prior_strength = float(prior_strength)
        self.prior_mean = float(prior_mean)
        self.prior_second_moment = float(prior_second_moment)
        self.max_stake = float(max_stake)
        self.sum_normalized = 0.0
        self.sum_squares = 0.0
        self.log_wealth = 0.0
        self.n_updates = 0
        self.last_stake: float | None = None

    @property
    def stake(self) -> float:
        """Return the next stake, using past observations only."""
        denominator = self.prior_strength + self.n_updates
        mean = (self.prior_strength * self.prior_mean + self.sum_normalized) / denominator
        second_moment = (
            self.prior_strength * self.prior_second_moment + self.sum_squares
        ) / denominator
        return float(np.clip(max(0.0, mean) / second_moment, 0.0, self.max_stake))

    @property
    def log_e_value(self) -> float:
        return self.log_wealth

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        normalized = float(value / self.bound)
        stake = self.stake
        factor = 1 + stake * normalized
        if factor <= 0:
            raise RuntimeError("predictable stake produced a nonpositive betting factor")
        self.last_stake = stake
        self.log_wealth += float(np.log(factor))
        self.sum_normalized += normalized
        self.sum_squares += normalized**2
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
