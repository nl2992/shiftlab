"""F3 comparison driver. ``--stage pilot|dev|dev_v2``. Dev seed block only."""

import argparse
import datetime
import json
import subprocess
import sys
import time

from shiftlab.paper3.riskbudget.harness import ROOT, build_arms, run_regimes
from shiftlab.paper3.riskbudget.harness_v2 import build_arms_v2, run_regimes_v2
from shiftlab.paper3.simulation import seeds_for

OUT = ROOT / "outputs" / "paper3" / "riskbudget"
LEDGER = (
    ROOT
    / "papers"
    / "paper3_cost_aware_adaptation"
    / "2026_programme"
    / "ledger"
    / "riskbudget.jsonl"
)
STAGES = {"pilot": (200, 20000), "dev": (1000, 30000), "dev_v2": (1000, 40000)}


def git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def ledger(stage, config, wall):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": git_sha(),
        "git_dirty": True,
        "workstream": "F3_riskbudget",
        "stage": stage,
        "config": config,
        "wall_clock_s": wall,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=float) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES), required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n", type=int, default=None, help="override number of seeds")
    ap.add_argument("--regimes", nargs="*", default=None)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    n, start = STAGES[a.stage]
    n = a.n or n
    seeds = seeds_for("dev", n, start)
    tag = a.tag or (a.stage if a.n is None else f"{a.stage}_n{n}")
    cfg = {
        "stage": a.stage,
        "n": n,
        "start": start,
        "workers": a.workers,
        "T": 300,
        "tag": tag,
        "n_arms": len(build_arms_v2() if a.stage == "dev_v2" else build_arms()),
    }
    t0 = time.time()
    run = run_regimes_v2 if a.stage == "dev_v2" else run_regimes
    run(OUT / tag, seeds, a.workers, regimes=a.regimes, log=lambda m: print(m, flush=True))
    ledger(a.stage, cfg, time.time() - t0)
    print("wall", time.time() - t0)


if __name__ == "__main__":
    sys.exit(main())
