"""Generate a rational certificate for the original T=7 decomposed LP."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from cut_certificate_helpers import exact_costs, exact_payoff, game_for
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"
TARGET = OUT / "full_t7_certificate_v1.json"


def matrix_for(game):
    emat, erhs = game.learner.matrix()
    fmat, frhs = game.opponent.matrix()
    payoff = exact_payoff(game)
    keys = list(payoff)
    a = coo_matrix(
        ([float(payoff[k]) for k in keys], ([k[0] for k in keys], [k[1] for k in keys])),
        shape=(game.learner.count, game.opponent.count),
    ).tocsr()
    n_x = game.learner.count
    inequality = vstack(
        [hstack([a.T, -fmat.T]), hstack([csr_matrix((1, n_x)), csr_matrix(frhs.reshape(1, -1))])]
    ).tocsr()
    equality = hstack([emat, csr_matrix((len(erhs), len(frhs)))]).tocsr()
    return inequality, equality, erhs, frhs


def exact_residual(game, exact, inequality, equality, dual_ub, dual_eq, frhs, erhs):
    if any(v > 0 for v in dual_ub):
        raise ValueError("Wrong inequality dual sign")
    n_x = game.learner.count
    a, e = inequality.tocsc(), equality.tocsc()
    correction = F(0)
    for col in range(inequality.shape[1]):
        lhs = sum(
            (
                F(float(a.data[i])) * dual_ub[a.indices[i]]
                for i in range(a.indptr[col], a.indptr[col + 1])
            ),
            F(0),
        )
        lhs += sum(
            (
                F(float(e.data[i])) * dual_eq[e.indices[i]]
                for i in range(e.indptr[col], e.indptr[col + 1])
            ),
            F(0),
        )
        if col < n_x:
            correction += max(F(0), lhs - exact[col])
        elif lhs:
            raise ValueError(f"Free-column residual at {col}: {lhs}")
    dual = game.config.alpha * dual_ub[-1] + sum(
        (F(int(v)) * m for v, m in zip(erhs, dual_eq, strict=True)), F(0)
    )
    return dual - correction, dual, correction


def opponent_flow(game, raw):
    flow = [None] * game.opponent.count
    flow[0] = F(1)
    for parent, children, _ in game.opponent.infos.values():
        if flow[parent] is None:
            raise ValueError("Opponent parent not initialized")
        masses = [F(float(max(0.0, -raw[child]))).limit_denominator(10**7) for child in children]
        if not sum(masses):
            masses[0] = F(1)
        total = sum(masses)
        for child, mass in zip(children, masses, strict=True):
            flow[child] = flow[parent] * mass / total
    if any(v is None for v in flow):
        raise ValueError("Missing opponent sequence")
    return flow


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    game = game_for(7)
    exact = exact_costs(game)
    inequality, equality, erhs, frhs = matrix_for(game)
    objective = np.r_[np.array([float(v) for v in exact]), np.zeros(len(frhs))]
    rhs = np.r_[np.zeros(game.opponent.count), float(game.config.alpha)]
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=rhs,
        A_eq=equality,
        b_eq=erhs,
        bounds=[(0, None)] * game.learner.count + [(None, None)] * len(frhs),
        method="highs",
        options={
            "time_limit": 60.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(result.message)
    raw = list(result.ineqlin.marginals)
    alpha_dual = F(float(raw[-1])).limit_denominator(10**7)
    if alpha_dual > 0:
        raise ValueError("Positive risk multiplier")
    y = opponent_flow(game, raw[:-1])
    dual_ub = [alpha_dual * v for v in y] + [alpha_dual]
    dual_eq = [F(float(v)).limit_denominator(10**7) for v in result.eqlin.marginals]
    lower, dual, correction = exact_residual(
        game, exact, inequality, equality, dual_ub, dual_eq, frhs, erhs
    )
    policy, records = game.recover(result.x[: game.learner.count])
    risk = game.null_risk(policy)
    cost = sum(game.expected_metrics(policy)[:3])
    noquery = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    base = sum(game.expected_metrics(noquery)[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    upper = activation * cost + (1 - activation) * base
    if lower > upper or activation * risk > game.config.alpha:
        raise ValueError("Invalid certificate")
    signed = {
        "horizon": 7,
        "dual_ub": [str(x) for x in dual_ub],
        "dual_eq": [str(x) for x in dual_eq],
        "lower": str(lower),
        "dual_value": str(dual),
        "correction": str(correction),
        "upper": str(upper),
        "gap": str(upper - lower),
        "raw_cost": str(cost),
        "raw_risk": str(risk),
        "activation": str(activation),
        "behavior": records,
    }
    encoded = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    result_json = {
        "certificate": signed,
        "certificate_sha256": hashlib.sha256(encoded).hexdigest(),
        "numeric_objective": float(result.fun),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            (OUT / "FULL_T7_CERT_PROTOCOL_V1.md").read_bytes()
        ).hexdigest(),
    }
    TARGET.write_text(json.dumps(result_json, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "lower": float(lower),
                "upper": float(upper),
                "gap": float(upper - lower),
                "risk": str(activation * risk),
            }
        )
    )


if __name__ == "__main__":
    main()
