"""Exact small-cell cost screen for policies with monotone promotion events."""

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


def is_monotone(table: tuple[int, ...]) -> bool:
    # Tape index uses y1 as the low bit and y2 as the high bit.
    for y1, y2 in product((0, 1), repeat=2):
        here = table[y1 + 2 * y2]
        for z1, z2 in product((0, 1), repeat=2):
            if y1 <= z1 and y2 <= z2 and here > table[z1 + 2 * z2]:
                return False
    return True


def pure_plans() -> list[dict[str, object]]:
    plans = []
    for action1, query1 in product((0, 1), repeat=2):
        if query1:
            continuations = [
                {"action2_by_y1": (a0, a1), "query2": 0} for a0, a1 in product((0, 1), repeat=2)
            ]
        else:
            continuations = [
                {"action2_by_y1": (a2, a2), "query2": q2} for a2, q2 in product((0, 1), repeat=2)
            ]
        for continuation in continuations:
            action2_by_y1 = continuation["action2_by_y1"]
            table_list = [0] * 4
            for y1, y2 in product((0, 1), repeat=2):
                table_list[y1 + 2 * y2] = int(bool(action1 or action2_by_y1[y1]))
            table = tuple(table_list)
            risk = F(sum(table), 4)
            plans.append(
                {
                    "action1": action1,
                    "query1": query1,
                    "action2_by_y1": action2_by_y1,
                    "query2": continuation["query2"],
                    "promotion_table": table,
                    "monotone": is_monotone(table),
                    "boundary_risk": risk,
                }
            )
    return plans


def plan_cost(plan: dict[str, object], model: RegimeModel, query_cost: F, switch_cost: F) -> F:
    action1 = int(plan["action1"])
    query1 = int(plan["query1"])
    a2s = tuple(plan["action2_by_y1"])
    query2 = int(plan["query2"])
    result = F(0)
    for p, prior in ((model.emission0, 1 - model.prior1), (model.emission1, model.prior1)):
        loss1 = p if action1 == 0 else 1 - p
        stage1 = loss1 + query_cost * query1 + switch_cost * action1
        if query1:
            expected_loss2 = sum(
                (p if action2 == 0 else 1 - p) * (p if y1 else 1 - p)
                for y1, action2 in enumerate(a2s)
            )
        else:
            expected_loss2 = p if a2s[0] == 0 else 1 - p
        expected_switch2 = (
            switch_cost * sum((a2s[y1] != action1) * (p if y1 else 1 - p) for y1 in (0, 1))
            if query1
            else switch_cost * (a2s[0] != action1)
        )
        stage2 = expected_loss2 + query_cost * query2 + expected_switch2
        result += prior * (stage1 + stage2)
    return result


def conditional_null_risk(plan: dict[str, object], probability1: F) -> F:
    if plan["action1"]:
        return F(1)
    if plan["query1"]:
        action0, action1 = plan["action2_by_y1"]
        return (1 - probability1) * action0 + probability1 * action1
    return F(plan["action2_by_y1"][0])


def run() -> dict[str, object]:
    model = RegimeModel(transition01=0, transition10=0)
    config = GameConfig(
        horizon=2,
        budget=1,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    plans = pure_plans()
    monotone = [plan for plan in plans if plan["monotone"]]
    costs = [plan_cost(plan, model, config.query_cost, config.switch_cost) for plan in monotone]
    risks = [plan["boundary_risk"] for plan in monotone]
    result = linprog(
        np.array([float(value) for value in costs]),
        A_ub=np.array([[float(value) for value in risks]]),
        b_ub=np.array([float(config.alpha)]),
        A_eq=np.ones((1, len(monotone))),
        b_eq=np.array([1.0]),
        bounds=[(0.0, None)] * len(monotone),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    weights = [F(float(value)).limit_denominator(10**8) for value in result.x]
    total_weight = sum(weights)
    weights = [value / total_weight for value in weights]
    risk = sum((w * r for w, r in zip(weights, risks, strict=True)), F(0))
    cost = sum((w * c for w, c in zip(weights, costs, strict=True)), F(0))
    assert risk <= config.alpha

    # Exact finite extensive-form policy LP for all 16 pure plans. The null sees
    # the public root choice, so enumerate endpoint responses separately by root choice.
    all_costs = [plan_cost(plan, model, config.query_cost, config.switch_cost) for plan in plans]
    null_responses = tuple(product((F(0), F(1, 2)), repeat=4))
    risk_rows = [
        [
            float(conditional_null_risk(plan, response[2 * plan["action1"] + plan["query1"]]))
            for plan in plans
        ]
        for response in null_responses
    ]
    unrestricted_lp = linprog(
        np.array([float(value) for value in all_costs]),
        A_ub=np.array(risk_rows),
        b_ub=np.full(len(risk_rows), float(config.alpha)),
        A_eq=np.ones((1, len(plans))),
        b_eq=np.array([1.0]),
        bounds=[(0.0, None)] * len(plans),
        method="highs",
    )
    if not unrestricted_lp.success:
        raise RuntimeError(unrestricted_lp.message)
    unrestricted_weights = [F(float(value)).limit_denominator(10**8) for value in unrestricted_lp.x]
    unrestricted_total = sum(unrestricted_weights)
    unrestricted_weights = [value / unrestricted_total for value in unrestricted_weights]
    unrestricted_primal_cost = sum(
        (w * c for w, c in zip(unrestricted_weights, all_costs, strict=True)), F(0)
    )
    assert all(
        sum((w * F(row[j]) for j, w in enumerate(unrestricted_weights)), F(0))
        <= config.alpha + F(1, 10**12)
        for row in risk_rows
    )
    dual_nu = F(float(unrestricted_lp.eqlin.marginals[0])).limit_denominator(10**8)
    dual_mu = [
        -F(float(value)).limit_denominator(10**8) for value in unrestricted_lp.ineqlin.marginals
    ]
    assert all(value >= 0 for value in dual_mu)
    assert all(
        dual_nu
        <= all_costs[j]
        + sum((dual_mu[i] * F(risk_rows[i][j]) for i in range(len(risk_rows))), F(0))
        for j in range(len(plans))
    )
    dual_bound = dual_nu - config.alpha * sum(dual_mu)
    assert dual_bound == unrestricted_primal_cost == F(987, 1000)

    unrestricted = CausalSwitchingGame(config, model)

    def selected_policy(history, outcomes):
        choices = unrestricted.choices(history)
        if not history:
            mass = {(0, 0): F(4, 5), (0, 1): F(1, 5)}
        elif history[0][1] == 0:
            mass = {(0, 0): F(1)}
        else:
            observed = dict(unrestricted.information(history, outcomes)[1])
            mass = {(observed[1], 0): F(1)}
        return tuple(mass.get(choice, F(0)) for choice in choices)

    candidate_metrics = unrestricted.expected_metrics(selected_policy)
    candidate_causal_risk = unrestricted.null_risk(selected_policy)
    assert sum(candidate_metrics[:3]) == cost
    assert candidate_causal_risk == risk == config.alpha
    report, _, _ = unrestricted.solve()
    unrestricted_cost = F(report["calibrated_total_cost"])
    assert cost == F(987, 1000)
    assert unrestricted_cost == cost
    selected = [
        {
            "weight": str(weight),
            **{key: value for key, value in plan.items() if key != "boundary_risk"},
        }
        for weight, plan in zip(weights, monotone, strict=True)
        if weight
    ]
    return {
        "status": "monotone_policy_lp_screen_passed",
        "contract": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "model": "static hidden regime; emissions 1/4 and 3/4, equal prior",
        },
        "pure_policy_count": len(plans),
        "monotone_pure_policy_count": len(monotone),
        "monotone_mixture_risk": str(risk),
        "monotone_mixture_cost": str(cost),
        "independent_forward_cost": str(sum(candidate_metrics[:3])),
        "independent_causal_null_risk": str(candidate_causal_risk),
        "unrestricted_causal_game_recovered_cost": str(unrestricted_cost),
        "all_policy_mixture_primal_cost": str(unrestricted_primal_cost),
        "all_policy_exact_dual_bound": str(dual_bound),
        "all_policy_dual_certificate": {
            "nu": str(dual_nu),
            "nonzero_null_response_multipliers": [
                {"response_index": i, "mu": str(value)} for i, value in enumerate(dual_mu) if value
            ],
            "constraints_verified_for_pure_plans": len(plans),
        },
        "observed_cost_gap": str(cost - unrestricted_cost),
        "selected_monotone_mixture": selected,
        "unrestricted_solver_objective": report["solver_objective"],
        "unrestricted_solver_gap_certificate": "not available; compare with analytic test oracle only",
        "scope": "Exhaustive two-round monotone-policy class; no scalable algorithm or efficacy claim.",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_monotone_policy_cost_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))
