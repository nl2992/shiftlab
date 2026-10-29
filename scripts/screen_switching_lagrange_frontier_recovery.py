"""Screen generic Lagrangian frontier recovery on the certified six-event game."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def scalar_policy(game: CausalSwitchingGame, multiplier: float):
    """Solve min_x C(x)+lambda sup_nu R(x,nu) by sequence-form duality."""
    game.build()
    learner_flow, learner_rhs = game.learner.matrix()
    null_flow, null_rhs = game.opponent.matrix()
    n_x, n_f = game.learner.count, null_flow.shape[0]
    risk_matrix = csr_matrix(
        (
            list(game.risk.values()),
            (
                [key[0] for key in game.risk],
                [key[1] for key in game.risk],
            ),
        ),
        shape=(n_x, game.opponent.count),
    )
    objective = np.zeros(n_x + n_f)
    for sequence, cost in game.cost.items():
        objective[sequence] = cost
    objective[n_x:] = multiplier * null_rhs
    inequalities = hstack([risk_matrix.T, -null_flow.T], format="csr")
    equalities = hstack([learner_flow, csr_matrix((learner_flow.shape[0], n_f))], format="csr")
    result = linprog(
        objective,
        A_ub=inequalities,
        b_ub=np.zeros(inequalities.shape[0]),
        A_eq=equalities,
        b_eq=learner_rhs,
        bounds=[(0, None)] * n_x + [(None, None)] * n_f,
        method="highs",
        options={
            "time_limit": 60.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(f"scalar LP failed at lambda={multiplier}: {result.message}")
    policy, records = game.recover(result.x[:n_x])
    metrics = game.expected_metrics(policy)
    cost = sum(metrics[:3])
    risk = game.null_risk(policy)
    scalar_value = cost + F(str(multiplier)) * risk
    return {
        "lambda": multiplier,
        "policy": policy,
        "records": records,
        "cost": cost,
        "risk": risk,
        "metrics": metrics,
        "lp_objective": float(result.fun),
        "scalar_value_after_recovery": str(scalar_value),
        "max_inequality_residual": float(max(0.0, np.max(inequalities @ result.x - 0.0))),
    }


def root_mixture_policy(game, left_policy, right_policy, left_weight):
    """Represent a persistent private root lottery as a behavioral policy."""

    def policy(history, outcomes):
        left_likelihood = F(1)
        right_likelihood = F(1)
        for index, selected in enumerate(history):
            prefix = history[:index]
            left_choices = left_policy(prefix, outcomes)
            right_choices = right_policy(prefix, outcomes)
            available = game.choices(prefix)
            selected_index = available.index(selected)
            left_likelihood *= left_choices[selected_index]
            right_likelihood *= right_choices[selected_index]
        left_mass = left_weight * left_likelihood
        right_mass = (1 - left_weight) * right_likelihood
        total = left_mass + right_mass
        if not total:
            return right_policy(history, outcomes)
        posterior_left = left_mass / total
        left_choices = left_policy(history, outcomes)
        right_choices = right_policy(history, outcomes)
        return tuple(
            posterior_left * left + (1 - posterior_left) * right
            for left, right in zip(left_choices, right_choices, strict=True)
        )

    return policy


def main() -> None:
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    game = CausalSwitchingGame(config, model)

    # Bisection locates a pair whose exactly forward-verified risks bracket alpha.
    low = scalar_policy(game, 0.0)
    high_multiplier = 1.0
    high = scalar_policy(game, high_multiplier)
    while high["risk"] > config.alpha:
        high_multiplier *= 2
        high = scalar_policy(game, high_multiplier)
        if high_multiplier > 1_048_576:
            raise RuntimeError("failed to find a low-risk scalarized policy")
    bracket = None
    for _ in range(16):
        mid_multiplier = (low["lambda"] + high["lambda"]) / 2
        mid = scalar_policy(game, mid_multiplier)
        if mid["risk"] >= config.alpha:
            low = mid
        else:
            high = mid
        if low["risk"] >= config.alpha >= high["risk"]:
            bracket = (low, high)
    if bracket is None:
        raise RuntimeError("scalarized policies did not bracket the risk constraint")

    above, below = bracket
    above_risk, below_risk = above["risk"], below["risk"]
    if above_risk == below_risk:
        weight_above = F(1)
    else:
        weight_above = (config.alpha - below_risk) / (above_risk - below_risk)
    weight_below = 1 - weight_above

    # Preserve one root coin across the whole trajectory, not a fresh coin at each history.
    mixture = root_mixture_policy(game, above["policy"], below["policy"], weight_above)
    mixture_cost = sum(game.expected_metrics(mixture)[:3])
    mixture_risk = game.null_risk(mixture)
    weighted_component_risk = weight_above * above_risk + weight_below * below_risk
    weighted_component_cost = weight_above * above["cost"] + weight_below * below["cost"]
    assert weighted_component_risk == config.alpha
    assert mixture_cost == weighted_component_cost
    assert mixture_risk <= weighted_component_risk
    assert mixture_risk <= config.alpha

    reference_path = Path("outputs/switching_reversal_diagnostic_v1/results.json")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    oracle_cost = F(reference["oracle"]["lp_report"]["calibrated_total_cost"])
    dual_distance = abs(F(str(above["lambda"])) - F(str(below["lambda"])))
    result = {
        "status": "generic_lagrangian_frontier_recovery_screen",
        "contract": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "causal_null": "history-adaptive conditional Bernoulli success probability in [0,1/2]",
        },
        "high_risk_policy": {
            "lambda": above["lambda"],
            "cost": str(above["cost"]),
            "risk": str(above_risk),
            "scalar_lp_objective": above["lp_objective"],
        },
        "low_risk_policy": {
            "lambda": below["lambda"],
            "cost": str(below["cost"]),
            "risk": str(below_risk),
            "scalar_lp_objective": below["lp_objective"],
        },
        "mixture": {
            "high_risk_weight": str(weight_above),
            "low_risk_weight": str(weight_below),
            "cost": str(mixture_cost),
            "risk": str(mixture_risk),
            "oracle_cost": str(oracle_cost),
            "cost_gap_to_certified_oracle_upper": str(mixture_cost - oracle_cost),
        },
        "screen_limits": {
            "dual_multiplier_bracket_width": str(dual_distance),
            "scalar_lp_solver_tolerance": 1e-9,
            "not_a_certified_approximation_bound": True,
            "scope": "one finite instance; numerical LP solves and exact forward risk/cost evaluation; no novelty or efficacy claim",
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_lagrange_frontier_recovery_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
