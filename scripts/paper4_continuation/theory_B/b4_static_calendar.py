"""B4: does the pre-promotion problem reduce to stopping on (belief, budget, t)?

Test model (a locked sub-game of the switching problem, as in the alias counterexample):
fixed calendar of q queries at events 1..q, delay 1, one promotion decision after all q
labels are released.  The alternative is STATIC (exchangeable): hidden s in {0,1}, prior 1/2,
P(Y=1|s)=e_s, promotion gain +1 if s=1 and -1 if s=0.  The policy is f: {0,1}^q -> [0,1].
Under a static alternative the alternative belief at the decision is a function of the
count of positives, so "(belief, budget, t)"-measurable policies are exactly count-symmetric f.

Robust constraint: for every full-history causal null nu (p_t in [0,1/2] chosen after seeing
all earlier outcomes), sum_tape P_nu(tape) f(tape) <= alpha.  Endpoint nulls suffice (Lemma 2),
so the LP enumerates all 2^(2^q - 1) endpoint strategies (q <= 4).

We compare the unrestricted LP optimum with the count-symmetric optimum, verify both exactly
in rationals, and report the least-favourable null mixture (dual support).

Usage: uv run --no-sync python scripts/paper4_continuation/theory_B/b4_static_calendar.py
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).parent))
from b_common import write_result  # noqa: E402

HALF = F(1, 2)


def tapes(q):
    return list(product((0, 1), repeat=q))


def alt_utility(tape, e0, e1):
    n1 = sum(tape)
    n0 = len(tape) - n1
    p1 = HALF * e1**n1 * (1 - e1) ** n0
    p0 = HALF * e0**n1 * (1 - e0) ** n0
    return p1 - p0, p1 + p0  # (expected gain mass, alt probability of tape)


def robust_risk(f, q):
    """Exact Krale/causal recursion v(h) = max(v(h0), (v(h0)+v(h1))/2)."""

    def v(prefix):
        if len(prefix) == q:
            return f[prefix]
        a, b = v(prefix + (0,)), v(prefix + (1,))
        return max(a, (a + b) / 2)

    return v(())


def endpoint_rows(q):
    nodes = [p for k in range(q) for p in product((0, 1), repeat=k)]
    rows = []
    for choice in product((F(0), HALF), repeat=len(nodes)):
        strat = dict(zip(nodes, choice, strict=True))
        row = []
        for tape in tapes(q):
            prob = F(1)
            for k, y in enumerate(tape):
                p = strat[tape[:k]]
                prob *= p if y else 1 - p
            row.append(prob)
        rows.append(row)
    return rows


def solve(q, e0, e1, alpha, symmetric):
    ts = tapes(q)
    util = [alt_utility(t, e0, e1)[0] for t in ts]
    rows = endpoint_rows(q)
    # deduplicate rows
    rows = [list(r) for r in {tuple(r) for r in rows}]
    if symmetric:
        groups = list(range(q + 1))
        cvec = [-float(sum(u for t, u in zip(ts, util, strict=True) if sum(t) == k)) for k in groups]
        a_ub = [[float(sum(r[i] for i, t in enumerate(ts) if sum(t) == k)) for k in groups]
                for r in rows]
        nvar = q + 1
    else:
        cvec = [-float(u) for u in util]
        a_ub = [[float(x) for x in r] for r in rows]
        nvar = len(ts)
    res = linprog(cvec, A_ub=np.array(a_ub), b_ub=[float(alpha)] * len(rows),
                  bounds=[(0, 1)] * nvar, method="highs")
    assert res.success
    x = [F(v).limit_denominator(10**6) for v in res.x]
    f = {t: (x[sum(t)] if symmetric else x[i]) for i, t in enumerate(ts)}
    risk = robust_risk(f, q)
    scale = min(F(1), alpha / risk) if risk else F(1)
    f = {t: v * scale for t, v in f.items()}
    value = sum(u * f[t] for t, u in zip(ts, util, strict=True))
    duals = -np.array(res.ineqlin.marginals)
    support = [i for i, d in enumerate(duals) if d > 1e-9]
    iid_row = [F(1, 2**q)] * len(ts)
    support_is_iid_only = all(rows[i] == iid_row for i in support)
    return {"lp_value": -res.fun, "exact_value": value, "exact_robust_risk": robust_risk(f, q),
            "iid_risk": sum(F(1, 2**q) * v for v in f.values()),
            "policy": {"".join(map(str, t)): f[t] for t in ts if f[t]},
            "dual_support_size": len(support), "dual_support_iid_only": support_is_iid_only,
            "n_null_rows": len(rows)}


def main():
    out = {"purpose": "B4 counterexample search: static alternative, fixed calendar, d=1",
           "cases": []}
    for q in (2, 3, 4):
        for e0, e1 in ((F(1, 4), F(3, 4)), (F(1, 10), F(9, 10)), (F(1, 3), F(3, 4))):
            for alpha in (F(1, 20), F(1, 10), F(1, 4)):
                full = solve(q, e0, e1, alpha, symmetric=False)
                sym = solve(q, e0, e1, alpha, symmetric=True)
                gap = full["exact_value"] - sym["exact_value"]
                out["cases"].append({"q": q, "e0": e0, "e1": e1, "alpha": alpha,
                                     "unrestricted": full, "count_symmetric": sym,
                                     "gap_exact": gap, "gap_float": float(gap)})
                print(q, e0, e1, alpha, float(full["exact_value"]), float(sym["exact_value"]),
                      float(gap), full["dual_support_iid_only"], flush=True)
    write_result("b4_static_calendar_v1.json", out, Path(__file__))


if __name__ == "__main__":
    main()
