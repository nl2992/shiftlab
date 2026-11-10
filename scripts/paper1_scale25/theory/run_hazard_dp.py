"""Exact hazard-DP optimum and perfect-information benchmark for the instances used by real_stack_mc.py.

Usage: python run_hazard_dp.py [env_index ...]   (default: all). Output: docs/paper1_scale25/theory/hazard_dp_values_<idx>.csv
"""

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reduced_dp as R
from hazard_dp import oracle_hazard, solve_hazard

ENVS = [(0.02, 0.35, 0.65), (0.05, 0.35, 0.65), (0.01, 0.2, 0.8)]
T, B, d, cs, cq = 160, 24, 8, 2.0, 0.05


def run(idx):
    h, lo, hi = ENVS[idx]
    name = f"hazard_h{h}" if (lo, hi) == (0.35, 0.65) else f"hazard_h{h}_strong"
    rows = []

    def put(q, v):
        rows.append({"env": name, "quantity": q, "value": round(float(v), 4)})
        print(rows[-1], flush=True)

    for G in (100, 200):
        put(f"V_opt_G{G}", solve_hazard(T=T, B=B, d=d, cs=cs, cq=cq, h=h, p_lo=lo, p_hi=hi, G=G))
    put("oracle_known_regime_path", oracle_hazard(T, cs, h, lo, hi, n=6000))
    put("V_opt_no_labels", solve_hazard(T=T, B=0, d=d, cs=cs, cq=cq, h=h, p_lo=lo, p_hi=hi, G=100))
    if idx == 0:
        inst = R.Inst(T=T, B=B, d=d, cs=cs, cq=cq)
        rows.append(
            {
                "env": "stationary_flat",
                "quantity": "V_opt",
                "value": round(R.solve_optimal(inst)[0], 4),
            }
        )
        rows.append(
            {
                "env": "stationary_flat",
                "quantity": "oracle_known_p",
                "value": round(inst.oracle_cost(), 4),
            }
        )
        rows.append(
            {
                "env": "stationary_flat",
                "quantity": "V_opt_no_labels",
                "value": round(R.solve_optimal(R.Inst(T=T, B=0, d=d, cs=cs, cq=cq))[0], 4),
            }
        )
        print(rows[-3:], flush=True)
    out = HERE.parents[2] / f"docs/paper1_scale25/theory/hazard_dp_values_{idx}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["env", "quantity", "value"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    for i in [int(a) for a in sys.argv[1:]] or range(len(ENVS)):
        run(i)
