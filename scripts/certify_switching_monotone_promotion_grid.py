"""Rationally certify both policy-class optima in the registered M1-M9 grid.

HiGHS supplies candidate dual vectors only. Every saved dual lower bound and
recovered-policy upper bound is independently checked using Fraction arithmetic.
The monotone LP includes the tape-cover constraints from the screening protocol.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from certify_switching_reversal_lp_bound import (
    ceil_fraction,
    exact_alternative_costs,
    matrix_fraction,
    rationalize,
)
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack
from screen_switching_monotone_promotion_grid import (
    CELLS,
    is_increasing,
    promotion_tape_probabilities,
)

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/switching_monotone_promotion_grid_cert_v1/results.json"
TOLERANCE = F(1, 10**7)


def lp_matrices(game: CausalSwitchingGame, monotone: bool):
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    risks = list(game.risk)
    from scipy.sparse import coo_matrix

    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in risks],
            ([key[0] for key in risks], [key[1] for key in risks]),
        ),
        shape=(nx, ny),
    ).tocsr()
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    rhs = [F(0)] * ny + [game.config.alpha]
    if monotone:
        mono, _ = game.promotion_tape_matrix()
        if mono.shape[0]:
            inequality = vstack(
                [inequality, hstack([mono, csr_matrix((mono.shape[0], len(f_rhs)))])]
            ).tocsr()
            rhs.extend([F(0)] * mono.shape[0])
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    return inequality, equality, rhs, list(e_rhs), nx, ny, len(f_rhs)


def exact_verify(game, policy, monotone, raw_ub, raw_eq):
    game.build()
    a, e, b, d, nx, _ny, nd = lp_matrices(game, monotone)
    y = [rationalize(value) for value in raw_ub]
    z = [rationalize(value) for value in raw_eq]
    if any(value > 0 for value in y):
        raise ArithmeticError("LP inequality dual has positive component")
    ac, ec = a.tocsc(), e.tocsc()
    correction = F(0)
    free_residual = F(0)
    costs = exact_alternative_costs(game)
    for col in range(nx + nd):
        lhs = sum(
            matrix_fraction(ac.data[i]) * y[ac.indices[i]]
            for i in range(ac.indptr[col], ac.indptr[col + 1])
        ) + sum(
            matrix_fraction(ec.data[i]) * z[ec.indices[i]]
            for i in range(ec.indptr[col], ec.indptr[col + 1])
        )
        if col < nx:
            correction += max(F(0), lhs - costs[col])
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual:
        raise ArithmeticError(f"free dual-column residual: {free_residual}")
    dual_value = sum(x * yy for x, yy in zip(b, y, strict=True)) + sum(
        matrix_fraction(rhs) * zz for rhs, zz in zip(d, z, strict=True)
    )
    lower = dual_value - ceil_fraction(correction, 10**12)
    metrics = game.expected_metrics(policy)
    upper = sum(metrics[:3])
    risk = game.null_risk(policy)
    tapes = promotion_tape_probabilities(game, policy)
    mono, witness = is_increasing(tapes)
    if monotone and not mono:
        raise ArithmeticError(f"recovered monotone-policy witness: {witness}")
    if risk > game.config.alpha:
        raise ArithmeticError(f"recovered policy violates risk: {risk}")
    if lower > upper or upper - lower > TOLERANCE:
        raise ArithmeticError(f"optimality bracket too wide: [{lower}, {upper}]")
    return {
        "certified_lower": str(lower),
        "feasible_upper": str(upper),
        "gap_upper": str(upper - lower),
        "risk_exact": str(risk),
        "iid_boundary_risk": str(game.null_risk(policy, iid_boundary=True)),
        "dual_value": str(dual_value),
        "dual_correction_upper": str(ceil_fraction(correction, 10**12)),
        "dual_inequality": [str(v) for v in y],
        "dual_equality": [str(v) for v in z],
        "promotion_event_monotone": mono,
    }


def certify_cell(cell):
    name, horizon, budget, delay, alpha, query_cost, switch_cost, p01, p10, e0, e1 = cell
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=alpha,
        query_cost=query_cost,
        switch_cost=switch_cost,
    )
    model = RegimeModel(
        transition01=p01,
        transition10=p10,
        emission0=e0,
        emission1=e1,
        prior1=F(1, 2),
    )
    classes = {}
    for label, monotone in (("unrestricted", False), ("monotone", True)):
        game = CausalSwitchingGame(config, model)
        game.build()
        a, e, b, d, nx, _ny, nd = lp_matrices(game, monotone)
        costs = exact_alternative_costs(game)
        objective = np.zeros(nx + nd)
        objective[:nx] = [float(x) for x in costs]
        result = linprog(
            objective,
            A_ub=a,
            b_ub=np.asarray([float(x) for x in b]),
            A_eq=e,
            b_eq=np.asarray(d, dtype=float),
            bounds=[(0, None)] * nx + [(None, None)] * nd,
            method="highs",
            options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
        )
        if not result.success:
            raise RuntimeError(f"{name}/{label}: {result.message}")
        policy, _ = game.recover(result.x[:nx])
        classes[label] = exact_verify(
            game, policy, monotone, result.ineqlin.marginals, result.eqlin.marginals
        )
        classes[label]["solver_objective_proposal"] = float(result.fun)
    return {"cell": name, "classes": classes}


def main(verify_only: bool = False):
    if verify_only:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        # Rebuild each primal policy from its stored sequence realization is not
        # possible from a dual-only payload; verification is performed during
        # generation and source hashes bind that operation.
        if data["status"] != "rational_primal_dual_brackets_for_monotone_promotion_grid":
            raise ValueError("unexpected certificate payload status")
        return data
    rows = [certify_cell(cell) for cell in CELLS]
    payload = {
        "status": "rational_primal_dual_brackets_for_monotone_promotion_grid",
        "protocol": "docs/switching_monotone_promotion_grid_protocol_v1.md",
        "tolerance": str(TOLERANCE),
        "cells": rows,
        "summary": {
            "cell_count": len(rows),
            "all_brackets_close": all(
                F(row["classes"][kind]["gap_upper"]) <= TOLERANCE
                for row in rows
                for kind in ("unrestricted", "monotone")
            ),
            "all_unrestricted_events_monotone": all(
                row["classes"]["unrestricted"]["promotion_event_monotone"] for row in rows
            ),
            "all_iid_equals_robust_risk": all(
                row["classes"]["unrestricted"]["iid_boundary_risk"]
                == row["classes"]["unrestricted"]["risk_exact"]
                for row in rows
            ),
        },
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "scripts/certify_switching_monotone_promotion_grid.py",
                "scripts/screen_switching_monotone_promotion_grid.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_monotone_promotion_grid_protocol_v1.md",
            )
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return payload


if __name__ == "__main__":
    main()
