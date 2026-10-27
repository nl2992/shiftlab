"""Run the registered one-step Certification Exponent comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from reproduce_molitor_mope_matched import _init_mope_worker, generate_streams
from scipy.stats import beta, binomtest

from shiftlab.dive.certification_exponent_one_step import ProjectedKellyOneStep

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/certification_exponent_one_step_protocol_v1.md"
DEFAULT_MOPE_REPO = ROOT / "tmp/mope_reference"
DEFAULT_OUTPUT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/certification_exponent_one_step_v1"
)
ALPHA = 0.05
HORIZON = 200
NULL_STREAMS = 1_000
ALT_STREAMS = 300
MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def cp_interval(events: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    tail = (1.0 - confidence) / 2.0
    low = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    high = 1.0 if events == trials else float(beta.ppf(1.0 - tail, events + 1, trials - events))
    return low, high


def evaluate_projected_kelly(actions: np.ndarray, rewards: np.ndarray) -> dict[str, Any]:
    monitor = ProjectedKellyOneStep(target_action=1, alpha=ALPHA)
    stopping_time = HORIZON + 1
    max_wealth = 1.0
    for event, (action, reward) in enumerate(zip(actions, rewards, strict=True), start=1):
        update = monitor.update(int(action), int(reward))
        max_wealth = max(max_wealth, update.wealth)
        if update.certified:
            stopping_time = event
            break
    return {
        "method": "certification_exponent_projected_kelly_1step",
        "promoted": stopping_time <= HORIZON,
        "labels_used": min(stopping_time, HORIZON),
        "censored_stopping_time": stopping_time,
        "empty_confidence_set": False,
        "final_wealth_or_lower": monitor.wealth,
        "max_wealth": max_wealth,
    }


def evaluate_fixed_horizon(actions: np.ndarray, rewards: np.ndarray) -> dict[str, Any]:
    score = (np.where(actions == 1, 2.0, 0.0) - 1.0) * rewards
    radius = 2.0 * np.sqrt(np.log(1.0 / ALPHA) / (2.0 * HORIZON))
    lower = float(score.mean() - radius)
    return {
        "method": "fixed_horizon_hoeffding",
        "promoted": lower > 0.0,
        "labels_used": HORIZON,
        "censored_stopping_time": HORIZON,
        "empty_confidence_set": False,
        "final_wealth_or_lower": lower,
        "max_wealth": np.nan,
    }


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    result: list[dict[str, Any]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        successes = int(group["promoted"].sum())
        low, high = cp_interval(successes, len(group))
        row: dict[str, Any] = {
            "scenario": scenario,
            "method": method,
            "streams": len(group),
            "promotions": successes,
            "promotion_rate": successes / len(group),
            "promotion_ci95_low": low,
            "promotion_ci95_high": high,
            "mean_labels_used": float(group["labels_used"].mean()),
            "median_censored_stopping_time": float(group["censored_stopping_time"].median()),
            "empty_paths": int(group["empty_confidence_set"].sum()),
        }
        result.append(row)
    return pd.DataFrame(result)


def _evaluate_mope_stream(task: tuple[str, int, np.ndarray]) -> dict[str, Any]:
    """Count a gate only if its lower-bound crossing precedes any empty set."""
    import reproduce_molitor_mope_matched as mope_runner

    scenario, replication_id, data = task
    if mope_runner._WORKER_MOPE is None:
        raise RuntimeError("pinned MOPE worker was not initialized")
    lower, upper = mope_runner._WORKER_MOPE(data, 0.0, 2.0, ALPHA)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    if lower.shape != (HORIZON,) or upper.shape != (HORIZON,):
        raise RuntimeError("MOPE returned confidence paths with an unexpected shape")
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise RuntimeError("MOPE returned non-finite confidence bounds")
    empty = np.flatnonzero(lower > upper + 1e-10)
    crossing = np.flatnonzero(lower > 0.0)
    first_empty = int(empty[0] + 1) if empty.size else HORIZON + 1
    crossing_event = int(crossing[0] + 1) if crossing.size else HORIZON + 1
    valid_crossing = crossing_event < first_empty
    return {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": "official_mope_gate",
        "promoted": bool(valid_crossing),
        "labels_used": crossing_event if valid_crossing else HORIZON,
        "censored_stopping_time": crossing_event if valid_crossing else HORIZON + 1,
        "empty_confidence_set": bool(empty.size),
        "first_empty_event": first_empty if empty.size else None,
        "first_lower_crossing_event": crossing_event if crossing.size else None,
        "final_wealth_or_lower": float(lower[-1]),
        "max_wealth": np.nan,
    }


def run(
    *,
    mope_repo: Path,
    output: Path,
    null_streams: int,
    alternative_streams: int,
    workers: int,
    device_name: str,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if not (mope_repo / ".git").exists():
        raise FileNotFoundError(f"Pinned MOPE repository is unavailable: {mope_repo}")
    import subprocess

    revision = subprocess.run(
        ["git", "-C", str(mope_repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != MOPE_COMMIT:
        raise RuntimeError(f"Expected MOPE commit {MOPE_COMMIT}, got {revision}")

    import torch

    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but not available")

    output.mkdir(parents=True)
    metrics: list[dict[str, Any]] = []
    mope_tasks: list[tuple[str, int, np.ndarray]] = []
    stream_hashes: dict[tuple[str, int], str] = {}
    scenarios = (
        ("equal_value_null", null_streams, 101_026, 0.5, 0.5),
        ("target_improves", alternative_streams, 202_026, 0.35, 0.65),
    )
    for scenario, count, seed, mu0, mu1 in scenarios:
        actions_all, rewards_all, hashes = generate_streams(
            scenario=scenario,
            streams=count,
            seed=seed,
            mu0=mu0,
            mu1=mu1,
            device=device,
        )
        for replication_id, (actions, rewards, stream_hash) in enumerate(
            zip(actions_all, rewards_all, hashes, strict=True)
        ):
            stream_hashes[(scenario, replication_id)] = stream_hash
            for metric in (
                evaluate_projected_kelly(actions, rewards),
                evaluate_fixed_horizon(actions, rewards),
            ):
                metrics.append(
                    {
                        "scenario": scenario,
                        "replication_id": replication_id,
                        "stream_sha256": stream_hash,
                        **metric,
                    }
                )
            mope_tasks.append(
                (
                    scenario,
                    replication_id,
                    np.column_stack((np.where(actions == 1, 2.0, 0.0), rewards)),
                )
            )

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_mope_worker,
        initargs=(str(mope_repo.resolve()),),
    ) as executor:
        mope_rows = list(executor.map(_evaluate_mope_stream, mope_tasks, chunksize=1))
    for row in mope_rows:
        key = (str(row["scenario"]), int(row["replication_id"]))
        metrics.append(
            {
                **row,
                "stream_sha256": stream_hashes[key],
                "final_wealth_or_lower": np.nan,
                "max_wealth": np.nan,
            }
        )

    metric_frame = pd.DataFrame(metrics).sort_values(
        ["scenario", "replication_id", "method"], ignore_index=True
    )
    summary = summarize(metric_frame)
    metric_path = output / "per_stream_metrics.csv"
    summary_path = output / "summary.csv"
    metric_frame.to_csv(metric_path, index=False)
    summary.to_csv(summary_path, index=False)

    paired: dict[str, Any] = {}
    alt = metric_frame[metric_frame["scenario"] == "target_improves"].pivot(
        index="replication_id", columns="method", values="promoted"
    )
    left = alt["certification_exponent_projected_kelly_1step"].astype(bool).to_numpy()
    right = alt["official_mope_gate"].astype(bool).to_numpy()
    wins = int(np.sum(left & ~right))
    losses = int(np.sum(~left & right))
    discordant = wins + losses
    paired["projected_kelly_vs_mope_alternative"] = {
        "kelly_only_promotions": wins,
        "mope_only_promotions": losses,
        "paired_rate_difference": float(np.mean(left.astype(float) - right.astype(float))),
        "mcnemar_exact_two_sided_p": (
            float(binomtest(wins, discordant, 0.5).pvalue) if discordant else 1.0
        ),
        "interpretation": "paired synthetic stream contrast; no OBD validity claim",
    }

    mope_files = [mope_repo / name for name in ("opebetrp.py", "opebet.py", "LICENSE")]
    gpu_name = torch.cuda.get_device_name(device) if device.type == "cuda" else None
    manifest = {
        "schema_version": "1.0.0",
        "status": "completed_source_faithful_one_step_adaptation_synthetic_only",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "repository_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "protocol": {
            "path": str(PROTOCOL.relative_to(ROOT)),
            "sha256": sha256(PROTOCOL),
            "alpha": ALPHA,
            "horizon": HORIZON,
            "null_streams": null_streams,
            "alternative_streams": alternative_streams,
            "seed_schemes": {"null": 101_026, "alternative": 202_026},
            "null_reward_means_action0_action1": [0.5, 0.5],
            "alternative_reward_means_action0_action1": [0.35, 0.65],
            "logger": [0.5, 0.5],
            "target_action": 1,
            "feedback": "IID stationary action/reward episodes with immediate complete reward",
        },
        "methods": {
            "projected_kelly": {
                "code_sha256": sha256(
                    ROOT / "src/shiftlab/dive/certification_exponent_one_step.py"
                ),
                "deviations": [
                    "one-step binary-reward specialization only",
                    "trivial feasible bet until both actions have appeared",
                    "SLSQP fit may be suboptimal; pathwise feasibility is retained as the soundness condition",
                ],
            },
            "mope": {
                "repository": "https://github.com/n17s/mope",
                "commit": revision,
                "source_sha256": {path.name: sha256(path) for path in mope_files},
            },
            "fixed_horizon": "one-sided Hoeffding lower bound at T only; no optional-stopping claim",
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "device": str(device),
            "gpu_name": gpu_name,
            "cpu_parallel_workers_for_mope": workers,
        },
        "paired_contrasts": paired,
        "artifacts_sha256": {
            metric_path.name: sha256(metric_path),
            summary_path.name: sha256(summary_path),
        },
        "limitations": [
            "The experiment is context-free IID stationary synthetic logged-bandit data.",
            "It is not a reproduction of the paper's multi-step trees or its complete experiment suite.",
            "It does not validate the assumptions of the real Open Bandit Dataset replay.",
            "The fitted optimizer is an adaptation; infeasible numerical iterates fall back to zero bet.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return {"summary": summary, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mope-repo", type=Path, default=DEFAULT_MOPE_REPO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--null-streams", type=int, default=NULL_STREAMS)
    parser.add_argument("--alternative-streams", type=int, default=ALT_STREAMS)
    args = parser.parse_args()
    if min(args.workers, args.null_streams, args.alternative_streams) < 1:
        parser.error("workers and stream counts must be positive")
    result = run(
        mope_repo=args.mope_repo.resolve(),
        output=args.output.resolve(),
        null_streams=args.null_streams,
        alternative_streams=args.alternative_streams,
        workers=args.workers,
        device_name=args.device,
    )
    print(result["summary"].to_string(index=False))
    print(f"Manifest: {args.output.resolve() / 'manifest.json'}")


if __name__ == "__main__":
    main()
