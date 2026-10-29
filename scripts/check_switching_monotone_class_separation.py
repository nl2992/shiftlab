"""Exhaustively check a signed-future-value separation for monotone promotion events."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

TAPES = tuple(product((0, 1), repeat=2))
ALTERNATIVE = {(0, 1): F(1, 2), (1, 1): F(1, 2)}
PAYOFF = {(0, 1): F(1), (1, 1): F(-2)}
ALPHA = F(1, 10)
SWITCH_COST = F(1, 20)


def event(mask: int, tape: tuple[int, int]) -> bool:
    return bool(mask & (1 << (tape[0] + 2 * tape[1])))


def monotone(mask: int) -> bool:
    for y1, y2 in TAPES:
        if event(mask, (y1, y2)):
            for z1, z2 in TAPES:
                if y1 <= z1 and y2 <= z2 and not event(mask, (z1, z2)):
                    return False
    return True


def null_probability(mask: int, p1: F, p20: F, p21: F) -> F:
    total = F(0)
    for y1, y2 in TAPES:
        prob1 = p1 if y1 else 1 - p1
        p2 = p21 if y1 else p20
        prob2 = p2 if y2 else 1 - p2
        if event(mask, (y1, y2)):
            total += prob1 * prob2
    return total


def causal_risk(mask: int) -> F:
    endpoints = (F(0), F(1, 2))
    return max(
        null_probability(mask, p1, p20, p21) for p1, p20, p21 in product(endpoints, repeat=3)
    )


def alternative_net_value(mask: int) -> F:
    value = F(0)
    for tape, probability in ALTERNATIVE.items():
        if event(mask, tape):
            value += probability * (PAYOFF[tape] - SWITCH_COST)
    return value


def run() -> dict[str, object]:
    masks = range(1 << len(TAPES))
    monotone_masks = [mask for mask in masks if monotone(mask)]
    values = {mask: alternative_net_value(mask) for mask in masks}
    risks = {mask: causal_risk(mask) for mask in masks}

    # Event 01 is robustly safe after an upfront alpha/risk randomization.
    target_mask = 1 << (0 + 2 * 1)
    target_risk = risks[target_mask]
    activation = ALPHA / target_risk
    target_safe_value = activation * values[target_mask]
    assert target_risk == F(1, 2)
    assert activation == F(1, 5)
    assert values[target_mask] == F(19, 40)
    assert target_safe_value == F(19, 200)

    # Every monotone event that includes 01 must also include 11. Under this
    # alternative its gross expected value is nonpositive; switch costs only lower it.
    monotone_values = [values[mask] for mask in monotone_masks]
    assert max(monotone_values) == 0
    assert all(not (event(mask, (0, 1)) and not event(mask, (1, 1))) for mask in monotone_masks)
    for mask in monotone_masks:
        if event(mask, (0, 1)):
            assert values[mask] <= 0

    return {
        "status": "monotone_class_separation_check_passed",
        "contract": {
            "labels": 2,
            "hard_budget": 2,
            "delay": 1,
            "alpha": str(ALPHA),
            "switch_cost": str(SWITCH_COST),
            "query_cost": "0 (separation holds even without charging queries)",
            "null": "each conditional success probability is in [0, 1/2]",
            "alternative_label_tapes": {"01": "1/2", "11": "1/2"},
            "promotion_payoff": {"01": "1", "11": "-2", "other": "0"},
        },
        "boolean_events_checked": 16,
        "monotone_events_checked": len(monotone_masks),
        "monotone_best_net_value_before_safety_mixing": str(max(monotone_values)),
        "nonmonotone_event": "01",
        "nonmonotone_event_risk": str(target_risk),
        "safe_activation_probability": str(activation),
        "nonmonotone_safe_net_value": str(target_safe_value),
        "separation": "monotone class value 0; unrestricted safe value at least 19/200",
        "scope": "Exact two-label signed-future-value counterexample; not an algorithm or novelty claim.",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_monotone_class_separation_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
