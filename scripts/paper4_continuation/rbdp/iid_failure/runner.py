"""Run all 7 policies on one (chain, alpha) setting. Importable; used by run_study.py and crosscheck.py."""
from __future__ import annotations

import time

from iidlib import (Chain, Post, calibrate_p1, calibrate_p2, calibrate_p3, calibrate_p4, cost, policy6, risks)

C_QUERY, K_SWITCH = 0.01, 0.0
_POST = {}


def get_post(ch):
    key = (ch.t01, ch.t10, ch.e0, ch.e1, ch.prior1, ch.T, ch.B)
    if key not in _POST:
        if len(_POST) > 6:
            _POST.clear()
        _POST[key] = Post(ch)
    return _POST[key]


def solver_policy(ch, alpha, mode):
    from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, solve

    t0 = time.perf_counter()
    r = solve(RBDPConfig(T=ch.T, B=ch.B, t01=ch.t01, t10=ch.t10, e0=ch.e0, e1=ch.e1, prior1=ch.prior1, c=ch.c,
                         k=ch.k, alpha=alpha, n_beta=201, mode=mode, lattice_exact=True, compute_lower=False))
    r["wall_s"] = time.perf_counter() - t0
    return r


def run_setting(ch: Chain, alpha: float, tag: dict):
    """Returns a list of dict rows, one per policy."""
    post = get_post(ch)
    C0 = ch.C0()
    rows = []

    def add(name, param, ri, rc, cst, extra=None):
        d = dict(tag, policy=name, alpha=alpha, T=ch.T, B=ch.B, calib=param, risk_iid=ri, risk_causal=rc,
                 ratio_causal_over_alpha=rc / alpha, ratio_iid_over_alpha=ri / alpha, cost=cst, C0=C0,
                 cost_saving_vs_never=C0 - cst, violates=bool(rc > alpha + 1e-9))
        if extra:
            d.update(extra)
        rows.append(d)

    for cal in (calibrate_p1, calibrate_p2, calibrate_p3, calibrate_p4):
        pol = cal(ch, alpha)
        ri, rc = risks(pol, ch)
        add(pol.name, pol.param(), ri, rc, cost(pol, ch, post))
    g = policy6(ch, post, alpha)
    add("P6_eprocess_gate", {"th": g["th"], "activation": g["activation"]}, g["risk_iid"], g["risk_causal"], g["cost"],
        {"ville_bound": g["ville_bound"], "causal_risk_kind": "exact (Lemma A on gate policy, times activation)"})
    s5 = solver_policy(ch, alpha, "iid")
    add("P5_iid_optimal_pomdp", {"mode": "iid"}, s5["risk_iid"], s5["risk_causal"], s5["U"],
        {"causal_risk_kind": "solver evaluator; upper bound when the plan randomises at a node", "solver_C0": s5["C0"],
         "n_pre_nodes": s5["n_pre_nodes"], "wall_s": s5["wall_s"]})
    s7 = solver_policy(ch, alpha, "causal")
    add("P7_rbdp_causal", {"mode": "causal"}, s7["risk_iid"], s7["risk_causal"], s7["U"],
        {"causal_risk_kind": "solver evaluator; upper bound when the plan randomises at a node", "solver_C0": s7["C0"],
         "n_pre_nodes": s7["n_pre_nodes"], "wall_s": s7["wall_s"]})
    return rows
