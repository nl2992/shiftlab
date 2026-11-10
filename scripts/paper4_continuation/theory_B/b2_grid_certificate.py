"""B2: tree-free certificate L <= V* <= U from belief-space grids (delay d = 1 only).

L (float64): Lagrangian bound of the IID relaxation with a Lovejoy-style grid LOWER bound
   on the pricing POMDP.  Hidden modes {alt s=0, alt s=1, IID}; at d=1 the decision-time
   belief lives on the 2-simplex.  The min-cost value is concave in the belief, so linear
   interpolation on a Freudenthal (Kuhn) triangulation of grid values under-estimates it; by
   monotonicity of the Bellman backup the grid values are lower bounds by induction.  The
   promotion continuation (alternative-only delayed-HMM DP) is lower-bounded the same way on a
   1-D grid in pi = P(s_t = 1).  L(lam) = J_low(root; lam) - alpha*lam <= V*_IID <= V*.
U (exact rational): a finite-state controller whose memory is (t, budget, snapped grid point),
   acting greedily w.r.t. the grid values; post-promotion a snapped 1-D controller.  Its exact
   alternative cost and exact full-causal-null risk are computed on the product
   (memory x hidden regime) / (memory) with endpoint null maximisation, then root-repaired
   with never-promote.  No learner public-history tree is built.

Usage: uv run --no-sync python scripts/paper4_continuation/theory_B/b2_grid_certificate.py
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from b1_static_scale import count_learner_infos  # noqa: E402
from b_common import write_result  # noqa: E402

E20 = (F(1, 20), F(19, 20))
QC, SW = F(1, 100), F(1, 10)


class Model:
    def __init__(self, T, B, trans, emis, alpha=F(1, 10)):
        self.T, self.B, self.alpha = T, B, alpha
        self.a01 = self.a10 = trans
        self.e = emis
        p1 = F(1, 2) * (1 - self.a10) + F(1, 2) * self.a01  # prior propagated one step
        self.pi1 = p1
        self.f = {k: float(v) for k, v in dict(a01=self.a01, a10=self.a10, e0=emis[0],
                                                 e1=emis[1]).items()}

    # float belief maps (used for grid backups and controller memory updates)
    def prop(self, pi):
        return pi * (1 - self.f["a10"]) + (1 - pi) * self.f["a01"]

    def py1(self, pi):
        return self.f["e0"] + (self.f["e1"] - self.f["e0"]) * pi

    def post(self, pi, y):
        l1 = self.f["e1"] if y else 1 - self.f["e1"]
        l0 = self.f["e0"] if y else 1 - self.f["e0"]
        num = pi * l1
        den = num + (1 - pi) * l0
        return self.prop(np.where(den > 0, num / np.where(den > 0, den, 1), 0.0))


# ------------------------------------------------------------------ grids
class Grid2:
    """Points (i, j), i + j <= N, meaning w0 = i/N, w1 = j/N, wI = 1 - (i+j)/N."""

    def __init__(self, N):
        self.N = N
        pts = [(i, j) for i in range(N + 1) for j in range(N + 1 - i)]
        self.idx = {p: k for k, p in enumerate(pts)}
        self.w0 = np.array([p[0] / N for p in pts])
        self.w1 = np.array([p[1] / N for p in pts])
        self.lut = np.full((N + 2, N + 2), -1)
        for (i, j), k in self.idx.items():
            self.lut[i, j] = k

    def bary(self, w0, w1):
        """Vertices (3 index arrays) and weights (3 arrays) of the containing triangle."""
        N = self.N
        x = np.clip(np.asarray(w0, float) * N, 0, N)
        y = np.clip(np.asarray(w1, float) * N, 0, N)
        s = x + y
        scale = np.where(s > N, N / np.where(s > 0, s, 1), 1.0)
        x, y = x * scale, y * scale
        i = np.minimum(np.floor(x), N - 1).astype(int)
        j = np.minimum(np.floor(y), N - 1).astype(int)
        over = i + j > N - 1
        dec_i = over & (i > 0)
        i = np.where(dec_i, i - 1, i)
        j = np.where(over & ~dec_i, j - 1, j)
        fx, fy = x - i, y - j
        upper = fx + fy > 1 + 1e-12
        iu, ju = np.minimum(i + 1, N), np.minimum(j + 1, N)
        v = [np.where(upper, self.lut[iu, j], self.lut[i, j]),
             np.where(upper, self.lut[i, ju], self.lut[iu, j]),
             np.where(upper, self.lut[np.minimum(i + 1, N), np.minimum(j + 1, N)], self.lut[i, ju])]
        wts = [np.where(upper, 1 - fy, 1 - fx - fy), np.where(upper, 1 - fx, fx),
               np.where(upper, fx + fy - 1, fy)]
        wts = [np.clip(w, 0, None) for w in wts]
        tot = sum(wts)
        wts = [w / tot for w in wts]
        assert all((vv >= 0).all() for vv in v), "triangulation lookup failed"
        return v, wts

    def interp(self, vals, w0, w1):
        v, wts = self.bary(w0, w1)
        return sum(wt * vals[vv] for vv, wt in zip(v, wts, strict=True))

    def snap(self, w0, w1):
        v, wts = self.bary(np.atleast_1d(w0), np.atleast_1d(w1))
        k = np.argmax(np.stack(wts), axis=0)
        return np.stack(v)[k, np.arange(len(k))]


def interp1(vals, pi, Nc):
    x = np.clip(pi * Nc, 0, Nc)
    i = np.minimum(np.floor(x).astype(int), Nc - 1)
    f = x - i
    return (1 - f) * vals[i] + f * vals[i + 1]


# ------------------------------------------------------------------ lower bound
def continuation_lb(m: Model, Nc):
    """Vc[t][old][rem] arrays over pi grid; returns also promote(t, rem, q) arrays and policy."""
    pis = np.linspace(0, 1, Nc + 1)
    c, k = float(QC), float(SW)
    Vc, pol = {}, {}
    for t in range(m.T, 0, -1):
        for old in (0, 1):
            for rem in range(m.B + 1):
                best, arg = None, None
                for a in (0, 1):
                    for q in ((0, 1) if rem else (0,)):
                        py = m.py1(pis)
                        val = (py if a == 0 else 1 - py) + c * q + k * (a != old)
                        if t < m.T:
                            if q:
                                for y in (0, 1):
                                    pr = py if y else 1 - py
                                    val = val + pr * interp1(Vc[t + 1, a, rem - 1], m.post(pis, y), Nc)
                            else:
                                val = val + interp1(Vc[t + 1, a, rem], m.prop(pis), Nc)
                        if best is None:
                            best, arg = val, np.full(len(pis), 2 * a + q)
                        else:
                            better = val < best
                            best = np.where(better, val, best)
                            arg = np.where(better, 2 * a + q, arg)
                Vc[t, old, rem] = best
                pol[t, old, rem] = arg
    return Vc, pol, pis


def promote_lb(m, Vc, t, rem, q, pi, Nc):
    c, k = float(QC), float(SW)
    py = m.py1(pi)
    val = 1 - py + c * q + k
    if t < m.T:
        if q:
            for y in (0, 1):
                val = val + (py if y else 1 - py) * interp1(Vc[t + 1, 1, rem - 1], m.post(pi, y), Nc)
        else:
            val = val + interp1(Vc[t + 1, 1, rem], m.prop(pi), Nc)
    return val


def pricing_lb(m: Model, g: Grid2, Vc, Nc, lam):
    """Grid lower bound J[t, rem] over the 2-simplex grid and greedy action indices."""
    c = float(QC)
    w0, w1 = g.w0, g.w1
    wI = 1 - w0 - w1
    A = w0 + w1
    pi = np.where(A > 0, w1 / np.where(A > 0, A, 1), 0.5)
    J, act = {}, {}
    for t in range(m.T, 0, -1):
        for rem in range(m.B + 1):
            options = []
            for q in ((0, 1) if rem else (0,)):
                options.append(((1, q), A * promote_lb(m, Vc, t, rem, q, pi, Nc) + lam * wI))
                val = A * (m.py1(pi) + c * q)
                if t < m.T:
                    if q:
                        for y in (0, 1):
                            ma = A * (m.py1(pi) if y else 1 - m.py1(pi))
                            mi = wI / 2
                            M = ma + mi
                            safe = np.where(M > 0, M, 1)
                            pin = m.post(pi, y)
                            nw0, nw1 = ma * (1 - pin) / safe, ma * pin / safe
                            val = val + M * g.interp(J[t + 1, rem - 1], nw0, nw1)
                    else:
                        pin = m.prop(pi)
                        val = val + g.interp(J[t + 1, rem], A * (1 - pin), A * pin)
                options.append(((0, q), val))
            stack = np.stack([o[1] for o in options])
            k = np.argmin(stack, axis=0)
            J[t, rem] = stack[k, np.arange(stack.shape[1])]
            act[t, rem] = [options[i][0] for i in k]
    return J, act


def root_belief(m):
    p1 = float(m.pi1)
    return (1 - p1) / 2, p1 / 2  # alt mass 1, IID mass 1 -> normalised


# ------------------------------------------------------------------ exact controller evaluation
def evaluate_controller(m: Model, g: Grid2, act, cpol, pis, Nc):
    """Exact (rational) alt cost and causal/IID risk of the snapped-grid controller."""
    e = {0: m.e[0], 1: m.e[1]}
    trans = {0: {0: 1 - m.a01, 1: m.a01}, 1: {0: m.a10, 1: 1 - m.a10}}
    w0g, w1g = g.w0, g.w1

    def pi_of(k):
        A = w0g[k] + w1g[k]
        return w1g[k] / A if A > 0 else 0.5

    def succ(k, q, y):
        a, b = w0g[k], w1g[k]
        wI = 1 - a - b
        A = a + b
        p = pi_of(k)
        if not q:
            pn = m.prop(np.array([p]))[0]
            return int(g.snap(A * (1 - pn), A * pn)[0])
        py = m.py1(p)
        ma = A * (py if y else 1 - py)
        M = ma + wI / 2
        pn = m.post(np.array([p]), y)[0]
        if M <= 0:
            return int(g.snap(0.0, 0.0)[0])
        return int(g.snap(ma * (1 - pn) / M, ma * pn / M)[0])

    def csnap(p):
        return int(round(min(max(p, 0.0), 1.0) * Nc))

    @lru_cache(maxsize=None)
    def cont(t, old, rem, ci, s):
        code = int(cpol[t, old, rem][ci])
        a, q = divmod(code, 2)
        val = (e[s] if a == 0 else 1 - e[s]) + QC * q + SW * (a != old)
        if t < m.T:
            p = pis[ci]
            for s2 in (0, 1):
                ts = trans[s][s2]
                if not ts:
                    continue
                if q:
                    for y in (0, 1):
                        py = e[s] if y else 1 - e[s]
                        ni = csnap(m.post(np.array([p]), y)[0])
                        val += ts * py * cont(t + 1, a, rem - 1, ni, s2)
                else:
                    val += ts * cont(t + 1, a, rem, csnap(m.prop(np.array([p]))[0]), s2)
        return val

    def promote_cost(t, rem, k, q, s):
        val = 1 - e[s] + QC * q + SW
        if t < m.T:
            p = pi_of(k)
            for s2 in (0, 1):
                ts = trans[s][s2]
                if not ts:
                    continue
                if q:
                    for y in (0, 1):
                        py = e[s] if y else 1 - e[s]
                        val += ts * py * cont(t + 1, 1, rem - 1, csnap(m.post(np.array([p]), y)[0]), s2)
                else:
                    val += ts * cont(t + 1, 1, rem, csnap(m.prop(np.array([p]))[0]), s2)
        return val

    states = set()

    @lru_cache(maxsize=None)
    def cost(t, rem, k, s):
        states.add((t, rem, k))
        a, q = act[t, rem][k]
        if a:
            return promote_cost(t, rem, k, q, s)
        val = e[s] + QC * q
        if t < m.T:
            for s2 in (0, 1):
                ts = trans[s][s2]
                if not ts:
                    continue
                if q:
                    for y in (0, 1):
                        py = e[s] if y else 1 - e[s]
                        val += ts * py * cost(t + 1, rem - 1, succ(k, 1, y), s2)
                else:
                    val += ts * cost(t + 1, rem, succ(k, 0, None), s2)
        return val

    @lru_cache(maxsize=None)
    def risk(t, rem, k, causal):
        a, q = act[t, rem][k]
        if a:
            return F(1)
        if t == m.T:
            return F(0)
        if not q:
            return risk(t + 1, rem, succ(k, 0, None), causal)
        v0 = risk(t + 1, rem - 1, succ(k, 1, 0), causal)
        v1 = risk(t + 1, rem - 1, succ(k, 1, 1), causal)
        return max(v0, (v0 + v1) / 2) if causal else (v0 + v1) / 2

    r0w0, r0w1 = root_belief(m)
    k0 = int(g.snap(r0w0, r0w1)[0])
    p1 = m.pi1
    total = (1 - p1) * cost(1, m.B, k0, 0) + p1 * cost(1, m.B, k0, 1)
    return total, risk(1, m.B, k0, True), risk(1, m.B, k0, False), len(states)


def never_cost(m):
    p, total = m.pi1, F(0)
    for _ in range(m.T):
        total += m.e[0] + (m.e[1] - m.e[0]) * p
        p = p * (1 - m.a10) + (1 - p) * m.a01
    return total


def certify(m: Model, N, Nc, n_lam=24):
    g = Grid2(N)
    Vc, cpol, pis = continuation_lb(m, Nc)
    r0 = root_belief(m)

    def L(lam):
        J, act = pricing_lb(m, g, Vc, Nc, lam)
        # root masses: alt 1 + IID 1 = 2 (beliefs are normalised)
        return 2 * float(g.interp(J[1, m.B], np.array([r0[0]]), np.array([r0[1]]))[0]) - float(m.alpha) * lam, act

    # golden-section on concave L(lam)
    lo, hi = 0.0, 40.0
    phi = (5 ** 0.5 - 1) / 2
    a, b = hi - phi * (hi - lo), lo + phi * (hi - lo)
    fa, fb = L(a)[0], L(b)[0]
    for _ in range(40):
        if fa < fb:
            lo, a, fa = a, b, fb
            b = lo + phi * (hi - lo)
            fb = L(b)[0]
        else:
            hi, b, fb = b, a, fa
            a = hi - phi * (hi - lo)
            fa = L(a)[0]
    lam_star = (lo + hi) / 2
    l_star = max(fa, fb, L(0.0)[0])
    cn = never_cost(m)
    best_u, best = cn, {"lam": None, "note": "never-promote"}
    vstates = 0
    for lam in sorted({lam_star, *np.geomspace(0.05, 40, n_lam)}):
        _, act = L(float(lam))
        raw, rc, ri, ns = evaluate_controller(m, g, act, cpol, pis, Nc)
        vstates = max(vstates, ns)
        activation = min(F(1), m.alpha / rc) if rc else F(1)
        u = activation * raw + (1 - activation) * cn
        if u < best_u:
            best_u, best = u, {"lam": float(lam), "raw_cost": raw, "causal_risk": rc,
                               "iid_risk": ri, "activation": activation}
    return {"N": N, "Nc": Nc, "L_float": l_star - 1e-9, "lam_star": lam_star, "U": best_u,
            "U_float": float(best_u), "best_controller": best,
            "grid_points_per_t_rem": len(g.w0),
            "lb_state_count": m.T * (m.B + 1) * len(g.w0),
            "controller_memory_states_reached": vstates}


CELLS = [
    ("C1", 5, 2, F(1, 4), E20, "193099/80000", "193099/80000"),
    ("C4", 6, 3, F(1, 4), E20, "461083/160000", "461083/160000"),
    ("C5", 8, 3, F(1, 4), E20, "24735833/6400000", None),
    ("C2", 5, 2, F(9, 10), (F(1, 10), F(9, 10)), "76309/31250", None),
    ("C3", 6, 3, F(3, 4), E20, "118361/40000", None),
    ("C6", 8, 3, F(3, 4), E20, "39589/10000", None),
    ("P12", 12, 4, F(1, 4), E20, None, None),
    ("P16", 16, 5, F(1, 4), E20, None, None),
]


def main():
    out = {"purpose": "B2 grid lower bound + snapped FSC upper bound (d=1), tree-free",
           "float_note": "L computed in float64 with a 1e-9 margin; not a rational certificate. "
                         "U, its causal risk and repair are exact rationals.", "cells": []}
    for cid, T, B, tr, em, vstar, _ in CELLS:
        m = Model(T, B, tr, em)
        rec = {"id": cid, "T": T, "B": B, "d": 1, "transition": str(tr),
               "emissions": [str(x) for x in em], "Vstar_reference": vstar,
               "learner_infosets_counted": count_learner_infos(T, B, 1), "runs": []}
        for N in (4, 8, 16, 32, 64):
            t0 = time.perf_counter()
            r = certify(m, N, Nc=8 * N)
            r["seconds"] = time.perf_counter() - t0
            if vstar:
                vs = F(vstar)
                r["L_le_Vstar"] = r["L_float"] <= float(vs) + 1e-12
                r["U_ge_Vstar"] = r["U"] >= vs
                r["gap_to_Vstar_U"] = float(r["U"] - vs)
                r["gap_to_Vstar_L"] = float(vs) - r["L_float"]
            rec["runs"].append(r)
            print(cid, N, round(r["L_float"], 6), round(r["U_float"], 6), vstar and float(F(vstar)),
                  r["lb_state_count"], rec["learner_infosets_counted"], round(r["seconds"], 1),
                  flush=True)
            if r["seconds"] > 90:
                break
        out["cells"].append(rec)
    write_result("b2_grid_certificate_v1.json", out, Path(__file__))


if __name__ == "__main__":
    main()
