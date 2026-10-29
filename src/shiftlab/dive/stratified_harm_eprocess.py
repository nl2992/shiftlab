"""Fixed-bound per-stratum e-processes and standard multiplicity combinations."""

from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.special import logsumexp

from shiftlab.dive.eprocess import BoundedMeanEProcess


class StratifiedEProcess:
    """Compose bounded-mean e-processes for a fixed set of strata.

    Each stratum has a fixed symmetric bound and its own component process for
    ``E[value_t | past, stratum_t=k] <= 0``. An update advances only the selected
    component; an unobserved component therefore remains at e-value one.

    ``combination="mixture"`` uses the fixed convex mixture of component
    e-values. ``combination="bonferroni"`` alarms if any component crosses its
    allocated threshold ``1 / (alpha * stratum_weight)``. These are standard
    compositions and do not establish the component nulls or their filtration
    assumptions.
    """

    def __init__(
        self,
        *,
        bounds: tuple[float, ...],
        alpha: float = 0.05,
        weights: tuple[float, ...] | None = None,
        combination: Literal["bonferroni", "mixture"] = "mixture",
        stakes: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8),
        stake_weights: tuple[float, ...] | None = None,
    ) -> None:
        try:
            bound_values = tuple(float(bound) for bound in bounds)
        except (TypeError, ValueError) as exc:
            raise ValueError("bounds must be a nonempty tuple of finite positive values") from exc
        if not bound_values or any(not np.isfinite(bound) or bound <= 0 for bound in bound_values):
            raise ValueError("bounds must be a nonempty tuple of finite positive values")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie in (0, 1)")
        if combination not in ("bonferroni", "mixture"):
            raise ValueError("combination must be 'bonferroni' or 'mixture'")

        count = len(bound_values)
        if weights is None:
            weight_values = tuple(1.0 / count for _ in bound_values)
        else:
            try:
                weight_values = tuple(float(weight) for weight in weights)
            except (TypeError, ValueError) as exc:
                raise ValueError("stratum weights must be positive and sum to one") from exc
            if (
                len(weight_values) != count
                or any(not np.isfinite(weight) or weight <= 0 for weight in weight_values)
                or not np.isclose(sum(weight_values), 1.0)
            ):
                raise ValueError("stratum weights must be positive and sum to one")

        self._bounds = bound_values
        self.alpha = float(alpha)
        self.weights = weight_values
        self.combination = combination
        self._components = tuple(
            BoundedMeanEProcess(
                bound=bound,
                alpha=alpha,
                stakes=stakes,
                weights=stake_weights,
            )
            for bound in self._bounds
        )

    @property
    def bounds(self) -> tuple[float, ...]:
        """Immutable bounds fixed at construction."""
        return self._bounds

    @property
    def component_log_e_values(self) -> tuple[float, ...]:
        """Current log e-value for each stratum's component process."""
        return tuple(component.log_e_value for component in self._components)

    @property
    def log_e_mixture(self) -> float:
        """Log of the fixed convex mixture, whether or not it is the alarm rule."""
        return float(logsumexp(np.log(self.weights) + self.component_log_e_values))

    @property
    def adjusted_max_log_statistic(self) -> float:
        """Maximum weight-adjusted component log evidence for Bonferroni testing."""
        return float(max(np.log(self.weights) + self.component_log_e_values))

    @property
    def log_statistic(self) -> float:
        """Selected alarm statistic, with common threshold ``-log(alpha)``."""
        if self.combination == "mixture":
            return self.log_e_mixture
        return self.adjusted_max_log_statistic

    @property
    def alarm(self) -> bool:
        """Whether the selected combination has crossed its level-alpha threshold."""
        return self.log_statistic >= -np.log(self.alpha)

    def update(self, stratum: int, value: float) -> float:
        """Update one predeclared stratum and return the selected log statistic."""
        if isinstance(stratum, bool) or not isinstance(stratum, (int, np.integer)):
            raise TypeError("stratum must be an integer index")
        if not 0 <= stratum < len(self._components):
            raise ValueError("stratum index is outside the fixed bounds")
        self._components[int(stratum)].update(value)
        return self.log_statistic
