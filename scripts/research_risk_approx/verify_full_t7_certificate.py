"""Verify T=7 full decomposed LP certificate without an optimizer."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import exact_costs, game_for, restore_policy
from generate_full_t7_certificate import exact_residual, matrix_for

ROOT = Path(__file__).resolve().parents[2]


def verify():
    saved = json.loads(
        (ROOT / "docs/risk_preserving_approx/full_t7_certificate_v1.json").read_text(
            encoding="utf-8"
        )
    )
    cert = saved["certificate"]
    encoded = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != saved["certificate_sha256"]:
        raise ValueError("Checksum mismatch")
    game = game_for(7)
    exact = exact_costs(game)
    inequality, equality, erhs, frhs = matrix_for(game)
    lower, dual, correction = exact_residual(
        game,
        exact,
        inequality,
        equality,
        [F(v) for v in cert["dual_ub"]],
        [F(v) for v in cert["dual_eq"]],
        frhs,
        erhs,
    )
    if (lower, dual, correction) != (
        F(cert["lower"]),
        F(cert["dual_value"]),
        F(cert["correction"]),
    ):
        raise ValueError("Dual discrepancy")
    policy = restore_policy(game, cert["behavior"])
    risk = game.null_risk(policy)
    cost = sum(game.expected_metrics(policy)[:3])
    safe = lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    safe_cost = sum(game.expected_metrics(safe)[:3])
    activation = F(cert["activation"])
    upper = activation * cost + (1 - activation) * safe_cost
    if (
        not 0 <= activation <= 1
        or activation * risk > game.config.alpha
        or (risk, cost, upper) != (F(cert["raw_risk"]), F(cert["raw_cost"]), F(cert["upper"]))
        or lower > upper
        or upper - lower != F(cert["gap"])
    ):
        raise ValueError("Upper policy or gap invalid")
    return {
        "lower": str(lower),
        "upper": str(upper),
        "gap": str(upper - lower),
        "risk_bound": str(activation * risk),
        "checksum": saved["certificate_sha256"],
    }


if __name__ == "__main__":
    result = verify()
    print(
        json.dumps(
            {
                "lower": float(F(result["lower"])),
                "upper": float(F(result["upper"])),
                "gap": float(F(result["gap"])),
                "risk_bound": result["risk_bound"],
                "checksum": result["checksum"],
            }
        )
    )
