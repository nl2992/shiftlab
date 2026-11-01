"""Tests for the RPOQ S3 exact solver (toy instance, no claims)."""

from __future__ import annotations

import itertools
import math

import numpy as np

from shiftlab.dive.rpoq_exact import (
    Evaluator,
    Instance,
    constant_table,
    monotone_in_wealth,
    neyman_table,
)

SMALL = {"horizon": 5, "delay": 2, "budget": 2, "grid": (0.5, 1.0)}


def _simulate(inst: Instance, p_z, act, n: int, seed: int) -> float:
    """Independent event-level simulator of the same protocol (prefix + delay + cap)."""
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n):
        events: list[dict] = []
        pointer = 0
        wealth = 1.0
        budget = inst.budget
        alarm = False
        last = inst.horizon + inst.delay
        for t in range(last + 1):
            while pointer < len(events):
                e = events[pointer]
                if e["q"] is not None and e["arrival"] > t:
                    break
                wealth = round(wealth * e["factor"], 10)
                pointer += 1
                if wealth >= inst.threshold - 1e-12:
                    alarm = True
                    break
            if alarm:
                break
            if t >= inst.horizon:
                continue
            ctx = int(rng.random() >= inst.p_context[0])
            buf = tuple(
                ("p", e["arrival"], e["ctx"], e["q"])
                if e["q"] is not None and e["arrival"] > t
                else ("d", e["factor"])
                for e in events[pointer:]
            )
            if budget == 0:
                continue
            q = act(t, ctx, wealth, buf, budget)
            z = 1 if rng.random() < p_z[ctx] else -1
            if rng.random() < q:
                budget -= 1
                events.append(
                    {
                        "ctx": ctx,
                        "q": q,
                        "arrival": t + inst.delay,
                        "factor": inst.factor(ctx, q, z),
                    }
                )
            else:
                events.append(
                    {"ctx": ctx, "q": None, "arrival": t, "factor": inst.unqueried_factor(ctx, q)}
                )
        hits += alarm
    return hits / n


def test_optimal_dominates_every_constant_table():
    inst = Instance(**SMALL)
    v_opt = Evaluator(inst, inst.p_alt, inst.budget).value()
    for qa, qb in itertools.product(inst.grid, repeat=2):
        pol = constant_table({0: qa, 1: qb})
        assert Evaluator(inst, inst.p_alt, inst.budget, policy=pol).value() <= v_opt + 1e-9


def test_null_alarm_probability_is_at_most_alpha():
    inst = Instance(**SMALL)
    alt = Evaluator(inst, inst.p_alt, inst.budget)
    alt.value()
    policies = [alt.act, constant_table(neyman_table(inst))]
    policies += [
        constant_table({0: qa, 1: qb}) for qa, qb in itertools.product(inst.grid, repeat=2)
    ]
    for pol in policies:
        v_null = Evaluator(inst, inst.p_null, inst.budget, policy=pol).value()
        assert v_null <= inst.alpha + 1e-9


def test_exact_value_matches_independent_simulation():
    inst = Instance(**SMALL)
    alt = Evaluator(inst, inst.p_alt, inst.budget)
    exact = alt.value()
    n = 20000
    sim = _simulate(inst, inst.p_alt, alt.act, n, seed=7)
    sigma = math.sqrt(max(exact * (1 - exact), 1e-6) / n)
    assert abs(sim - exact) < 5 * sigma


def test_exact_null_value_matches_simulation_for_constant_policy():
    inst = Instance(**SMALL)
    pol = constant_table({0: 1.0, 1: 1.0})
    exact = Evaluator(inst, inst.p_null, inst.budget, policy=pol).value()
    n = 20000
    sim = _simulate(inst, inst.p_null, pol, n, seed=11)
    sigma = math.sqrt(max(exact * (1 - exact), 1e-6) / n)
    assert abs(sim - exact) < 5 * sigma


def test_more_budget_never_hurts():
    values = [
        Evaluator(Instance(**{**SMALL, "budget": b}), Instance().p_alt, b).value()
        for b in (0, 1, 2)
    ]
    assert values[0] == 0.0
    assert values[0] <= values[1] + 1e-12 <= values[2] + 2e-12


def test_monotone_selection_helper():
    assert monotone_in_wealth([(1.0, (0.5,)), (2.0, (0.5, 1.0)), (3.0, (1.0,))])
    assert monotone_in_wealth([(1.0, (1.0,)), (2.0, (0.5,)), (3.0, (0.5,))])
    assert not monotone_in_wealth([(1.0, (0.5,)), (2.0, (1.0,)), (3.0, (0.5,))])
