"""Exact check: a fixed e-threshold is a subset of alpha-safe switching policies."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def enumerate_policy(theta: F, *, horizon: int, delay: int, alpha: F) -> dict[str, F]:
    assert 0 < alpha <= F(1, 2)
    query_cost, switch_cost = F(1, 100), F(1, 10)
    decision_loss, switches, promotion = F(0), F(0), F(0)
    for first_outcome, outcome_weight in ((0, 1 - theta), (1, theta)):
        chance = 2 * alpha if first_outcome and delay < horizon else F(0)
        for promote, coin_weight in ((False, 1 - chance), (True, chance)):
            weight = outcome_weight * coin_weight
            for time in range(1, horizon + 1):
                action = int(promote and time >= 1 + delay)
                if time == 1:
                    # The queried first label is fixed on this branch.
                    loss = F(first_outcome)
                else:
                    loss = theta if not action else 1 - theta
                decision_loss += weight * loss
            promotion += weight * promote
            switches += weight * promote
    return {
        "promotion_probability": promotion,
        "queries": F(1),
        "decision_loss": decision_loss,
        "switching_cost": switch_cost * switches,
        "total_cost": decision_loss + switch_cost * switches + query_cost,
    }


def run() -> dict[str, object]:
    alpha, horizon, delay = F(1, 10), 20, 2
    laws = []
    for theta in (F(0), F(1, 4), F(1, 2), F(3, 4), F(1)):
        row = enumerate_policy(theta, horizon=horizon, delay=delay, alpha=alpha)
        assert row["promotion_probability"] == 2 * alpha * theta
        assert row["queries"] == 1
        if theta <= F(1, 2):
            assert row["promotion_probability"] <= alpha
        laws.append({"theta": str(theta), **{k: str(v) for k, v in row.items()}})
    formula_checks = []
    for t, d, a in product((8, 20), (1, 2), (F(1, 20), F(1, 10))):
        mean_cost = (
            sum(
                enumerate_policy(theta, horizon=t, delay=d, alpha=a)["total_cost"]
                for theta in (F(1, 4), F(3, 4))
            )
            / 2
        )
        improvement = (t - d) * a / 4 - a / 10 - F(1, 100)
        assert mean_cost == F(t, 2) - improvement
        formula_checks.append({"T": t, "delay": d, "alpha": str(a), "cost": str(mean_cost)})
    no_arrival = enumerate_policy(F(3, 4), horizon=2, delay=2, alpha=alpha)
    assert no_arrival["promotion_probability"] == 0
    assert no_arrival["total_cost"] == F(3, 2) + F(1, 100)
    primary_cost = (
        sum(
            enumerate_policy(theta, horizon=horizon, delay=delay, alpha=alpha)["total_cost"]
            for theta in (F(1, 4), F(3, 4))
        )
        / 2
    )
    assert primary_cost == F(957, 100)
    assert F(3, 2) ** 5 < 10 <= F(3, 2) ** 6
    optional = []
    for theta in (F(1, 4), F(1, 2), F(3, 4)):
        cost, requests, error, expected_initial_wealth, expected_final_wealth = (F(0),) * 5
        for active, coin_weight in ((False, 1 - 2 * alpha), (True, 2 * alpha)):
            initial_wealth = F(1) / (2 * alpha) if active else F(0)
            expected_initial_wealth += coin_weight * initial_wealth
            if not active:
                cost += coin_weight * horizon * theta
                continue
            for first, weight in ((0, 1 - theta), (1, theta)):
                mass = coin_weight * weight
                requests += mass
                error += mass * first
                decision_cost = theta * delay + (1 - theta if first else theta) * (horizon - delay)
                # Y_1 is conditioned on in this branch; only rounds 2..d
                # have expected theta before the queried label can be used.
                decision_cost += first - theta
                cost += mass * (decision_cost + F(1, 100) + F(1, 10) * first)
                expected_final_wealth += mass * initial_wealth * 2 * first
        assert requests == 2 * alpha
        assert expected_initial_wealth == 1
        if theta <= F(1, 2):
            assert error <= alpha and expected_final_wealth <= expected_initial_wealth
        optional.append(
            {
                "theta": str(theta),
                "cost": str(cost),
                "queries": str(requests),
                "promotion_probability": str(error),
            }
        )
    optional_prior_cost = (F(optional[0]["cost"]) + F(optional[2]["cost"])) / 2
    assert optional_prior_cost == primary_cost - (1 - 2 * alpha) / 100
    assert optional_prior_cost == F(4781, 500)
    return {
        "status": "fixed_e_gate_is_strictly_restrictive_in_this_instance",
        "primary": {
            "T": horizon,
            "delay": delay,
            "alpha": str(alpha),
            "one_label_policy_cost": str(primary_cost),
            "fixed_gate_cost_B_1_through_5": "10",
            "optional_query_policy_cost": str(optional_prior_cost),
        },
        "law_specific_checks": laws,
        "formula_checks": formula_checks,
        "no_arrival_boundary_checked": True,
        "optional_query_checks": optional,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact supporting counterexample; not a new method or empirical validation.",
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_risk_frontier_audit_v1/checks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["primary"], indent=2))
