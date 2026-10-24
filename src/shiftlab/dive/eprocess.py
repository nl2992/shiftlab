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

    @property
    def predictable_stake(self) -> float:
        """Posterior mean stake for the next mixture update, from past evidence only."""
        posterior = np.exp(self.log_wealth + np.log(self.weights) - self.log_e_value)
        return float(np.dot(posterior, self.stakes))

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


class PredictablePlugInEmpiricalBernsteinEProcess:
    """One-sided PM-EB process for globally bounded conditional-mean nulls.

    Inputs are scaled to ``[0, 1]`` and tested against mean ``1/2``. The stake
    follows the predictable variance schedule of Waudby-Smith and Ramdas
    (2024), capped below one. The process uses the predictable empirical
    Bernstein correction based on squared deviations from the prior smoothed
    mean. A fixed threshold ``1/alpha`` gives anytime control when the
    conditional mean is at most ``1/2`` at every update. This class uses a
    global support bound; it does not normalize by current covariates.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float = 0.05,
        max_stake: float = 0.5,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if not np.isfinite(max_stake) or not 0 < max_stake < 1:
            raise ValueError("max_stake must lie strictly between zero and one")
        self.bound = float(bound)
        self.alpha = float(alpha)
        self.max_stake = float(max_stake)
        self.n_updates = 0
        self.sum_observations = 0.0
        self.sum_predictive_squared_deviations = 0.0
        self.predictive_mean = 0.5
        self.predictive_variance = 0.25
        self.log_wealth = 0.0
        self.last_stake: float | None = None

    @property
    def stake(self) -> float:
        """Return the next predictable PM-EB stake."""
        time = self.n_updates + 1
        numerator = 2 * np.log(2 / self.alpha)
        denominator = self.predictive_variance * time * np.log1p(time)
        return float(min(self.max_stake, np.sqrt(numerator / denominator)))

    @property
    def log_e_value(self) -> float:
        return self.log_wealth

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        observation = 0.5 * (value / self.bound + 1)
        stake = self.stake
        psi = (-np.log1p(-stake) - stake) / 4
        residual = observation - self.predictive_mean
        increment = stake * (observation - 0.5) - 4 * residual**2 * psi
        self.last_stake = stake
        self.log_wealth += float(increment)
        self.sum_observations += observation
        time = self.n_updates + 1
        self.predictive_mean = (0.5 + self.sum_observations) / (time + 1)
        post_update_residual = observation - self.predictive_mean
        self.sum_predictive_squared_deviations += post_update_residual**2
        self.predictive_variance = (0.25 + self.sum_predictive_squared_deviations) / (time + 1)
        self.n_updates = time
        return self.log_e_value


class PPIBlockConfidenceSequence:
    """One-sided confidence sequence for running means of bounded PPI block estimates.

    Each input is a PPI estimate for one block with support ``[-eta_max, 1+eta_max]``.
    The estimator is affinely normalized to ``[0, 1]``. A finite mixture of
    conjugate-mixture empirical-Bernstein (CM-EB) betting factors yields a time-uniform
    lower confidence bound for its running mean. This adapts PPRM's test-stream bound
    to paired-cost PPI estimates; it does not include PPRM's source-risk upper bound.

    A crossing tests the running-mean null. It does not by itself test the stronger
    eventwise conditional-mean null or certify an alternative policy.
    """

    def __init__(
        self,
        *,
        max_reliance: float,
        threshold: float,
        alpha: float = 0.05,
        lambda_count: int = 64,
        root_iterations: int = 36,
    ):
        if not np.isfinite(max_reliance) or max_reliance < 0:
            raise ValueError("max_reliance must be finite and nonnegative")
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("threshold must lie in [0, 1]")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if isinstance(lambda_count, bool) or not isinstance(lambda_count, int) or lambda_count < 2:
            raise ValueError("lambda_count must be an integer of at least two")
        if (
            isinstance(root_iterations, bool)
            or not isinstance(root_iterations, int)
            or root_iterations < 1
        ):
            raise ValueError("root_iterations must be a positive integer")
        self.max_reliance = float(max_reliance)
        self.threshold = float(threshold)
        self.alpha = float(alpha)
        self.root_iterations = root_iterations
        self.lambdas = np.geomspace(1e-4, 0.99, lambda_count)
        self.log_weights = np.full(lambda_count, -np.log(lambda_count), dtype=float)
        self.psi = -np.log1p(-self.lambdas) - self.lambdas
        support_width = 1 + 2 * self.max_reliance
        self.normalized_threshold = (self.threshold + self.max_reliance) / support_width
        self.n_updates = 0
        self.sum_observations = 0.0
        self.sum_squared_prediction_errors = 0.0
        self.predictive_mean = 0.5
        self._lower_bound = 0.0
        self.log_crossing_statistic = 0.0

    @property
    def alarm(self) -> bool:
        return self.n_updates > 0 and self.log_crossing_statistic >= -np.log(self.alpha)

    @property
    def lower_bound(self) -> float:
        """Return a time-uniform lower bound for the average block conditional mean."""
        if self.n_updates:
            radius = self._radius()
            normalized_lower = self.sum_observations / self.n_updates - radius / self.n_updates
            self._lower_bound = float(
                np.clip(
                    -self.max_reliance + (1 + 2 * self.max_reliance) * normalized_lower,
                    0.0,
                    1.0,
                )
            )
        return self._lower_bound

    @staticmethod
    def _logsumexp(values: np.ndarray) -> float:
        maximum = float(np.max(values))
        return maximum + float(np.log(np.exp(values - maximum).sum()))

    def _mixture_log_value(self, excess_sum: float) -> float:
        return self._logsumexp(
            self.log_weights
            + self.lambdas * excess_sum
            - self.psi * self.sum_squared_prediction_errors
        )

    def _radius(self) -> float:
        target = -np.log(self.alpha)
        lower, upper = 0.0, 1.0
        while self._mixture_log_value(upper) < target:
            upper *= 2.0
        for _ in range(self.root_iterations):
            midpoint = (lower + upper) / 2
            if self._mixture_log_value(midpoint) < target:
                lower = midpoint
            else:
                upper = midpoint
        return upper

    def update(self, estimate: float) -> bool:
        """Consume one completed block and return whether the running-mean null crossed."""
        lower_support = -self.max_reliance
        upper_support = 1 + self.max_reliance
        if (
            not np.isfinite(estimate)
            or not lower_support - 1e-12 <= estimate <= upper_support + 1e-12
        ):
            raise ValueError("PPI estimate is outside the declared support")
        normalized = (float(estimate) + self.max_reliance) / (1 + 2 * self.max_reliance)
        self.sum_squared_prediction_errors += (normalized - self.predictive_mean) ** 2
        self.sum_observations += normalized
        self.n_updates += 1
        self.predictive_mean = self.sum_observations / self.n_updates
        excess_sum = self.sum_observations - self.n_updates * self.normalized_threshold
        self.log_crossing_statistic = self._mixture_log_value(excess_sum)
        self._lower_bound = 0.0
        return self.alarm


class PredictableHedgedPositiveEProcess:
    """Positive-direction branch of the hedged capital process at mean 1/2.

    The input is globally bounded in ``[-bound, bound]`` and is mapped to
    ``[0, 1]``. The process tests the composite upper-mean null by betting only
    on the positive direction. This branch is a nonnegative supermartingale
    when the conditional mean is at most 1/2; the full two-sided hedge is not
    valid for that one-sided composite null because its negative branch can
    grow when the true mean is below 1/2.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float = 0.05,
        max_stake: float = 1.0,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if not np.isfinite(max_stake) or not 0 < max_stake <= 1:
            raise ValueError("max_stake must lie in (0, 1]")
        self.bound = float(bound)
        self.alpha = float(alpha)
        self.max_stake = float(max_stake)
        self.n_updates = 0
        self.sum_observations = 0.0
        self.sum_predictive_squared_deviations = 0.0
        self.predictive_mean = 0.5
        self.predictive_variance = 0.25
        self.log_wealth = 0.0
        self.last_stake: float | None = None

    @property
    def stake(self) -> float:
        """Return the next predictable positive-direction stake."""
        time = self.n_updates + 1
        numerator = 2 * np.log(2 / self.alpha)
        denominator = self.predictive_variance * time * np.log1p(time)
        return float(min(self.max_stake, np.sqrt(numerator / denominator)))

    @property
    def log_e_value(self) -> float:
        return self.log_wealth

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        observation = 0.5 * (value / self.bound + 1)
        stake = self.stake
        factor = 1 + stake * (observation - 0.5)
        if factor <= 0:
            raise RuntimeError("positive-direction hedge produced a nonpositive factor")
        self.last_stake = stake
        self.log_wealth += float(np.log(factor))
        self.sum_observations += observation
        time = self.n_updates + 1
        self.predictive_mean = (0.5 + self.sum_observations) / (time + 1)
        residual = observation - self.predictive_mean
        self.sum_predictive_squared_deviations += residual**2
        self.predictive_variance = (0.25 + self.sum_predictive_squared_deviations) / (time + 1)
        self.n_updates = time
        return self.log_e_value


class PPIBlockMixtureEProcess:
    """Combine CM-EB and predictable positive betting for bounded PPI block means.

    Both component e-processes test the same null that the running mean of the
    block estimates is at most ``threshold``. Their fixed 1/2 mixture is therefore
    also an e-process and can be monitored at the original alpha level. The
    positive-betting component receives the centered block estimate and uses the
    deterministic support bound implied by ``max_reliance`` and ``threshold``.
    """

    def __init__(
        self,
        *,
        max_reliance: float,
        threshold: float,
        alpha: float = 0.05,
    ):
        self.cm_eb = PPIBlockConfidenceSequence(
            max_reliance=max_reliance,
            threshold=threshold,
            alpha=alpha,
        )
        centered_bound = max(
            threshold + max_reliance,
            1 + max_reliance - threshold,
        )
        self.positive_betting = PredictableHedgedPositiveEProcess(
            bound=centered_bound,
            alpha=alpha,
        )
        self.alpha = float(alpha)

    @property
    def log_e_value(self) -> float:
        return self.log_e_value_at_weight(0.5)

    def log_e_value_at_weight(self, cm_eb_weight: float) -> float:
        """Return a fixed convex mixture of component e-values."""
        if not np.isfinite(cm_eb_weight) or not 0 < cm_eb_weight < 1:
            raise ValueError("cm_eb_weight must lie strictly between zero and one")
        return float(
            logsumexp(
                [
                    np.log(cm_eb_weight) + self.cm_eb.log_crossing_statistic,
                    np.log1p(-cm_eb_weight) + self.positive_betting.log_e_value,
                ]
            )
        )

    def alarm_at_weight(self, cm_eb_weight: float) -> bool:
        return self.log_e_value_at_weight(cm_eb_weight) >= -np.log(self.alpha)

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, estimate: float) -> bool:
        self.cm_eb.update(estimate)
        self.positive_betting.update(estimate - self.cm_eb.threshold)
        return self.alarm


class StartedMixtureEProcess:
    """A prespecified mixture of e-processes started at fixed stream positions.

    Processes are 1 before their start and evolve afterward. A fixed convex mixture
    retains Ville validity and can respond to a recent harmful regime without an
    uncontrolled sequence of test restarts.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float,
        starts: tuple[int, ...],
        weights: tuple[float, ...] | None = None,
    ):
        if not starts or any(isinstance(s, bool) or s < 0 for s in starts):
            raise ValueError("starts must be a nonempty collection of nonnegative integers")
        if tuple(sorted(set(starts))) != starts:
            raise ValueError("starts must be strictly increasing")
        if weights is None:
            weights_array = np.full(len(starts), 1 / len(starts), dtype=float)
        else:
            weights_array = np.asarray(weights, dtype=float)
            if (
                weights_array.shape != (len(starts),)
                or not np.isfinite(weights_array).all()
                or np.any(weights_array <= 0)
                or not np.isclose(weights_array.sum(), 1.0)
            ):
                raise ValueError("weights must be positive, sum to one, and match starts")
        self.starts = starts
        self.weights = weights_array
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
        return float(logsumexp(logs + np.log(self.weights)))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.processes[0].alpha)

    def update(self, value: float) -> float:
        for start, process in zip(self.starts, self.processes, strict=True):
            if self.time >= start:
                process.update(value)
        self.time += 1
        return self.log_e_value


class VectorizedStartedMixtureEProcess:
    """Vectorized implementation of ``StartedMixtureEProcess``'s fixed mixture.

    The start and stake weights are fixed before observations. This class stores
    component log wealth in one array and applies the same per-event updates as
    ``StartedMixtureEProcess``. It is a computational optimization, not a change
    to the e-process or its assumptions.
    """

    DEFAULT_STAKES = np.asarray((0.05, 0.1, 0.2, 0.4, 0.8), dtype=float)

    def __init__(
        self,
        *,
        bound: float,
        alpha: float,
        starts: tuple[int, ...],
        weights: tuple[float, ...] | None = None,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if not starts or any(isinstance(s, bool) or s < 0 for s in starts):
            raise ValueError("starts must be a nonempty collection of nonnegative integers")
        if tuple(sorted(set(starts))) != starts:
            raise ValueError("starts must be strictly increasing")
        weight_array = (
            np.full(len(starts), 1 / len(starts), dtype=float)
            if weights is None
            else np.asarray(weights, dtype=float)
        )
        if (
            weight_array.shape != (len(starts),)
            or not np.isfinite(weight_array).all()
            or np.any(weight_array <= 0)
            or not np.isclose(weight_array.sum(), 1.0)
        ):
            raise ValueError("weights must be positive, sum to one, and match starts")
        self.bound = float(bound)
        self.alpha = float(alpha)
        self.starts = np.asarray(starts, dtype=np.int64)
        self.weights = weight_array
        self.stakes = self.DEFAULT_STAKES.copy()
        self.stake_weights = np.full(len(self.stakes), 1 / len(self.stakes), dtype=float)
        self.log_start_weights = np.log(self.weights)
        self.log_stake_weights = np.log(self.stake_weights)
        self.log_wealth = np.zeros((len(self.starts), len(self.stakes)), dtype=float)
        self.time = 0

    @property
    def log_e_value(self) -> float:
        component_log_e = logsumexp(self.log_wealth + self.log_stake_weights, axis=1)
        component_log_e = np.where(self.time >= self.starts, component_log_e, 0.0)
        return float(logsumexp(component_log_e + self.log_start_weights))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        active = self.time >= self.starts
        self.log_wealth[active] += np.log1p(self.stakes * (value / self.bound))
        self.time += 1
        return self.log_e_value


class HorizonHedgedStartedMixtureEProcess(StartedMixtureEProcess):
    """Fixed convex mixture over candidate horizons and start-time priors.

    If each component is an e-process under the same filtration, mixing first
    over start positions and then over horizon hypotheses preserves the
    e-process property by linearity. The horizon and start weights are fixed
    before the stream; this class does not adapt weights to observed outcomes.
    """

    def __init__(
        self,
        *,
        bound: float,
        alpha: float,
        horizons: tuple[int, ...],
        horizon_weights: tuple[float, ...],
        start_fractions: tuple[float, ...],
        start_weights: tuple[float, ...],
    ):
        horizon_weight_array = np.asarray(horizon_weights, dtype=float)
        start_weight_array = np.asarray(start_weights, dtype=float)
        fractions = np.asarray(start_fractions, dtype=float)
        if (
            not horizons
            or any(
                isinstance(h, bool) or not isinstance(h, (int, np.integer)) or h <= 0
                for h in horizons
            )
            or len(set(horizons)) != len(horizons)
        ):
            raise ValueError("horizons must be unique positive integers")
        if (
            horizon_weight_array.shape != (len(horizons),)
            or not np.isfinite(horizon_weight_array).all()
            or np.any(horizon_weight_array <= 0)
            or not np.isclose(horizon_weight_array.sum(), 1.0)
        ):
            raise ValueError("horizon_weights must be positive, sum to one, and match horizons")
        if (
            not len(fractions)
            or fractions.shape != start_weight_array.shape
            or not np.isfinite(fractions).all()
            or np.any((fractions < 0) | (fractions > 1))
            or np.any(np.diff(fractions) <= 0)
        ):
            raise ValueError("start_fractions must be finite, increasing, and lie in [0, 1]")
        if (
            not np.isfinite(start_weight_array).all()
            or np.any(start_weight_array <= 0)
            or not np.isclose(start_weight_array.sum(), 1.0)
        ):
            raise ValueError("start_weights must be positive and sum to one")

        component_weights: dict[int, float] = {}
        for horizon, horizon_weight in zip(horizons, horizon_weight_array, strict=True):
            for fraction, start_weight in zip(fractions, start_weight_array, strict=True):
                start = round(int(horizon) * float(fraction))
                component_weights[start] = component_weights.get(start, 0.0) + float(
                    horizon_weight * start_weight
                )
        starts = tuple(sorted(component_weights))
        weights = tuple(component_weights[start] for start in starts)
        super().__init__(bound=bound, alpha=alpha, starts=starts, weights=weights)
        self.horizons = tuple(int(horizon) for horizon in horizons)
        self.horizon_weights = horizon_weight_array
        self.start_fractions = fractions
        self.start_weights = start_weight_array
