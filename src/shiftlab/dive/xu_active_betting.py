"""Formula-level Xu et al. active betting transfer to paired decision cost.

The published paper tests a bounded risk ``R in [0, 1]`` with null
``E[R] >= theta`` and factor
``1 + lambda * (theta - rhat - L/q * (R - rhat))``.  For paired excess
cost ``Z = c(pi,Y) - c(ref,Y) - epsilon`` bounded by ``bound`` in absolute
value, map ``R = 1/2 - Z/(2*bound)`` and ``theta = 1/2``.  The resulting
factor grows for positive harm and is an e-factor under the conditional null
``E[Z | past] <= 0`` when the proxy, query propensity, and stake are
predictable and labels are queried with that propensity.

This module implements only the scalar formula and a wrapper around the
repository's existing square-root residual-moment query policy.  It does not
validate a data-generating process, identify counterfactual costs, or establish
that a fitted proxy/query policy is calibrated after distribution shift.
"""

from __future__ import annotations

import numpy as np

from shiftlab.dive.query import AdaptiveQueryPolicy

_FACTOR_TOL = 1e-12


def xu_minimum_query_probability(*, stake: float) -> float:
    """Return Xu et al.'s minimum propensity for a nonnegative factor.

    With ``theta=1/2``, the source restriction is
    ``lambda <= 1 / (1/q_min - theta)``, equivalently
    ``q_min >= lambda / (1 + lambda*theta)``.  Equality can permit a zero
    factor at a support endpoint.
    """
    if not np.isfinite(stake) or stake <= 0:
        raise ValueError("stake must be finite and positive")
    return float(stake / (1.0 + 0.5 * stake))


def xu_maximum_stake(*, minimum_propensity: float) -> float:
    """Return the source-compatible stake cap for ``theta=1/2``."""
    if not np.isfinite(minimum_propensity) or not 0 < minimum_propensity <= 1:
        raise ValueError("minimum_propensity must lie in (0, 1]")
    return float(1.0 / (1.0 / minimum_propensity - 0.5))


def xu_paired_betting_factor(
    *,
    proxy_excess_cost: float,
    queried: bool,
    propensity: float,
    stake: float,
    bound: float,
    observed_excess_cost: float | None = None,
) -> float:
    """Compute one Xu predictor-based factor for paired excess cost.

    ``proxy_excess_cost`` and the observed score are in original cost units and
    must lie in ``[-bound, bound]``.  Their normalized score is ``z=Z/(2B)``;
    thus the corresponding Xu risk and predictor are ``R=1/2-z`` and
    ``rhat=1/2-zhat``.  An unqueried event contributes the predictable proxy
    factor. A queried event uses the Horvitz--Thompson correction.
    """
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("bound must be finite and positive")
    if not np.isfinite(stake) or stake <= 0:
        raise ValueError("stake must be finite and positive")
    if not np.isfinite(propensity) or not 0 < propensity <= 1:
        raise ValueError("propensity must lie in (0, 1]")
    if propensity < xu_minimum_query_probability(stake=stake):
        raise ValueError("propensity is below the Xu nonnegativity floor for this stake")
    if not np.isfinite(proxy_excess_cost) or abs(proxy_excess_cost) > bound + 1e-12:
        raise ValueError("proxy_excess_cost must lie within [-bound, bound]")

    proxy_score = float(proxy_excess_cost / (2.0 * bound))
    if queried:
        if observed_excess_cost is None or not np.isfinite(observed_excess_cost):
            raise ValueError("a queried event requires a finite observed excess cost")
        if abs(observed_excess_cost) > bound + 1e-12:
            raise ValueError("observed_excess_cost must lie within [-bound, bound]")
        observed_score = float(observed_excess_cost / (2.0 * bound))
        corrected_score = proxy_score + (observed_score - proxy_score) / propensity
    else:
        if observed_excess_cost is not None:
            raise ValueError("an unqueried outcome must not be supplied to the learner")
        corrected_score = proxy_score

    factor = 1.0 + stake * corrected_score
    # The published weak inequality allows zero at the exact floor. Permit
    # tiny negative round-off there, but reject genuine support violations.
    if factor < -_FACTOR_TOL:
        raise ArithmeticError("Xu betting factor is negative beyond numerical tolerance")
    return float(max(0.0, factor))


class XuActivePairedEProcess:
    """Product process using the Xu predictor-based paired-cost factor."""

    def __init__(self, *, bound: float, stake: float, minimum_propensity: float) -> None:
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(minimum_propensity) or not 0 < minimum_propensity <= 1:
            raise ValueError("minimum_propensity must lie in (0, 1]")
        if not np.isfinite(stake) or stake <= 0:
            raise ValueError("stake must be finite and positive")
        if stake > xu_maximum_stake(minimum_propensity=minimum_propensity) + _FACTOR_TOL:
            raise ValueError("stake exceeds the Xu cap implied by minimum_propensity")
        self.bound = float(bound)
        self.stake = float(stake)
        self.minimum_propensity = float(minimum_propensity)
        self.log_wealth = 0.0

    @property
    def wealth(self) -> float:
        """Current wealth, derived from the numerically stable log state."""
        return float(np.exp(self.log_wealth)) if self.log_wealth > -746.0 else 0.0

    def update(
        self,
        *,
        proxy_excess_cost: float,
        queried: bool,
        propensity: float,
        observed_excess_cost: float | None = None,
    ) -> float:
        if propensity < self.minimum_propensity:
            raise ValueError("propensity is below the process minimum_propensity")
        factor = xu_paired_betting_factor(
            proxy_excess_cost=proxy_excess_cost,
            queried=queried,
            propensity=propensity,
            stake=self.stake,
            bound=self.bound,
            observed_excess_cost=observed_excess_cost,
        )
        self.log_wealth = (
            float("-inf") if factor == 0.0 else self.log_wealth + float(np.log(factor))
        )
        return self.wealth


def xu_variance_query_policy(
    *,
    target_rate: float,
    minimum_propensity: float,
    maximum_propensity: float,
    stake: float,
) -> AdaptiveQueryPolicy:
    """Build the repository's clipped square-root-moment Xu query policy.

    Pass a pre-outcome proxy and its predicted residual second moment to the
    returned policy's ``fit_multiplier``/``probabilities`` methods.  The
    ``variance`` score uses ``sqrt(residual_second_moment)``, matching Xu et
    al.'s ``q*(x) proportional to sqrt(E[(R-rhat)^2 | X=x])`` up to the common
    paired-score scale. Multiplier fitting is a finite validation-slice
    approximation to the paper's population budget constraint.
    """
    required_floor = xu_minimum_query_probability(stake=stake)
    if minimum_propensity < required_floor:
        raise ValueError("minimum_propensity is below the Xu stake's validity floor")
    return AdaptiveQueryPolicy(
        "variance",
        target_rate=target_rate,
        q_min=minimum_propensity,
        q_max=maximum_propensity,
        variance_power=0.5,
    )
