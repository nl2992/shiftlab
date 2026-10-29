"""Optimizer-free verification of saved incumbent-mixture certificate."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import game_for
from mixture_incumbent_helpers import component_policy, mixture_policy
from verify_cut_certificate import verify

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / "docs/risk_preserving_approx"
    result = json.loads((out / "mixture_incumbent_t7_v1.json").read_text(encoding="utf-8"))
    cert = result["certificate"]
    encoded = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != result["certificate_sha256"]:
        raise ValueError("Mixture checksum mismatch")
    previous_path = out / "causal_cut_certificate_t7_v1.json"
    verify(previous_path)
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    if previous["certificate_sha256"] != cert["prior_certificate_sha256"]:
        raise ValueError("Wrong lower-bound certificate")
    lower = F(previous["certificate"]["lower"])
    if lower != F(cert["prior_lower"]):
        raise ValueError("Incorrect lower bound")
    game = game_for(7)
    components = []
    for key in ("first", "second"):
        row = cert[key]
        policy = component_policy(game, row["records"])
        risk = game.null_risk(policy)
        cost = sum(game.expected_metrics(policy)[:3])
        if risk != F(row["risk"]) or cost != F(row["cost"]):
            raise ValueError("Component metrics do not match")
        components.append((policy, risk, cost))
    weight = F(cert["weight"])
    if not 0 <= weight <= 1:
        raise ValueError("Invalid weight")
    bound = weight * components[0][1] + (1 - weight) * components[1][1]
    combined = mixture_policy(game, components[0][0], components[1][0], weight)
    actual_risk = game.null_risk(combined)
    cost = sum(game.expected_metrics(combined)[:3])
    if (
        bound != F(cert["risk_bound"])
        or actual_risk != F(cert["actual_risk"])
        or cost != F(cert["cost"])
        or cost - lower != F(cert["gap"])
        or actual_risk > bound
        or bound > game.config.alpha
        or cost < lower
    ):
        raise ValueError("Mixture certificate invalid")
    print(
        json.dumps(
            {
                "weight": str(weight),
                "cost": float(cost),
                "actual_risk": str(actual_risk),
                "risk_bound": str(bound),
                "lower": float(lower),
                "gap": float(cost - lower),
                "checksum": result["certificate_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
