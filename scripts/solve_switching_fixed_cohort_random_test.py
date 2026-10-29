"""Optimize an arbitrary robust-safe test on a fixed delayed cohort."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def alternative_tape_probability_and_gain(model: RegimeModel, tape: tuple[int, ...]):
    posterior = model.prior1
    last_event = 0
    probability = F(1)
    for event, outcome in enumerate(tape, start=1):
        state_probability = model.propagate(posterior, event - last_event)
        positive = model.emission(state_probability)
        mass = positive if outcome else 1 - positive
        probability *= mass
        likelihood1 = model.emission1 if outcome else 1 - model.emission1
        posterior = state_probability * likelihood1 / mass
        last_event = event
    future_gain = F(0)
    for event in (5, 6):
        state_probability = model.propagate(posterior, event - last_event)
        future_gain += 2 * model.emission(state_probability) - 1
    return probability, future_gain - F(1, 10)


def null_tape_probability(tape: tuple[int, ...], endpoint_policy: tuple[F, ...]) -> F:
    p1 = endpoint_policy[0]
    p2 = endpoint_policy[1 + tape[0]]
    p3 = endpoint_policy[3 + 2 * tape[0] + tape[1]]
    probability = F(1)
    for outcome, success in zip(tape, (p1, p2, p3), strict=True):
        probability *= success if outcome else 1 - success
    return probability


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    tapes = tuple(product((0, 1), repeat=3))
    alt = [alternative_tape_probability_and_gain(model, tape) for tape in tapes]
    alt_probability = [row[0] for row in alt]
    gain = [row[1] for row in alt]
    endpoint_policies = tuple(product((F(0), F(1, 2)), repeat=7))
    risk_matrix = [
        [
            sum(
                (
                    null_tape_probability(tape, endpoint)
                    for tape_index, tape in enumerate(tapes)
                    if tape_index == j
                ),
                F(0),
            )
            for j in range(len(tapes))
        ]
        for endpoint in endpoint_policies
    ]
    objective_gain = [alt_probability[j] * gain[j] for j in range(len(tapes))]
    result = linprog(
        -np.array([float(value) for value in objective_gain]),
        A_ub=np.array([[float(value) for value in row] for row in risk_matrix]),
        b_ub=np.full(len(risk_matrix), float(config.alpha)),
        bounds=[(0.0, 1.0)] * len(tapes),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    raw_test = [F(float(value)).limit_denominator(10**9) for value in result.x]
    raw_risks = [
        sum((mass * weight for mass, weight in zip(row, raw_test, strict=True)), F(0))
        for row in risk_matrix
    ]
    worst_raw_risk = max(raw_risks, default=F(0))
    activation = min(F(1), config.alpha / worst_raw_risk) if worst_raw_risk else F(1)
    test = [activation * value for value in raw_test]
    safe_risks = [
        sum((mass * weight for mass, weight in zip(row, test, strict=True)), F(0))
        for row in risk_matrix
    ]
    worst_safe_risk = max(safe_risks, default=F(0))
    assert worst_safe_risk <= config.alpha
    expected_gain = sum(
        (p * g * f for p, g, f in zip(alt_probability, gain, test, strict=True)), F(0)
    )
    expected_promotions = sum((p * f for p, f in zip(alt_probability, test, strict=True)), F(0))
    baseline_decision_cost = sum(
        (
            model.emission(model.propagate(model.prior1, event))
            for event in range(1, config.horizon + 1)
        ),
        F(0),
    )
    baseline_total_cost = baseline_decision_cost + config.query_cost * 3
    cohort_cost = baseline_total_cost - expected_gain

    previous = json.loads(
        Path("outputs/switching_episode_composition_grid_v1/results.json").read_text(
            encoding="utf-8"
        )
    )
    cell = next(
        row
        for row in previous["cells"]
        if row["model"]["transition"] == "1/10"
        and row["model"]["emission0"] == "1/50"
        and row["model"]["emission1"] == "49/50"
    )
    episode_cost = F(cell["best_composition"]["total_cost"])
    oracle_policy_cost = F(cell["oracle_policy_cost"])
    report = {
        "status": "completed_fixed_cohort_robust_test_optimization",
        "configuration": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "calendar": [1, 2, 3],
            "decision_round": 5,
            "model": {
                "transition01": str(model.transition01),
                "transition10": str(model.transition10),
                "emission0": str(model.emission0),
                "emission1": str(model.emission1),
                "prior1": str(model.prior1),
            },
        },
        "test_lp": {
            "objective_value_unscaled_float": -float(result.fun),
            "test_probabilities_by_tape": [
                {
                    "tape": list(tape),
                    "probability": str(value),
                    "gain": str(gain[j]),
                    "alt_probability": str(alt_probability[j]),
                }
                for j, (tape, value) in enumerate(zip(tapes, test, strict=True))
            ],
            "endpoint_null_policies": len(endpoint_policies),
            "worst_raw_recovered_risk": str(worst_raw_risk),
            "safety_activation": str(activation),
            "worst_safe_risk": str(worst_safe_risk),
            "risk_constraints_checked_exactly": len(safe_risks),
        },
        "economic_comparison": {
            "continue_cost": str(
                sum(
                    (
                        model.emission(model.propagate(model.prior1, t))
                        for t in range(1, config.horizon + 1)
                    ),
                    F(0),
                )
            ),
            "fixed_query_cost": str(config.query_cost * 3),
            "baseline_total_cost_before_test_gain": str(baseline_total_cost),
            "test_expected_gain": str(expected_gain),
            "expected_promotions": str(expected_promotions),
            "pathwise_queries": 3,
            "optimized_safe_cohort_total_cost": str(cohort_cost),
            "episode_composition_cost": str(episode_cost),
            "episode_minus_cohort_test": str(episode_cost - cohort_cost),
            "recovered_unrestricted_oracle_policy_cost": str(oracle_policy_cost),
            "cohort_test_minus_oracle_policy": str(cohort_cost - oracle_policy_cost),
        },
        "scope": "Fixed-calendar terminal randomized test only; floating LP, exact recovered risk; not a method or certified optimum.",
        "sha256": {
            source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
            for source in (
                "scripts/solve_switching_fixed_cohort_random_test.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "docs/switching_fixed_cohort_random_test_protocol_v1.md",
                "outputs/switching_episode_composition_grid_v1/results.json",
            )
        },
    }
    target = Path("outputs/switching_fixed_cohort_random_test_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
