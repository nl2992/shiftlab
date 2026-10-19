"""CLI for bounded acquisition, generation, validation and real-execution reports."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .catalogue import SOURCES
from .gpu.environment import environment
from .schemas import SyntheticConfig
from .storage import save_dataset
from .synthetic import SCENARIOS, generate_chunks
from .synthetic.generators import schedule
from .synthetic.oracle_spec import oracle_spec
from .validation import validate_all


def generate(config: SyntheticConfig):
    if config.device == "auto":
        config = config.model_copy(
            update={"device": "cuda" if environment()["cuda_available"] else "cpu"}
        )
    weights, truth = schedule(config)
    oracle = {
        **truth,
        "configuration": config.model_dump(),
        "mathematical_definition": SCENARIOS[config.scenario],
        "structured_oracle_specification": oracle_spec(config, weights, truth),
        "rng": "NumPy PCG64 or torch CUDA generator; seeded by config; chunk size part of identity",
        "initial_numpy_states": {
            str(seed): np.random.default_rng(seed).bit_generator.state
            for seed in [config.seed, config.seed + 701, config.seed + 900, config.seed + 901]
        },
        "oracle_observability": "full DGP regime, not necessarily learner-conditional",
        "intervention_oracle": "No dynamic optimal controller implemented. The separate synthetic.adaptation.intervention_reference compares one fixed candidate update against holding using evaluator-only future expected losses, costs, deployment delay and transient penalties; scripts/adaptation_reference.py executes its Gaussian concept-shift reference. It is not a learned-policy or sample-fitted refitting guarantee.",
        "causality": "exogenous; performative environments use a separate interactive interface",
    }
    provenance = {
        "publisher": "ShiftLab",
        "source_url": "local://shiftlab/data/synthetic",
        "citation": "ShiftLab synthetic specification v1",
        "license": "MIT",
        "permitted_use": "Research and reuse under MIT",
        "environment": environment(),
        "limitations": [
            "Research-imposed utilities.",
            "Oracle quantiles are DGP conditional or marginal as labelled; not a guarantee for a fitted model.",
            "Dependence scenarios require dependence-aware inference.",
        ],
    }
    return save_dataset(
        generate_chunks(config),
        config.scenario,
        config.output,
        provenance,
        config.model_dump(),
        "synthetic_known",
        oracle,
    )


def _main(command=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data")
    parser.add_argument("--config")
    parser.add_argument("--dataset", choices=list(SOURCES))
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"])
    parser.add_argument(
        "--execute", action="store_true", help="Explicitly allow network acquisition"
    )
    args = parser.parse_args()
    root = Path(args.root)
    configuration = yaml.safe_load(Path(args.config).read_text()) if args.config else {}
    if command == "inventory":
        rows = [{"dataset": name, **value} for name, value in SOURCES.items()]
        rows.extend(
            {
                "dataset": name,
                "status": "synthetic_implemented",
                "timing": "simulation index",
                "definition": definition,
            }
            for name, definition in SCENARIOS.items()
        )
        pointers = [json.loads(p.read_text()) for p in root.glob("manifests/*.json")]
        for row in rows:
            versions = [p for p in pointers if p["dataset"] == row["dataset"]]
            row["acquired_versions"] = len(versions)
            row["acquired_rows_latest"] = (
                max(versions, key=lambda p: p["acquired_at"])["n_observations"] if versions else 0
            )
        root.joinpath("reports").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(root / "reports/data_inventory.csv", index=False)
        print(root / "reports/data_inventory.csv")
    elif command == "generate":
        suite = configuration.pop("scenarios", None)
        seeds = configuration.pop("seeds", None)
        if args.device:
            configuration["device"] = args.device
        configuration["output"] = str(root)
        base = SyntheticConfig.model_validate(configuration)
        for scenario in suite or [base.scenario]:
            for seed in seeds or [base.seed]:
                c = SyntheticConfig.model_validate(
                    {**base.model_dump(), "scenario": scenario, "seed": seed}
                )
                print(generate(c), flush=True)
    elif command == "download":
        if not args.dataset:
            parser.error("--dataset is required")
        if not args.execute:
            print(
                json.dumps(
                    {
                        "dry_run": True,
                        "source": SOURCES[args.dataset],
                        "configuration": configuration,
                        "next_step": "Add --execute to acquire under the source terms",
                    },
                    indent=2,
                )
            )
        else:
            from .real.adapters import acquire

            print(acquire(args.dataset, configuration, root))
    elif command == "validate":
        results = validate_all(root)
        print(json.dumps(results, indent=2))
        if any("error" in row for row in results):
            raise SystemExit(1)
    elif command == "report":
        from .report import build_report

        print(build_report(root))
    elif command == "benchmark":
        from .gpu.benchmarks import benchmark

        print(benchmark(root, configuration))
    else:
        raise ValueError(f"Unknown command {command}")


def main(command=None):
    import requests

    try:
        _main(command)
    except (ValueError, RuntimeError, OSError, KeyError, requests.RequestException) as exc:
        raise SystemExit(f"Data command failed: {exc}") from None
