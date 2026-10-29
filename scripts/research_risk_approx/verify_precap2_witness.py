"""Optimizer-free verification of the saved T=7 capped-policy upper witness."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import game_for, restore_policy
from verify_full_t7_certificate import verify

from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / "docs/risk_preserving_approx"
    saved = json.loads((out / "precap2_t7_witness_v1.json").read_text(encoding="utf-8"))
    cert = saved["certificate"]
    encoded = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != saved["certificate_sha256"]:
        raise ValueError("Checksum mismatch")
    full = verify()
    if full["checksum"] != cert["lower_checksum"]:
        raise ValueError("Wrong full-oracle certificate")
    base = game_for(7)
    game = PrePromotionCapGame(base.config, base.model, pre_cap=cert["pre_cap"])
    game.build()
    policy = restore_policy(game, cert["behavior"])
    risk = game.null_risk(policy)
    cost = sum(game.expected_metrics(policy)[:3])
    noquery = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    baseline = sum(game.expected_metrics(noquery)[:3])
    activation = F(cert["activation"])
    upper = activation * cost + (1 - activation) * baseline
    lower = F(full["lower"])
    if (
        not 0 <= activation <= 1
        or activation * risk > game.config.alpha
        or (risk, cost, upper, lower, upper - lower)
        != (
            F(cert["raw_risk"]),
            F(cert["raw_cost"]),
            F(cert["upper"]),
            F(cert["lower"]),
            F(cert["gap"]),
        )
    ):
        raise ValueError("Upper witness or gap invalid")
    print(
        json.dumps(
            {
                "upper": float(upper),
                "lower": float(lower),
                "gap": float(upper - lower),
                "risk_bound": str(activation * risk),
                "checksum": saved["certificate_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
