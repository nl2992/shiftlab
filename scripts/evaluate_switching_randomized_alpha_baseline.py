"""Exact finite-cell evaluation of a repeatedly randomized safe test baseline."""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path


def schedule(horizon: int, delay: int, budget: int) -> tuple[int, ...]:
    cutoff = horizon - delay
    if cutoff < budget:
        raise ValueError("registered cell needs enough event times for all queries to arrive")
    times = tuple((j * cutoff + budget - 1) // budget for j in range(1, budget + 1))
    assert len(set(times)) == budget and max(times) <= cutoff
    return times


def kl_bernoulli(p: float, q: float) -> float:
    return p * math.log(p / q) + (1 - p) * math.log((1 - p) / (1 - q))


def beta_alpha(alpha: float, divergence: float) -> float:
    low, high = alpha, 1.0
    for _ in range(100):
        mid = (low + high) / 2
        if kl_bernoulli(mid, alpha) <= divergence:
            low = mid
        else:
            high = mid
    return low


def noisy_lower_bound(
    *, horizon: int, onset: int, budget: int, delay: int, epsilon: F, alpha: F
) -> float:
    length = horizon - onset + 1
    epsilon_float, alpha_float = float(epsilon), float(alpha)
    kappa = kl_bernoulli(0.5 + epsilon_float, 0.5)
    return (
        2
        * epsilon_float
        * sum(
            1
            - beta_alpha(
                alpha_float,
                min(budget, max(0, j - delay + 1)) * kappa,
            )
            for j in range(length)
        )
    )


def evaluate(delay: int) -> dict[str, object]:
    horizon, onset, budget = 120, 61, 20
    epsilon, alpha = F(1, 10), F(1, 20)
    query_cost, switch_cost = F(1, 100), F(1, 10)
    rho = 2 * alpha / budget
    queries = schedule(horizon, delay, budget)
    post_change_probabilities = [F(1, 2) if s < onset else F(1, 2) + epsilon for s in queries]

    survival = F(1)
    gross = F(0)
    for time in range(onset, horizon + 1):
        survival = F(1)
        for event, probability in zip(queries, post_change_probabilities, strict=True):
            if event + delay <= time:
                survival *= 1 - rho * probability
        gross += 2 * epsilon * survival

    no_promotion = math.prod(1 - rho * p for p in post_change_probabilities)
    false_promotion_risk = 1 - (1 - rho / 2) ** budget
    net_excess = gross + query_cost * budget - switch_cost * no_promotion
    lower_gross = noisy_lower_bound(
        horizon=horizon, onset=onset, budget=budget, delay=delay, epsilon=epsilon, alpha=alpha
    )
    return {
        "delay": delay,
        "query_times": list(queries),
        "queries_issued": budget,
        "per_attempt_promotion_coin": str(rho),
        "worst_causal_null_promotion_risk_exact": str(false_promotion_risk),
        "worst_causal_null_promotion_risk": float(false_promotion_risk),
        "risk_level": str(alpha),
        "post_change_gross_decision_regret_exact": str(gross),
        "post_change_gross_decision_regret": float(gross),
        "query_charge": str(query_cost * budget),
        "probability_never_promoted_under_alternative": str(no_promotion),
        "switch_cost_excess": str(-switch_cost * no_promotion),
        "net_cost_excess_exact": str(net_excess),
        "net_cost_excess": float(net_excess),
        "noisy_information_lower_bound_gross": lower_gross,
        "noisy_information_lower_bound_net": lower_gross - float(switch_cost),
        "gap_net_upper_minus_lower": float(net_excess) - lower_gross + float(switch_cost),
    }


def run() -> dict[str, object]:
    results = [evaluate(delay) for delay in (1, 5, 20)]
    for row in results:
        risk = F(row["worst_causal_null_promotion_risk_exact"])
        assert risk <= F(1, 20)
        assert len(row["query_times"]) == 20
    return {
        "status": "completed_exact_randomized_test_baseline",
        "policy": "query at fixed evenly spaced event times; on each released positive, promote with fresh probability 2 alpha/B; hold; continue all scheduled queries",
        "parameters": {
            "horizon": 120,
            "onset": 61,
            "budget": 20,
            "epsilon": "1/10",
            "alpha": "1/20",
            "query_cost": "1/100",
            "switch_cost": "1/10",
        },
        "delays": results,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact expected-value calculation for one standard randomized test baseline; not an experiment, optimality claim or novel method.",
    }


if __name__ == "__main__":
    report = run()
    target = Path("outputs/switching_randomized_alpha_baseline_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
