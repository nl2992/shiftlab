"""Exact LP screen of monotone terminal maps on a frozen symmetric-HMM grid."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import check_switching_monotone_restriction_counterexample as base

PERSISTENCE_FLIPS = (F(1, 10), F(1, 4), F(2, 5))
EMISSION_ERRORS = (F(1, 20), F(1, 10), F(1, 4))


def solve_cell(flip_probability: F, emission_error: F) -> dict[str, object]:
    """Run the registered exact-primal/rational-dual pair for one model cell."""
    base.ALPHA = F(1, 20)
    base.QUERY_COST = F(1, 100)
    base.SWITCH_COST = F(1, 10)
    base.PRIOR1 = F(1, 2)
    base.P01 = flip_probability
    base.P10 = flip_probability
    base.THETA0 = emission_error
    base.THETA1 = 1 - emission_error

    tape_probability, future_positive = base.alternative_tape_law()
    utility = [
        probability * (2 * positive - 1 - base.SWITCH_COST)
        for probability, positive in zip(tape_probability, future_positive, strict=True)
    ]
    null_rows = base.null_endpoint_rows()
    q_unrestricted, value_unrestricted, _ = base._solve(utility, null_rows, monotone=False)
    q_monotone, value_monotone, mono_certificate = base._solve(utility, null_rows, monotone=True)
    risk_unrestricted = base._max_risk(null_rows, q_unrestricted)
    risk_monotone = base._max_risk(null_rows, q_monotone)
    mono_upper = F(mono_certificate["dual_upper_exact"])
    gap = value_unrestricted - mono_upper
    assert risk_unrestricted <= base.ALPHA and risk_monotone <= base.ALPHA
    assert value_monotone <= mono_upper
    return {
        "flip_probability": str(flip_probability),
        "emission_error": str(emission_error),
        "tape_probabilities": [str(value) for value in tape_probability],
        "future_positive_probabilities": [str(value) for value in future_positive],
        "unrestricted_map": [str(value) for value in q_unrestricted],
        "unrestricted_value": str(value_unrestricted),
        "unrestricted_risk": str(risk_unrestricted),
        "monotone_map": [str(value) for value in q_monotone],
        "monotone_value": str(value_monotone),
        "monotone_risk": str(risk_monotone),
        "monotone_dual_upper": str(mono_upper),
        "certified_unrestricted_minus_monotone_gap": str(gap),
        "strict_certified_gap": gap > 0,
        "monotone_dual_certificate": mono_certificate,
    }


def run() -> dict[str, object]:
    cells = [solve_cell(p, a) for p in PERSISTENCE_FLIPS for a in EMISSION_ERRORS]
    paths = (
        __file__,
        "scripts/check_switching_monotone_restriction_counterexample.py",
        "docs/switching_symmetric_hmm_monotonicity_screen_v1.md",
    )
    result = {
        "status": "completed_frozen_symmetric_hmm_monotonicity_screen",
        "registered_protocol": "docs/switching_symmetric_hmm_monotonicity_screen_v1.md",
        "contract": {
            "horizon": 4,
            "budget": 3,
            "delay": 1,
            "alpha": str(F(1, 20)),
            "query_cost": str(F(1, 100)),
            "switch_cost": str(F(1, 10)),
            "endpoint_null_count": 128,
            "persistence_flip_grid": [str(p) for p in PERSISTENCE_FLIPS],
            "emission_error_grid": [str(a) for a in EMISSION_ERRORS],
        },
        "cells": cells,
        "certified_separations": sum(cell["strict_certified_gap"] for cell in cells),
        "interpretation": (
            "A strict certified gap in any cell rejects a symmetry-based without-loss monotonicity "
            "claim. No gap means only that this frozen finite grid did not refute it."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths
        },
    }
    out = Path("outputs/switching_symmetric_hmm_monotonicity_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    report = run()
    print(
        json.dumps(
            {
                "status": report["status"],
                "certified_separations": report["certified_separations"],
                "cells": [
                    {
                        "flip_probability": cell["flip_probability"],
                        "emission_error": cell["emission_error"],
                        "unrestricted_value": cell["unrestricted_value"],
                        "monotone_dual_upper": cell["monotone_dual_upper"],
                        "certified_gap": cell["certified_unrestricted_minus_monotone_gap"],
                        "strict_certified_gap": cell["strict_certified_gap"],
                    }
                    for cell in report["cells"]
                ],
            },
            indent=2,
        )
    )
