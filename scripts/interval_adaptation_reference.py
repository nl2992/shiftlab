"""Execute a Gaussian interval-score reference for a single abrupt variance shift."""

import argparse
from pathlib import Path

import pandas as pd
import yaml
from scipy.stats import norm

from shiftlab.data.cli import generate
from shiftlab.data.provenance import commit, sha256, source_hash, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.adaptation import (
    gaussian_interval_score_expectation,
    interval_recalibration_reference,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default="configs/data/synthetic/adaptation_interval_stress.yaml"
    )
    parser.add_argument("--report-dir", default="data/reports/evaluator_only/adaptation_interval")
    args = parser.parse_args()
    config = SyntheticConfig.model_validate(yaml.safe_load(Path(args.config).read_text()))
    if config.scenario != "target_variance" or config.pattern != "abrupt":
        parser.error("Reference requires target_variance with an abrupt schedule")
    dataset = generate(config)
    oracle = pd.read_parquet(dataset / "evaluator_only/oracle.parquet")
    sigma = oracle.sigma.to_numpy()
    baseline_sigma = config.noise
    shifted_sigma = config.noise * (1 + config.severity)
    alpha = 0.1
    nominal_z = float(norm.ppf(1 - alpha / 2))
    stale_radius = nominal_z * baseline_sigma
    recalibrated_radius = nominal_z * shifted_sigma
    stale_score = gaussian_interval_score_expectation(sigma, stale_radius, alpha)
    recalibrated_score = gaussian_interval_score_expectation(sigma, recalibrated_radius, alpha)
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for horizon in (10, 100):
        reference = interval_recalibration_reference(
            stale_score,
            recalibrated_score,
            horizon=horizon,
            update_cost=0.5,
            resource_cost=2,
            remaining_budget=3,
            deployment_delay=2,
            transient_penalties=[1.0, 0.5],
        )
        path = report / f"interval-horizon-{horizon}.csv"
        reference.to_csv(path, index=False)
        actions = reference.oracle_action.value_counts().to_dict()
        summaries[str(horizon)] = {
            "rows": len(reference),
            "oracle_actions": actions,
            "mean_hold_expected_score": float(reference.hold_expected_interval_score.mean()),
            "mean_recalibrated_expected_score": float(
                reference.recalibrated_expected_interval_score.mean()
            ),
            "resource_feasible_fraction": float(reference.update_feasible.mean()),
        }
    write_json(
        report / "protocol.json",
        {
            "dataset_version": dataset.name,
            "configuration": config.model_dump(),
            "processing_commit": commit(),
            "source_hash": source_hash(),
            "script_sha256": sha256(Path(__file__)),
            "loss": "Expected central Gaussian Winkler interval score; oracle mean and scale are known.",
            "alpha": alpha,
            "stale_radius": stale_radius,
            "recalibrated_radius": recalibrated_radius,
            "schedule": "One abrupt target-variance change; recalibration candidate is the exact post-change Gaussian radius.",
            "oracle_scope": "Independent-start, one fixed radius recalibration versus hold; horizon truncated at stream end.",
            "deployment_delay": 2,
            "transient_score_penalties": [1.0, 0.5],
            "update_cost_interval_score_units": 0.5,
            "resource_cost": 2,
            "remaining_budget_each_counterfactual": 3,
            "utility_origin": "Imposed interval-score and resource costs; not application-grounded.",
            "observability": "Evaluator-only future score; never a learner input.",
            "summaries": summaries,
            "limitations": [
                "The reference assumes Gaussian residuals and an oracle-centered interval.",
                "Each start is an independent counterfactual with the same remaining budget.",
                "It is not a dynamic controller, fitted recalibration guarantee, or sequential budget allocation policy.",
                "Costs and penalties are imposed research controls.",
            ],
        },
    )
    for horizon_key, result in summaries.items():
        print(
            f"horizon={horizon_key} actions={result['oracle_actions']} "
            f"mean_hold={result['mean_hold_expected_score']:.3f} "
            f"mean_recalibrated={result['mean_recalibrated_expected_score']:.3f}"
        )
    print("data/reports/evaluator_only/adaptation_interval")


if __name__ == "__main__":
    main()
