"""F3 v3 driver (spec 03F section 7). ``--stage select|scarce|orig30``. Dev seed block only.

select: 12 v3 candidates + comparators, scarce family, seeds 70000-70199 (h = 50).
scarce: fresh evaluation on the scarce family, seeds 71000-71499 (needs configs/paper3/f3_v3_frozen.json).
orig30: original 30 regimes, T = 300, seeds 72000-72299.
"""

import argparse
import datetime
import json
import subprocess
import sys
import time

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.harness_v3 import (
    OUT,
    T_SC,
    orig30_arms,
    run_family,
    scarce_eval_arms,
    selection_arms,
)
from shiftlab.paper3.simulation import seeds_for

LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
STAGES = {
    "select": ("scarce", selection_arms, 200, 70000, T_SC, "v3_select"),
    "scarce": ("scarce", scarce_eval_arms, 500, 71000, T_SC, "v3_scarce"),
    "orig30": ("orig", orig30_arms, 300, 72000, 300, "v3_orig30"),
}


def git(*a):
    try:
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES), required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--n", type=int, default=None, help="override number of seeds (smoke only)")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    which, arms_fn, n, start, T, tag = STAGES[a.stage]
    n = a.n or n
    tag = a.tag or (tag if a.n is None else f"{tag}_n{n}")
    seeds = seeds_for("dev", n, start)
    arms = arms_fn()
    t0 = time.time()
    run_family(which, arms, seeds, OUT / tag, T, a.workers, log=lambda m: print(m, flush=True))
    wall = time.time() - t0
    if a.n is None:
        rec = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "git_sha": git("rev-parse", "HEAD"),
            "git_dirty": True,
            "workstream": "F3_riskbudget",
            "stage": f"v3_{a.stage}",
            "config": {
                "seeds": [seeds[0], seeds[-1]],
                "n": n,
                "T": T,
                "workers": a.workers,
                "tag": tag,
                "arms": [x["name"] for x in arms],
            },
            "wall_clock_s": wall,
        }
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=float) + "\n")
    print("wall", wall)


if __name__ == "__main__":
    sys.exit(main())
