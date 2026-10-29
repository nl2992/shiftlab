"""Compare a randomized fixed cohort with the adaptive causal switching oracle."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def alternative_tapes(model: RegimeModel, n: int, horizon: int, delay: int):
    result = {}
    for tape in product((0, 1), repeat=n):
        posterior = model.prior1
        probability = F(1)
        for t, y in enumerate(tape, start=1):
            state = model.propagate(posterior, 1)
            py = model.emission(state)
            probability *= py if y else 1 - py
            likelihood = model.emission1 if y else 1 - model.emission1
            posterior = state * likelihood / (py if y else 1 - py)
        decision_time = n + delay
        delta = F(0)
        for t in range(decision_time, horizon + 1):
            py = model.emission(model.propagate(posterior, t - n))
            delta += 1 - 2 * py
        result[tape] = (probability, delta)
    return result


def null_profile_tape_laws(max_n: int, cohorts: tuple[int, ...]):
    """Joint endpoint-null laws, sharing choices while query histories coincide."""
    prefixes = tuple(prefix for size in range(max_n) for prefix in product((0, 1), repeat=size))
    profiles = []
    for endpoint_bits in product((0, 1), repeat=len(prefixes)):
        conditional = dict(zip(prefixes, (F(bit, 2) for bit in endpoint_bits), strict=True))
        laws = {}
        for n in cohorts:
            law = {}
            for tape in product((0, 1), repeat=n):
                mass = F(1)
                for i, y in enumerate(tape):
                    p = conditional[tape[:i]]
                    mass *= p if y else 1 - p
                law[tape] = mass
            laws[n] = law
        profiles.append(laws)
    return profiles


def main() -> None:
    horizon, budget, delay = 6, 3, 1
    alpha, query_cost, switch_cost = F(1, 10), F(1, 100), F(1, 10)
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    cohorts = tuple(range(1, min(budget, horizon - delay) + 1))
    tape_data = {n: alternative_tapes(model, n, horizon, delay) for n in cohorts}
    null_profiles = null_profile_tape_laws(budget, cohorts)

    p_index = {n: n for n in range(budget + 1)}
    x_index = {}
    cursor = budget + 1
    for n in cohorts:
        for tape in tape_data[n]:
            x_index[n, tape] = cursor
            cursor += 1
    u_index = cursor
    nvars = cursor + 1
    objective_exact = [F(0)] * nvars
    for n in range(budget + 1):
        objective_exact[p_index[n]] = F(n) * query_cost
    for n in cohorts:
        for tape, (alt_mass, delta) in tape_data[n].items():
            objective_exact[x_index[n, tape]] = alt_mass * (delta + switch_cost)
    objective = np.array([float(value) for value in objective_exact])

    rows, rhs, rows_exact, rhs_exact = [], [], [], []
    for n in cohorts:
        for tape in tape_data[n]:
            row = np.zeros(nvars)
            row[x_index[n, tape]] = 1.0
            row[p_index[n]] = -1.0
            rows.append(row)
            rhs.append(0.0)
            exact_row = [F(0)] * nvars
            exact_row[x_index[n, tape]] = F(1)
            exact_row[p_index[n]] = F(-1)
            rows_exact.append(exact_row)
            rhs_exact.append(F(0))
    for profile in null_profiles:
        row = np.zeros(nvars)
        exact_row = [F(0)] * nvars
        for n in cohorts:
            for tape, mass in profile[n].items():
                row[x_index[n, tape]] = float(mass)
                exact_row[x_index[n, tape]] = mass
        row[u_index] = -1.0
        exact_row[u_index] = F(-1)
        rows.append(row)
        rhs.append(0.0)
        rows_exact.append(exact_row)
        rhs_exact.append(F(0))
    row = np.zeros(nvars)
    row[u_index] = 1.0
    rows.append(row)
    rhs.append(float(alpha))
    exact_row = [F(0)] * nvars
    exact_row[u_index] = F(1)
    rows_exact.append(exact_row)
    rhs_exact.append(alpha)

    equality = np.zeros((1, nvars))
    equality_exact = [F(0)] * nvars
    for n in range(budget + 1):
        equality[0, p_index[n]] = 1.0
        equality_exact[p_index[n]] = F(1)
    result = linprog(
        objective,
        A_ub=np.asarray(rows),
        b_ub=np.asarray(rhs),
        A_eq=equality,
        b_eq=np.array([1.0]),
        bounds=[(0.0, None)] * nvars,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)

    p = {n: F(float(result.x[p_index[n]])).limit_denominator(100_000) for n in range(budget + 1)}
    total_p = sum(p.values())
    p = {n: value / total_p for n, value in p.items()}
    x = {
        (n, tape): min(p[n], F(float(result.x[index])).limit_denominator(10**9))
        for (n, tape), index in x_index.items()
    }

    def joint_risk(profile) -> F:
        return sum(x[n, tape] * profile[n][tape] for n in cohorts for tape in tape_data[n])

    raw_risk = max(joint_risk(profile) for profile in null_profiles)
    if raw_risk > alpha:
        factor = alpha / raw_risk
        x = {key: value * factor for key, value in x.items()}
    worst_profile = max(null_profiles, key=joint_risk)
    risk_by_n = {
        n: str(sum(x[n, tape] * worst_profile[n][tape] for tape in tape_data[n])) for n in cohorts
    }
    risk = joint_risk(worst_profile)

    base = sum(model.emission(model.propagate(model.prior1, t)) for t in range(1, horizon + 1))
    query_term = sum(F(n) * query_cost * p[n] for n in range(budget + 1))
    promotion_term = sum(
        x[n, tape] * tape_data[n][tape][0] * (tape_data[n][tape][1] + switch_cost)
        for n in cohorts
        for tape in tape_data[n]
    )
    exact_cost = base + query_term + promotion_term

    # Independently embed the recovered policy in the reference game recursion.
    game = CausalSwitchingGame(
        GameConfig(
            horizon=horizon,
            budget=budget,
            delay=delay,
            alpha=alpha,
            query_cost=query_cost,
            switch_cost=switch_cost,
        ),
        model,
    )

    def recovered_policy(history, outcomes):
        choices = game.choices(history)
        if not history:
            mass = {(0, 0): F(1) - p[3], (0, 1): p[3]}
            return tuple(mass.get(choice, F(0)) for choice in choices)
        cohort_three = history[0][1] == 1
        if not cohort_three:
            target = (0, 0)
        elif len(history) in (1, 2):
            target = (0, 1)
        elif len(history) == 3:
            released = dict(outcomes)
            target = (int(all(released.get(t) == 1 for t in (1, 2, 3))), 0)
        else:
            target = (history[-1][0], 0)
        return tuple(F(choice == target) for choice in choices)

    independent_metrics = game.expected_metrics(recovered_policy)
    independent_risk = game.null_risk(recovered_policy)
    assert sum(independent_metrics[:3]) == exact_cost
    assert independent_risk == risk

    # Rationalize the numerical dual and verify a rigorous lower bound exactly.
    dual_ub = [F(float(value)).limit_denominator(10**9) for value in result.ineqlin.marginals]
    dual_eq = F(float(result.eqlin.marginals[0])).limit_denominator(10**9)
    dual_ub = [min(value, F(0)) for value in dual_ub]
    slacks = []
    for column in range(nvars):
        lhs = sum(rows_exact[row][column] * dual_ub[row] for row in range(len(rows_exact)))
        lhs += equality_exact[column] * dual_eq
        slacks.append(objective_exact[column] - lhs)
    residual = sum(max(F(0), -slack) for slack in slacks)
    restricted_lower_relative = (
        sum(rhs_exact[row] * dual_ub[row] for row in range(len(rows_exact))) + dual_eq - residual
    )
    restricted_feasible_relative = query_term + promotion_term
    assert restricted_lower_relative <= restricted_feasible_relative
    restricted_lower_total = base + restricted_lower_relative
    restricted_upper_total = base + restricted_feasible_relative
    oracle_upper = F(461083, 160000)

    expected_queries = sum(F(n) * p[n] for n in range(budget + 1))
    promotion_probability = sum(
        x[n, tape] * tape_data[n][tape][0] for n in cohorts for tape in tape_data[n]
    )
    policy = {
        "cohort_probability": {str(n): str(p[n]) for n in range(budget + 1)},
        "conditional_promotion_probability_by_tape": {
            str(n): {
                "".join(map(str, tape)): str(x[n, tape] / p[n] if p[n] else F(0))
                for tape in tape_data[n]
            }
            for n in cohorts
        },
    }
    sources = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/compare_switching_fixed_cohort_to_adaptive_oracle.py",
    )
    output = {
        "status": "registered_matched_fixed_cohort_vs_adaptive_oracle_diagnostic",
        "config": {
            "horizon": horizon,
            "budget": budget,
            "delay": delay,
            "alpha": str(alpha),
            "query_cost": str(query_cost),
            "switch_cost": str(switch_cost),
        },
        "model": {name: str(getattr(model, name)) for name in model.__dataclass_fields__},
        "cohorts": list(cohorts),
        "joint_endpoint_null_profile_count": len(null_profiles),
        "null_profile_semantics": (
            "The causal null shares each conditional probability across cohort branches until "
            "their query histories diverge; cohort choice is not revealed at time zero."
        ),
        "numerical_lp_objective_relative_to_no_query": result.fun,
        "recovered_policy": policy,
        "exact_recovered_policy": {
            "base_no_action_cost": str(base),
            "expected_query_cost": str(query_term),
            "expected_incremental_deployment_and_switch_cost": str(promotion_term),
            "total_expected_cost": str(exact_cost),
            "worst_causal_null_promotion_risk": str(risk),
            "risk_by_cohort": risk_by_n,
            "expected_queries": str(expected_queries),
            "alternative_promotion_probability": str(promotion_probability),
            "pathwise_query_cap": budget,
            "independent_game_cost_check": str(sum(independent_metrics[:3])),
            "independent_game_null_risk_check": str(independent_risk),
        },
        "restricted_lp_rational_certificate": {
            "lower_total_cost": str(restricted_lower_total),
            "feasible_upper_total_cost": str(restricted_upper_total),
            "bracket_width": str(restricted_upper_total - restricted_lower_total),
            "dual_residual_sum": str(residual),
            "dual_inequality_multipliers": [str(value) for value in dual_ub],
            "dual_equality_multiplier": str(dual_eq),
            "dual_inequality_signs_verified": all(value <= 0 for value in dual_ub),
            "dual_constraint_slacks_nonnegative_after_residual": all(
                slack + residual >= 0 for slack in slacks
            ),
        },
        "oracle_certificate": {
            "unrestricted_lower": "576353749991/200000000000",
            "unrestricted_upper": str(oracle_upper),
            "fixed_cohort_certified_excess_over_unrestricted_upper": str(
                restricted_lower_total - oracle_upper
            ),
        },
        "interpretation": (
            "The recovered fixed-cohort policy is exactly re-evaluated and risk-safe. The "
            "fixed-cohort LP value is enclosed by an exact rational primal-dual certificate. "
            "This is a one-cell structural separation, not a novel algorithm or empirical "
            "efficacy result."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sources
        },
    }
    target = Path("outputs/switching_fixed_cohort_vs_adaptive_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["exact_recovered_policy"], indent=2))


if __name__ == "__main__":
    main()
