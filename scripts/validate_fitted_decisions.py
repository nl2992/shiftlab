"""Execute fitted, learner-only decision diagnostics over the named stress presets."""

import json
from collections import Counter
from dataclasses import replace
from itertools import product
from pathlib import Path

import numpy as np

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now
from shiftlab.data.synthetic import decision_stress_catalogue
from shiftlab.data.synthetic.fitted_decisions import evaluate_fitted_decision_preset


def main() -> None:
    seeds = [31, 43, 59, 71, 89]
    records = []
    presets = list(decision_stress_catalogue(seed=seeds[0], n=12000))
    template = presets[0]
    presets.append(
        replace(
            template,
            name="hidden_utility_unobserved",
            config=template.config.model_copy(update={"scenario": "hidden_cost", "severity": 1.0}),
            policy_class="Frozen binary logistic policy with generic fallback utility",
            loss="Evaluator-only regime-varying FN cost, undisclosed to the learner",
            oracle_policy="Cost-sensitive action using the hidden true cost and event probability",
            learner_visible_context="No decision_context; learner must use the explicit symmetric unit-cost fallback.",
            expected_relation="Identical learner inputs can have different utility-optimal actions.",
        )
    )
    policy_classes = ["logistic", "random_forest", "shallow_tree"]
    for preset in presets:
        for policy_class in policy_classes:
            for seed in seeds:
                records.extend(
                    evaluate_fitted_decision_preset(preset, seed=seed, policy_class=policy_class)
                )

    expected_grid = set(product([preset.name for preset in presets], policy_classes, seeds))
    observed_counts = Counter((row["preset"], row["policy_class"], row["seed"]) for row in records)
    observed_grid = set(observed_counts)
    missing_grid = sorted(expected_grid - observed_grid)
    duplicate_grid = sorted(key for key, count in observed_counts.items() if count != 3)
    unexpected_grid = sorted(observed_grid - expected_grid)
    replication_check = {
        "expected_preset_policy_seed_cells": len(expected_grid),
        "observed_preset_policy_seed_cells": len(observed_grid),
        "expected_regime_rows_per_cell": 3,
        "missing_cells": missing_grid,
        "cells_with_wrong_regime_row_count": duplicate_grid,
        "unexpected_cells": unexpected_grid,
        "passes": not missing_grid and not duplicate_grid and not unexpected_grid,
    }
    metric_fields = [
        "brier_score",
        "mean_realized_cost",
        "mean_fitted_expected_cost",
        "mean_oracle_expected_cost",
        "mean_decision_regret",
    ]
    metric_rows_valid = all(
        row["n_test"] > 0
        and all(np.isfinite(row[field]) for field in metric_fields)
        and 0 <= row["brier_score"] <= 1
        for row in records
    )
    checks_pass = replication_check["passes"] and metric_rows_valid

    summary = []
    for preset_name in sorted({row["preset"] for row in records}):
        for policy_class in policy_classes:
            for regime in ["all", "baseline", "shifted"]:
                rows = [
                    row
                    for row in records
                    if row["preset"] == preset_name
                    and row["regime"] == regime
                    and row["policy_class"] == policy_class
                ]
                if not rows:
                    continue
                fields = [
                    "n_train",
                    "n_test",
                    "training_positive_rate",
                    "test_positive_rate",
                    "fitted_action_rate",
                    "oracle_action_rate",
                    "brier_score",
                    "mean_realized_cost",
                    "mean_fitted_expected_cost",
                    "mean_oracle_expected_cost",
                    "mean_decision_regret",
                    "mean_actual_fn_cost",
                    "mean_policy_fn_cost",
                    "fraction_using_declared_context",
                ]
                summary.append(
                    {
                        "preset": preset_name,
                        "policy_class": policy_class,
                        "regime": regime,
                        "replicates": len(rows),
                        **{
                            f"mean_{field}": float(np.mean([row[field] for row in rows]))
                            for field in fields
                        },
                        **{
                            f"sd_{field}": float(np.std([row[field] for row in rows], ddof=1))
                            for field in fields
                        },
                    }
                )

    report = {
        "description": "Five-seed comparison of three frozen fitted binary-policy classes on ten named synthetic presets plus a hidden-utility impossibility diagnostic. Summary standard deviations describe across-seed spread and are not confidence intervals.",
        "fit_protocol": "A standardized logistic regression, a fixed 200-tree random forest and a depth-4 decision tree are independently fit on training-partition binary outcomes whose labels arrived before the first test request; test outcomes and evaluator oracle data are excluded from fitting. Hyperparameters are fixed a priori, with no test-set tuning.",
        "decision_protocol": "Actions use only fitted event probabilities and per-request declared false-positive/false-negative costs and feasibility. When context is missing, a symmetric unit-cost fallback is used and reported.",
        "replicates_per_preset": len(seeds),
        "named_preset_count": len(presets) - 1,
        "supplemental_diagnostic": "hidden_utility_unobserved",
        "n_per_seed": 12000,
        "utility_status": "Imposed research objectives, not application-grounded cost estimates.",
        "records": records,
        "summary": summary,
        "replication_check": replication_check,
        "metric_rows_valid": metric_rows_valid,
        "checks_pass": checks_pass,
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "These are three baseline fitted policy classes, not implementations or comparisons of the three target papers' algorithms.",
            "Across-seed sample standard deviations are descriptive and do not account for shared preset structure or justify confidence-interval claims.",
            "Oracle expected cost uses evaluator-only conditional event probabilities and is a reference, not a learner input.",
            "The fallback utility in cases with hidden or absent decision context is deliberately generic; resulting regret includes utility non-identifiability.",
        ],
    }
    output = Path("data/reports/fitted_decision_validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for row in summary:
        if row["regime"] == "all":
            print(
                f"{row['preset']} ({row['policy_class']}): "
                f"fitted regret={row['mean_mean_decision_regret']:.4f} "
                f"Brier={row['mean_brier_score']:.5f}"
            )
    print(output)
    if not checks_pass:
        raise SystemExit("Fitted-decision validation checks failed; inspect the JSON report.")


if __name__ == "__main__":
    main()
