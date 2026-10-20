"""Run evaluator-only independent-start adaptation contrasts across temporal schedules."""

import argparse
from pathlib import Path

import pandas as pd
import yaml

from shiftlab.data.cli import generate
from shiftlab.data.provenance import commit, sha256, source_hash, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.adaptation import intervention_reference

SCENARIOS = {
    "long_stationary_late_break": {"pattern": "abrupt", "change_fraction": 0.8, "severity": 2.0},
    "frequent_small_changes": {"pattern": "multiple", "severity": 0.5},
    "rare_large_break": {"pattern": "abrupt", "change_fraction": 0.5, "severity": 3.0},
    "recurring_structure": {"pattern": "recurring", "severity": 1.5},
    "temporary_shock_recovery": {"pattern": "temporary", "severity": 2.0},
    "gradual_degradation": {"pattern": "linear", "severity": 2.0},
    "variable_dwell": {"pattern": "variable_dwell", "severity": 1.5},
    "adversarial_timing": {"pattern": "oblivious_adversarial", "severity": 2.0},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/data/synthetic/adaptation_stress.yaml")
    parser.add_argument(
        "--report-dir", default="data/reports/evaluator_only/adaptation_stress_suite"
    )
    args = parser.parse_args()
    base = SyntheticConfig.model_validate(yaml.safe_load(Path(args.config).read_text()))
    if base.scenario != "concept":
        parser.error("Suite requires concept DGP with IID unit-variance features")
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    rows, summaries, versions = [], [], {}
    for name, overrides in SCENARIOS.items():
        config = base.model_copy(update=overrides)
        dataset = generate(config)
        versions[name] = dataset.name
        oracle = pd.read_parquet(dataset / "evaluator_only/oracle.parquet")
        weight = oracle.weight.to_numpy()
        stale = config.noise**2 + (config.severity * weight) ** 2
        updated = config.noise**2 + (config.severity * (1 - weight)) ** 2
        n = len(stale)
        # Explicitly imposed contrast: variable costs, a tight compute case, and transient harm.
        resource = 1 + (pd.Series(range(n)).to_numpy() % 4 if name == "variable_dwell" else 0)
        budget = (
            1 if name == "variable_dwell" else (0 if name == "long_stationary_late_break" else 3)
        )
        loss_cost = 2.0 if name == "recurring_structure" else 0.5
        for horizon in (10, 100):
            reference = intervention_reference(
                stale,
                updated,
                horizon=horizon,
                update_cost=loss_cost,
                resource_cost=resource,
                remaining_budget=budget,
                deployment_delay=2,
                transient_penalties=[2.0, 1.0],
            )
            reference.insert(0, "scenario", name)
            reference.insert(1, "pattern", config.pattern)
            reference.insert(2, "horizon", horizon)
            rows.append(reference)
            summary = {
                "scenario": name,
                "pattern": config.pattern,
                "horizon": horizon,
                "starts": n,
                "update_count": int(reference.oracle_action.eq("update").sum()),
                "feasible_fraction": float(reference.update_feasible.mean()),
                "mean_net_update_benefit": float(reference.net_update_benefit.mean()),
                "mean_selected_benefit": float(
                    reference.loc[reference.oracle_action.eq("update"), "net_update_benefit"].mean()
                )
                if reference.oracle_action.eq("update").any()
                else 0.0,
                "resource_cost_design": "variable 1-4 units"
                if name == "variable_dwell"
                else "1 unit",
                "remaining_budget_each_independent_start": budget,
                "update_cost_loss_units": loss_cost,
                "transient_penalties_loss_units": [2.0, 1.0],
            }
            summaries.append(summary)
    pd.concat(rows, ignore_index=True).to_csv(report / "independent_starts.csv", index=False)
    pd.DataFrame(summaries).to_csv(report / "summary.csv", index=False)
    write_json(
        report / "protocol.json",
        {
            "dataset_versions": versions,
            "base_configuration": base.model_dump(),
            "scenario_overrides": SCENARIOS,
            "processing_commit": commit(),
            "source_hash": source_hash(),
            "script_sha256": sha256(Path(__file__)),
            "risk": "analytical Gaussian feature-integrated MSE for two fixed coefficient vectors",
            "scope": "evaluator-only single fixed update versus hold at independent start times; horizons truncated at stream end",
            "controls": "deployment delay 2; transient penalties [2,1]; imposed loss and resource costs; tight and variable budgets",
            "limitations": [
                "No interacting or sequential updates, learned controller, fitted predictor, or application-grounded utility.",
                "Each start is independent and receives the same declared remaining budget.",
                "The fixed updated coefficient is not refit as regimes change; Gaussian IID feature assumptions apply.",
                "Feedback-change and interval recalibration require separate loss references.",
            ],
        },
    )
    print(report)


if __name__ == "__main__":
    main()
