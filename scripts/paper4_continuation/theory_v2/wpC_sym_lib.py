"""WP C (theory_v2): closed forms for the symmetric stationary anti-persistent B = 1 premium.

Model: t01 = t10 = t in (1/2, 1], prior 1/2, e0 = e, e1 = 1 - e.  r = 2t - 1 = -rho, g = (1-2e)^2.
After a label Y_tau = y released at tau + d, the gain of action 1 over action 0 at time tau + j is
w_y(j) = (2y - 1) g rho^j  (j >= d), and 0 at every step before release (stationary symmetric).

Exact objects (all Fractions):
  G_y(tau)   open-loop optimum of a NONZERO 0/1 schedule on j = d..T-tau with switch cost k (A_0 = 0,
             no switch charged after T) -- computed by brute DP ("window DP"), no closed form assumed.
  gamma_window: N1 assembled from G_y(tau), using Lemma Pre (g_pre <= max(0, g_z0, g_z1, g_both)).
  closed forms: Gbar_y, Delta, LB, UB (see STOCHASTIC_POSITIVE_PREMIUM.md, Theorem SP1).
"""

from __future__ import annotations

from fractions import Fraction as F


def weights(T, d, tau, r, g, y):
    rho = -r
    return [(2 * y - 1) * g * rho**j for j in range(d, T - tau + 1)]


def open_loop_best(w, k):
    """max over nonzero 0/1 schedules of sum a_j w_j - k * #switches (start at 0, end free)."""
    NEG = None
    # state: (action, promoted) -> best value
    best = {(0, False): F(0)}
    for wj in w:
        nxt = {}
        for (a, pr), v in best.items():
            for b in (0, 1):
                nv = v + (wj if b else 0) - (k if b != a else 0)
                key = (b, pr or b == 1)
                if key not in nxt or nv > nxt[key]:
                    nxt[key] = nv
        best = nxt
    vals = [v for (a, pr), v in best.items() if pr]
    return max(vals) if vals else NEG


def window_table(T, d, r, g, k):
    """{tau: (G_0(tau), G_1(tau))} for tau = 1..T-d."""
    return {tau: tuple(open_loop_best(weights(T, d, tau, r, g, y), k) for y in (0, 1))
            for tau in range(1, T - d + 1)}


def gamma_over_alpha_window(T, d, r, g, c, k):
    """Exact Gamma/alpha from Theorem N1 + Lemma Pre, with G_y(tau) by brute DP."""
    tab = window_table(T, d, r, g, k)
    if not tab:
        return F(0), {}
    G0bar = max(v[0] for v in tab.values())
    G1bar = max(v[1] for v in tab.values())
    both = max((max(v[0], 0) + max(v[1], 0)) / 2 - c for v in tab.values())
    r_c = max(F(0), G1bar - 2 * c, both)
    r_iid = max(r_c, G0bar - 2 * c)
    return r_iid - r_c, {"G0bar": G0bar, "G1bar": G1bar, "both_best": both, "r_c": r_c,
                         "r_IID": r_iid,
                         "kappa": max(v[0] + v[1] for v in tab.values()) - (G0bar + G1bar - k)}


# ---------------- closed forms (Theorem SP1) ----------------

def gbar_closed(T, d, r, g, k, y):
    """Lemma W: max_tau G_y(tau) = k + sum_{j in P_y}(a_j - 2k)^+ if a_{j*} > 2k else a_{j*} - k."""
    rho = -r
    P = [j for j in range(d, T) if (2 * y - 1) * rho**j > 0]
    if not P:
        return None
    a = [g * r**j for j in P]
    if a[0] > 2 * k:
        return k + sum(x - 2 * k for x in a if x > 2 * k)
    return a[0] - k


def closed_bounds(T, d, r, g, c, k):
    """(LB, UB) on Gamma/alpha; LB == UB when Gbar_1 <= 0 (or P_1 empty)."""
    G0 = gbar_closed(T, d, r, g, k, 0)
    G1 = gbar_closed(T, d, r, g, k, 1)
    if G0 is None:
        return F(0), F(0)
    if G1 is None or G1 <= 0:
        v = max(F(0), min(G0 - 2 * c, G0 / 2 - c))
        return v, v
    D = G0 - G1
    lb = max(F(0), min(G0 - 2 * c, D, D / 2 - c))
    ub = max(F(0), min(G0 - 2 * c, D, (D + k) / 2 - c))
    return lb, ub


def k0_closed(T, d, r, g, c):
    """k = 0, d odd: Gamma/alpha = (g r^d (1 - rho^{T-d}) / (2 (1 + r)) - c)^+ ; d even: 0."""
    if T <= d or d % 2 == 0:
        return F(0)
    rho = -r
    return max(F(0), g * r**d * (1 - rho ** (T - d)) / (2 * (1 + r)) - c)


def ksmall_closed(T, d, r, g, c, k):
    """2k < g r^{T-1}, d odd, T >= d+2: Gamma/alpha = (min{Gbar0-2c, Delta, (Delta+k)/2 - c})^+ with
    Delta = g r^d (1 - rho^L)/(1 - rho) - 2k [L odd], L = T - d."""
    rho = -r
    L = T - d
    A = g * r**d * (1 - rho**L) / (1 - rho)
    D = A - (2 * k if L % 2 else 0)
    G0 = gbar_closed(T, d, r, g, k, 0)
    return max(F(0), min(G0 - 2 * c, D, (D + k) / 2 - c))


# ---------------- Theorem SP1 exact closed form (primitives) ----------------

def J_threshold(r, g, k, cap):
    """Largest j <= cap with g r^j > 2k (cap if k == 0 and r > 0); -1 if none."""
    J = -1
    for j in range(0, cap + 1):
        if g * r**j > 2 * k:
            J = j
    return J


def gbar_primitive(T, d, r, g, k):
    """(Gbar_0, Gbar_1) for d odd from geometric sums; Gbar_1 None if T < d + 2."""
    assert d % 2 == 1 and 0 < r <= 1
    Ms = min(T - 1, J_threshold(r, g, k, T - 1))

    def gsum(first, last):  # sum over j = first, first+2, ..., <= last of (g r^j - 2k)
        if last < first:
            return None
        m = (last - first) // 2 + 1
        geo = g * r**first * ((1 - r ** (2 * m)) / (1 - r**2) if r < 1 else m)
        return geo - 2 * k * m

    s0 = gsum(d, Ms)
    G0 = k + s0 if s0 is not None else g * r**d - k
    if T < d + 2:
        return G0, None
    s1 = gsum(d + 1, Ms)
    G1 = k + s1 if s1 is not None else g * r ** (d + 1) - k
    return G0, G1


def sp1_exact(T, d, r, g, c, k):
    """Gamma/alpha = [min{Gbar0/2 - c, Delta, (Delta + k)/2 - c}]^+ (d odd); 0 for d even or T <= d."""
    if T <= d or d % 2 == 0:
        return F(0)
    G0, G1 = gbar_primitive(T, d, r, g, k)
    if G1 is None:
        return max(F(0), G0 / 2 - c)
    D = G0 - G1
    return max(F(0), min(G0 / 2 - c, D, (D + k) / 2 - c))


def sp1_lower(d, r, g, c, k):
    """C2b: T-uniform lower bound (d odd, T >= d+1): (1/2)[g r^d - 2c - max(k, g r^{d+1} - k)]^+."""
    a_d, a_d1 = g * r**d, g * r ** (d + 1)
    return max(F(0), min((a_d - k) / 2 - c, a_d - a_d1, (a_d - a_d1 + k) / 2 - c))
