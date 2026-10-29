"""Exact two-label gap between causal and fixed-kernel null risk."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def causal_xor_risk(p1: F, p20: F, p21: F) -> F:
    """P(Y1 != Y2) for p2 selected after observing Y1."""
    return (1 - p1) * p20 + p1 * (1 - p21)


def static_product_xor_risk(q1: F, q2: F) -> F:
    """P(Y1 != Y2) for independent, nonadaptive Bernoulli labels."""
    return (1 - q1) * q2 + q1 * (1 - q2)


def main() -> None:
    endpoint = (F(0), F(1, 2))
    causal_rows = [
        (p1, p20, p21, causal_xor_risk(p1, p20, p21))
        for p1, p20, p21 in product(endpoint, repeat=3)
    ]
    static_rows = [
        (q1, q2, static_product_xor_risk(q1, q2)) for q1, q2 in product(endpoint, repeat=2)
    ]
    causal_max = max(row[3] for row in causal_rows)
    fixed_kernel_max = max(row[2] for row in static_rows)
    causal_argmax = [row[:3] for row in causal_rows if row[3] == causal_max]
    fixed_argmax = [row[:2] for row in static_rows if row[2] == fixed_kernel_max]

    # The event probability is linear in a mixture over fixed product kernels,
    # so no convex mixture can exceed the largest component value.
    assert causal_max == F(3, 4)
    assert fixed_kernel_max == F(1, 2)
    assert causal_max - fixed_kernel_max == F(1, 4)
    assert any(args == (F(1, 2), F(1, 2), F(0)) for args in causal_argmax)

    payload = {
        "status": "exact_static_null_mixture_separation_passed",
        "event": "promote iff queried labels differ (Y1 != Y2)",
        "hard_budget": 2,
        "query_clock": "query at events 1 and 2; fixed delay 2; decide after both labels release",
        "conditional_null": "each event-time Bernoulli probability is in [0, 1/2]",
        "causal_adversary": {
            "risk_max": str(causal_max),
            "endpoint_parameterization": ["p1", "p2_given_y1_0", "p2_given_y1_1"],
            "argmaxes": [[str(x) for x in row] for row in causal_argmax],
            "endpoint_profiles_checked": len(causal_rows),
        },
        "fixed_nonadaptive_kernels": {
            "risk_max": str(fixed_kernel_max),
            "parameters": ["q1", "q2"],
            "argmaxes": [[str(x) for x in row] for row in fixed_argmax],
            "endpoint_kernels_checked": len(static_rows),
        },
        "any_mixture_of_fixed_kernels_upper_bound": str(fixed_kernel_max),
        "causal_understatement": str(causal_max - fixed_kernel_max),
        "risk_alpha_separating_witness": "1/2 < alpha < 3/4",
        "scope": "Exact two-label separation only; no algorithmic novelty claim.",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_static_null_mixture_separation_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
