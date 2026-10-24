"""Event-order buffering for decision-harm evidence with delayed labels.

This module preserves the event-time order of evidence increments when queried
labels arrive out of order. It is an ordering primitive, not a validity result:
callers must separately justify their estimand, filtration, propensity weights,
and conditional-mean null.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ResolvedEvidence:
    """An evidence increment released in event order."""

    event_index: int
    event_time: float
    available_time: float
    value: float

    @property
    def feedback_delay(self) -> float:
        return self.available_time - self.event_time


class EventOrderBuffer:
    """Release resolved increments only when the contiguous event prefix is ready.

    Register every event once, in increasing index order. An immediately
    available proxy increment can be supplied at registration. If a queried
    label is pending, register with ``value=None`` and resolve it exactly once
    when feedback arrives. A later event may resolve first, but it remains
    buffered until every earlier event has resolved.
    """

    def __init__(self) -> None:
        self._next_registration = 0
        self._next_release = 0
        self._last_event_time = float("-inf")
        self._pending: dict[int, tuple[float, float | None, float | None]] = {}

    @property
    def pending_count(self) -> int:
        return sum(value is None for _, value, _ in self._pending.values())

    @property
    def buffered_count(self) -> int:
        return len(self._pending)

    def register(
        self, event_index: int, event_time: float, value: float | None = None
    ) -> list[ResolvedEvidence]:
        """Register an event and release any newly contiguous resolved prefix."""
        if event_index != self._next_registration:
            raise ValueError("events must be registered exactly once in index order")
        if not isfinite(event_time) or event_time < self._last_event_time:
            raise ValueError("event times must be finite and nondecreasing")
        if value is not None and not isfinite(value):
            raise ValueError("evidence values must be finite")
        self._pending[event_index] = (
            float(event_time),
            value,
            float(event_time) if value is not None else None,
        )
        self._next_registration += 1
        self._last_event_time = float(event_time)
        return self._drain()

    def resolve(
        self, event_index: int, *, available_time: float, value: float
    ) -> list[ResolvedEvidence]:
        """Attach an arrived label-derived increment and release ready events."""
        if event_index not in self._pending:
            raise ValueError("event is unknown, already released, or was not registered")
        event_time, existing_value, _ = self._pending[event_index]
        if existing_value is not None:
            raise ValueError("event evidence has already been resolved")
        if not isfinite(available_time) or available_time < event_time:
            raise ValueError("feedback availability must be finite and no earlier than its event")
        if not isfinite(value):
            raise ValueError("evidence values must be finite")
        self._pending[event_index] = (event_time, float(value), float(available_time))
        return self._drain()

    def _drain(self) -> list[ResolvedEvidence]:
        released: list[ResolvedEvidence] = []
        while self._next_release in self._pending:
            event_time, value, available_time = self._pending[self._next_release]
            if value is None:
                break
            assert available_time is not None
            released.append(ResolvedEvidence(self._next_release, event_time, available_time, value))
            del self._pending[self._next_release]
            self._next_release += 1
        return released
