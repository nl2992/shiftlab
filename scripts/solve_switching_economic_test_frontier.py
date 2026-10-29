"""Exact fixed-cohort economic test reference; standard optimization, not a novel method."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache
from itertools import combinations, product
from math import comb
from pathlib import Path

HORIZON, DELAY = 20, 2
QUERY_COST, SWITCH_COST, ALPHA = F(1, 100), F(1, 10), F(1, 10)


@dataclass(frozen=True)
class Point:
    queries: int
    cutoff: int
    risk: F
    gain: F


def tail(n: int, cutoff: int, probability: F) -> F:
    return sum(
        (
            F(comb(n, s)) * probability**s * (1 - probability) ** (n - s)
            for s in range(max(0, cutoff), n + 1)
        ),
        F(0),
    )


def point(n: int, cutoff: int) -> Point:
    high, low = tail(n, cutoff, F(3, 4)), tail(n, cutoff, F(1, 4))
    remaining = HORIZON - n - DELAY + 1
    gain = remaining * (high - low) / 4 - SWITCH_COST * (high + low) / 2 - n * QUERY_COST
    return Point(n, cutoff, tail(n, cutoff, F(1, 2)), gain)


def weighted(plan, field: str) -> F:
    return sum(weight * getattr(p, field) for weight, p in plan)


def optimize(points: list[Point]):
    plans = [((F(1), p),) for p in points if p.risk <= ALPHA]
    for left, right in combinations(points, 2):
        if left.risk > right.risk:
            left, right = right, left
        if left.risk < ALPHA < right.risk:
            high_weight = (ALPHA - left.risk) / (right.risk - left.risk)
            plans.append(((1 - high_weight, left), (high_weight, right)))
    assert plans
    return max(plans, key=lambda p: (weighted(p, "gain"), -weighted(p, "queries")))


@cache
def adversarial_null(n: int, cutoff: int, observed: int = 0, positive: int = 0) -> F:
    if observed == n:
        return F(positive >= cutoff)
    negative = adversarial_null(n, cutoff, observed + 1, positive)
    positive_value = adversarial_null(n, cutoff, observed + 1, positive + 1)
    return max(negative, (negative + positive_value) / 2)


def word_knapsack(n: int) -> F:
    remaining = HORIZON - n - DELAY + 1
    words = []
    null_mass = F(1, 2) ** n
    for word in product((0, 1), repeat=n):
        high, low = F(1), F(1)
        for y in word:
            high *= F(3, 4) if y else F(1, 4)
            low *= F(1, 4) if y else F(3, 4)
        benefit = remaining * (high - low) / 4 - SWITCH_COST * (high + low) / 2
        words.append((benefit / null_mass, benefit))
    capacity, gain = ALPHA, F(0)
    for density, benefit in sorted(words, reverse=True):
        if density <= 0 or capacity == 0:
            break
        rejection_probability = min(F(1), capacity / null_mass)
        gain += rejection_probability * benefit
        capacity -= rejection_probability * null_mass
    return gain - n * QUERY_COST


def run() -> dict[str, object]:
    all_points = [Point(0, 1, F(0), F(0))]
    checks, results = [], []
    previous_cost = F(HORIZON, 2)
    for budget in range(7):
        if budget:
            points = [point(budget, j) for j in range(budget + 2)]
            assert all(adversarial_null(budget, p.cutoff) == p.risk for p in points)
            fixed = optimize(points)
            assert weighted(fixed, "gain") == word_knapsack(budget)
            checks.append(
                {
                    "n": budget,
                    "word_count": 2**budget,
                    "knapsack_and_count_frontier_agree": True,
                    "all_threshold_adversarial_risks_agree": True,
                }
            )
            all_points.extend(points)
        plan = optimize(all_points)
        cost = F(HORIZON, 2) - weighted(plan, "gain")
        risk = weighted(plan, "risk")
        assert risk <= ALPHA and cost <= previous_cost
        assert all(p.queries <= budget for w, p in plan if w)
        if budget == 1:
            assert cost == F(4781, 500)
        previous_cost = cost
        results.append(
            {
                "hard_cap": budget,
                "exact_cost": str(cost),
                "cost": float(cost),
                "worst_null_risk": str(risk),
                "expected_queries": str(weighted(plan, "queries")),
                "pathwise_max_queries": max(p.queries for w, p in plan if w),
                "lottery": [
                    {
                        "weight": str(w),
                        "queries": p.queries,
                        "count_cutoff": p.cutoff,
                        "conditional_risk": str(p.risk),
                    }
                    for w, p in plan
                    if w
                ],
            }
        )
    return {
        "status": "fixed_cohort_reference_complete_no_novel_method_claim",
        "parameters": {
            "T": HORIZON,
            "delay": DELAY,
            "alpha": str(ALPHA),
            "query_cost": str(QUERY_COST),
            "switch_cost": str(SWITCH_COST),
            "prior_high": "1/2",
            "theta": ["1/4", "3/4"],
        },
        "frontier": results,
        "independent_checks": checks,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Upfront mixtures of fixed cohorts and terminal tests, not all sequential switching policies.",
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_economic_test_frontier_v1/results.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["frontier"], indent=2))
