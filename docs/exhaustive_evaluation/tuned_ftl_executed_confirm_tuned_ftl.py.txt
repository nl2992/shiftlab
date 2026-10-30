"""Fresh test against the development-selected FTL family, not a fixed weak setting."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/tuned_ftl_confirmation"
REG = DOC / "tuned_ftl_confirmation_registration.json"
STATUS = DOC / "tuned_ftl_confirmation_status.json"
CASES = ["useful_initial", "useful", "late", "small", "reversal"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def register():
    if REG.exists():
        raise FileExistsError("immutable tuned baseline confirmation exists")
    dev = ROOT / "outputs/exhaustive_evaluation/round3_paired/metrics.csv"
    metrics = pd.read_csv(dev, keep_default_na=False)
    configs = pd.DataFrame(
        json.loads((DOC / "round3_registration.json").read_text())["configurations"]
    )
    eligible = (
        metrics[metrics.kind.isin(["harmful", "tie", "identical"])]
        .groupby("id")
        .promotion_rate.max()
    )
    mean = metrics.groupby("id").delta_vs_incumbent.mean()
    ranked = (
        configs[configs.bet == "ftl"].set_index("id").join(mean).join(eligible.rename("max_null"))
    )
    ranked = ranked[ranked.max_null <= 0.05].sort_values("delta_vs_incumbent")
    winner = ranked.index[0]
    main = configs[configs.id == "R3_0036"].iloc[0]
    baseline = configs[configs.id == winner].iloc[0]
    rows = [main.to_dict(), baseline.to_dict()]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "new independent synthetic matched-tuning comparison",
        "selection": "best FTL mean cost across all original development cases, empirical null screen <=.05; no per-confirmation-cell choice",
        "development_sha256": sha(dev),
        "configs": rows,
        "FTL_parameter_settings_considered": int((configs.bet == "ftl").sum()),
        "cases": CASES,
        "paths": 1000,
        "batch": 250,
        "horizon": 2000,
        "frac": 0.2,
        "budget": 400,
        "delay": 5,
        "alpha": 0.05,
        "margin": 0.01,
        "query_cost": 0.001,
        "switch_cost": 1,
        "world_seed_base": 202622000,
        "query_seed_base": 202623000,
        "primary": "equal-weight mean total cost, four persistent cases, main minus tuned FTL",
        "practical_gate": ">=10 percent cost reduction, paired 95 percent interval below zero",
        "extra": "reversal reported separately; no new real-data confirmation",
        "sources": {
            p: sha(ROOT / p)
            for p in [
                "src/shiftlab/sota_search/paired_control.py",
                "scripts/exhaustive_evaluation/confirm_tuned_ftl.py",
            ]
        },
    }
    REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    for p in reg["sources"]:
        (DOC / ("tuned_ftl_executed_" + Path(p).name + ".txt")).write_bytes((ROOT / p).read_bytes())
    print("Frozen candidate R3_0036 vs best of 324 FTL settings:", winner, flush=True)


def run():
    reg = json.loads(REG.read_text())
    assert all(sha(ROOT / p) == h for p, h in reg["sources"].items())
    if STATUS.exists():
        raise FileExistsError("inspect original process/status before restarting")
    OUT.mkdir(parents=True, exist_ok=True)
    status = {"status": "running", "completed": [], "registration_sha256": sha(REG)}
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    configs = [PairedConfig(**{k: v for k, v in c.items() if k != "id"}) for c in reg["configs"]]
    for j, kind in enumerate(reg["cases"]):
        for b in range(reg["paths"] // reg["batch"]):
            offset = j * 100 + b
            s = paired_world(
                kind,
                paths=reg["batch"],
                horizon=reg["horizon"],
                seed=reg["world_seed_base"] + offset,
            )
            value = paired_screen(
                s,
                configs,
                frac=reg["frac"],
                budget=reg["budget"],
                delay=reg["delay"],
                seed=reg["query_seed_base"] + offset,
                alpha=reg["alpha"],
                margin=reg["margin"],
                query_cost=reg["query_cost"],
                switch_cost=reg["switch_cost"],
            )
            np.savez_compressed(OUT / f"{j:02d}_{kind}_b{b:03d}.npz", **value)
            status["completed"].append([kind, b])
            STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(kind, "1000 fresh paths complete", flush=True)
    status["status"] = "completed"
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


def analyze():
    reg = json.loads(REG.read_text())
    assert json.loads(STATUS.read_text())["status"] == "completed"
    rows = []
    paired = []
    costs = []
    for j, kind in enumerate(reg["cases"]):
        with_arrays = [np.load(p) for p in sorted(OUT.glob(f"{j:02d}_{kind}_b*.npz"))]
        tc = np.concatenate([a["total_cost"] for a in with_arrays], axis=1)
        dc = np.concatenate([a["delta_vs_incumbent"] for a in with_arrays], axis=1)
        assert tc.shape == (2, 1000)
        if kind != "reversal":
            paired.append(tc[0] - tc[1])
            costs.append(tc[1].mean())
        rows.append(
            {
                "case": kind,
                "candidate_cost": float(tc[0].mean()),
                "tuned_ftl_cost": float(tc[1].mean()),
                "paired_difference": float((tc[0] - tc[1]).mean()),
                "candidate_delta_vs_incumbent": float(dc[0].mean()),
                "baseline_delta_vs_incumbent": float(dc[1].mean()),
            }
        )
        for a in with_arrays:
            a.close()
    paired = np.stack(paired)
    estimate = float(paired.mean())
    se = float(np.sqrt(np.sum(paired.var(1, ddof=1) / paired.shape[1])) / len(paired))
    interval = [estimate - 1.96 * se, estimate + 1.96 * se]
    relative = -estimate / np.mean(costs)
    result = {
        "candidate": reg["configs"][0],
        "baseline": reg["configs"][1],
        "primary_delta": estimate,
        "paired_normal_95_interval": interval,
        "relative_cost_reduction": float(relative),
        "practical_gate_pass": bool(relative >= 0.1 and interval[1] < 0),
        "cases": rows,
        "interpretation": "Matched development-selected FTL comparator; fixed-component 27 percent result cannot substitute for this test",
    }
    (DOC / "tuned_ftl_confirmation_decision.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["register", "run", "analyze"])
    args = parser.parse_args()
    {"register": register, "run": run, "analyze": analyze}[args.action]()
