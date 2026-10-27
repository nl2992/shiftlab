"""Run frozen WP1 stages; fidelity replays the receipt-checked historic increments on CPU."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.gated_monitor_comparison import comparison_seed
from shiftlab.dive.predictable_bound_replay import first_crossing, replay_mixture_log_e

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / "docs/gated_vs_ungated_monitor_comparison_protocol.md"
HISTORIC = ROOT / "outputs/monitor_signal_diagnostic_20_60_v2"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def fidelity() -> tuple[pd.DataFrame, dict]:
    path = HISTORIC / "metrics/event_traces.parquet"
    receipt = HISTORIC / "reports/manifest.json"
    manifest = json.loads(receipt.read_text(encoding="utf-8"))
    expected = manifest["sha256"]["artifacts"]["metrics\\event_traces.parquet"]
    if digest(path) != expected:
        raise RuntimeError("historic trace checksum mismatch")
    traces = pd.read_parquet(
        path, filters=[("method", "==", "uniform_proxy"), ("scenario", "==", "boundary_local_harm")]
    )
    if set(traces.seed.unique()) != set(range(20373024, 20373084)):
        raise RuntimeError("historic fidelity seed block does not match protocol")
    rows = []
    for seed, group in traces.groupby("seed"):
        group = group.sort_values("event_offset")
        np.testing.assert_array_equal(group.event_offset, np.arange(len(group)))
        np.testing.assert_allclose(group.propensity, 0.2, rtol=0, atol=1e-14)
        values = group.ppi_increment.to_numpy(dtype=float)
        for arm, bound in [("uniform_ppi_common96p9", 96.9), ("uniform_ppi", 45.9)]:
            log_e = replay_mixture_log_e(values, bound, alpha=0.05)
            alarm = first_crossing(log_e, alpha=0.05)
            rows.append(
                {
                    "seed": int(seed),
                    "arm": arm,
                    "bound": bound,
                    "first_alarm": alarm,
                    "crossed": alarm is not None,
                }
            )
            if bound == 96.9:
                np.testing.assert_allclose(log_e, group.learner_log_e, atol=1e-10, rtol=0)
    result = pd.DataFrame(rows)
    counts = result.groupby("arm").crossed.sum().astype(int).to_dict()
    return result, {
        "counts": counts,
        "passes": counts == {"uniform_ppi_common96p9": 6, "uniform_ppi": 47},
        "inputs_sha256": {
            str(path.relative_to(ROOT)): digest(path),
            str(receipt.relative_to(ROOT)): digest(receipt),
        },
    }


def one_task(task: tuple) -> list[dict]:
    return comparison_seed(*task)


def starting_provenance() -> dict:
    sources = sorted(
        set((ROOT / "src/shiftlab").rglob("*.py"))
        | {
            PROTOCOL,
            Path(__file__),
            ROOT / "uv.lock",
            ROOT / "scripts/reproduce_timans_risk_monitor_paired_cost.py",
            ROOT / "docs/stratified_monitor_regime_map.md",
        }
    )
    return {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git("rev-parse", "HEAD"),
        "dirty_paths": git("status", "--porcelain").splitlines(),
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
        "thread_environment": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["fidelity", "smoke", "null", "compare"], required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    # A committed header anchors the protocol; later amendments must be explicit.
    match = re.search(
        r"\*\*Freeze commit:\*\* `([0-9a-f]{40})`", PROTOCOL.read_text(encoding="utf-8")
    )
    if match is None:
        raise RuntimeError("protocol is not frozen")
    git("rev-parse", "--verify", match[1] + "^{commit}")
    git("diff", "--exit-code", "HEAD", "--", str(PROTOCOL.relative_to(ROOT)))
    out = ROOT / f"outputs/gated_monitor_{args.stage}"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    device = "cpu" if args.stage == "fidelity" else ("cuda" if torch.cuda.is_available() else "cpu")
    hardware = environment()
    provenance = starting_provenance()
    start = time.perf_counter()
    inputs = {}
    if args.stage == "fidelity":
        frame, result = fidelity()
        inputs = result.pop("inputs_sha256")
    else:
        previous = ROOT / "outputs/gated_monitor_fidelity/decision.json"
        if not previous.exists() or not json.loads(previous.read_text())["passes"]:
            raise RuntimeError("fidelity must pass before fresh streams")
        if args.stage in {"null", "compare"}:
            smoke = ROOT / "outputs/gated_monitor_smoke/manifest.json"
            if not smoke.exists():
                raise RuntimeError("smoke and runtime projection required before full runs")
        if args.stage == "compare":
            calibration = ROOT / "outputs/gated_monitor_null/analysis/decision.json"
            if (
                not calibration.exists()
                or not json.loads(calibration.read_text())["primary_passes"]
            ):
                raise RuntimeError("primary gated null calibration must pass before comparison")
        if args.stage == "smoke":
            tasks = [
                ("boundary_local_harm", seed, 0.2, device) for seed in range(58600000, 58600005)
            ]
        elif args.stage == "null":
            tasks = [
                (scenario, seed, budget, device)
                for scenario in ("stationary", "benign_nuisance")
                for budget in (0.02, 0.05, 0.1, 0.2)
                for seed in range(58500000, 58502000)
            ]
        else:
            tasks = [
                (scenario, seed, budget, device)
                for scenario in (
                    "stationary",
                    "benign_nuisance",
                    "boundary_local_harm",
                    "harmful_adaptation",
                )
                for budget in (0.02, 0.05, 0.1, 0.2)
                for seed in range(58400000, 58400100)
            ]
        out.mkdir(parents=True, exist_ok=True)
        (out / "launch.json").write_text(
            json.dumps(
                {
                    **provenance,
                    "stage": args.stage,
                    "workers": args.workers,
                    "device": device,
                    "tasks": len(tasks),
                    "hardware": hardware,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if args.workers == 1:
            rows = [row for task in tasks for row in one_task(task)]
        else:
            with ProcessPoolExecutor(args.workers, mp_context=get_context("spawn")) as pool:
                rows = [row for block in pool.map(one_task, tasks) for row in block]
        frame = pd.DataFrame(rows)
        result = {"stage": args.stage, "tasks": len(tasks), "inference": args.stage != "smoke"}
    out.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out / "streams.parquet", index=False)
    (out / "decision.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - start
    manifest = {
        **provenance,
        "stage": args.stage,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "git_head_at_end": git("rev-parse", "HEAD"),
        "dirty_paths_at_end": git("status", "--porcelain").splitlines(),
        "command": subprocess.list2cmdline(sys.argv),
        "device": device,
        "hardware": hardware,
        "runtime_seconds": elapsed,
        "workers": args.workers,
        "config": {"n": 3200, "d": 16, "epsilon": 0.1, "alpha": 0.05},
        "inputs_sha256": inputs,
        "outputs_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    if args.stage == "smoke":
        manifest["projected_serial_seconds"] = {
            "null": elapsed / 5 * 16000,
            "compare": elapsed / 5 * 1600,
        }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result, "runtime_seconds": elapsed}, indent=2))
    if args.stage == "fidelity" and not result["passes"]:
        raise RuntimeError("S1 failed: reconcile before any fresh seed")


if __name__ == "__main__":
    main()
