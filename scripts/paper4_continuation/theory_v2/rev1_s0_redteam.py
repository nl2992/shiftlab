"""Reviewer 1 red team for Theorem S0 (MULTILABEL_ZERO_PREMIUM.md section 2): static, c = 0.

Per static cell (t01 = t10 = 0, c = 0), all in exact rationals:
 (H) exact lower hull of {(R_IID, C)} over the FULL pure-plan class, by parametric search with the general
     exact Lagrangian DP wpB_lib.solve (no calendar restriction); exact breakpoints lambda_i.
 (CAL) at every breakpoint and every edge midpoint lambda: J_general(lambda) == J_greedy(lambda), where
     J_greedy is wpB_static.static_solve(greedy=True) (queries forced at 1..min(B,T) before promotion).
 (MON) the greedy DP plan is z-monotone under both tie rules (stop iff D < 0, stop iff D <= 0).
 (REC) an independent implementation (this file) of the closed recursions G_t, D_t of Lemmas G / D equals the
     DP stop-minus-continue advantage Dtab at every reachable greedy state; {s : D_t <= 0} and {s : D_t < 0}
     are up-sets in s at each t; induction claims 1-4 hold on a rational (x, y) grid.
 (GAM) certified Gamma = V*_causal - V*_IID by theory_C gamma_cell, at alpha = every interior hull-vertex
     risk (hull breakpoints in alpha), midpoints between them, and fixed alphas incl. > 1/2.
     force_fcg=True for T <= FCG_TMAX so V*_causal is certified by FCG rather than by IID-optimum safety.
usage: rev1_s0_redteam.py OUT.json WORKER NWORKERS [SEED NRANDOM]
  with SEED NRANDOM: instead of the fixed adversarial list, NRANDOM seeded random mid-size cells chosen to give
  nontrivial hulls (T 5-7, B 3-T, d 1-2, moderate emissions), split across workers.
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from functools import lru_cache
from itertools import product

sys.set_int_max_str_digits(0)

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpB_lib import Model, solve  # noqa: E402
from wpB_static import rc_static, static_solve, z_monotone_static  # noqa: E402

FCG_TMAX = 6
GENERAL_TMAX = 7  # general (non-calendar) exact DP is used for the hull / CAL when T <= this


def cells():
    """Deterministic adversarial cell list: (T, B, d, e0, e1, prior, k, tag)."""
    out = []
    E = {
        "mid": (F(1, 10), F(9, 10)),
        "near_half": (F(49, 100), F(51, 100)),
        "near_half2": (F(499, 1000), F(501, 1000)),
        "near_edges": (F(1, 1000), F(999, 1000)),
        "asym_lo": (F(1, 1000), F(51, 100)),
        "asym_hi": (F(49, 100), F(999, 1000)),
        "weak": (F(2, 5), F(3, 5)),
    }
    P = [F(1, 1000), F(1, 100), F(1, 2), F(99, 100), F(999, 1000), F(1, 3)]
    K = [F(0), F(1, 100), F(1, 2), F(3), F(10)]
    # (a) large delay relative to T
    for T in (2, 3, 4, 5, 6, 7):
        for d in sorted({T - 1, T, T + 2} - {0}):
            for i, (en, e) in enumerate(E.items()):
                if i % 2 == T % 2:
                    out.append((T, T, d, *e, P[(T + d + i) % len(P)], K[(T + i) % len(K)], f"delay:{en}"))
    # (b) budget near / above horizon
    for T in (3, 4, 5, 6, 7, 8):
        for B in sorted({T - 1, T, T + 3}):
            for i, (en, e) in enumerate(E.items()):
                if (i + B) % 3 == 0:
                    out.append((T, B, 1 + (i % 2), *e, P[(B + i) % len(P)], K[(B + 2 * i) % len(K)], f"budget:{en}"))
    # (c) large switch cost
    for T in (3, 5, 7):
        for k in (F(1), F(3), F(10)):
            for en in ("mid", "near_edges", "asym_hi", "weak"):
                e = E[en]
                out.append((T, min(T, 4), 1, *e, F(1, 2) if en != "weak" else F(99, 100), k, f"k:{en}"))
    # (d) priors near 0/1 with every emission type
    for p in (F(1, 1000), F(1, 100), F(99, 100), F(999, 1000)):
        for en, e in E.items():
            for T, B, d in ((4, 3, 1), (6, 4, 2)):
                out.append((T, B, d, *e, p, F(1, 10), f"prior:{en}"))
    # (e) small edge cases
    for T, B, d in ((1, 1, 1), (1, 3, 1), (2, 1, 1), (2, 2, 1), (2, 2, 3), (3, 1, 2)):
        for en in ("mid", "near_half", "near_edges"):
            out.append((T, B, d, *E[en], F(1, 2), F(1, 10), f"edge:{en}"))
    # (f) larger cells, certified Gamma only (general DP skipped)
    for T, B, d in ((8, 6, 1), (8, 8, 2), (8, 5, 3), (9, 6, 1), (9, 4, 2)):
        for en in ("mid", "near_edges", "asym_lo", "weak"):
            out.append((T, B, d, *E[en], F(1, 3), F(1, 20), f"large:{en}"))
    # (g) seeded random mid-size cells (nontrivial hulls)
    import random

    rng = random.Random(20261110)
    ev = list(E.values()) + [(F(1, 5), F(7, 10)), (F(1, 20), F(3, 5)), (F(3, 10), F(19, 20))]
    for _ in range(80):
        T = rng.randint(4, 7)
        B = rng.randint(2, T + 1)
        d = rng.randint(1, 3)
        e = rng.choice(ev)
        p = rng.choice(P + [F(1, 5), F(4, 5), F(1, 20)])
        k = rng.choice([F(0), F(1, 100), F(1, 20), F(1, 5), F(1), F(3)])
        out.append((T, B, d, *e, p, k, "random"))
    # GameConfig requires B <= T; B > T is identical to B = T (at most T queries), so clamp and dedupe.
    seen, res = set(), []
    for c in out:
        c = (c[0], min(c[1], c[0]), *c[2:])
        if c[:7] not in seen:
            seen.add(c[:7])
            res.append(c)
    return res


# ---------------- independent closed-form recursions (Lemmas G, D) ----------------
def recursions(T, B, d, e0, e1, k):
    n = min(B, T)

    def released_at(t):  # a label (queried at t - d) is released at time t
        return 1 <= t - d <= n

    def branches(t):  # (L0, LN, L1) weights for the transition t -> t+1
        if released_at(t + 1):
            return ((1 - e0, F(1, 2), 1 - e1), (e0, F(1, 2), e1))
        return ((F(1), F(1), F(1)),)

    @lru_cache(None)
    def G(t, x):
        lin = x * (1 - 2 * e0) + (1 - 2 * e1)
        if t == T:
            return lin + k * x + k
        tot = lin
        for L0, _LN, L1 in branches(t):
            xl = x * L0 / L1
            tot += L1 * min(max(G(t + 1, xl), F(0)), 2 * k * (1 + xl))
        return tot

    @lru_cache(None)
    def D(t, x, y):
        if t == T:
            return y + G(T, x)
        tot = G(t, x)
        for L0, LN, L1 in branches(t):
            xl, yl = x * L0 / L1, y * LN / L1
            tot += L1 * (max(D(t + 1, xl, yl), F(0)) - max(G(t + 1, xl), F(0)))
        return tot

    return G, D, n


def m_at(t, d, n):
    return max(0, min(n, t - d))


def xy(m, s, e0, e1, p, lam):
    a1 = p * e1**s * (1 - e1) ** (m - s)
    return (1 - p) * e0**s * (1 - e0) ** (m - s) / a1, lam / 2**m / a1


def threshold_event(T, d, n, e0, e1, p, lam, D, strict):
    """Promotion indicator over z in {0,1}^n of 'promote at first t with D_t <(=) 0'."""
    stop = {}
    for t in range(1, T + 1):
        m = m_at(t, d, n)
        for s in range(m + 1):
            v = D(t, *xy(m, s, e0, e1, p, lam))
            stop[(t, s)] = v < 0 if strict else v <= 0
    g = {}
    for z in product((0, 1), repeat=n):
        g[z] = int(any(stop[(t, sum(z[: m_at(t, d, n)]))] for t in range(1, T + 1)))
    return stop, g


def upsets(stop, T, d, n):
    for t in range(1, T + 1):
        m = m_at(t, d, n)
        for s in range(m):
            if stop[(t, s)] and not stop[(t, s + 1)]:
                return False
    return True


def monotone(g, n):
    for z, v in g.items():
        for i in range(n):
            if z[i] == 0 and v > g[z[:i] + (1,) + z[i + 1:]]:
                return False
    return True


def grid_claims(T, G, D):
    xs = [F(1, 1000), F(1, 50), F(1, 7), F(1, 2), F(1), F(3, 2), F(4), F(19), F(200), F(5000)]
    ys = [F(0), F(1, 100), F(1, 5), F(1), F(3), F(40), F(1000)]
    bad = []
    for t in range(1, T + 1):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                dv, gv = D(t, x, y), G(t, x)
                if dv < gv:
                    bad.append(("D<G", t, str(x), str(y)))
                if i:
                    xp = xs[i - 1]
                    if dv < D(t, xp, y):
                        bad.append(("D dec x", t, str(x), str(y)))
                    if dv - gv < D(t, xp, y) - G(t, xp):
                        bad.append(("D-G dec x", t, str(x), str(y)))
                    if gv < G(t, xp):
                        bad.append(("G dec x", t, str(x)))
                if j and dv < D(t, x, ys[j - 1]):
                    bad.append(("D dec y", t, str(x), str(y)))
    return bad


# ---------------- exact hull over the full pure-plan class ----------------
def exact_hull(T, B, d, e0, e1, p, k):
    mdl = Model(T, B, d, 0, 0, e0, e1, p, 0, k, exact=True)

    def pt(lam, tie):
        J, _plan, info = solve(mdl, lam, tie=tie)
        R = info["R"]
        return J, R, J - lam * R

    # leftmost vertex: lambda -> 0+ (wpB_lib needs lam > 0 to report R); vertices with a breakpoint below
    # 1e-12 would be missed, which only shrinks the alpha set, not the validity of any check.
    lam0 = F(1, 10**12)
    J0, R0, C0 = pt(lam0, "minR")
    Cmax_bound = T * (1 + 2 * k) + 1
    lamM = Cmax_bound * 2 ** min(B, T) * 4
    JM, RM, CM = pt(lamM, "minR")
    verts = {(R0, C0), (RM, CM)}
    bps = []

    def rec(a, b):
        if a[0] <= b[0]:
            return
        lam = (b[1] - a[1]) / (a[0] - b[0])
        J, R, C = pt(lam, "minR")
        if J < a[1] + lam * a[0]:
            verts.add((R, C))
            rec(a, (R, C))
            rec((R, C), b)
        else:
            bps.append(lam)

    rec((R0, C0), (RM, CM))
    return sorted(verts, key=lambda v: -v[0]), sorted(bps), lamM, mdl


def run_cell(cell):
    T, B, d, e0, e1, p, k, tag = cell
    rec = {"cell": {"T": T, "B": B, "d": d, "e0": str(e0), "e1": str(e1), "prior": str(p), "k": str(k), "tag": tag}}
    G, D, n = recursions(T, B, d, e0, e1, k)
    rec["grid_claim_violations"] = grid_claims(T, G, D)[:5]
    lams = []
    if T <= GENERAL_TMAX:
        verts, bps, lamM, mdl = exact_hull(T, B, d, e0, e1, p, k)
        rec["hull_vertices_R"] = [str(v[0]) for v in verts]
        rec["breakpoints"] = [str(b) for b in bps]
        edges = [F(0)] + bps + [lamM]
        lams = bps + [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
        vR = [v[0] for v in verts]
    else:
        mdl = None
        lams = [F(1, 10), F(1, 2), F(2), F(10)]
        vR = []
    checks = []
    for lam in lams:
        ch = {"lam": str(lam)}
        Jg = {}
        for tie, strict in (("cont", True), ("promote", False)):
            J, plan, Dtab = static_solve(T, B, d, e0, e1, 0, k, 1 - p, lam, p, greedy=True, tie=tie, exact=True)
            Jg[tie] = J
            ch[f"zmono_{tie}"] = z_monotone_static(plan, T, B, d)[0]
            # recursion vs DP at every reachable greedy state
            err = F(0)
            for (t, _pend, _b, m, s), v in Dtab.items():
                if v is None:
                    continue
                err = max(err, abs(v - D(t, *xy(m, s, e0, e1, p, lam))))
            ch["rec_vs_dp_maxabs"] = str(err)
            stop, g = threshold_event(T, d, n, e0, e1, p, lam, D, strict)
            ch[f"upset_{tie}"] = upsets(stop, T, d, n)
            ch[f"thr_event_monotone_{tie}"] = monotone(g, n)
            ch[f"thr_R_eq_dp_R_{tie}"] = sum(F(v) for v in g.values()) / 2**n == rc_static(plan, T, B, d, e0, e1, 1 - p, p)
        if mdl is not None:
            Jgen, _, info = solve(mdl, lam, tie="minR")
            ch["CAL_J_general_eq_greedy"] = Jgen == Jg["cont"]
            ch["general_minR"] = str(info["R"])
        checks.append(ch)
    rec["lambda_checks"] = checks
    # certified Gamma
    alphas = set()
    interior = [r for r in vR if 0 < r < 1]
    alphas.update(interior[:4])
    alphas.update((vR[i] + vR[i + 1]) / 2 for i in range(min(3, len(vR) - 1)))
    alphas.update({F(1, 20), F(1, 2), F(3, 4), F(99, 100)})
    gam = []
    for a in sorted(alphas):
        if not (0 <= a <= 1):
            continue
        o = gamma_cell(T, B, d, 0, 0, e0, e1, prior=p, c=0, k=k, alpha=a, force_fcg=T <= FCG_TMAX)
        gam.append({"alpha": str(a), "Gamma_lo_f": o["Gamma_lo_f"], "Gamma_hi_f": o["Gamma_hi_f"],
                    "Gamma_hi_le_1e-9_exact": F(o["Gamma_hi"]) <= F(1, 10**9), "src": o["V_causal_source"],
                    "pos": o["Gamma_positive_certified"]})
    rec["gamma"] = gam
    return rec


def main():
    out, w, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    t0 = time.time()
    if len(sys.argv) > 5:
        import random

        rng = random.Random(int(sys.argv[4]))
        em = [(F(1, 10), F(9, 10)), (F(1, 5), F(7, 10)), (F(1, 20), F(3, 5)), (F(3, 10), F(19, 20)),
              (F(2, 5), F(3, 5)), (F(1, 100), F(4, 5)), (F(1, 1000), F(999, 1000))]
        allc = []
        for _ in range(int(sys.argv[5])):
            T = rng.randint(5, 7)
            allc.append((T, rng.randint(3, T), rng.randint(1, 2), *rng.choice(em),
                         rng.choice([F(1, 10), F(1, 4), F(1, 2), F(3, 4), F(9, 10)]),
                         rng.choice([F(0), F(1, 100), F(1, 10), F(1, 2)]), f"random2:{sys.argv[4]}"))
    else:
        allc = cells()
    mine = [c for i, c in enumerate(allc) if i % nw == w]
    recs = []
    for c in mine:
        t = time.time()
        r = run_cell(c)
        r["seconds"] = time.time() - t
        recs.append(r)
        print(c[-1], c[:3], f"{r['seconds']:.1f}s", flush=True)
    fails = []
    for r in recs:
        if r["grid_claim_violations"]:
            fails.append((r["cell"], "grid"))
        for ch in r["lambda_checks"]:
            for key, v in ch.items():
                if isinstance(v, bool) and not v:
                    fails.append((r["cell"], ch["lam"], key))
            if ch["rec_vs_dp_maxabs"] != "0":
                fails.append((r["cell"], ch["lam"], "rec_vs_dp", ch["rec_vs_dp_maxabs"]))
        for g in r["gamma"]:
            if g["pos"] or not g["Gamma_hi_le_1e-9_exact"]:
                fails.append((r["cell"], g["alpha"], "GAMMA_NOT_ZERO", g["Gamma_lo_f"], g["Gamma_hi_f"]))
    payload = {
        "script": "scripts/paper4_continuation/theory_v2/rev1_s0_redteam.py",
        "worker": w, "n_workers": nw, "n_cells_total_list": len(allc), "n_cells": len(recs),
        "n_lambda_checks": sum(len(r["lambda_checks"]) for r in recs),
        "n_gamma_certs": sum(len(r["gamma"]) for r in recs),
        "max_Gamma_hi": max((g["Gamma_hi_f"] for r in recs for g in r["gamma"]), default=None),
        "n_failures": len(fails), "failures": fails[:50], "seconds": time.time() - t0, "records": recs,
    }
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "records"})


if __name__ == "__main__":
    main()
