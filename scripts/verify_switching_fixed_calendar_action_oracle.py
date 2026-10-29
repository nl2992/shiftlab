"""Verify saved fixed-calendar dual certificates and recovered policies without LP solves."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts.certify_switching_reversal_lp_bound import exact_alternative_costs, matrix_fraction
from scripts.compare_switching_fixed_calendar_action_oracle import FixedCalendarGame
from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def main() -> None:
    result_path = Path("outputs/switching_fixed_calendar_action_oracle_v1/results.json")
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    model = RegimeModel(**{name: F(value) for name, value in saved["model"].items()})
    alpha, query_cost, switch_cost = (
        F(saved["alpha"]),
        F(saved["query_cost"]),
        F(saved["switch_cost"]),
    )
    verified = 0
    for cell in saved["cells"]:
        config = GameConfig(
            horizon=cell["horizon"],
            budget=cell["budget"],
            delay=cell["delay"],
            alpha=alpha,
            query_cost=query_cost,
            switch_cost=switch_cost,
        )
        for row in cell["all_calendars"]:
            game = FixedCalendarGame(config, model, tuple(row["schedule"]))
            game.build()
            e_matrix, e_rhs = game.learner.matrix()
            f_matrix, f_rhs = game.opponent.matrix()
            nx, ny = game.learner.count, game.opponent.count
            keys = list(game.risk)
            payoff = coo_matrix(
                (
                    [float(game.risk[key]) for key in keys],
                    ([key[0] for key in keys], [key[1] for key in keys]),
                ),
                shape=(nx, ny),
            ).tocsr()
            inequality = vstack(
                [
                    hstack([payoff.T, -f_matrix.T]),
                    hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
                ]
            ).tocsr()
            equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
            exact_cost = exact_alternative_costs(game)
            cert = row["certificate"]
            dual_ub = [F(value) for value in cert["dual_inequality"]]
            dual_eq = [F(value) for value in cert["dual_equality"]]
            assert len(dual_ub) == inequality.shape[0]
            assert len(dual_eq) == equality.shape[0]
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
                if column < nx:
                    violations.append(max(F(0), lhs - exact_cost[column]))
                else:
                    free_residual = max(free_residual, abs(lhs))
            assert free_residual == 0
            correction = sum(violations)
            assert correction == F(cert["rounding_correction"])
            rhs_exact = [F(0)] * ny + [alpha]
            dual_value = sum(a * b for a, b in zip(rhs_exact, dual_ub, strict=True))
            dual_value += sum(
                matrix_fraction(rhs) * multiplier
                for rhs, multiplier in zip(e_rhs, dual_eq, strict=True)
            )
            assert dual_value == F(cert["dual_value"])
            lower = dual_value - correction
            assert lower == F(row["certified_optimum_lower_bound"])

            behavior = {}
            for record in row["decision_records"]:
                history = tuple(tuple(choice) for choice in record["history"])
                outcomes = tuple(tuple(outcome) for outcome in record["released"])
                choices = tuple(tuple(choice) for choice in record["choices"])
                probabilities = tuple(F(value) for value in record["probabilities"])
                behavior[game.information(history, outcomes)] = dict(zip(choices, probabilities))

            def policy(history, outcomes):
                weights = behavior[game.information(history, outcomes)]  # noqa: B023 - Consumed synchronously within this loop iteration.
                return tuple(weights[choice] for choice in game.choices(history))  # noqa: B023 - Consumed synchronously within this loop iteration.

            metrics = game.expected_metrics(policy)
            risk = game.null_risk(policy)
            assert sum(metrics[:3]) == F(row["raw_policy_cost"])
            assert risk == F(row["raw_policy_risk"])
            assert risk <= alpha
            assert metrics[3] == F(len(row["schedule"]))
            assert sum(metrics[:3]) == F(row["certified_policy_upper_bound"])
            assert lower <= sum(metrics[:3])
            verified += 1

    print(
        json.dumps(
            {
                "status": "saved_fixed_calendar_certificates_verified_without_optimizer",
                "calendars_verified": verified,
                "cells": len(saved["cells"]),
                "source_hash_matches": saved["source_sha256"][
                    "scripts/compare_switching_fixed_calendar_action_oracle.py"
                ]
                == hashlib.sha256(
                    Path("scripts/compare_switching_fixed_calendar_action_oracle.py").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
