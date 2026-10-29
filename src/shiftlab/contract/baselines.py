"""In-repo baselines implemented as contract ``Monitor`` objects (parity with ``replay_gated``).

These may import ``shiftlab.dive``; external adapters may not. Each wraps the existing
``gated_increment`` and ``PredictableBoundMeanEProcess`` so results can be compared exactly.
Validity rests on the same conditions as the underlying e-process: the eventwise null
``E[Z_t - epsilon | past] <= 0``, a propensity that is predictable before the coin, and the
bound ``C/q + epsilon`` chosen before the outcome. The wrapper does not establish them.

Gated monitors exploit the disagreement indicator: they return a positive propensity only on
disagreements and 0.0 on agreements (where the cost is known to be zero), while still using
their latent pacing propensity for the support bound, as ``replay_gated`` does. ``UniformHT``
ignores the indicator and pays for labels on agreements too.
"""

from __future__ import annotations

import numpy as np

from ..dive.eprocess import PredictableBoundMeanEProcess
from ..dive.gated_monitor_comparison import DisagreementPacer, gated_increment
from .interface import Feedback, PublicEvent, TaskSpec


class _HorvitzThompsonMonitor:
    """Shared e-process update; subclasses choose the propensity and the increment."""

    def __init__(self) -> None:
        self._spec: TaskSpec | None = None
        self._process: PredictableBoundMeanEProcess | None = None
        self._latent_q: float | None = None  # drives the support bound
        self._returned_q: float | None = None  # what the harness sees

    def reset(self, spec: TaskSpec) -> None:
        self._spec = spec
        self._process = PredictableBoundMeanEProcess(alpha=spec.alpha)
        self._latent_q = self._returned_q = None

    def _choose(self, event: PublicEvent) -> tuple[float, float]:
        """Return (latent q for the bound, q returned to the harness)."""
        raise NotImplementedError

    def _increment(self, event: PublicEvent, observed: float | None, q: float) -> float:
        raise NotImplementedError

    def _after_event(self, event: PublicEvent) -> None:
        return None

    def propensity(self, event: PublicEvent) -> float:
        latent, returned = self._choose(event)
        self._latent_q, self._returned_q = float(latent), float(returned)
        return self._returned_q

    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None:
        if self._spec is None or self._process is None or self._latent_q is None:
            raise RuntimeError("reset and propensity must precede observe")
        spec, q = self._spec, self._latent_q
        observed: float | None = None
        if feedback is not None:
            if feedback.propensity != self._returned_q:
                raise ValueError("feedback propensity differs from the one returned")
            observed = float(feedback.paired_cost)
            if abs(observed) > spec.cost_bound:
                raise ValueError("observed paired cost must lie in [-C, C]")
        value = self._increment(event, observed, q)
        bound = spec.cost_bound / q + spec.epsilon
        if abs(value) > bound:
            if abs(value) - bound > 1e-9 * bound:
                raise ValueError("increment exceeds its predictable support bound")
            value = float(np.copysign(bound, value))
        self._process.update(value, bound=bound)
        self._after_event(event)
        self._latent_q = self._returned_q = None

    @property
    def log_e_value(self) -> float:
        return 0.0 if self._process is None else self._process.log_e_value


class _PacedBase(_HorvitzThompsonMonitor):
    def __init__(
        self,
        *,
        validation_disagreement: np.ndarray,
        validation_tariffs: np.ndarray,
        budget_rate: float,
    ) -> None:
        super().__init__()
        self._validation = (validation_disagreement, validation_tariffs, budget_rate)
        self._pacer: DisagreementPacer | None = None

    def reset(self, spec: TaskSpec) -> None:
        super().reset(spec)
        self._pacer = DisagreementPacer(*self._validation)

    def _pace(self) -> float:
        raise NotImplementedError

    def _choose(self, event: PublicEvent) -> tuple[float, float]:
        q = self._pace()
        return q, (q if event.disagreement else 0.0)

    def _increment(self, event: PublicEvent, observed: float | None, q: float) -> float:
        return gated_increment(
            disagreement=event.disagreement,
            observed_cost=observed,
            propensity=q,
            epsilon=self._spec.epsilon,  # type: ignore[union-attr]
        )

    def _after_event(self, event: PublicEvent) -> None:
        assert self._pacer is not None
        self._pacer.observe(event.disagreement, event.price)


class GatedHTFixed(_PacedBase):
    """Gated HT with the fixed validation-seeded propensity (``gated_ht_fixed``)."""

    def _pace(self) -> float:
        assert self._pacer is not None
        return self._pacer.fixed


class GatedHTPaced(_PacedBase):
    """Gated HT with the 200-event past-only paced propensity (``gated_ht_paced``)."""

    def _pace(self) -> float:
        assert self._pacer is not None
        return self._pacer.propensity


class UniformHT(_HorvitzThompsonMonitor):
    """Constant-q HT monitor that does not exploit the disagreement indicator.

    It returns ``q`` on every event and pays for labels on agreements as well. The increment is
    ``Z/q - epsilon`` for a queried event and ``-epsilon`` otherwise, with bound ``C/q + epsilon``.
    ``q`` must be passed explicitly (for the E2 parity it is the budget rate ``r``, so expected
    spend ``q * E[price]`` matches the gated target); there is no default.
    """

    def __init__(self, q: float) -> None:
        super().__init__()
        if not 0 < q <= 1:
            raise ValueError("q must lie in (0, 1]")
        self._q_value: float = float(q)

    def reset(self, spec: TaskSpec) -> None:
        super().reset(spec)

    def _choose(self, event: PublicEvent) -> tuple[float, float]:
        return self._q_value, self._q_value

    def _increment(self, event: PublicEvent, observed: float | None, q: float) -> float:
        eps = self._spec.epsilon  # type: ignore[union-attr]
        return -eps + (observed / q if observed is not None else 0.0)
