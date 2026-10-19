"""Execute fitted, learner-only decision diagnostics over the named stress presets."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

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
    for preset in presets:
        for seed in seeds:
            records.extend(evaluate_fitted_decision_preset(preset, seed=seed))

    summary = []
    for preset_name in sorted({row["preset"] for row in records}):
        for regime in ["all", "baseline", "shifted"]:
            rows = [
                row for row in records if row["preset"] == preset_name and row["regime"] == regime
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
                    "regime": regime,
                    "replicates": len(rows),
                    **{
                        f"mean_{field}": float(np.mean([row[field] for row in rows]))
                        for field in fields
                    },
                }
            )

    report = {
        "description": "Five-seed fitted binary-policy diagnostics on ten named synthetic presets plus a hidden-utility impossibility diagnostic.",
        "fit_protocol": "A frozen standardized logistic regression is fit on training-partition binary outcomes whose labels arrived before the first test request; test outcomes and evaluator oracle data are excluded from fitting.",
        "decision_protocol": "Actions use only fitted event probabilities and per-request declared false-positive/false-negative costs and feasibility. When context is missing, a symmetric unit-cost fallback is used and reported.",
        "replicates_per_preset": len(seeds),
        "named_preset_count": len(presets) - 1,
        "supplemental_diagnostic": "hidden_utility_unobserved",
        "n_per_seed": 12000,
        "utility_status": "Imposed research objectives, not application-grounded cost estimates.",
        "records": records,
        "summary": summary,
        "limitations": [
            "This is one frozen logistic policy class, not a comparison of the three target papers' algorithms.",
            "Seed-level results are descriptive; no across-seed confidence intervals are claimed.",
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
                f"{row['preset']}: fitted regret={row['mean_mean_decision_regret']:.4f} "
                f"Brier={row['mean_brier_score']:.5f}"
            )
    print(output)


if __name__ == "__main__":
    main()
