"""Save an exact-risk T=7 pre-promotion-cap upper witness."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import game_for
from verify_full_t7_certificate import verify

from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"
TARGET = OUT / "precap2_t7_witness_v1.json"


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    previous = verify()
    base = game_for(7)
    game = PrePromotionCapGame(base.config, base.model, pre_cap=2)
    _, policy, records = game.solve()
    risk = game.null_risk(policy)
    cost = sum(game.expected_metrics(policy)[:3])
    noquery = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    safe_cost = sum(game.expected_metrics(noquery)[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    upper = activation * cost + (1 - activation) * safe_cost
    previous_screen = json.loads(
        (OUT / "prepromotion_cap_screen_v1.json").read_text(encoding="utf-8")
    )
    original = next(r for r in previous_screen["rows"] if r["horizon"] == 7 and r["pre_cap"] == 2)
    if upper != F(original["safe_cost"]) or activation * risk > game.config.alpha:
        raise ValueError("Screen cost or risk not reproduced")
    lower = F(previous["lower"])
    signed = {
        "horizon": 7,
        "pre_cap": 2,
        "behavior": records,
        "raw_risk": str(risk),
        "raw_cost": str(cost),
        "activation": str(activation),
        "upper": str(upper),
        "lower": str(lower),
        "gap": str(upper - lower),
        "lower_checksum": previous["checksum"],
    }
    encoded = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    payload = {
        "certificate": signed,
        "certificate_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "upper": float(upper),
                "lower": float(lower),
                "gap": float(upper - lower),
                "risk": str(activation * risk),
            }
        )
    )


if __name__ == "__main__":
    main()
