"""WP C: exact-rational sweep of Theorem SP1 (window DP = N1 + Lemma Pre) vs the closed form, plus C2d tables.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpC_sp1_sweep.py OUT.json
No LP is solved here: the window DP is an independent brute-force evaluation of N1's design gains in the
symmetric stationary family (the reduction itself is certified against gamma_cell by wpC_sp1_certified.py).
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

from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpC_sym_lib import gamma_over_alpha_window, k0_closed, sp1_exact, sp1_lower  # noqa: E402


def main():
    out = sys.argv[1]
    t0 = time.time()
    # 1. closed form == window DP, and LB <= exact
    n = ok = lb_ok = ev0 = ev = 0
    fails = []
    for t, e, T, d, c, k in itertools.product(
            [F(11, 20), F(3, 5), F(3, 4), F(9, 10), F(19, 20), F(1)], [F(1, 20), F(1, 10), F(1, 5), F(3, 10)],
            range(2, 16), [1, 2, 3, 4, 5], [F(0), F(1, 100), F(1, 20)],
            [F(0), F(1, 100), F(1, 50), F(1, 20), F(1, 10), F(1, 5)]):
        if T <= d:
            continue
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        w, _ = gamma_over_alpha_window(T, d, r, g, c, k)
        ex = sp1_exact(T, d, r, g, c, k)
        n += 1
        ok += w == ex
        if w != ex:
            fails.append([str(x) for x in (t, e, T, d, c, k, w, ex)])
        if d % 2 == 1:
            lb_ok += sp1_lower(d, r, g, c, k) <= w
        else:
            ev += 1
            ev0 += w == 0
    check = {"n": n, "closed_eq_window": ok, "fails": fails[:20], "LB_le_exact_odd_d": lb_ok,
             "even_d_cells": ev, "even_d_zero": ev0}
    # 2. C2d tables (alpha-normalised, exact)
    tables = {}
    g = (1 - 2 * F(1, 10)) ** 2  # e = 1/10
    for (lab, k, c) in (("k0_c0", F(0), F(0)), ("k0_c1/100", F(0), F(1, 100)),
                        ("k1/50_c1/100", F(1, 50), F(1, 100)), ("k1/10_c0", F(1, 10), F(0))):
        tab = {}
        for t in (F(3, 5), F(3, 4), F(9, 10), F(1)):
            r = 2 * t - 1
            tab[str(t)] = {f"d{d}": [str(sp1_exact(T, d, r, g, c, k)) for T in range(2, 31)]
                           for d in (1, 2, 3, 5)}
        tables[lab] = {"T_range": [2, 30], "e": "1/10", "rows_by_t": tab}
    # 3. k = 0 closed form vs exact, larger T
    k0 = sum(sp1_exact(T, d, 2 * t - 1, g, c, F(0)) == k0_closed(T, d, 2 * t - 1, g, c)
             for t in (F(3, 5), F(3, 4), F(9, 10)) for T in range(2, 41) for d in (1, 2, 3, 4)
             for c in (F(0), F(1, 100)))
    # 4. mixing threshold, d = 1, T -> infinity proxy T = 60
    mix = {}
    for (k, c) in ((F(0), F(0)), (F(0), F(1, 100)), (F(1, 50), F(0)), (F(1, 50), F(1, 100))):
        mix[f"k{k}_c{c}"] = [[str(t), str(sp1_exact(60, 1, 2 * t - 1, g, c, k))]
                             for t in (F(51, 100), F(26, 50), F(53, 100), F(11, 20), F(3, 5), F(13, 20), F(7, 10),
                                       F(3, 4), F(4, 5), F(9, 10), F(19, 20))]
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpC_sp1_sweep.py", "check": check,
               "k0_closed_eq_exact": [k0, 3 * 39 * 4 * 2], "tables": tables, "mixing_d1_T60": mix,
               "seconds": time.time() - t0}
    save_refuse_overwrite(out, payload)
    print(check, payload["k0_closed_eq_exact"], payload["seconds"])


if __name__ == "__main__":
    main()
