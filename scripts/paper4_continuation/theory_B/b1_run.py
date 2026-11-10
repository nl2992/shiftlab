"""B1 experiments: pricing-state counts, exactness checks, policy-column generation with
causal-null row generation, and the invalid 'lower bound' from restricted pricing.

Usage: uv run --no-sync python scripts/paper4_continuation/theory_B/b1_run.py
Writes docs/paper4_continuation/theory_B/results/b1_column_generation_v1.json (refuses overwrite).
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).parent))
from b1_pricing import Pricing, column_metrics, mixture_robust_risk  # noqa: E402
from b_common import built_game, cell, describe, write_result  # noqa: E402

from shiftlab.paper4.frontier_cuts import exact_costs, risk_row_for_null  # noqa: E402
from shiftlab.paper4.frontier_cuts_fast import frontier_cut_generation_fast  # noqa: E402

E20 = (F(1, 20), F(19, 20))
E4 = (F(1, 4), F(3, 4))
CELLS = [
    # id, T, B, d, transition, emissions, role
    ("C1", 5, 2, 1, F(1, 4), E20, "persistent HMM"),
    ("C2", 5, 2, 1, F(9, 10), (F(1, 10), F(9, 10)), "reversal HMM"),
    ("C3", 6, 3, 1, F(3, 4), E20, "reversal HMM"),
    ("C4", 6, 3, 1, F(1, 4), E20, "persistent HMM"),
    ("H5", 6, 2, 2, F(1, 10), E4, "persistent HMM d=2"),
    ("C6", 8, 3, 1, F(3, 4), E20, "reversal HMM scale"),
    ("S1", 6, 3, 1, F(0), E20, "static alternative"),
    ("S2", 6, 2, 2, F(0), E4, "static alternative d=2"),
    ("S3", 8, 3, 1, F(0), E4, "static alternative"),
    ("S4", 8, 3, 2, F(0), E4, "static alternative d=2"),
]
LP_CHECK = {"C1", "C2", "C3", "C4", "S1", "S2"}


def rat(x):
    return F(float(x)).limit_denominator(10**9)


def lp_pricing_check(game, lam_iid):
    c = np.array([float(x) for x in exact_costs(game)])
    r = np.array([float(x) for x in risk_row_for_null(game, {})])
    eq, rhs = game.learner.matrix()
    res = linprog(c + float(lam_iid) * r, A_eq=eq, b_eq=rhs, bounds=[(0, None)] * len(c),
                  method="highs")
    return float(res.fun)


def solve_master(cols_c, cols_r, alpha):
    n, k = len(cols_c), len(cols_r[0])
    a_ub = np.array([[float(cols_r[j][i]) for j in range(n)] for i in range(k)])
    res = linprog([float(c) for c in cols_c], A_ub=a_ub, b_ub=[float(alpha)] * k,
                  A_eq=np.ones((1, n)), b_eq=[1.0], bounds=[(0, None)] * n, method="highs",
                  options={"primal_feasibility_tolerance": 1e-10,
                           "dual_feasibility_tolerance": 1e-10})
    assert res.success, res.message
    lam = tuple(max(F(0), -rat(m)) for m in res.ineqlin.marginals)
    return res, lam, rat(res.eqlin.marginals[0])


def column_generation(game, restrict=False, max_outer=25, max_inner=60):
    cfg = game.config
    alpha = cfg.alpha
    nus: list[dict] = []
    never = {info: (0, 0) for info in game.learner.infos}
    cols = [never]
    c_never = Pricing(game).solve((F(10**6),))[0][0]  # never-promote is optimal for huge lam
    assert column_metrics(game, never) == 0
    cols_c = [c_never]
    cols_r = [[F(0)]]
    trace = []
    best_l, best_u = None, None
    for outer in range(max_outer):
        for _inner in range(max_inner):
            res, lam, mu = solve_master(cols_c, cols_r, alpha)
            pricer = Pricing(game, nus=nus, restrict_calendar=restrict)
            vec, n_keys, _pol = pricer.solve(lam)
            j_star = vec[0] + sum(l * r for l, r in zip(lam, vec[1:], strict=True))
            lower = j_star - alpha * sum(lam, F(0))
            best_l = lower if best_l is None else max(best_l, lower)
            trace.append({"outer": outer, "rows": 1 + len(nus), "cols": len(cols),
                          "master": float(res.fun), "lower_exact": lower,
                          "pricing_keys": n_keys, "reduced_cost": float(j_star - mu)})
            if j_star >= mu - F(1, 10**11):
                break
            pol = pricer.column()
            cols.append(pol)
            cols_c.append(vec[0])
            cols_r.append(list(vec[1:]))
        z = [max(F(0), rat(x)) for x in res.x]
        z = [w / sum(z) for w in z]
        raw_cost = sum(w * c for w, c in zip(z, cols_c, strict=True))
        robust, strategy = mixture_robust_risk(game, cols, z)
        activation = min(F(1), alpha / robust) if robust else F(1)
        upper = activation * raw_cost + (1 - activation) * c_never
        best_u = upper if best_u is None else min(best_u, upper)
        trace[-1].update({"raw_robust_risk": robust, "activation": activation, "upper": upper})
        if robust <= alpha + F(1, 10**9):
            break
        nus.append(strategy)
        for j, pol in enumerate(cols):
            cols_r[j].append(column_metrics(game, pol, strategy))
    return {"L": best_l, "U": best_u, "gap": best_u - best_l, "n_null_rows": len(nus),
            "n_columns": len(cols), "max_pricing_keys": max(t["pricing_keys"] for t in trace),
            "pricing_keys_by_rows": {r: max(t["pricing_keys"] for t in trace if t["rows"] == r)
                                     for r in sorted({t["rows"] for t in trace})},
            "trace": trace}


def main():
    out = {"purpose": "WP B1 policy-column generation with exact pricing-state counting",
           "cells": []}
    for cid, horizon, budget, delay, trans, emis, role in CELLS:
        started = time.perf_counter()
        config, model = cell(horizon, budget, delay, trans, emis)
        game = built_game(config, model)
        rec = {"id": cid, "role": role, "config": describe(config, model),
               "learner_information_sets": len(game.learner.infos),
               "learner_sequences": game.learner.count}
        # (1) state counts with IID-only pricing and with belief-only (aliased) key
        p_full = Pricing(game)
        v_m, n_full, _ = p_full.solve((F(1, 2),))
        v_t, _, _ = p_full.solve((F(1, 2),), memoise=False)
        n_alt = Pricing(game, key_mode="alt_only").solve((F(1, 2),))[1]
        rec["iid_pricing_keys"] = n_full
        rec["alt_belief_only_keys"] = n_alt
        rec["memo_equals_tree_dp"] = v_m == v_t
        if cid in LP_CHECK:
            rec["lp_check_abs_diff"] = abs(lp_pricing_check(game, F(1, 2))
                                           - float(v_m[0] + v_m[1] / 2))
        # (2) reference optimum
        ref = frontier_cut_generation_fast(config, model)
        rec["reference_fcg"] = {"U": ref["U"], "L": ref["L"], "cuts": ref["n_rows"] - 1,
                                "U0_iid_repaired": ref["U0"]}
        v_star_hi, v_star_lo = ref["U"], ref["L"]
        # (3) exact-pricing column generation with row generation
        cg = column_generation(game)
        cg["L_le_Vstar_upper"] = cg["L"] <= v_star_hi
        cg["U_ge_Vstar_lower"] = cg["U"] >= v_star_lo
        rec["column_generation"] = cg
        # (4) restricted (calendar) pricing: pseudo lower bound
        cal = column_generation(game, restrict=True)
        rec["calendar_restricted_pricing"] = {
            "pseudo_L": cal["L"], "U": cal["U"],
            "pseudo_L_exceeds_Vstar": cal["L"] > v_star_hi}
        rec["seconds"] = time.perf_counter() - started
        print(cid, rec["learner_information_sets"], n_full, n_alt,
              float(cg["L"]), float(cg["U"]), float(v_star_hi), cg["n_null_rows"],
              cg["pricing_keys_by_rows"], float(cal["L"]), round(rec["seconds"], 1), flush=True)
        out["cells"].append(rec)
    path = write_result("b1_column_generation_v1.json", out, Path(__file__))
    print("wrote", path)


if __name__ == "__main__":
    main()
