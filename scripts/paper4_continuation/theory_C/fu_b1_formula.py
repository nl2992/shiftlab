"""Follow-up 2: exact B = 1 premium formula (Theorem N1) vs certified Gamma, incl. TP2-violating cells.

Theorem N1 (doc): for B = 1 and alpha <= 1/2, with design gains computed from exact sequence costs,
  r_IID = max(0, 2 g_z1, 2 g_z0, g_both, g_pre),   r_c = max(0, 2 g_z1, g_z0, g_both, g_pre),
  Gamma = alpha (r_IID - r_c)  (maxima over query times tau).
usage: fu_b1_formula.py OUT.json SEED N [--budget S]
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F

from gamma_lib import gamma_cell, make, save_refuse_overwrite
from shiftlab.paper4.frontier_cuts import exact_costs, learner_only_game

TRANS = [F(0), F(1, 10), F(1, 4), F(2, 5), F(1, 2), F(3, 5), F(3, 4), F(9, 10), F(1)]
EMIS = [(F(1, 10), F(9, 10)), (F(1, 10), F(3, 5)), (F(2, 5), F(9, 10)), (F(1, 4), F(3, 4))]
PRIOR = [F(0), F(1, 4), F(1, 2), F(3, 4), F(1)]
COST = [F(0), F(1, 100), F(1, 10)]
ALPHA = [F(1, 20), F(1, 10)]


def seq_of(game, steps, labels):
    """Sequence id after playing `steps` [(a,q),...] with queried labels from `labels`."""
    history, outcomes, seq = (), (), 0
    for (a, q) in steps:
        t = len(history) + 1
        _p, children, choices = game.learner.infos[game.information(history, outcomes)]
        seq = children[choices.index((a, q))]
        if a:
            return seq
        history = history + ((a, q),)
        if q:
            outcomes = outcomes + ((t, labels[t]),)
    return seq


def formula(T, d, t01, t10, e0, e1, prior, c, k, alpha):
    config, model = make(T, 1, d, t01, t10, e0, e1, prior, c, k, alpha)
    game = learner_only_game(config, model)
    costs = exact_costs(game)
    idle = [(0, 0)] * T
    C0 = costs[seq_of(game, idle, {})]
    g_pre = None
    best = {"z0": None, "z1": None, "both": None}

    def upd(key, val):
        if best[key] is None or val > best[key]:
            best[key] = val

    pre = []
    for s in range(1, T + 1):  # promote at s with no earlier query: (1,0) or (1,1)
        for q in (0, 1):
            pre.append(C0 - costs[seq_of(game, [(0, 0)] * (s - 1) + [(1, q)], {})])
    for tau in range(1, T + 1):
        base = [(0, 0)] * (tau - 1) + [(0, 1)]
        for s in range(tau + 1, min(tau + d - 1, T) + 1):  # promote before release
            steps = base + [(0, 0)] * (s - tau - 1) + [(1, 0)]
            pre.append(C0 - costs[seq_of(game, steps, {tau: 0})])
        if tau + d > T:
            continue
        N = {y: costs[seq_of(game, base + [(0, 0)] * (T - tau), {tau: y})] for y in (0, 1)}
        P = {}
        for y in (0, 1):
            P[y] = min(costs[seq_of(game, base + [(0, 0)] * (s - tau - 1) + [(1, 0)], {tau: y})]
                       for s in range(tau + d, T + 1))
        upd("z0", C0 - (P[0] + N[1]))
        upd("z1", C0 - (N[0] + P[1]))
        upd("both", C0 - (P[0] + P[1]))
    g_pre = max(pre)
    cands_c = [F(0), g_pre] + [v for v in (2 * best["z1"] if best["z1"] is not None else None,
                                           best["z0"], best["both"]) if v is not None]
    r_c = max(cands_c)
    r_iid = max([r_c] + ([2 * best["z0"]] if best["z0"] is not None else []))
    return alpha * (r_iid - r_c), {"r_IID": str(r_iid), "r_c": str(r_c), "g_pre": str(g_pre),
                                    **{f"g_{kk}": str(v) for kk, v in best.items()}}


def main():
    args = sys.argv[1:]
    budget = 560.0
    if "--budget" in args:
        i = args.index("--budget")
        budget = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    out, seed, n = args[0], int(args[1]), int(args[2])
    rng = random.Random(seed)
    started = time.time()
    rows = []
    for _ in range(n):
        if time.time() - started > budget:
            break
        T, d = rng.choice([3, 4, 5, 6]), rng.choice([1, 2])
        t01, t10 = rng.choice(TRANS), rng.choice(TRANS)
        e0, e1 = rng.choice(EMIS)
        prior, c, k, alpha = rng.choice(PRIOR), rng.choice(COST), rng.choice(COST), rng.choice(ALPHA)
        r = gamma_cell(T, 1, d, t01, t10, e0, e1, prior, c, k, alpha)
        pred, parts = formula(T, d, t01, t10, e0, e1, prior, c, k, alpha)
        p1 = prior
        marg = []
        for _t in range(T):
            p1 = p1 * (1 - t10) + (1 - p1) * t01
            marg.append(e0 + (e1 - e0) * p1)
        lo, hi = F(r["Gamma_lo"]), F(r["Gamma_hi"])
        rows.append({
            "cell": r["cell"], "Gamma_lo_f": float(lo), "Gamma_hi_f": float(hi),
            "positive": lo > 0, "pred": str(pred), "pred_f": float(pred),
            "match": lo - F(1, 10**9) <= pred <= hi + F(1, 10**9),
            "tp2": t01 + t10 <= 1, "M": min(marg[: max(T - d, 1)]) >= F(1, 2), **parts,
        })
    viol = [r for r in rows if not (r["tp2"] and r["M"])]
    payload = {
        "script": "scripts/paper4_continuation/theory_C/fu_b1_formula.py", "seed": seed,
        "n_run": len(rows), "n_match": sum(r["match"] for r in rows),
        "n_positive": sum(r["positive"] for r in rows),
        "n_tp2_and_M": sum(r["tp2"] and r["M"] for r in rows),
        "n_positive_tp2_and_M": sum(r["positive"] for r in rows if r["tp2"] and r["M"]),
        "n_violating": len(viol), "n_violating_positive": sum(r["positive"] for r in viol),
        "n_tp2_violated": sum(not r["tp2"] for r in rows),
        "n_tp2_violated_positive": sum(r["positive"] for r in rows if not r["tp2"]),
        "n_M_violated_tp2_ok": sum(r["tp2"] and not r["M"] for r in rows),
        "n_M_violated_tp2_ok_positive": sum(r["positive"] for r in rows if r["tp2"] and not r["M"]),
        "seconds": time.time() - started, "rows": rows,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})
    for r in rows:
        if not r["match"]:
            print("MISMATCH", r["cell"], r["Gamma_lo_f"], r["Gamma_hi_f"], r["pred_f"])


if __name__ == "__main__":
    main()
