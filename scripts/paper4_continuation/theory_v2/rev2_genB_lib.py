"""rev2 (P2 review of GENERAL_B_PREMIUM.md): independent exact-rational evaluators for t = 1, d = 1, c = k = 0.

Written from the primitive model (CAUSAL_SAFETY_PREMIUM_THEORY.md section 0), not from wpG_lib:
  S_1 = theta ~ Ber(1/2), S_s = theta (s odd) / 1 - theta (s even); Y_s ~ Ber(1-e) if S_s = 1 else Ber(e).
  X_j := Y_tau_j (tau_j odd) or 1 - Y_tau_j (tau_j even); D = sum(2X - 1); w_s = s_s (1-2e) tanh(D L / 2).
Causal worst-case risk of a leaf promotion function g on a label tree: R(h) = max(R(h0), (R(h0)+R(h1))/2).
"""
from __future__ import annotations

import math
from fractions import Fraction as F
from itertools import product


def lam(e):
    return (1 - e) / e


def th(D, e):  # tanh(D L / 2) = (lam^D - 1)/(lam^D + 1), exact, D any int
    x = lam(e) ** D
    return (x - 1) / (x + 1)


def m_of(D, e):
    return (1 - 2 * e) * th(abs(D), e)


def w_at(s, D, e):  # gain of action 1 over 0 at time s given D (released labels)
    sgn = 1 if s % 2 == 1 else -1
    return sgn * (1 - 2 * e) * th(D, e)


def p_theta1(D, e):
    x = lam(e) ** D
    return x / (1 + x)


def tree_risk(leaf_vals):
    """leaf_vals: list of length 2^B indexed by bits (first label = most significant). Returns (causal, iid)."""
    R = list(leaf_vals)
    while len(R) > 1:
        R = [max(R[2 * i], (R[2 * i] + R[2 * i + 1]) / 2) for i in range(len(R) // 2)]
    return R[0], sum(leaf_vals) / len(leaf_vals)


# ---------------- static slope problem ----------------
def absD_classes(B, e):
    """per |D| = k: (weight per pattern P_A(y) m(D), number of patterns)."""
    out = {}
    for a in range(B + 1):
        D = 2 * a - B
        pa = ((1 - e) ** a * e ** (B - a) + e ** a * (1 - e) ** (B - a)) / 2
        k = abs(D)
        wgt = pa * m_of(D, e)
        n = math.comb(B, a)
        if k in out:
            assert out[k][0] == wgt
            out[k] = (wgt, out[k][1] + n)
        else:
            out[k] = (wgt, n)
    return out


def S_iid(B, alpha, e):
    """exact static IID slope; returns (S, fstar dict |D| -> fraction in [0,1])."""
    cls = absD_classes(B, e)
    budget = F(alpha) * 2 ** B
    S, fstar = F(0), {}
    for k in sorted(cls, key=lambda k: -cls[k][0]):
        wgt, n = cls[k]
        take = min(F(n), budget) if wgt > 0 else F(0)
        fstar[k] = take / n
        S += wgt * take
        budget -= take
    return S, fstar


# ---------------- aligned re-timing learner (Theorem A) ----------------
def aligned_leaves(B, e):
    """enumerate z in {0,1}^B for the aligned learner; return list of dicts (z, D_B, tau_B, PA)."""
    out = []
    for z in product((0, 1), repeat=B):
        D, tau, p1, p0 = 0, 0, F(1), F(1)
        for i, zi in enumerate(z):
            # choose tau_i
            if i == 0:
                tau = 1
            else:
                s = tau + 1
                if D > 0 and s % 2 == 0:
                    s += 1
                if D < 0 and s % 2 == 1:
                    s += 1
                tau = s
            y = zi
            x = y if tau % 2 == 1 else 1 - y
            p1 *= (1 - e) if x == 1 else e  # theta = 1: X ~ Ber(1-e)
            p0 *= e if x == 1 else (1 - e)
            D += 2 * x - 1
        out.append(dict(z=z, D=D, tau=tau, PA=(p1 + p0) / 2))
    return out


def aligned_eval(T, B, e, alpha, start=None):
    """Theorem A step 4 plan: promote w.p. f*(|D_B|) at the first t >= start (default 2B), t <= T, with w_t > 0.
    Returns exact causal risk, IID risk and VOI under A."""
    start = 2 * B if start is None else start
    S, fstar = S_iid(B, alpha, e)
    g, voi = [], F(0)
    for lf in aligned_leaves(B, e):
        D = lf["D"]
        assert lf["tau"] + 1 <= max(start, lf["tau"] + 1) and lf["tau"] <= 2 * B - 1
        ts = [t for t in range(max(start, lf["tau"] + 1), T + 1) if w_at(t, D, e) > 0]
        val = fstar[abs(D)] if ts else F(0)
        g.append(val)
        if ts:
            voi += lf["PA"] * val * m_of(D, e) * len(ts)  # all right-sign steps from sigma on
    rc, ri = tree_risk(g)
    return dict(S_iid=S, risk_causal=rc, risk_iid=ri, voi=voi)


# ---------------- calendar 1..B, label-tree quantities ----------------
def calendar_leaves(B, e):
    """calendar 1..B: for each y in {0,1}^B, X_j = y_j flipped at even j."""
    out = []
    for y in product((0, 1), repeat=B):
        x = [yj if (j + 1) % 2 == 1 else 1 - yj for j, yj in enumerate(y)]
        a = sum(x)
        pa = ((1 - e) ** a * e ** (B - a) + e ** a * (1 - e) ** (B - a)) / 2
        out.append(dict(y=y, x=x, PA=pa))
    return out


def full_voi_calendar(T, B, e):
    """sum_t E_A (w_t)^+ on calendar 1..B (exact)."""
    tot = F(0)
    for lf in calendar_leaves(B, e):
        for t in range(1, T + 1):
            n = min(t - 1, B)
            D = sum(2 * xi - 1 for xi in lf["x"][:n])
            w = w_at(t, D, e)
            if w > 0:
                tot += lf["PA"] * w
    return tot


def betting_eval(T, B, e, alpha):
    """Theorem V test policy on calendar 1..B (exact). Returns causal risk, IID risk, VOI_test, E[tau;tau<=B],
    P(tau>B)."""
    alpha = F(alpha)
    g, voi, Etau, Pno = [], F(0), F(0), F(0)
    for lf in calendar_leaves(B, e):
        y, x = lf["y"], lf["x"]
        E1 = E0 = F(1)
        tau = None
        for n in range(1, B + 1):
            phi = 2 * (1 - e) if y[n - 1] == 1 else 2 * e
            if n % 2 == 1:
                E1 *= phi
            else:
                E0 *= phi
            if (E1 + E0) / 2 >= 1 / alpha:
                tau = n
                break
        sigma = None
        if tau is not None:
            Etau += lf["PA"] * tau
            for t in range(tau + 1, T + 1):
                n = min(t - 1, B)
                D = sum(2 * xi - 1 for xi in x[:n])
                if w_at(t, D, e) > 0:
                    sigma = t
                    break
        else:
            Pno += lf["PA"]
        g.append(F(1) if sigma is not None else F(0))
        if sigma is not None:
            for t in range(sigma, T + 1):
                n = min(t - 1, B)
                D = sum(2 * xi - 1 for xi in x[:n])
                w = w_at(t, D, e)
                if t == sigma or w > 0:
                    voi += lf["PA"] * w
    rc, ri = tree_risk(g)
    return dict(risk_causal=rc, risk_iid=ri, voi_test=voi, E_tau_le_B=Etau, P_tau_gt_B=Pno)


def thmV_constants(B, e, alpha):
    e, alpha = float(e), float(alpha)
    Ie = math.log(2) + (1 - e) * math.log(1 - e) + e * math.log(e)
    L = math.log((1 - e) / e)
    K = 2 * math.log(4 * (1 - e) / alpha) / Ie
    h = B // 2
    if h > 0 and h * Ie > math.log(2 / alpha):
        pi = math.exp(-2 * (h * Ie - math.log(2 / alpha)) ** 2 / (h * L * L))
    else:
        pi = 1.0
    return K, pi
