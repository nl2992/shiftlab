"""Summarize the prespecified direct-frontload-plus-E_rb development screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

CANDIDATE = "E_rb:gated_adaptive_range+front"
COMPARATORS = (
    "E_rb:gated_adaptive_range",
    "gated_adaptive_range+front",
    "rmm:gated_adaptive_range+RMM",
    "CONTROL_never_switch",
)
METRICS = (
    "net",
    "loss",
    "labels",
    "switches",
    "n_promotions",
    "n_rollbacks",
    "first_deploy",
)


def mean_interval(values: np.ndarray) -> tuple[float, float, float]:
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1) / np.sqrt(len(values)))
    half = float(student_t.ppf(0.975, len(values) - 1) * se)
    return mean, mean - half, mean + half


def wilson(successes: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return float(center - radius), float(center + radius)


def summarize(records_path: Path) -> dict:
    rows = [json.loads(line) for line in records_path.read_text().splitlines() if line]
    seeds = sorted({int(row["seed"]) for row in rows})
    regimes = sorted({row["regime"] for row in rows})
    by_key = {(row["regime"], int(row["seed"]), row["policy"]): row for row in rows}
    policies = sorted({row["policy"] for row in rows})
    result: dict = {
        "records": str(records_path),
        "n_paired_seeds_per_regime": len(seeds),
        "regimes": regimes,
        "mean_metrics": {},
        "paired_net_differences_candidate_minus_comparator": {},
    }
    for policy in policies:
        result["mean_metrics"][policy] = {}
        for regime in regimes:
            rs = [by_key[(regime, seed, policy)] for seed in seeds]
            result["mean_metrics"][policy][regime] = {
                metric: float(np.mean([row[metric] for row in rs])) for metric in METRICS
            }
    for regime in regimes:
        result["paired_net_differences_candidate_minus_comparator"][regime] = {}
        for comparator in COMPARATORS:
            diffs = np.array(
                [
                    by_key[(regime, seed, CANDIDATE)]["net"]
                    - by_key[(regime, seed, comparator)]["net"]
                    for seed in seeds
                ],
                dtype=float,
            )
            mean, low, high = mean_interval(diffs)
            result["paired_net_differences_candidate_minus_comparator"][regime][comparator] = {
                "mean": mean,
                "ci95_low": low,
                "ci95_high": high,
            }
    null_rows = (
        [by_key[("F0_null", seed, CANDIDATE)] for seed in seeds] if "F0_null" in regimes else []
    )
    if null_rows:
        promoted = sum(int(row["n_promotions"] > 0) for row in null_rows)
        result["candidate_null_diagnostic"] = {
            "episodes_with_any_promotion": promoted,
            "episodes": len(null_rows),
            "rate": promoted / len(null_rows),
            "wilson95": wilson(promoted, len(null_rows)),
            "episodes_with_multiple_promotions": sum(
                int(row["n_promotions"] > 1) for row in null_rows
            ),
            "interpretation": "pilot diagnostic only; 20 seeds do not validate nominal alpha",
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
