"""F3 confirmation runner (registration: 2026_programme/04F_F3_CONFIRMATION_REGISTRATION.md).

Arms are read from the frozen configs/paper3/f3_confirmation_arms_v1.json, not from outputs/.
``--smoke`` runs the same pipeline on 20 smoke-block seeds (plumbing only).
The confirmation block is opened only with ``--open-confirmation`` and only once: the run refuses
to start if its output directory already exists.
"""

import argparse
import datetime
import json
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from shiftlab.paper3.riskbudget.harness import FIELDS, ROOT, all_regimes
from shiftlab.paper3.riskbudget.harness_v2 import DIAG, make_arm_v2
from shiftlab.paper3.riskbudget.metrics import harm_summary
from shiftlab.paper3.simulation import (
    CONFIG_DIR,
    SimulationEvaluator,
    generate_tape,
    make_spec,
    run_policy,
    seeds_for,
)

ARMS_FILE = CONFIG_DIR / "f3_confirmation_arms_v1.json"
OUT = ROOT / "outputs" / "paper3" / "riskbudget"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
CONF_N, CONF_START, T = 1000, 500000, 300
_REG = _ARMS = None


def load_arms():
    return json.loads(ARMS_FILE.read_text())["arms"]


def _init():
    global _REG, _ARMS
    _REG, _ARMS = all_regimes(), load_arms()


def _task(args):
    rid, seed = args
    reg = _REG[rid]
    tape, truth = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    rows = []
    for arm in _ARMS:
        pol = make_arm_v2(arm, T)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in FIELDS if k in e}
        row.update(harm_summary(tape, rec, spec.costs.k))
        row["frac_time_deployed"] = float(np.mean(rec.a))
        for k in DIAG:
            if hasattr(pol, k):
                row[k] = float(getattr(pol, k))
        rows.append(row)
    return seed, rows


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--smoke", action="store_true")
    g.add_argument("--open-confirmation", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.smoke:
        seeds, out = seeds_for("smoke", 20, 9000), OUT / "confirm_smoke"
    else:
        seeds, out = seeds_for("confirmation", CONF_N, CONF_START), OUT / "confirm"
        if out.exists():
            sys.exit("confirmation output already exists: the block is opened once")
    out.mkdir(parents=True, exist_ok=True)
    names = [x["name"] for x in load_arms()]
    keys = sorted(set(FIELDS) | set(DIAG) | {"sup_harm", "final_harm", "frac_time_deployed"})
    t0 = time.time()
    with Pool(a.workers, initializer=_init) as pool:
        for rid in all_regimes():
            res = dict(pool.imap_unordered(_task, [(rid, s) for s in seeds], chunksize=2))
            fields = {
                f: [[res[s][i].get(f) for s in seeds] for i in range(len(names))] for f in keys
            }
            (out / f"{rid}.json").write_text(
                json.dumps({"regime": rid, "seeds": seeds, "arms": names, "fields": fields})
            )
            print(f"done {rid} {time.time() - t0:.0f}s", flush=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": sha,
        "git_dirty": dirty,
        "workstream": "F3_riskbudget",
        "stage": "confirm_smoke" if a.smoke else "confirmation",
        "config": {"seeds": [seeds[0], seeds[-1]], "n": len(seeds), "T": T, "arms": names},
        "wall_clock_s": time.time() - t0,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


if __name__ == "__main__":
    main()
