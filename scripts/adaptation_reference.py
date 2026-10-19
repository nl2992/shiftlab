"""Execute a restricted full-information reference for the Gaussian coefficient-shift DGP."""

import argparse
from pathlib import Path

import pandas as pd
import yaml

from shiftlab.data.cli import generate
from shiftlab.data.provenance import commit, source_hash, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.adaptation import intervention_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--report-dir", default="data/reports/evaluator_only/adaptation")
    args = parser.parse_args()
    config = SyntheticConfig.model_validate(yaml.safe_load(Path(args.config).read_text()))
    if config.scenario != "concept":
        parser.error("Analytic reference requires the concept DGP with IID unit-variance features")
    directory = generate(config)
    oracle = pd.read_parquet(directory / "evaluator_only/oracle.parquet")
    weight = oracle.weight.to_numpy()
    # Fixed predictors beta0=1 (stale) and beta0=1-severity (updated).
    # Other coefficients agree. Integrate (beta0-beta_true)^2 over X0~N(0,1).
    stale = config.noise**2 + (config.severity * weight) ** 2
    updated = config.noise**2 + (config.severity * (1 - weight)) ** 2
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    for horizon in [10, 100]:
        reference = intervention_reference(
            stale,
            updated,
            horizon=horizon,
            update_cost=5,
            resource_cost=2,
            remaining_budget=3,
            deployment_delay=2,
            transient_penalties=[4, 2, 1],
        )
        reference.to_csv(report / f"horizon-{horizon}.csv", index=False)
    write_json(
        report / "protocol.json",
        {
            "dataset_version": directory.name,
            "configuration": config.model_dump(),
            "processing_commit": commit(),
            "source_hash": source_hash(),
            "oracle_scope": "independent-start, one fixed updated predictor versus fixed stale predictor",
            "risk": "analytical Gaussian feature-integrated MSE; not fitted-model test error",
            "stale_coefficient_0": 1.0,
            "updated_coefficient_0": 1 - config.severity,
            "loss_cost": 5,
            "resource_cost": 2,
            "remaining_budget_each_counterfactual": 3,
            "deployment_delay": 2,
            "transient_expected_loss_penalties": [4, 2, 1],
            "utility_origin": "synthetically imposed cumulative squared-loss and resource units",
            "observability": "evaluator-only future risk; never a learner input",
            "adversary": "ex ante changes one step after reviews at multiples of review_period; no action access",
        },
    )
    print(report)


if __name__ == "__main__":
    main()
