"""Evaluate an established uniform-query, all-onset safe switching baseline.

This is a deterministic bound calculation, not an efficacy experiment or new method.
"""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path


def query_schedule(horizon: int, budget: int) -> tuple[int, ...]:
    if type(horizon) is not int or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if type(budget) is not int or not 0 <= budget <= horizon:
        raise ValueError("budget must be an integer in [0, horizon]")
    if budget == 0:
        return ()
    # Exactly B distinct, nearly equally spaced event times in {1,...,T}.
    schedule = tuple((j * horizon + budget - 1) // budget for j in range(1, budget + 1))
    assert len(schedule) == budget and len(set(schedule)) == budget
    return schedule


def binary_kl(p: float, q: float) -> float:
    return p * math.log(p / q) + (1 - p) * math.log((1 - p) / (1 - q))


def evaluate_cell(
    *,
    horizon: int,
    onset: int,
    budget: int,
    delay: int,
    epsilon: float,
    alpha: float,
    query_cost: float,
) -> dict[str, object]:
    if not 1 <= onset <= horizon or not 1 <= delay:
        raise ValueError("onset and delay are outside their valid ranges")
    if not 0 < epsilon < 0.5 or not 0 < alpha < 1 or query_cost < 0:
        raise ValueError("invalid epsilon, alpha or query cost")

    label_cutoff = max(0, horizon - delay)
    effective_budget = min(budget, label_cutoff)
    schedule = query_schedule(label_cutoff, effective_budget) if effective_budget else ()
    threshold = math.log(horizon / alpha)  # uniform onset mass 1/T
    kappa = binary_kl(0.5 + epsilon, 0.5)
    log_lr_width = math.log((1 + 2 * epsilon) / (1 - 2 * epsilon))
    success_lr = F(1, 1) + 2 * F(str(epsilon))
    alpha_fraction = F(str(alpha))
    tails: list[float] = []
    arrived_counts: list[int] = []

    for t in range(onset, horizon + 1):
        visible_through = t - delay
        m = sum(onset <= s <= visible_through for s in schedule)
        arrived_counts.append(m)
        if m == 0 or m * kappa <= threshold:
            tails.append(1.0)
        else:
            exponent = -2 * (m * kappa - threshold) ** 2 / (m * log_lr_width**2)
            tails.append(min(1.0, math.exp(exponent)))

    gap = 2 * epsilon
    gross_regret_upper = gap * sum(tails)
    query_charge = query_cost * budget
    available_labels = arrived_counts[-1] if arrived_counts else 0
    max_log_lr = available_labels * math.log(1 + 2 * epsilon)
    impossible_to_cross = max_log_lr < threshold
    exact_gross_regret_if_impossible = gap * (horizon - onset + 1) if impossible_to_cross else None

    # Every component is maximized by setting every queried label to one. This computes
    # the maximum of the full onset mixture, including components that start before nu.
    max_full_mixture = (
        sum(
            (
                success_lr ** sum(event >= start for event in schedule)
                for start in range(1, horizon + 1)
            ),
            F(0),
        )
        / horizon
    )
    full_mixture_cannot_cross = max_full_mixture < 1 / alpha_fraction
    exact_gross_if_full_mixture_inert = (
        gap * (horizon - onset + 1) if full_mixture_cannot_cross else None
    )
    # The learner switches at most once and the comparator pays one switch. The
    # learner's expected switch-cost excess is therefore nonpositive.
    net_excess_upper = gross_regret_upper + query_charge
    return {
        "horizon": horizon,
        "onset": onset,
        "budget": budget,
        "queries_issued": len(schedule),
        "delay": delay,
        "epsilon": epsilon,
        "alpha": alpha,
        "unit_query_cost": query_cost,
        "query_times": list(schedule),
        "threshold_log_T_over_alpha": threshold,
        "post_change_kl_per_label": kappa,
        "log_lr_increment_range": log_lr_width,
        "arrived_post_change_queries_by_decision": arrived_counts,
        "available_post_change_queries_by_horizon": available_labels,
        "maximum_component_log_lr_if_all_positive": max_log_lr,
        "impossible_to_promote_even_if_all_available_labels_are_positive": impossible_to_cross,
        "exact_gross_decision_regret_if_promotion_is_impossible": exact_gross_regret_if_impossible,
        "maximum_full_mixture_wealth_all_positive_exact": str(max_full_mixture),
        "maximum_full_mixture_wealth_all_positive": float(max_full_mixture),
        "full_mixture_threshold": 1 / alpha,
        "full_mixture_cannot_cross_on_any_label_sequence": full_mixture_cannot_cross,
        "exact_gross_decision_regret_if_full_mixture_is_inert": exact_gross_if_full_mixture_inert,
        "gross_decision_regret_upper": gross_regret_upper,
        "total_query_charge": query_charge,
        "net_cost_excess_upper": net_excess_upper,
        "scope": "Exact pathwise maximum of the full mixture plus a Hoeffding upper bound; not efficacy or novelty evidence.",
    }


def run() -> dict[str, object]:
    common = {
        "horizon": 120,
        "onset": 61,
        "budget": 20,
        "epsilon": 0.10,
        "alpha": 0.05,
        "query_cost": 0.0,
    }
    rows = [evaluate_cell(**common, delay=d) for d in (1, 5, 20)]
    for row in rows:
        counts = row["arrived_post_change_queries_by_decision"]
        assert counts == sorted(counts)
        assert len(row["query_times"]) == common["budget"]
        assert max(row["query_times"], default=0) <= common["horizon"]
        assert (
            0
            <= row["gross_decision_regret_upper"]
            <= (2 * common["epsilon"] * (common["horizon"] - common["onset"] + 1))
        )
        assert row["maximum_full_mixture_wealth_all_positive"] < row["full_mixture_threshold"]
        assert row["full_mixture_cannot_cross_on_any_label_sequence"]
    return {
        "status": "pass",
        "policy": "use up to B nearly equally spaced queries, all released by T; uniform all-onset likelihood-ratio mixture; promote once at 1/alpha; never rollback",
        "cells": rows,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Analytic concentration-bound evaluation only; not an experiment, a matched performance result, or a novelty claim.",
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_uniform_safe_baseline_v1/results.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
