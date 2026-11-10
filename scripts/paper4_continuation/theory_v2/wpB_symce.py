"""WP B: systematic search for the smallest certified Gamma > 0 cell in a given family.

Cells are scanned in increasing (T, B). For each cell the Lagrangian hull is computed by parametric
DP (wpB_falsify.hull, floats); at each vertex whose DP-optimal plan is not z-monotone (both
tie-breaks), alpha is set to the midpoint between that vertex's R and each neighbouring vertex's R,
and the repo's certified gamma_cell (exact rationals) is run.  Records every certified Gamma > 0.
usage: wpB_symce.py OUT.json FAMILY TMIN TMAX BLIST DLIST
FAMILY: sym (t01=t10, e0=1-e1, prior 1/2) | static
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import product

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpB_falsify import hull, point  # noqa: E402
from wpB_lib import Model, z_monotone  # noqa: E402

TS = [F(1, 100), F(1, 20), F(1, 10), F(1, 4)]
ES = [F(9, 10), F(99, 100), F(999, 1000)]
KS = [F(0), F(1, 100), F(1, 20)]
CS = [F(0)]


def main():
    out, family = sys.argv[1], sys.argv[2]
    tmin, tmax = int(sys.argv[3]), int(sys.argv[4])
    blist = [int(x) for x in sys.argv[5].split(",")]
    dlist = [int(x) for x in sys.argv[6].split(",")]
    t0 = time.time()
    found, scanned, flagged_cells = [], 0, 0
    for T in range(tmin, tmax + 1):
        for B in blist:
            if B > T:
                continue
            for d, tr, e1, k, c in product(dlist, TS, ES, KS, CS):
                if d >= T:
                    continue
                if family == "sym":
                    cell = (T, B, d, tr, tr, 1 - e1, e1, F(1, 2), c, k)
                else:
                    cell = (T, B, d, F(0), F(0), 1 - e1, e1, tr, c, k)
                m = Model(*[float(x) if isinstance(x, F) else x for x in cell])
                rng = hull(m)
                Rs = []
                flags = []
                for lo, hi in rng:
                    lam = (lo + hi) / 2 if hi < 1e4 else lo + 1
                    oks = []
                    for tie in ("cont", "promote"):
                        _, R, C, plan = point(m, lam, tie)
                        oks.append(z_monotone(plan, m)[0])
                    Rs.append(R)
                    flags.append(not any(oks))
                scanned += 1
                if not any(flags):
                    continue
                flagged_cells += 1
                for i, fl in enumerate(flags):
                    if not fl:
                        continue
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(Rs):
                            alpha = F((Rs[i] + Rs[j]) / 2).limit_denominator(4096)
                            g = gamma_cell(*cell, alpha)
                            if g["Gamma_positive_certified"]:
                                rec = {"cell": [str(x) for x in cell], "alpha": str(alpha),
                                       "Gamma_lo": g["Gamma_lo_f"], "Gamma_hi": g["Gamma_hi_f"],
                                       "Gamma_lo_exact": g["Gamma_lo"] if len(g["Gamma_lo"]) < 200 else None,
                                       "L_causal_eq_U_causal": g["L_causal"] == g["U_causal"],
                                       "V_IID_lp": g["V_IID_lp"], "R_vertex": Rs[i]}
                                found.append(rec)
                                print("GAMMA>0", rec, flush=True)
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_symce.py", "family": family,
               "args": sys.argv[3:], "seconds": time.time() - t0, "cells_scanned": scanned,
               "cells_flagged": flagged_cells, "n_certified_positive": len(found), "found": found}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "found"})


if __name__ == "__main__":
    main()
