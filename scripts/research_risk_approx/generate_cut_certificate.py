"""Generate exact certificates for registered restricted-master diagnostic."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from cut_certificate_helpers import exact_costs, exact_payoff, game_for, lower_bound, null_cut
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, vstack

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(horizon):
    target = OUT / f"causal_cut_certificate_t{horizon}_v1.json"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    game = game_for(horizon)
    emat, erhs = game.learner.matrix()
    fmat, frhs = game.opponent.matrix()
    exact = exact_costs(game)
    if max(abs(float(x) - game.cost.get(i, 0.0)) for i, x in enumerate(exact)) > 1e-10:
        raise ValueError("Exact versus numerical cost mismatch")
    payoff = exact_payoff(game)
    keys = list(payoff)
    a = coo_matrix(
        (
            [float(payoff[key]) for key in keys],
            ([key[0] for key in keys], [key[1] for key in keys]),
        ),
        shape=(game.learner.count, game.opponent.count),
    ).tocsr()
    costs = np.array([float(v) for v in exact])
    options = {
        "time_limit": 60.0,
        "primal_feasibility_tolerance": 1e-9,
        "dual_feasibility_tolerance": 1e-9,
    }
    cuts = []
    selected = []
    best = None
    trace = []
    signatures = set()
    status = "iteration_limit"
    always = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    safe_cost = sum(game.expected_metrics(always)[:3])
    for iteration in range(65):
        master = linprog(
            costs,
            A_ub=vstack([csr_matrix([list(map(float, cut))]) for cut in cuts]).tocsr()
            if cuts
            else None,
            b_ub=np.full(len(cuts), float(game.config.alpha)) if cuts else None,
            A_eq=emat,
            b_eq=erhs,
            bounds=(0, None),
            method="highs",
            options=options,
        )
        if not master.success:
            raise RuntimeError("Master failed: " + master.message)
        response = linprog(
            -(a.T @ master.x),
            A_eq=fmat,
            b_eq=frhs,
            bounds=(0, None),
            method="highs",
            options=options,
        )
        if not response.success:
            raise RuntimeError("Response failed: " + response.message)
        y = np.rint(response.x)
        if np.max(np.abs(response.x - y)) > 1e-8:
            raise ValueError("Non-integral response")
        seq = [int(i) for i in np.flatnonzero(y)]
        cut = null_cut(game, payoff, seq)
        response_risk = float(np.dot(np.array([float(v) for v in cut]), master.x))
        policy, records = game.recover(master.x)
        risk = game.null_risk(policy)
        if abs(float(risk) - response_risk) > 1e-7:
            raise ValueError("Risk cross-check failed")
        raw_cost = sum(game.expected_metrics(policy)[:3])
        activation = min(F(1), game.config.alpha / risk) if risk else F(1)
        upper = activation * raw_cost + (1 - activation) * safe_cost
        if best is None or upper < best[0]:
            best = (upper, risk, activation, raw_cost, records, iteration)
        trace.append(
            {
                "iteration": iteration,
                "master_numeric": float(master.fun),
                "risk_numeric": response_risk,
                "safe_cost": str(upper),
            }
        )
        if response_risk <= float(game.config.alpha) + 1e-9:
            status = "numerical_master_converged"
            break
        signature = tuple(seq)
        if signature in signatures:
            status = "duplicate_response"
            break
        if iteration == 64:
            break
        signatures.add(signature)
        selected.append(seq)
        cuts.append(cut)
    dual_eq = [F(float(v)).limit_denominator(10**7) for v in master.eqlin.marginals]
    dual_ub = (
        [F(float(v)).limit_denominator(10**7) for v in master.ineqlin.marginals] if cuts else []
    )
    bound, dual, correction = lower_bound(game, exact, cuts, dual_eq, dual_ub)
    upper, risk, activation, raw_cost, records, best_iteration = best
    if bound > upper or activation * risk > game.config.alpha:
        raise ValueError("Computed certificate inconsistent")
    signed = {
        "horizon": horizon,
        "null_responses": selected,
        "dual_eq": [str(x) for x in dual_eq],
        "dual_ub": [str(x) for x in dual_ub],
        "dual_value": str(dual),
        "correction": str(correction),
        "lower": str(bound),
        "upper": str(upper),
        "gap": str(upper - bound),
        "activation": str(activation),
        "raw_risk": str(risk),
        "raw_cost": str(raw_cost),
        "best_iteration": best_iteration,
        "behavior": records,
    }
    canonical = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "certificate": signed,
        "certificate_sha256": hashlib.sha256(canonical).hexdigest(),
        "status": status,
        "iterations": trace,
        "source_sha256": sha(Path(__file__)),
        "helper_sha256": sha(ROOT / "scripts/research_risk_approx/cut_certificate_helpers.py"),
        "protocol_sha256": sha(OUT / "CAUSAL_CUT_CERT_PROTOCOL_V1.md"),
    }
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "horizon": horizon,
                "status": status,
                "cuts": len(cuts),
                "lower": float(bound),
                "upper": float(upper),
                "gap": float(upper - bound),
                "seconds": time.time(),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    for horizon in (6, 7):
        main(horizon)
