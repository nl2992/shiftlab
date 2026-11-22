"""Run the 100-stream F3 screen (protocol 05G_F3_REAL_SCREEN100_PROTOCOL.md).

One task = (condition, stream, episode); every listed arm x 5 dev seeds (offset 61000).
Writes outputs/paper3/riskbudget/screen100/<condition>/<stream>.json with arrays
(n_arms, n_episodes, n_seeds) for J, J_never, sup_harm, frac_time_deployed.

    PYTHONPATH=src OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/paper3/riskbudget/screen100_run.py
"""

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.real_streams import (
    CONDITIONS,
    build_real_arms,
    corruption_rng,
    make_real_spec,
    make_real_tape,
    run_arm_row,
)
from shiftlab.paper3.simulation import seeds_for

DATA = ROOT / "data" / "screen100_losses"
OUT = ROOT / "outputs" / "paper3" / "riskbudget" / "screen100"
ARMS = ("never", "wald_cut", "cusum", "gate_wald", "cusum_rb_h8", "stoploss_h14",
        "f3_pi1_h14", "f3v2d_h14", "f3_pi1_h50", "f3v2d_h50")  # fmt: skip
FIELDS = ("J", "J_never", "sup_harm", "frac_time_deployed")
N_SEEDS, SEED_START = 5, 61000
_ARMS = None
_CACHE: dict = {}


def _init():
    global _ARMS
    by = {a["name"]: a for a in build_real_arms()}
    _ARMS = [by[n] for n in ARMS]


def _task(args):
    cond, stream, ep, delay = args
    if stream not in _CACHE:
        d = np.load(DATA / f"{stream}.npz")
        _CACHE.clear()
        _CACHE[stream] = (d["l0"], d["l1"])
    l0, l1 = _CACHE[stream]
    tape = make_real_tape(l0[ep], l1[ep], delay, cond, corruption_rng(stream, ep, cond))
    spec = make_real_spec(delay, cond)
    seeds = seeds_for("dev", N_SEEDS, SEED_START)
    rows = [[run_arm_row(a, tape, spec, delay, s) for s in seeds] for a in _ARMS]
    return cond, stream, ep, [[[r[f] for r in arm] for arm in rows] for f in FIELDS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="smoke test: first N tasks only")
    a = ap.parse_args()
    stats = [s for s in json.loads((DATA / "stats.json").read_text()) if s["status"] == "built"]
    done = {(c, p.stem) for c in CONDITIONS for p in (OUT / c).glob("*.json")} if OUT.exists() else set()
    tasks = [(c, s["name"], e, s["delay"]) for c in CONDITIONS for s in stats
             if (c, s["name"]) not in done for e in range(s["K"])]  # fmt: skip
    if a.limit:
        tasks = tasks[: a.limit]
    k_of = {s["name"]: s["K"] for s in stats}
    res: dict = {}
    t0 = time.time()
    with Pool(a.workers, initializer=_init, maxtasksperchild=50) as pool:
        for i, (c, s, e, vals) in enumerate(pool.imap(_task, tasks, chunksize=1)):
            res[(c, s, e)] = vals
            if (i + 1) % 50 == 0:
                print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
            if not a.limit and all((c, s, ee) in res for ee in range(k_of[s])):
                body = {"stream": s, "condition": c, "arms": list(ARMS), "fields": {
                    f: [[res[(c, s, ee)][fi][ai] for ee in range(k_of[s])] for ai in range(len(ARMS))]
                    for fi, f in enumerate(FIELDS)}}  # fmt: skip
                (OUT / c).mkdir(parents=True, exist_ok=True)
                (OUT / c / f"{s}.json").write_text(json.dumps(body))
                for ee in range(k_of[s]):
                    del res[(c, s, ee)]
    print(f"done {len(tasks)} tasks in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
