"""Verify the saved reversal-cell LP certificate without running an optimizer."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts.certify_switching_reversal_lp_bound import (
    exact_alternative_costs,
    fixed_graph_policy,
    matrix_fraction,
)
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def main() -> None:
    path = Path("outputs/switching_reversal_lp_certificate_v1/results.json")
    saved = json.loads(path.read_text(encoding="utf-8"))
    cert = saved["certificate"]
    signed = {
        "dual_inequality": cert["dual_inequality"],
        "dual_equality": cert["dual_equality"],
        "dual_value": cert["dual_value"],
        "rounding_correction_upper": cert["rounding_correction_upper"],
        "certified_lower_bound_decimal_rounded_down": cert[
            "certified_lower_bound_decimal_rounded_down"
        ],
        "feasible_policy_upper_bound": cert["feasible_policy_upper_bound"],
        "free_column_residual": cert["free_column_residual"],
    }
    encoded = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == saved["certificate_sha256"]

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
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    indices = list(game.risk)
    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in indices],
            ([key[0] for key in indices], [key[1] for key in indices]),
        ),
        shape=(nx, game.opponent.count),
    ).tocsr()
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    exact_cost = exact_alternative_costs(game)
    dual_ub = [F(value) for value in cert["dual_inequality"]]
    dual_eq = [F(value) for value in cert["dual_equality"]]
    assert len(dual_ub) == inequality.shape[0]
    assert len(dual_eq) == equality.shape[0]
    assert all(value <= 0 for value in dual_ub)

    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    residuals = []
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
            residuals.append(max(F(0), lhs - exact_cost[column]))
        else:
            free_residual = max(free_residual, abs(lhs))
    assert free_residual == 0
    assert cert["free_column_residual"] == "0"

    exact_rhs = [F(0)] * ny + [config.alpha]
    dual_value = sum(a * b for a, b in zip(exact_rhs, dual_ub, strict=True))
    dual_value += sum(
        matrix_fraction(rhs) * value for rhs, value in zip(e_rhs, dual_eq, strict=True)
    )
    correction = sum(residuals)
    correction_upper = F(cert["rounding_correction_upper"])
    lower_decimal = F(cert["certified_lower_bound_decimal_rounded_down"])
    assert correction <= correction_upper
    assert dual_value == F(cert["dual_value"])
    assert lower_decimal <= dual_value - correction_upper

    policy = fixed_graph_policy(game, F(2, 5))
    metrics = game.expected_metrics(policy)
    upper = sum(metrics[:3])
    assert game.null_risk(policy) == config.alpha
    assert upper == F(cert["feasible_policy_upper_bound"])
    assert lower_decimal <= upper
    print(
        json.dumps(
            {
                "status": "saved_certificate_verified_exactly_without_optimizer",
                "lower_bound": str(lower_decimal),
                "upper_bound": str(upper),
                "gap_upper": str(upper - lower_decimal),
                "dual_constraint_residual_upper": cert["rounding_correction_upper"],
                "certificate_sha256": saved["certificate_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
