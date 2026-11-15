"""Joint tuning of the shielded system (spec 03F 6.5): 32-config random search, R = 20.

usage: tune_v2.py [v2|v1|both] --n 32 --workers 8
Same protocol as scripts/paper3/joint/tune.py: tuning seeds seeds_for("dev", 6, 0), the 24 original
regimes, T = 300, objective = mean over regimes of mean J / mean J_never; config 0 is the
documented default. Output: outputs/paper3/riskbudget/tuning_v2/{f3v2,f3v1_tuned}.json.
"""

import argparse
import datetime
import json
import subprocess
import sys
import time

import numpy as np

from shiftlab.paper3.riskbudget import harness_v2 as H
from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.simulation import load_regimes, seeds_for

R_TUNE = 20
LEDGER = (
    ROOT
    / "papers"
    / "paper3_cost_aware_adaptation"
    / "2026_programme"
    / "ledger"
    / "riskbudget.jsonl"
)


def git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def log(m):
    print(m, flush=True)


def ledger(stage, config, results, wall):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": git_sha(),
        "git_dirty": True,
        "workstream": "F3_riskbudget_v2",
        "stage": stage,
        "config": config,
        "results": results,
        "wall_clock_s": wall,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=float) + "\n")


def tune(which, n, workers, seed):
    path = H.TUNE_DIR / ("f3v2.json" if which == "v2" else "f3v1_tuned.json")
    if path.exists():
        log(f"{path.name}: exists, skip")
        return
    H.TUNE_DIR.mkdir(parents=True, exist_ok=True)
    cfgs = H.sample_v2_configs(n, seed) if which == "v2" else H.sample_v1_configs(n, seed)
    mk = H.v2_arm if which == "v2" else H.v1_arm
    arms = [mk(c, R_TUNE, f"cfg{i}") for i, c in enumerate(cfgs)]
    rids = list(load_regimes().keys())
    seeds = seeds_for("dev", 6, 0)
    t0 = time.time()
    log(f"{which}: {n} configs x {len(rids)} regimes x {len(seeds)} seeds, R={R_TUNE}")
    A = H.tune_arms(arms, rids, seeds, workers, log=log)
    wall = time.time() - t0
    sc = H.tuning_score(A)
    best = int(np.argmin(sc))
    viol = (A["sup_harm"] > R_TUNE + 1e-9).mean((1, 2))
    out = {
        "method": "f3v2" if which == "v2" else "f3v1_tuned",
        "wall_clock_s": wall,
        "objective": "mean_regime(mean_seed J / mean_seed J_never)",
        "R": R_TUNE,
        "delta": 0.05 if which == "v2" else 0.0,
        "tune_seeds": seeds,
        "T": H.T_DEFAULT,
        "n_regimes": len(rids),
        "configs": cfgs,
        "scores": sc.tolist(),
        "mean_queries": A["n_queries"].mean((1, 2)).tolist(),
        "mean_n_sampled": A["n_sampled"].mean((1, 2)).tolist(),
        "tuning_violation_rate": viol.tolist(),
        "best": best,
        "best_config": cfgs[best],
        "default_score": float(sc[0]),
        "cpu_s": float(A["sec"].sum()),
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1, default=float))
    tmp.rename(path)
    log(f"{which}: best cfg {best} score {sc[best]:.4f} (default {sc[0]:.4f}); wall {wall:.0f}s")
    ledger(
        "tuning_v2" if which == "v2" else "tuning_v1_tuned",
        {"n_configs": n, "seeds": seeds, "T": H.T_DEFAULT, "R": R_TUNE},
        {"best": best, "best_score": float(sc[best]), "default_score": float(sc[0])},
        wall,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["v2", "v1", "both"])
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    for w in ("v1", "v2") if a.which == "both" else (a.which,):
        tune(w, a.n, a.workers, a.seed)


if __name__ == "__main__":
    sys.exit(main())
