"""Evaluator-owned label broker for strict-streaming multi-model experiments.

Algorithms receive PublicEvent, QueryReceipt and Feedback values only, never the
broker or SyntheticWorld. A receipt discloses purchase and propensity but neither
the label nor its future arrival time. The repository's EventOrderBuffer can be
used by adapters that need evidence in source-event order.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from .generators import PublicEvent, SyntheticWorld


@dataclass(frozen=True)
class QueryReceipt:
    event_index: int
    requested_propensity: float
    effective_propensity: float
    purchased: bool
    remaining_labels: int
    paid: float


@dataclass(frozen=True)
class Feedback:
    event_index: int
    available_time: int
    propensity: float
    outcome: float | None
    predictive_losses: tuple[float, ...] | None
    decision_losses: tuple[float, ...] | None
    missing: bool


class FeedbackStream:
    def __init__(self, world: SyntheticWorld, *, budget: int, query_seed: int):
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ValueError("budget must be a nonnegative label count")
        self._world = world
        self._rng = np.random.default_rng(query_seed)
        self._budget = budget
        self._time = -1
        self._submitted = True
        self._pending: list[tuple[int, int, float]] = []
        self.labels_purchased = 0
        self.money_spent = 0.0

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def _release(self) -> tuple[Feedback, ...]:
        released = []
        truth = self._world.truth
        while self._pending and self._pending[0][0] <= self._time:
            available, index, propensity = heapq.heappop(self._pending)
            missing = bool(truth.missing[index])
            released.append(
                Feedback(
                    index,
                    available,
                    propensity,
                    None if missing else float(truth.outcomes[index]),
                    None if missing else tuple(truth.predictive_losses[index]),
                    None if missing else tuple(truth.decision_losses[index]),
                    missing,
                )
            )
        return tuple(released)

    def open_round(self, time: int) -> tuple[PublicEvent | None, tuple[Feedback, ...]]:
        if time != self._time + 1 or not self._submitted:
            raise ValueError("advance one round at a time after submitting the preceding query")
        self._time = time
        self._submitted = time >= len(self._world.events)
        released = self._release()
        event = self._world.events[time] if time < len(self._world.events) else None
        return event, released

    def request(self, propensity: float) -> tuple[QueryReceipt, tuple[Feedback, ...]]:
        if self._submitted or self._time < 0:
            raise ValueError("each public event permits exactly one query decision")
        if isinstance(propensity, bool) or not np.isfinite(propensity) or not 0 <= propensity <= 1:
            raise ValueError("propensity must be finite in [0, 1]")
        effective = float(propensity) if self.labels_purchased < self._budget else 0.0
        purchased = bool(self._rng.random() < effective)
        event = self._world.events[self._time]
        paid = event.label_cost if purchased else 0.0
        if purchased:
            self.labels_purchased += 1
            self.money_spent += paid
            available = int(self._world.truth.availability[self._time])
            heapq.heappush(self._pending, (available, self._time, effective))
        self._submitted = True
        return QueryReceipt(
            self._time,
            float(propensity),
            effective,
            purchased,
            self._budget - self.labels_purchased,
            paid,
        ), self._release()
