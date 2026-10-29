"""Jointly optimize a two-calendar lottery and full branch action policies."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts.certify_switching_reversal_lp_bound import (
    ceil_decimal,
    exact_alternative_costs,
    floor_decimal,
    matrix_fraction,
)
from scripts.compare_switching_fixed_calendar_action_oracle import FixedCalendarGame
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def branch_matrices(game: CausalSwitchingGame):
    game.build()
    learner_eq, learner_rhs = game.learner.matrix()
    opponent_eq, opponent_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    keys = list(game.risk)
    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in keys],
            ([key[0] for key in keys], [key[1] for key in keys]),
        ),
        shape=(nx, ny),
    ).tocsr()
    return learner_eq, learner_rhs, opponent_eq, opponent_rhs, payoff, nx, ny


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
    branch_specs = {"no_query": (), "early_three": (1, 2, 3)}
    games = {
        name: FixedCalendarGame(config, model, schedule) for name, schedule in branch_specs.items()
    }
    matrices = {name: branch_matrices(game) for name, game in games.items()}
    names = tuple(branch_specs)
    nx = {name: matrices[name][5] for name in names}
    nz = {name: matrices[name][2].shape[0] for name in names}
    offsets = {}
    cursor = 0
    for name in names:
        offsets[name] = {"x": cursor, "z": cursor + nx[name]}
        cursor += nx[name] + nz[name]
    nvars = cursor

    objective_exact = [F(0)] * nvars
    for name in names:
        costs = exact_alternative_costs(games[name])
        for i, value in enumerate(costs):
            objective_exact[offsets[name]["x"] + i] = value
    objective = np.array([float(value) for value in objective_exact])

    inequality_blocks = []
    inequality_rhs = []
    for name in names:
        _, _, _, _opponent_rhs, payoff, _branch_nx, branch_ny = matrices[name]
        row = [csr_matrix((branch_ny, nvars))]
        row[0] = payoff.T
        # Construct a full-width sparse block row with the branch's x and z columns.
        pieces = []
        for other in names:
            if other == name:
                pieces.extend([payoff.T, -matrices[name][2].T])
            else:
                pieces.extend(
                    [
                        csr_matrix((branch_ny, nx[other])),
                        csr_matrix((branch_ny, nz[other])),
                    ]
                )
        inequality_blocks.append(hstack(pieces).tocsr())
        inequality_rhs.extend([0.0] * branch_ny)

    risk_row_full = csr_matrix((1, nvars))
    for name in names:
        f_rhs = matrices[name][3]
        start = offsets[name]["z"]
        risk_row_full[0, start : start + nz[name]] = f_rhs.reshape(1, -1)
    inequality_blocks.append(risk_row_full.tocsr())
    inequality_rhs.append(float(config.alpha))
    inequality = vstack(inequality_blocks).tocsr()
    inequality_rhs = np.asarray(inequality_rhs)

    equality_blocks = []
    equality_rhs = []
    for name in names:
        learner_eq = matrices[name][0]
        start = offsets[name]["x"]
        for local_row in range(1, learner_eq.shape[0]):
            full_row = csr_matrix((1, nvars))
            full_row[0, start : start + nx[name]] = learner_eq.getrow(local_row)
            equality_blocks.append(full_row)
            equality_rhs.append(0.0)
    root_row = csr_matrix((1, nvars))
    for name in names:
        start = offsets[name]["x"]
        root_row[0, start] = 1.0
    equality_blocks.append(root_row)
    equality_rhs.append(1.0)
    equality = vstack(equality_blocks).tocsr()
    equality_rhs = np.asarray(equality_rhs)

    bounds = []
    for name in names:
        bounds.extend([(0.0, None)] * nx[name])
        bounds.extend([(None, None)] * nz[name])
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=inequality_rhs,
        A_eq=equality,
        b_eq=equality_rhs,
        bounds=bounds,
        method="highs",
        options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
    )
    if not result.success:
        raise RuntimeError(result.message)

    branch_results = {}
    branch_policies = {}
    total_cost = F(0)
    total_risk = F(0)
    total_queries = F(0)
    for name in names:
        x_start = offsets[name]["x"]
        realization = [
            F(float(value)).limit_denominator(10**9)
            for value in result.x[x_start : x_start + nx[name]]
        ]
        probability = realization[0]
        if not probability:
            raise RuntimeError(f"branch {name} received zero mass; recovery omitted")
        normalized = [value / probability for value in realization]
        game = games[name]
        policy, records = game.recover([float(value) for value in normalized])
        branch_policies[name] = policy
        metrics = game.expected_metrics(policy)
        risk = game.null_risk(policy)
        assert sum(metrics[:3]) * probability == sum(
            exact_alternative_costs(game)[i] * realization[i] for i in range(nx[name])
        )
        total_cost += probability * sum(metrics[:3])
        total_risk += probability * risk
        total_queries += probability * metrics[3]
        branch_results[name] = {
            "schedule": list(branch_specs[name]),
            "probability": str(probability),
            "conditional_cost": str(sum(metrics[:3])),
            "conditional_risk": str(risk),
            "weighted_risk_contribution": str(probability * risk),
            "conditional_metrics": [str(value) for value in metrics],
            "records": records,
        }
    assert sum(F(branch["probability"]) for branch in branch_results.values()) == 1
    assert total_risk <= config.alpha
    assert max(len(schedule) for schedule in branch_specs.values()) <= config.budget

    full_game = CausalSwitchingGame(config, model)

    def combined_policy(history, outcomes):
        full_choices = full_game.choices(history)
        if not history:
            weights = {choice: F(0) for choice in full_choices}
            for name in names:
                probability = F(branch_results[name]["probability"])
                branch_choices = games[name].choices(())
                for choice, conditional in zip(
                    branch_choices, branch_policies[name]((), ()), strict=True
                ):
                    weights[choice] += probability * conditional
            return tuple(weights[choice] for choice in full_choices)
        name = "early_three" if history[0][1] else "no_query"
        branch_choices = games[name].choices(history)
        branch_weights = dict(
            zip(branch_choices, branch_policies[name](history, outcomes), strict=True)
        )
        return tuple(branch_weights.get(choice, F(0)) for choice in full_choices)

    combined_metrics = full_game.expected_metrics(combined_policy)
    combined_risk = full_game.null_risk(combined_policy)
    assert sum(combined_metrics[:3]) == total_cost
    assert combined_metrics[3] == total_queries
    assert combined_risk == total_risk

    dual_ub = [F(float(value)).limit_denominator(10**7) for value in result.ineqlin.marginals]
    dual_eq = [F(float(value)).limit_denominator(10**7) for value in result.eqlin.marginals]
    assert all(value <= 0 for value in dual_ub)
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    violations = []
    free_residual = F(0)
    for column in range(inequality.shape[1]):
        lhs = sum(
            matrix_fraction(a_csc.data[i]) * dual_ub[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            matrix_fraction(e_csc.data[i]) * dual_eq[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        if any(offsets[name]["x"] <= column < offsets[name]["z"] for name in names):
            violations.append(max(F(0), lhs - objective_exact[column]))
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual:
        raise AssertionError(f"free dual column residual: {free_residual}")
    correction = sum(violations)
    dual_value = sum(
        F(float(rhs)).limit_denominator(10**9) * value
        for rhs, value in zip(inequality_rhs, dual_ub, strict=True)
    ) + sum(
        F(float(rhs)).limit_denominator(10**9) * value
        for rhs, value in zip(equality_rhs, dual_eq, strict=True)
    )
    certified_lower = dual_value - correction
    assert certified_lower <= total_cost

    oracle_game = CausalSwitchingGame(config, model)
    oracle_report, _, _ = oracle_game.solve()
    sources = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/solve_switching_randomized_calendar_action.py",
    )
    output = {
        "status": "joint_randomized_calendar_action_sequence_form_with_exact_dual_check",
        "contract": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "model": {name: str(getattr(model, name)) for name in model.__dataclass_fields__},
        },
        "branch_results": branch_results,
        "randomized_calendar_action_policy": {
            "expected_cost": str(total_cost),
            "worst_causal_null_promotion_risk": str(total_risk),
            "expected_queries": str(total_queries),
            "pathwise_query_cap": config.budget,
            "independent_full_game_cost_check": str(sum(combined_metrics[:3])),
            "independent_full_game_risk_check": str(combined_risk),
        },
        "lp": {
            "solver_objective": result.fun,
            "variables": nvars,
            "inequalities": inequality.shape[0],
            "equalities": equality.shape[0],
            "dual_value": str(dual_value),
            "dual_correction": str(correction),
            "certified_lower_bound": str(certified_lower),
            "feasible_upper_bound": str(total_cost),
            "bracket_width": str(total_cost - certified_lower),
            "bracket_width_decimal_rounded_up": ceil_decimal(total_cost - certified_lower),
            "certified_lower_bound_decimal_rounded_down": floor_decimal(certified_lower),
            "free_column_residual": str(free_residual),
            "dual_inequality": [str(value) for value in dual_ub],
            "dual_equality": [str(value) for value in dual_eq],
        },
        "adaptive_oracle_feasible_upper": oracle_report["calibrated_total_cost"],
        "certified_gap_over_adaptive_feasible_policy": str(
            certified_lower - F(oracle_report["calibrated_total_cost"])
        ),
        "certified_gap_decimal_rounded_down": floor_decimal(
            certified_lower - F(oracle_report["calibrated_total_cost"])
        ),
        "interpretation": (
            "Exact value certificate for a two-calendar lottery with full action control. The "
            "class is still narrower than arbitrary randomized calendars or adaptive sensing; "
            "this is not a novel algorithm or efficacy result."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sources
        },
    }
    target = Path("outputs/switching_randomized_calendar_action_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "randomized_calendar_action_policy": output["randomized_calendar_action_policy"],
                "certificate": {
                    key: output["lp"][key]
                    for key in (
                        "certified_lower_bound_decimal_rounded_down",
                        "feasible_upper_bound",
                        "bracket_width_decimal_rounded_up",
                        "free_column_residual",
                    )
                },
                "adaptive_oracle_feasible_upper": output["adaptive_oracle_feasible_upper"],
                "certified_gap_lower": output["certified_gap_decimal_rounded_down"],
                "branch_probabilities": {
                    name: branch["probability"] for name, branch in branch_results.items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
