"""Register/run round-two development compositions and paper-formula comparators."""

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search.bottleneck_round import bottleneck_combinations
from shiftlab.sota_search.combination_screen import Combination, make_world, screen
from shiftlab.sota_search.published_baselines import (
    active_rcps_cost,
    pprm_batch_cost,
    pr_empirical_bernstein,
)

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/round2"
REG = DOC / "round2_registration.json"
STATUS = DOC / "round2_status.json"
CASES = [
    ("null", 5, 0),
    ("nuisance", 5, 0),
    ("abrupt", 5, 0),
    ("small", 5, 0),
    ("late", 5, 0),
    ("recurring", 5, 0),
    ("guidance_failure", 5, 0),
    ("abrupt", 24, 0),
    ("null", 5, 300),
    ("abrupt", 5, 300),
    ("late", 5, 1000),
    ("late", 5, 5000),
]
SOURCES = [
    "src/shiftlab/sota_search/combination_screen.py",
    "src/shiftlab/sota_search/bottleneck_round.py",
    "src/shiftlab/sota_search/published_baselines.py",
    "scripts/exhaustive_evaluation/run_bottleneck_round.py",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def register():
    if REG.exists():
        raise FileExistsError("immutable registration exists")
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exploratory development",
        "motivation": "round1 late-harm weakness, propensity range penalty and fragile guidance",
        "configs": [
            dict(id=f"R2_{i:04d}", **asdict(c)) for i, c in enumerate(bottleneck_combinations())
        ],
        "cases": CASES,
        "paths": 96,
        "horizon": 2000,
        "frac": 0.2,
        "budget": 400,
        "alpha_test": 0.04,
        "alpha_calibration": 0.01,
        "world_seed_base": 202611000,
        "query_seed_base": 202612000,
        "primary": "shift-attributable harm before first alarm, subject to null and resource checks",
        "warning": "not net switching cost, not independent confirmation, not a novelty claim",
        "sources_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "comparators": [
            "round1_top",
            "matched_cost_parent",
            "original_H2c_style",
            "active_RCPS_FTL_cost_adapter",
            "PR_PM_EB_cost_formula",
            "PPRM_batched_CM_EB_cost_formula",
        ],
    }
    REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    for p in SOURCES:
        (DOC / ("round2_executed_" + Path(p).name + ".txt")).write_bytes((ROOT / p).read_bytes())
    print("Registered", len(reg["configs"]), "new compositions,", len(CASES), "cases", flush=True)


def run():
    reg = json.loads(REG.read_text())
    assert all(sha(ROOT / p) == v for p, v in reg["sources_sha256"].items())
    if STATUS.exists():
        raise FileExistsError("inspect existing run/handle; do not restart")
    OUT.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "running",
        "registration_sha256": sha(REG),
        "started_utc": datetime.now(UTC).isoformat(),
        "completed_cases": [],
    }
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    configs = bottleneck_combinations()
    anchors = [
        Combination(0.25, 0.9, 0.75, "uniform", True),
        Combination(0, 0.9, 0.75, "uniform", True),
        Combination(1, 0.995, 0.5, "uniform", False),
    ]
    ids = [c["id"] for c in reg["configs"]] + reg["comparators"][:3]
    rows = []
    for j, (kind, delay, ncal) in enumerate(reg["cases"]):
        start = time.perf_counter()
        st = make_world(
            kind, paths=reg["paths"], horizon=reg["horizon"], seed=reg["world_seed_base"] + j
        )
        if ncal:
            cal = make_world(
                "null", paths=reg["paths"], horizon=ncal, seed=reg["world_seed_base"] + 10000 + j
            )
            st["r0"] = np.minimum(
                1, cal["loss"].mean(1) + np.sqrt(np.log(1 / reg["alpha_calibration"]) / (2 * ncal))
            )
        kw = {
            "budget": reg["budget"],
            "delay": delay,
            "seed": reg["query_seed_base"] + j,
            "alpha": reg["alpha_test"],
        }
        result = screen(st, configs + anchors, frac=reg["frac"], return_accounting=True, **kw)
        name = f"{j:02d}_{kind}_d{delay}_cal{ncal}"
        np.savez_compressed(OUT / (name + ".npz"), **result)
        results = [(ids[i], {k: v[i] for k, v in result.items()}) for i in range(len(ids))]
        for tag, monitor in zip(
            reg["comparators"][3:],
            (active_rcps_cost, pr_empirical_bernstein, pprm_batch_cost),
            strict=True,
        ):
            # PPRM uses one random label per five-event batch; a distinct batch
            # observation contract with the same maximum label count, disclosed.
            extra = {} if monitor == pprm_batch_cost else {"frac": reg["frac"]}
            value = monitor(st, **kw, **extra)
            results.append((tag, value))
            np.savez_compressed(OUT / (tag + "_" + name + ".npz"), **value)
        onset = st["evaluator"]["active"].argmax(1)
        cum = np.cumsum(np.maximum(st["evaluator"]["harm"], 0), axis=1)
        for tag, value in results:
            alarm = value["first"]
            T = reg["horizon"]
            upto = np.maximum(np.minimum(alarm, T - 1) - 1, 0)
            rows.append(
                {
                    "id": tag,
                    "case": name,
                    "kind": kind,
                    "delay": delay,
                    "ncal": ncal,
                    "alarm_rate": float(np.mean(alarm < T)),
                    "pre_alarm": float(np.mean(alarm < onset)),
                    "post_power": float(np.mean((alarm >= onset) & (alarm < T))),
                    "harm_to_alarm": float(
                        np.mean(np.where(alarm > 0, cum[np.arange(reg["paths"]), upto], 0))
                    ),
                    "labels": float(value["labels"].mean()),
                    "labels_max": int(value["labels"].max()),
                    "calibration_labels": ncal,
                    "nominal_upper_mean": float(np.mean(st["r0"])),
                }
            )
        pd.DataFrame(rows).to_csv(OUT / "metrics.csv", index=False)
        status["completed_cases"].append(
            {
                "case": name,
                "configs_completed": len(configs),
                "seconds": time.perf_counter() - start,
            }
        )
        STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(
            name,
            "completed",
            len(configs),
            "compositions + 6 references;",
            round(time.perf_counter() - start, 2),
            "seconds",
            flush=True,
        )
    status.update(
        status="completed",
        finished_utc=datetime.now(UTC).isoformat(),
        distinct_round2_configs=len(configs),
        new_config_case_evaluations=len(configs) * len(CASES),
        metric_sha256=sha(OUT / "metrics.csv"),
    )
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["register", "run"])
    args = p.parse_args()
    register() if args.action == "register" else run()
