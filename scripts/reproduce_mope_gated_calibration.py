"""Calibrate and compare the pinned MOPE gated-deployment confidence sequence.

This is a synthetic IID contextual-bandit comparison. CUDA generates common
stream uniforms; the official MOPE numerical procedure runs unchanged on CPU.
No observation-level artifacts are written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Limit nested BLAS pools before NumPy/SciPy load. The independent reference
# solves run in separate processes, so one BLAS thread per worker avoids
# multiplying each worker into a machine-wide thread pool.
for _thread_env in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_env] = "1"

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

try:
    from scripts.reproduce_mope_gated_null_smoke import (
        DEFAULT_REPO,
        EXPECTED_MOPE_COMMIT,
        load_official_mope,
        sha256,
    )
except ModuleNotFoundError:
    from reproduce_mope_gated_null_smoke import (
        DEFAULT_REPO,
        EXPECTED_MOPE_COMMIT,
        load_official_mope,
        sha256,
    )

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/mope_gated_calibration_protocol_v1.md"
SMOKE_HELPER = ROOT / "scripts/reproduce_mope_gated_null_smoke.py"
DEFAULT_OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/mope_gated_calibration_v1"
METHODS = ("official_mope", "fixed_n_hoeffding")
CELLS = {"zero_mean": 0.50, "positive_gain": 0.75, "negative_gain": 0.25}
REWARD_PROBABILITY = {0: 0.1, 1: 0.9}
BEHAVIOR_ACTION1 = 0.5
TARGET_P_ACTION1 = {0: 0.2, 1: 0.8}
W_MIN, W_MAX = 0.4, 1.6
ALPHA = 0.05
_WORKER_MOPE: Any = None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_cell_streams(uniforms: np.ndarray, context1_probability: float) -> np.ndarray:
    """Map common uniforms to evaluator events `(target/logger weight, reward)`."""
    if uniforms.ndim != 3 or uniforms.shape[-1] != 3:
        raise ValueError("uniforms must have shape (streams, events, 3)")
    if not 0 <= context1_probability <= 1:
        raise ValueError("context probability must be in [0, 1]")
    if not np.isfinite(uniforms).all() or np.any(uniforms < 0) or np.any(uniforms >= 1):
        raise ValueError("uniforms must be finite values in [0, 1)")
    context1 = uniforms[:, :, 0] < context1_probability
    action1 = uniforms[:, :, 1] < BEHAVIOR_ACTION1
    target_probability = np.where(
        context1,
        TARGET_P_ACTION1[1],
        TARGET_P_ACTION1[0],
    )
    action_probability = np.where(action1, target_probability, 1.0 - target_probability)
    weights = action_probability / BEHAVIOR_ACTION1
    rewards = (
        uniforms[:, :, 2] < np.where(action1, REWARD_PROBABILITY[1], REWARD_PROBABILITY[0])
    ).astype(np.float64)
    return np.stack((weights, rewards), axis=-1)


def exact_binomial_interval(
    successes: int, trials: int, confidence: float = 0.95
) -> tuple[float, float]:
    """Two-sided Clopper–Pearson interval for descriptive event rates."""
    tail = (1.0 - confidence) / 2.0
    lower = 0.0 if successes == 0 else float(beta.ppf(tail, successes, trials - successes + 1))
    upper = (
        1.0
        if successes == trials
        else float(beta.ppf(1.0 - tail, successes + 1, trials - successes))
    )
    return lower, upper


def exact_upper(successes: int, trials: int, confidence: float) -> float:
    if successes == trials:
        return 1.0
    return float(beta.ppf(confidence, successes + 1, trials - successes))


def validate_mope_path(lower: np.ndarray, upper: np.ndarray, horizon: int) -> bool:
    """Validate path shape/order and return whether any confidence set is empty."""
    if lower.shape != (horizon,) or upper.shape != (horizon,):
        raise RuntimeError("MOPE returned a confidence path with the wrong length")
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise RuntimeError("MOPE returned a non-finite confidence path")
    if np.any(np.diff(lower) < -1e-10) or np.any(np.diff(upper) > 1e-10):
        raise RuntimeError("MOPE confidence paths were not monotone")
    return bool(np.any(lower > upper + 1e-10))


def _init_mope_worker(repo_path: str) -> None:
    global _WORKER_MOPE
    torch.set_num_threads(1)
    _WORKER_MOPE, revision = load_official_mope(Path(repo_path))
    if revision != EXPECTED_MOPE_COMMIT:
        raise RuntimeError(f"unexpected MOPE source revision: {revision}")


def _evaluate_stream(task: tuple[str, int, int, float, np.ndarray]) -> list[dict[str, Any]]:
    cell, seed, horizon, true_delta, stream = task
    if _WORKER_MOPE is None:
        raise RuntimeError("MOPE worker was not initialized")
    lower, upper = _WORKER_MOPE(stream, W_MIN, W_MAX, ALPHA)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    empty_cs = validate_mope_path(lower, upper, horizon)
    crossings = np.flatnonzero(lower > 0)
    mope_promoted = bool(crossings.size)
    mope_labels = int(crossings[0] + 1) if mope_promoted else horizon
    z = (stream[:, 0] - 1.0) * stream[:, 1]
    hoeffding_radius = (W_MAX - W_MIN) * np.sqrt(np.log(1.0 / ALPHA) / (2.0 * horizon))
    fixed_promoted = bool(z.mean() - hoeffding_radius > 0.0)
    return [
        {
            "cell": cell,
            "seed": seed,
            "method": "official_mope",
            "true_delta": true_delta,
            "promoted": mope_promoted,
            "labels_used": mope_labels,
            "crossing_event": int(crossings[0] + 1) if mope_promoted else None,
            "empty_confidence_set": empty_cs,
        },
        {
            "cell": cell,
            "seed": seed,
            "method": "fixed_n_hoeffding",
            "true_delta": true_delta,
            "promoted": fixed_promoted,
            "labels_used": horizon,
            "crossing_event": horizon if fixed_promoted else None,
            "empty_confidence_set": False,
        },
    ]


def paired_bootstrap_interval(
    differences: np.ndarray, seed: int, replicates: int = 10_000
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, differences.size, size=(replicates, differences.size))
    means = differences[samples].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def run(
    repo: Path,
    output: Path,
    seeds: int,
    horizon: int,
    seed_offset: int,
    device_name: str,
    workers: int,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    if not PROTOCOL.exists():
        raise FileNotFoundError(PROTOCOL)
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(
        "cuda"
        if device_name == "cuda" or (device_name == "auto" and torch.cuda.is_available())
        else "cpu"
    )
    if device.type != "cuda":
        raise RuntimeError("this registered run requires CUDA uniform generation")

    started = time.perf_counter()
    _official_mope, revision = load_official_mope(repo)
    if revision != EXPECTED_MOPE_COMMIT:
        raise RuntimeError(f"unexpected MOPE source revision: {revision}")
    generator = torch.Generator(device=device).manual_seed(seed_offset)
    uniforms_gpu = torch.rand((seeds, horizon, 3), generator=generator, device=device)
    uniforms = uniforms_gpu.cpu().numpy()

    tasks: list[tuple[str, int, int, float, np.ndarray]] = []
    for cell, context1_probability in CELLS.items():
        streams = build_cell_streams(uniforms, context1_probability)
        true_delta = 0.24 * (2.0 * context1_probability - 1.0)
        for index, stream in enumerate(streams):
            tasks.append((cell, seed_offset + index, horizon, true_delta, stream))

    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_mope_worker,
        initargs=(str(repo),),
    ) as executor:
        for completed, stream_rows in enumerate(
            executor.map(_evaluate_stream, tasks, chunksize=1), 1
        ):
            rows.extend(stream_rows)
            if completed % 100 == 0 or completed == len(tasks):
                print(f"completed streams={completed}/{len(tasks)}", flush=True)

    per_stream = pd.DataFrame(rows).sort_values(["cell", "seed", "method"]).reset_index(drop=True)
    alpha_upper = 1.0 - 0.05 / 7
    summary_rows = []
    for (cell, method), frame in per_stream.groupby(["cell", "method"], sort=True):
        promotions = int(frame["promoted"].sum())
        lo, hi = exact_binomial_interval(promotions, len(frame))
        summary_rows.append(
            {
                "cell": cell,
                "method": method,
                "streams": len(frame),
                "promotions": promotions,
                "promotion_rate": promotions / len(frame),
                "promotion_ci95_low": lo,
                "promotion_ci95_high": hi,
                "simultaneous_one_sided_upper_nonpositive_cells": (
                    exact_upper(promotions, len(frame), alpha_upper)
                    if cell in ("zero_mean", "negative_gain")
                    else None
                ),
                "empty_confidence_set_rate": float(frame["empty_confidence_set"].mean()),
                "simultaneous_one_sided_upper_empty_set": (
                    exact_upper(
                        int(frame["empty_confidence_set"].sum()),
                        len(frame),
                        alpha_upper,
                    )
                    if method == "official_mope"
                    else None
                ),
                "mean_labels_used": float(frame["labels_used"].mean()),
                "true_delta": float(frame["true_delta"].iloc[0]),
            }
        )
    summary = pd.DataFrame(summary_rows)
    positive = per_stream[per_stream["cell"] == "positive_gain"].pivot(
        index="seed", columns="method", values=["promoted", "labels_used"]
    )
    power_diff = (
        positive["promoted"]["official_mope"].astype(float)
        - positive["promoted"]["fixed_n_hoeffding"].astype(float)
    ).to_numpy()
    labels_diff = (
        positive["labels_used"]["official_mope"].astype(float)
        - positive["labels_used"]["fixed_n_hoeffding"].astype(float)
    ).to_numpy()
    contrasts = {
        "positive_gain": {
            "paired_power_difference_mope_minus_fixed_n": float(power_diff.mean()),
            "paired_power_difference_bootstrap_95": list(
                paired_bootstrap_interval(power_diff, seed_offset + 1)
            ),
            "paired_label_difference_mope_minus_fixed_n": float(labels_diff.mean()),
            "paired_label_difference_bootstrap_95": list(
                paired_bootstrap_interval(labels_diff, seed_offset + 2)
            ),
        }
    }
    output.mkdir(parents=True)
    per_stream.to_csv(output / "stream_metrics.csv", index=False)
    summary.to_csv(output / "summary_metrics.csv", index=False)
    elapsed = time.perf_counter() - started
    source_files = [
        Path(__file__),
        PROTOCOL,
        SMOKE_HELPER,
        repo / "opebetrp.py",
        repo / "opebet.py",
        repo / "LICENSE",
    ]
    error_bounds = (
        summary.loc[
            summary["cell"].isin(["zero_mean", "negative_gain"]),
            "simultaneous_one_sided_upper_nonpositive_cells",
        ]
        .dropna()
        .tolist()
    )
    error_bounds.extend(
        summary.loc[
            (summary["method"] == "official_mope"),
            "simultaneous_one_sided_upper_empty_set",
        ]
        .dropna()
        .tolist()
    )
    null_max_upper = float(max(error_bounds))
    manifest = {
        "schema_version": "1.0.0",
        "status": (
            "smoke_not_research"
            if (seeds, horizon) != (1_000, 200)
            else "calibration_and_power_complete"
            if null_max_upper < 0.05
            else "calibration_gate_failed"
        ),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "official MOPE gated-deployment confidence sequence",
        "reference_commit": revision,
        "protocol": {
            "path": str(PROTOCOL.relative_to(ROOT)),
            "protocol_sha256": sha256(PROTOCOL),
            "streams_per_cell": seeds,
            "events_per_stream": horizon,
            "seed_offset": seed_offset,
            "cells": CELLS,
            "true_delta_by_cell": {"zero_mean": 0.0, "positive_gain": 0.12, "negative_gain": -0.12},
            "alpha": ALPHA,
            "importance_weight_support": [W_MIN, W_MAX],
            "reward_support": [0, 1],
            "generation_device": str(device),
            "generation_gpu": torch.cuda.get_device_name(0),
            "solver_workers": workers,
            "fixed_n_baseline": "one-sided Hoeffding lower bound at N with Z=(w-1)r and range width 1.2",
            "simultaneous_error_upper_bound": "Bonferroni Clopper-Pearson one-sided bounds at confidence 1 - 0.05/7 over four nonpositive promotion rates and three MOPE empty-set rates",
            "bootstrap_replicates": 10_000,
            "bootstrap_seeds": [seed_offset + 1, seed_offset + 2],
        },
        "results": {
            "summary": summary.astype(object)
            .where(pd.notna(summary), None)
            .to_dict(orient="records"),
            "paired_contrasts": contrasts,
            "max_simultaneous_null_upper_bound": null_max_upper,
            "elapsed_seconds": elapsed,
        },
        "source_sha256": {str(p.relative_to(ROOT)): file_sha256(p) for p in source_files},
        "outputs": {
            "stream_metrics": "stream_metrics.csv",
            "aggregate_metrics": "summary_metrics.csv",
            "row_level_features_or_outcomes_written": 0,
        },
        "limitations": [
            "IID synthetic contextual-bandit study only; not an OBD or real-data result.",
            "One fixed target policy, one logging policy, one support range and one horizon; no multiple-candidate FWER claim.",
            "The fixed-N Hoeffding gate is a deliberately simple distribution-free comparator and may be conservative.",
            "Monte Carlo calibration supports only these registered cells; the published method's theorem and assumptions remain the validity basis.",
            "No delay, adaptive querying, scouting, retraining cost or operational utility is represented.",
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    report = [
        "# MOPE gated-deployment IID calibration and power comparison",
        "",
        f"Status: {manifest['status']}; runtime {elapsed:.1f}s; generated on {device}.",
        "",
        summary.to_markdown(index=False),
        "",
        json.dumps(contrasts, indent=2),
        "",
        "Interpretation is restricted to the frozen IID synthetic policy-value contract. This does not validate chronological OBD feedback or establish a ShiftGuard novelty result.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    checksum_files = [
        p for p in sorted(output.iterdir()) if p.is_file() and p.name != "artifact_checksums.json"
    ]
    checksum_manifest = {
        "files": {
            p.name: {"bytes": p.stat().st_size, "sha256": file_sha256(p)} for p in checksum_files
        }
    }
    (output / "artifact_checksums.json").write_text(
        json.dumps(checksum_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", type=int, default=1_000)
    parser.add_argument("--horizon", type=int, default=200)
    parser.add_argument("--seed-offset", type=int, default=2_040_000_000)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help="independent processes for the pinned MOPE reference solver",
    )
    args = parser.parse_args()
    if args.seeds < 1 or args.horizon < 1 or args.workers < 1:
        parser.error("--seeds, --horizon, and --workers must be positive")
    result = run(
        args.repo,
        args.output,
        args.seeds,
        args.horizon,
        args.seed_offset,
        args.device,
        args.workers,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "max_simultaneous_null_upper_bound": result["results"][
                    "max_simultaneous_null_upper_bound"
                ],
                "elapsed_seconds": result["results"]["elapsed_seconds"],
                "output": str(args.output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
