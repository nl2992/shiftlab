"""Reviewer 1 (SP1) independent implementations. Does NOT import any wpC_* code.

(1) sp1_formula: Theorem SP1 exactly as stated (Lemma W closed form for G-bar_y, then
    Gamma = alpha*[min{G0/2-c, Delta, (Delta+k)/2-c}]^+), using a_j = g r^j and the parity rule.
(2) n1_brute: Theorem N1 with every design gain computed by exact DP from the primitive HMM
    (forward filtering in Fractions, no Lemma S / W / K / Pre used):
      g_z0(tau), g_z1(tau), g_both(tau) by DP over post-release 0/1 schedules (nonzero),
      g_pre by DP over plans that promote before release (or never query / query unreleased),
      then Gamma = alpha*(2 max g_z0 - r_c)^+.
All arithmetic exact (Fraction).
"""

from __future__ import annotations

from fractions import Fraction as F

NEG = None  # sentinel for -infinity


def _mx(a, b):
    if a is NEG:
        return b
    if b is NEG:
        return a
    return a if a >= b else b


# ---------------------------------------------------------------- (1) SP1 as stated
def sp1_formula(T, d, t, e, c, k, alpha):
    t, e, c, k, alpha = map(F, (t, e, c, k, alpha))
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    a = lambda j: g * r**j  # noqa: E731
    if T < d + 1:
        return F(0)

    def gbar(y):
        # positive steps of branch y: w_y(j) = (2y-1) g (-r)^j > 0
        P = [j for j in range(d, T) if ((2 * y - 1) * (-1) ** j) > 0]
        if not P:
            return NEG
        jstar = min(P)
        if a(jstar) > 2 * k:
            return k + sum(max(F(0), a(j) - 2 * k) for j in P)
        return a(jstar) - k

    G0, G1 = gbar(0), gbar(1)
    if G0 is NEG:  # no positive step for branch 0: z0 gain is negative
        return F(0)
    G1p = F(0) if (G1 is NEG or G1 < 0) else G1
    Delta = G0 - G1p
    val = min(G0 / 2 - c, Delta, (Delta + k) / 2 - c)
    return alpha * max(F(0), val)


def sp1_lower_bound(d, t, e, c, k):
    t, e, c, k = map(F, (t, e, c, k))
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    ad, ad1 = g * r**d, g * r ** (d + 1)
    return max(F(0), min((ad - k) / 2 - c, ad - ad1, (ad - ad1 + k) / 2 - c))


# ---------------------------------------------------------------- (2) N1 by brute DP
def _hmm(T, t01, t10, e0, e1, prior1):
    """Marginals P(S_t=1), t=1..T (index t)."""
    p = [None] * (T + 2)
    p[1] = prior1 * (1 - t10) + (1 - prior1) * t01  # propagate(prior1, 1)
    for s in range(2, T + 2):
        p[s] = p[s - 1] * (1 - t10) + (1 - p[s - 1]) * t01
    return p


def _post_weights(T, tau, d, t01, t10, e0, e1, p):
    """For y in {0,1}: P(Y_tau=y) and weights w_y[s] = 2 q_s(y) - 1 for s in [tau+d, T]."""
    ps = p[tau]
    out = {}
    for y in (0, 1):
        ly1 = e1 if y else 1 - e1
        ly0 = e0 if y else 1 - e0
        py = ps * ly1 + (1 - ps) * ly0
        b = ps * ly1 / py  # P(S_tau=1 | Y_tau=y)
        w = {}
        for s in range(tau + 1, T + 1):
            b = b * (1 - t10) + (1 - b) * t01
            if s >= tau + d:
                q = e0 + (e1 - e0) * b
                w[s] = 2 * q - 1
        out[y] = (py, w)
    return out


def _best_sched(times, w, k, start_action, need_nonzero):
    """max over 0/1 schedules x on `times` (consecutive) of sum x_s w_s - k*#switches, starting from
    start_action before the first time; need_nonzero: at least one 1. No switch charged after T."""
    # state: (action, nonzero_seen) -> value
    st = {(start_action, start_action == 1): F(0)}
    for s in times:
        nst = {}
        for (act, nz), v in st.items():
            for x in (0, 1):
                nv = v + (w[s] if x else 0) - (k if x != act else 0)
                key = (x, nz or x == 1)
                if key not in nst or nv > nst[key]:
                    nst[key] = nv
        st = nst
    best = NEG
    for (act, nz), v in st.items():
        if need_nonzero and not nz:
            continue
        best = _mx(best, v)
    return best


def n1_brute(T, d, t01, t10, e0, e1, prior1, c, k, alpha, return_parts=False):
    t01, t10, e0, e1, prior1, c, k, alpha = map(F, (t01, t10, e0, e1, prior1, c, k, alpha))
    p = _hmm(T, t01, t10, e0, e1, prior1)
    marg_w = {s: 2 * (e0 + (e1 - e0) * p[s]) - 1 for s in range(1, T + 1)}
    gz0 = gz1 = gboth = NEG
    for tau in range(1, T - d + 1):
        pw = _post_weights(T, tau, d, t01, t10, e0, e1, p)
        times = list(range(tau + d, T + 1))
        # before release the plan holds A = 0 and earns nothing extra over C_0 (marg weights x 0)
        G = {y: _best_sched(times, pw[y][1], k, 0, True) for y in (0, 1)}
        P = {y: pw[y][0] for y in (0, 1)}
        gz0 = _mx(gz0, P[0] * G[0] - c)
        gz1 = _mx(gz1, P[1] * G[1] - c)
        gboth = _mx(gboth, P[0] * G[0] + P[1] * G[1] - c)
    # g_pre: promote (A=1 somewhere) before any release; enumerate query time q in {None, 1..T}
    gpre = NEG
    for q in [None] + list(range(1, T + 1)):
        rel = None if q is None or q + d > T else q + d
        pre_end = T if rel is None else rel - 1
        pre_times = list(range(1, pre_end + 1))
        # DP over pre schedules, must contain a 1; track last action
        st = {(0, False): F(0)}
        for s in pre_times:
            nst = {}
            for (act, nz), v in st.items():
                for x in (0, 1):
                    nv = v + (marg_w[s] if x else 0) - (k if x != act else 0)
                    key = (x, nz or x == 1)
                    if key not in nst or nv > nst[key]:
                        nst[key] = nv
            st = nst
        qc = c if q is not None else F(0)
        for (act, nz), v in st.items():
            if not nz:
                continue
            if rel is None:
                gpre = _mx(gpre, v - qc)
            else:
                pw = _post_weights(T, q, d, t01, t10, e0, e1, p)
                tot = v - qc
                for y in (0, 1):
                    tot += pw[y][0] * _best_sched(list(range(rel, T + 1)), pw[y][1], k, act, False)
                gpre = _mx(gpre, tot)
    if gz0 is NEG:
        G = F(0)
    else:
        rc = F(0)
        for v in (gpre, gz0, gboth, None if gz1 is NEG else 2 * gz1):
            rc = _mx(rc, v)
        G = alpha * max(F(0), 2 * gz0 - rc)
    if return_parts:
        return G, dict(gz0=gz0, gz1=gz1, gboth=gboth, gpre=gpre)
    return G


def n1_brute_sym(T, d, t, e, c, k, alpha, return_parts=False):
    t, e = F(t), F(e)
    return n1_brute(T, d, t, t, e, 1 - e, F(1, 2), c, k, alpha, return_parts)
