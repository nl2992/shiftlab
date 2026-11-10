"""Follow-up: random exact search for Gamma > 0 under a STATIC alternative (t01 = t10 = 0).

Biased toward correlated-coin conditions: low priors and asymmetric emissions (P_A(Y=1) < 1/2).
usage: fu_static_search.py OUT.json SEED N [--budget S]
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F

from gamma_lib import gamma_cell, save_refuse_overwrite

PRIOR = [F(1, 20), F(1, 10), F(1, 4), F(1, 3), F(1, 2), F(2, 3), F(3, 4), F(9, 10)]
E0 = [F(1, 20), F(1, 10), F(1, 4), F(2, 5)]
E1 = [F(11, 20), F(3, 5), F(3, 4), F(9, 10), F(19, 20)]
COST = [F(0), F(1, 100), F(1, 10)]
ALPHA = [F(1, 20), F(1, 10), F(1, 4)]


def main():
    args = sys.argv[1:]
    budget = 540.0
    if "--budget" in args:
        i = args.index("--budget")
        budget = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    out, seed, n = args[0], int(args[1]), int(args[2])
    rng = random.Random(seed)
    started = time.time()
    rows = []
    for _ in range(n):
        if time.time() - started > budget:
            break
        T = rng.choice([3, 4, 5, 6, 7])
        B = rng.choice([b for b in (2, 3, 4) if b <= T and not (T == 7 and b == 4)])
        d = rng.choice([1, 2, 3])
        prior, e0, e1 = rng.choice(PRIOR), rng.choice(E0), rng.choice(E1)
        c, k, alpha = rng.choice(COST), rng.choice(COST), rng.choice(ALPHA)
        r = gamma_cell(T, B, d, 0, 0, e0, e1, prior, c, k, alpha)
        marg = e0 + (e1 - e0) * prior
        rows.append({"cell": r["cell"], "Gamma_lo": r["Gamma_lo"], "Gamma_lo_f": r["Gamma_lo_f"],
                     "Gamma_hi_f": r["Gamma_hi_f"], "positive": r["Gamma_positive_certified"],
                     "P_A_Y1": str(marg), "M": marg >= F(1, 2),
                     "iid_opt_causal_safe": r["iid_opt_causal_safe"]})
    payload = {
        "script": "scripts/paper4_continuation/theory_C/fu_static_search.py", "seed": seed,
        "n_run": len(rows), "n_positive": sum(r["positive"] for r in rows),
        "n_M_violated": sum(not r["M"] for r in rows),
        "n_iid_vertex_unsafe": sum(not r["iid_opt_causal_safe"] for r in rows),
        "max_Gamma_hi": max(r["Gamma_hi_f"] for r in rows),
        "seconds": time.time() - started, "rows": rows,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})


if __name__ == "__main__":
    main()
