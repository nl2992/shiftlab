"""Compare fixed query calendars with unrestricted adaptive causal-game policies."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts.certify_switching_reversal_lp_bound import (
    exact_alternative_costs,
    floor_decimal,
    matrix_fraction,
)
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class FixedCalendarGame(CausalSwitchingGame):
    def __init__(self, config: GameConfig, model: RegimeModel, schedule: tuple[int, ...]):
        self.schedule = frozenset(schedule)
        super().__init__(config, model)

    def choices(self, history):
        query = int(len(history) + 1 in self.schedule)
        return ((0, query), (1, query))


def schedules(horizon: int, budget: int, delay: int):
    available = tuple(range(1, horizon - delay + 1))
    return tuple(
        schedule
        for count in range(min(budget, len(available)) + 1)
        for schedule in combinations(available, count)
    )


def certify_game(game: CausalSwitchingGame) -> dict:
    """Build an exact-cost LP and verify a rationalized dual lower bound."""
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    risk_indices = list(game.risk)
    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in risk_indices],
            ([key[0] for key in risk_indices], [key[1] for key in risk_indices]),
        ),
        shape=(nx, ny),
    ).tocsr()
    objective = np.zeros(nx + len(f_rhs))
    exact_cost = exact_alternative_costs(game)
    objective[:nx] = np.array([float(value) for value in exact_cost])
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    upper_rhs = np.r_[np.zeros(ny), float(game.config.alpha)]
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=upper_rhs,
        A_eq=equality,
        b_eq=e_rhs,
        bounds=[(0, None)] * nx + [(None, None)] * len(f_rhs),
        method="highs",
        options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
    )
    if not result.success:
        raise RuntimeError(result.message)
    dual_ub = [F(float(value)).limit_denominator(10**7) for value in result.ineqlin.marginals]
    dual_eq = [F(float(value)).limit_denominator(10**7) for value in result.eqlin.marginals]
    if any(value > 0 for value in dual_ub):
        raise AssertionError("positive inequality dual multiplier")
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    violations = [F(0)] * nx
    free_residual = F(0)
    for column in range(nx + len(f_rhs)):
        lhs = sum(
            matrix_fraction(a_csc.data[i]) * dual_ub[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            matrix_fraction(e_csc.data[i]) * dual_eq[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        if column < nx:
            violations[column] = max(F(0), lhs - exact_cost[column])
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual:
        raise AssertionError(f"free dual column residual {free_residual}")
    rhs_exact = [F(0)] * ny + [game.config.alpha]
    dual_value = sum(a * b for a, b in zip(rhs_exact, dual_ub, strict=True))
    dual_value += sum(
        matrix_fraction(rhs) * multiplier for rhs, multiplier in zip(e_rhs, dual_eq, strict=True)
    )
    correction = sum(violations)
    lower = dual_value - correction
    return {
        "lower_bound": str(lower),
        "dual_value": str(dual_value),
        "rounding_correction": str(correction),
        "free_column_residual": str(free_residual),
        "dual_signs_valid": all(value <= 0 for value in dual_ub),
        "all_column_constraints_valid_after_correction": all(
            violation <= correction for violation in violations
        ),
        "learner_sequences": nx,
        "opponent_sequences": ny,
        "solver_objective": float(result.fun),
        "lower_decimal_rounded_down": floor_decimal(lower),
        "dual_inequality": [str(value) for value in dual_ub],
        "dual_equality": [str(value) for value in dual_eq],
    }


def solve_calendar(config: GameConfig, model: RegimeModel, schedule: tuple[int, ...]) -> dict:
    game = FixedCalendarGame(config, model, schedule)
    report, raw_policy, records = game.solve()
    raw_metrics = game.expected_metrics(raw_policy)
    raw_risk = game.null_risk(raw_policy)

    def safe_policy(history, outcomes):
        target = (0, int(len(history) + 1 in schedule))
        return tuple(F(choice == target) for choice in game.choices(history))

    safe_metrics = game.expected_metrics(safe_policy)
    assert game.null_risk(safe_policy) == 0

    activation = min(F(1), config.alpha / raw_risk) if raw_risk else F(1)
    mixed_metrics = tuple(
        activation * value + (1 - activation) * safe
        for value, safe in zip(raw_metrics, safe_metrics, strict=True)
    )
    risk = activation * raw_risk
    assert risk <= config.alpha
    assert mixed_metrics[3] == len(schedule)
    certificate = certify_game(game)
    assert F(certificate["lower_bound"]) <= sum(raw_metrics[:3])

    return {
        "schedule": list(schedule),
        "solver_objective": report["solver_objective"],
        "raw_policy_cost": str(sum(raw_metrics[:3])),
        "raw_policy_risk": str(raw_risk),
        "safe_mixture_probability": str(activation),
        "calibrated_cost": str(sum(mixed_metrics[:3])),
        "calibrated_risk": str(risk),
        "certified_optimum_lower_bound": certificate["lower_bound"],
        "certified_policy_upper_bound": str(sum(raw_metrics[:3])),
        "certificate_bracket_width": str(sum(raw_metrics[:3]) - F(certificate["lower_bound"])),
        "certificate": certificate,
        "expected_queries": str(mixed_metrics[3]),
        "expected_switches": str(mixed_metrics[4]),
        "nodes": report["nodes"],
        "decision_records": [
            {
                "history": record["history"],
                "released": record["released"],
                "choices": record["choices"],
                "probabilities": record["probabilities"],
            }
            for record in records
            if any(F(value) for value in record["probabilities"])
        ],
    }


def main() -> None:
    alpha, query_cost, switch_cost = F(1, 10), F(1, 100), F(1, 10)
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    cells = []
    for horizon, budget in ((4, 2), (5, 2), (6, 3)):
        config = GameConfig(
            horizon=horizon,
            budget=budget,
            delay=1,
            alpha=alpha,
            query_cost=query_cost,
            switch_cost=switch_cost,
        )
        calendar_results = [
            solve_calendar(config, model, schedule)
            for schedule in schedules(horizon, budget, config.delay)
        ]
        best_calendar = min(calendar_results, key=lambda result: F(result["calibrated_cost"]))
        minimum_certified_calendar_lower = min(
            F(result["certified_optimum_lower_bound"]) for result in calendar_results
        )
        oracle_game = CausalSwitchingGame(config, model)
        oracle_report, _, _ = oracle_game.solve()
        cells.append(
            {
                "horizon": horizon,
                "budget": budget,
                "delay": config.delay,
                "calendar_count": len(calendar_results),
                "best_recovered_calendar_policy": best_calendar,
                "unrestricted_adaptive_recovered_policy": {
                    "cost": oracle_report["calibrated_total_cost"],
                    "risk": oracle_report["calibrated_risk_bound"],
                    "raw_risk": oracle_report["raw_causal_null_risk"],
                    "expected_metrics": oracle_report["calibrated_metrics"],
                    "solver_objective": oracle_report["solver_objective"],
                    "nodes": oracle_report["nodes"],
                },
                "recovered_policy_cost_gap_calendar_minus_adaptive": str(
                    F(best_calendar["calibrated_cost"]) - F(oracle_report["calibrated_total_cost"])
                ),
                "minimum_fixed_calendar_certified_lower_bound": str(
                    minimum_certified_calendar_lower
                ),
                "adaptive_feasible_policy_cost": oracle_report["calibrated_total_cost"],
                "certified_class_separation_lower_bound": str(
                    minimum_certified_calendar_lower - F(oracle_report["calibrated_total_cost"])
                ),
                "all_calendars": calendar_results,
            }
        )

    source_files = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/compare_switching_fixed_calendar_action_oracle.py",
    )
    output = {
        "status": "registered_growing_horizon_fixed_calendar_vs_adaptive_oracle_screen",
        "model": {name: str(getattr(model, name)) for name in model.__dataclass_fields__},
        "alpha": str(alpha),
        "query_cost": str(query_cost),
        "switch_cost": str(switch_cost),
        "cells": cells,
        "interpretation": (
            "Each deterministic calendar receives a numerically optimized full action policy; "
            "recovered policies and null risks are evaluated exactly. The minimum recovered "
            "calendar is not an exact optimum certificate, and this baseline does not include "
            "adaptive sequential acquisition. No novelty or efficacy claim is made."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in source_files
        },
    }
    target = Path("outputs/switching_fixed_calendar_action_oracle_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            [
                {
                    "T": cell["horizon"],
                    "B": cell["budget"],
                    "calendar_count": cell["calendar_count"],
                    "best_schedule": cell["best_recovered_calendar_policy"]["schedule"],
                    "calendar_cost": cell["best_recovered_calendar_policy"]["calibrated_cost"],
                    "adaptive_cost": cell["unrestricted_adaptive_recovered_policy"]["cost"],
                    "gap": cell["recovered_policy_cost_gap_calendar_minus_adaptive"],
                }
                for cell in cells
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
