"""SECOND LOOK: frozen v3 on the 14 real streams (03F section 7, step 4).

Same episodes, conditions, tapes and policy seeds (dev offsets 60000-60019) as run_real.py, so runs
are paired with outputs/paper3/riskbudget/real/. Only the v3 arms (h in 6, 14, 24, 50, 100) are run;
output goes to outputs/paper3/riskbudget/real_v3/. Run once with the frozen v3 config; nothing here
is tuned on these streams. Refuses to overwrite unless --force.
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.harness_v3 import load_frozen_v3, v3_arm
from shiftlab.paper3.riskbudget.real_streams import (
    CONDITIONS,
    HS,
    ROW_FIELDS,
    STREAMS,
    R_of,
    corruption_rng,
    delay_of,
    load_stream,
    make_real_spec,
    make_real_tape,
    run_arm_row,
)
from shiftlab.paper3.simulation import seeds_for

OUT = ROOT / "outputs" / "paper3" / "riskbudget" / "real_v3"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
N_SEEDS, SEED_START = 20, 60000
_ARMS = None
_DATA: dict = {}


def build_v3_real_arms() -> list[dict]:
    sh = load_frozen_v3()
    return [v3_arm(sh, R_of(h), f"v3_h{h}") for h in HS]


def episode_rows(arms, l0_row, l1_row, delay, cond, rng, seeds):
    tape = make_real_tape(l0_row, l1_row, delay, cond, rng)
    spec = make_real_spec(delay, cond)
    return [[run_arm_row(a, tape, spec, delay, s) for s in seeds] for a in arms]


def _init():
    global _ARMS
    _ARMS = build_v3_real_arms()


def _task(args):
    cond, stream, ep = args
    if stream not in _DATA:
        _DATA[stream] = load_stream(stream)
    l0, l1 = _DATA[stream]
    seeds = seeds_for("dev", N_SEEDS, SEED_START)
    rows = episode_rows(
        _ARMS, l0[ep], l1[ep], delay_of(stream), cond, corruption_rng(stream, ep, cond), seeds
    )
    return cond, stream, ep, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.workers > 6:
        sys.exit("at most 6 workers")
    if OUT.exists():
        if not a.force:
            sys.exit(f"{OUT} exists; pass --force to overwrite")
        shutil.rmtree(OUT)
    names = [x["name"] for x in build_v3_real_arms()]
    seeds = seeds_for("dev", N_SEEDS, SEED_START)
    tasks = [
        (c, s, e)
        for c in CONDITIONS
        for s in STREAMS
        for e in range(len(np.load(STREAMS[s][0] / f"{s}.npz")["l0"]))
    ]
    n_ep = {s: sum(1 for t in tasks if t[0] == CONDITIONS[0] and t[1] == s) for s in STREAMS}
    res: dict = {}
    t0 = time.time()
    with Pool(a.workers, initializer=_init, maxtasksperchild=40) as pool:
        for i, (c, s, e, rows) in enumerate(pool.imap_unordered(_task, tasks, chunksize=1)):
            res[(c, s, e)] = rows
            if (i + 1) % 20 == 0:
                print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
            if all((c, s, ee) in res for ee in range(n_ep[s])):
                n = n_ep[s]
                fields = {
                    f: [
                        [
                            [res[(c, s, ee)][ai][si].get(f) for si in range(len(seeds))]
                            for ee in range(n)
                        ]
                        for ai in range(len(names))
                    ]
                    for f in ROW_FIELDS
                }
                d = OUT / c
                d.mkdir(parents=True, exist_ok=True)
                body = {
                    "stream": s, "condition": c, "delay": delay_of(s), "n_episodes": n,
                    "seeds": seeds, "arms": names, "fields": fields,
                }  # fmt: skip
                (d / f"{s}.json").write_text(json.dumps(body))
                for ee in range(n):
                    del res[(c, s, ee)]
                print(f"wrote {c}/{s} {time.time() - t0:.0f}s", flush=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": sha,
        "git_dirty": True,
        "workstream": "F3_riskbudget",
        "stage": "real_streams_v3_second_look",
        "config": {
            "protocol": "03F section 7; SECOND LOOK (streams seen once with earlier arms)",
            "frozen": "configs/paper3/f3_v3_frozen.json",
            "conditions": list(CONDITIONS),
            "n_episodes": sum(n_ep.values()),
            "seeds": [seeds[0], seeds[-1]],
            "n_seeds": len(seeds),
            "T": 2000,
            "arms": names,
        },
        "wall_clock_s": time.time() - t0,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


if __name__ == "__main__":
    main()
