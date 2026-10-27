"""Reconstruct and verify the registered one-step Certification Exponent run."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from reproduce_certification_exponent_one_step import (
    ALPHA,
    HORIZON,
    MOPE_COMMIT,
    PROTOCOL,
    ROOT,
    _init_mope_worker,
)
from reproduce_molitor_mope_matched import generate_streams
from scipy.stats import beta, binomtest

from shiftlab.dive.certification_exponent_one_step import ProjectedKellyOneStep

METHODS = (
    "certification_exponent_projected_kelly_1step",
    "fixed_horizon_hoeffding",
    "official_mope_gate",
)
MOPE_REPO = ROOT / "tmp/mope_reference"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def clopper_pearson(successes: int, n: int) -> tuple[float, float]:
    tail = 0.025
    lower = 0.0 if successes == 0 else float(beta.ppf(tail, successes, n - successes + 1))
    upper = 1.0 if successes == n else float(beta.ppf(1.0 - tail, successes + 1, n - successes))
    return lower, upper


def _reconstruct_stream_methods(
    actions: np.ndarray, rewards: np.ndarray
) -> dict[str, dict[str, Any]]:
    monitor = ProjectedKellyOneStep(target_action=1, alpha=ALPHA)
    stopping_time = HORIZON + 1
    for event, (action, reward) in enumerate(zip(actions, rewards, strict=True), start=1):
        result = monitor.update(int(action), int(reward))
        if result.certified:
            stopping_time = event
            break
    kelly = {
        "promoted": stopping_time <= HORIZON,
        "labels_used": min(stopping_time, HORIZON),
        "censored_stopping_time": stopping_time,
        "empty_confidence_set": False,
    }
    scores = (np.where(actions == 1, 2.0, 0.0) - 1.0) * rewards
    radius = 2.0 * np.sqrt(np.log(1.0 / ALPHA) / (2.0 * HORIZON))
    fixed = {
        "promoted": bool(scores.mean() - radius > 0.0),
        "labels_used": HORIZON,
        "censored_stopping_time": HORIZON,
        "empty_confidence_set": False,
    }
    return {
        METHODS[0]: kelly,
        METHODS[1]: fixed,
    }


def _mope_worker_init(repo: str) -> None:
    _init_mope_worker(repo)


def _replay_mope(task: tuple[str, int, np.ndarray]) -> dict[str, Any]:
    import reproduce_molitor_mope_matched as source_loader

    scenario, replication_id, data = task
    if source_loader._WORKER_MOPE is None:
        raise RuntimeError("pinned MOPE source is not loaded in verifier worker")
    lower, upper = source_loader._WORKER_MOPE(data, 0.0, 2.0, ALPHA)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    if lower.shape != (HORIZON,) or upper.shape != (HORIZON,):
        raise RuntimeError("MOPE replay returned an unexpected path shape")
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise RuntimeError("MOPE replay returned non-finite bounds")
    empty = np.flatnonzero(lower > upper + 1e-10)
    crossing = np.flatnonzero(lower > 0.0)
    first_empty = int(empty[0] + 1) if empty.size else HORIZON + 1
    first_crossing = int(crossing[0] + 1) if crossing.size else HORIZON + 1
    promoted = first_crossing < first_empty
    return {
        "scenario": scenario,
        "replication_id": replication_id,
        "method": METHODS[2],
        "promoted": bool(promoted),
        "labels_used": first_crossing if promoted else HORIZON,
        "censored_stopping_time": first_crossing if promoted else HORIZON + 1,
        "empty_confidence_set": bool(empty.size),
        "first_empty_event": first_empty if empty.size else None,
        "first_lower_crossing_event": first_crossing if crossing.size else None,
    }


def _expected_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        promoted = int(group["promoted"].astype(bool).sum())
        low, high = clopper_pearson(promoted, len(group))
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "promotions": promoted,
                "promotion_rate": promoted / len(group),
                "promotion_ci95_low": low,
                "promotion_ci95_high": high,
                "mean_labels_used": float(group["labels_used"].mean()),
                "median_censored_stopping_time": float(group["censored_stopping_time"].median()),
                "empty_paths": int(group["empty_confidence_set"].astype(bool).sum()),
            }
        )
    return pd.DataFrame(rows)


def verify(output: Path, *, workers: int, device_name: str) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    metrics_path = output / "per_stream_metrics.csv"
    summary_path = output / "summary.csv"
    for path in (manifest_path, metrics_path, summary_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["artifacts_sha256"]
    for name, digest in expected.items():
        path = output / name
        if not path.is_file() or digest != sha256(path):
            raise ValueError(f"artifact checksum mismatch: {name}")
    execution_source = manifest["execution_source"]
    if execution_source["runner_snapshot"] not in expected:
        raise ValueError("runner source snapshot is absent from artifact hashes")
    if expected[execution_source["runner_snapshot"]] != execution_source["runner_sha256"]:
        raise ValueError("runner snapshot hash metadata disagree")
    if manifest["status"] != "completed_source_faithful_one_step_adaptation_synthetic_only":
        raise ValueError("manifest status is not the expected completed status")
    if manifest["protocol"]["sha256"] != sha256(PROTOCOL):
        raise ValueError("frozen protocol hash mismatch")
    if manifest["methods"]["projected_kelly"]["code_sha256"] != sha256(
        ROOT / "src/shiftlab/dive/certification_exponent_one_step.py"
    ):
        raise ValueError("projected Kelly implementation hash mismatch")
    if manifest["protocol"]["alpha"] != ALPHA or manifest["protocol"]["horizon"] != HORIZON:
        raise ValueError("protocol alpha or horizon does not match verifier")
    protocol = manifest["protocol"]
    if protocol["seed_schemes"] != {"null": 101_026, "alternative": 202_026}:
        raise ValueError("registered seed schemes do not match verifier")
    if protocol["null_reward_means_action0_action1"] != [0.5, 0.5]:
        raise ValueError("registered null distribution does not match verifier")
    if protocol["alternative_reward_means_action0_action1"] != [0.35, 0.65]:
        raise ValueError("registered alternative does not match verifier")
    if protocol["logger"] != [0.5, 0.5] or protocol["target_action"] != 1:
        raise ValueError("registered logger or target policy does not match verifier")

    revision = subprocess.run(
        ["git", "-C", str(MOPE_REPO), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != MOPE_COMMIT or manifest["methods"]["mope"]["commit"] != revision:
        raise ValueError("MOPE repository revision mismatch")
    for name, digest in manifest["methods"]["mope"]["source_sha256"].items():
        if sha256(MOPE_REPO / name) != digest:
            raise ValueError(f"pinned MOPE source checksum mismatch: {name}")

    import torch

    device = (
        torch.device("cuda" if device_name == "auto" and torch.cuda.is_available() else "cpu")
        if device_name == "auto"
        else torch.device(device_name)
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested for stream reconstruction but unavailable")

    recorded = pd.read_csv(metrics_path)
    scenario_specs = (
        ("equal_value_null", int(protocol["null_streams"]), 101_026, 0.5, 0.5),
        ("target_improves", int(protocol["alternative_streams"]), 202_026, 0.35, 0.65),
    )
    expected_basic: list[dict[str, Any]] = []
    mope_tasks: list[tuple[str, int, np.ndarray]] = []
    expected_hashes: dict[tuple[str, int], str] = {}
    for scenario, count, seed, mu0, mu1 in scenario_specs:
        actions_batch, rewards_batch, hashes = generate_streams(
            scenario=scenario,
            streams=count,
            seed=seed,
            mu0=mu0,
            mu1=mu1,
            device=device,
        )
        for replication_id, (actions, rewards, stream_hash) in enumerate(
            zip(actions_batch, rewards_batch, hashes, strict=True)
        ):
            expected_hashes[(scenario, replication_id)] = stream_hash
            for method, row in _reconstruct_stream_methods(actions, rewards).items():
                expected_basic.append(
                    {
                        "scenario": scenario,
                        "replication_id": replication_id,
                        "method": method,
                        "stream_sha256": stream_hash,
                        **row,
                    }
                )
            mope_tasks.append(
                (
                    scenario,
                    replication_id,
                    np.column_stack((np.where(actions == 1, 2.0, 0.0), rewards)),
                )
            )
    expected_basic_frame = pd.DataFrame(expected_basic)
    observed_basic = recorded[recorded.method.isin(METHODS[:2])]
    if len(recorded) != 3 * (scenario_specs[0][1] + scenario_specs[1][1]):
        raise ValueError("unexpected per-stream row count")
    key = ["scenario", "replication_id", "method"]
    if recorded.duplicated(key).any() or len(recorded) != len(recorded.drop_duplicates(key)):
        raise ValueError("duplicate per-stream metric keys")
    if len(observed_basic) != len(expected_basic_frame):
        raise ValueError("unexpected count of projected-Kelly/fixed-horizon records")
    recorded_hash = {
        (r.scenario, int(r.replication_id)): r.stream_sha256 for r in recorded.itertuples()
    }
    if recorded_hash != expected_hashes:
        raise ValueError("recorded stream hashes do not match regenerated streams")
    observed_basic = observed_basic.sort_values(key).reset_index(drop=True)
    expected_basic_frame = expected_basic_frame.sort_values(key).reset_index(drop=True)
    for column in (
        "scenario",
        "replication_id",
        "method",
        "stream_sha256",
        "promoted",
        "labels_used",
        "censored_stopping_time",
        "empty_confidence_set",
    ):
        if not observed_basic[column].astype(str).equals(expected_basic_frame[column].astype(str)):
            raise ValueError(f"reconstructed method field mismatch: {column}")

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_mope_worker_init,
        initargs=(str(MOPE_REPO.resolve()),),
    ) as executor:
        mope_rows = list(executor.map(_replay_mope, mope_tasks, chunksize=1))
    expected_mope = pd.DataFrame(mope_rows).sort_values(key).reset_index(drop=True)
    observed_mope = recorded[recorded.method.eq(METHODS[2])].sort_values(key).reset_index(drop=True)
    if len(observed_mope) != len(expected_mope):
        raise ValueError("unexpected count of official-MOPE records")
    for column in (
        "scenario",
        "replication_id",
        "method",
        "promoted",
        "labels_used",
        "censored_stopping_time",
        "empty_confidence_set",
        "first_empty_event",
        "first_lower_crossing_event",
    ):
        left = observed_mope[column].where(observed_mope[column].notna(), None).tolist()
        right = expected_mope[column].where(expected_mope[column].notna(), None).tolist()
        if [None if pd.isna(x) else x for x in left] != [None if pd.isna(x) else x for x in right]:
            raise ValueError(f"pinned MOPE reconstruction mismatch: {column}")

    recomputed_summary = _expected_summary(recorded)
    observed_summary = (
        pd.read_csv(summary_path).sort_values(["scenario", "method"]).reset_index(drop=True)
    )
    recomputed_summary = recomputed_summary.sort_values(["scenario", "method"]).reset_index(
        drop=True
    )
    if list(observed_summary.columns) != list(recomputed_summary.columns):
        raise ValueError("summary schema mismatch")
    for column in ("scenario", "method", "streams", "promotions", "empty_paths"):
        if not observed_summary[column].astype(str).equals(recomputed_summary[column].astype(str)):
            raise ValueError(f"summary count mismatch: {column}")
    numeric = [
        column
        for column in recomputed_summary.columns
        if column not in {"scenario", "method", "streams", "promotions", "empty_paths"}
    ]
    for column in numeric:
        if not np.allclose(
            observed_summary[column], recomputed_summary[column], rtol=1e-11, atol=1e-14
        ):
            raise ValueError(f"summary statistic mismatch: {column}")

    alternative = recorded[recorded.scenario.eq("target_improves")].pivot(
        index="replication_id", columns="method", values="promoted"
    )
    left = alternative[METHODS[0]].astype(bool).to_numpy()
    right = alternative[METHODS[2]].astype(bool).to_numpy()
    wins = int(np.sum(left & ~right))
    losses = int(np.sum(~left & right))
    discordant = wins + losses
    paired = manifest["paired_contrasts"]["projected_kelly_vs_mope_alternative"]
    if wins != paired["kelly_only_promotions"] or losses != paired["mope_only_promotions"]:
        raise ValueError("paired contrast counts mismatch")
    if not np.isclose(
        paired["paired_rate_difference"], float(np.mean(left.astype(float) - right.astype(float)))
    ):
        raise ValueError("paired rate difference mismatch")
    pvalue = float(binomtest(wins, discordant, 0.5).pvalue) if discordant else 1.0
    if not np.isclose(paired["mcnemar_exact_two_sided_p"], pvalue):
        raise ValueError("exact paired p-value mismatch")

    return {
        "status": "passed_full_seed_stream_and_pinned_reference_reconstruction",
        "metrics_rows_reconstructed": len(recorded),
        "registered_streams": sum(count for _, count, *_ in scenario_specs),
        "mope_paths_reconstructed": len(expected_mope),
        "methods_reconstructed": list(METHODS),
        "protocol_sha256": sha256(PROTOCOL),
        "per_stream_metrics_sha256": sha256(metrics_path),
        "summary_sha256": sha256(summary_path),
        "runner_sha256_at_execution": execution_source["runner_sha256"],
        "verifier_sha256": sha256(Path(__file__)),
        "limitations": "reconstructs the registered synthetic streams and methods; does not validate assumptions on OBD or reproduce the full multi-step-tree paper experiments",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    result = verify(args.output.resolve(), workers=args.workers, device_name=args.device)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
