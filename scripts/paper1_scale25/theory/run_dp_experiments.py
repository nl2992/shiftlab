"""Approximation-gap experiments on the reduced exact DP (docs/paper1_scale25/THEORETICAL_ANALYSIS.md).

For each instance: Bayes-optimal value V*, perfect-information benchmark (p known, no labels), and the exact
expected cost of each reduced controller (policy evaluation, no Monte Carlo). Output:
docs/paper1_scale25/theory/dp_gaps.csv. Reduced-unit parameters (time compression 0.4 relative to the real
disagreement-step scale, cs scaled the same way: 5 -> 2; see THEORETICAL_ANALYSIS.md section 4): lookahead 4, bundle horizon 8, hazard 0.025/step,
cutoff H = 0.55 T.
"""

from __future__ import annotations

import csv
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import reduced_dp as R

OUT = ROOT / "docs/paper1_scale25/theory/dp_gaps.csv"


def controllers(T, look=4, hor=8, hz=0.025):
    H = round(0.55 * T)
    e48 = {"disc": 0.5, "look": look, "hazard": hz}
    f60 = {"bundle": 2, "horizon": hor, "hazard": hz}
    out = {}
    for kind in ("beta", "wald"):
        k = "EQ" if kind == "beta" else "W"
        out[f"{k}"] = R.Ctrl(rate_mode="estimated", kind=kind, gamma=0.3)
        out[f"{k}+cut"] = R.Ctrl(rate_mode="estimated", kind=kind, gamma=0.3, cutoff_H=H)
        out[f"{k}+cut+E48"] = R.Ctrl(
            rate_mode="estimated", kind=kind, gamma=0.3, cutoff_H=H, e48=e48
        )
        out[f"{k}+cut+F60"] = R.Ctrl(
            rate_mode="estimated", kind=kind, gamma=0.3, cutoff_H=H, f60=f60
        )
        out[f"{k}+cut+E48+F60"] = R.Ctrl(
            rate_mode="estimated", kind=kind, gamma=0.3, cutoff_H=H, e48=e48, f60=f60
        )
    return out


def job(args):
    inst, name, ctrl = args
    t0 = time.time()
    v = R.solve_optimal(inst)[0] if name == "OPT" else R.evaluate(inst, ctrl)
    return inst.name, name, v, time.time() - t0


INSTANCES = [
    R.Inst(T=160, B=24, d=8, cs=2.0, name="base_d8_cs2_flat"),
    R.Inst(T=160, B=24, d=2, cs=2.0, name="shortdelay_d2_cs2_flat"),
    R.Inst(T=160, B=24, d=8, cs=5.0, name="highcs_d8_cs5_flat"),
    R.Inst(
        T=160,
        B=24,
        d=8,
        cs=2.0,
        prior=("points", (0.35, 0.65), (0.5, 0.5)),
        name="base_d8_cs2_twopoint",
    ),
    R.Inst(
        T=160,
        B=24,
        d=8,
        cs=2.0,
        prior=("points", (0.5, 0.65), (0.6, 0.4)),
        name="base_d8_cs2_nullheavy",
    ),
]

if __name__ == "__main__":
    jobs = []
    for inst in INSTANCES:
        jobs.append((inst, "OPT", None))
        for nm, c in controllers(inst.T).items():
            jobs.append((inst, nm, c))
    res = {}
    with ProcessPoolExecutor(max_workers=14) as ex:
        for iname, nm, v, secs in ex.map(job, jobs):
            res[(iname, nm)] = v
            print(f"{iname:28s} {nm:18s} {v:8.3f}  ({secs:.0f}s)", flush=True)
    rows = []
    for inst in INSTANCES:
        orc = inst.oracle_cost()
        vstar = res[(inst.name, "OPT")]
        for nm in ["OPT", *controllers(inst.T).keys()]:
            v = res[(inst.name, nm)]
            rows.append(
                {
                    "instance": inst.name,
                    "T": inst.T,
                    "B": inst.B,
                    "d": inst.d,
                    "cs": inst.cs,
                    "cq": inst.cq,
                    "prior": str(inst.prior),
                    "controller": nm,
                    "J": round(v, 4),
                    "J_opt": round(vstar, 4),
                    "J_oracle_known_p": round(orc, 4),
                    "gap_abs": round(v - vstar, 4),
                    "gap_pct_of_J": round(100 * (v - vstar) / v, 3),
                    "gap_share_of_bayes_regret": round((v - vstar) / (vstar - orc), 4)
                    if vstar > orc
                    else "",
                }
            )
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT)
