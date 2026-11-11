"""Reviewer 1 red team for Theorem SP1 (STOCHASTIC_POSITIVE_PREMIUM.md) against certified gamma_cell.

usage: rev1_sp1_redteam.py OUT.json WORKER NWORKERS [SEED NCELLS]
Adversarial symmetric stationary cells (t01=t10=t, e0=e, e1=1-e, prior 1/2, B=1):
  k at / near the cover thresholds g r^j / 2, c at / near (a_d-k)/2 and (Delta+k)/2, T in {d+1, d+2, ...},
  r near 0 and near 1 (incl. r = 1), e near 0 and near 1/2, alpha in {1/20, 1/4, 1/2}.
Per cell: certified [Gamma_lo, Gamma_hi] from theory_C gamma_cell (force_fcg=True so V_causal is FCG-certified),
the SP1 closed form (rev1_sp1_lib.sp1_formula, independent) and the N1-by-brute-DP value (rev1_sp1_lib.n1_brute_sym).
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from rev1_sp1_lib import n1_brute_sym, sp1_formula, sp1_lower_bound  # noqa: E402

TS = [F(1), F(999, 1000), F(99, 100), F(9, 10), F(3, 4), F(3, 5), F(51, 100), F(501, 1000)]
ES = [F(1, 1000), F(1, 20), F(1, 10), F(1, 4), F(49, 100)]
AL = [F(1, 20), F(1, 4), F(1, 2)]
EPS = F(1, 1000)


def k_choices(g, r, d):
    out = [F(0)]
    for j in (d, d + 1, d + 2):
        th = g * r**j / 2
        out += [th, th * (1 - EPS), th * (1 + EPS)]
    out.append(g * r**d)  # k = a_d: G0 <= 0 edge
    return out


def c_choices(g, r, d, k, T, t, e):
    ad = g * r**d
    out = [F(0)]
    base = (ad - k) / 2
    if base > 0:
        out += [base, base * (1 - EPS), base * (1 + EPS)]
    # c near the hedge threshold (Delta+k)/2, using Delta from the formula with c=0 (Delta indep. of c)
    hed = sp1_lower_bound(d, t, e, 0, k)  # min{(ad-k)/2, ad-ad1, (ad-ad1+k)/2} at c=0
    if hed > 0:
        out += [hed, hed * (1 - EPS)]
    return out


def cells(seed, n):
    rng = random.Random(seed)
    out = []
    # structured: SP1-D bullet-1 suspect (r=1, T=d+1, k < g <= 2k) and threshold ties
    for d in (1, 3):
        for e in (F(1, 10), F(1, 4)):
            g = (1 - 2 * e) ** 2
            for kk in (g * 3 / 4, g / 2, g * 9 / 10):
                for al in AL:
                    out.append((d + 1, d, F(1), e, F(0), kk, al, "SP1-D_T=d+1_g<=2k"))
    seen = set(out)
    while len(out) < n:
        t = rng.choice(TS)
        e = rng.choice(ES)
        d = rng.choice([1, 1, 2, 3, 3, 4])
        T = rng.choice([d + 1, d + 1, d + 2, d + 2, d + 3, min(8, d + 4), min(8, d + 5)])
        T = max(T, d + 1)
        if T > 8:
            continue
        r = 2 * t - 1
        g = (1 - 2 * e) ** 2
        k = rng.choice(k_choices(g, r, d))
        c = rng.choice(c_choices(g, r, d, k, T, t, e))
        al = rng.choice(AL)
        cell = (T, d, t, e, c, k, al, "rand")
        if cell[:7] in {x[:7] for x in seen}:
            continue
        seen.add(cell)
        out.append(cell)
    return out


def main():
    out_path, w, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    allc = cells(seed, n)
    mine = allc[w::nw]
    rows, fails = [], 0
    t0 = time.time()
    for T, d, t, e, c, k, al, tag in mine:
        res = gamma_cell(T, 1, d, t, t, e, 1 - e, F(1, 2), c, k, al, force_fcg=True)
        lo, hi = F(res["Gamma_lo"]), F(res["Gamma_hi"])
        f = sp1_formula(T, d, t, e, c, k, al)
        b = n1_brute_sym(T, d, t, e, c, k, al)
        ok_f = lo <= f <= hi
        ok_b = lo <= b <= hi
        fails += (not ok_f) or (not ok_b)
        rows.append(
            dict(
                T=T, d=d, t=str(t), e=str(e), c=str(c), k=str(k), alpha=str(al), tag=tag,
                Gamma_lo=str(lo), Gamma_hi=str(hi), width=float(hi - lo),
                sp1=str(f), n1_brute=str(b), sp1_in=ok_f, brute_in=ok_b, sp1_eq_brute=(f == b),
                src=res["V_causal_source"],
            )
        )
    payload = dict(
        script="rev1_sp1_redteam.py", worker=w, nworkers=nw, seed=seed, ncells_total=len(allc),
        ncells=len(rows), failures=fails,
        sp1_in=sum(r["sp1_in"] for r in rows), brute_in=sum(r["brute_in"] for r in rows),
        sp1_eq_brute=sum(r["sp1_eq_brute"] for r in rows),
        positive=sum(F(r["Gamma_lo"]) > 0 for r in rows),
        max_width=max((r["width"] for r in rows), default=0.0),
        seconds=time.time() - t0, rows=rows,
    )
    save_refuse_overwrite(out_path, payload)
    print({k_: v for k_, v in payload.items() if k_ != "rows"})


if __name__ == "__main__":
    main()
