"""Optimize safe randomized fixed cohorts for the registered reversal cell."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.delayed_regime_information import RegimeModel


def words(n: int):
    return list(product((0, 1), repeat=n))


def posterior_and_word_probability(model: RegimeModel, word: tuple[int, ...]):
    posterior = model.prior1
    probability = F(1)
    for y in word:
        state = model.propagate(posterior, 1)
        py = model.emission(state)
        probability *= py if y else 1 - py
        likelihood1 = model.emission1 if y else 1 - model.emission1
        posterior = state * likelihood1 / (py if y else 1 - py)
    return posterior, probability


def future_gain(model: RegimeModel, posterior: F, *, n: int, delay: int, horizon: int) -> F:
    gain = F(0)
    for time in range(n + delay, horizon + 1):
        positive = model.emission(model.propagate(posterior, time - n))
        gain += 2 * positive - 1
    return gain


def endpoint_strategies(max_queries: int):
    prefixes = [prefix for depth in range(max_queries) for prefix in words(depth)]
    for choices in product((F(0), F(1, 2)), repeat=len(prefixes)):
        p_by_prefix = dict(zip(prefixes, choices, strict=True))
        yield p_by_prefix


def null_word_probability(strategy, word: tuple[int, ...]) -> F:
    probability = F(1)
    for t, y in enumerate(word):
        p = strategy[word[:t]]
        probability *= p if y else 1 - p
    return probability


def run() -> dict[str, object]:
    horizon, budget, delay = 6, 3, 1
    alpha, query_cost, switch_cost = F(1, 10), F(1, 100), F(1, 10)
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    query_counts = list(range(1, min(budget, horizon - delay) + 1))
    plans = []
    for n in query_counts:
        for word in words(n):
            posterior, alt_probability = posterior_and_word_probability(model, word)
            gain = future_gain(model, posterior, n=n, delay=delay, horizon=horizon)
            plans.append((n, word, alt_probability, gain))

    w_index = {n: i for i, n in enumerate(query_counts)}
    z_start = len(query_counts)
    z_index = {(n, word): z_start + i for i, (n, word, _, _) in enumerate(plans)}
    variable_count = z_start + len(plans)
    objective = np.zeros(variable_count)
    for n in query_counts:
        objective[w_index[n]] = float(query_cost * n)
    for n, word, probability, gain in plans:
        objective[z_index[n, word]] = -float(probability * (gain - switch_cost))

    rows, rhs = [], []
    mass_row = np.zeros(variable_count)
    for n in query_counts:
        mass_row[w_index[n]] = 1.0
    rows.append(mass_row)
    rhs.append(1.0)
    for n, word, _, _ in plans:
        row = np.zeros(variable_count)
        row[z_index[n, word]] = 1.0
        row[w_index[n]] = -1.0
        rows.append(row)
        rhs.append(0.0)

    strategies = list(endpoint_strategies(budget))
    risk_rows = []
    for strategy in strategies:
        row = np.zeros(variable_count)
        for n, word, _, _ in plans:
            row[z_index[n, word]] = float(null_word_probability(strategy, word))
        rows.append(row)
        rhs.append(float(alpha))
        risk_rows.append(row)

    result = linprog(
        objective,
        A_ub=np.asarray(rows),
        b_ub=np.asarray(rhs),
        bounds=[(0, None)] * variable_count,
        method="highs",
        options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
    )
    if not result.success:
        raise RuntimeError(f"fixed-cohort LP failed: {result.message}")

    x = [F(float(value)).limit_denominator(10**9) for value in result.x]
    exact_risks = [
        sum(F(float(coef)).limit_denominator(10**9) * x[i] for i, coef in enumerate(row))
        for row in risk_rows
    ]
    worst_risk = max(exact_risks, default=F(0))
    safety_scale = min(F(1), alpha / worst_risk) if worst_risk else F(1)
    x = [value * safety_scale for value in x]
    exact_risks = [risk * safety_scale for risk in exact_risks]
    worst_risk = max(exact_risks, default=F(0))
    assert worst_risk <= alpha

    masses = {n: x[w_index[n]] for n in query_counts}
    chosen = [
        {
            "cohort_size": n,
            "outcome_word": "".join(map(str, word)),
            "cohort_mass": str(masses[n]),
            "unconditional_promotion_mass": str(x[z_index[n, word]]),
            "test_probability_given_cohort": str(
                x[z_index[n, word]] / masses[n] if masses[n] else F(0)
            ),
            "alternative_word_probability": str(probability),
            "expected_postdecision_gain": str(gain),
        }
        for n, word, probability, gain in plans
        if masses[n] or x[z_index[n, word]]
    ]
    expected_queries = sum((n * masses[n] for n in query_counts), F(0))
    expected_promotions = sum(
        (x[z_index[n, word]] * probability for n, word, probability, _ in plans), F(0)
    )
    expected_gain = (
        sum(
            (
                x[z_index[n, word]] * probability * (gain - switch_cost)
                for n, word, probability, gain in plans
            ),
            F(0),
        )
        - query_cost * expected_queries
    )
    baseline_decision_cost = F(horizon, 2)
    total_cost = baseline_decision_cost - expected_gain
    decision_cost = baseline_decision_cost - sum(
        (x[z_index[n, word]] * probability * gain for n, word, probability, gain in plans),
        F(0),
    )
    query_charge = query_cost * expected_queries
    switch_charge = switch_cost * expected_promotions

    oracle_total = F(
        json.loads(Path("outputs/switching_reversal_diagnostic_v1/results.json").read_text())[
            "oracle"
        ]["lp_report"]["calibrated_total_cost"]
    )
    metrics_cost = decision_cost + query_charge + switch_charge
    assert metrics_cost == total_cost
    return {
        "status": "completed_robust_fixed_cohort_frontier",
        "parameters": {
            "horizon": horizon,
            "budget": budget,
            "delay": delay,
            "alpha": str(alpha),
            "query_cost": str(query_cost),
            "switch_cost": str(switch_cost),
            "model": {
                "transition01": str(model.transition01),
                "transition10": str(model.transition10),
                "emission0": str(model.emission0),
                "emission1": str(model.emission1),
                "prior1": str(model.prior1),
            },
        },
        "cohort_sizes": query_counts,
        "causal_null_endpoint_strategies": len(strategies),
        "worst_causal_null_risk_after_rational_recovery": str(worst_risk),
        "safety_scale_after_rational_recovery": str(safety_scale),
        "lottery_masses": {str(n): str(mass) for n, mass in masses.items()},
        "expected_queries": str(expected_queries),
        "expected_promotions": str(expected_promotions),
        "metrics": {
            "decision_cost": str(decision_cost),
            "query_cost": str(query_charge),
            "switch_cost": str(switch_charge),
            "total_cost": str(total_cost),
        },
        "oracle_total_cost": str(oracle_total),
        "oracle_minus_fixed_cohort_cost": str(oracle_total - total_cost),
        "oracle_strictly_better": oracle_total < total_cost,
        "nonzero_plan_entries": chosen,
        "lp_objective_before_rational_recovery": float(result.fun),
        "max_lp_constraint_violation": float(max(0, np.max(np.asarray(rows) @ result.x - rhs))),
        "scope": "Strongest randomized upfront fixed-cohort terminal-test comparator in this finite cell; no contingent stopping or rollback.",
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                "scripts/solve_switching_fixed_cohort_frontier.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_reversal_diagnostic_v1.md",
            )
        },
    }


if __name__ == "__main__":
    output = run()
    folder = Path("outputs/switching_reversal_diagnostic_v1")
    (folder / "fixed_cohort_frontier.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))
