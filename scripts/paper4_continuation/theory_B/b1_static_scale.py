"""B1 (static / exchangeable alternative): tree-free certified pipeline and a Gamma=0 screen.

Pipeline (never builds the learner tree):
  1. Dantzig-Wolfe column generation over deterministic learner policies with the IID row,
     priced EXACTLY over the unrestricted policy class by the key-merged DP of b1_pricing
     (keys = t, budget, alt belief incl. pending, iid/alt likelihood ratio).  For a static
     alternative these keys are count statistics.  L = J*(lam) - alpha*lam <= V*_IID <= V*.
  2. Exact full-causal-null verification of the returned root mixture on the product
     (key, generated pending outcomes, consistent-column set); endpoint best response.
  3. If robust risk <= alpha: U = mixture cost, else root-repair with never-promote.
  Report L, U, number of pricing keys, verifier states, and the learner-tree size (counted
  combinatorially, not built).

Usage: uv run --no-sync python scripts/paper4_continuation/theory_B/b1_static_scale.py
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F
from functools import cache
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).parent))
from b1_pricing import Pricing  # noqa: E402
from b_common import HALF, cell, describe, initial_belief, release, write_result  # noqa: E402

from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame  # noqa: E402


def count_learner_infos(T, B, d):
    """Pre-promotion learner information sets (decision nodes) of the public tree."""

    @cache
    def go(t, rem, recent):  # recent: query bits of the last d-1 events (pending at t)
        # number of information sets at times >= t, per unit of history multiplicity
        if t > T:
            return 0
        total = 1  # this decision node
        if t == T:
            return total
        for q in ((0, 1) if rem else (0,)):
            nxt = (recent + (q,))
            released = nxt[0] if len(nxt) >= d else 0
            nxt = nxt[1:] if len(nxt) >= d else nxt
            total += (2 if released else 1) * go(t + 1, rem - q, nxt)
        return total

    return go(1, B, ())


class TreeFreeGame(FirstPromotionDecomposedGame):
    """Uses only the exact belief / continuation machinery; no learner tree is built."""


def iid_column_generation(game, max_iter=80):
    alpha = game.config.alpha
    cols, cc, cr = [], [], []
    for lam in (F(10**6), F(0)):
        p = Pricing(game)
        vec, nk, pol = p.solve((lam,))
        cols.append(dict(pol))
        cc.append(vec[0])
        cr.append(vec[1])
    max_keys = nk
    lower = None
    for _ in range(max_iter):
        res = linprog([float(c) for c in cc], A_ub=[[float(r) for r in cr]], b_ub=[float(alpha)],
                      A_eq=np.ones((1, len(cc))), b_eq=[1.0], bounds=[(0, None)] * len(cc),
                      method="highs")
        lam = max(F(0), -F(float(res.ineqlin.marginals[0])).limit_denominator(10**9))
        mu = F(float(res.eqlin.marginals[0])).limit_denominator(10**9)
        p = Pricing(game)
        vec, nk, pol = p.solve((lam,))
        max_keys = max(max_keys, nk)
        j = vec[0] + lam * vec[1]
        lb = j - alpha * lam
        lower = lb if lower is None else max(lower, lb)
        if j >= mu - F(1, 10**11):
            break
        cols.append(dict(pol))
        cc.append(vec[0])
        cr.append(vec[1])
    z = [max(F(0), F(float(x)).limit_denominator(10**9)) for x in res.x]
    z = [w / sum(z) for w in z]
    return cols, cc, cr, z, lower, max_keys


def keyed_robust_risk(game, cols, z):
    """Exact sup over causal nulls of the root mixture of key-measurable columns.

    State: (t, rem, alt belief, rho, generated pending outcomes, alive columns).  The learner
    key depends only on released labels; the null sees pending outcomes."""
    cfg = game.config
    memo = {}

    def visit(t, rem, belief, rho, pending, alive):
        if t > cfg.horizon or not alive:
            return F(0)
        k = (t, rem, belief, rho, pending, alive)
        if k in memo:
            return memo[k]
        key = (t, rem, belief, rho, ())
        groups = {}
        for j in alive:
            groups.setdefault(cols[j][key], []).append(j)
        val = F(0)
        for (a, q), members in groups.items():
            fs = frozenset(members)
            if a:
                val += sum(z[j] for j in members)
                continue
            if t == cfg.horizon:
                continue
            nb = game._transition_belief(t, belief, q)
            outs = []
            for y in ((0, 1) if q else (None,)):
                pend = pending + (((t, y),) if q else ())
                rel = release(game, t + 1, nb)
                if rel is None:
                    outs.append(visit(t + 1, rem - q, nb, rho, pend, fs))
                    continue
                d, branches = rel
                s = d - cfg.delay
                yy = dict(pend)[s]
                pend2 = tuple(i for i in pend if i[0] != s)
                (m_alt, bel), = [(m, b) for y2, m, b in branches if y2 == yy]
                outs.append(visit(t + 1, rem - q, bel, rho * HALF / m_alt, pend2, fs))
            if q:
                v0, v1 = outs
                val += max(v0, (v0 + v1) / 2)
            else:
                val += outs[0]
        memo[k] = val
        return val

    r = visit(1, cfg.budget, initial_belief(game), F(1), (), frozenset(range(len(cols))))
    return r, len(memo)


def pipeline(config, model):
    t0 = time.perf_counter()
    game = TreeFreeGame(config, model)
    cols, cc, cr, z, lower, keys = iid_column_generation(game)
    raw_cost = sum(w * c for w, c in zip(z, cc, strict=True))
    iid_risk = sum(w * r for w, r in zip(z, cr, strict=True))
    robust, vstates = keyed_robust_risk(game, cols, z)
    act = min(F(1), config.alpha / robust) if robust else F(1)
    upper = act * raw_cost + (1 - act) * cc[0]
    return {"L": lower, "U": upper, "gap": upper - lower, "iid_risk_of_mixture": iid_risk,
            "robust_risk_of_mixture": robust, "activation": act,
            "certified_optimal": upper - lower <= F(1, 10**7),
            "pricing_keys": keys, "verifier_states": vstates,
            "learner_infosets_counted": count_learner_infos(config.horizon, config.budget,
                                                            config.delay),
            "seconds": time.perf_counter() - t0}


def main():
    out = {"purpose": "B1 static-alternative tree-free certified pipeline + Gamma=0 screen",
           "scale": [], "screen": []}
    # scale demonstration (static alternative)
    for T, B, d in ((8, 3, 1), (10, 4, 2), (14, 5, 2), (18, 6, 2), (24, 6, 1)):
        config, model = cell(T, B, d, F(0), (F(1, 4), F(3, 4)))
        r = pipeline(config, model)
        r["config"] = describe(config, model)
        out["scale"].append(r)
        print("scale", T, B, d, float(r["L"]), float(r["U"]), r["pricing_keys"],
              r["verifier_states"], r["learner_infosets_counted"], round(r["seconds"], 1),
              flush=True)
        if r["seconds"] > 240:
            break
    # Gamma screen: random static cells, IID optimum robust-safe?
    rng = random.Random(20261110)
    for i in range(40):
        T = rng.randint(4, 8)
        B = rng.randint(1, min(4, T))
        d = rng.randint(1, 3)
        e0 = F(rng.randint(1, 9), 20)
        e1 = F(rng.randint(11, 19), 20)
        alpha = F(rng.choice((1, 2, 5)), 20)
        config, model = cell(T, B, d, F(0), (e0, e1), alpha=alpha)
        r = pipeline(config, model)
        r["config"] = describe(config, model)
        out["screen"].append(r)
        print("screen", i, T, B, d, e0, e1, alpha, float(r["gap"]), r["robust_risk_of_mixture"],
              r["iid_risk_of_mixture"], flush=True)
    out["screen_summary"] = {
        "cells": len(out["screen"]),
        "certified_optimal": sum(r["certified_optimal"] for r in out["screen"]),
        "max_gap": max(r["gap"] for r in out["screen"])}
    write_result("b1_static_scale_v1.json", out, Path(__file__))


if __name__ == "__main__":
    main()
