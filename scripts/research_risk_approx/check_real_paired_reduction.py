"""Exact algebraic checks for bounded paired-loss binary encoding."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "docs/risk_preserving_approx/real_paired_reduction_checks_v1.json"


def encoded_mean(l0, l1, action):
    probability = (1 + l0 - l1) / 2
    return probability if action == 0 else 1 - probability


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    grid = [F(0), F(1, 4), F(1, 2), F(3, 4), F(1)]
    checked = 0
    for l0 in grid:
        for l1 in grid:
            offset = (l0 + l1 - 1) / 2
            for action in (0, 1):
                original = l0 if action == 0 else l1
                assert original == encoded_mean(l0, l1, action) + offset
                checked += 1
    # Two different full observations produce overlapping binary supports.
    a, b = (F(1, 2), F(1, 4)), (F(1, 4), F(1, 2))
    pa = (1 + a[0] - a[1]) / 2
    pb = (1 + b[0] - b[1]) / 2
    assert (pa, pb) == (F(5, 8), F(3, 8))
    assert min(pa, pb) > 0 and max(pa, pb) < 1
    # The transformed event need not satisfy an arbitrary fixed model's emission.
    assert pa not in (F(1, 20), F(19, 20))
    # Binary draw has different pathwise loss even when expected differences agree.
    assert a[0] != F(0) and a[0] != F(1)
    payload = {
        "status": "exact_algebraic_checks_passed",
        "grid_cases": checked,
        "overlapping_observation_example": {
            "pair_a": [str(x) for x in a],
            "pair_b": [str(x) for x in b],
            "encoded_positive_probability_a": str(pa),
            "encoded_positive_probability_b": str(pb),
        },
        "scope": "Data-free exact arithmetic; no real-data or HMM fit performed.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            (ROOT / "docs/risk_preserving_approx/REAL_PAIRED_REDUCTION_PROTOCOL_V1.md").read_bytes()
        ).hexdigest(),
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
