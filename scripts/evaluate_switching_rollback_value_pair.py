"""Measure rollback value under a fixed delayed acquisition contract."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import pairwise, product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

TESTS = tuple(product((0, 1), repeat=2))
NULL_ENDPOINTS = tuple(product((F(0), F(1, 2)), repeat=3))


def tape_probability_and_posterior(model, observations):
    posterior = model.prior1
    last_event = 0
    probability = F(1)
    for event, outcome in observations:
        state = model.propagate(posterior, event - last_event)
        positive = model.emission(state)
        mass = positive if outcome else 1 - positive
        probability *= mass
        likelihood1 = model.emission1 if outcome else 1 - model.emission1
        posterior = state * likelihood1 / mass
        last_event = event
    return probability, posterior, last_event


def pair_values(model, rollback_enabled):
    probabilities = []
    net_gains = []
    for y1, y2 in TESTS:
        pair_probability, posterior, last = tape_probability_and_posterior(
            model, ((1, y1), (2, y2))
        )
        expected_net_gain = F(0)
        for y4 in (0, 1):
            state4 = model.propagate(posterior, 4 - last)
            p4 = model.emission(state4)
            outcome_probability = p4 if y4 else 1 - p4
            state4_posterior = (
                state4 * (model.emission1 if y4 else 1 - model.emission1) / outcome_probability
            )
            p5 = model.emission(model.propagate(state4_posterior, 1))
            p6 = model.emission(model.propagate(state4_posterior, 2))
            gain5, gain6 = 2 * p5 - 1, 2 * p6 - 1
            if rollback_enabled and gain6 < -F(1, 10):
                net = gain5 - F(2, 10)  # promotion and round-6 rollback
            else:
                net = gain5 + gain6 - F(1, 10)  # promotion; hold through round 6
            expected_net_gain += outcome_probability * net
        probabilities.append(pair_probability)
        net_gains.append(expected_net_gain)
    return probabilities, net_gains


def risk_matrix():
    rows = []
    for p1, p20, p21 in NULL_ENDPOINTS:
        row = []
        for y1, y2 in TESTS:
            first = p1 if y1 else 1 - p1
            p2 = p21 if y1 else p20
            second = p2 if y2 else 1 - p2
            row.append(first * second)
        rows.append(row)
    return rows


def optimize_test(model, rollback_enabled, risks, alpha):
    probabilities, gains = pair_values(model, rollback_enabled)
    coefficients = [p * g for p, g in zip(probabilities, gains, strict=True)]
    result = linprog(
        -np.array([float(value) for value in coefficients]),
        A_ub=np.array([[float(value) for value in row] for row in risks]),
        b_ub=np.full(len(risks), float(alpha)),
        bounds=[(0.0, 1.0)] * len(TESTS),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    raw = [F(float(value)).limit_denominator(10**9) for value in result.x]
    raw_risk = max(sum((r * f for r, f in zip(row, raw, strict=True)), F(0)) for row in risks)
    activation = min(F(1), alpha / raw_risk) if raw_risk else F(1)
    safe = [activation * value for value in raw]
    safe_risk = max(sum((r * f for r, f in zip(row, safe, strict=True)), F(0)) for row in risks)
    assert safe_risk <= alpha
    return {
        "test": safe,
        "test_strings": [str(value) for value in safe],
        "raw_worst_risk": str(raw_risk),
        "activation": str(activation),
        "worst_safe_risk": str(safe_risk),
        "solver_objective": -float(result.fun),
        "alt_pair_probabilities": probabilities,
        "net_gain_by_pair": gains,
    }


def evaluate_cost(model, test, rollback_enabled, pair_riskfree_probabilities, pair_gains, config):
    expected_gain = sum(
        (
            p * gain * f
            for p, gain, f in zip(pair_riskfree_probabilities, pair_gains, test, strict=True)
        ),
        F(0),
    )
    base_cost = (
        sum(
            (
                model.emission(model.propagate(model.prior1, t))
                for t in range(1, config.horizon + 1)
            ),
            F(0),
        )
        + config.query_cost * 3
    )
    return {
        "base_continue_plus_queries": str(base_cost),
        "expected_net_gain": str(expected_gain),
        "total_cost": str(base_cost - expected_gain),
    }


def explicit_world_cost(model, test, rollback_enabled, config):
    total = F(0)
    for states in product((0, 1), repeat=config.horizon + 1):
        state_mass = model.prior1 if states[0] else 1 - model.prior1
        for previous, current in pairwise(states):
            if previous == 0:
                transition = model.transition01 if current else 1 - model.transition01
            else:
                transition = 1 - model.transition10 if current else model.transition10
            state_mass *= transition
        for outcomes in product((0, 1), repeat=config.horizon):
            mass = state_mass
            for state, outcome in zip(states[1:], outcomes, strict=True):
                emission = model.emission1 if state else model.emission0
                mass *= emission if outcome else 1 - emission
            if not mass:
                continue
            promotion = test[2 * outcomes[0] + outcomes[1]]
            rollback = False
            if rollback_enabled:
                _, posterior, last = tape_probability_and_posterior(
                    model, ((1, outcomes[0]), (2, outcomes[1]), (4, outcomes[3]))
                )
                gain6 = 2 * model.emission(model.propagate(posterior, 6 - last)) - 1
                rollback = gain6 < -config.switch_cost
            cost = config.query_cost * 3 + sum(map(F, outcomes[:4]))
            cost += promotion * (
                1
                - outcomes[4]
                + (outcomes[5] if rollback else 1 - outcomes[5])
                + config.switch_cost
                + (config.switch_cost if rollback else F(0))
            )
            cost += (1 - promotion) * (outcomes[4] + outcomes[5])
            total += mass * cost
    return total


def run_model(config, model, name):
    risks = risk_matrix()
    no_rollback = optimize_test(model, False, risks, config.alpha)
    rollback = optimize_test(model, True, risks, config.alpha)
    _, gains_with_rollback = pair_values(model, True)
    no_rollback_same_test = evaluate_cost(
        model,
        no_rollback["test"],
        True,
        no_rollback["alt_pair_probabilities"],
        gains_with_rollback,
        config,
    )
    no_rollback_cost = evaluate_cost(
        model,
        no_rollback["test"],
        False,
        no_rollback["alt_pair_probabilities"],
        no_rollback["net_gain_by_pair"],
        config,
    )
    rollback_cost = evaluate_cost(
        model,
        rollback["test"],
        True,
        rollback["alt_pair_probabilities"],
        rollback["net_gain_by_pair"],
        config,
    )
    explicit_no_rollback_cost = explicit_world_cost(model, no_rollback["test"], False, config)
    explicit_rollback_cost = explicit_world_cost(model, rollback["test"], True, config)
    assert explicit_no_rollback_cost == F(no_rollback_cost["total_cost"])
    assert explicit_rollback_cost == F(rollback_cost["total_cost"])
    return {
        "name": name,
        "model": {
            "transition01": str(model.transition01),
            "transition10": str(model.transition10),
            "emission0": str(model.emission0),
            "emission1": str(model.emission1),
            "prior1": str(model.prior1),
        },
        "pairs": [list(pair) for pair in TESTS],
        "no_rollback_optimized_test": {
            "test_probabilities": no_rollback["test_strings"],
            "risk": no_rollback["worst_safe_risk"],
            "activation": no_rollback["activation"],
            "solver_objective": no_rollback["solver_objective"],
            "cost": no_rollback_cost,
        },
        "rollback_enabled_same_promotion_test": {
            "test_probabilities": no_rollback["test_strings"],
            "risk": no_rollback["worst_safe_risk"],
            "cost": no_rollback_same_test,
        },
        "rollback_enabled_optimized_test": {
            "test_probabilities": rollback["test_strings"],
            "risk": rollback["worst_safe_risk"],
            "activation": rollback["activation"],
            "solver_objective": rollback["solver_objective"],
            "cost": rollback_cost,
        },
        "rollback_value_fixed_test": str(
            F(no_rollback_cost["total_cost"]) - F(no_rollback_same_test["total_cost"])
        ),
        "additional_test_redesign_value": str(
            F(no_rollback_same_test["total_cost"]) - F(rollback_cost["total_cost"])
        ),
        "total_rollback_capability_value": str(
            F(no_rollback_cost["total_cost"]) - F(rollback_cost["total_cost"])
        ),
        "risk_kernels_checked": len(risks),
        "explicit_hidden_world_checks": 2 ** (config.horizon + 1 + config.horizon),
        "explicit_no_rollback_cost": str(explicit_no_rollback_cost),
        "explicit_rollback_cost": str(explicit_rollback_cost),
    }


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    recurrent = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    one_way = RegimeModel(
        transition01=F(1, 10),
        transition10=F(0),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    result = {
        "status": "completed_registered_rollback_value_pair",
        "protocol": "docs/switching_rollback_value_pair_protocol_v1.md",
        "fixed_contract": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "query_events": [1, 2, 4],
            "promotion_decision_round": 5,
            "rollback_decision_round": 6,
        },
        "models": [
            run_model(config, recurrent, "recurrent"),
            run_model(config, one_way, "one_way_no_regime_reversal"),
        ],
        "sha256": {
            source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
            for source in (
                "scripts/evaluate_switching_rollback_value_pair.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_rollback_value_pair_protocol_v1.md",
            )
        },
        "scope": "Fixed-cohort optimal test with one possible rollback; development comparison, not a new method or recurrent regret result.",
    }
    target = Path("outputs/switching_rollback_value_pair_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
