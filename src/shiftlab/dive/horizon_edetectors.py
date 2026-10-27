"""Finite-horizon Shiryaev-Roberts and CUSUM e-detectors.

The score supplied to this module must yield a predictable bounded e-factor
under the null. The implementation does not verify that scientific condition.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import logsumexp


class HorizonCalibratedEDetector:
    """SR or CUSUM e-detector with a fixed finite-horizon false-alarm bound.

    At each calendar time, a non-skipped score ``x`` with ``|x| <= bound`` is
    converted to the fixed-stake e-factors ``1 + stake * x / bound``. A skipped
    time contributes factor one. In particular, a skip still opens a new
    calendar-time start in the SR/CUSUM recursions.

    ``alarm_time`` is the one-based calendar position of the first crossing.
    This differs from the zero-based ``first_alarm`` convention used by WP1.

    For horizon ``H`` and null-conditional e-factors, the selected statistic
    satisfies ``P(max_{t <= H} statistic_t >= H / alpha) <= alpha``. This is a
    finite-horizon guarantee; it is not an anytime-valid ``1 / alpha`` e-value
    threshold. The horizon, detector kind, stakes, and mixture weights are fixed
    at construction. A skip decision must be predictable under the null
    filtration, and callers remain responsible for validity of the score and
    any adaptive sampling or feedback assumptions.
    """

    def __init__(
        self,
        *,
        bound: float,
        horizon: int,
        alpha: float = 0.05,
        kind: str = "sr",
        stakes: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8),
        weights: tuple[float, ...] | None = None,
    ):
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise ValueError("horizon must be a positive integer")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        if kind not in {"sr", "cusum"}:
            raise ValueError("kind must be 'sr' or 'cusum'")
        stake_array = np.asarray(stakes, dtype=float)
        if (
            stake_array.ndim != 1
            or not len(stake_array)
            or not np.isfinite(stake_array).all()
            or np.any((stake_array <= 0) | (stake_array > 1))
        ):
            raise ValueError("stakes must be a nonempty finite vector in (0, 1]")
        if weights is None:
            weight_array = np.full(len(stake_array), 1.0 / len(stake_array))
        else:
            weight_array = np.asarray(weights, dtype=float)
            if (
                weight_array.shape != stake_array.shape
                or not np.isfinite(weight_array).all()
                or np.any(weight_array <= 0)
                or not np.isclose(weight_array.sum(), 1.0)
            ):
                raise ValueError("weights must be positive, sum to one, and match stakes")

        self.bound = float(bound)
        self.horizon = horizon
        self.alpha = float(alpha)
        self.kind = kind
        self.stakes = stake_array
        self.weights = weight_array
        self._log_weights = np.log(weight_array)
        self._log_components = np.full(len(stake_array), -np.inf, dtype=float)
        self.n_updates = 0
        self.alarm_time: int | None = None

    @property
    def log_threshold(self) -> float:
        """Log of the finite-horizon threshold ``horizon / alpha``."""
        return math.log(self.horizon) - math.log(self.alpha)

    @property
    def threshold(self) -> float:
        """Finite-horizon threshold, or infinity if it exceeds float range."""
        try:
            return math.exp(self.log_threshold)
        except OverflowError:
            return math.inf

    @property
    def component_log_statistics(self) -> tuple[float, ...]:
        """Log SR/CUSUM statistics for the fixed stake components."""
        return tuple(float(value) for value in self._log_components)

    @property
    def log_statistic(self) -> float:
        """Log fixed-weight mixture statistic at the latest calendar time."""
        if self.n_updates == 0:
            return -np.inf
        return float(logsumexp(self._log_components + self._log_weights))

    @property
    def alarm(self) -> bool:
        """Whether the fixed finite-horizon threshold has ever been crossed."""
        return self.alarm_time is not None

    def update(self, value: float | None = None, *, skip: bool = False) -> float:
        """Advance one calendar time and return the log mixture statistic.

        When ``skip`` is true, ``value`` is ignored and every component uses
        factor one. The recursion still advances, preserving a new start at this
        calendar time. Updates beyond the registered horizon raise RuntimeError.
        """
        if self.n_updates >= self.horizon:
            raise RuntimeError("registered horizon has been exhausted")
        if not isinstance(skip, bool):
            raise TypeError("skip must be a boolean")
        if skip:
            log_factors = np.zeros_like(self.stakes)
        else:
            if value is None or not np.isfinite(value) or abs(value) > self.bound:
                raise ValueError("value must be finite and within the declared bound")
            scaled = self.stakes * (float(value) / self.bound)
            with np.errstate(divide="ignore"):
                log_factors = np.log1p(scaled)

        if self.kind == "sr":
            self._log_components = log_factors + np.logaddexp(0.0, self._log_components)
        else:
            self._log_components = log_factors + np.maximum(0.0, self._log_components)
        self.n_updates += 1
        result = self.log_statistic
        if self.alarm_time is None and result >= self.log_threshold:
            self.alarm_time = self.n_updates
        return result
