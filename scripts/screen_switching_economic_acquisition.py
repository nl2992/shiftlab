"""Exact prescreen of one-step query VOI; this is not a novel algorithm or efficacy run."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache
from pathlib import Path


@dataclass(frozen=True)
class State:
    time: int
    budget: int
    observed: int
    positive: int
    pending: tuple[int, ...]
    action: int


class ExactScreen:
    horizon = 20
    initial_budget = 3
    delay = 2
    query_cost = F(1, 100)
    switch_cost = F(1, 10)
    alpha = F(1, 10)

    def __init__(self) -> None:
        self.initial = State(1, 3, 0, 0, (0,), 0)

    def posterior_high(self, state: State) -> F:
        odds = F(3) ** (2 * state.positive - state.observed)
        return odds / (1 + odds)

    def predictive(self, state: State) -> F:
        return F(1, 4) + self.posterior_high(state) / 2

    def choices(self, state: State, *, queries: bool = True):
        assert state.budget >= 0
        assert state.observed + sum(state.pending) + state.budget == self.initial_budget
        actions = [0]
        if state.action == 1 or F(3) ** (2 * state.positive - state.observed) >= 10:
            actions.append(1)
        query_options = (
            (0, 1)
            if queries and state.budget and (state.time + self.delay <= self.horizon)
            else (0,)
        )
        return [(a, q) for a in actions for q in query_options]

    def branches(self, state: State, action: int, query: int, *, null: bool = False):
        queue = (*state.pending, query)
        due, pending = queue[0], queue[1:]
        probability = F(1, 4) if null else self.predictive(state)
        outcomes = [(F(1), 0)] if not due else [(1 - probability, 0), (probability, 1)]
        return [
            (
                weight,
                State(
                    state.time + 1,
                    state.budget - query,
                    state.observed + due,
                    state.positive + positive,
                    pending,
                    action,
                ),
            )
            for weight, positive in outcomes
        ]

    def immediate(self, state: State, action: int, query: int) -> F:
        probability = self.predictive(state)
        return (
            (probability if action == 0 else 1 - probability)
            + self.switch_cost * (action != state.action)
            + self.query_cost * query
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def no_queries(self, state: State) -> F:
        if state.time > self.horizon:
            return F(0)
        return min(
            self.option_value(state, a, q, self.no_queries)
            for a, q in self.choices(state, queries=False)
        )

    def option_value(self, state, action, query, continuation):
        return self.immediate(state, action, query) + sum(
            weight * continuation(next_state)
            for weight, next_state in self.branches(state, action, query)
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def optimal(self, state: State) -> F:
        if state.time > self.horizon:
            return F(0)
        return min(self.option_value(state, a, q, self.optimal) for a, q in self.choices(state))

    def choice(self, state: State, *, candidate: bool):
        continuation = self.no_queries if candidate else self.optimal
        # Equal values prefer no query and retaining the existing action.
        return min(
            self.choices(state),
            key=lambda aq: (
                self.option_value(state, *aq, continuation),
                aq[1],
                aq[0] != state.action,
            ),
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def evaluate_candidate(self, state: State) -> tuple[F, F]:
        if state.time > self.horizon:
            return F(0), F(0)
        action, query = self.choice(state, candidate=True)
        cost = self.immediate(state, action, query)
        count = F(query)
        for weight, next_state in self.branches(state, action, query):
            future_cost, future_count = self.evaluate_candidate(next_state)
            cost += weight * future_cost
            count += weight * future_count
        return cost, count

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def null_promotion_probability(self, state: State) -> F:
        if state.time > self.horizon:
            return F(0)
        action, query = self.choice(state, candidate=False)
        if state.action == 0 and action == 1:
            return F(1)
        return sum(
            weight * self.null_promotion_probability(next_state)
            for weight, next_state in self.branches(state, action, query, null=True)
        )


def run() -> dict[str, object]:
    screen = ExactScreen()
    candidate_cost, candidate_queries = screen.evaluate_candidate(screen.initial)
    optimum = screen.optimal(screen.initial)
    null_promotion = screen.null_promotion_probability(screen.initial)
    forward = [forward_audit(screen, theta) for theta in (F(1, 4), F(3, 4))]
    assert sum(row["cost"] for row in forward) / 2 == optimum
    assert forward[0]["promotion_probability"] == null_promotion
    explicit_policy = F(13483, 1600)
    assert candidate_cost == 10 and candidate_queries == 0
    assert optimum <= explicit_policy < candidate_cost
    assert null_promotion <= screen.alpha
    values = {
        "candidate_cost": candidate_cost,
        "candidate_expected_queries": candidate_queries,
        "bellman_cost": optimum,
        "explicit_three_query_policy_cost": explicit_policy,
        "bellman_null_promotion_probability": null_promotion,
        "candidate_minus_bellman_cost": candidate_cost - optimum,
    }
    return {
        "status": "candidate_rejected",
        "parameters": {
            "T": 20,
            "B": 3,
            "delay": 2,
            "alpha": "1/10",
            "query_cost": "1/100",
            "switch_cost": "1/10",
            "prior_high": "1/2",
            "theta": ["1/4", "3/4"],
        },
        "exact": {key: str(value) for key, value in values.items()},
        "decimal": {key: float(value) for key, value in values.items()},
        "optimal_cache": screen.optimal.cache_info()._asdict(),
        "forward_audit": [{key: str(value) for key, value in row.items()} for row in forward],
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact stationary prescreen, not a new method or efficacy confirmation.",
    }


def forward_audit(screen: ExactScreen, theta: F) -> dict[str, F]:
    """Integrate the computed policy forward under each fixed true law.

    This checks backward posterior-predictive values against a separate law-specific
    occupancy calculation, including query costs, switches and all decision rounds.
    """
    masses = {(screen.initial, False): F(1)}
    cost, queries, switches = F(0), F(0), F(0)
    for time in range(1, screen.horizon + 1):
        following: dict[tuple[State, bool], F] = {}
        assert sum(masses.values()) == 1
        for (state, promoted), mass in masses.items():
            assert state.time == time
            action, query = screen.choice(state, candidate=False)
            cost += mass * (
                (theta if action == 0 else 1 - theta)
                + screen.query_cost * query
                + screen.switch_cost * (action != state.action)
            )
            queries += mass * query
            switches += mass * (action != state.action)
            promoted = promoted or (state.action == 0 and action == 1)
            due = state.pending[0]
            branches = [(F(1), 0)] if not due else [(1 - theta, 0), (theta, 1)]
            for weight, positive in branches:
                following_state = State(
                    time + 1,
                    state.budget - query,
                    state.observed + due,
                    state.positive + positive,
                    (*state.pending[1:], query),
                    action,
                )
                assert following_state.budget >= 0
                assert (
                    following_state.budget + following_state.observed + sum(following_state.pending)
                    == screen.initial_budget
                )
                key = following_state, promoted
                following[key] = following.get(key, F(0)) + mass * weight
        masses = following
    assert sum(masses.values()) == 1
    return {
        "theta": theta,
        "cost": cost,
        "expected_queries": queries,
        "expected_switches": switches,
        "promotion_probability": sum(mass for (_, promoted), mass in masses.items() if promoted),
    }


if __name__ == "__main__":
    result = run()
    path = Path("outputs/switching_economic_acquisition_screen_v1/results.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
