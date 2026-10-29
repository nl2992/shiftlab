"""Additive v2 contract types: delayed, pending and missing feedback, and a switching layer.

Standard library and numpy only, like ``interface``; ``interface.py`` itself is unchanged, so the
v1 harness, the baselines and the sandbox packet are unaffected. v2 events are the unchanged
``PublicEvent``; the v2 harness adds a start-of-round ``receive`` call and richer ``observe``
outcomes. Oracle quantities (release rounds, losses, regime labels) never cross this interface.

Round order (``docs/switching_problem_v1.md``): (1) labels whose release round is ``t`` are
delivered through ``receive``; (2) the public event ``t`` is built; (3) a ``Switcher`` chooses the
deployed policy ``A_t`` from public information; (4) ``propensity`` is called, then the harness
coin; (5) a bought query's price is charged and reserved immediately; (6) ``observe`` is called
once. ``Feedback.t`` is always the original event index, so a late label is attributable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .interface import Feedback, PublicEvent, TaskSpec

__all__ = [
    "Delivery",
    "MissingFeedback",
    "MonitorV2",
    "PendingQuery",
    "QueryOutcome",
    "SwitchContext",
    "Switcher",
]


@dataclass(frozen=True)
class MissingFeedback:
    """A bought query whose label is missing at its release time: charged, and no ``Z``.

    ``t`` is the original event index; ``propensity`` the ``q`` used at that event.
    """

    t: int
    propensity: float


@dataclass(frozen=True)
class PendingQuery:
    """Receipt for a bought query whose label is released at a later round.

    Tells the monitor the query was bought and charged (so it is not an unqueried event). It
    carries no release time: the delay is not public unless the task declares it.
    """

    t: int
    propensity: float


Delivery = Feedback | MissingFeedback
# ``observe`` outcome: None = not bought (or refused); Feedback/MissingFeedback = delivered in
# this round; PendingQuery = bought, label arrives later through ``receive``.
QueryOutcome = Delivery | PendingQuery | None


@dataclass(frozen=True)
class SwitchContext:
    """Public state offered to a ``Switcher`` when it chooses ``A_t`` (0 = incumbent, 1 = candidate).

    ``remaining_budget`` already excludes pending queries (charged at request time);
    ``pending_queries``/``pending_spend`` report them for planning. ``query_cost`` and
    ``switch_cost`` are the declared per-query and per-switch charges, in loss units.
    """

    t: int
    current_policy: int
    n_switches: int
    remaining_budget: float
    pending_queries: int
    pending_spend: float
    query_cost: float
    switch_cost: float


class MonitorV2(Protocol):
    """Monitor with delayed/pending/missing feedback. ``log_e_value`` is read after ``observe``."""

    def reset(self, spec: TaskSpec) -> None: ...

    def receive(self, t: int, released: Sequence[Delivery]) -> None:
        """Start of round ``t``: labels released now, ordered by (release round, event index)."""

    def propensity(self, event: PublicEvent) -> float: ...

    def observe(self, event: PublicEvent, outcome: QueryOutcome) -> None: ...

    @property
    def log_e_value(self) -> float: ...


class Switcher(MonitorV2, Protocol):
    """A ``MonitorV2`` that also chooses the deployed policy each round from public information."""

    def choose(self, event: PublicEvent, context: SwitchContext) -> int: ...
