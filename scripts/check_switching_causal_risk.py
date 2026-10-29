"""Exact causal-null semantics checks, not a novel acquisition/switching method."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def average_at_endpoint(zero: F, one: F) -> F:
    """Maximize (1-p)*zero+p*one for 0 <= p <= 1/2."""
    return max(zero, (zero + one) / 2)


def sequential_null_risk(table: tuple[int, ...]) -> F:
    # Index order is (Y1,Y2)=(0,0),(0,1),(1,0),(1,1).
    after_zero = average_at_endpoint(F(table[0]), F(table[1]))
    after_one = average_at_endpoint(F(table[2]), F(table[3]))
    return average_at_endpoint(after_zero, after_one)


def causal_coin_risks(table: tuple[int, ...], q: F) -> tuple[F, F]:
    # Index order is (Y,U)=(0,0),(0,1),(1,0),(1,1).
    # Y's conditional law must be selected before the fresh coin U.
    zero = (1 - q) * table[0] + q * table[1]
    one = (1 - q) * table[2] + q * table[3]
    causal = average_at_endpoint(zero, one)
    arrival_relaxation = (1 - q) * average_at_endpoint(F(table[0]), F(table[2]))
    arrival_relaxation += q * average_at_endpoint(F(table[1]), F(table[3]))
    return causal, arrival_relaxation


def run() -> dict[str, object]:
    subsets, coin_cases = [], []
    iid_safe = robust_safe = monotone_cases = strict_cases = 0
    for table in product((0, 1), repeat=4):
        iid = F(sum(table), 4)
        robust = sequential_null_risk(table)
        # Independently enumerate all extreme causal null strategies:
        # p1, p2(Y1=0), p2(Y1=1), each in {0,1/2}.
        brute = max(
            (1 - p1) * ((1 - p20) * table[0] + p20 * table[1])
            + p1 * ((1 - p21) * table[2] + p21 * table[3])
            for p1, p20, p21 in product((F(0), F(1, 2)), repeat=3)
        )
        assert robust == brute and robust >= iid
        iid_safe += iid <= F(1, 4)
        robust_safe += robust <= F(1, 4)
        subsets.append({"table": table, "iid_risk": str(iid), "causal_risk": str(robust)})
        monotone = table[2] >= table[0] and table[3] >= table[1]
        for q in (F(0), F(1, 4), F(1, 2), F(3, 4), F(1)):
            causal, relaxed = causal_coin_risks(table, q)
            assert causal <= relaxed
            assert not monotone or causal == relaxed
            monotone_cases += monotone
            strict_cases += causal < relaxed
            coin_cases.append(
                {
                    "table": table,
                    "coin_probability": str(q),
                    "causal_risk": str(causal),
                    "arrival_relaxed_risk": str(relaxed),
                    "monotone_in_y": monotone,
                }
            )
    assert (iid_safe, robust_safe) == (5, 2)
    # The singleton (Y1,Y2)=(0,1) represents the contingent second query.
    iid_activated = F(2, 5) * F(1, 4)
    robust_activated = F(2, 5) * sequential_null_risk((0, 1, 0, 0))
    assert iid_activated == F(1, 10) and robust_activated == F(1, 5)
    causal, relaxed = causal_coin_risks((1, 0, 0, 1), F(1, 2))
    assert (causal, relaxed) == (F(1, 2), F(3, 4))
    assert (causal / 5, relaxed / 5) == (F(1, 10), F(3, 20))
    return {
        "status": "causal_semantics_checks_passed_no_method_nominated",
        "two_label_rules": subsets,
        "two_label_summary": {
            "iid_safe_at_quarter": iid_safe,
            "robust_safe_at_quarter": robust_safe,
            "extreme_null_strategies_per_rule": 8,
        },
        "future_coin_cases": coin_cases,
        "future_coin_summary": {
            "cases": len(coin_cases),
            "monotone_equalities": monotone_cases,
            "strict_causal_arrival_gaps": strict_cases,
            "largest_gap": str(
                max(F(row["arrival_relaxed_risk"]) - F(row["causal_risk"]) for row in coin_cases)
            ),
        },
        "activated_contingent_rule": {
            "iid_risk": str(iid_activated),
            "actual_worst_risk": str(robust_activated),
            "pathwise_query_cap": 2,
        },
        "activated_future_coin_rule": {
            "actual_worst_risk": str(causal / 5),
            "arrival_relaxed_risk": str(relaxed / 5),
            "pathwise_query_cap": 1,
            "requires_delay_at_least": 2,
        },
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Elementary exact risk-order checks; no policy efficacy or novelty claim.",
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_causal_risk_v1/results.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k.endswith("summary")}, indent=2))
