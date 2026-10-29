"""v2 adapters for the in-repo baselines, and a trivial alarm-then-switch ``Switcher``.

``DelayedHT`` wraps a v1 Horvitz-Thompson baseline (``GatedHTFixed``, ``GatedHTPaced``,
``UniformHT``). The propensity and its predictable support bound are fixed at the event, the
pacer advances at the event (it uses only public disagreement and price), and the e-process
increment of a bought query is applied when its label is released, in release order. An
unqueried event is applied immediately. A ``MissingFeedback`` applies the increment ``-epsilon``
at release (HT term 0 minus ``epsilon``; the update is never skipped), valid only under
missingness at random given the public past (see ``R3_delayed_update_validity_note.md``).
Labels must be released in event order (non-decreasing event index); an out-of-order release
raises ``OutOfOrderRelease`` because updating in release order is not valid in general. Pass
``allow_out_of_order=True`` only for diagnostics, never for validity claims. With delay 0 and no
missing labels this reproduces the v1 monitor exactly.

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


class OutOfOrderRelease(ValueError):
    """A label was released after the label of a later event (release order != event order)."""


class DelayedHT:
    """Delay-aware wrapper for the HT baselines (see module docstring for the update rule)."""

    def __init__(self, inner: _HorvitzThompsonMonitor, *, allow_out_of_order: bool = False) -> None:
        self._inner = inner
        self._allow_out_of_order = allow_out_of_order
        self._pending: dict[int, tuple[PublicEvent, float]] = {}
        self._last_released = -1

    def reset(self, spec: TaskSpec) -> None:
        self._inner.reset(spec)
        self._pending = {}
        self._last_released = -1

    def _note_release(self, t: int) -> None:
        if t < self._last_released and not self._allow_out_of_order:
            raise OutOfOrderRelease(
                f"label of event {t} released after the label of event {self._last_released}; "
                "release-order updating is not valid in general (allow_out_of_order is for "
                "diagnostics only)"
            )
        self._last_released = max(self._last_released, t)

    def receive(self, t: int, released: Sequence[Delivery]) -> None:
        for item in released:
            self._note_release(item.t)
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
            self._note_release(event.t)
            inner.observe(event, None)  # missing label: increment -epsilon, never skipped
        else:
            if outcome is not None:
                self._note_release(event.t)
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
