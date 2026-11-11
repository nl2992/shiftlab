"""WP-M (P1): Theorem M4 (B = 2, k = 0) against certified gamma_cell, plus the first-label relaxation LP.

usage (repo root): uv run --no-sync python scripts/paper4_continuation/theory_v2/wpM_b2_check.py OUT.json
Single process.  Checks per cell:
  (a) certified Gamma/alpha >= M4 bound (zeta(T) - 4c - (s0inf + s1inf)/2);
  (b) certified VOI_IID/alpha <= s0inf (Theorem M4 upper bound S_I^inf, c = 0 value is an upper bound for c > 0);
  (c) certified VOI_IID/alpha >= zeta(T) - 4c (explicit IID plan);
  (d) float LP with rows {IID, nu_1} (nu_1: p = 0 at the first query, 1/2 after):
      V_IID <= V_N' <= V_causal and VOI_N'/alpha <= max(H_empty, s1, (s0+s1)/2) at the brute finite-T slopes.
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import time
from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import vstack

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))
sys.set_int_max_str_digits(0)

from gamma_lib import gamma_cell, make, save_refuse_overwrite  # noqa: E402
from shiftlab.paper4.frontier_cuts_fast import FastGame, float_risk_row  # noqa: E402
from wpM_b2_lib import H_empty, branch_slopes, closed_inf, m4_bound  # noqa: E402


def relax_lp(T, B, d, t, e, c, k, alpha):
    config, model = make(T, B, d, t, t, e, 1 - e, F(1, 2), c, k, alpha)
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    n = game.learner.count
    flow, rhs = game.learner.matrix()
    obj = np.zeros(n)
    for key, value in game.cost.items():
        obj[key] = value
    nu1 = {(((0, 0),) * m, ()): F(0) for m in range(T)}
    rows = vstack([float_risk_row(game, {}, n), float_risk_row(game, nu1, n)])
    out = {}
    for name, A in (("IID", rows[0]), ("Nprime", rows)):
        res = linprog(obj, A_ub=A, b_ub=[float(alpha)] * A.shape[0], A_eq=flow, b_eq=rhs,
                      bounds=[(0, None)] * n, method="highs",
                      options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
        out[name] = float(res.fun)
    return out


def main():
    out = sys.argv[1]
    rows, fails = [], []
    t_start = time.time()
    grid = list(itertools.product([F(2, 3), F(3, 4), F(9, 10)], [F(1, 10)], [1, 3], [F(0), F(1, 100)]))
    for t, e, d, c in grid:
        ci = closed_inf(t, e, d)
        Ts = [T for T in (4, 6, 8, 10, 12) if T >= d + 2]
        if (t, e, d, c) in {(F(3, 4), F(1, 10), 1, F(0)), (F(9, 10), F(1, 10), 1, F(0)),
                            (F(2, 3), F(1, 10), 1, F(0))}:
            Ts.append(14)
        for T in Ts:
            sl = branch_slopes(t, e, d, T)
            s0T = max(sl[0])
            s1T = max(sl[1])
            hE = H_empty(t, e, d, T)
            for alpha in ((F(1, 20),) if T == 14 else (F(1, 20), F(1, 4))):
                t0 = time.time()
                o = gamma_cell(T, 2, d, t, t, e, 1 - e, F(1, 2), c, F(0), alpha)
                C0 = F(T, 2)
                glo, ghi = F(o["Gamma_lo"]), F(o["Gamma_hi"])
                voi_lo, voi_hi = C0 - F(o["U_IID"]), C0 - F(o["L_IID"])
                m4 = m4_bound(t, e, d, T, c)
                tol = F(1, 10**9)
                ok_a = glo / alpha >= m4["gamma_over_alpha_lb"] - tol
                ok_b = voi_lo / alpha <= ci["s0"] + tol
                ok_c = voi_hi / alpha >= m4["zeta"] - tol
                row = {"t": str(t), "e": str(e), "d": d, "c": str(c), "T": T, "alpha": str(alpha),
                       "Gamma_over_alpha_cert": [float(glo / alpha), float(ghi / alpha)],
                       "VOI_IID_over_alpha_cert": [float(voi_lo / alpha), float(voi_hi / alpha)],
                       "rho_cert": [float(max(F(0), glo) / voi_hi), float(max(F(0), ghi) / voi_lo)],
                       "M4_gamma_over_alpha_lb": float(m4["gamma_over_alpha_lb"]),
                       "M4_rho_lb": float(m4["rho_lb"]), "zeta": float(m4["zeta"]),
                       "s0inf": float(ci["s0"]), "s1inf": float(ci["s1"]),
                       "s0_T_brute": float(s0T), "s1_T_brute": float(s1T), "H_empty_T_brute": float(hE),
                       "ok_gamma_lb": ok_a, "ok_voi_ub": ok_b, "ok_voi_lb": ok_c,
                       "src": o["V_causal_source"]}
                if c == 0:
                    lp = relax_lp(T, 2, d, t, e, c, F(0), alpha)
                    v_iid, v_np = lp["IID"], lp["Nprime"]
                    s_prime = max(float(hE), float(s1T), float((s0T + s1T) / 2))
                    row.update({"V_IID_lp": v_iid, "V_Nprime_lp": v_np,
                                "VOI_Nprime_over_alpha": (float(C0) - v_np) / float(alpha),
                                "S_prime_T": s_prime,
                                "ok_relax_order": v_iid - 1e-8 <= v_np <= float(F(o["U_causal"])) + 1e-8,
                                "ok_relax_slope": (float(C0) - v_np) / float(alpha) <= s_prime + 1e-7})
                row["sec"] = round(time.time() - t0, 2)
                okall = all(v for kk, v in row.items() if kk.startswith("ok_"))
                row["ok_all"] = okall
                rows.append(row)
                if not okall:
                    fails.append(row)
                print(json.dumps(row), flush=True)
    payload = {"script": os.path.relpath(__file__, ROOT), "n_cells": len(rows), "n_fail": len(fails),
               "fails": fails, "rows": rows, "elapsed_s": round(time.time() - t_start, 1)}
    save_refuse_overwrite(out, payload)
    print("cells", len(rows), "fails", len(fails))


if __name__ == "__main__":
    main()
