"""Run a matched synthetic comparison of OPI, MOPE, and fixed-N gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
import scipy
from scipy.stats import beta

from shiftlab.dive.anytime_policy_identification import (
    bounded_dr_pseudo_outcomes,
    lil_value_bounds,
    optimal_policy_set,
    optimal_policy_stopping_time,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/opi_mope_matched_protocol_v1.md"
DEFAULT_MOPE_REPO = ROOT / "tmp/mope_reference"
DEFAULT_OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1"
ALPHA = 0.05
HORIZON = 200
NULL_STREAMS = 1_000
ALT_STREAMS = 300
TRUNCATION = 1.0
POLICY_TREATMENT_PROBABILITIES = np.array([0.0, 0.5, 1.0], dtype=np.float64)
POLICIES = np.stack([1.0 - POLICY_TREATMENT_PROBABILITIES, POLICY_TREATMENT_PROBABILITIES], axis=-1)
METHODS = (
    "opi_anytime",
    "fixed_horizon_policy_selection",
    "official_mope_gate",
    "fixed_horizon_gate",
)
MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"
_WORKER_MOPE: Any = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def cp_interval(events: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    tail = (1.0 - confidence) / 2.0
    lower = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    upper = 1.0 if events == trials else float(beta.ppf(1.0 - tail, events + 1, trials - events))
    return lower, upper


def _init_mope_worker(repo_string: str) -> None:
    global _WORKER_MOPE
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    # The pinned QP solver writes a status line for nearly every time step.
    # Keep worker noise out of the terminal; exceptions still propagate.
    null_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_fd, 1)
    finally:
        os.close(null_fd)
    from scripts.reproduce_mope_gated_null_smoke import load_official_mope

    _WORKER_MOPE, revision = load_official_mope(Path(repo_string))
    if revision != MOPE_COMMIT:
        raise RuntimeError(f"Unexpected MOPE source commit: {revision}")


def _evaluate_mope(task: tuple[str, int, np.ndarray]) -> dict[str, object]:
    scenario, replication_id, data = task
    if _WORKER_MOPE is None:
        raise RuntimeError("MOPE worker did not load the pinned implementation")
    lower, upper = _WORKER_MOPE(data, 0.0, 2.0, ALPHA)
    lower_array = np.asarray(lower, dtype=np.float64)
    upper_array = np.asarray(upper, dtype=np.float64)
    if lower_array.shape != (HORIZON,) or upper_array.shape != (HORIZON,):
        raise RuntimeError("MOPE returned a confidence path with the wrong length")
    if np.any(~np.isfinite(lower_array)) or np.any(~np.isfinite(upper_array)):
        raise RuntimeError("MOPE returned a non-finite confidence path")
    if np.any(np.diff(lower_array) < -1e-10) or np.any(np.diff(upper_array) > 1e-10):
        raise RuntimeError("MOPE confidence path was not monotone")
    crossing = np.flatnonzero(lower_array > 0.0)
    promoted = bool(crossing.size)
    return {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": "official_mope_gate",
        "false_optimal_eliminated_anytime": None,
        "false_optimal_excluded_at_horizon": None,
        "unique_stopped": None,
        "correct_singleton_at_horizon": None,
        "promoted": promoted,
        "labels_used": int(crossing[0] + 1) if promoted else HORIZON,
        "censored_stopping_time": None,
        "empty_confidence_set": bool(np.any(lower_array > upper_array + 1e-10)),
        "final_candidate_set_size": None,
    }


def generate_streams(
    *,
    scenario: str,
    streams: int,
    seed: int,
    mu0: float,
    mu1: float,
    device: Any,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    # Import PyTorch only in the parent process. On Windows, spawned MOPE
    # workers re-import this module; loading CUDA DLLs in every worker can
    # exhaust the system paging file even though MOPE itself is CPU-only.
    import torch

    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    shape = (streams, HORIZON)
    actions = torch.bernoulli(
        torch.full(shape, 0.5, dtype=torch.float32, device=device), generator=generator
    ).to(torch.int64)
    reward_uniforms = torch.rand(shape, dtype=torch.float32, device=device, generator=generator)
    means = torch.where(actions == 1, mu1, mu0)
    rewards = (reward_uniforms < means).to(torch.float32)
    actions_np = actions.cpu().numpy()
    rewards_np = rewards.cpu().numpy().astype(np.float64)
    hashes = [
        hashlib.sha256(np.column_stack((a, r)).astype(np.float64).tobytes()).hexdigest()
        for a, r in zip(actions_np, rewards_np, strict=True)
    ]
    return actions_np, rewards_np, hashes


def _opi_and_fixed_selection(
    actions: np.ndarray,
    rewards: np.ndarray,
    *,
    scenario: str,
    replication_id: int,
    stream_hash: str,
    mu0: float,
    mu1: float,
) -> list[dict[str, object]]:
    n = len(actions)
    h = np.full((n, 2), 0.5, dtype=np.float64)
    rhat = np.full((n, 2), 0.5, dtype=np.float64)
    phi_lower, phi_upper = bounded_dr_pseudo_outcomes(
        actions=actions,
        rewards=rewards,
        logging_probabilities=h,
        target_policies=POLICIES,
        reward_predictions=rhat,
        truncation=TRUNCATION,
    )
    m = len(POLICIES)
    one_sided_alpha = ALPHA / (2.0 * m)
    lower = np.stack(
        [lil_value_bounds(phi_lower[:, i], one_sided_alpha, TRUNCATION) for i in range(m)]
    )
    upper = np.stack(
        [1.0 - lil_value_bounds(phi_upper[:, i], one_sided_alpha, TRUNCATION) for i in range(m)]
    )
    candidate_set = optimal_policy_set(lower, upper)
    stopping_time = optimal_policy_stopping_time(lower, upper)
    true_values = (
        1.0 - POLICY_TREATMENT_PROBABILITIES
    ) * mu0 + POLICY_TREATMENT_PROBABILITIES * mu1
    optimal_indices = np.flatnonzero(true_values == true_values.max())
    false_anytime = not bool(candidate_set[optimal_indices].all())
    final_set_size = int(candidate_set[:, -1].sum())
    correct_final_singleton = bool(
        len(optimal_indices) == 1
        and final_set_size == 1
        and candidate_set[int(optimal_indices[0]), -1]
    )
    opi = {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": "opi_anytime",
        "false_optimal_eliminated_anytime": false_anytime,
        "false_optimal_excluded_at_horizon": bool(not candidate_set[optimal_indices, -1].all()),
        "unique_stopped": bool(stopping_time <= HORIZON),
        "correct_singleton_at_horizon": correct_final_singleton,
        "promoted": None,
        "labels_used": min(stopping_time, HORIZON),
        "censored_stopping_time": min(stopping_time, HORIZON + 1),
        "empty_confidence_set": None,
        "final_candidate_set_size": final_set_size,
        "stream_sha256": stream_hash,
    }

    # Fixed-N finite-class selector: exact bounded score ranges under this
    # preregistered logger/policy/model contract, with alpha/(2m) per tail.
    event_actions = np.array([0, 0, 1, 1], dtype=np.int64)
    event_rewards = np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float64)
    event_h = np.full((4, 2), 0.5, dtype=np.float64)
    event_rhat = np.full((4, 2), 0.5, dtype=np.float64)
    event_low, event_up = bounded_dr_pseudo_outcomes(
        event_actions,
        event_rewards,
        event_h,
        POLICIES,
        event_rhat,
        TRUNCATION,
    )
    score_ranges = np.maximum(
        event_low.max(axis=0) - event_low.min(axis=0),
        event_up.max(axis=0) - event_up.min(axis=0),
    )
    radius = score_ranges * np.sqrt(np.log(1.0 / one_sided_alpha) / (2.0 * HORIZON))
    fixed_lower = phi_lower.mean(axis=0) - radius
    fixed_upper = 1.0 - phi_upper.mean(axis=0) + radius
    fixed_set = fixed_upper >= fixed_lower.max()
    fixed_size = int(fixed_set.sum())
    fixed_correct = bool(
        len(optimal_indices) == 1 and fixed_size == 1 and fixed_set[int(optimal_indices[0])]
    )
    fixed = {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": "fixed_horizon_policy_selection",
        "false_optimal_eliminated_anytime": None,
        "false_optimal_excluded_at_horizon": bool(not fixed_set[optimal_indices].all()),
        "unique_stopped": bool(fixed_size == 1),
        "correct_singleton_at_horizon": fixed_correct,
        "promoted": None,
        "labels_used": HORIZON,
        "censored_stopping_time": HORIZON,
        "empty_confidence_set": None,
        "final_candidate_set_size": fixed_size,
        "stream_sha256": stream_hash,
    }

    weights = np.where(actions == 1, 2.0, 0.0)
    z = (weights - 1.0) * rewards
    gate_radius = 2.0 * np.sqrt(np.log(1.0 / ALPHA) / (2.0 * HORIZON))
    gate_promoted = bool(z.mean() - gate_radius > 0.0)
    fixed_gate = {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": "fixed_horizon_gate",
        "false_optimal_eliminated_anytime": None,
        "false_optimal_excluded_at_horizon": None,
        "unique_stopped": None,
        "correct_singleton_at_horizon": None,
        "promoted": gate_promoted,
        "labels_used": HORIZON,
        "censored_stopping_time": None,
        "empty_confidence_set": False,
        "final_candidate_set_size": None,
        "stream_sha256": stream_hash,
    }
    return [opi, fixed, fixed_gate]


def make_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        row: dict[str, object] = {
            "scenario": scenario,
            "method": method,
            "streams": len(group),
            "mean_labels_used": float(group["labels_used"].mean()),
            "empty_confidence_sets": int(group["empty_confidence_set"].fillna(False).sum()),
        }
        for source, prefix in (
            ("false_optimal_eliminated_anytime", "false_optimal_eliminated_anytime"),
            ("false_optimal_excluded_at_horizon", "false_optimal_excluded_at_horizon"),
            ("unique_stopped", "unique_stops"),
            ("correct_singleton_at_horizon", "correct_singletons"),
            ("promoted", "promotions"),
        ):
            observed = group[source].dropna().astype(bool)
            if not observed.empty:
                successes = int(observed.sum())
                low, high = cp_interval(successes, len(observed))
                row[f"{prefix}_count"] = successes
                row[f"{prefix}_rate"] = successes / len(observed)
                row[f"{prefix}_ci95_low"] = low
                row[f"{prefix}_ci95_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    import torch

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mope-repo", type=Path, default=DEFAULT_MOPE_REPO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--null-streams", type=int, default=NULL_STREAMS)
    parser.add_argument("--alternative-streams", type=int, default=ALT_STREAMS)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
    if args.workers < 1 or args.null_streams < 1 or args.alternative_streams < 1:
        parser.error("worker and stream counts must be positive")
    if not (args.mope_repo / ".git").exists():
        parser.error(f"MOPE repository is missing: {args.mope_repo}")

    device = (
        torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else "cpu")
        if args.device == "auto"
        else torch.device(args.device)
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA was requested but is unavailable")
    output = args.output.resolve()
    output.mkdir(parents=True)
    started = datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = []
    mope_tasks: list[tuple[str, int, np.ndarray]] = []
    stream_count = 0

    scenarios = (
        ("all_tied_null", args.null_streams, 101_026, 0.5, 0.5),
        ("unique_best_action_1", args.alternative_streams, 202_026, 0.35, 0.65),
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
            rows.extend(
                _opi_and_fixed_selection(
                    actions,
                    rewards,
                    scenario=scenario,
                    replication_id=replication_id,
                    stream_hash=stream_hash,
                    mu0=mu0,
                    mu1=mu1,
                )
            )
            data = np.column_stack((np.where(actions == 1, 2.0, 0.0), rewards))
            mope_tasks.append((scenario, replication_id, data))
            stream_count += 1

    with ProcessPoolExecutor(
        max_workers=args.workers,
        initializer=_init_mope_worker,
        initargs=(str(args.mope_repo.resolve()),),
    ) as executor:
        rows.extend(executor.map(_evaluate_mope, mope_tasks, chunksize=1))

    # Populate MOPE stream hashes from the corresponding per-stream OPI rows.
    hash_lookup = {
        (str(row["scenario"]), int(cast(int, row["replication_id"]))): str(
            cast(str, row["stream_sha256"])
        )
        for row in rows
        if row["method"] == "opi_anytime"
    }
    for row in rows:
        if row["method"] == "official_mope_gate":
            row["stream_sha256"] = hash_lookup[
                (str(row["scenario"]), int(cast(int, row["replication_id"])))
            ]

    metrics = pd.DataFrame(rows)
    summary = make_summary(metrics)
    metrics_path = output / "per_stream_metrics.parquet"
    summary_path = output / "summary.parquet"
    metrics.to_parquet(metrics_path, index=False)
    summary.to_parquet(summary_path, index=False)
    metrics.to_csv(output / "per_stream_metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)

    source_files = [
        args.mope_repo / "opebetrp.py",
        args.mope_repo / "opebet.py",
        args.mope_repo / "LICENSE",
    ]
    subprocess_hashes = {path.name: sha256(path) for path in source_files}
    implementation = Path(__file__).resolve()
    module = ROOT / "src/shiftlab/dive/anytime_policy_identification.py"
    manifest = {
        "experiment": "matched_molitor_opi_mope_fixed_horizon_v1",
        "status": "complete",
        "run_started_utc": started,
        "run_finished_utc": datetime.now(UTC).isoformat(),
        "repository_head": "525c79e36614c1611a801e3e39d598412efba9ad",
        "reference_implementation": {
            "repository": "https://github.com/n17s/mope",
            "commit": MOPE_COMMIT,
            "source_sha256": subprocess_hashes,
        },
        "configuration": {
            "alpha": ALPHA,
            "horizon": HORIZON,
            "policies_action1_probability": POLICY_TREATMENT_PROBABILITIES.tolist(),
            "logger_action_probabilities": [0.5, 0.5],
            "reward_model": "fixed predictable rhat=0.5",
            "truncation": TRUNCATION,
            "null_streams": args.null_streams,
            "alternative_streams": args.alternative_streams,
            "scenario_means": {
                "all_tied_null": {"action0": 0.5, "action1": 0.5},
                "unique_best_action_1": {"action0": 0.35, "action1": 0.65},
            },
            "mope_target": "fixed pi(action1)=1 versus the h=0.5 logger",
            "mope_weight_support": [0.0, 2.0],
            "mope_fixed_n_gate_score_range": [-1.0, 1.0],
            "opi_tail_alpha": ALPHA / (2 * len(POLICIES)),
            "seed_by_scenario": {
                "all_tied_null": 101_026,
                "unique_best_action_1": 202_026,
            },
        },
        "learner_visible": ["logged action", "binary reward", "known logger", "fixed policy class"],
        "evaluator_only": ["true action means", "best policy identity"],
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scipy_version": scipy.__version__,
        "python_version": platform.python_version(),
        "workers": args.workers,
        "source_sha256": {
            str(implementation.relative_to(ROOT)): sha256(implementation),
            str(module.relative_to(ROOT)): sha256(module),
            str(PROTOCOL.relative_to(ROOT)): sha256(PROTOCOL),
        },
        "output_sha256": {
            metrics_path.name: sha256(metrics_path),
            summary_path.name: sha256(summary_path),
        },
        "limitations": [
            "synthetic stationary IID two-action context-free task",
            "MOPE tests one preselected candidate against the logger; OPI selects among three policies",
            "fixed-horizon and anytime methods use different decision targets and endpoints",
            "no real data, delayed labels, drift, slate effects, or intervention costs",
        ],
        "stream_count": stream_count,
        "per_stream_rows": len(metrics),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = build_report(summary, manifest)
    (output / "report.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"Completed matched synthetic comparison with {stream_count} shared streams.")


def build_report(summary: pd.DataFrame, manifest: dict[str, object]) -> str:
    return f"""# Matched OPI, MOPE, and fixed-horizon comparison

**Status:** complete synthetic comparison; not a real-data result.  
**Device:** {manifest["device"]} ({manifest["gpu_name"] or "CPU"}).  
**Design:** {manifest["stream_count"]} shared streams, horizon {HORIZON}, two stationary reward scenarios, logged with `h=(0.5,0.5)`.

## Results

{summary.to_markdown(index=False, floatfmt=".4f")}

The official MOPE method tests one preselected `pi(action1)=1` policy against the logger; OPI identifies the best policy in a fixed three-policy class. Their endpoints differ. The fixed-horizon gate shares the MOPE improvement estimand, while the fixed-horizon policy selector shares the OPI ranking estimand. Rates have exact two-sided 95% Clopper-Pearson intervals in the summary table. Every method received the same per-stream action/reward realization; per-stream stream hashes make this correspondence checkable.

## Limitations

This is a context-free stationary Bernoulli bandit with immediate labels, no intervention cost, no adaptation, and no distribution shift. It tests algorithm behavior under the registered synthetic contracts only. It cannot establish any real-data validity, broad ShiftGuard superiority, or economic utility. The prior OBD applicability audit remains in force.
"""


if __name__ == "__main__":
    main()
