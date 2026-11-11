"""WP-M (P1): Theorem M1 (B = 1 relative premium) against certified gamma_cell, and against wpC2 data.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpM_b1_check.py OUT.json
Single process.  rho certified interval: [Gamma_lo / (C0 - L_IID), Gamma_hi / (C0 - U_IID)].
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))
sys.set_int_max_str_digits(0)

from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpM_b1_lib import rho_exact, rho_limit_k0, rho_lower  # noqa: E402


def certified_rho(T, d, t, e, c, k, alpha):
    o = gamma_cell(T, 1, d, t, t, e, 1 - e, F(1, 2), c, k, alpha)
    C0 = F(T, 2)
    glo, ghi = F(o["Gamma_lo"]), F(o["Gamma_hi"])
    vlo, vhi = C0 - F(o["U_IID"]), C0 - F(o["L_IID"])
    lo = max(F(0), glo) / vhi if vhi > 0 else F(0)
    hi = max(F(0), ghi) / vlo if vlo > 0 else F(0)
    return lo, hi, o


def main():
    out = sys.argv[1]
    rows, fails = [], []
    t_start = time.time()
    grid = list(itertools.product([F(2, 3), F(3, 4), F(9, 10)], [F(1, 10), F(1, 5)], [1, 3],
                                  [F(0), F(1, 100)], [F(0), F(1, 50)]))
    for t, e, d, c, k in grid:
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        Ts = sorted({d + 1, d + 2, 6, 8, 10, 11, 12, 14})
        lb = rho_lower(d, r, g, c, k)
        for T in Ts:
            alphas = [F(1, 10)] + ([F(1, 20), F(1, 2)] if T == 8 else [])
            for alpha in alphas:
                t0 = time.time()
                lo, hi, o = certified_rho(T, d, t, e, c, k, alpha)
                ex = rho_exact(T, d, r, g, c, k)
                ok_exact = lo - F(1, 10**9) <= ex <= hi + F(1, 10**9)
                ok_lb = lb is None or lb <= hi + F(1, 10**9)
                row = {"t": str(t), "e": str(e), "d": d, "c": str(c), "k": str(k), "T": T,
                       "alpha": str(alpha), "rho_cert_lo": float(lo), "rho_cert_hi": float(hi),
                       "rho_M1_exact": float(ex), "rho_M1_lower": None if lb is None else float(lb),
                       "exact_inside": ok_exact, "lower_ok": ok_lb, "src": o["V_causal_source"],
                       "sec": round(time.time() - t0, 2)}
                rows.append(row)
                if not (ok_exact and ok_lb):
                    fails.append(row)
                print(json.dumps(row), flush=True)
    # data check: wpC2 compact F_anti B = 1 cells
    data = json.load(open(os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/"
                                             "wpC2_relative_premium_v1_compact.json")))
    drows = []
    for cell in data["cells"]:
        if cell["family"] != "F_anti" or cell["B"] != 1 or cell["status"] != "ok":
            continue
        t, e, c, k = F(cell["t01"]), F(cell["e0"]), F(cell["c"]), F(cell["k"])
        ex = rho_exact(cell["T"], cell["d"], 2 * t - 1, (1 - 2 * e) ** 2, c, k)
        lo, hi = cell["rho_interval"]
        drows.append({"t": cell["t01"], "k": cell["k"], "T": cell["T"], "alpha": cell["alpha"],
                      "rho_data": cell["rho_mid"], "rho_M1": float(ex),
                      "match": abs(float(ex) - cell["rho_mid"]) <= 1e-7})
    limits = {}
    for t, e, d, c in itertools.product([F(2, 3), F(3, 4), F(9, 10)], [F(1, 10), F(1, 5)], [1, 3],
                                        [F(0), F(1, 100)]):
        r, g = 2 * t - 1, (1 - 2 * e) ** 2
        limits[f"t={t},e={e},d={d},c={c},k=0"] = float(rho_limit_k0(d, r, g, c))
    payload = {"script": os.path.relpath(__file__, ROOT), "n_cells": len(rows), "n_fail": len(fails),
               "fails": fails, "rows": rows, "data_check": {"n": len(drows),
                                                             "n_match": sum(x["match"] for x in drows),
                                                             "rows": drows},
               "k0_limits": limits, "elapsed_s": round(time.time() - t_start, 1)}
    save_refuse_overwrite(out, payload)
    print("cells", len(rows), "fails", len(fails), "data", len(drows), sum(x["match"] for x in drows))


if __name__ == "__main__":
    main()
