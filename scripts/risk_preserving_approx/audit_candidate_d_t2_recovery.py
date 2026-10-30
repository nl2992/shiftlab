"""Audit a fixed Candidate D multiplier pair against the exact T=2 LP."""

from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def load_policy(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    compiled = json.loads((path.parent / "compile.json").read_text(encoding="utf-8"))
    cost = F(data["alternative_cost"])
    risk = F(data["causal_null_risk"])
    lam = F(compiled["config"]["lambda"])
    optimum = -F(str(compiled["exact_scalarized_game_value"])).limit_denominator(10**9)
    gap = cost + lam * risk - optimum
    return cost, risk, data, lam, gap


def exact_constrained_audit(config: GameConfig, model: RegimeModel):
    start = time.perf_counter()
    game = CausalSwitchingGame(config, model)
    game.build()
    e_matrix, e = game.learner.matrix()
    f_matrix, f = game.opponent.matrix()
    n_x, n_y = game.learner.count, game.opponent.count
    null_payoff = csr_matrix(
        (
            [game.risk[k] for k in game.risk],
            ([k[0] for k in game.risk], [k[1] for k in game.risk]),
        ),
        shape=(n_x, n_y),
    )
    objective = np.zeros(n_x + len(f))
    for sequence, value in game.cost.items():
        objective[sequence] = float(value)
    inequalities = vstack(
        [
            hstack([null_payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, n_x)), csr_matrix(f.reshape(1, -1))]),
        ]
    ).tocsr()
    rhs = np.r_[np.zeros(n_y), float(config.alpha)]
    equality = hstack([e_matrix, csr_matrix((len(e), len(f)))]).tocsr()
    result = linprog(
        objective,
        A_ub=inequalities,
        b_ub=rhs,
        A_eq=equality,
        b_eq=e,
        bounds=[(0, None)] * n_x + [(None, None)] * len(f),
        method="highs",
        options={
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(f"exact constrained LP failed: {result.message}")
    solve_seconds = time.perf_counter() - start
    policy, _records = game.recover(result.x[:n_x])
    metrics = game.expected_metrics(policy)
    oracle_cost = sum(metrics[:3])
    oracle_risk = game.null_risk(policy)
    lambda_star = F(str(-result.ineqlin.marginals[-1])).limit_denominator(10**9)
    return game, {
        "status": result.message,
        "objective": str(F(str(result.fun)).limit_denominator(10**9)),
        "recovered_cost": str(oracle_cost),
        "recovered_risk": str(oracle_risk),
        "lambda_star_from_alpha_dual": str(lambda_star),
        "equality_residual": float(np.max(np.abs(equality @ result.x - e))),
        "inequality_violation": float(max(0.0, np.max(inequalities @ result.x - rhs))),
        "learner_sequences": n_x,
        "null_sequences": n_y,
        "flow_nodes": game.nodes,
        "solve_seconds_including_build": solve_seconds,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--low-risk", type=Path, required=True)
    parser.add_argument("--high-risk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = GameConfig(
        horizon=2, budget=1, delay=1, alpha=F(1, 10), query_cost=F(1, 100), switch_cost=F(1, 10)
    )
    model = RegimeModel()
    _game, oracle = exact_constrained_audit(config, model)
    low_cost, low_risk, low, lambda_low, low_gap = load_policy(args.low_risk)
    high_cost, high_risk, high, lambda_high, high_gap = load_policy(args.high_risk)
    alpha = config.alpha
    lambda_star = F(oracle["lambda_star_from_alpha_dual"])
    high_risk_policy = low_risk >= alpha
    safe_policy = high_risk <= alpha
    multiplier_ordered = lambda_low < lambda_high and high_risk_policy and safe_policy
    dual_in_interval = lambda_low <= lambda_star <= lambda_high
    result = {
        "instance": {"T": 2, "B": 1, "d": 1, "alpha": str(alpha)},
        "exact_constrained_oracle": oracle,
        "lambda_low": {
            "lambda": str(lambda_low),
            "cost": str(low_cost),
            "risk": str(low_risk),
            "scalarized_cost": str(low_cost + lambda_low * low_risk),
            "solver_gap": str(low_gap),
            "query_cap": low.get("max_pathwise_queries"),
        },
        "lambda_high": {
            "lambda": str(lambda_high),
            "cost": str(high_cost),
            "risk": str(high_risk),
            "scalarized_cost": str(high_cost + lambda_high * high_risk),
            "solver_gap": str(high_gap),
            "query_cap": high.get("max_pathwise_queries"),
        },
        "risk_bracketed": bool(multiplier_ordered),
        "exact_dual_inside_multiplier_interval": bool(dual_in_interval),
        "certified_bracket": bool(multiplier_ordered and dual_in_interval),
    }

    if result["certified_bracket"]:
        weight_high_risk = (alpha - high_risk) / (low_risk - high_risk)
        mixture_cost = weight_high_risk * low_cost + (1 - weight_high_risk) * high_cost
        exact_cost_gaps = [low_gap, high_gap]
        epsilon = max(exact_cost_gaps)
        delta = lambda_high - lambda_low
        result["root_mixture"] = {
            "weight_on_high_risk_policy": str(weight_high_risk),
            "cost": str(mixture_cost),
            "risk_upper_bound": str(alpha),
            "exact_oracle_cost": oracle["recovered_cost"],
            "cost_gap": str(mixture_cost - F(oracle["recovered_cost"])),
            "conditional_recovery_bound_epsilon": str(epsilon),
            "conditional_recovery_bound_delta": str(delta),
            "conditional_recovery_bound_total": str(epsilon + delta),
            "bound_useful_at_tolerance_5e-3": epsilon + delta <= F(5, 1000),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
