"""Exact small-horizon check of the supporting budget/delay lower-bound algebra.

No learner is fitted and no efficacy or statistical novelty conclusion is tested.
"""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from math import comb
from pathlib import Path


def check(max_horizon: int = 9) -> dict[str, object]:
    schedules = 0
    cases = 0
    largest_gap = 0.0
    for horizon in range(1, max_horizon + 1):
        for budget in range(horizon + 1):
            subsets = list(combinations(range(1, horizon + 1), budget))
            schedules += len(subsets)
            for length in range(1, horizon + 1):
                onsets = horizon - length + 1
                for delay in range(1, horizon + 1):
                    widths = [max(0, j - delay + 1) for j in range(length)]
                    lower = sum(max(0, 1 - budget * w / onsets) for w in widths)
                    total_misses = 0
                    for subset in subsets:
                        misses = 0
                        for j, width in enumerate(widths):
                            hits = sum(
                                any(nu <= s <= nu + j - delay for s in subset)
                                for nu in range(1, onsets + 1)
                            )
                            assert hits <= budget * width
                            misses += onsets - hits
                        mean_misses = misses / onsets
                        assert mean_misses + 1e-12 >= lower
                        if length <= delay:
                            assert misses == length * onsets
                        total_misses += misses
                        cases += 1
                    expected_uniform = sum(
                        comb(horizon - w, budget) / comb(horizon, budget)
                        if horizon - w >= budget
                        else 0.0
                        for w in widths
                    )
                    exhaustive_uniform = total_misses / (len(subsets) * onsets)
                    gap = abs(expected_uniform - exhaustive_uniform)
                    largest_gap = max(largest_gap, gap)
                    assert gap < 1e-12
    return {
        "status": "pass",
        "max_horizon": max_horizon,
        "query_subsets": schedules,
        "schedule_length_delay_cases": cases,
        "largest_uniform_formula_error": largest_gap,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact finite enumeration; not efficacy, statistical calibration or novelty.",
    }


if __name__ == "__main__":
    result = check()
    target = Path("outputs/switching_budget_delay_lower_bound_v1/checks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
