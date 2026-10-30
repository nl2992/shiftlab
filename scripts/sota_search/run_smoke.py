"""Run registered synthetic-only infrastructure smoke experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

from shiftlab.sota_search.supervisor import Limits, run_batch
from shiftlab.sota_search.budget import ProgrammeBudget, ProgrammeLimits


def main():
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    dirty = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            "src",
            "scripts/sota_search",
            "configs/sota_search",
            "pyproject.toml",
            "uv.lock",
        ],
        cwd=repo,
        encoding="utf-8",
    )
    if dirty.strip():
        raise RuntimeError("commit research source before launching a registered batch")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    files = sorted((repo / "src/shiftlab/sota_search").glob("*.py")) + [
        repo / "src/shiftlab/dive/eprocess.py",
        repo / "src/shiftlab/dive/prediction_powered_evalues.py",
        Path(__file__).resolve(),
        repo / "configs/sota_search/resource_budget.json",
    ]
    source = hashlib.sha256()
    for path in files:
        source.update(str(path.relative_to(repo)).encode())
        source.update(path.read_bytes())
    limits = Limits(**json.loads((repo / "configs/sota_search/resource_budget.json").read_text()))
    jobs = []
    for method in ("ppe", "ipw"):
        for risk in (0.2, 0.5):
            for seed in range(271000, 271003):
                jobs.append(
                    {
                        "metadata": {
                            "parent_algorithm": "PPE" if method == "ppe" else "bounded_betting",
                            "candidate_algorithm": method,
                            "modification_id": "infrastructure_smoke",
                            "component_configuration": {"horizon": 512, "feedback": "immediate"},
                            "hyperparameters": {"stake": 0.08, "threshold": 0.2},
                            "generator_family": "iid_bernoulli_diagnostic",
                            "shift_type": "stationary_null"
                            if risk == 0.2
                            else "stationary_alternative",
                            "shift_magnitude": 0,
                            "predictive_degradation": risk - 0.2,
                            "decision_harm": None,
                            "proxy_quality": "constant_nominal",
                            "delay_model": "immediate",
                            "label_budget": {"expected_fraction": 0.2},
                            "cost_configuration": {"label": 1},
                            "random_seed": seed,
                            "code_commit": commit,
                            "source_hash": source.hexdigest(),
                            "baseline_version": "local_repository_adapter_v1",
                            "validity_status": "diagnostic_only",
                            "environment": {
                                "python": platform.python_version(),
                                "platform": platform.platform(),
                                "packages": {
                                    name: version(name) for name in ("numpy", "scipy", "psutil")
                                },
                            },
                        },
                        "argv": [
                            "-m",
                            "shiftlab.sota_search.smoke_worker",
                            "--method",
                            method,
                            "--risk",
                            str(risk),
                            "--seed",
                            str(seed),
                        ],
                    }
                )
    programme = ProgrammeBudget(
        repo / "outputs/sota_search",
        ProgrammeLimits(
            **json.loads((repo / "configs/sota_search/programme_budget.json").read_text())
        ),
    )
    try:
        programme.import_previous(
            default_wall=limits.run_wall_seconds, default_cpu=limits.run_cpu_seconds
        )
        results = run_batch(args.output, jobs, limits, repo, programme=programme)
    finally:
        programme.close()
    counts = {}
    for row in results:
        status = row["execution_status"]
        counts[status] = counts.get(status, 0) + 1
    print(json.dumps({"output": str(args.output), "status_counts": counts}))


if __name__ == "__main__":
    main()
