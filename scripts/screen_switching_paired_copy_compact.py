"""Exact arithmetic screen for a delayed paired-copy causal-null test."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from math import comb
from pathlib import Path


def binomial_tail(n: int, threshold: int, probability: Fraction) -> Fraction:
    return sum(
        (
            Fraction(comb(n, successes))
            * probability**successes
            * (1 - probability) ** (n - successes)
            for successes in range(threshold, n + 1)
        ),
        Fraction(),
    )


def find_test(alpha: Fraction, target_power: Fraction) -> tuple[int, int, Fraction, Fraction]:
    for pairs in range(1, 1001):
        for threshold in range(1, pairs + 1):
            risk = binomial_tail(pairs, threshold, Fraction(1, 4))
            power = binomial_tail(pairs, threshold, Fraction(1, 2))
            if risk <= alpha and power >= target_power:
                return pairs, threshold, risk, power
    raise RuntimeError("No test found within the declared search range")


def main() -> None:
    alpha = Fraction(1, 10)
    target_power = Fraction(99, 100)
    query_cost = Fraction(1, 100)
    switch_cost = Fraction(1, 10)
    future_rounds = 10_000
    pairs, threshold, risk, power = find_test(alpha, target_power)
    requests = 2 * pairs
    compact_states = 4 * (pairs + 1) + 2
    value = power * (future_rounds - switch_cost) - requests * query_cost
    oracle_upper_bound = Fraction(future_rounds)
    oracle_gap_upper_bound = oracle_upper_bound - value
    script_path = Path(__file__)
    script_sha256 = hashlib.sha256(script_path.read_bytes()).hexdigest()

    result = {
        "contract": {
            "alternative_pair_law": "Y_(2i-1)=Y_(2i)=X_i, X_i iid Bernoulli(1/2)",
            "causal_null": "each queried label conditional success probability <= 1/2 given full prior history",
            "delay": 1,
            "alpha": str(alpha),
            "target_alternative_power": str(target_power),
            "query_cost": str(query_cost),
            "switch_cost": str(switch_cost),
            "future_reward_rounds": future_rounds,
        },
        "test": {
            "pairs": pairs,
            "threshold_joint_positive_pairs": threshold,
            "pathwise_query_budget": requests,
            "exact_worst_causal_null_risk": str(risk),
            "alternative_promotion_probability": str(power),
            "controller_state_count_upper_bound": compact_states,
            "controller_memory_bits_upper_bound": (compact_states - 1).bit_length(),
        },
        "value": {
            "compact_net_improvement": str(value),
            "full_history_oracle_net_improvement_upper_bound": str(oracle_upper_bound),
            "full_history_oracle_minus_compact_gap_upper_bound": str(oracle_gap_upper_bound),
            "relative_gap_upper_bound": str(oracle_gap_upper_bound / oracle_upper_bound),
        },
        "script_sha256": script_sha256,
    }
    output = Path("outputs/switching_paired_copy_compact_screen_v1") / "results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
