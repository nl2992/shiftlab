"""Register/run paired-benefit round with explicit promotion and net-cost metrics."""

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search.combination_screen import Combination, screen
from shiftlab.sota_search.paired_control import paired_configurations, paired_screen, paired_world
from shiftlab.sota_search.paired_references import paired_fixed_mixture, paired_paper_reference

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/round3_paired"
REG = DOC / "round3_registration.json"
STATUS = DOC / "round3_status.json"
CASES = [
    ("harmful", 5),
    ("tie", 5),
    ("identical", 5),
    ("useful_initial", 5),
    ("useful", 5),
    ("small", 5),
    ("late", 5),
    ("reversal", 5),
    ("useful", 24),
]
SOURCE = [
    "src/shiftlab/sota_search/paired_control.py",
    "src/shiftlab/sota_search/paired_references.py",
    "src/shiftlab/sota_search/combination_screen.py",
    "src/shiftlab/sota_search/published_baselines.py",
    "scripts/exhaustive_evaluation/run_paired_round.py",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def register():
    if REG.exists():
        raise FileExistsError("immutable round3 registration exists")
    configs = paired_configurations()
    assert len(configs) == len(set(configs)) == 648
    value = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exploratory development, no novelty claim",
        "motivation": "negative alarm-to-challenger real pilots; test independent benefit certification",
        "configurations": [dict(id=f"R3_{i:04d}", **asdict(c)) for i, c in enumerate(configs)],
        "activity_audit": "modes change eligible evidence; all query/pace/bet/memory/capital dimensions can change behavior; no guidance-floor aliases",
        "cases": CASES,
        "paths": 128,
        "horizon": 2000,
        "frac": 0.2,
        "budget": 400,
        "delay_contract": "fixed event delay",
        "alpha": 0.05,
        "benefit_margin": 0.01,
        "query_cost": 0.001,
        "switch_cost": 1.0,
        "world_seed_base": 202614000,
        "query_seed_base": 202615000,
        "primary": "realized total cost delta versus no switch; null promotion probability separately",
        "source_risk": "absolute gate uses known synthetic nominal; paired target needs no source-risk calibration",
        "guarantee_scope": "conditional paired mean null for a frozen candidate; no future-gain guarantee under reversals",
        "baselines": [
            "no_action",
            "always_candidate",
            "existing_fixed_mixture_IPW",
            "paired_PR_PM_EB",
            "paired_RCPS_FTL",
            "unsafe_alarm_only",
        ],
        "sources_sha256": {p: sha(ROOT / p) for p in SOURCE},
    }
    REG.write_text(json.dumps(value, indent=2), encoding="utf-8")
    for p in SOURCE:
        (DOC / ("round3_executed_" + Path(p).name + ".txt")).write_bytes((ROOT / p).read_bytes())
    print("Registered 648 paired-control combinations and six references", flush=True)


def run():
    reg = json.loads(REG.read_text())
    assert all(sha(ROOT / p) == v for p, v in reg["sources_sha256"].items())
    if STATUS.exists():
        raise FileExistsError("inspect existing run handle before restarting")
    OUT.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "registration_sha256": sha(REG),
        "completed_cases": [],
    }
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    configs = paired_configurations()
    rows = []
    for j, (kind, delay) in enumerate(reg["cases"]):
        started = time.perf_counter()
        S, T = reg["paths"], reg["horizon"]
        s = paired_world(kind, paths=S, horizon=T, seed=reg["world_seed_base"] + j)
        kw = {
            "frac": reg["frac"],
            "budget": reg["budget"],
            "delay": delay,
            "seed": reg["query_seed_base"] + j,
            "alpha": reg["alpha"],
            "margin": reg["benefit_margin"],
            "query_cost": reg["query_cost"],
            "switch_cost": reg["switch_cost"],
        }
        result = paired_screen(s, configs, **kw)
        name = f"{j:02d}_{kind}_d{delay}"
        np.savez_compressed(OUT / (name + ".npz"), **result)
        entries = [
            (f"R3_{i:04d}", {k: v[i] for k, v in result.items()}) for i in range(len(configs))
        ]
        for tag, value in [
            ("existing_fixed_mixture_IPW", paired_fixed_mixture(s, **kw)),
            ("paired_PR_PM_EB", paired_paper_reference(s, method="pr", **kw)),
            ("paired_RCPS_FTL", paired_paper_reference(s, method="rcps", **kw)),
        ]:
            entries.append((tag, value))
            np.savez_compressed(OUT / (tag + "_" + name + ".npz"), **value)
        unsafe = screen(
            s,
            [Combination(0.25, 0.9, 0.75, "uniform", True)],
            frac=reg["frac"],
            budget=reg["budget"],
            delay=delay,
            seed=reg["query_seed_base"] + j,
            alpha=reg["alpha"],
            return_accounting=True,
        )
        alarm = unsafe["first"][0]
        old0 = np.pad(np.cumsum(s["loss"], axis=1), ((0, 0), (1, 0)))
        old1 = np.pad(np.cumsum(s["candidate_loss"], axis=1), ((0, 0), (1, 0)))
        decision = old0[np.arange(S), alarm] + old1[:, T] - old1[np.arange(S), alarm]
        total = (
            decision
            + reg["query_cost"] * unsafe["labels_at_alarm"][0]
            + reg["switch_cost"] * (alarm < T)
        )
        unsafe_value = {
            "first": alarm,
            "labels": unsafe["labels_at_alarm"][0],
            "decision_cost": decision,
            "total_cost": total,
            "delta_vs_incumbent": total - old0[:, T],
        }
        entries.append(("unsafe_alarm_only", unsafe_value))
        np.savez_compressed(OUT / ("unsafe_alarm_only_" + name + ".npz"), **unsafe_value)
        for tag, first, dc in [
            ("no_action", np.full(S, T), old0[:, T]),
            ("always_candidate", np.zeros(S, dtype=int), old1[:, T]),
        ]:
            total = dc + reg["switch_cost"] * (first < T)
            entries.append(
                (
                    tag,
                    {
                        "first": first,
                        "labels": np.zeros(S, dtype=int),
                        "decision_cost": dc,
                        "total_cost": total,
                        "delta_vs_incumbent": total - old0[:, T],
                    },
                )
            )
        for tag, value in entries:
            rows.append(
                {
                    "id": tag,
                    "case": name,
                    "kind": kind,
                    "delay": delay,
                    "promotion_rate": float(np.mean(value["first"] < T)),
                    "total_cost": float(value["total_cost"].mean()),
                    "delta_vs_incumbent": float(value["delta_vs_incumbent"].mean()),
                    "worsening_probability": float(np.mean(value["delta_vs_incumbent"] > 0)),
                    "labels": float(value["labels"].mean()),
                    "labels_max": int(value["labels"].max()),
                    "mean_promotion_time": float(value["first"].mean()),
                    "null_case": kind in ("harmful", "tie", "identical"),
                }
            )
        pd.DataFrame(rows).to_csv(OUT / "metrics.csv", index=False)
        status["completed_cases"].append(
            {"case": name, "configurations": len(configs), "seconds": time.perf_counter() - started}
        )
        STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(
            name,
            "completed",
            len(configs),
            "combinations;",
            round(time.perf_counter() - started, 2),
            "seconds",
            flush=True,
        )
    status.update(
        status="completed",
        finished_utc=datetime.now(UTC).isoformat(),
        effective_configurations=len(configs),
        config_case_evaluations=len(configs) * len(CASES),
        metrics_sha256=sha(OUT / "metrics.csv"),
    )
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["register", "run"])
    args = p.parse_args()
    register() if args.action == "register" else run()
