"""Calibrate the budget-aware comparators on SIMULATION calibration seeds (dev block only).

For R in {12, 20, 30} (k = 3, T = 300, 30 regimes): smallest margin c in {0..R} for stoploss_cal and
largest CUSUM threshold h_c in {.5,1,2,3,4,6,8,12} for cusumrb_cal such that the violation rate
P(sup H > R) <= 0.05 in EVERY regime on seeds_for("dev", 200, 80000). If none qualifies, the most
conservative grid value is used and this is recorded. Writes configs/paper3/f3_calibrated_comparators_v1.json
(including each grid value's pooled J and worst-regime violation rate). Never touches the
confirmation or model_selection blocks, and not the real streams.
"""

import argparse
import datetime
import json
import sys
import time
from multiprocessing import Pool

import numpy as np

from shiftlab.paper3.joint.harness import make_policy
from shiftlab.paper3.riskbudget.comparators_cal import CusumRollbackBudget, StopLossMargin
from shiftlab.paper3.riskbudget.harness import ROOT, all_regimes
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
OUT_CFG = CONFIG_DIR / "f3_calibrated_comparators_v1.json"
OUT = ROOT / "outputs" / "paper3" / "riskbudget" / "calib"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
RS, HGRID, T, DELTA = (12, 20, 30), (0.5, 1, 2, 3, 4, 6, 8, 12), 300, 0.05
N_CAL, START_CAL = 200, 80000
EPS = 1e-9


def inner_spec():
    return next(a for a in json.loads(ARMS_FILE.read_text())["arms"] if a["name"] == "cusum_rb_h4")[
        "inner"
    ]


def grid_arms():
    """-> list of (kind, R, value)."""
    g = [("stoploss_cal", R, float(c)) for R in RS for c in range(R + 1)]
    g += [("cusumrb_cal", R, float(h)) for R in RS for h in HGRID]
    return g


def make_cal_arm(kind, R, v, T_):
    inner = make_policy(inner_spec(), T_)
    if kind == "stoploss_cal":
        return StopLossMargin(inner, R, v)
    return CusumRollbackBudget(inner, v, R)


_REG = _GRID = None


def _init():
    global _REG, _GRID
    _REG, _GRID = all_regimes(), grid_arms()


def _task(args):
    rid, seed = args
    reg = _REG[rid]
    tape, truth = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    J, S = [], []
    for kind, R, v in _GRID:
        rec = run_policy(make_cal_arm(kind, R, v, T), tape, spec, seed)
        J.append(float(ev.evaluate(rec)["J"]))
        S.append(harm_summary(tape, rec, spec.costs.k)["sup_harm"])
    return rid, seed, J, S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seeds", type=int, default=N_CAL)
    a = ap.parse_args()
    if a.workers > 6:
        sys.exit("at most 6 workers")
    if OUT_CFG.exists():
        sys.exit(f"{OUT_CFG} exists; calibration is written once")
    seeds = seeds_for("dev", a.seeds, START_CAL)
    rids, grid = list(all_regimes()), grid_arms()
    ri, si = {r: i for i, r in enumerate(rids)}, {s: i for i, s in enumerate(seeds)}
    J = np.full((len(grid), len(rids), len(seeds)), np.nan)
    S = np.full_like(J, np.nan)
    t0 = time.time()
    tasks = [(r, s) for r in rids for s in seeds]
    with Pool(a.workers, initializer=_init, maxtasksperchild=200) as pool:
        for n, (rid, s, j, sup) in enumerate(pool.imap_unordered(_task, tasks, chunksize=2)):
            J[:, ri[rid], si[s]], S[:, ri[rid], si[s]] = j, sup
            if (n + 1) % 600 == 0:
                print(f"{n + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "calib.npz", J=J, S=S, seeds=seeds, rids=rids)
    cfg = {"version": "f3_calibrated_comparators_v1", "standard": {}, "calibration": {}}
    cfg["standard"] = {
        "violation_rate_max_every_regime": DELTA,
        "seeds": [seeds[0], seeds[-1]],
        "n_seeds": len(seeds),
        "T": T,
        "k": 3.0,
        "n_regimes": len(rids),
        "inner": "wald_cut (frozen, f3_confirmation_arms_v1.json)",
        "c_grid": "0..R (smallest meeting standard)",
        "h_grid": list(HGRID),
        "h_rule": "largest meeting standard",
    }
    for R in RS:
        ent = {}
        for kind in ("stoploss_cal", "cusumrb_cal"):
            idx = [i for i, g in enumerate(grid) if g[0] == kind and g[1] == R]
            front = []
            for i in idx:
                viol = (S[i] > R + EPS).mean(1)  # per regime
                w = int(np.argmax(viol))
                front.append(
                    {
                        "value": grid[i][2],
                        "pooled_J": float(J[i].mean()),
                        "worst_viol": float(viol[w]),
                        "worst_regime": rids[w],
                        "pooled_viol": float(viol.mean()),
                        "meets": bool(viol.max() <= DELTA + EPS),
                    }
                )
            ok = [f for f in front if f["meets"]]
            if kind == "stoploss_cal":
                pick = (
                    min(ok, key=lambda f: f["value"])
                    if ok
                    else max(front, key=lambda f: f["value"])
                )
            else:
                pick = (
                    max(ok, key=lambda f: f["value"])
                    if ok
                    else min(front, key=lambda f: f["value"])
                )
            ent[kind] = {
                "chosen": pick["value"],
                "standard_reached": bool(ok),
                "chosen_stats": pick,
                "frontier": front,
            }
        cfg["calibration"][f"R{R}"] = ent
    OUT_CFG.write_text(json.dumps(cfg, indent=1))
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "workstream": "F3_riskbudget",
        "stage": "calibrate_comparators",
        "config": {
            "seeds": [seeds[0], seeds[-1]],
            "n": len(seeds),
            "T": T,
            "chosen": {
                k: {kk: vv["chosen"] for kk, vv in v.items()} for k, v in cfg["calibration"].items()
            },
            "standard_reached": {
                k: {kk: vv["standard_reached"] for kk, vv in v.items()}
                for k, v in cfg["calibration"].items()
            },
        },
        "wall_clock_s": time.time() - t0,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec["config"], indent=1))


if __name__ == "__main__":
    main()
