"""DIAGNOSTIC on the real streams (clean feedback, h=14): frozen v3 vs exact-mixture width vs the deterministic
matched comparator. Same tapes/seeds as run_real_v3.py (dev offsets 60000-60019, SECOND LOOK). Not registered; output in outputs/.../proto_real."""
import copy, json, sys, time
from multiprocessing import Pool
import numpy as np
from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.harness_v3 import _frozen_arm, load_frozen_v3, v3_arm
from shiftlab.paper3.riskbudget.real_streams import (STREAMS, R_of, corruption_rng, delay_of, load_stream, make_real_spec, make_real_tape, run_arm_row)
from shiftlab.paper3.simulation import seeds_for

H, COND = 14, "clean"
SEEDS = seeds_for("dev", 20, 60000)
_D = {}; _A = None


def arms():
    sh = load_frozen_v3(); a = [_frozen_arm("never"), _frozen_arm("wald_cut"), v3_arm(sh, R_of(H), "v3")]
    s = copy.deepcopy(sh); s["mix_m"] = 12; a.append(v3_arm(s, R_of(H), "mix12"))
    s = copy.deepcopy(sh); s["deterministic"] = True; a.append(v3_arm(s, R_of(H), "det"))
    return a


def init():
    global _A; _A = arms()


def task(x):
    st, ep = x
    if st not in _D: _D[st] = load_stream(st)
    l0, l1 = _D[st]
    tape = make_real_tape(l0[ep], l1[ep], delay_of(st), COND, corruption_rng(st, ep, COND))
    spec = make_real_spec(delay_of(st), COND)
    return st, ep, [[run_arm_row(a, tape, spec, delay_of(st), s) for s in SEEDS] for a in _A]


def main():
    names = [a["name"] for a in arms()]
    tasks = [(s, e) for s in STREAMS for e in range(len(np.load(STREAMS[s][0] / f"{s}.npz")["l0"]))]
    t0 = time.time(); J = {n: [] for n in names}; V = {n: [] for n in names}; per = {}
    with Pool(6, initializer=init, maxtasksperchild=40) as p:
        for st, ep, rows in p.imap_unordered(task, tasks, chunksize=1):
            for n, r in zip(names, rows):
                j = np.mean([x["J"] for x in r]); v = np.mean([x["sup_harm"] > R_of(H) + 1e-9 for x in r])
                per.setdefault(st, {}).setdefault(n, []).append((j, v))
    print("wall", round(time.time() - t0), "n_episodes", len(tasks))
    # equal weight over streams, then episodes
    sm = {n: np.mean([np.mean([e[0] for e in per[s][n]]) for s in per]) for n in names}
    sv = {n: np.mean([np.mean([e[1] for e in per[s][n]]) for s in per]) for n in names}
    ne = sum(len(per[s]["never"]) for s in per)
    for n in names: print(f"{n:9s} mean J {sm[n]:9.2f}  viol {100*sv[n]:.2f}%  (J-never {sm[n]-sm['never']:+.2f})")
    g0 = sm["never"] - sm["wald_cut"]
    for n in names[2:]: print(f"{n:9s} keeps {100*(sm['never']-sm[n])/g0:5.1f}% of Wald's gain over never")
    print("per-stream (J never / wald / v3 / mix12 / det):")
    for s in per: print(f"  {s:18s}", " ".join(f"{np.mean([e[0] for e in per[s][n]]):8.1f}" for n in names))
    json.dump({s: {n: per[s][n] for n in names} for s in per}, open(ROOT / "outputs/paper3/riskbudget/proto_real.json", "w"))


if __name__ == "__main__":
    main()
