"""Exact full-causal-null risk verification for deterministic finite controllers.

This is a policy-specific verifier, not a controller synthesis algorithm. The
null response can depend on the complete generated history; finite-horizon
dynamic programming is exact because the fixed controller, pending labels,
budget, time, and previous deployment form a Markov state for its best response.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache
from typing import Protocol


class DeterministicController(Protocol):
    """A deterministic learner controller with public finite memory."""

    @property
    def initial_state(self) -> Hashable: ...

    def step(
        self,
        memory: Hashable,
        time: int,
        released: tuple[int, ...],
        previous_action: int,
        remaining_queries: int,
    ) -> tuple[int, int, Hashable]:
        """Return deployment, query, and next memory for this event."""


PendingLabel = tuple[int, int, int]  # release time, request time, outcome


@dataclass(frozen=True)
class RiskVerification:
    risk: F
    visited_states: int


def verify_causal_null_risk(
    controller: DeterministicController,
    *,
    horizon: int,
    budget: int,
    delay: int,
) -> RiskVerification:
    """Return exact worst-case probability of ever deploying action 1.

    The null observes every generated queried label immediately, including
    labels still pending to the learner. On each query its conditional positive
    probability may be any value in ``[0, 1/2]``. The objective is linear in
    that probability, so endpoint choices 0 and 1/2 suffice.
    """
    if any(type(value) is not int for value in (horizon, budget, delay)):
        raise ValueError("horizon, budget and delay must be integers")
    if horizon < 1 or not 0 <= budget <= horizon or delay < 1:
        raise ValueError("require horizon >= 1, delay >= 1 and 0 <= budget <= horizon")

    visited: set[tuple] = set()

    @cache
    def value(
        time: int,
        memory: Hashable,
        previous_action: int,
        remaining: int,
        pending: tuple[PendingLabel, ...],
    ) -> F:
        if time > horizon:
            return F(0)
        visited.add((time, memory, previous_action, remaining, pending))

        released_items = tuple(
            sorted((item for item in pending if item[0] == time), key=lambda x: x[1])
        )
        released = tuple(item[2] for item in released_items)
        still_pending = tuple(item for item in pending if item[0] != time)
        action, query, next_memory = controller.step(
            memory, time, released, previous_action, remaining
        )
        if action not in (0, 1) or query not in (0, 1):
            raise ValueError("controller actions and query indicators must be binary")
        if query and remaining == 0:
            raise ValueError("controller violates the pathwise query budget")
        if action == 1:
            return F(1)

        if not query:
            return value(
                time + 1,
                next_memory,
                action,
                remaining,
                still_pending,
            )

        next_pending_0 = tuple(sorted(still_pending + ((time + delay, time, 0),)))
        next_pending_1 = tuple(sorted(still_pending + ((time + delay, time, 1),)))
        risk_0 = value(time + 1, next_memory, action, remaining - 1, next_pending_0)
        risk_half = (
            risk_0 + value(time + 1, next_memory, action, remaining - 1, next_pending_1)
        ) / 2
        return max(risk_0, risk_half)

    risk = value(1, controller.initial_state, 0, budget, ())
    return RiskVerification(risk=risk, visited_states=len(visited))
