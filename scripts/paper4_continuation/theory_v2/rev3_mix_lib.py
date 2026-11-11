"""rev3 (P5 review of MIXING_PREMIUM_THEOREM.md): independent exact-rational evaluators.

Written from the primitive model (CAUSAL_SAFETY_PREMIUM_THEORY.md section 0), NOT from wpM_* scripts.
Symmetric stationary chain t01 = t10 = t, rho = 1 - 2t, r = |rho|; emissions (e, 1-e); prior 1/2.
Deviation x := 2 P(S = 1 | info) - 1.  A label at deviation x has P(Y=1) = (1 + a x)/2, a = 1 - 2e, and the posterior
deviation is (x + s a)/(1 + s a x), s = 2y - 1.  Between steps x -> rho x.  Gain of action 1 at a step: w = a x.

B = 1 (any k): brute-force design gains G_y(tau) over all 0/1 post-release schedules (switch cost k per change, A_0 = 0,
no switch after T).  B <= 2 (k = 0): brute-force branch slopes s_y(T), H_empty(T) over all pure plans, exact.
"""
from __future__ import annotations

from fractions import Fraction as F
from functools import lru_cache
from itertools import product


class Chain:
    def __init__(self, t, e):
        self.t, self.e = F(t), F(e)
        self.rho = 1 - 2 * self.t
        self.r = abs(self.rho)
        self.a = 1 - 2 * self.e
        self.g = self.a ** 2

    def post(self, x, s):  # posterior deviation after label with sign s at prior deviation x
        return (x + s * self.a) / (1 + s * self.a * x)

    def py(self, x, s):  # P(label sign s | deviation x)
        return (1 + s * self.a * x) / 2


# ------------------------------------------------------------------ B = 1
def b1_design_gains(ch: Chain, T, d, k):
    """{y: max_tau G_y(tau)} by brute force; G_y over nonzero schedules on offsets j in [d, T - tau]."""
    out = {}
    for y in (0, 1):
        s = 2 * y - 1
        best = None
        for tau in range(1, T - d + 1):
            js = list(range(d, T - tau + 1))
            w = [s * ch.g * ch.rho ** j for j in js]
            for bits in product((0, 1), repeat=len(js)):
                if not any(bits):
                    continue
                val = sum(b * wj for b, wj in zip(bits, w))
                prev, sw = 0, 0
                for b in bits:
                    sw += b != prev
                    prev = b
                val -= k * sw  # no switch after T (window end = T)
                if best is None or val > best:
                    best = val
        out[y] = best  # None if no window
    return out


def m1_prediction(ch: Chain, T, d, c, k):
    """M1.1 closed form rho_Gamma = Pi^+/(G0 - 2c) with brute-force G_y; returns dict."""
    G = b1_design_gains(ch, T, d, k)
    G0, G1 = G[0], G[1]
    delta = G0 - (max(G1, 0) if G1 is not None else 0)
    Pi = min(G0 / 2 - c, delta, (delta + k) / 2 - c)
    rho_g = (Pi / (G0 - 2 * c)) if Pi > 0 else F(0)
    out = {"G0": G0, "G1": G1, "Pi": Pi, "rhoG_pred": rho_g, "Gamma_over_alpha_pred": max(Pi, 0)}
    if k == 0:
        n = T - d
        r, rho, g = ch.r, ch.rho, ch.g
        dn = g * r ** d * (1 - rho ** n) / (1 + r)
        n0 = (n + 1) // 2
        g0n = g * r ** d * (1 - r ** (2 * n0)) / (1 - r ** 2)
        num = dn / 2 - c
        out["rhoG_m1_3"] = num / (g0n - 2 * c) if num > 0 else F(0)
    cond = 2 * c + k < ch.g * ch.r ** d * (1 - ch.r)
    out["m1_2_condition"] = cond
    if cond:
        L = (ch.g * ch.r ** d - 2 * c - max(k, ch.g * ch.r ** (d + 1) - k))
        out["c1"] = L / (2 * (k + ch.g * ch.r ** d / (1 - ch.r ** 2) - 2 * c))
    return out


# ------------------------------------------------------------------ B <= 2, k = 0 branch slopes
def _post_value(ch, xs):
    """Promote at first step with xs[i] > 0 (k = 0, free play): value sum of (a x)^+; if none positive the best
    forced promotion is max (a x) (<= 0).  xs: deviations at candidate steps from promotion-eligible time on."""
    pos = [ch.a * x for x in xs if x > 0]
    if pos:
        return sum(pos)
    return max((ch.a * x for x in xs), default=None)


def branch_options(ch: Chain, T, B, d, c, u, y):
    """All (g_y, r_y) of class-Q pure plans after first label Y_u = y (first query at u), k = 0.

    g_y includes the first query's cost c.  r_y = IID probability of promotion given Y_u = y.
    Returns a list of (g, r) pairs (exhaustive up to dominance within fixed (event, timing))."""
    s = 2 * y - 1
    x_u = s * ch.a  # posterior deviation at u
    opts = [(-c, F(0))]  # never promote, no second query
    first_rel = u + d
    if first_rel > T:
        return opts  # Q plans then never promote
    steps = range(first_rel, T + 1)
    dev1 = {t: x_u * ch.rho ** (t - u) for t in steps}
    # no second query (or B = 1): event = everything, promote at sigma >= first_rel
    for sig in steps:
        val = ch.a * dev1[sig] + sum(max(ch.a * dev1[t], 0) for t in steps if t > sig)
        opts.append((val - c, F(1)))
    if B < 2:
        return opts
    for u2 in range(u + 1, T + 1):  # second query time (deterministic within branch: no info before its release)
        rel2 = u2 + d
        xpre = x_u * ch.rho ** (u2 - u)
        branch_v = {}
        for sv in (-1, 1):
            p = ch.py(xpre, sv)
            xp = ch.post(xpre, sv)
            branch_v[sv] = (p, xp)

        def dev(t, sv):
            if t < rel2:
                return dev1[t]
            p, xp = branch_v[sv]
            return xp * ch.rho ** (t - u2)

        # promotion before rel2 (common sigma, event everything), continuation free with both v
        for sig in range(first_rel, min(rel2, T + 1)):
            val = 0
            for sv in (-1, 1):
                p, _ = branch_v[sv]
                vv = ch.a * dev(sig, sv) + sum(max(ch.a * dev(t, sv), 0) for t in range(sig + 1, T + 1))
                val += p * vv
            opts.append((val - 2 * c, F(1)))
        if rel2 > T:
            continue
        # promotion after rel2: per-v sigma_v in [rel2, T] or never
        per_v = {}
        for sv in (-1, 1):
            p, _ = branch_v[sv]
            cands = [None]
            for sig in range(rel2, T + 1):
                vv = ch.a * dev(sig, sv) + sum(max(ch.a * dev(t, sv), 0) for t in range(sig + 1, T + 1))
                cands.append(vv)
            best = max(v for v in cands if v is not None)
            per_v[sv] = (p, best)
        for e0, e1 in product((0, 1), repeat=2):
            if not (e0 or e1):
                opts.append((-2 * c, F(0)))
                continue
            val = (per_v[-1][0] * per_v[-1][1] if e0 else 0) + (per_v[1][0] * per_v[1][1] if e1 else 0)
            opts.append((val - 2 * c, F(e0 + e1, 2)))
    return opts


def h_empty(ch: Chain, T, B, d, c):
    """Best class-P gain: promote before the first release (or never query), k = 0, free continuation."""
    best = F(0)  # promote with no query: w = 0 everywhere, gain 0 (k = 0)
    for u in range(1, T + 1):
        if u + d > T:
            continue
        for y_dummy in (0,):
            pass
        tot = 0
        for s_ in (-1, 1):
            x_u = s_ * ch.a
            dev1 = {t: x_u * ch.rho ** (t - u) for t in range(u + d, T + 1)}
            v_single = sum(max(ch.a * dev1[t], 0) for t in dev1)
            bestv = v_single  # no second query
            if B >= 2:
                for u2 in range(u + 1, T + 1):
                    if u2 < u + d:
                        continue  # handled as common below
                    bestv = max(bestv, _two_label_value(ch, T, d, u, x_u, u2) - c)
            tot += F(1, 2) * bestv
        cand = tot - c
        best = max(best, cand)
        if B >= 2:  # common second query time u2 < u + d
            for u2 in range(u + 1, min(u + d, T + 1)):
                tot2 = 0
                for s_ in (-1, 1):
                    tot2 += F(1, 2) * _two_label_value(ch, T, d, u, s_ * ch.a, u2)
                best = max(best, tot2 - 2 * c)
    return best


def _two_label_value(ch, T, d, u, x_u, u2):
    """sum_t E(a x_t)^+ from u + d on, given first-label deviation x_u at u and second label at u2."""
    rel2 = u2 + d
    val = 0
    for t in range(u + d, min(rel2, T + 1)):
        val += max(ch.a * x_u * ch.rho ** (t - u), 0)
    xpre = x_u * ch.rho ** (u2 - u)
    for sv in (-1, 1):
        p = ch.py(xpre, sv)
        xp = ch.post(xpre, sv)
        for t in range(rel2, T + 1):
            val += p * max(ch.a * xp * ch.rho ** (t - u2), 0)
    return val


def slopes(ch: Chain, T, B, d, c):
    """s_y(T) = max g_y/r_y over class Q (all first-query times u), H_empty, S_I, S', plus per-branch option sets."""
    s = {0: None, 1: None}
    frontier = {0: {}, 1: {}}  # y -> r -> best g (over all u)
    for u in range(1, T + 1):
        for y in (0, 1):
            for g, r in branch_options(ch, T, B, d, c, u, y):
                if r > 0:
                    val = g / r
                    if s[y] is None or val > s[y]:
                        s[y] = val
    H = h_empty(ch, T, B, d, c)
    pos = lambda z: max(z, 0) if z is not None else F(0)
    S_I = max(pos(H), pos(s[0]), pos(s[1]))
    S_p = max(pos(H), pos(s[1]), (pos(s[0]) + pos(s[1])) / 2)
    return {"s0": s[0], "s1": s[1], "H": H, "S_I": S_I, "S_prime": S_p}


def best_ratio_pure(ch: Chain, T, B, d, c, alpha):
    """SUPERSEDED (v1 bug): combines branch options whose second query time u2 < u + d differs between branches,
    which no single plan can do (y is unknown before u + d).  Kept for the record; use best_ratio_pure_v2."""
    best = None
    for u in range(1, T + 1):
        fr = {}
        for y in (0, 1):
            m = {}
            for g, r in branch_options(ch, T, B, d, c, u, y):
                if r not in m or g > m[r]:
                    m[r] = g
            fr[y] = m
        for r0, g0 in fr[0].items():
            for r1, g1 in fr[1].items():
                R = (r0 + r1) / 2
                if R >= alpha and R > 0:
                    val = ((g0 + g1) / 2) / R
                    if best is None or val > best:
                        best = val
    H = h_empty(ch, T, B, d, c)
    if best is None or H > best:
        best = H
    return best


# ------------------------------------------------------------------ M4 closed forms (from the statement)
def m4_closed(ch: Chain, d):
    g, r = ch.g, ch.r
    s0 = g * r ** d * (3 + r) / (2 * (1 - r ** 2))
    s1 = g * r ** d / (1 - r)
    return s0, s1


def zeta_plan(ch: Chain, T, d):
    """zeta(T) = max_delta H0(delta; T): query at 1; Y1 = 0 -> promote at 1+d, query at 1+delta, follow sign(w)."""
    best = None
    x_u = -ch.a
    for u2 in range(2, T + 1):
        v = _two_label_value(ch, T, d, 1, x_u, u2)
        # promotion at 1+d forced: w there is a * x_u * rho^d = g r^d > 0 for odd d, already counted as positive
        if best is None or v > best:
            best = v
    # also no second query
    v1 = sum(max(ch.a * x_u * ch.rho ** (t - 1), 0) for t in range(1 + d, T + 1))
    return max(best if best is not None else v1, v1)


def m4_bound(ch: Chain, T, d, c):
    s0, s1 = m4_closed(ch, d)
    z = zeta_plan(ch, T, d)
    gam = z - 4 * c - (s0 + s1) / 2
    return {"zeta": z, "s0inf": s0, "s1inf": s1, "Gamma_over_alpha_bound": gam,
            "rhoG_bound": max(gam, 0) / s0}


def m4_T0(ch: Chain, d, c, Tmax=80):
    """Smallest T with explicit truncation bound s0inf - g(r^{d+delta}/2 + r^{T-delta})/(1-r) - 4c > (s0+s1)/2."""
    s0, s1 = m4_closed(ch, d)
    g, r = ch.g, ch.r
    for T in range(d + 2, Tmax + 1):
        for dl in range(1, T - d + 1):
            lb = s0 - g * (r ** (d + dl) / 2 + r ** (T - dl)) / (1 - r)
            if lb - 4 * c > (s0 + s1) / 2:
                return T
    return None


def m4_T0_exact(ch: Chain, d, c, Tmax=40):
    s0, s1 = m4_closed(ch, d)
    for T in range(d + 2, Tmax + 1):
        if zeta_plan(ch, T, d) - 4 * c > (s0 + s1) / 2:
            return T
    return None


def U_B(ch: Chain, B, d):
    return (1 + ch.a * ch.r) ** (B - 1) * ch.a * B * ch.r ** d / (1 - ch.r)


def branch_options_tagged(ch: Chain, T, B, d, c, u, y):
    """As branch_options, but each option carries tag = u2 if the second query precedes the first release
    (u2 < u + d, so it must be common to both branches), else None."""
    out = []
    base = branch_options(ch, T, 1, d, c, u, y)
    out += [(g, r, None) for g, r in base]
    if B < 2:
        return out
    # recompute B = 2 options per u2 by restricting branch_options' loop to one u2 at a time
    for u2 in range(u + 1, T + 1):
        tag = u2 if u2 < u + d else None
        for g, r in _options_one_u2(ch, T, d, c, u, y, u2):
            out.append((g, r, tag))
    return out


def _options_one_u2(ch, T, d, c, u, y, u2):
    s = 2 * y - 1
    x_u = s * ch.a
    first_rel = u + d
    if first_rel > T:
        return []
    dev1 = {t: x_u * ch.rho ** (t - u) for t in range(first_rel, T + 1)}
    rel2 = u2 + d
    xpre = x_u * ch.rho ** (u2 - u)
    bv = {sv: (ch.py(xpre, sv), ch.post(xpre, sv)) for sv in (-1, 1)}

    def dev(t, sv):
        return dev1[t] if t < rel2 else bv[sv][1] * ch.rho ** (t - u2)

    opts = [(-2 * c, F(0))]
    for sig in range(first_rel, min(rel2, T + 1)):
        val = sum(bv[sv][0] * (ch.a * dev(sig, sv) + sum(max(ch.a * dev(t, sv), 0) for t in range(sig + 1, T + 1)))
                  for sv in (-1, 1))
        opts.append((val - 2 * c, F(1)))
    if rel2 <= T:
        per_v = {}
        for sv in (-1, 1):
            per_v[sv] = max(ch.a * dev(sig, sv) + sum(max(ch.a * dev(t, sv), 0) for t in range(sig + 1, T + 1))
                            for sig in range(rel2, T + 1))
        for e0, e1 in ((1, 0), (0, 1), (1, 1)):
            val = (bv[-1][0] * per_v[-1] if e0 else 0) + (bv[1][0] * per_v[1] if e1 else 0)
            opts.append((val - 2 * c, F(e0 + e1, 2)))
    return opts


def best_ratio_pure_v2(ch: Chain, T, B, d, c, alpha):
    """max gain/R_IID over feasible pure plans with R_IID >= alpha: branch options must share any tag."""
    best = None
    for u in range(1, T + 1):
        fr = {}
        for y in (0, 1):
            m = {}
            for g, r, tag in branch_options_tagged(ch, T, B, d, c, u, y):
                key = (r, tag)
                if key not in m or g > m[key]:
                    m[key] = g
            fr[y] = m
        for (r0, t0), g0 in fr[0].items():
            for (r1, t1), g1 in fr[1].items():
                if t0 is not None and t1 is not None and t0 != t1:
                    continue
                if (t0 is None) != (t1 is None) and (t0 is not None or t1 is not None):
                    # one branch commits to an early second query, the other must make the same query:
                    # allow only if the other branch's option is also tagged identically
                    continue
                R = (r0 + r1) / 2
                if R >= alpha and R > 0:
                    val = ((g0 + g1) / 2) / R
                    if best is None or val > best:
                        best = val
    H = h_empty(ch, T, B, d, c)
    return H if best is None or H > best else best
