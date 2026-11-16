"""F3 real-stream check runner (protocol: 2026_programme/05F_F3_REAL_STREAM_PROTOCOL.md).

For each stream, condition, episode and policy seed, runs every arm. One task = one
(condition, stream, episode); output outputs/paper3/riskbudget/real/<condition>/<stream>.json with
arrays shaped (n_arms, n_episodes, n_seeds) per field. Refuses to overwrite unless --force.
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
from shiftlab.paper3.riskbudget.real_streams import (
    CONDITIONS,
    ROW_FIELDS,
    STREAMS,
    build_real_arms,
    corruption_rng,
    delay_of,
    load_stream,
    make_real_spec,
    make_real_tape,
    run_arm_row,
)
from shiftlab.paper3.simulation import seeds_for

OUT = ROOT / "outputs" / "paper3" / "riskbudget" / "real"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
N_SEEDS, SEED_START = 20, 60000
_ARMS = None
_DATA: dict = {}


def _init():
    global _ARMS
    _ARMS = build_real_arms()


def _task(args):
    cond, stream, ep = args
    if stream not in _DATA:
        _DATA[stream] = load_stream(stream)
    l0, l1 = _DATA[stream]
    delay = delay_of(stream)
    tape = make_real_tape(l0[ep], l1[ep], delay, cond, corruption_rng(stream, ep, cond))
    spec = make_real_spec(delay, cond)
    seeds = seeds_for("dev", N_SEEDS, SEED_START)
    rows = [[run_arm_row(a, tape, spec, delay, s) for s in seeds] for a in _ARMS]
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
    names = [x["name"] for x in build_real_arms()]
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
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": sha,
        "git_dirty": dirty,
        "workstream": "F3_riskbudget",
        "stage": "real_streams",
        "config": {
            "protocol": "05F_F3_REAL_STREAM_PROTOCOL.md",
            "conditions": list(CONDITIONS),
            "streams": list(STREAMS),
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
