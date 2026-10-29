"""v2 adapters for the in-repo baselines, and a trivial alarm-then-switch ``Switcher``.

``DelayedHT`` wraps a v1 Horvitz-Thompson baseline (``GatedHTFixed``, ``GatedHTPaced``,
``UniformHT``). The propensity and its predictable support bound are fixed at the event, the
pacer advances at the event (it uses only public disagreement and price), and the e-process
increment of a bought query is applied when its label is released, in release order. An
unqueried event is applied immediately. A ``MissingFeedback`` is applied as an unobserved label
(HT term 0), which is a conservative missing-at-random simplification, not a validity claim.
Validity of the e-process under delayed, out-of-order updating is NOT established here: with
delay 0 and no missing labels this reproduces the v1 monitor exactly; otherwise results are
descriptive.

``V1MonitorShim`` runs an unmodified v1 monitor in the v2 harness and rejects any delayed or
missing outcome, so it can only be used where v2 must reproduce v1.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .baselines import _HorvitzThompsonMonitor
from .interface import Feedback, Monitor, PublicEvent, TaskSpec
from .interface_v2 import (
    Delivery,
    MissingFeedback,
    MonitorV2,
    PendingQuery,
    QueryOutcome,
    SwitchContext,
)


class V1MonitorShim:
    """Adapt a v1 ``Monitor`` for streams with no delay and no missing labels."""

    def __init__(self, monitor: Monitor) -> None:
        self._monitor = monitor

    def reset(self, spec: TaskSpec) -> None:
        self._monitor.reset(spec)

    def receive(self, t: int, released: Sequence[Delivery]) -> None:
        if released:
            raise ValueError("a v1 monitor cannot receive delayed feedback")

    def propensity(self, event: PublicEvent) -> float:
        return self._monitor.propensity(event)

    def observe(self, event: PublicEvent, outcome: QueryOutcome) -> None:
        if isinstance(outcome, (PendingQuery, MissingFeedback)):
            raise TypeError("a v1 monitor cannot handle pending or missing feedback")
        self._monitor.observe(event, outcome)

    @property
    def log_e_value(self) -> float:
        return self._monitor.log_e_value


class DelayedHT:
    """Delay-aware wrapper for the HT baselines (see module docstring for the update rule)."""

    def __init__(self, inner: _HorvitzThompsonMonitor) -> None:
        self._inner = inner
        self._pending: dict[int, tuple[PublicEvent, float]] = {}

    def reset(self, spec: TaskSpec) -> None:
        self._inner.reset(spec)
        self._pending = {}

    def receive(self, t: int, released: Sequence[Delivery]) -> None:
        for item in released:
            event, latent = self._pending.pop(item.t)
            observed = float(item.paired_cost) if isinstance(item, Feedback) else None
            self._apply(event, observed, latent)

    def propensity(self, event: PublicEvent) -> float:
        return self._inner.propensity(event)

    def observe(self, event: PublicEvent, outcome: QueryOutcome) -> None:
        inner = self._inner
        if isinstance(outcome, PendingQuery):
            if outcome.propensity != inner._returned_q or inner._latent_q is None:
                raise ValueError("pending query propensity differs from the one returned")
            self._pending[event.t] = (event, inner._latent_q)
            inner._after_event(event)  # public-only pacing step; the e-process waits for the label
            inner._latent_q = inner._returned_q = None
        elif isinstance(outcome, MissingFeedback):
            inner.observe(event, None)  # unobserved label: HT term 0
        else:
            inner.observe(event, outcome)

    def _apply(self, event: PublicEvent, observed: float | None, latent: float) -> None:
        inner = self._inner
        spec = inner._spec
        assert spec is not None and inner._process is not None
        if observed is not None and abs(observed) > spec.cost_bound:
            raise ValueError("observed paired cost must lie in [-C, C]")
        value = inner._increment(event, observed, latent)
        bound = spec.cost_bound / latent + spec.epsilon
        if abs(value) > bound:
            if abs(value) - bound > 1e-9 * bound:
                raise ValueError("increment exceeds its predictable support bound")
            value = float(np.copysign(bound, value))
        inner._process.update(value, bound=bound)

    @property
    def log_e_value(self) -> float:
        return self._inner.log_e_value


class AlarmThenSwitch:
    """Trivial ``Switcher``: deploy the candidate from the round after the first alarm, never back.

    The alarm is the wrapped monitor's ``log_e_value >= log(1/alpha)`` read at the start of a round
    (after that round's releases), so the switch uses public information only. This is a plumbing
    baseline, not a method: an alarm alone does not establish economic benefit of switching.
    """

    def __init__(self, monitor: MonitorV2) -> None:
        self._monitor = monitor
        self._threshold = float("inf")
        self._switched = False

    def reset(self, spec: TaskSpec) -> None:
        self._monitor.reset(spec)
        self._threshold = -float(np.log(spec.alpha))
        self._switched = False

    def receive(self, t: int, released: Sequence[Delivery]) -> None:
        self._monitor.receive(t, released)

    def choose(self, event: PublicEvent, context: SwitchContext) -> int:
        if not self._switched and self._monitor.log_e_value >= self._threshold:
            self._switched = True
        return 1 if self._switched else 0

    def propensity(self, event: PublicEvent) -> float:
        return self._monitor.propensity(event)

    def observe(self, event: PublicEvent, outcome: QueryOutcome) -> None:
        self._monitor.observe(event, outcome)

    @property
    def log_e_value(self) -> float:
        return self._monitor.log_e_value
