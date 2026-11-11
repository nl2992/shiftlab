"""rev3 P5 red team: certified gamma_cell cells vs M1-M5, using the independent rev3_mix_lib evaluators.

Usage (repo root):  nice -n 10 uv run --no-sync python scripts/paper4_continuation/theory_v2/rev3_mix_redteam.py SET OUT.json
SET in {b1, b2}.  One process; refuse-overwrite output.  Every comparison is exact-rational against the certified
intervals (VOI_X = C0 - V_X, C0 = T/2).  A 'fail' means a certified interval excludes the theorem's claim.
"""
from __future__ import annotations

import json
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "theory_C"))

from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from rev3_mix_lib import (  # noqa: E402
    U_B, Chain, best_ratio_pure, m1_prediction, m4_bound, slopes,
)

TS = [F(11, 20), F(2, 3), F(3, 4), F(17, 20), F(9, 10)]
E = F(1, 10)


def cells_b1():
    out = []
    for t in TS:
        for d in (1, 3):
            for c in (F(0), F(1, 200), F(1, 100)):
                for T in sorted({d + 1, d + 2, 9, 12}):
                    out.append((T, 1, d, t, E, c, F(0), F(1, 4)))
                for al in (F(1, 20), F(1, 4), F(1, 2)):
                    out.append((10, 1, d, t, E, c, F(0), al))
    k = F(1, 50)
    for t in (F(2, 3), F(3, 4)):
        ch = Chain(t, E)
        cstar = (ch.g * ch.r * (1 - ch.r) - k) / 2
        for c in (cstar - F(1, 1000), cstar):
            for T in (3, 6, 9):
                out.append((T, 1, 1, t, E, c, k, F(1, 4)))
    for t in (F(2, 3), F(3, 4)):  # Pi threshold at k = 0: c = g r/(2(1+r))
        ch = Chain(t, E)
        c = ch.g * ch.r / (2 * (1 + ch.r))
        for T in (4, 5, 6, 7):
            out.append((T, 1, 1, t, E, c, F(0), F(1, 4)))
    for T in (4, 6, 8):  # scope probe alpha > 1/2
        out.append((T, 1, 1, F(3, 4), E, F(0), F(0), F(3, 4)))
    return list(dict.fromkeys(out))


def cells_b2():
    out = []
    a = F(1, 20)
    fam = {
        (F(11, 20), 1): (2, 3, 4, 8), (F(11, 20), 3): (4, 5, 6, 8),
        (F(2, 3), 1): (4, 5, 6, 7, 10), (F(2, 3), 3): (6, 7, 8, 9),
        (F(3, 4), 1): (8, 9, 10, 11, 12), (F(3, 4), 3): (10, 11, 12),
        (F(17, 20), 1): (6, 10, 12), (F(17, 20), 3): (8, 12),
        (F(9, 10), 1): (6, 10, 12), (F(9, 10), 3): (8, 12),
    }
    for (t, d), Ts in fam.items():
        for T in Ts:
            out.append((T, 2, d, t, E, F(0), F(0), a))
    for t in (F(11, 20), F(2, 3), F(3, 4)):
        for c in (F(1, 200), F(1, 100)):
            for T in (6, 10):
                out.append((T, 2, 1, t, E, c, F(0), a))
            for T in (8, 11):
                out.append((T, 2, 3, t, E, c, F(0), a))
    for t, d, T0 in ((F(2, 3), 1, 6), (F(2, 3), 3, 8), (F(3, 4), 1, 10), (F(3, 4), 3, 12)):
        for al in (F(1, 4), F(1, 2)):
            for T in sorted({T0, 10}):
                out.append((T, 2, d, t, E, F(0), F(0), al))
    for c in (F(1, 80), F(1, 75)):  # near the M4 limiting cost threshold g r/(16(1+r)) = 1/75 at t = 3/4, d = 1
        for T in (10, 12):
            out.append((T, 2, 1, F(3, 4), E, c, F(0), a))
    for t in (F(3, 4), F(2, 3)):
        out.append((14, 2, 1, t, E, F(0), F(0), a))
    return list(dict.fromkeys(out))


def le(x, y):
    return x <= y


def run_cell(cell):
    T, B, d, t, e, c, k, al = cell
    t0 = time.time()
    g = gamma_cell(T, B, d, t, t, e, 1 - e, c=c, k=k, alpha=al)
    C0 = F(T, 2)
    LI, UI = F(g["L_IID"]), F(g["U_IID"])
    LC, UC = F(g["L_causal"]), F(g["U_causal"])
    voi_i = (C0 - UI, C0 - LI)
    voi_c = (C0 - UC, C0 - LC)
    gam = (F(g["Gamma_lo"]), F(g["Gamma_hi"]))
    rho_lo = max(gam[0], 0) / voi_i[1] if voi_i[1] > 0 else F(0)
    rho_hi = gam[1] / voi_i[0] if voi_i[0] > 0 else None
    ch = Chain(t, e)
    rec = {"cell": dict(T=T, B=B, d=d, t=str(t), e=str(e), c=str(c), k=str(k), alpha=str(al)),
           "Gamma": [str(x) for x in gam], "VOI_IID": [str(x) for x in voi_i], "VOI_causal": [str(x) for x in voi_c],
           "rhoG": [float(rho_lo), None if rho_hi is None else float(rho_hi)],
           "source": g["V_causal_source"], "checks": {}, "values": {}}
    ck, vals = rec["checks"], rec["values"]
    UB = U_B(ch, B, d)
    ck["M2b_IID"] = le(voi_i[0], al * UB)
    ck["M2b_causal"] = le(voi_c[0], al * UB)
    vals["alpha_UB"] = float(al * UB)
    if B == 1 and al <= F(1, 2):
        p = m1_prediction(ch, T, d, c, k)
        vals.update({kk: float(v) if isinstance(v, F) else v for kk, v in p.items() if v is not None})
        ck["M1_1_rho_in_interval"] = rho_lo <= p["rhoG_pred"] and (rho_hi is None or p["rhoG_pred"] <= rho_hi)
        ck["M1_1_Gamma_in_interval"] = gam[0] <= al * p["Gamma_over_alpha_pred"] <= gam[1]
        if "rhoG_m1_3" in p:
            ck["M1_3_equals_M1_1"] = p["rhoG_m1_3"] == p["rhoG_pred"]
        if "c1" in p:
            ck["M1_2_c1_le_rho"] = rho_hi is None or p["c1"] <= rho_hi
    if k == 0:
        s = slopes(ch, T, B, d, c)
        zb = best_ratio_pure(ch, T, B, d, c, al)
        vals.update({kk: float(v) for kk, v in s.items() if v is not None})
        vals["zeta_best_pure"] = float(zb)
        ck["M3i_causal_le_aSprime"] = le(voi_c[0], al * s["S_prime"])
        ck["M3ii_IID_le_aSI"] = le(voi_i[0], al * s["S_I"])
        ck["M3iii_Gamma_ge"] = le(al * (zb - s["S_prime"]), gam[1])
        ck["eval_consistency_IID_ge_zeta"] = le(al * zb, voi_i[1])
        vals["VOI_IID_over_alpha_mid"] = float((voi_i[0] + voi_i[1]) / 2 / al)
        vals["VOI_c_over_alpha_mid"] = float((voi_c[0] + voi_c[1]) / 2 / al)
        if s["S_I"] > 0 and s["H"] >= 0:
            ck["M5_rho_le"] = rho_lo <= 1 - s["H"] / s["S_I"]
        if B == 2 and d % 2 == 1 and al <= F(1, 2):
            m = m4_bound(ch, T, d, c)
            vals.update({kk: float(v) for kk, v in m.items()})
            ck["M4_Gamma_ge_bound"] = le(al * m["Gamma_over_alpha_bound"], gam[1])
            ck["M4_rho_ge_bound"] = rho_hi is None or le(m["rhoG_bound"], rho_hi)
            ck["M4_IID_ge_zeta_minus_4c"] = le(al * (m["zeta"] - 4 * c), voi_i[1])
            ck["M4_IID_le_s0inf"] = le(voi_i[0], al * m["s0inf"])
            vals["M4_bound_positive"] = m["Gamma_over_alpha_bound"] > 0
    rec["seconds"] = round(time.time() - t0, 2)
    return rec


def main():
    which, out = sys.argv[1], sys.argv[2]
    if os.path.exists(out):
        print(f"refusing to overwrite {out}", file=sys.stderr)
        sys.exit(2)
    cells = cells_b1() if which == "b1" else cells_b2()
    print(len(cells), "cells", flush=True)
    recs, fails = [], []
    for i, cell in enumerate(cells):
        rec = run_cell(cell)
        recs.append(rec)
        bad = [kk for kk, v in rec["checks"].items() if v is False]
        if bad:
            fails.append({"cell": rec["cell"], "failed": bad})
        print(i, rec["cell"], rec["seconds"], "FAIL " + ",".join(bad) if bad else "ok", flush=True)
    summary = {}
    for rec in recs:
        for kk, v in rec["checks"].items():
            s = summary.setdefault(kk, [0, 0])
            s[0] += v is True
            s[1] += 1
    save_refuse_overwrite(out, {"set": which, "n_cells": len(recs), "check_summary_pass_total": summary,
                                "failures": fails, "cells": recs})


if __name__ == "__main__":
    main()
