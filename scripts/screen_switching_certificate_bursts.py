"""Exact finite screen of standard burst rollout; no novel-method claim."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from functools import cache
from itertools import product
from pathlib import Path

from screen_switching_economic_acquisition import ExactScreen, State


class BurstScreen(ExactScreen):
    def __init__(self, *, budget: int, delay: int, query_cost: F, switch_cost: F) -> None:
        self.initial_budget = budget
        self.delay = delay
        self.query_cost = query_cost
        self.switch_cost = switch_cost
        self.initial = State(1, budget, 0, 0, (0,) * (delay - 1), 0)

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def burst(self, state: State, remaining: int) -> F:
        if remaining == 0:
            return self.no_queries(state)
        assert state.time + remaining - 1 + self.delay <= self.horizon
        assert remaining <= state.budget
        return min(
            self.immediate(state, a, 1)
            + sum(w * self.burst(s, remaining - 1) for w, s in self.branches(state, a, 1))
            for a, q in self.choices(state)
            if q == 1
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def rollout_choice(self, state: State) -> tuple[int, int, int, F]:
        options = []
        for a, _ in self.choices(state, queries=False):
            value = self.option_value(state, a, 0, self.no_queries)
            options.append((value, 0, a != state.action, 0, a))
        maximum = min(state.budget, self.horizon - self.delay - state.time + 1)
        for n in range(1, maximum + 1):
            for a, q in self.choices(state):
                if q:
                    value = self.immediate(state, a, 1) + sum(
                        w * self.burst(s, n - 1) for w, s in self.branches(state, a, 1)
                    )
                    options.append((value, 1, a != state.action, n, a))
        value, query, _, plan_length, action = min(options)
        return action, query, plan_length, value

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def rollout(self, state: State) -> tuple[F, F]:
        if state.time > self.horizon:
            return F(0), F(0)
        action, query, _, plan_value = self.rollout_choice(state)
        value, count = self.immediate(state, action, query), F(query)
        for weight, successor in self.branches(state, action, query):
            future, future_count = self.rollout(successor)
            value += weight * future
            count += weight * future_count
        assert value <= plan_value <= self.no_queries(state)
        return value, count

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def rollout_null_promotion(self, state: State) -> F:
        if state.time > self.horizon:
            return F(0)
        action, query, _, _ = self.rollout_choice(state)
        if state.action == 0 and action == 1:
            return F(1)
        return sum(
            w * self.rollout_null_promotion(s)
            for w, s in self.branches(state, action, query, null=True)
        )


def run() -> dict[str, object]:
    rows = []
    for budget, delay, c, k in product((3, 5), (1, 3), (F(1, 100), F(1, 5)), (F(1, 10), F(1))):
        screen = BurstScreen(budget=budget, delay=delay, query_cost=c, switch_cost=k)
        base = screen.no_queries(screen.initial)
        optimum = screen.optimal(screen.initial)
        rollout, queries = screen.rollout(screen.initial)
        myopic, _ = screen.evaluate_candidate(screen.initial)
        null_error = screen.rollout_null_promotion(screen.initial)
        audits = [forward_rollout_audit(screen, theta) for theta in (F(1, 4), F(3, 4))]
        assert sum(audit["cost"] for audit in audits) / 2 == rollout
        assert sum(audit["queries"] for audit in audits) / 2 == queries
        assert audits[0]["promotion_probability"] == null_error
        assert optimum <= rollout <= base
        assert null_error <= screen.alpha
        row = {
            "B": budget,
            "delay": delay,
            "query_cost": str(c),
            "switch_cost": str(k),
            "no_query_cost": str(base),
            "bellman_cost": str(optimum),
            "one_step_cost": str(myopic),
            "burst_rollout_cost": str(rollout),
            "rollout_expected_queries": str(queries),
            "rollout_null_promotion": str(null_error),
            "rollout_gap_to_bellman": str(rollout - optimum),
            "strict_gain_over_one_step": rollout < myopic,
            "initial_planned_requests": screen.rollout_choice(screen.initial)[2],
            "bellman_states": screen.optimal.cache_info().currsize,
            "law_specific_forward_audit": [
                {key: str(value) for key, value in audit.items()} for audit in audits
            ],
        }
        rows.append(row)
        # Cached methods include self in their keys. Release each cell after its metrics.
        for method in (
            screen.no_queries,
            screen.optimal,
            screen.evaluate_candidate,
            screen.burst,
            screen.rollout_choice,
            screen.rollout,
            screen.rollout_null_promotion,
        ):
            method.cache_clear()
    assert any(row["strict_gain_over_one_step"] for row in rows)
    sources = [Path(__file__), Path(__file__).with_name("screen_switching_economic_acquisition.py")]
    return {
        "status": "standard_rollout_reference_screened_not_nominated",
        "cells": rows,
        "summary": {
            "cells": len(rows),
            "strict_gains_over_one_step": sum(row["strict_gain_over_one_step"] for row in rows),
            "matches_bellman": sum(F(row["rollout_gap_to_bellman"]) == 0 for row in rows),
            "positive_bellman_gaps": sum(F(row["rollout_gap_to_bellman"]) > 0 for row in rows),
        },
        "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "scope": "Exact stationary development screen; no new algorithm, efficacy or novelty claim.",
    }


def forward_rollout_audit(screen: BurstScreen, theta: F) -> dict[str, F]:
    masses = {(screen.initial, False): F(1)}
    cost, queries = F(0), F(0)
    for time in range(1, screen.horizon + 1):
        assert sum(masses.values()) == 1
        following: dict[tuple[State, bool], F] = {}
        for (state, promoted), mass in masses.items():
            assert state.time == time
            action, query, _, _ = screen.rollout_choice(state)
            cost += mass * (
                (theta if action == 0 else 1 - theta)
                + query * screen.query_cost
                + (action != state.action) * screen.switch_cost
            )
            queries += mass * query
            promoted = promoted or (state.action == 0 and action == 1)
            queue = (*state.pending, query)
            due = queue[0]
            outcomes = [(F(1), 0)] if not due else [(1 - theta, 0), (theta, 1)]
            for weight, positive in outcomes:
                next_state = State(
                    time + 1,
                    state.budget - query,
                    state.observed + due,
                    state.positive + positive,
                    queue[1:],
                    action,
                )
                assert next_state.budget >= 0
                assert (
                    next_state.budget + next_state.observed + sum(next_state.pending)
                    == screen.initial_budget
                )
                key = next_state, promoted
                following[key] = following.get(key, F(0)) + mass * weight
        masses = following
    assert sum(masses.values()) == 1
    return {
        "theta": theta,
        "cost": cost,
        "queries": queries,
        "promotion_probability": sum(mass for (_, promoted), mass in masses.items() if promoted),
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_certificate_burst_screen_v1/results.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
