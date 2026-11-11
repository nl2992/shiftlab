"""WP-M (P1): B = 2 first-label-relaxation quantities (Theorem M4), k = 0.

Symmetric stationary chain t01 = t10 = t, rho = 1 - 2t, r = |rho|, emissions (e, 1-e), prior 1/2, a = 1 - 2e,
g = a^2, delay d.  All finite-T quantities are computed by an exact Bayesian forward filter (Fractions) that
does NOT use the closed forms; the closed forms are T = infinity suprema (Theorem M4).

Gain of action 1 over action 0 at time s: w_s = 2 q_s - 1 = a (2 P(S_s = 1 | released labels) - 1).
"""

from __future__ import annotations

import itertools
from fractions import Fraction as F


def _posterior_dev(t, e, obs, s):
    """x = 2 P(S_s = 1 | obs) - 1 and P(obs), obs = [(time, y)] with times <= s, stationary prior 1/2."""
    obs = sorted(obs)
    p1, p0 = F(1, 2), F(1, 2)  # joint P(S_cur = ., obs so far), cur = 1
    cur = 1
    for time_, y in obs:
        for _ in range(time_ - cur):
            p1, p0 = p1 * (1 - t) + p0 * t, p0 * (1 - t) + p1 * t
        cur = time_
        l1 = (1 - e) if y == 1 else e
        l0 = e if y == 1 else (1 - e)
        p1, p0 = p1 * l1, p0 * l0
    for _ in range(s - cur):
        p1, p0 = p1 * (1 - t) + p0 * t, p0 * (1 - t) + p1 * t
    tot = p1 + p0
    return (p1 - p0) / tot, tot


def released_value(t, e, d, T, labels, start, cond):
    """sum_{s=start}^{T} E[(w_s)^+ | cond] where labels = [(time, value or None)], value None = averaged.

    cond = list of (time, y) that are conditioned on (their probability is divided out)."""
    a = 1 - 2 * e
    free = [i for i, (_, y) in enumerate(labels) if y is None]
    _, pc = _posterior_dev(t, e, cond, max([c[0] for c in cond], default=1))
    total = F(0)
    for vals in itertools.product((0, 1), repeat=len(free)):
        full = list(labels)
        for i, v in zip(free, vals):
            full[i] = (full[i][0], v)
        # probability of the full label vector relative to cond
        _, pf = _posterior_dev(t, e, full, max(x[0] for x in full))
        weight = pf / pc
        for s in range(start, T + 1):
            rel = [x for x in full if x[0] + d <= s]
            if not rel:
                continue
            x, _ = _posterior_dev(t, e, rel, s)
            total += weight * max(F(0), a * x)
    return total


def H_branch(t, e, d, T, y, delta, u1=1):
    """Branch y1 = y: promote at u1 + d, second label (free) queried at u1 + delta."""
    labels = [(u1, y)] + ([(u1 + delta, None)] if u1 + delta <= T else [])
    return released_value(t, e, d, T, labels, u1 + d, [(u1, y)])


def pattern_ratio(t, e, d, T, y, delta, v, u1=1):
    """Branch y1 = y, promote only after label 2 (at u1 + delta) is released with value v: 2 * gain."""
    u2 = u1 + delta
    if u2 + d > T:
        return F(0)
    labels = [(u1, y), (u2, v)]
    return 2 * released_value(t, e, d, T, labels, u2 + d, [(u1, y)])


def H_empty(t, e, d, T, u1=1):
    """Unconditional promotion; both labels free; second label time may depend on y1 (sup over delta_y)."""
    best = F(0)
    for y in (0, 1):
        pass
    vals = []
    for y in (0, 1):
        vals.append(max([H_branch(t, e, d, T, y, dl, u1) for dl in range(1, T)] +
                        [released_value(t, e, d, T, [(u1, y)], u1 + d, [(u1, y)])]))
    best = (vals[0] + vals[1]) / 2
    return best


def branch_slopes(t, e, d, T, u1=1):
    """Exact (finite T, k = c = 0, query at u1) branch slopes s_0, s_1 and best immediate-promotion zeta."""
    out = {}
    for y in (0, 1):
        imm = [H_branch(t, e, d, T, y, dl, u1) for dl in range(1, T - u1 + 1)]
        imm.append(released_value(t, e, d, T, [(u1, y)], u1 + d, [(u1, y)]))
        pat = [pattern_ratio(t, e, d, T, y, dl, v, u1) for dl in range(1, T - u1 + 1) for v in (0, 1)]
        out[y] = (max(imm), max(pat) if pat else F(0))
    return out


# ---------------- T = infinity closed forms (Theorem M4, d odd, k = 0) ----------------

def closed_inf(t, e, d):
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    assert d % 2 == 1 and 0 < r < 1
    base = g * r**d / (2 * (1 - r**2))
    s0 = base * (3 + r)          # = Gbar_0^inf + v1   (immediate promotion after Y_1 = 0, free label far away)
    s1 = base * (2 + 2 * r)      # = g r^d / (1 - r)   (pattern (1, 0) at delta = 1)
    h_empty = base * (2 + 2 * r)  # = 2 v1
    pat0 = base * 2 * (1 + r**2)  # best branch-0 pattern (delta = 2)
    h1 = base * (1 + 3 * r)       # Gbar_1^inf + v1
    return {"s0": s0, "s1": s1, "H_empty": h_empty, "pat0": pat0, "H1": h1,
            "gamma_over_alpha_lb_inf": (s0 - s1) / 2, "rho_lb_inf": (s0 - s1) / (2 * s0)}


def H_inf_delta(t, e, d, y, delta):
    """Closed form H_y^(1)(delta) at T = infinity: Gbar_y^inf + v1 - g r^{d+delta} / (2 (1 - r))."""
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    gb = g * r**d / (1 - r**2) * (1 if y == 0 else r)
    v1 = g * r**d / (2 * (1 - r))
    return gb + v1 - g * r ** (d + delta) / (2 * (1 - r))


def zeta(t, e, d, T, c=F(0)):
    """Explicit IID plan ratio: query at 1; after Y_1 = 0 promote at 1 + d, free label 2 at 1 + delta (best
    delta); branch 1 idle.  Ratio >= H_0 - 4c (each branch pays at most 2 queries)."""
    best = max([H_branch(t, e, d, T, 0, dl) for dl in range(1, T)] +
               [released_value(t, e, d, T, [(1, 0)], 1 + d, [(1, 0)])])
    return best - 4 * c


def m4_bound(t, e, d, T, c=F(0)):
    ci = closed_inf(t, e, d)
    z = zeta(t, e, d, T, c)
    lb = z - (ci["s0"] + ci["s1"]) / 2
    return {"zeta": z, "gamma_over_alpha_lb": lb, "rho_lb": max(F(0), lb) / ci["s0"]}


def zeta_closed_lb(t, e, d, T, c=F(0)):
    """Explicit truncation bound: zeta(T) - 4c >= s0inf - g (r^{d+delta}/2 + r^{T-delta})/(1-r) - 4c, best delta."""
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    s0 = closed_inf(t, e, d)["s0"]
    if T - d < 1:
        return None
    return max(s0 - g * (r ** (d + dl) / 2 + r ** (T - dl)) / (1 - r) for dl in range(1, T - d + 1)) - 4 * c


def T0_explicit(t, e, d, c=F(0), Tmax=400):
    """Smallest T with zeta_closed_lb(T) > (s0inf + s1inf)/2 (uniformity threshold of Theorem M4)."""
    ci = closed_inf(t, e, d)
    thr = (ci["s0"] + ci["s1"]) / 2
    for T in range(d + 2, Tmax):
        z = zeta_closed_lb(t, e, d, T, c)
        if z is not None and z > thr:
            return T
    return None
