"""Independently verify the randomized-calendar certificate without optimization."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, hstack, lil_matrix, vstack

from scripts.certify_switching_reversal_lp_bound import (
    ceil_decimal,
    exact_alternative_costs,
    floor_decimal,
    matrix_fraction,
)
from scripts.compare_switching_fixed_calendar_action_oracle import FixedCalendarGame
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def main() -> None:
    saved = json.loads(
        Path("outputs/switching_randomized_calendar_action_v1/results.json").read_text(
            encoding="utf-8"
        )
    )
    contract = saved["contract"]
    config = GameConfig(
        horizon=contract["horizon"],
        budget=contract["budget"],
        delay=contract["delay"],
        alpha=F(contract["alpha"]),
        query_cost=F(contract["query_cost"]),
        switch_cost=F(contract["switch_cost"]),
    )
    model = RegimeModel(**{name: F(value) for name, value in contract["model"].items()})
    branch_specs = {"no_query": (), "early_three": (1, 2, 3)}
    games = {
        name: FixedCalendarGame(config, model, schedule) for name, schedule in branch_specs.items()
    }
    names = tuple(branch_specs)
    matrices = {}
    nx, nz = {}, {}
    for name, game in games.items():
        game.build()
        e, e_rhs = game.learner.matrix()
        f, f_rhs = game.opponent.matrix()
        nx[name], nz[name] = game.learner.count, f.shape[0]
        keys = list(game.risk)
        payoff = coo_matrix(
            (
                [float(game.risk[key]) for key in keys],
                ([key[0] for key in keys], [key[1] for key in keys]),
            ),
            shape=(nx[name], game.opponent.count),
        ).tocsr()
        matrices[name] = (e, e_rhs, f, f_rhs, payoff)

    offsets, cursor = {}, 0
    for name in names:
        offsets[name] = {"x": cursor, "z": cursor + nx[name]}
        cursor += nx[name] + nz[name]
    nvars = cursor
    objective_exact = [F(0)] * nvars
    inequality_blocks, inequality_rhs = [], []
    for name in names:
        _, _, f, _, payoff = matrices[name]
        row_count = payoff.shape[1]
        pieces = []
        for other in names:
            if other == name:
                pieces.extend([payoff.T, -f.T])
            else:
                pieces.extend(
                    [csr_matrix((row_count, nx[other])), csr_matrix((row_count, nz[other]))]
                )
        inequality_blocks.append(hstack(pieces).tocsr())
        inequality_rhs.extend([0.0] * row_count)
        for i, coefficient in enumerate(exact_alternative_costs(games[name])):
            objective_exact[offsets[name]["x"] + i] = coefficient

    risk_row = lil_matrix((1, nvars), dtype=float)
    for name in names:
        _, _, _, f_rhs, _ = matrices[name]
        start = offsets[name]["z"]
        risk_row[0, start : start + nz[name]] = f_rhs.reshape(1, -1)
    inequality_blocks.append(risk_row.tocsr())
    inequality_rhs.append(float(config.alpha))
    inequality = vstack(inequality_blocks).tocsr()
    inequality_rhs = np.asarray(inequality_rhs)

    equality_blocks, equality_rhs = [], []
    for name in names:
        e, _, _, _, _ = matrices[name]
        start = offsets[name]["x"]
        for local_row in range(1, e.shape[0]):
            row = lil_matrix((1, nvars), dtype=float)
            row[0, start : start + nx[name]] = e.getrow(local_row)
            equality_blocks.append(row.tocsr())
            equality_rhs.append(0.0)
    root = lil_matrix((1, nvars), dtype=float)
    for name in names:
        root[0, offsets[name]["x"]] = 1.0
    equality_blocks.append(root.tocsr())
    equality_rhs.append(1.0)
    equality = vstack(equality_blocks).tocsr()
    equality_rhs = np.asarray(equality_rhs)

    cert = saved["lp"]
    dual_ub = [F(value) for value in cert["dual_inequality"]]
    dual_eq = [F(value) for value in cert["dual_equality"]]
    assert len(dual_ub) == inequality.shape[0]
    assert len(dual_eq) == equality.shape[0]
    assert all(value <= 0 for value in dual_ub)
    objective = [F(value) for value in objective_exact]
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
            violations.append(max(F(0), lhs - objective[column]))
        else:
            free_residual = max(free_residual, abs(lhs))
    assert free_residual == 0
    correction = sum(violations)
    assert correction == F(cert["dual_correction"])
    dual_value = sum(
        F(float(rhs)).limit_denominator(10**9) * value
        for rhs, value in zip(inequality_rhs, dual_ub, strict=True)
    ) + sum(
        F(float(rhs)).limit_denominator(10**9) * value
        for rhs, value in zip(equality_rhs, dual_eq, strict=True)
    )
    assert dual_value == F(cert["dual_value"])
    lower = dual_value - correction
    upper = F(cert["feasible_upper_bound"])
    assert lower == F(cert["certified_lower_bound"])
    assert upper == F(saved["randomized_calendar_action_policy"]["expected_cost"])
    assert lower <= upper
    assert cert["certified_lower_bound_decimal_rounded_down"] == floor_decimal(lower)
    assert cert["bracket_width_decimal_rounded_up"] == ceil_decimal(upper - lower)

    policies, branch_metrics = {}, {}
    weighted_cost, weighted_risk = F(0), F(0)
    for name, game in games.items():
        records = saved["branch_results"][name]["records"]
        behavior = {}
        for record in records:
            history = tuple(tuple(choice) for choice in record["history"])
            outcomes = tuple(tuple(outcome) for outcome in record["released"])
            choices = tuple(tuple(choice) for choice in record["choices"])
            masses = tuple(F(value) for value in record["probabilities"])
            behavior[game.information(history, outcomes)] = dict(zip(choices, masses, strict=True))

        def make_policy(branch_game, branch_behavior):
            def policy(history, outcomes):
                weights = branch_behavior[branch_game.information(history, outcomes)]  # noqa: B023 - Consumed synchronously within this loop iteration.
                return tuple(weights[choice] for choice in branch_game.choices(history))  # noqa: B023 - Consumed synchronously within this loop iteration.

            return policy  # noqa: B023 - Consumed synchronously within this loop iteration.

        policy = make_policy(game, behavior)

        p = F(saved["branch_results"][name]["probability"])
        metrics = game.expected_metrics(policy)
        risk = game.null_risk(policy)
        assert sum(metrics[:3]) == F(saved["branch_results"][name]["conditional_cost"])
        assert risk == F(saved["branch_results"][name]["conditional_risk"])
        assert metrics[3] == F(len(branch_specs[name]))
        policies[name] = policy
        branch_metrics[name] = metrics
        weighted_cost += p * sum(metrics[:3])
        weighted_risk += p * risk
    assert weighted_cost == upper
    assert weighted_risk == F(
        saved["randomized_calendar_action_policy"]["worst_causal_null_promotion_risk"]
    )
    assert weighted_risk <= config.alpha

    full_game = CausalSwitchingGame(config, model)

    def combined_policy(history, outcomes):
        choices = full_game.choices(history)
        if not history:
            weights = {choice: F(0) for choice in choices}
            for name in names:
                p = F(saved["branch_results"][name]["probability"])
                for choice, mass in zip(
                    games[name].choices(()), policies[name]((), ()), strict=True
                ):
                    weights[choice] += p * mass
            return tuple(weights[choice] for choice in choices)
        name = "early_three" if history[0][1] else "no_query"
        local = dict(
            zip(games[name].choices(history), policies[name](history, outcomes), strict=True)
        )
        return tuple(local.get(choice, F(0)) for choice in choices)

    metrics = full_game.expected_metrics(combined_policy)
    risk = full_game.null_risk(combined_policy)
    assert sum(metrics[:3]) == upper
    assert risk == weighted_risk
    assert metrics[3] == F(saved["randomized_calendar_action_policy"]["expected_queries"])
    adaptive_cost = F(saved["adaptive_oracle_feasible_upper"])
    certified_gap = lower - adaptive_cost
    assert saved["certified_gap_decimal_rounded_down"] == floor_decimal(certified_gap)

    print(
        json.dumps(
            {
                "status": "randomized_calendar_certificate_verified_without_optimizer",
                "branch_count": len(names),
                "primal_dual_width_upper": cert["bracket_width_decimal_rounded_up"],
                "expected_cost": str(upper),
                "causal_null_risk": str(risk),
                "adaptive_feasible_cost": saved["adaptive_oracle_feasible_upper"],
                "certified_gap_lower": saved["certified_gap_decimal_rounded_down"],
                "source_hash_matches": saved["source_sha256"][
                    "scripts/solve_switching_randomized_calendar_action.py"
                ]
                == hashlib.sha256(
                    Path("scripts/solve_switching_randomized_calendar_action.py").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
