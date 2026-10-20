"""Export checks of realized synthetic regime schedules and temporal intervals."""

from pathlib import Path

import numpy as np

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.generators import schedule

PATTERNS = [
    "abrupt",
    "multiple",
    "linear",
    "sigmoid",
    "recurring",
    "hmm",
    "seasonal",
    "temporary",
    "variable_dwell",
    "oblivious_adversarial",
]
SEEDS = [11, 23, 37, 53, 71]


def _longest_run(values: np.ndarray) -> int:
    if not len(values):
        return 0
    boundaries = np.r_[0, np.flatnonzero(np.diff(values) != 0) + 1, len(values)]
    return int(np.diff(boundaries).max())


def evaluate() -> dict:
    n, tau, width, regimes, review_period = 30000, 12000, 600, 5, 100
    records = []
    summaries = {}
    for pattern in PATTERNS:
        group = []
        for seed in SEEDS:
            config = SyntheticConfig(
                n=n,
                scenario="concept",
                seed=seed,
                pattern=pattern,
                regimes=regimes,
                review_period=review_period,
                change_fraction=tau / n,
                transition_fraction=width / n,
            )
            weights, truth = schedule(config)
            actual_changes = (np.flatnonzero(np.diff(weights) != 0) + 1).tolist()
            if pattern in {"linear", "sigmoid"}:
                boundary_check = truth["change_times"] == [] and truth["transition_intervals"] == [
                    [tau, tau + width]
                ]
            elif pattern == "seasonal":
                boundary_check = truth["change_times"] == [] and truth["transition_intervals"] == [
                    [tau, n - 1]
                ]
            else:
                boundary_check = truth["change_times"] == actual_changes
            null_config = config.model_copy(update={"severity": 0})
            null_weights, null_truth = schedule(null_config)
            row = {
                "pattern": pattern,
                "seed": seed,
                "realized_change_indices": truth["change_times"],
                "transition_intervals": truth["transition_intervals"],
                "number_of_weight_changes": len(actual_changes),
                "weight_min": float(weights.min()),
                "weight_max": float(weights.max()),
                "interior_weight_fraction": float(np.mean((weights > 0) & (weights < 1))),
                "longest_constant_dwell_rows": _longest_run(weights),
                "boundaries_match_recorded_truth": bool(boundary_check),
                "zero_strength_is_exact_null": bool(
                    not null_weights.any()
                    and null_truth == {"change_times": [], "transition_intervals": []}
                ),
            }
            if pattern == "hmm":
                row["post_activation_switch_rate"] = float(np.mean(np.diff(weights[tau:]) != 0))
            group.append(row)
        summary = {
            "replicates": len(group),
            "all_boundary_checks_pass": all(
                row["boundaries_match_recorded_truth"] for row in group
            ),
            "all_zero_strength_checks_pass": all(
                row["zero_strength_is_exact_null"] for row in group
            ),
            "mean_number_of_weight_changes": float(
                np.mean([row["number_of_weight_changes"] for row in group])
            ),
            "mean_interior_weight_fraction": float(
                np.mean([row["interior_weight_fraction"] for row in group])
            ),
        }
        if pattern == "hmm":
            expected = 1 / width
            observed = float(np.mean([row["post_activation_switch_rate"] for row in group]))
            tolerance = 5 * np.sqrt(expected * (1 - expected) / (len(SEEDS) * (n - tau)))
            summary.update(
                expected_post_activation_switch_rate=expected,
                observed_post_activation_switch_rate=observed,
                switch_rate_tolerance=float(tolerance),
                switch_rate_check_pass=bool(abs(observed - expected) < tolerance),
            )
        summaries[pattern] = summary
        records.extend(group)
    return {
        "description": "Five-seed schedule diagnostics for ten temporal patterns, including transition intervals and the hidden Markov dwell-rate control.",
        "parameters": {
            "n": n,
            "change_index": tau,
            "transition_width": width,
            "regimes": regimes,
            "review_period": review_period,
            "seeds": SEEDS,
        },
        "records": records,
        "summary": summaries,
        "limitations": [
            "Deterministic schedule formulas are checked independently in tests/data/test_temporal_schedule_properties.py.",
            "The HMM switch-rate tolerance is a finite-sample diagnostic, not a guarantee for each path.",
            "Schedules are simulation indices and do not imply real-source changepoints.",
        ],
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/temporal_pattern_validation.json")
    write_json(output, report)
    for pattern, row in report["summary"].items():
        print(
            f"{pattern}: weight_changes={row['mean_number_of_weight_changes']:.2f} "
            f"interior={row['mean_interior_weight_fraction']:.3f} "
            f"boundaries={row['all_boundary_checks_pass']}"
        )
    print(output)


if __name__ == "__main__":
    main()
