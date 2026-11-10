"""Exact-certified causal-safety premium Gamma = V*_causal - V*_IID on small cells.

V*_IID: LP with the single IID(1/2) risk row (FCG iteration 0).  Certified interval
[L_IID, U_IID]: L_IID = exact rationalised dual bound, U_IID = exact cost of the
recovered LP policy root-mixed with never-promote to exact IID risk <= alpha.
V*_causal: if the (repaired) IID optimum is causal-safe, U_causal <= U_IID and FCG is
not needed; otherwise FCG-fast gives exact [L, U].
Gamma in [L_causal - U_IID, U_causal - L_IID].
"""

from __future__ import annotations

import json
import os
import sys
from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.paper4.frontier_cuts import (
    _iid_risk,
    exact_costs,
    exact_dual_lower_bound_multi,
    mix_root_never_promote,
    risk_row_for_null,
)
from shiftlab.paper4.frontier_cuts_fast import (
    FastGame,
    float_risk_row,
    frontier_cut_generation_fast,
)


def make(T, B, d, t01, t10, e0, e1, prior=F(1, 2), c=F(1, 100), k=F(1, 10), alpha=F(1, 10)):
    config = GameConfig(
        horizon=T,
        budget=B,
        delay=d,
        alpha=F(alpha),
        query_cost=F(c),
        switch_cost=F(k),
        max_nodes=400_000,
    )
    model = RegimeModel(
        transition01=F(t01),
        transition10=F(t10),
        emission0=F(e0),
        emission1=F(e1),
        prior1=F(prior),
    )
    return config, model


def iid_solve(config, model):
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    n = game.learner.count
    flow, rhs = game.learner.matrix()
    obj = np.zeros(n)
    for key, value in game.cost.items():
        obj[key] = value
    row = float_risk_row(game, {}, n)
    res = linprog(
        obj,
        A_ub=row,
        b_ub=[float(config.alpha)],
        A_eq=flow,
        b_eq=rhs,
        bounds=[(0, None)] * n,
        method="highs",
        options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10},
    )
    if not res.success:
        raise RuntimeError(res.message)
    costs = exact_costs(game)
    dual_ub = [F(float(v)).limit_denominator(10**9) for v in res.ineqlin.marginals]
    dual_eq = [F(float(v)).limit_denominator(10**9) for v in res.eqlin.marginals]
    exact_row = risk_row_for_null(game, {})
    lower, *_ = exact_dual_lower_bound_multi(game, costs, [exact_row], flow, rhs, dual_ub, dual_eq)
    policy, _ = game.recover(res.x)
    r_iid = _iid_risk(game, policy)
    r_causal = game.null_risk(policy)
    act = min(F(1), config.alpha / r_iid) if r_iid else F(1)
    if act < 1:
        repaired, _safe = mix_root_never_promote(game, policy, act)
    else:
        repaired = policy
    upper = sum(game.expected_metrics(repaired)[:3])
    return {
        "game": game,
        "policy": policy,
        "lp": float(res.fun),
        "lambda_float": -float(res.ineqlin.marginals[0]),
        "L_IID": lower,
        "U_IID": upper,
        "R_iid_raw": r_iid,
        "R_causal_raw": r_causal,
        "R_causal_repaired": act * r_causal,
        "activation_iid": act,
    }


def gamma_cell(
    T,
    B,
    d,
    t01,
    t10,
    e0,
    e1,
    prior=F(1, 2),
    c=F(1, 100),
    k=F(1, 10),
    alpha=F(1, 10),
    force_fcg=False,
):
    config, model = make(T, B, d, t01, t10, e0, e1, prior, c, k, alpha)
    iid = iid_solve(config, model)
    out = {
        "cell": {
            "T": T,
            "B": B,
            "d": d,
            "t01": str(F(t01)),
            "t10": str(F(t10)),
            "e0": str(F(e0)),
            "e1": str(F(e1)),
            "prior": str(F(prior)),
            "c": str(F(c)),
            "k": str(F(k)),
            "alpha": str(F(alpha)),
        },
        "V_IID_lp": iid["lp"],
        "lambda_float": iid["lambda_float"],
        "L_IID": str(iid["L_IID"]),
        "U_IID": str(iid["U_IID"]),
        "R_causal_iid_opt_raw": str(iid["R_causal_raw"]),
        "R_iid_iid_opt_raw": str(iid["R_iid_raw"]),
        "iid_opt_causal_safe": iid["R_causal_repaired"] <= config.alpha,
    }
    if out["iid_opt_causal_safe"] and not force_fcg:
        lc, uc = iid["L_IID"], iid["U_IID"]
        out["V_causal_source"] = "IID optimum causal-safe"
    else:
        fcg = frontier_cut_generation_fast(config, model)
        lc, uc = fcg["L"], fcg["U"]
        out["V_causal_source"] = f"FCG-fast ({fcg['n_rows']} rows)"
    out["L_causal"], out["U_causal"] = str(lc), str(uc)
    g_lo = lc - iid["U_IID"]
    g_hi = uc - iid["L_IID"]
    out["Gamma_lo"], out["Gamma_hi"] = str(g_lo), str(g_hi)
    out["Gamma_lo_f"], out["Gamma_hi_f"] = float(g_lo), float(g_hi)
    out["Gamma_positive_certified"] = g_lo > 0
    return out


def save_refuse_overwrite(path, payload):
    if os.path.exists(path):
        print(f"refusing to overwrite {path}", file=sys.stderr)
        sys.exit(2)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, default=str)
    print("wrote", path)
