"""WP C (C1/C2 asymmetric + C3 modulus): stochastic anti-persistent asymmetric cells, B = 1.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpC_asym.py OUT.json SEED N [BUDGET_S]
Random cells: t01, t10 in (0,1) with t01 + t10 > 1, stationary prior, emissions e0 < 1/2 < e1,
T in 3..7, d in 1..3, c, k in {0, 1/100, 1/20}, alpha = 1/10.  For each cell:
  certified Gamma (gamma_cell), N1 closed form (fu_b1_formula), and the continuity bound (Prop. C3)
  Gamma >= Gamma_SP1(ref) - 8 alpha (T(1+k)+c) * TVB, ref = symmetric stationary cell with
  t = (t01+t10)/2, e = (e0 + 1 - e1)/2, TVB = |dp1| + (T-1) max|dt| + T max|de|.
"""

from __future__ import annotations

import os
import random
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))

from fu_b1_formula import formula  # noqa: E402
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpC_sym_lib import sp1_exact  # noqa: E402

TR = [F(11, 20), F(3, 5), F(13, 20), F(7, 10), F(3, 4), F(4, 5), F(17, 20), F(9, 10), F(19, 20)]
EM0 = [F(1, 20), F(1, 10), F(1, 5), F(3, 10)]
EM1 = [F(7, 10), F(4, 5), F(9, 10), F(19, 20)]
COST = [F(0), F(1, 100), F(1, 20)]


def main():
    out, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
    rng = random.Random(seed)
    rows, t0 = [], time.time()
    while len(rows) < n and time.time() - t0 < budget:
        t01, t10 = rng.choice(TR), rng.choice(TR)
        if t01 + t10 <= 1:
            continue
        sym_t = t01 == t10
        if rng.random() < 0.25:  # force a symmetric-emission sub-sample
            e0 = rng.choice(EM0)
            e1 = 1 - e0
        else:
            e0, e1 = rng.choice(EM0), rng.choice(EM1)
        T, d = rng.choice([3, 4, 5, 6, 7]), rng.choice([1, 2, 3])
        if T <= d:
            continue
        c, k, al = rng.choice(COST), rng.choice(COST), F(1, 10)
        pi = t01 / (t01 + t10)
        cert = gamma_cell(T, 1, d, t01, t10, e0, e1, pi, c, k, al)
        lo, hi = F(cert["Gamma_lo"]), F(cert["Gamma_hi"])
        n1, parts = formula(T, d, t01, t10, e0, e1, pi, c, k, al)
        # symmetric reference and continuity bound
        tr, er = (t01 + t10) / 2, (e0 + 1 - e1) / 2
        ref = al * sp1_exact(T, d, 2 * tr - 1, (1 - 2 * er) ** 2, c, k)
        tvb = abs(pi - F(1, 2)) + (T - 1) * max(abs(t01 - tr), abs(t10 - tr)) + T * max(abs(e0 - er),
                                                                                        abs(e1 - 1 + er))
        mod = 8 * al * (T * (1 + k) + c) * tvb
        qbar = e0 + (e1 - e0) * pi
        rows.append({"t01": str(t01), "t10": str(t10), "e0": str(e0), "e1": str(e1), "prior": str(pi),
                     "T": T, "d": d, "c": str(c), "k": str(k), "alpha": str(al),
                     "sym_t": sym_t, "sym_e": e0 + e1 == 1, "qbar": str(qbar),
                     "Gamma_lo": str(lo), "Gamma_hi": str(hi), "positive": lo > 0,
                     "N1": str(n1), "ok_N1": lo <= n1 <= hi, **parts,
                     "SP1_ref": str(ref), "TVB": str(tvb), "modulus": str(mod),
                     "ok_continuity": hi >= ref - mod and lo <= ref + mod,
                     "continuity_informative": ref - mod > 0})
    def cnt(f):
        return sum(1 for r in rows if f(r))
    summ = {"n": len(rows), "ok_N1": cnt(lambda r: r["ok_N1"]), "positive": cnt(lambda r: r["positive"]),
            "ok_continuity": cnt(lambda r: r["ok_continuity"]),
            "continuity_informative": cnt(lambda r: r["continuity_informative"])}
    for dd in (1, 2, 3):
        summ[f"d{dd}"] = [cnt(lambda r: r["d"] == dd), cnt(lambda r: r["d"] == dd and r["positive"])]
    for lab, f in (("qbar>1/2", lambda r: F(r["qbar"]) > F(1, 2)), ("qbar<1/2", lambda r: F(r["qbar"]) < F(1, 2)),
                   ("qbar=1/2", lambda r: F(r["qbar"]) == F(1, 2))):
        summ[lab] = [cnt(f), cnt(lambda r: f(r) and r["positive"])]
    summ["seconds"] = time.time() - t0
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpC_asym.py", "seed": seed,
                                "summary": summ, "rows": rows})
    print(summ)


if __name__ == "__main__":
    main()
