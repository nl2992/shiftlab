"""C3 check: deterministic-alternation family (t01=t10=1, B=1, d=1, prior 1/2, emissions e,1-e).

Theorem C3 (doc): for even T >= 4, g=(1-2e)^2, g > 3k - 2c, g > 2k, (T/2-1)(g-2k) >= 2c,
alpha <= 1/2:  V_IID = T/2 - alpha (G0 - 2c),  V_causal = T/2 - alpha ((G0+G1)/2 - c),
Gamma = alpha ((g - k)/2 - c), with G0 = (T/2)(g-2k)+k, G1 = (T/2-1)(g-2k).
For odd T the theorem predicts nothing; Gamma = 0 is recorded as observed.
usage: c3_alternation_check.py OUT.json
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import product

from gamma_lib import gamma_cell, save_refuse_overwrite


def predicted(T, e, c, k, alpha):
    g = (1 - 2 * e) ** 2
    G0 = F(T, 2) * (g - 2 * k) + k
    G1 = (F(T, 2) - 1) * (g - 2 * k)
    cond = (T % 2 == 0 and T >= 4 and g > 3 * k - 2 * c and g > 2 * k
            and G1 >= 2 * c and alpha <= F(1, 2))
    return cond, F(T, 2) - alpha * (G0 - 2 * c), F(T, 2) - alpha * ((G0 + G1) / 2 - c), \
        alpha * ((g - k) / 2 - c)


def main():
    out = sys.argv[1]
    rows = []
    started = time.time()
    grid = product([4, 5, 6, 7, 8], [F(1, 20), F(1, 10), F(1, 5), F(3, 10)],
                   [F(0), F(1, 100), F(1, 50)], [F(0), F(1, 20), F(1, 10), F(1, 4)],
                   [F(1, 20), F(1, 10), F(1, 4)])
    for T, e, c, k, alpha in grid:
        r = gamma_cell(T, 1, 1, 1, 1, e, 1 - e, F(1, 2), c, k, alpha, force_fcg=True)
        cond, v_iid, v_c, gam = predicted(T, e, c, k, alpha)
        L_IID, U_IID = F(r["L_IID"]), F(r["U_IID"])
        L_c, U_c = F(r["L_causal"]), F(r["U_causal"])
        tol = F(1, 10**9)
        row = {"T": T, "e": str(e), "c": str(c), "k": str(k), "alpha": str(alpha),
               "conditions": cond, "Gamma_lo": r["Gamma_lo_f"], "Gamma_hi": r["Gamma_hi_f"],
               "V_IID_interval": [float(L_IID), float(U_IID)],
               "V_causal_interval": [float(L_c), float(U_c)]}
        if cond:
            row["pred_V_IID"], row["pred_V_causal"], row["pred_Gamma"] = str(v_iid), str(v_c), str(gam)
            row["V_IID_match"] = L_IID - tol <= v_iid <= U_IID + tol
            row["V_causal_match"] = L_c - tol <= v_c <= U_c + tol
        rows.append(row)
    cond_rows = [r for r in rows if r["conditions"]]
    payload = {
        "script": "scripts/paper4_continuation/theory_C/c3_alternation_check.py",
        "seconds": time.time() - started,
        "n_cells": len(rows),
        "n_conditions_hold": len(cond_rows),
        "n_V_IID_match": sum(r["V_IID_match"] for r in cond_rows),
        "n_V_causal_match": sum(r["V_causal_match"] for r in cond_rows),
        "odd_T_max_Gamma_hi": max(r["Gamma_hi"] for r in rows if r["T"] % 2),
        "rows": rows,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})
    for r in cond_rows:
        if not (r["V_IID_match"] and r["V_causal_match"]):
            print("MISMATCH", r)


if __name__ == "__main__":
    main()
