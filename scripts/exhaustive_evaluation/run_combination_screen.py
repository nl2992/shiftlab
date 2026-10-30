"""Register, then execute a reproducible 540-combination DEVELOPMENT screen."""

import argparse
import hashlib
import json
import platform
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search.combination_screen import combinations, config_dicts, make_world, screen

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/round1"
MANIFEST = DOC / "round1_registration.json"
CASES = [
    ("null", 5),
    ("nuisance", 5),
    ("abrupt", 5),
    ("small", 5),
    ("late", 5),
    ("recurring", 5),
    ("guidance_failure", 5),
    ("abrupt", 24),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register():
    if MANIFEST.exists():
        raise FileExistsError("Registration is immutable; inspect it rather than overwrite")
    value = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exploratory_development_not_confirmation",
        "config_count": 540,
        "configs": config_dicts(),
        "cases": CASES,
        "paths": 64,
        "horizon": 1200,
        "frac": 0.20,
        "budget": 240,
        "world_seed_base": 202610300,
        "query_seed_base": 202610400,
        "known_nominal": True,
        "tolerance": 0.0,
        "alpha": 0.05,
        "primary_diagnostic": "whole-sequence null alarm rate then post-onset detection and harm-to-alarm",
        "exclusions": "not net switching utility; not real data; not faithful published baseline reproduction",
        "engine_sha256": sha(ROOT / "src/shiftlab/sota_search/combination_screen.py"),
        "runner_sha256": sha(Path(__file__)),
    }
    MANIFEST.write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(f"Registered {value['config_count']} distinct combinations", flush=True)


def run():
    reg = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert reg["engine_sha256"] == sha(ROOT / "src/shiftlab/sota_search/combination_screen.py")
    assert reg["runner_sha256"] == sha(Path(__file__))
    configs = combinations()
    assert [asdict(c) for c in configs] == [
        {k: v for k, v in c.items() if k != "id"} for c in reg["configs"]
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    statusfile = MANIFEST.with_name(MANIFEST.name.replace("_registration", "_status"))
    if statusfile.exists():
        raise FileExistsError("Run already has a status; inspect its live handle before resuming")
    status = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "registration_sha256": sha(MANIFEST),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "completed_cases": [],
    }
    statusfile.write_text(json.dumps(status, indent=2), encoding="utf-8")
    rows = []
    for j, (kind, delay) in enumerate(reg["cases"]):
        start = time.perf_counter()
        stream = make_world(
            kind, paths=reg["paths"], horizon=reg["horizon"], seed=reg["world_seed_base"] + j
        )
        result = screen(
            stream,
            configs,
            frac=reg["frac"],
            budget=reg["budget"],
            delay=delay,
            seed=reg["query_seed_base"] + j,
        )
        name = f"{j:02d}_{kind}_d{delay}"
        np.savez_compressed(OUT / f"{name}.npz", **result)
        active = stream["evaluator"]["active"]
        onset = active.argmax(1)
        T = reg["horizon"]
        harm = np.maximum(stream["evaluator"]["harm"], 0)
        cumharm = np.cumsum(harm, axis=1)
        for i, cfg in enumerate(reg["configs"]):
            alarm = result["first"][i]
            upto = np.maximum(np.minimum(alarm, T - 1) - 1, 0)
            harm_to_alarm = np.where(alarm > 0, cumharm[np.arange(reg["paths"]), upto], 0)
            rows.append(
                {
                    "id": cfg["id"],
                    "case": name,
                    "kind": kind,
                    "delay": delay,
                    "alarm_rate": float(np.mean(alarm < T)),
                    "pre_alarm": float(np.mean(alarm < onset)),
                    "post_power": float(np.mean((alarm >= onset) & (alarm < T))),
                    "mean_censored_alarm": float(alarm.mean()),
                    "harm_to_alarm": float(harm_to_alarm.mean()),
                    "labels": float(result["labels"][i].mean()),
                    "labels_max": int(result["labels"][i].max()),
                }
            )
        pd.DataFrame(rows).to_csv(OUT / "metrics.csv", index=False)
        status["completed_cases"].append(
            {
                "case": name,
                "seconds": time.perf_counter() - start,
                "configs_completed": len(configs),
            }
        )
        statusfile.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(
            name,
            "completed",
            len(configs),
            "configs;",
            round(time.perf_counter() - start, 2),
            "seconds",
            flush=True,
        )
    status.update(
        status="completed",
        finished_utc=datetime.now(UTC).isoformat(),
        distinct_configurations_tested=len(configs),
        config_case_evaluations=len(rows),
        metrics_sha256=sha(OUT / "metrics.csv"),
    )
    statusfile.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("register", "run"))
    p.add_argument(
        "--corrected",
        action="store_true",
        help="Separately registered correction; preserve v1 artifacts",
    )
    args = p.parse_args()
    if args.corrected:
        MANIFEST = DOC / "round1_corrected_registration.json"
        OUT = ROOT / "outputs/exhaustive_evaluation/round1_corrected"
    register() if args.action == "register" else run()
