"""WP C (C4): certified Gamma(B) for B = 1..4 on symmetric stationary anti-persistent cells.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpC_budget.py OUT.json PART NPARTS
Records V*_IID(B), V*_causal(B) intervals so the identity bounds
  Gamma(B) >= Gamma(1) - [V_c(1) - V_c(B)],  Gamma(B) <= Gamma(1) + [V_I(1) - V_I(B)]
can be evaluated.
"""

from __future__ import annotations

import itertools
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))

from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpC_sym_lib import sp1_exact  # noqa: E402


def main():
    out, part, nparts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
    cells = list(itertools.product([F(3, 5), F(3, 4), F(9, 10)], [F(1, 10), F(1, 5)], [4, 5, 6, 7],
                                   [1, 2], [F(0), F(1, 100)], [F(0), F(1, 50)]))
    cells = cells[part::nparts]
    rows, t0 = [], time.time()
    for (t, e, T, d, c, k) in cells:
        if time.time() - t0 > budget:
            break
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        rec = {"t": str(t), "e": str(e), "T": T, "d": d, "c": str(c), "k": str(k), "alpha": "1/10",
               "SP1_B1": str(F(1, 10) * sp1_exact(T, d, r, g, c, k)), "B": {}}
        for B in (1, 2, 3, 4):
            if B == 4 and T > 6:
                continue
            x = gamma_cell(T, B, d, t, t, e, 1 - e, F(1, 2), c, k, F(1, 10))
            rec["B"][B] = {kk: x[kk] for kk in ("L_IID", "U_IID", "L_causal", "U_causal", "Gamma_lo",
                                                 "Gamma_hi", "V_causal_source")}
        rows.append(rec)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpC_budget.py",
                                "part": part, "nparts": nparts, "n": len(rows),
                                "seconds": time.time() - t0, "rows": rows})
    print(len(rows), time.time() - t0)


if __name__ == "__main__":
    main()
