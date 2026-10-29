"""Exact causal-null risk evaluation for deterministic public-memory controllers."""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache

Memory = Hashable
Decision = tuple[int, int, Memory]
ReleaseUpdate = Callable[[Memory, int, int], Memory]
DecisionRule = Callable[[int, Memory, int], Decision]


@dataclass(frozen=True)
class DeterministicFSC:
    """A controller whose internal state is a deterministic function of public data."""

    initial_memory: Memory
    on_release: ReleaseUpdate
    decide: DecisionRule


@dataclass(frozen=True)
class FSCRiskResult:
    risk: F
    visited_states: int


def worst_case_promotion_risk(
    controller: DeterministicFSC,
    *,
    horizon: int,
    budget: int,
    delay: int,
) -> FSCRiskResult:
    """Compute exact worst-null probability of any promotion.

    The null chooses each queried label's conditional success probability in [0, 1/2]
    after observing the full generated-label history. Since the continuation value is
    affine in the current success probability, a maximizing choice is always 0 or 1/2.
    Pending labels stay in the evaluator state until their fixed release event; the
    controller is updated only when each label is released.
    """
    if type(horizon) is not int or type(budget) is not int or type(delay) is not int:
        raise TypeError("horizon, budget and delay must be integers")
    if horizon < 1 or not 0 <= budget <= horizon or delay < 1:
        raise ValueError("invalid horizon, hard budget or delay")

    # Entries are (release_event, request_event, outcome). The null sees all entries;
    # the controller sees an outcome only through on_release when its release is due.
    Pending = tuple[tuple[int, int, int], ...]

    @cache
    def visit(time: int, memory: Memory, remaining: int, pending: Pending) -> F:
        if time > horizon:
            return F(0)

        due = tuple(item for item in pending if item[0] == time)
        future_pending = tuple(item for item in pending if item[0] != time)
        updated_memory = memory
        for _release, request, outcome in due:
            updated_memory = controller.on_release(updated_memory, request, outcome)

        action, query, next_memory = controller.decide(time, updated_memory, remaining)
        if action not in (0, 1) or query not in (0, 1):
            raise ValueError("controller actions and query decisions must be binary")
        if query and remaining == 0:
            raise ValueError("controller violates the pathwise hard query budget")
        if action == 1:
            return F(1)

        if not query:
            return visit(time + 1, next_memory, remaining, future_pending)

        next_pending_0 = tuple(sorted((*future_pending, (time + delay, time, 0))))
        next_pending_1 = tuple(sorted((*future_pending, (time + delay, time, 1))))
        value_if_zero = visit(time + 1, next_memory, remaining - 1, next_pending_0)
        value_if_half = (
            value_if_zero + visit(time + 1, next_memory, remaining - 1, next_pending_1)
        ) / 2
        return max(value_if_zero, value_if_half)

    risk = visit(1, controller.initial_memory, budget, ())
    return FSCRiskResult(risk=risk, visited_states=visit.cache_info().currsize)
