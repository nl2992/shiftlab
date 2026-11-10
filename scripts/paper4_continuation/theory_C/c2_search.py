"""C2 counterexample search: random exact cells; flags TP2/MLR/marginal conditions.

usage: c2_search.py OUT.json SEED N_CELLS FAMILY [TIME_BUDGET_S]
FAMILY in {sym_persistent, asym_persistent, any, b1}
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F

from gamma_lib import gamma_cell, save_refuse_overwrite

TRANS = [F(0), F(1, 20), F(1, 10), F(1, 4), F(2, 5), F(1, 2), F(3, 5), F(3, 4), F(9, 10), F(1)]
E1 = [F(3, 5), F(3, 4), F(9, 10), F(19, 20)]
E0 = [F(1, 20), F(1, 10), F(1, 4), F(2, 5)]
PRIOR = [F(0), F(1, 10), F(1, 4), F(1, 2), F(3, 4), F(9, 10), F(1)]
COSTS_C = [F(0), F(1, 100), F(1, 20)]
COSTS_K = [F(0), F(1, 10), F(1, 2)]
ALPHA = [F(1, 20), F(1, 10), F(1, 4)]


def marginals(T, t01, t10, e0, e1, prior):
    out = []
    p = prior
    for _ in range(T):
        p = p * (1 - t10) + (1 - p) * t01  # one propagate step (state-1 prob)
        out.append(e0 + (e1 - e0) * p)
    return out


def sample(rng, family):
    T = rng.choice([3, 4, 5])
    B = rng.choice([b for b in (1, 2, 3) if b <= T])
    if family == "b1":
        T = rng.choice([3, 4, 5, 6])
        B = 1
    d = rng.choice([1, 2])
    while True:
        if family == "sym_persistent":
            t = rng.choice([x for x in TRANS if x <= F(1, 2)])
            t01 = t10 = t
            e1 = rng.choice(E1)
            e0 = 1 - e1
            prior = F(1, 2)
        else:
            t01, t10 = rng.choice(TRANS), rng.choice(TRANS)
            e0, e1 = rng.choice(E0), rng.choice(E1)
            prior = rng.choice(PRIOR)
        if family in ("asym_persistent", "b1") and t01 + t10 > 1:
            continue
        break
    return dict(T=T, B=B, d=d, t01=t01, t10=t10, e0=e0, e1=e1, prior=prior,
                c=rng.choice(COSTS_C), k=rng.choice(COSTS_K), alpha=rng.choice(ALPHA))


def main():
    out, seed, n, family = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    budget = float(sys.argv[5]) if len(sys.argv) > 5 else 480.0
    rng = random.Random(seed)
    started = time.time()
    rows = []
    for _ in range(n):
        if time.time() - started > budget:
            break
        p = sample(rng, family)
        m = marginals(p["T"], p["t01"], p["t10"], p["e0"], p["e1"], p["prior"])
        try:
            r = gamma_cell(p["T"], p["B"], p["d"], p["t01"], p["t10"], p["e0"], p["e1"],
                           p["prior"], p["c"], p["k"], p["alpha"])
        except Exception as exc:  # record, do not hide
            rows.append({"params": {k: str(v) for k, v in p.items()}, "error": repr(exc)})
            continue
        r["tp2"] = p["t01"] + p["t10"] <= 1
        r["symmetric"] = p["t01"] == p["t10"] and p["e0"] + p["e1"] == 1 and p["prior"] == F(1, 2)
        r["min_marginal_P1"] = str(min(m))
        r["marginal_ge_half"] = min(m) >= F(1, 2)
        rows.append(r)
    pos = [r for r in rows if r.get("Gamma_positive_certified")]
    payload = {
        "script": "scripts/paper4_continuation/theory_C/c2_search.py",
        "seed": seed, "family": family, "n_run": len(rows), "seconds": time.time() - started,
        "n_gamma_positive_certified": len(pos),
        "n_errors": sum("error" in r for r in rows),
        "rows": rows,
    }
    save_refuse_overwrite(out, payload)
    print(family, "run", len(rows), "Gamma>0:", len(pos))
    for r in pos[:20]:
        print(r["cell"], r["Gamma_lo_f"], "tp2", r["tp2"], "sym", r["symmetric"],
              "marg>=1/2", r["marginal_ge_half"])


if __name__ == "__main__":
    main()
