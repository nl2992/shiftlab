"""Prediction-powered e-values for selectively observed outcomes.

This module implements the missing-label transformation from Csillag et al.,
"Prediction-Powered E-Values" (ICML 2025). It transforms a nonnegative base
e-value using a predictable proxy and a predictable label-query propensity.
It is a factor-level construction: validity still depends on the base factor
being an e-value under the chosen null and on the query indicator being
conditionally randomized with its recorded propensity.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def minimum_query_probability(*, lower: float, upper: float) -> float:
    """Smallest query propensity guaranteeing a nonnegative PPE factor.

    The base factor must lie in ``[lower, upper]``. The paper's condition is
    ``q >= 1 - lower / upper``. For a betting factor ``1 + lambda*z/B`` with
    ``|z| <= B``, this becomes ``q >= 2*lambda/(1+lambda)``.
    """
    if not np.isfinite(lower) or not np.isfinite(upper) or lower <= 0 or upper < lower:
        raise ValueError("factor bounds must satisfy 0 < lower <= upper")
    return float(1.0 - lower / upper)


def prediction_powered_factor(
    *,
    proxy_factor: float,
    queried: bool,
    propensity: float,
    lower: float,
    upper: float,
    observed_factor: float | None = None,
) -> float:
    """Return one PPE factor without exposing unqueried outcomes to the learner.

    ``proxy_factor`` and ``propensity`` must be fixed before the current label
    arrives. If queried, the returned factor is
    ``proxy_factor + (observed_factor - proxy_factor) / propensity``; otherwise
    it is the proxy factor. The function enforces the paper's propensity floor
    so the corrected factor is nonnegative for every admissible base factor.
    """
    if not np.isfinite(lower) or not np.isfinite(upper) or lower <= 0 or upper < lower:
        raise ValueError("factor bounds must satisfy 0 < lower <= upper")
    if not np.isfinite(propensity) or not 0 < propensity <= 1:
        raise ValueError("propensity must lie in (0, 1]")
    if not np.isfinite(proxy_factor) or not lower <= proxy_factor <= upper:
        raise ValueError("proxy factor must lie within the declared base-factor bounds")
    if propensity + 1e-12 < minimum_query_probability(lower=lower, upper=upper):
        raise ValueError("propensity is below the PPE nonnegativity threshold")

    if not queried:
        if observed_factor is not None:
            raise ValueError("an unqueried outcome must not be supplied to the learner")
        return float(proxy_factor)
    if observed_factor is None or not np.isfinite(observed_factor):
        raise ValueError("a queried event requires a finite observed factor")
    if not lower <= observed_factor <= upper:
        raise ValueError("observed factor must lie within the declared base-factor bounds")
    corrected = proxy_factor + (observed_factor - proxy_factor) / propensity
    if corrected < -1e-12:
        raise ArithmeticError("PPE correction became negative despite validated bounds")
    return float(max(0.0, corrected))


@dataclass(frozen=True)
class PPEUpdate:
    """Audit record for one predictable PPE update."""

    factor: float
    queried: bool
    propensity: float
    proxy_factor: float


class PredictionPoweredEProcess:
    """Product of prediction-powered factors for one fixed base process.

    This class does not establish that the base factors are valid e-values.
    The caller must justify the null, filtration, base-factor conditional
    expectation, proxy predictability, and randomized/missing-at-random query
    mechanism for the application.
    """

    def __init__(self, *, lower: float, upper: float) -> None:
        minimum_query_probability(lower=lower, upper=upper)
        self.lower = float(lower)
        self.upper = float(upper)
        self.wealth = 1.0
        self.updates: list[PPEUpdate] = []

    def update(
        self,
        *,
        proxy_factor: float,
        queried: bool,
        propensity: float,
        observed_factor: float | None = None,
    ) -> float:
        """Append one factor, requiring omitted outcomes to stay omitted."""
        factor = prediction_powered_factor(
            proxy_factor=proxy_factor,
            queried=queried,
            propensity=propensity,
            lower=self.lower,
            upper=self.upper,
            observed_factor=observed_factor,
        )
        self.wealth *= factor
        self.updates.append(
            PPEUpdate(
                factor=factor,
                queried=queried,
                propensity=float(propensity),
                proxy_factor=float(proxy_factor),
            )
        )
        return self.wealth

    @property
    def log_wealth(self) -> float:
        return float(np.log(self.wealth)) if self.wealth > 0 else float("-inf")
