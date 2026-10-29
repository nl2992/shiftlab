"""Exact arithmetic screen for the growing posterior-alias witness."""

from __future__ import annotations

import json
from fractions import Fraction as F


def main() -> None:
    alpha = F(1, 10)
    rows = []
    for budget in range(2, 9):
        full_activation = min(F(1), alpha * 2**budget)
        suffix_activation = min(F(1), alpha * 2 ** (budget - 1))
        full_risk = full_activation / 2**budget
        suffix_risk = suffix_activation / 2 ** (budget - 1)
        full_power = F(9, 10) * full_activation
        suffix_power = suffix_activation
        assert full_risk <= alpha
        assert suffix_risk <= alpha
        rows.append(
            {
                "budget": budget,
                "full_history_risk": str(full_risk),
                "full_history_alt_power": str(full_power),
                "suffix_controller_states": 2,
                "suffix_risk": str(suffix_risk),
                "suffix_alt_power": str(suffix_power),
            }
        )

    assert rows[3]["full_history_alt_power"] == "9/10"
    assert rows[3]["suffix_alt_power"] == "1"
    assert rows[3]["suffix_risk"] == "1/16"
    print(
        json.dumps(
            {
                "status": "exact_alias_family_scaling_screen_passed",
                "alpha": str(alpha),
                "results": rows,
                "interpretation": "one-bit suffix trigger reaches unit alternative power by budget five; no growing memory gap in this family",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
