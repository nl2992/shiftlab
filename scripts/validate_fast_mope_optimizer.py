"""Compare the closed-form MOPE optimizer with pinned CVXPY reference code."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from fast_mope_optimizer import solve_gd_exact

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MOPE_REPO = ROOT / "tmp/mope_reference"
EXPECTED_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mope-repo", type=Path, default=DEFAULT_MOPE_REPO)
    parser.add_argument("--cases", type=int, default=250)
    parser.add_argument("--wmax", type=float, default=80.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.cases < 1:
        parser.error("--cases must be positive")
    revision = subprocess.run(
        ["git", "-C", str(args.mope_repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != EXPECTED_COMMIT:
        raise RuntimeError(f"Expected MOPE {EXPECTED_COMMIT}, found {revision}")
    sys.path.insert(0, str(args.mope_repo))
    mope_module: Any = importlib.import_module("opebetrp")
    reference: Any = mope_module.solve_gd
    reference_wealth: Any = mope_module.wealth_lb_gd

    rng = np.random.default_rng(2026102607)
    solution_errors: list[float] = []
    objective_errors: list[float] = []
    infeasible_reference = 0
    wmax = args.wmax
    if wmax <= 1.0:
        parser.error("--wmax must exceed one")
    constraints = np.array(
        [
            [-1.0, 1.0],
            [-1.0, -2.0],
            [wmax - 1.0, -1.0],
            [wmax - 1.0, wmax],
        ],
        dtype=np.float64,
    )
    psi = 2.0 - 4.0 * np.log(2.0)
    for _ in range(args.cases):
        factor = rng.normal(size=(2, 2))
        matrix = factor.T @ factor + np.eye(2) * 10.0 ** rng.uniform(-7.0, 1.0)
        linear = rng.normal(size=2) * 10.0 ** rng.uniform(-2.0, 2.0)
        reference_solution = np.asarray(reference(wmax, matrix, linear), dtype=np.float64)
        exact_solution = solve_gd_exact(wmax, matrix, linear)
        reference_objective = psi * float(reference_solution @ matrix @ reference_solution) + float(
            linear @ reference_solution
        )
        exact_objective = psi * float(exact_solution @ matrix @ exact_solution) + float(
            linear @ exact_solution
        )
        solution_errors.append(float(np.max(np.abs(reference_solution - exact_solution))))
        objective_errors.append(abs(reference_objective - exact_objective))
        infeasible_reference += int(np.any(constraints @ reference_solution < -0.5 - 1e-6))

    import tqdm

    tqdm.tqdm = lambda iterable, **_kwargs: iterable
    path_errors: list[float] = []
    empty_set_mismatches = 0
    path_stream_lengths = [75, 75, 75, 75]
    for stream_index, stream_length in enumerate(path_stream_lengths):
        stream_rng = np.random.default_rng(2026102610 + stream_index)
        weights = stream_rng.choice(
            [0.0, wmax], size=stream_length, p=[1.0 - 1.0 / wmax, 1.0 / wmax]
        )
        rewards = stream_rng.binomial(1, 0.01, size=stream_length).astype(np.float64)
        if stream_index == 0:
            rewards[:] = 0.0
        elif stream_index == 1:
            rewards[weights == wmax] = 1.0
        elif stream_index == 2:
            rewards[weights == wmax] = 0.0
        wr = np.column_stack((weights, rewards))
        reference_lower, reference_upper = reference_wealth(wr, 0.0, wmax, 0.05)
        mope_module.solve_gd = solve_gd_exact
        fast_lower, fast_upper = mope_module.wealth_lb_gd(wr, 0.0, wmax, 0.05)
        mope_module.solve_gd = reference
        reference_lower = np.asarray(reference_lower)
        reference_upper = np.asarray(reference_upper)
        fast_lower = np.asarray(fast_lower)
        fast_upper = np.asarray(fast_upper)
        if not (
            reference_lower.shape == fast_lower.shape == (stream_length,)
            and reference_upper.shape == fast_upper.shape == (stream_length,)
        ):
            raise AssertionError("MOPE path comparison returned an unexpected shape")
        path_errors.extend(
            [
                float(np.max(np.abs(reference_lower - fast_lower))),
                float(np.max(np.abs(reference_upper - fast_upper))),
            ]
        )
        reference_empty = reference_lower > reference_upper + 1e-9
        fast_empty = fast_lower > fast_upper + 1e-9
        empty_set_mismatches += int(not np.array_equal(reference_empty, fast_empty))

    result = {
        "status": "passed"
        if infeasible_reference == 0
        and max(objective_errors) <= 1e-7
        and empty_set_mismatches == 0
        and max(path_errors) <= 2.0e-4
        else "failed",
        "seed": 2026102607,
        "cases": args.cases,
        "wmax": wmax,
        "reference_repository_commit": revision,
        "reference_file_sha256": sha256(args.mope_repo / "opebetrp.py"),
        "fast_solver_file_sha256": sha256(Path(__file__).with_name("fast_mope_optimizer.py")),
        "maximum_absolute_solution_difference": max(solution_errors),
        "maximum_objective_difference": max(objective_errors),
        "infeasible_reference_solution_count": infeasible_reference,
        "confidence_path_comparison": {
            "streams": len(path_stream_lengths),
            "events_per_stream": path_stream_lengths,
            "maximum_lower_or_upper_path_difference": max(path_errors),
            "empty_set_path_mismatches": empty_set_mismatches,
            "tolerance": 2.0e-4,
        },
        "claim_scope": "optimizer equivalence only; not OBD confidence-sequence validity",
    }
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
