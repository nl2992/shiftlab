"""Verify the T=8 lower bound and cap witness without invoking an optimizer."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import exact_costs, game_for, restore_policy
from generate_full_t8_decomposed_certificate import exact_residual, matrix_for

from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

ROOT = Path(__file__).resolve().parents[2]
CERT = ROOT / "docs/risk_preserving_approx/full_t8_decomposed_certificate_v1.json"
SOURCE = ROOT / "scripts/research_risk_approx/generate_full_t8_decomposed_certificate.py"
EXECUTED = ROOT / "docs/risk_preserving_approx/full_t8_decomposed_executed_source_v1.txt"


def verify() -> dict:
    saved = json.loads(CERT.read_text(encoding="utf-8"))
    cert = saved["certificate"]
    encoded = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != saved["certificate_sha256"]:
        raise ValueError("certificate checksum mismatch")
    if hashlib.sha256(EXECUTED.read_bytes()).hexdigest() != saved["source_sha256"]:
        raise ValueError("preserved executed source hash mismatch")
    game = game_for(8)
    exact = exact_costs(game)
    inequality, equality, erhs, _frhs = matrix_for(game)
    lower, dual_value, correction = exact_residual(
        game,
        exact,
        inequality,
        equality,
        [F(value) for value in cert["dual_ub"]],
        [F(value) for value in cert["dual_eq"]],
        erhs,
    )
    if (lower, dual_value, correction) != (
        F(cert["lower"]),
        F(cert["dual_value"]),
        F(cert["correction"]),
    ):
        raise ValueError("exact dual or correction discrepancy")

    full_policy = restore_policy(game, cert["full_behavior"])
    full_metrics = game.expected_metrics(full_policy)
    full_risk = game.null_risk(full_policy)
    full_raw_cost = sum(full_metrics[:3])
    safe = lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    safe_cost = sum(game.expected_metrics(safe)[:3])
    full_activation = F(cert["full_activation"])
    full_upper = full_activation * full_raw_cost + (1 - full_activation) * safe_cost

    cap = PrePromotionCapGame(game.config, game.model, pre_cap=2)
    cap.build()
    cap_policy = restore_policy(cap, cert["cap_behavior"])
    cap_cost = sum(cap.expected_metrics(cap_policy)[:3])
    cap_risk = cap.null_risk(cap_policy)
    upper = min(full_upper, cap_cost)
    if (
        full_raw_cost != F(cert["full_raw_cost"])
        or full_risk != F(cert["full_raw_risk"])
        or full_activation * full_risk > game.config.alpha
        or full_upper != F(cert["full_upper"])
        or cap_cost != F(cert["cap_cost"])
        or cap_risk != F(cert["cap_risk"])
        or cap_risk > cap.config.alpha
        or upper != F(cert["upper"])
        or lower > upper
        or upper - lower != F(cert["gap"])
    ):
        raise ValueError("policy upper, risk or bracket invalid")
    return {
        "lower": str(lower),
        "upper": str(upper),
        "gap": str(upper - lower),
        "cap_cost": str(cap_cost),
        "cap_risk": str(cap_risk),
        "full_risk": str(full_risk),
        "certificate_sha256": saved["certificate_sha256"],
    }


if __name__ == "__main__":
    result = verify()
    print(
        json.dumps(
            {
                "lower": float(F(result["lower"])),
                "upper": float(F(result["upper"])),
                "gap": float(F(result["gap"])),
                "cap_cost": result["cap_cost"],
                "cap_risk": result["cap_risk"],
                "certificate_sha256": result["certificate_sha256"],
            }
        )
    )
