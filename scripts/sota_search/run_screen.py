"""Preregistered 540-configuration first-stage development screen."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from shiftlab.sota_search.adapters import AdapterConfig
from shiftlab.sota_search.budget import ProgrammeBudget, ProgrammeLimits
from shiftlab.sota_search.generators import FAMILIES, WorldConfig
from shiftlab.sota_search.provenance import archive_source, source_provenance
from shiftlab.sota_search.supervisor import Limits, run_batch


def configurations():
    variants = {
        "Q1": [
            ("direct", "uniform"),
            ("ppe", "uniform"),
            ("multiscale", "uniform"),
            ("reliable", "uniform"),
            ("ppe", "variance"),
            ("ppe", "robust"),
            ("ppe", "growth"),
            ("ppe", "mixed"),
            ("ppe", "paced"),
        ],
        "Q2": [
            ("direct", "uniform"),
            ("ppe", "uniform"),
            ("multiscale", "uniform"),
            ("reliable", "uniform"),
            ("ppe", "variance"),
            ("ppe", "robust"),
            ("ppe", "growth"),
            ("ppe", "mixed"),
            ("ppe", "paced"),
        ],
        "Q3": [
            ("frozen", "uniform"),
            ("greedy", "uniform"),
            ("hysteresis", "uniform"),
            ("certified", "uniform"),
            ("reversal", "uniform"),
            ("cams_inspired", "uniform"),
            ("reversal", "robust"),
            ("reversal", "mixed"),
            ("reversal", "paced"),
        ],
    }
    scenarios = [
        "stationary",
        "benign_covariate",
        "harmful_concept",
        "transient_challenger",
        "harm_without_accuracy",
    ]
    for track, methods in variants.items():
        for family in FAMILIES:
            for index, scenario in enumerate(scenarios):
                for method, query in methods:
                    yield {
                        "world": asdict(
                            WorldConfig(
                                family=family,
                                scenario=scenario,
                                horizon=512,
                                delay=3,
                                delay_model="independent_random",
                                proxy_quality="stale",
                            )
                        ),
                        "adapter": asdict(AdapterConfig(track=track, method=method, query=query)),
                        "seed": 291000 + index,
                        "source_seed": 391000 + index,
                    }


def main():
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = repo / "outputs/sota_search"
    if args.output.resolve().parent != root.resolve():
        raise ValueError("screen output must be a direct programme archive child")
    provenance, files = source_provenance(repo)
    limits = Limits(**json.loads((repo / "configs/sota_search/resource_budget.json").read_text()))
    programme = ProgrammeBudget(
        root,
        ProgrammeLimits(
            **json.loads((repo / "configs/sota_search/programme_budget.json").read_text())
        ),
    )
    jobs = []
    for config in configurations():
        adapter, world = config["adapter"], config["world"]
        jobs.append(
            {
                "metadata": {
                    **provenance,
                    "parent_algorithm": "PPE_or_bounded_paired_betting",
                    "candidate_algorithm": adapter["method"],
                    "modification_id": adapter["query"],
                    "component_configuration": config,
                    "hyperparameters": adapter,
                    "generator_family": world["family"],
                    "shift_type": world["scenario"],
                    "shift_magnitude": world["severity"],
                    "proxy_quality": world["proxy_quality"],
                    "delay_model": world["delay_model"],
                    "label_budget": {"fraction": adapter["budget_fraction"], "source_labels": 512},
                    "cost_configuration": {
                        "label": world["label_cost"],
                        "switch": world["switch_cost"],
                    },
                    "random_seed": config["seed"],
                    "baseline_version": "core_streaming_v1",
                    "validity_status": "uncalibrated_development_only",
                    "provenance_class": "LOCAL_HEURISTIC_composition_of_audited_components",
                },
                "argv": [
                    "-m",
                    "shiftlab.sota_search.search_worker",
                    "--configuration",
                    json.dumps(config),
                ],
            }
        )
    try:
        programme.import_previous(
            default_wall=limits.run_wall_seconds, default_cpu=limits.run_cpu_seconds
        )
        results = run_batch(args.output, jobs, limits, repo, programme=programme)
        archive_source(args.output / "executed_source.zip", repo, files)
        summary = {
            "attempts": len(results),
            "completed": sum(row["execution_status"] == "completed" for row in results),
            "programme_usage": programme.usage(),
        }
        with (args.output / "batch_summary.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, indent=2)
        print(json.dumps(summary))
    finally:
        programme.close()


if __name__ == "__main__":
    main()
