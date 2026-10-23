"""Prediction-powered estimates for selectively observed paired decision losses."""

from __future__ import annotations

import numpy as np


def prediction_powered_estimate(
    proxy_value: float,
    query_indicator: bool,
    observed_value: float | None,
    propensity: float,
) -> float:
    """Return h + I/q (Z-h), validating the pre-outcome propensity contract.

    ``proxy_value`` must be formed without the current outcome. ``propensity`` is the
    probability selected before observing that outcome and ``observed_value`` must be
    supplied exactly when the label was queried and arrived immediately.
    """
    if not np.isfinite(proxy_value):
        raise ValueError("proxy_value must be finite")
    if not np.isfinite(propensity) or not 0 < propensity <= 1:
        raise ValueError("propensity must lie in (0, 1]")
    if query_indicator:
        if observed_value is None or not np.isfinite(observed_value):
            raise ValueError("a queried label requires a finite observed_value")
        return float(proxy_value + (observed_value - proxy_value) / propensity)
    if observed_value is not None:
        raise ValueError("unqueried outcomes must not be passed to the estimator")
    return float(proxy_value)


def prediction_powered_bound(outcome_bound: float, min_propensity: float) -> float:
    """Uniform absolute bound for ``h + I/q (Z-h)`` over |Z|, |h| <= M."""
    if not np.isfinite(outcome_bound) or outcome_bound <= 0:
        raise ValueError("outcome_bound must be finite and positive")
    if not np.isfinite(min_propensity) or not 0 < min_propensity <= 1:
        raise ValueError("min_propensity must lie in (0, 1]")
    return float(outcome_bound * (2 / min_propensity - 1))


class AdaptiveReliance:
    """Prequential PPRM-style scalar tuning of reliance on a loss proxy.

    The plug-in coefficient is estimated only from historical labeled outcomes and
    can be updated after each queried label arrives. This is an analogue of PPRM's
    predictable proxy-reliance tuning, not a reproduction of its batch risk bounds.
    """

    def __init__(self, *, query_fraction: float, max_reliance: float = 10.0):
        if not np.isfinite(query_fraction) or not 0 < query_fraction <= 1:
            raise ValueError("query_fraction must lie in (0, 1]")
        if not np.isfinite(max_reliance) or max_reliance <= 0:
            raise ValueError("max_reliance must be finite and positive")
        self.query_fraction = float(query_fraction)
        self.max_reliance = float(max_reliance)
        self.proxy_values: list[float] = []
        self.observed_values: list[float] = []
        self.reliance = 0.0

    def fit(self, proxy_values: np.ndarray, observed_values: np.ndarray) -> AdaptiveReliance:
        proxy = np.asarray(proxy_values, dtype=float).reshape(-1)
        observed = np.asarray(observed_values, dtype=float).reshape(-1)
        if len(proxy) != len(observed) or len(proxy) < 2:
            raise ValueError("proxy and observed histories must match and contain >=2 rows")
        if not np.isfinite(proxy).all() or not np.isfinite(observed).all():
            raise ValueError("historical proxy and observed values must be finite")
        self.proxy_values = proxy.tolist()
        self.observed_values = observed.tolist()
        self._refit()
        return self

    def observe(self, proxy_value: float, observed_value: float) -> None:
        if not np.isfinite(proxy_value) or not np.isfinite(observed_value):
            raise ValueError("arrived proxy and outcome values must be finite")
        self.proxy_values.append(float(proxy_value))
        self.observed_values.append(float(observed_value))
        self._refit()

    def _refit(self) -> None:
        proxy = np.asarray(self.proxy_values, dtype=float)
        observed = np.asarray(self.observed_values, dtype=float)
        variance = float(np.var(proxy))
        if len(proxy) < 2 or variance <= 1e-12:
            self.reliance = 0.0
            return
        covariance = float(np.mean((proxy - proxy.mean()) * (observed - observed.mean())))
        if self.query_fraction == 1:
            self.reliance = 0.0
            return
        label_to_unlabeled = self.query_fraction / (1 - self.query_fraction)
        estimate = covariance / ((1 + label_to_unlabeled) * variance)
        self.reliance = float(np.clip(estimate, 0.0, self.max_reliance))
