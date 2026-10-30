"""Frozen fresh-seed synthetic confirmation, not real-data or novelty confirmation."""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from shiftlab.sota_search.combination_screen import Combination, screen
from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world
from shiftlab.sota_search.paired_references import paired_fixed_mixture, paired_paper_reference

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/paired_confirmation"
REG = DOC / "paired_synthetic_confirmation_registration.json"
STATUS = DOC / "paired_synthetic_confirmation_status.json"
SOURCES = [
    "src/shiftlab/sota_search/paired_control.py",
    "src/shiftlab/sota_search/paired_references.py",
    "src/shiftlab/sota_search/combination_screen.py",
    "src/shiftlab/sota_search/published_baselines.py",
    "scripts/exhaustive_evaluation/confirm_paired_synthetic.py",
]
CASES = [
    ("harmful", 5000),
    ("tie", 5000),
    ("harmful_after_shift", 5000),
    ("useful_initial", 1000),
    ("useful", 1000),
    ("late", 1000),
    ("small", 1000),
    ("reversal", 1000),
]
IDS = ["selected_discounted", "pooled_parent", "fixed_mixture", "paired_RCPS", "unsafe_alarm_only"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def register():
    if REG.exists():
        raise FileExistsError("immutable confirmation registration exists")
    value = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "independent synthetic confirmation of restricted components; not novelty/G4 claim",
        "cases": CASES,
        "horizon": 2000,
        "batch_paths": 250,
        "delay": 5,
        "frac": 0.2,
        "budget": 400,
        "alpha": 0.05,
        "margin": 0.01,
        "query_cost": 0.001,
        "switch_cost": 1,
        "world_seed_base": 202620000,
        "query_seed_base": 202621000,
        "shortlist": "R3_0036 selected on development only; matched gamma=1 parent",
        "candidates": [
            {
                "mode": "direct",
                "allocation": "uniform",
                "gamma": g,
                "cap": 0.75,
                "restart": False,
                "pace": "none",
                "bet": "kelly",
            }
            for g in (0.98, 1)
        ],
        "methods": IDS,
        "primary": "equal-weight mean total cost across four persistent-benefit cases versus fixed paired_RCPS",
        "practical_gate": ">=10 percent reduction in mean total cost, paired 95 percent interval below zero",
        "safety_gate": "one-sided Clopper-Pearson upper <=.06 on each null; simultaneous confidence .95 across 4 paired methods x 3 nulls",
        "adversarial_gate": "reversal mean cost excess <=5 versus no action; failure forbids general dynamic-benefit claim",
        "inference": "independent paths; paired same streams; Bonferroni one-sided intervals for null size; fresh seeds disjoint from development",
        "sources_sha256": {p: sha(ROOT / p) for p in SOURCES},
    }
    REG.write_text(json.dumps(value, indent=2), encoding="utf-8")
    for p in SOURCES:
        (DOC / ("confirmation_executed_" + Path(p).name + ".txt")).write_bytes(
            (ROOT / p).read_bytes()
        )
    print(
        "Frozen restricted confirmation:",
        sum(n for _, n in CASES),
        "independent paths across 8 cases",
        flush=True,
    )


def run():
    reg = json.loads(REG.read_text())
    assert all(sha(ROOT / p) == v for p, v in reg["sources_sha256"].items())
    if STATUS.exists():
        raise FileExistsError("inspect original handle/status; do not restart")
    OUT.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "registration_sha256": sha(REG),
        "completed_batches": [],
    }
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    configs = [PairedConfig(**d) for d in reg["candidates"]]
    for j, (kind, N) in enumerate(reg["cases"]):
        for batch in range((N + reg["batch_paths"] - 1) // reg["batch_paths"]):
            start = time.perf_counter()
            S = min(reg["batch_paths"], N - batch * reg["batch_paths"])
            T = reg["horizon"]
            seedoffset = j * 100 + batch
            s = paired_world(kind, paths=S, horizon=T, seed=reg["world_seed_base"] + seedoffset)
            kw = {
                "frac": reg["frac"],
                "budget": reg["budget"],
                "delay": reg["delay"],
                "seed": reg["query_seed_base"] + seedoffset,
                "alpha": reg["alpha"],
                "margin": reg["margin"],
                "query_cost": reg["query_cost"],
                "switch_cost": reg["switch_cost"],
            }
            value = paired_screen(s, configs, **kw)
            results = [{k: v[i] for k, v in value.items()} for i in range(len(configs))]
            results.append(paired_fixed_mixture(s, **kw))
            results.append(paired_paper_reference(s, method="rcps", **kw))
            alarm = screen(
                s,
                [Combination(0.25, 0.9, 0.75, "uniform", True)],
                frac=reg["frac"],
                budget=reg["budget"],
                delay=reg["delay"],
                seed=reg["query_seed_base"] + seedoffset,
                alpha=reg["alpha"],
                return_accounting=True,
            )
            first = alarm["first"][0]
            p0 = np.pad(np.cumsum(s["loss"], axis=1), ((0, 0), (1, 0)))
            p1 = np.pad(np.cumsum(s["candidate_loss"], axis=1), ((0, 0), (1, 0)))
            dc = p0[np.arange(S), first] + p1[:, T] - p1[np.arange(S), first]
            tc = (
                dc
                + reg["query_cost"] * alarm["labels_at_alarm"][0]
                + reg["switch_cost"] * (first < T)
            )
            results.append(
                {
                    "first": first,
                    "labels": alarm["labels_at_alarm"][0],
                    "total_cost": tc,
                    "delta_vs_incumbent": tc - p0[:, T],
                }
            )
            stacked = {
                k: np.stack([r[k] for r in results])
                for k in ("first", "labels", "total_cost", "delta_vs_incumbent")
            }
            name = f"{j:02d}_{kind}_b{batch:03d}"
            np.savez_compressed(OUT / (name + ".npz"), **stacked)
            status["completed_batches"].append(
                {"case": kind, "batch": batch, "paths": S, "seconds": time.perf_counter() - start}
            )
            STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(kind, N, "paths completed", flush=True)
    status.update(status="completed", finished_utc=datetime.now(UTC).isoformat())
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


def analyze():
    reg = json.loads(REG.read_text())
    assert json.loads(STATUS.read_text())["status"] == "completed"
    rows = []
    data = {}
    for j, (kind, N) in enumerate(reg["cases"]):
        batches = [np.load(p) for p in sorted(OUT.glob(f"{j:02d}_{kind}_b*.npz"))]
        values = {k: np.concatenate([b[k] for b in batches], axis=1) for k in batches[0].files}
        assert values["first"].shape == (5, N)
        data[kind] = values
        for i, name in enumerate(reg["methods"]):
            K = int(np.sum(values["first"][i] < reg["horizon"]))
            upper = float(beta.ppf(1 - 0.05 / 12, K + 1, N - K)) if K < N else 1.0
            rows.append(
                {
                    "case": kind,
                    "method": name,
                    "N": N,
                    "promotions": K,
                    "promotion_rate": K / N,
                    "simultaneous_null_upper": upper
                    if kind in ("harmful", "tie", "harmful_after_shift") and i < 4
                    else np.nan,
                    "total_cost": float(values["total_cost"][i].mean()),
                    "delta_vs_incumbent": float(values["delta_vs_incumbent"][i].mean()),
                    "labels": float(values["labels"][i].mean()),
                }
            )
        for b in batches:
            b.close()
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "summary.csv", index=False)
    persistent = ["useful_initial", "useful", "late", "small"]
    delta = np.stack([data[k]["total_cost"][0] - data[k]["total_cost"][3] for k in persistent])
    estimate = float(delta.mean())
    se = float(np.sqrt(np.sum(delta.var(axis=1, ddof=1) / delta.shape[1])) / len(persistent))
    comparator = float(np.mean([data[k]["total_cost"][3].mean() for k in persistent]))
    interval = [estimate - 1.96 * se, estimate + 1.96 * se]
    reduction = -estimate / comparator
    safety = table[
        (table.method == "selected_discounted")
        & table.case.isin(["harmful", "tie", "harmful_after_shift"])
    ]
    reversal = float(data["reversal"]["delta_vs_incumbent"][0].mean())
    verdict = {
        "status": "analyzed",
        "primary_paired_delta": estimate,
        "paired_normal_95_interval": interval,
        "relative_cost_reduction": reduction,
        "practical_gate_pass": bool(reduction >= 0.1 and interval[1] < 0),
        "safety_gate_pass": bool((safety.simultaneous_null_upper <= 0.06).all()),
        "reversal_mean_excess": reversal,
        "adversarial_gate_pass": bool(reversal <= 5),
        "scope": "restricted synthetic component confirmation, not real transfer or novelty",
    }
    (DOC / "paired_confirmation_decision.json").write_text(
        json.dumps(verdict, indent=2), encoding="utf-8"
    )
    print(json.dumps(verdict), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["register", "run", "analyze"])
    args = p.parse_args()
    {"register": register, "run": run, "analyze": analyze}[args.action]()
