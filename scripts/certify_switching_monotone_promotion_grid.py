"""Rationally certify both policy-class optima in the registered M1-M9 grid.

HiGHS supplies candidate dual vectors only. Every saved dual lower bound and
recovered-policy upper bound is independently checked using Fraction arithmetic.
The monotone LP includes the tape-cover constraints from the screening protocol.
"""

from __future__ import annotations

import argparse
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
    y = [as_fraction(value) for value in raw_ub]
    z = [as_fraction(value) for value in raw_eq]
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
        "policy_records": policy_records(game, policy),
    }


def as_fraction(value):
    if isinstance(value, F):
        return value
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return F(value)
    return rationalize(value)


def policy_records(game, policy):
    records = []
    for (history, released), (_, _children, choices) in game.learner.infos.items():
        probabilities = policy(history, released)
        records.append(
            {
                "history": [list(choice) for choice in history],
                "released": [list(item) for item in released],
                "choices": [list(choice) for choice in choices],
                "probabilities": [str(value) for value in probabilities],
            }
        )
    return records


def policy_from_records(game, records):
    behavior = {}
    for record in records:
        history = tuple(tuple(choice) for choice in record["history"])
        released = tuple(tuple(item) for item in record["released"])
        choices = tuple(tuple(choice) for choice in record["choices"])
        probabilities = tuple(F(value) for value in record["probabilities"])
        if choices != game.choices(history) or len(choices) != len(probabilities):
            raise ArithmeticError("saved policy action set is inconsistent with the game")
        if any(value < 0 for value in probabilities) or sum(probabilities) != 1:
            raise ArithmeticError("saved policy probabilities are not a distribution")
        key = (history, released)
        if key not in game.learner.infos or game.learner.infos[key][2] != choices:
            raise ArithmeticError("saved policy information set is not in the game")
        if key in behavior:
            raise ArithmeticError("duplicate saved policy information set")
        behavior[key] = probabilities
    if len(behavior) != len(game.learner.infos):
        raise ArithmeticError("saved policy does not cover every learner information set")

    def policy(history, outcomes):
        return behavior[game.information(history, outcomes)]

    return policy


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
        policy, records = game.recover(result.x[:nx])
        classes[label] = exact_verify(
            game, policy, monotone, result.ineqlin.marginals, result.eqlin.marginals
        )
        classes[label]["policy_records"] = records
        classes[label]["solver_objective_proposal"] = float(result.fun)
    return {"cell": name, "classes": classes}


def main(verify_only: bool = False):
    if verify_only:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if data["status"] != "rational_primal_dual_brackets_for_monotone_promotion_grid":
            raise ValueError("unexpected certificate payload status")
        for relative_path, expected_hash in data["source_sha256"].items():
            actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise ValueError(f"source hash mismatch: {relative_path}")
        if len(data["cells"]) != len(CELLS):
            raise ValueError("certificate has the wrong number of registered cells")
        for cell, row in zip(CELLS, data["cells"], strict=True):
            name, horizon, budget, delay, alpha, query_cost, switch_cost, p01, p10, e0, e1 = cell
            if row["cell"] != name:
                raise ValueError("certificate cells are out of registered order")
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
            for label, monotone in (("unrestricted", False), ("monotone", True)):
                saved = row["classes"][label]
                game = CausalSwitchingGame(config, model)
                game.build()
                policy = policy_from_records(game, saved["policy_records"])
                checked = exact_verify(
                    game,
                    policy,
                    monotone,
                    saved["dual_inequality"],
                    saved["dual_equality"],
                )
                for key, value in checked.items():
                    if saved[key] != value:
                        raise ValueError(f"certificate mismatch at {name}/{label}/{key}")
        print(json.dumps(data["summary"], indent=2))
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify", action="store_true", help="verify saved certificates without optimization"
    )
    main(verify_only=parser.parse_args().verify)
