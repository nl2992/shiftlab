"""WP C: Theorem SP1 exact closed form vs certified gamma_cell and N1 (fu_b1_formula) -- B = 1.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpC_sp1_certified.py OUT.json PART NPARTS
Grid: t in {11/20, 3/5, 3/4, 9/10, 1}, e in {1/20, 1/10, 1/5, 3/10}, T in 2..8, d in 1..4,
c in {0, 1/100, 1/20}, k in {0, 1/50, 1/10}; alpha = 1/10, plus alpha in {1/4, 1/2} when T = 6.
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
from wpC_sym_lib import gamma_over_alpha_window, sp1_exact, sp1_lower  # noqa: E402


def main():
    out, part, nparts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    grid = []
    for t, e, T, d, c, k in itertools.product(
            [F(11, 20), F(3, 5), F(3, 4), F(9, 10), F(1)], [F(1, 20), F(1, 10), F(1, 5), F(3, 10)],
            range(2, 9), [1, 2, 3, 4], [F(0), F(1, 100), F(1, 20)], [F(0), F(1, 50), F(1, 10)]):
        if T <= d:
            continue
        for al in ([F(1, 10), F(1, 4), F(1, 2)] if T == 6 else [F(1, 10)]):
            grid.append((t, e, T, d, c, k, al))
    grid = grid[part::nparts]
    rows, t0 = [], time.time()
    for (t, e, T, d, c, k, al) in grid:
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        cert = gamma_cell(T, 1, d, t, t, e, 1 - e, F(1, 2), c, k, al)
        lo, hi = F(cert["Gamma_lo"]), F(cert["Gamma_hi"])
        n1, parts = formula(T, d, t, t, e, 1 - e, F(1, 2), c, k, al)
        ex = al * sp1_exact(T, d, r, g, c, k)
        win, _ = gamma_over_alpha_window(T, d, r, g, c, k)
        row = {"t": str(t), "e": str(e), "T": T, "d": d, "c": str(c), "k": str(k), "alpha": str(al),
               "Gamma_lo": str(lo), "Gamma_hi": str(hi), "SP1": str(ex), "N1": str(n1),
               "ok_SP1": lo <= ex <= hi, "ok_N1": lo <= n1 <= hi, "ok_window": al * win == ex,
               "positive": lo > 0, "exact_interval": lo == hi,
               "g_pre_le_r_c": F(parts["g_pre"]) <= F(parts["r_c"])}
        if d % 2 == 1:
            row["LB"] = str(al * sp1_lower(d, r, g, c, k))
            row["ok_LB"] = al * sp1_lower(d, r, g, c, k) <= hi
        rows.append(row)
    summ = {k2: sum(r.get(k2, False) for r in rows) for k2 in
            ("ok_SP1", "ok_N1", "ok_window", "positive", "exact_interval", "g_pre_le_r_c", "ok_LB")}
    summ["n"] = len(rows)
    summ["n_odd_d"] = sum(r["d"] % 2 for r in rows)
    summ["n_positive_even_d"] = sum(r["positive"] for r in rows if r["d"] % 2 == 0)
    summ["seconds"] = time.time() - t0
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpC_sp1_certified.py",
                                "part": part, "nparts": nparts, "summary": summ, "rows": rows})
    print(summ)
    for r in rows:
        if not (r["ok_SP1"] and r["ok_N1"] and r["ok_window"] and r.get("ok_LB", True)):
            print("FAIL", r)


if __name__ == "__main__":
    main()
