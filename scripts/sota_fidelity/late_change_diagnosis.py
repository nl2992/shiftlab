"""Track B mechanism diagnosis for late improvement.

Protocol (locked before running): docs/sota_fidelity/late_change_diagnosis_protocol.md.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint",
           ROOT / "scripts/promising_directions/sota/competitors", ROOT / "scripts/sota_fidelity"):
    sys.path.insert(0, str(_p))

SEED_BASE = 2026120701
SEEDS = 100
LATE = ["F1_late_400", "F1_late_800", "F1_late_1200", "S_late_1500"]
CELLS = [f"{r}@B{b}" for r in LATE for b in (100, 200, 400)] + ["F1_late_800_d10", "F1_late_800_d400"]
HOSTS = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
         "SMCS+retain-incumbent"]
RMM = ["rmm:gated_deployment+RMM", "rmm:gated_deployment+RMM_noacq", "rmm:gated_deployment+RMM_single",
       "rmm:gated_deployment+RMM_norestart"]
LRMD = ["rmm:LRMD_k1", "rmm:LRMD", "rmm:LRMD_k3", "rmm:LRMD_single"]
FID = ["two_sided_esr_label_clock", "esr_rmmbets_fullalpha", "han_arw_label_clock",
       "shekhar_ramdas_rcs_t3_anyexcl"]
POLICIES = ["CONTROL_never_switch"] + HOSTS + RMM + LRMD + FID


def resolve(cell: str):
    from bench import CONTRACT, parse_regime

    if cell.startswith("F1_late_800_d"):
        R, _ = parse_regime("F1_late_800")
        return dataclasses.replace(R, name=cell, delay=int(cell.split("_d")[-1])), CONTRACT["budget"]
    R, b = parse_regime(cell)
    return R, b or CONTRACT["budget"]


def change_time(R) -> int:
    return int(R.p[1][0])


def _extra():
    from smoke_shin_esr import build_extra

    extra = build_extra()
    mod = sys.modules["atlas_v2_restart_monitor"]
    for k in ("gated_deployment+RMM_norestart", "LRMD_k3", "LRMD_single", "LRMD"):
        extra.setdefault(f"rmm:{k}", (lambda f: lambda T, B, cs, cq, a, d, r: f(T, B, cs, cq, a, d, r))(
            mod.FACTORIES[k]))
    return extra


def _job(args):
    import screen
    from bench import CONTRACT
    from simulator import run_episode
    from suite import build_suite, stream_from_losses

    cell, seed = args
    R, budget = resolve(cell)
    c = change_time(R)
    losses = R.sample(np.random.default_rng(np.random.SeedSequence([SEED_BASE, screen._h(cell), seed])))
    rows = []
    for pol in build_suite(losses.shape[0], budget, CONTRACT["cs"], CONTRACT["cq"], CONTRACT["alpha"],
                           R.delay, seed, SEED_BASE + screen._h(cell) % 1000, names=POLICIES,
                           extra=_extra()):
        preds, labels = stream_from_losses(losses, np.random.default_rng([SEED_BASE, screen._h(cell), seed, 7]))
        res = run_episode(pol, model_predictions=preds, labels=labels, delay=R.delay, budget=budget,
                          label_price=CONTRACT["cq"], switch_cost=CONTRACT["cs"], trace=True)
        assert res.requested_labels <= budget, pol.name
        dep = np.fromiter((r["deployed_model"] for r in res.records), int, len(res.records))
        req = np.fromiter((r["requested"] for r in res.records), int, len(res.records))
        post = np.flatnonzero(dep[c:] == 1)
        rows.append({
            "cell": cell, "seed": seed, "policy": pol.name, "change": c, "budget": budget,
            "delay": R.delay, "net": res.net_cost, "switches": res.deployment_switches,
            "promoted_before_change": int((dep[:c] == 1).any()),
            "detect_delay": int(post[0]) if len(post) else -1,
            "labels_before": int(req[:c].sum()), "labels_after": int(req[c:].sum()),
        })
    return rows


def run(out: Path, workers: int):
    jobs = [(cell, s) for cell in CELLS for s in range(SEEDS)]
    out.mkdir(parents=True, exist_ok=True)
    with Pool(workers) as pool, (out / "records.jsonl").open("w") as f:
        for i, rows in enumerate(pool.imap_unordered(_job, jobs, chunksize=4)):
            for r in rows:
                f.write(json.dumps(r) + "\n")
            if i % 200 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    git = {k: subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=ROOT).stdout.strip()
           for k, cmd in (("head", ["git", "rev-parse", "HEAD"]), ("status", ["git", "status", "--porcelain"]))}
    (out / "manifest.json").write_text(json.dumps(
        {"seed_base": SEED_BASE, "seeds": SEEDS, "cells": CELLS, "policies": POLICIES,
         "git_head": git["head"], "worktree_dirty": bool(git["status"])}, indent=1))


def _tci(x):
    from scipy import stats

    x = np.asarray(x, float)
    n = len(x)
    m, se = float(x.mean()), float(x.std(ddof=1) / math.sqrt(n))
    q = stats.t.ppf(0.975, n - 1)
    return {"mean": round(m, 3), "ci95": [round(m - q * se, 3), round(m + q * se, 3)],
            "excludes0": bool(se > 0 and abs(m) > q * se)}


def analyze(out: Path):
    import pandas as pd

    df = pd.read_json(out / "records.jsonl", lines=True)
    df["missed"] = (df.detect_delay < 0).astype(int)
    df["delay_obs"] = df.detect_delay.where(df.detect_delay >= 0)
    net = df.pivot_table(index=["cell", "seed"], columns="policy", values="net")
    contrasts = {
        "M4_noacq_minus_full": ("rmm:gated_deployment+RMM_noacq", "rmm:gated_deployment+RMM"),
        "M2_single_minus_full_gated": ("rmm:gated_deployment+RMM_single", "rmm:gated_deployment+RMM"),
        "M2_single_minus_full_LRMD": ("rmm:LRMD_single", "rmm:LRMD"),
        "M2_norestart_minus_full": ("rmm:gated_deployment+RMM_norestart", "rmm:gated_deployment+RMM"),
        "M1_LRMDk3_minus_k1": ("rmm:LRMD_k3", "rmm:LRMD_k1"),
        "M1_LRMDk2_minus_k1": ("rmm:LRMD", "rmm:LRMD_k1"),
        "M1_front_minus_nofront": ("gated_adaptive_range+front", "gated_adaptive_range"),
        "B_rmm_minus_esr": ("rmm:gated_deployment+RMM", "two_sided_esr_label_clock"),
        "B_LRMD_minus_esr": ("rmm:LRMD", "two_sided_esr_label_clock"),
        "B_LRMDk1_minus_esr": ("rmm:LRMD_k1", "two_sided_esr_label_clock"),
        "B_esr_minus_host": ("two_sided_esr_label_clock", "gated_deployment"),
        "B_esr_minus_never": ("two_sided_esr_label_clock", "CONTROL_never_switch"),
    }
    res = {"contrasts": {k: {cell: _tci(net.loc[cell][a] - net.loc[cell][b]) for cell in CELLS}
                         for k, (a, b) in contrasts.items()}}
    g = df.groupby(["cell", "policy"]).agg(
        net=("net", "mean"), missed=("missed", "mean"), delay_med=("delay_obs", "median"),
        early_promote=("promoted_before_change", "mean"), lab_before=("labels_before", "mean"),
        lab_after=("labels_after", "mean"), zero_after=("labels_after", lambda s: float((s == 0).mean())))
    res["summary"] = {f"{c}|{p}": {k: (None if pd.isna(v) else round(float(v), 3)) for k, v in row.items()}
                      for (c, p), row in g.to_dict("index").items()}
    res["manifest"] = json.loads((out / "manifest.json").read_text())
    (ROOT / "docs/sota_fidelity/late_change_diagnosis_results.json").write_text(json.dumps(res, indent=1))
    pd.set_option("display.width", 250)
    for k in contrasts:
        print(k, {c: (v["mean"], v["ci95"]) for c, v in res["contrasts"][k].items() if "@B200" in c or "_d" in c})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=9)
    a = ap.parse_args()
    run(a.out, a.workers) if a.cmd == "run" else analyze(a.out)


if __name__ == "__main__":
    main()
