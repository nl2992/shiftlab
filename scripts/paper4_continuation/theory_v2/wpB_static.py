"""WP B: count-based exact Lagrangian DP for the STATIC alternative (t01 = t10 = 0).

Worlds A0 (labels Ber(e0)), N (Ber(1/2)), A1 (Ber(e1)) with root weights (W0, WN, W1) =
((1-pi), lam, pi).  Because theta is static, the state is (t, pending release times, budget b,
released count m, released ones s); masses of a released sequence depend only on (m, s).
All values are mass-weighted (unnormalised).  Matches wpB_lib / the repo game conventions.
"""

from __future__ import annotations

from fractions import Fraction as F
from functools import lru_cache
from itertools import product


def static_solve(T, B, d, e0, e1, c, k, W0, WN, W1, greedy=False, tie="cont", exact=False):
    conv = F if exact else float
    e0, e1, c, k, W0, WN, W1 = map(conv, (e0, e1, c, k, W0, WN, W1))
    one, half = conv(1), conv(1) / 2

    def masses(m, s):
        return (W0 * e0 ** s * (one - e0) ** (m - s), WN * half ** m, W1 * e1 ** s * (one - e1) ** (m - s))

    def releases(t, pend):
        """pend: tuple of release times (sorted). Returns (released?, remaining)."""
        if pend and pend[0] <= t:
            return True, pend[1:]
        return False, pend

    @lru_cache(maxsize=None)
    def post(t, old, pend, b, m, s):
        a0, _, a1 = masses(m, s)
        A = a0 + a1
        best = None
        for a in (0, 1):
            for q in ((0, 1) if b else (0,)):
                v = (a0 * e0 + a1 * e1 if a == 0 else a0 * (one - e0) + a1 * (one - e1)) + c * q * A + k * (a != old) * A
                if t < T:
                    p2 = pend + ((t + d,) if q else ())
                    rel, p3 = releases(t + 1, p2)
                    if rel:
                        v += post(t + 1, a, p3, b - q, m + 1, s) + post(t + 1, a, p3, b - q, m + 1, s + 1)
                    else:
                        v += post(t + 1, a, p3, b - q, m, s)
                if best is None or v < best:
                    best = v
        return best

    def promote(t, pend, b, m, s, q):
        a0, n, a1 = masses(m, s)
        A = a0 + a1
        v = a0 * (one - e0) + a1 * (one - e1) + c * q * A + k * A
        if t < T:
            p2 = pend + ((t + d,) if q else ())
            rel, p3 = releases(t + 1, p2)
            if rel:
                v += post(t + 1, 1, p3, b - q, m + 1, s) + post(t + 1, 1, p3, b - q, m + 1, s + 1)
            else:
                v += post(t + 1, 1, p3, b - q, m, s)
        return v + n

    plan = {}
    Dtab = {}

    @lru_cache(maxsize=None)
    def J(t, pend, b, m, s):
        a0, n, a1 = masses(m, s)
        A = a0 + a1
        qopts = (1,) if (greedy and b) else ((0, 1) if b else (0,))
        stop = [(promote(t, pend, b, m, s, q), (1, q)) for q in qopts]
        cont = []
        for q in qopts:
            v = a0 * e0 + a1 * e1 + c * q * A
            if t < T:
                p2 = pend + ((t + d,) if q else ())
                rel, p3 = releases(t + 1, p2)
                if rel:
                    v += J(t + 1, p3, b - q, m + 1, s) + J(t + 1, p3, b - q, m + 1, s + 1)
                else:
                    v += J(t + 1, p3, b - q, m, s)
            cont.append((v, (0, q)))
        bs, bc = min(stop), min(cont)
        Dtab[(t, pend, b, m, s)] = (bs[0] - bc[0]) / a1 if a1 else None
        tol = 0 if exact else 1e-12 * (1 + abs(bc[0]))
        if bs[0] < bc[0] - tol or (tie == "promote" and bs[0] <= bc[0] + tol):
            choice = bs
        else:
            choice = bc
        # among equal-value query choices prefer no query
        plan[(t, pend, b, m, s)] = choice[1]
        return choice[0]

    val = J(1, (), B, 0, 0)
    return val, plan, Dtab


def run_z_static(plan, T, B, d, z):
    pend, b, m, s, j = (), B, 0, 0, 0
    pendlab = []
    for t in range(1, T + 1):
        if pend and pend[0] <= t:
            pend = pend[1:]
            y = pendlab.pop(0)
            m += 1
            s += y
        a, q = plan[(t, pend, b, m, s)]
        if a:
            return 1
        if q:
            pend = pend + (t + d,)
            pendlab.append(z[j])
            j += 1
            b -= 1
    return 0


def z_monotone_static(plan, T, B, d):
    n = min(B, T)
    g = {z: run_z_static(plan, T, B, d, z) for z in product((0, 1), repeat=n)}
    for z, v in g.items():
        for i in range(n):
            if z[i] == 0:
                z2 = z[:i] + (1,) + z[i + 1:]
                if v > g[z2]:
                    return False, (z, z2)
    return True, None


def rc_static(plan, T, B, d, e0, e1, W0, W1, exact=True):
    """Exact IID risk R and alternative pre-promotion promotion prob (diagnostic)."""
    conv = F if exact else float
    n = min(B, T)
    R = conv(0)
    for z in product((0, 1), repeat=n):
        R += conv(run_z_static(plan, T, B, d, z)) / 2 ** n
    return R
