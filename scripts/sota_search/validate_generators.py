"""Run the preregistered development-only generator validation batch."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from shiftlab.sota_search.budget import ProgrammeBudget, ProgrammeLimits
from shiftlab.sota_search.generators import FAMILIES, SCENARIOS, WorldConfig
from shiftlab.sota_search.provenance import archive_source, source_provenance
from shiftlab.sota_search.supervisor import Limits, run_batch


def main():
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    archive_root = repo / "outputs/sota_search"
    if output.parent != archive_root.resolve() or output.exists():
        raise ValueError("output must be a new direct child of outputs/sota_search")
    provenance, files = source_provenance(repo)
    limits = Limits(**json.loads((repo / "configs/sota_search/resource_budget.json").read_text()))
    programme = ProgrammeBudget(
        archive_root,
        ProgrammeLimits(
            **json.loads((repo / "configs/sota_search/programme_budget.json").read_text())
        ),
    )
    programme.import_previous(
        default_wall=limits.run_wall_seconds, default_cpu=limits.run_cpu_seconds
    )
    jobs = []
    for family in FAMILIES:
        for scenario in SCENARIOS:
            seed = 281001
            config = WorldConfig(
                family=family,
                scenario=scenario,
                horizon=512,
                delay=3,
                delay_model="independent_random",
            )
            jobs.append(
                {
                    "metadata": {
                        **provenance,
                        "parent_algorithm": None,
                        "candidate_algorithm": "generator_contract",
                        "modification_id": None,
                        "component_configuration": asdict(config),
                        "hyperparameters": {},
                        "generator_family": family,
                        "shift_type": scenario,
                        "shift_magnitude": config.severity,
                        "predictive_degradation": None,
                        "decision_harm": None,
                        "proxy_quality": config.proxy_quality,
                        "delay_model": config.delay_model,
                        "label_budget": {"hard_label_count": 64},
                        "cost_configuration": {
                            "label_cost": 2
                            if scenario == "labels_too_expensive"
                            else config.label_cost,
                            "switch_cost": config.switch_cost,
                        },
                        "random_seed": seed,
                        "baseline_version": "generator_contract_v1",
                        "validity_status": "diagnostic_only",
                        "provenance_class": "ORACLE_ONLY",
                    },
                    "argv": [
                        "-m",
                        "shiftlab.sota_search.generator_worker",
                        "--family",
                        family,
                        "--scenario",
                        scenario,
                        "--seed",
                        str(seed),
                        "--horizon",
                        "512",
                    ],
                }
            )
    try:
        results = run_batch(output, jobs, limits, repo, programme=programme)
        archive_source(output / "executed_source.zip", repo, files)
        with (output / "programme_usage_after.json").open("x", encoding="utf-8") as stream:
            json.dump(programme.usage(), stream, indent=2)
        print(
            json.dumps(
                {
                    "attempts": len(results),
                    "completed": sum(row["execution_status"] == "completed" for row in results),
                    "programme_usage": programme.usage(),
                }
            )
        )
    finally:
        programme.close()


if __name__ == "__main__":
    main()
