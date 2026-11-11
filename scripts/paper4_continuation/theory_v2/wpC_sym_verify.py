"""WP C: verify Theorem SP1 closed forms against gamma_cell (certified) and fu_b1_formula (N1, exact game).

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpC_sym_verify.py OUT.json PART NPARTS
Grid: symmetric stationary chains t in {3/5, 3/4, 9/10, 1}, e in {1/10, 1/5}, T in 2..7, d in 1..3,
c in {0, 1/100, 1/20}, k in {0, 1/50, 1/10}, alpha = 1/10 (plus alpha = 1/2 on a sub-grid).
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

from fu_b1_formula import formula  # noqa: E402
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpC_sym_lib import (closed_bounds, gamma_over_alpha_window, k0_closed,  # noqa: E402
                         ksmall_closed)


def main():
    out, part, nparts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    grid = []
    for t, e, T, d, c, k in itertools.product([F(3, 5), F(3, 4), F(9, 10), F(1)], [F(1, 10), F(1, 5)],
                                              range(2, 8), [1, 2, 3], [F(0), F(1, 100), F(1, 20)],
                                              [F(0), F(1, 50), F(1, 10)]):
        if T <= d:
            continue
        grid.append((t, e, T, d, c, k, F(1, 10)))
        if T == 5 and c == F(1, 100):
            grid.append((t, e, T, d, c, k, F(1, 2)))
    grid = grid[part::nparts]
    rows, t0 = [], time.time()
    for (t, e, T, d, c, k, al) in grid:
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        cert = gamma_cell(T, 1, d, t, t, e, 1 - e, F(1, 2), c, k, al)
        lo, hi = F(cert["Gamma_lo"]), F(cert["Gamma_hi"])
        n1, parts = formula(T, d, t, t, e, 1 - e, F(1, 2), c, k, al)
        win, wparts = gamma_over_alpha_window(T, d, r, g, c, k)
        lb, ub = closed_bounds(T, d, r, g, c, k)
        row = {"t": str(t), "e": str(e), "T": T, "d": d, "c": str(c), "k": str(k), "alpha": str(al),
               "Gamma_lo": str(lo), "Gamma_hi": str(hi), "N1": str(n1), "window": str(al * win),
               "LB": str(al * lb), "UB": str(al * ub),
               "kappa": str(wparts.get("kappa")), "g_pre": parts["g_pre"],
               "ok_window": lo <= al * win <= hi, "ok_N1": lo <= n1 <= hi,
               "ok_sandwich": al * lb <= lo and hi <= al * ub if True else None,
               "positive": lo > 0}
        # sandwich: closed LB <= true <= closed UB (true certified in [lo,hi])
        row["ok_sandwich"] = (al * lb <= hi) and (lo <= al * ub)
        if k == 0:
            row["k0"] = str(al * k0_closed(T, d, r, g, c))
            row["ok_k0"] = lo <= al * k0_closed(T, d, r, g, c) <= hi
        if d % 2 == 1 and T >= d + 2 and r < 1 and 2 * k < g * r ** (T - 1):
            ks = al * ksmall_closed(T, d, r, g, c, k)
            row["ksmall"] = str(ks)
            row["ok_ksmall"] = lo <= ks <= hi
        if r == 1 and d % 2 == 1 and T % 2 == 1 and d == 1:
            row["C3_oddT_zero"] = hi <= 0
        rows.append(row)
    summ = {
        "n": len(rows),
        "n_ok_window": sum(r["ok_window"] for r in rows),
        "n_ok_N1": sum(r["ok_N1"] for r in rows),
        "n_ok_sandwich": sum(r["ok_sandwich"] for r in rows),
        "n_k0": sum("ok_k0" in r for r in rows), "n_ok_k0": sum(r.get("ok_k0", False) for r in rows),
        "n_ksmall": sum("ok_ksmall" in r for r in rows),
        "n_ok_ksmall": sum(r.get("ok_ksmall", False) for r in rows),
        "n_positive": sum(r["positive"] for r in rows),
        "n_positive_even_d_r_lt_1": sum(r["positive"] for r in rows if r["d"] % 2 == 0 and r["t"] != "1"),
        "n_positive_window_but_not_cert": sum((F(r["window"]) > 0) != r["positive"] for r in rows),
        "n_kappa_positive": sum(r["kappa"] not in ("None",) and F(r["kappa"]) > 0 for r in rows),
        "n_C3_oddT": sum("C3_oddT_zero" in r for r in rows),
        "n_C3_oddT_zero": sum(r.get("C3_oddT_zero", False) for r in rows),
        "seconds": time.time() - t0,
    }
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpC_sym_verify.py",
                                "part": part, "nparts": nparts, "summary": summ, "rows": rows})
    print(summ)
    for r in rows:
        if not (r["ok_window"] and r["ok_N1"] and r["ok_sandwich"] and r.get("ok_k0", True)
                and r.get("ok_ksmall", True)):
            print("FAIL", r)


if __name__ == "__main__":
    main()
