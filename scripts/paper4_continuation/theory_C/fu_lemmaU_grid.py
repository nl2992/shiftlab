"""Follow-up 1: exhaustive exact grid over TP2 cells for Lemma U (multi-label zero premium).

Grid per (T, B): d in {1,2}; 12 TP2 transition pairs (incl. static 0,0); emissions in {(1/10,9/10),(1/10,3/5),(2/5,9/10)};
prior1 in {0, 1/2, stationary} (static: {0, 1/2, 1/4}); c, k in {0, 1/100, 1/10}; alpha in {1/20, 1/10}.
Flags per cell:
  M_marg : min_{t <= T-d} P_A(Y_t = 1) >= 1/2                      (Theorem Z1's (M))
  M_cond : P_A(Y_t = 1 | Y_S = y_S) >= 1/2 for every t <= T-d, every S subset of {1..t-d}
           with |S| <= B-1 and every y_S of positive probability     (per-query-node analogue)
usage: fu_lemmaU_grid.py OUT.json T B [--d D] [--budget S]
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import combinations, product

from gamma_lib import gamma_cell, save_refuse_overwrite

PAIRS = [(F(1, 10), F(1, 10)), (F(1, 4), F(1, 4)), (F(1, 2), F(1, 2)), (F(1, 10), F(1, 2)),
         (F(1, 2), F(1, 10)), (F(2, 5), F(1, 20)), (F(1, 20), F(2, 5)), (F(1, 4), F(3, 4)),
         (F(3, 4), F(1, 4)), (F(0), F(1, 2)), (F(1, 2), F(0)), (F(0), F(0))]
EMIS = [(F(1, 10), F(9, 10)), (F(1, 10), F(3, 5)), (F(2, 5), F(9, 10))]
COST = [F(0), F(1, 100), F(1, 10)]
ALPHA = [F(1, 20), F(1, 10)]


def priors(t01, t10):
    out = [F(0), F(1, 2)]
    if t01 + t10 > 0:
        s = t01 / (t01 + t10)
        if s not in out:
            out.append(s)
    else:  # static alternative: add a non-symmetric prior
        out.append(F(1, 4))
    return out


def label_prob(T, t01, t10, e0, e1, prior, observed: dict, t: int) -> F:
    """P_A(Y_t = 1 | Y_s = y_s for s in observed) by forward filtering (exact)."""
    p1 = prior * (1 - t10) + (1 - prior) * t01  # P(S_1 = 1)
    alpha = {0: 1 - p1, 1: p1}
    for s in range(1, t):
        if s in observed:
            y = observed[s]
            alpha = {st: m * ((e1 if st else e0) if y else (1 - (e1 if st else e0)))
                     for st, m in alpha.items()}
        alpha = {1: alpha[1] * (1 - t10) + alpha[0] * t01, 0: alpha[0] * (1 - t01) + alpha[1] * t10}
    z = alpha[0] + alpha[1]
    if z == 0:
        return None
    return (alpha[0] * e0 + alpha[1] * e1) / z


def m_flags(T, B, d, t01, t10, e0, e1, prior):
    marg = min(label_prob(T, t01, t10, e0, e1, prior, {}, t) for t in range(1, T - d + 1)) \
        if T - d >= 1 else F(1)
    cond_min = F(1)
    for t in range(1, T - d + 1):
        earlier = range(1, t - d + 1)
        for size in range(0, min(B - 1, len(earlier)) + 1):
            for S in combinations(earlier, size):
                for ys in product((0, 1), repeat=size):
                    p = label_prob(T, t01, t10, e0, e1, prior, dict(zip(S, ys)), t)
                    if p is not None:
                        cond_min = min(cond_min, p)
    return marg, cond_min


def main():
    args = sys.argv[1:]
    budget = 570.0
    if "--budget" in args:
        i = args.index("--budget")
        budget = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    ds = (1, 2)
    if "--d" in args:
        i = args.index("--d")
        ds = (int(args[i + 1]),)
        args = args[:i] + args[i + 2:]
    out, T, B = args[0], int(args[1]), int(args[2])
    started = time.time()
    rows, skipped = [], 0
    for d, (t01, t10), (e0, e1), c, k, alpha in product(ds, PAIRS, EMIS, COST, COST, ALPHA):
        for prior in priors(t01, t10):
            if time.time() - started > budget:
                skipped += 1
                continue
            marg, cond = m_flags(T, B, d, t01, t10, e0, e1, prior)
            try:
                r = gamma_cell(T, B, d, t01, t10, e0, e1, prior, c, k, alpha)
            except Exception as exc:
                rows.append({"params": [str(x) for x in (T, B, d, t01, t10, e0, e1, prior, c, k, alpha)],
                             "error": repr(exc)})
                continue
            rows.append({
                "cell": r["cell"], "Gamma_lo": r["Gamma_lo"], "Gamma_hi_f": r["Gamma_hi_f"],
                "Gamma_lo_f": r["Gamma_lo_f"], "positive": r["Gamma_positive_certified"],
                "M_marg_min": str(marg), "M_marg": marg >= F(1, 2),
                "M_cond_min": str(cond), "M_cond": cond >= F(1, 2),
                "R_causal_iid_opt_raw": r["R_causal_iid_opt_raw"],
            })
    pos = [r for r in rows if r.get("positive")]
    payload = {
        "script": "scripts/paper4_continuation/theory_C/fu_lemmaU_grid.py", "T": T, "B": B, "d": ds,
        "n_run": len(rows), "n_skipped_budget": skipped, "n_errors": sum("error" in r for r in rows),
        "n_positive": len(pos),
        "n_positive_with_M_marg": sum(r["M_marg"] for r in pos),
        "n_positive_with_M_cond": sum(r["M_cond"] for r in pos),
        "n_M_marg": sum(r.get("M_marg", False) for r in rows),
        "n_M_cond": sum(r.get("M_cond", False) for r in rows),
        "max_Gamma_hi_nonpositive": max((r["Gamma_hi_f"] for r in rows
                                         if "error" not in r and not r["positive"]), default=None),
        "seconds": time.time() - started, "rows": rows,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})


if __name__ == "__main__":
    main()
