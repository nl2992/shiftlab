"""Execute the frozen WP3 twenty-seed, late-onset development screen."""

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
from scipy.special import logsumexp

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.comparison_betting_engines import replay_engine
from shiftlab.dive.data_efficient_prescreen import (
    HORIZON,
    STARTS,
    _log_factors_to_detector,
    evidence_replays,
    optional_policy_replay,
)
from shiftlab.dive.data_efficient_source_panel import build_path, source_panel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / "docs/data_efficient_edetector_prescreen_protocol.md"
OUT = ROOT / "outputs/data_efficient_prescreen_20"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def first_alarm(logs: np.ndarray, threshold: float) -> int | None:
    hits = np.flatnonzero(logs >= np.log(threshold))
    return int(hits[0]) if len(hits) else None


def endpoint(alarm: int | None, onset: int) -> dict:
    detected = alarm is not None and onset <= alarm < HORIZON
    return {
        "first_alarm": alarm,
        "detected": detected,
        "pre_onset_alarm": alarm is not None and alarm < onset,
        "delay_censored": alarm - onset if detected else HORIZON - onset,
    }


def original_alarms(record: dict) -> list[tuple[str, str, int | None]]:
    """Preserve source-specific factors and restart the EB engine at each start."""
    logs = np.asarray(record["source_original_logs"], dtype=float)
    padded = np.pad(logs, (0, HORIZON - len(logs)), constant_values=logs[-1])
    gains = np.diff(np.r_[0.0, padded])
    engine = "source_pm_eb" if record["arm"] == "gated_eb_paced" else "source_fixed0p9"
    rows = [(engine, "fixed_start", first_alarm(padded, 20.0))]
    for kind in ("sr", "cusum"):
        _, alarm = _log_factors_to_detector(gains, kind=kind)
        rows.append((engine, kind, alarm))
    components = []
    values = np.pad(record["values"], (0, HORIZON - len(logs)))
    bounds = np.pad(record["bounds"], (0, HORIZON - len(logs)), mode="edge")
    for start in STARTS:
        path = np.zeros(HORIZON)
        path[start:] = (
            replay_engine(values[start:], bounds[start:], "pm_eb")
            if engine == "source_pm_eb"
            else np.cumsum(gains[start:])
        )
        components.append(path)
    started = logsumexp(components, axis=0) - np.log(len(STARTS))
    rows.append((engine, "started", first_alarm(started, 20.0)))
    return rows


def one_path(task: tuple[int, float, str]) -> list[dict]:
    seed, onset_fraction, device = task
    started = time.perf_counter()
    path = build_path(seed, onset_fraction, device)
    onset = path.scheduled_onset - 800
    rows = []
    for rate in (0.02, 0.05, 0.10, 0.20):
        records = source_panel(path, rate)
        budget = rate * HORIZON * float(path.tariffs[400:800].mean())
        for policy in ("uniform", "paced", "temporal", "candidate"):
            result = optional_policy_replay(
                path.x[800:],
                path.disagreement[800:],
                path.tariffs[800:],
                path.centered_cost[800:],
                path.common_uniforms[:HORIZON],
                validation_active=path.disagreement[400:800],
                validation_tariffs=path.tariffs[400:800],
                budget=budget,
                policy=policy,
            )
            records.append(
                {
                    "arm": "optional_" + policy,
                    "values": result["scores"],
                    "bounds": np.full(HORIZON, 5.1),
                    "labels": result["labels"],
                    "dollars": result["dollars"],
                    "budget": result["budget"],
                    "skipmask": ~result["selected"],
                    "theta_pre": float(result["theta"][:onset].mean()),
                    "theta_post": float(result["theta"][onset:].mean()),
                    "labels_pre": int(result["labels_mask"][:onset].sum()),
                    "labels_post": int(result["labels_mask"][onset:].sum()),
                    "cap_stop_index": result["cap_stop_index"],
                }
            )
        for record in records:
            shared = {
                "seed": seed,
                "onset_fraction": onset_fraction,
                "budget_rate": rate,
                "onset_event": onset,
                "arm": record["arm"],
                "labels": record["labels"],
                "dollars": record["dollars"],
                "budget": record["budget"],
                "same_null_harm_comparator": record["arm"]
                not in {"full_feedback", "feature_adwin"},
            }
            for key in ("theta_pre", "theta_post", "labels_pre", "labels_post", "cap_stop_index"):
                shared[key] = record.get(key)
            if record["budget"] is not None and record["dollars"] > record["budget"] + 1e-9:
                raise AssertionError("source arm exceeds registered cap")
            if record["values"] is None:
                rows.append(
                    {
                        **shared,
                        "engine": "ADWIN",
                        "detector": "feature_sentinel",
                        **endpoint(record["first_alarm"], onset),
                    }
                )
                continue
            evidence = evidence_replays(record["values"], record["bounds"], record.get("skipmask"))
            for detector, key in (
                ("fixed_start", "fixed_start_alarms"),
                ("started", "started_mixture_alarms"),
                ("sr", "sr_alarms"),
                ("cusum", "cusum_alarms"),
            ):
                for engine, alarm in evidence[key].items():
                    rows.append(
                        {**shared, "engine": engine, "detector": detector, **endpoint(alarm, onset)}
                    )
            if record.get("source_original_logs") is not None:
                for engine, detector, alarm in original_alarms(record):
                    rows.append(
                        {**shared, "engine": engine, "detector": detector, **endpoint(alarm, onset)}
                    )
    print(
        f"completed seed={seed} onset={onset_fraction} rows={len(rows)} seconds={time.perf_counter() - started:.2f}",
        flush=True,
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    match = re.search(
        r"\*\*Freeze commit:\*\* `([0-9a-f]{40})`", PROTOCOL.read_text(encoding="utf-8")
    )
    if match is None:
        raise RuntimeError("protocol not frozen")
    git("rev-parse", "--verify", match[1] + "^{commit}")
    sources = [
        PROTOCOL,
        Path(__file__),
        ROOT / "uv.lock",
        ROOT / "scripts/reproduce_timans_risk_monitor_paired_cost.py",
    ] + sorted((ROOT / "src/shiftlab").rglob("*.py"))
    for source in sources:
        relative = str(source.relative_to(ROOT))
        git("diff", "--exit-code", "HEAD", "--", relative)
        if not git("ls-files", "--", relative):
            raise RuntimeError(f"source not committed: {relative}")
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite {OUT}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tasks = [(seed, onset, device) for onset in (0.75, 0.50) for seed in range(59000000, 59000020)]
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git("rev-parse", "HEAD"),
        "dirty_paths": git("status", "--porcelain").splitlines(),
        "device": device,
        "hardware": environment(),
        "workers": args.workers,
        "tasks": tasks,
        "thread_environment": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
    }
    OUT.mkdir(parents=True)
    (OUT / "launch.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    start = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(args.workers, mp_context=get_context("spawn")) as pool:
        for index, block in enumerate(pool.map(one_path, tasks)):
            pd.DataFrame(block).to_csv(OUT / f"path_{index:02d}.csv", index=False)
            rows.extend(block)
    pd.DataFrame(rows).to_csv(OUT / "streams.csv", index=False)
    manifest.update(
        runtime_seconds=time.perf_counter() - start,
        rows=len(rows),
        recorded_at_utc=datetime.now(UTC).isoformat(),
        outputs_sha256={p.name: digest(p) for p in OUT.iterdir() if p.is_file()},
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"rows": len(rows), "runtime_seconds": manifest["runtime_seconds"]}), flush=True
    )


if __name__ == "__main__":
    main()
