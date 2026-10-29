"""Optimizer-free verification of saved joint-risk mixture certificate."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from cut_certificate_helpers import game_for
from joint_mixture_helpers import mix_many
from mixture_incumbent_helpers import component_policy
from verify_cut_certificate import verify
from verify_mixture_incumbent import main as verify_previous

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / "docs/risk_preserving_approx"
    saved = json.loads((out / "joint_mixture_t7_v1.json").read_text(encoding="utf-8"))
    cert = saved["certificate"]
    encoded = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != saved["certificate_sha256"]:
        raise ValueError("Joint mixture checksum mismatch")
    lower_path = out / "causal_cut_certificate_t7_v1.json"
    verify(lower_path)
    lower_cert = json.loads(lower_path.read_text(encoding="utf-8"))
    if lower_cert["certificate_sha256"] != cert["lower_certificate_sha256"]:
        raise ValueError("Lower certificate mismatch")
    lower = F(lower_cert["certificate"]["lower"])
    verify_previous()
    previous = json.loads((out / "mixture_incumbent_t7_v1.json").read_text(encoding="utf-8"))
    if F(previous["certificate"]["cost"]) != F(cert["previous_upper"]):
        raise ValueError("Previous upper mismatch")
    game = game_for(7)
    weights = [F(row["weight"]) for row in cert["components"]]
    policies = [component_policy(game, row["records"]) for row in cert["components"]]
    for row, policy in zip(cert["components"], policies, strict=True):
        if sum(game.expected_metrics(policy)[:3]) != F(row["cost"]):
            raise ValueError("Component cost mismatch")
    policy = mix_many(game, policies, weights)
    risk = game.null_risk(policy)
    cost = sum(game.expected_metrics(policy)[:3])
    baseline = component_policy(game, None)
    safe_cost = sum(game.expected_metrics(baseline)[:3])
    activation = F(cert["activation"])
    upper = activation * cost + (1 - activation) * safe_cost
    if not 0 <= activation <= 1 or activation * risk > game.config.alpha:
        raise ValueError("Risk violation")
    if (
        risk != F(cert["raw_risk"])
        or cost != F(cert["raw_cost"])
        or upper != F(cert["upper"])
        or lower != F(cert["lower"])
        or upper - lower != F(cert["gap"])
        or upper < lower
    ):
        raise ValueError("Joint certificate values mismatch")
    print(
        json.dumps(
            {
                "risk": str(risk),
                "activation": str(activation),
                "upper": float(upper),
                "lower": float(lower),
                "gap": float(upper - lower),
                "components": len(weights),
                "checksum": saved["certificate_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
