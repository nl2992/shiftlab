"""Evaluate a registered standard KL lower bound for a uniform unknown onset."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HORIZON = 120
BUDGET = 20
EPSILON = 0.1
ALPHA = 0.05
SWITCH_COST = 0.1
DELAYS = (1, 5, 20)


def kl_bernoulli(p: float, q: float) -> float:
    if p == 0:
        left = 0.0
    else:
        left = p * math.log(p / q)
    if p == 1:
        right = 0.0
    else:
        right = (1 - p) * math.log((1 - p) / (1 - q))
    return left + right


def beta_alpha(divergence: float) -> float:
    if divergence <= 0:
        return ALPHA
    if divergence >= math.log(1 / ALPHA):
        return 1.0
    low, high = ALPHA, 1.0
    for _ in range(100):
        mid = (low + high) / 2
        if kl_bernoulli(mid, ALPHA) <= divergence:
            low = mid
        else:
            high = mid
    return low


def labels_available(onset: int, time: int, delay: int) -> int:
    return min(BUDGET, max(0, time - onset - delay + 1))


def evaluate(delay: int, kappa: float) -> dict[str, object]:
    mixture_gross = 0.0
    individual_sum = 0.0
    time_rows = []
    for time in range(1, HORIZON + 1):
        active_counts = [labels_available(onset, time, delay) for onset in range(1, time + 1)]
        mean_count = sum(active_counts) / time
        mixture_power = beta_alpha(mean_count * kappa)
        mixture_gross += (2 * EPSILON / HORIZON) * time * (1 - mixture_power)

        # Average the existing fixed-onset bound over all onsets after summing each
        # onset's post-change decision losses.
        individual_regret_at_time = sum(1 - beta_alpha(count * kappa) for count in active_counts)
        individual_sum += (2 * EPSILON / HORIZON) * individual_regret_at_time
        time_rows.append(
            {
                "time": time,
                "active_onsets": time,
                "mean_arrived_post_onset_labels": mean_count,
                "mixture_power_upper_bound": mixture_power,
            }
        )

    onset_61 = (
        2
        * EPSILON
        * sum(
            1 - beta_alpha(labels_available(61, time, delay) * kappa)
            for time in range(61, HORIZON + 1)
        )
    )
    return {
        "delay": delay,
        "mixture_average_onset_gross_lower_bound": mixture_gross,
        "mixture_average_onset_net_lower_bound": mixture_gross - SWITCH_COST,
        "average_of_individual_onset_gross_bounds": individual_sum,
        "average_of_individual_onset_net_bounds": individual_sum - SWITCH_COST,
        "gross_sharpening_vs_average_individual": mixture_gross - individual_sum,
        "onset_61_gross_lower_bound_reference_only": onset_61,
        "onset_61_net_lower_bound_reference_only": onset_61 - SWITCH_COST,
        "timewise_mixture_inputs": time_rows,
    }


def run() -> dict[str, object]:
    kappa = kl_bernoulli(0.5 + EPSILON, 0.5)
    results = [evaluate(delay, kappa) for delay in DELAYS]
    return {
        "status": "registered_unknown_onset_kl_lower_bound_evaluated_no_method_claim",
        "parameters": {
            "horizon": HORIZON,
            "hard_query_cap": BUDGET,
            "epsilon": EPSILON,
            "alpha": ALPHA,
            "switch_cost": SWITCH_COST,
            "onset_prior": "uniform on 1,...,T",
            "delays": list(DELAYS),
            "per_label_kl": kappa,
        },
        "results": results,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Standard KL/data-processing lower bound; average-onset impossibility floor, not an attainable frontier or new method.",
    }


if __name__ == "__main__":
    report = run()
    target = Path("outputs/switching_unknown_onset_mixture_lower_bound_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in report["results"]:
        print(
            row["delay"],
            row["mixture_average_onset_gross_lower_bound"],
            row["average_of_individual_onset_gross_bounds"],
            row["gross_sharpening_vs_average_individual"],
        )
