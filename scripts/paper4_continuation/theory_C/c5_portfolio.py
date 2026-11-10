"""C5 follow-up: does a root portfolio (mixture) of opportunity calendars close the causal adaptivity gap?

For each calendar C and working level a in a grid, compute certified U_C(a) = causal value of the
calendar-restricted problem at level a.  A root lottery w over (C, a) has causal risk
<= sum w a (the null's sup of a sum is <= the sum of sups), so
   V_portfolio <= min { sum w U_C(a) : sum w a <= alpha, sum w = 1 }   (small LP).
Also prints the certified adaptive [L, U].
usage: c5_portfolio.py OUT.json
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import combinations

import numpy as np
from scipy.optimize import linprog

import gamma_lib
import shiftlab.paper4.frontier_cuts_fast as fcf
from c5_adaptivity_gap import ORIGINAL, calendar_class
from gamma_lib import save_refuse_overwrite

CELL = (7, 2, 2, F(2, 5), F(1, 20), F(1, 10), F(3, 5), F(0), F(0), F(0))
ALPHA = F(1, 10)
GRID = [F(0), F(1, 40), F(1, 20), F(3, 40), F(1, 10), F(1, 8), F(3, 20), F(1, 5), F(1, 4),
        F(3, 10), F(2, 5), F(1, 2), F(3, 4), F(1)]


def causal_value(cell, alpha, cls):
    fcf.FastGame = cls
    gamma_lib.FastGame = cls
    try:
        config, model = gamma_lib.make(*cell, alpha=alpha)
        r = fcf.frontier_cut_generation_fast(config, model)
    finally:
        fcf.FastGame = ORIGINAL
        gamma_lib.FastGame = ORIGINAL
    return r["L"], r["U"]


def main():
    out = sys.argv[1]
    started = time.time()
    T, B = CELL[0], CELL[1]
    L_ad, U_ad = causal_value(CELL, ALPHA, ORIGINAL)
    comps = []
    for cal in combinations(range(1, T + 1), B):
        cls = calendar_class(cal)
        for a in GRID:
            lo, up = causal_value(CELL, a, cls)
            comps.append((cal, a, lo, up))
    cost = np.array([float(u) for *_, u in comps])
    risk = np.array([[float(a) for _, a, _, _ in comps]])
    res = linprog(cost, A_ub=risk, b_ub=[float(ALPHA)], A_eq=np.ones((1, len(comps))), b_eq=[1.0],
                  bounds=[(0, None)] * len(comps), method="highs")
    support = [(str(comps[i][0]), str(comps[i][1]), float(res.x[i]), float(comps[i][3]))
               for i in range(len(comps)) if res.x[i] > 1e-9]
    best_single = min(float(u) for cal, a, lo, u in comps if a == ALPHA)
    payload = {
        "script": "scripts/paper4_continuation/theory_C/c5_portfolio.py",
        "cell": [str(x) for x in CELL], "alpha": str(ALPHA),
        "adaptive_causal": [str(L_ad), str(U_ad)],
        "best_single_calendar_causal_U": best_single,
        "portfolio_upper_bound_float": float(res.fun),
        "portfolio_support": support,
        "portfolio_minus_adaptive_L": float(res.fun) - float(L_ad),
        "note": "portfolio value is an upper bound (finite level grid, float LP over certified U's)",
        "seconds": time.time() - started,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items()})


if __name__ == "__main__":
    main()
