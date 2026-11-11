"""WP-M (P1): exploratory exact values of explicit B = 3 branch plans (k = c = 0), section 5 obstruction.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpM_b3_explore.py OUT.json T
Values are exact (forward filter) values of explicit plans at finite T, i.e. lower bounds on branch slopes; they are
not certified slopes.  Also records the B = 2 finite-T exact branch slopes and the M4 thresholds T0.
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpM_b2_lib import T0_explicit, branch_slopes, closed_inf, H_empty, released_value  # noqa: E402


def main():
    out, T = sys.argv[1], int(sys.argv[2])
    e, d = F(1, 10), 1
    res = {"T": T, "e": str(e), "d": d, "b3": {}, "b2_finite": {}, "T0": {}}
    for t in (F(3, 4),):
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        v1 = g * r**d / (2 * (1 - r))
        row = {"heur_s0_inf": float(g * r**d / (1 - r * r) + 2 * v1), "H_empty_inf_3v1": float(3 * v1)}
        for y in (0, 1):
            row[f"imm_{y}_two_free"] = float(max(
                released_value(t, e, d, T, [(1, y), (1 + a, None), (1 + b, None)], 1 + d, [(1, y)])
                for a in range(1, T // 2) for b in range(a + 1, T)))
            for dl in (1, 2):
                for v in (0, 1):
                    row[f"pat_{y}{v}_delta{dl}_plus_free"] = float(max(
                        2 * released_value(t, e, d, T, [(1, y), (1 + dl, v), (1 + dl + b, None)], 1 + dl + d,
                                           [(1, y)]) for b in range(1, T - dl - 1)))
        row["inf_pat10_plus_free"] = float(g * r**d / (1 - r) + (1 + g * r) * v1)
        row["inf_pat10_plus_two_free_B4"] = float(g * r**d / (1 - r) + (1 + g * r) * 2 * v1)
        row["inf_imm0_three_free_B4"] = float(g * r**d / (1 - r * r) + 3 * v1)
        res["b3"][str(t)] = row
    for t in (F(2, 3), F(3, 4), F(9, 10)):
        for Tb in (6, 8, 10, 12):
            sl = branch_slopes(t, e, d, Tb)
            res["b2_finite"][f"t={t},T={Tb}"] = {"s0": float(max(sl[0])), "s1": float(max(sl[1])),
                                                  "s0_imm": float(sl[0][0]), "s1_pattern": float(sl[1][1]),
                                                  "H_empty": float(H_empty(t, e, d, Tb))}
        for dd in (1, 3):
            for ee in (F(1, 10), F(1, 5)):
                ci = closed_inf(t, ee, dd)
                res["T0"][f"t={t},e={ee},d={dd},c=0"] = {"T0": T0_explicit(t, ee, dd),
                                                         "s0inf": float(ci["s0"]), "s1inf": float(ci["s1"]),
                                                         "liminf_rho_lb": float(ci["rho_lb_inf"])}
    save_refuse_overwrite(out, res)


if __name__ == "__main__":
    main()
