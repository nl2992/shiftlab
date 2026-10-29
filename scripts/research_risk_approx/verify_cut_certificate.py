"""Verify saved causal-cut certificates using exact arithmetic, without an optimizer."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import (
    exact_costs,
    exact_payoff,
    game_for,
    lower_bound,
    null_cut,
    restore_policy,
)

ROOT = Path(__file__).resolve().parents[2]


def verify(path):
    saved = json.loads(path.read_text(encoding="utf-8"))
    cert = saved["certificate"]
    canonical = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != saved["certificate_sha256"]:
        raise ValueError("Certificate checksum mismatch")
    game = game_for(cert["horizon"])
    costs = exact_costs(game)
    if max(abs(float(v) - game.cost.get(i, 0.0)) for i, v in enumerate(costs)) > 1e-10:
        raise ValueError("Cost reconstruction mismatch")
    payoff = exact_payoff(game)
    cuts = [null_cut(game, payoff, seq) for seq in cert["null_responses"]]
    bound, dual, correction = lower_bound(
        game, costs, cuts, [F(x) for x in cert["dual_eq"]], [F(x) for x in cert["dual_ub"]]
    )
    if (bound, dual, correction) != (
        F(cert["lower"]),
        F(cert["dual_value"]),
        F(cert["correction"]),
    ):
        raise ValueError("Dual certificate does not match")
    policy = restore_policy(game, cert["behavior"])
    risk = game.null_risk(policy)
    raw_cost = sum(game.expected_metrics(policy)[:3])
    always = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    safe_cost = sum(game.expected_metrics(always)[:3])
    activation = F(cert["activation"])
    upper = activation * raw_cost + (1 - activation) * safe_cost
    if not 0 <= activation <= 1 or activation * risk > game.config.alpha:
        raise ValueError("Upper policy is not risk-feasible")
    if risk != F(cert["raw_risk"]) or raw_cost != F(cert["raw_cost"]) or upper != F(cert["upper"]):
        raise ValueError("Upper policy evaluation does not match")
    if upper < bound or upper - bound != F(cert["gap"]):
        raise ValueError("Certificate bounds are inconsistent")
    return {
        "horizon": cert["horizon"],
        "cuts": len(cuts),
        "lower": float(bound),
        "upper": float(upper),
        "gap": float(upper - bound),
        "safe_risk": str(activation * risk),
        "checksum": saved["certificate_sha256"],
    }


def main():
    for horizon in (6, 7):
        path = ROOT / f"docs/risk_preserving_approx/causal_cut_certificate_t{horizon}_v1.json"
        print(json.dumps(verify(path)), flush=True)


if __name__ == "__main__":
    main()
