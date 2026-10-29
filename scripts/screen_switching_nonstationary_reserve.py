"""Exact recurrent-regime acquisition/reversal screen; no novel method claim."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from fractions import Fraction as F
from functools import cache
from pathlib import Path

from shiftlab.dive.delayed_regime_information import RegimeModel


@dataclass(frozen=True)
class State:
    time: int
    budget: int
    observed: int
    last_event: int
    posterior: F
    pending: tuple[int, ...]
    wealth: F
    action: int
    promotion: int = 0


class ReserveScreen:
    horizon = 12
    cap = 5
    query_cost = F(1, 100)
    switch_cost = F(1, 10)

    def __init__(self, delay: int) -> None:
        self.delay = delay
        self.model = RegimeModel(F(1, 20), F(1, 20), F(1, 20), F(19, 20), F(1))
        self.initial = State(1, self.cap, 0, 0, F(1), (), F(1), 0)

    def probability(self, state: State, event: int) -> F:
        return self.model.emission(self.model.propagate(state.posterior, event - state.last_event))

    def actions(self, state: State):
        assert state.budget >= 0
        assert state.budget + state.observed + len(state.pending) == self.cap
        return (0, 1) if state.action or state.wealth >= 10 else (0,)

    def query_options(self, state: State):
        return (0, 1) if state.budget and state.time + self.delay <= self.horizon else (0,)

    def next_states(self, state: State, action: int, query: int, *, null: bool = False):
        pending = (*state.pending, state.time) if query else state.pending
        next_state = replace(
            state,
            time=state.time + 1,
            budget=state.budget - query,
            pending=pending,
            action=action,
            promotion=state.promotion or (state.time if action else 0),
        )
        if not pending or pending[0] + self.delay != next_state.time:
            return [(F(1), next_state)]
        source = pending[0]
        p1 = self.model.propagate(state.posterior, source - state.last_event)
        p = self.model.emission(p1)
        outcome_probability = F(1, 2) if null else p
        bet = max(F(1, 2), p)
        rows = []
        for outcome, weight in ((0, 1 - outcome_probability), (1, outcome_probability)):
            posterior = p1 * (
                self.model.emission1 / p if outcome else (1 - self.model.emission1) / (1 - p)
            )
            factor = 2 * (bet if outcome else 1 - bet)
            rows.append(
                (
                    weight,
                    replace(
                        next_state,
                        observed=state.observed + 1,
                        last_event=source,
                        posterior=posterior,
                        wealth=state.wealth * factor,
                        pending=pending[1:],
                    ),
                )
            )
        return rows

    def costs(self, state: State, action: int, query: int):
        p = self.probability(state, state.time)
        return (
            (p if action == 0 else 1 - p),
            query * self.query_cost,
            (action != state.action) * self.switch_cost,
        )

    def option(self, state: State, action: int, query: int) -> F:
        return sum(self.costs(state, action, query)) + sum(
            w * self.optimal(s) for w, s in self.next_states(state, action, query)
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def optimal(self, state: State) -> F:
        if state.time > self.horizon:
            return F(0)
        if self.optimal.cache_info().misses > 100_000:
            raise RuntimeError("incomplete screen: planner state cap exceeded")
        return min(
            self.option(state, a, q) for a in self.actions(state) for q in self.query_options(state)
        )

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def decision(self, state: State, method: str):
        if method == "bellman":
            return min(
                ((a, q) for a in self.actions(state) for q in self.query_options(state)),
                key=lambda aq: (self.option(state, *aq), aq[1], aq[0] != state.action),
            )
        if method == "continue":
            return 0, 0
        commit_costs = {
            a: sum(
                self.probability(state, s) if a == 0 else 1 - self.probability(state, s)
                for s in range(state.time, self.horizon + 1)
            )
            + self.switch_cost * (a != state.action)
            for a in self.actions(state)
        }
        action = min(commit_costs, key=lambda a: (commit_costs[a], a != state.action))
        permitted = len(self.query_options(state)) == 2
        if method == "frontload":
            return action, int(permitted)
        wait = {"reserve_2": 2, "reserve_4": 4}[method]
        first_promotion = state.promotion or (state.time if action else 0)
        reserve_released = first_promotion and state.time >= first_promotion + wait
        return action, int(permitted and (self.cap - state.budget < 4 or reserve_released))

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def evaluate(self, state: State, method: str) -> tuple[F, ...]:
        if state.time > self.horizon:
            return (F(0),) * 6
        action, query = self.decision(state, method)
        loss, label_cost, switch_cost = self.costs(state, action, query)
        metrics = [
            loss,
            label_cost,
            switch_cost,
            F(query),
            F(action != state.action),
            F(state.action == 1 and action == 0),
        ]
        for weight, successor in self.next_states(state, action, query):
            for i, value in enumerate(self.evaluate(successor, method)):
                metrics[i] += weight * value
        return tuple(metrics)

    @cache  # noqa: B019 - Finite screen intentionally memoizes instance states.
    def null_promotion(self, state: State, method: str) -> F:
        if state.time > self.horizon:
            return F(0)
        action, query = self.decision(state, method)
        if state.action == 0 and action:
            return F(1)
        return sum(
            w * self.null_promotion(s, method)
            for w, s in self.next_states(state, action, query, null=True)
        )


def run():
    cells = []
    for delay in (1, 2):
        screen = ReserveScreen(delay)
        optimum = screen.optimal(screen.initial)
        rows = []
        for method in ("continue", "frontload", "reserve_2", "reserve_4", "bellman"):
            values = screen.evaluate(screen.initial, method)
            independent = forward_latent_check(screen, method)
            assert values == independent
            cost = sum(values[:3])
            error = screen.null_promotion(screen.initial, method)
            assert error <= F(1, 10)
            assert cost >= optimum
            if method == "bellman":
                assert cost == optimum
            names = (
                "decision_loss",
                "query_cost",
                "switch_cost",
                "queries",
                "switches",
                "rollbacks",
            )
            rows.append(
                {
                    "method": method,
                    "exact_cost": str(cost),
                    "cost": float(cost),
                    "excess_vs_bellman": str(cost - optimum),
                    "null_promotion": str(error),
                    **{name: str(value) for name, value in zip(names, values, strict=True)},
                    "latent_forward_verified": True,
                }
            )
        cells.append(
            {
                "delay": delay,
                "policies": rows,
                "planner_states": screen.optimal.cache_info().currsize,
            }
        )
        for method in (screen.optimal, screen.decision, screen.evaluate, screen.null_promotion):
            method.cache_clear()
    sources = [Path(__file__), Path("src/shiftlab/dive/delayed_regime_information.py")]
    return {
        "status": "development_screen_complete_no_novel_method_claim",
        "cells": cells,
        "parameters": {
            "T": 12,
            "B": 5,
            "alpha": "1/10",
            "query_cost": "1/100",
            "switch_cost": "1/10",
            "transition": "1/20",
            "emissions": ["1/20", "19/20"],
            "initial_state1_prior": "1",
        },
        "source_hashes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "scope": "Known recurrent model, exact expected costs; not a dynamic regret theorem or real-data result.",
    }


def forward_latent_check(screen: ReserveScreen, method: str) -> tuple[F, ...]:
    """Evaluate actions with actual latent transitions, not predictive branch weights.

    Hidden states/pending outcome values stay solely in this evaluator. The policy
    receives the same visible State used in backward planning.
    """
    masses = {(screen.initial, 1, ()): F(1)}
    totals = [F(0)] * 6
    for time in range(1, screen.horizon + 1):
        assert sum(masses.values()) == 1
        following = {}
        for (state, previous_hidden, pending_outcomes), mass in masses.items():
            action, query = screen.decision(state, method)
            hidden_probability = (
                1 - screen.model.transition10 if previous_hidden else screen.model.transition01
            )
            successors = screen.next_states(state, action, query)
            for hidden, hidden_weight in ((0, 1 - hidden_probability), (1, hidden_probability)):
                theta = screen.model.emission1 if hidden else screen.model.emission0
                branch_mass = mass * hidden_weight
                contributions = (
                    theta if action == 0 else 1 - theta,
                    screen.query_cost * query,
                    screen.switch_cost * (action != state.action),
                    F(query),
                    F(action != state.action),
                    F(state.action == 1 and action == 0),
                )
                for i, value in enumerate(contributions):
                    totals[i] += branch_mass * value
                outcomes = ((0, 1 - theta), (1, theta)) if query else ((0, F(1)),)
                for outcome, outcome_weight in outcomes:
                    pending = (*pending_outcomes, (time, outcome)) if query else pending_outcomes
                    if pending and pending[0][0] + screen.delay == time + 1:
                        # The posterior update is shared, but the probability of this
                        # outcome comes from the explicit latent process above.
                        successor = successors[pending[0][1]][1]
                        pending = pending[1:]
                    else:
                        assert len(successors) == 1
                        successor = successors[0][1]
                    assert successor.pending == tuple(event for event, _ in pending)
                    key = successor, hidden, pending
                    following[key] = following.get(key, F(0)) + branch_mass * outcome_weight
        masses = following
    assert sum(masses.values()) == 1
    return tuple(totals)


if __name__ == "__main__":
    target = Path("outputs/switching_nonstationary_reserve_screen_v1/results.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run()
    except RuntimeError as error:
        result = {"status": "incomplete", "reason": str(error)}
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
