"""Registered exact joint-null root mixture diagnostic."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

import generate_mixture_incumbent as source
import numpy as np
from cut_certificate_helpers import exact_payoff, game_for
from joint_mixture_helpers import mix_many
from mixture_incumbent_helpers import component_policy, realization
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack
from verify_cut_certificate import verify

from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"
TARGET = OUT / "joint_mixture_t7_v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    temp = ROOT / "outputs/risk_preserving_approx/joint_mixture_source_run_v1.json"
    if temp.exists():
        raise FileExistsError(f"Refusing to overwrite {temp}")
    temp.parent.mkdir(parents=True, exist_ok=True)
    saved_target = source.TARGET
    captured = []
    original_recover = FirstPromotionDecomposedGame.recover

    def collect(game, x):
        policy, records = original_recover(game, x)
        captured.append(records)
        return policy, records

    try:
        source.TARGET = temp
        with patch.object(FirstPromotionDecomposedGame, "recover", collect):
            source.main()
    finally:
        source.TARGET = saved_target
    game = game_for(7)
    records = [None, *captured]
    policies = [component_policy(game, item) for item in records]
    flows = [realization(game, policy) for policy in policies]
    costs = [sum(game.expected_metrics(policy)[:3]) for policy in policies]
    payoff = exact_payoff(game)
    keys = list(payoff)
    a = coo_matrix(
        ([float(payoff[k]) for k in keys], ([k[0] for k in keys], [k[1] for k in keys])),
        shape=(game.learner.count, game.opponent.count),
    ).tocsr()
    fmat, frhs = game.opponent.matrix()
    n = len(policies)
    b = np.array([[float(v) for v in flow] for flow in flows]) @ a
    inequality = vstack(
        [
            hstack([csr_matrix(b.T), -fmat.T]),
            hstack([csr_matrix((1, n)), csr_matrix(frhs.reshape(1, -1))]),
        ]
    ).tocsr()
    rhs = np.r_[np.zeros(game.opponent.count), float(game.config.alpha)]
    equality = hstack([csr_matrix(np.ones((1, n))), csr_matrix((1, len(frhs)))]).tocsr()
    objective = np.r_[np.array([float(v) for v in costs]), np.zeros(len(frhs))]
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=rhs,
        A_eq=equality,
        b_eq=[1.0],
        bounds=[(0, None)] * n + [(None, None)] * len(frhs),
        method="highs",
        options={
            "time_limit": 60.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError("Joint mixture LP failed: " + result.message)
    raw_weights = [F(float(max(0.0, v))).limit_denominator(10**7) for v in result.x[:n]]
    if not sum(raw_weights):
        raise ValueError("No positive mixture weights")
    weights = [v / sum(raw_weights) for v in raw_weights]
    support = [i for i, w in enumerate(weights) if w]
    weighted = [weights[i] for i in support]
    mixture = mix_many(game, [policies[i] for i in support], weighted)
    raw_risk = game.null_risk(mixture)
    raw_cost = sum(game.expected_metrics(mixture)[:3])
    if raw_cost != sum((weights[i] * costs[i] for i in support), F(0)):
        raise ValueError("Mixture cost reconstruction failed")
    activation = min(F(1), game.config.alpha / raw_risk) if raw_risk else F(1)
    upper = activation * raw_cost + (1 - activation) * costs[0]
    prior_mix = json.loads((OUT / "mixture_incumbent_t7_v1.json").read_text(encoding="utf-8"))
    old_upper = F(prior_mix["certificate"]["cost"])
    selected = "joint" if upper < old_upper else "previous"
    lower_path = OUT / "causal_cut_certificate_t7_v1.json"
    verify(lower_path)
    lower_cert = json.loads(lower_path.read_text(encoding="utf-8"))
    lower = F(lower_cert["certificate"]["lower"])
    if activation * raw_risk > game.config.alpha or upper < lower:
        raise ValueError("Risk or lower bound check failed")
    components = [
        {"weight": str(weights[i]), "records": records[i], "cost": str(costs[i]), "index": i}
        for i in support
    ]
    signed = {
        "components": components,
        "activation": str(activation),
        "raw_risk": str(raw_risk),
        "raw_cost": str(raw_cost),
        "upper": str(upper),
        "lower": str(lower),
        "gap": str(upper - lower),
        "previous_upper": str(old_upper),
        "selected": selected,
        "lower_certificate_sha256": lower_cert["certificate_sha256"],
    }
    encoded = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    payload = {
        "certificate": signed,
        "certificate_sha256": hashlib.sha256(encoded).hexdigest(),
        "lp_objective": float(result.fun),
        "lp_inequality_violation": float(max(0.0, np.max(inequality @ result.x - rhs))),
        "lp_equality_residual": float(np.max(np.abs(equality @ result.x - 1.0))),
        "candidates": n,
        "source_run_sha256": sha(temp),
        "source_sha256": sha(Path(__file__)),
        "protocol_sha256": sha(OUT / "JOINT_MIXTURE_PROTOCOL_V1.md"),
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "candidates": n,
                "support": len(support),
                "raw_risk": float(raw_risk),
                "activation": float(activation),
                "upper": float(upper),
                "previous": float(old_upper),
                "selected": selected,
                "gap": float(upper - lower),
            }
        )
    )


if __name__ == "__main__":
    main()
