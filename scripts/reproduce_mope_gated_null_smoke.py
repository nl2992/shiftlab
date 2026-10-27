"""Smoke-test the authors' MOPE gated-deployment code on its IID null contract.

This is an implementation check, not a calibration or efficacy experiment.
The official source is expected at ``tmp/mope_reference`` and is pinned by
commit hash below. Install its legacy runtime dependencies ephemerally with:

    uv run --with numba --with cvxpy --with tqdm python \\
      scripts/reproduce_mope_gated_null_smoke.py
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"
DEFAULT_REPO = ROOT / "tmp/mope_reference"
DEFAULT_OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/mope_gated_null_smoke_30"
DEFAULT_SEEDS = 30
DEFAULT_N = 200
ALPHA = 0.05
BEHAVIOR = np.array([0.5, 0.5], dtype=np.float64)
TARGET = np.array([0.2, 0.8], dtype=np.float64)
REWARD_MEAN = np.array([0.4, 0.4], dtype=np.float64)
W_MIN = 0.4
W_MAX = 1.6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_official_mope(repo: Path) -> tuple[Any, str]:
    if not (repo / ".git").exists():
        raise FileNotFoundError(
            f"Clone https://github.com/n17s/mope at {EXPECTED_MOPE_COMMIT} into {repo}"
        )
    revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != EXPECTED_MOPE_COMMIT:
        raise RuntimeError(f"Expected MOPE commit {EXPECTED_MOPE_COMMIT}, found {revision}")
    sys.path.insert(0, str(repo))
    tqdm = importlib.import_module("tqdm")
    tqdm.tqdm = lambda iterable, **_kwargs: iterable
    module = importlib.import_module("opebetrp")
    return module.wealth_lb_gd, revision


def make_null_stream(seed: int, n: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    actions = rng.choice(2, size=n, p=BEHAVIOR)
    weights = TARGET[actions] / BEHAVIOR[actions]
    rewards = rng.binomial(1, REWARD_MEAN[actions]).astype(np.float64)
    return np.column_stack((weights, rewards))


def run(repo: Path, output: Path, seeds: int, n: int, seed_offset: int) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    gated_cs, revision = load_official_mope(repo)
    # Suppress only tqdm's progress display; the author's numerical routine is
    # called unchanged.
    violations = 0
    promotions = 0
    final_widths: list[float] = []
    final_lowers: list[float] = []
    final_uppers: list[float] = []
    for offset in range(seeds):
        data = make_null_stream(seed_offset + offset, n)
        lower, upper = gated_cs(data, W_MIN, W_MAX, ALPHA)
        lower = np.asarray(lower, dtype=np.float64)
        upper = np.asarray(upper, dtype=np.float64)
        if lower.shape != (n,) or upper.shape != (n,):
            raise RuntimeError("MOPE returned a confidence-sequence path with the wrong length")
        if not np.isfinite(lower).all() or not np.isfinite(upper).all():
            raise RuntimeError("MOPE returned a non-finite confidence bound")
        if np.any(lower > upper + 1e-10):
            raise RuntimeError("MOPE returned an inverted confidence interval")
        violations += int(np.any(lower > 0) or np.any(upper < 0))
        promotions += int(np.any(lower > 0))
        final_widths.append(float(upper[-1] - lower[-1]))
        final_lowers.append(float(lower[-1]))
        final_uppers.append(float(upper[-1]))

    source_files = [repo / "opebetrp.py", repo / "opebet.py", repo / "LICENSE"]
    result = {
        "schema_version": "1.0.0",
        "status": "iid_null_smoke_only_not_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "MOPE / official gated-deployment confidence sequence",
        "source": {
            "repository": "https://github.com/n17s/mope",
            "commit": revision,
            "license": "MIT",
            "file_sha256": {path.name: sha256(path) for path in source_files},
        },
        "protocol": {
            "purpose": "exercise the unmodified official gated-deployment routine on a known IID null",
            "seeds": seeds,
            "seed_offset": seed_offset,
            "events_per_seed": n,
            "alpha": ALPHA,
            "behavior_probabilities": BEHAVIOR.tolist(),
            "target_probabilities": TARGET.tolist(),
            "known_importance_weight_support": [W_MIN, W_MAX],
            "reward_probability_by_action": REWARD_MEAN.tolist(),
            "true_target_minus_behavior_value": 0.0,
            "cpu_only_reason": "the reference implementation uses NumPy, SciPy, and Numba CPU code",
        },
        "results": {
            "cs_containment_failures": violations,
            "false_promotions": promotions,
            "mean_final_width": float(np.mean(final_widths)),
            "mean_final_lower": float(np.mean(final_lowers)),
            "mean_final_upper": float(np.mean(final_uppers)),
        },
        "limitations": [
            "This small IID synthetic run is an execution and arithmetic smoke check, not a type-I calibration.",
            "It does not test dependent contexts, delayed/selective feedback, adaptive policy selection, or OBD.",
            "The comparison is policy-value improvement under logged bandit feedback, not a generic paired-cost harm monitor.",
        ],
    }
    manifest = output / "manifest.json"
    manifest.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed-offset", type=int, default=2026102600)
    args = parser.parse_args()
    if args.seeds < 1 or args.n < 1:
        parser.error("--seeds and --n must be positive")
    result = run(args.repo, args.output, args.seeds, args.n, args.seed_offset)
    print(
        json.dumps(
            {
                "status": result["status"],
                **result["results"],
                "manifest": str(args.output / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
