"""Belief-grid value tables and query value-of-information (VOI) with delay and pending queue.

V[t, a, g]: relative expected cost-to-go from the start of round t (labels of round t already
absorbed) with deployed action a and P(state=H)=pi_g, under optimal switching and a *background*
label-arrival rate rho per round (labels still to come from future queries). Costs are relative
to the incumbent (action 0 has loss 0, action 1 has loss -E[Z]); switching costs k.
QVOI of a new query at t with m pending ones: label lands at tau = t + d; compare
E[V(tau, a, post(m pending))] - E[V(tau, a, post(m+1))] (exact enumeration of outcome sequences).
"""

from __future__ import annotations

from functools import cache
from itertools import product

import numpy as np

from .belief import Model

G = 41
GRID = np.linspace(0.0, 1.0, G)
RHO_LEVELS = np.array([0.0, 0.004, 0.01, 0.02, 0.04, 0.07, 0.12, 0.2, 0.35, 0.6])
_CACHE: dict = {}


def rho_level(rho: float) -> float:
    return float(RHO_LEVELS[np.argmin(np.abs(RHO_LEVELS - rho))])


def _interp_idx(x):
    x = np.clip(x, 0.0, 1.0) * (G - 1)
    i = np.minimum(x.astype(int), G - 2)
    return i, x - i


def lerp(v, i, f):
    return v[i] * (1 - f) + v[i + 1] * f


def build_tables(mod: Model, T: int, k: float, rho: float, horizon: int | None = None):
    """Returns (V[T+2,2,G], Q[T+1,2,G]); Q[t,a',g] excludes the switching fee.

    horizon: if given, only that many future rounds count after the evaluation round (ablation
    'no continuation': horizon=1 is the myopic one-round value).
    """
    key = (mod.a, mod.b, mod.P.tobytes(), round(mod.r, 3), T, k, rho, horizon)
    if key in _CACHE:
        return _CACHE[key]
    gL, gH = mod.gain
    g1 = gL + (gH - gL) * GRID  # E[Z] per round at each belief
    cost = np.stack([np.zeros(G), -g1])  # relative loss of a'=0/1
    prop = mod.pinf + (GRID - mod.pinf) * mod.lam
    ip, fp = _interp_idx(prop)
    PH, PL = mod.P[1], mod.P[0]
    m_o = np.stack([prop * PH[o] + (1 - prop) * PL[o] for o in range(len(PH))])  # (O,G)
    po = [
        np.where(m_o[o] > 1e-300, prop * PH[o] / np.maximum(m_o[o], 1e-300), 0.0)
        for o in range(len(PH))
    ]
    io = [_interp_idx(p) for p in po]
    V = np.zeros((T + 2, 2, G))
    Q = np.zeros((T + 1, 2, G))
    t_lo = 1 if horizon is None else max(1, T - horizon + 1)
    for t in range(T, 0, -1):
        for a2 in (0, 1):
            en = 0.0
            if t < T and t >= t_lo:
                nxt = V[t + 1, a2]
                en = (1 - rho) * lerp(nxt, ip, fp) + rho * sum(
                    m_o[o] * lerp(nxt, *io[o]) for o in range(len(PH))
                )
            Q[t, a2] = cost[a2] + en
        V[t, 0] = np.minimum(Q[t, 0], Q[t, 1] + k)
        V[t, 1] = np.minimum(Q[t, 1], Q[t, 0] + k)
    _CACHE[key] = (V, Q)
    if len(_CACHE) > 4000:
        _CACHE.clear()
    return V, Q


def myopic_V(mod: Model, k: float):
    """Value of a single decision round ignoring everything after it (ablation)."""
    gL, gH = mod.gain
    g1 = gL + (gH - gL) * GRID
    V = np.zeros((2, G))
    V[0] = np.minimum(0.0, -g1 + k)
    V[1] = np.minimum(-g1, k)
    return V


@cache
def _seqs(O: int, m: int):
    s = (
        np.array(list(product(range(O), repeat=m)), int).reshape(-1, m)
        if m
        else np.zeros((1, 0), int)
    )
    C = np.zeros((len(s), O))
    for o in range(O):
        C[:, o] = (s == o).sum(1)
    return C


@cache
def _binom(m: int):
    from scipy.special import comb

    j = np.arange(m + 1)
    return np.stack([j, m - j], 1).astype(float), comb(m, j)


def _extend(pi, mod: Model, n: int):
    """Given prior P(H)=pi (M,), the n-draw outcome sets: cond prob (M,K) and posterior (M,K)."""
    pi = np.atleast_1d(np.asarray(pi, float))
    O = len(mod.Zo)
    if O == 2:
        C, coef = _binom(n)
    else:
        C, coef = _seqs(O, n), 1.0
    lH = np.exp(C @ np.log(np.maximum(mod.P[1], 1e-300))) * coef
    lL = np.exp(C @ np.log(np.maximum(mod.P[0], 1e-300))) * coef
    cond = pi[:, None] * lH[None] + (1 - pi[:, None]) * lL[None]
    post = np.where(cond > 1e-300, pi[:, None] * lH[None] / np.maximum(cond, 1e-300), pi[:, None])
    return cond, post


def _V_at(Vrow, pi):
    i, f = _interp_idx(np.asarray(pi, float))
    return lerp(Vrow, i, f)


def _cap_pending(O, m, n):
    while m > 0 and ((m + n + 1) if O == 2 else O ** (m + n)) > (60 if O == 2 else 1024):
        m -= 1
    return m


def voi(
    mod: Model,
    V_tab,
    t: int,
    tau: int,
    dep: int,
    pi_t: float,
    m_pend: int,
    T: int,
    use_pending: bool = True,
    myopic: bool = False,
    k: float = 0.0,
    ns=(1, 2, 3, 5, 8, 12, 20),
    rem: int = 10**9,
) -> float:
    """KG*-style value per label: max_n [E V(m pending) - E V(m+n pending)] / n, labels landing
    at tau = t + d (0 if tau > T). n=1 alone is the myopic one-step VOI."""
    if tau > T:
        return 0.0
    O = len(mod.Zo)
    n_ok = [n for n in ns if n <= rem and (O == 2 or O**n <= 256)] or [1]
    mcap = _cap_pending(O, m_pend, max(n_ok)) if use_pending else 0
    n_ = max(tau - t, 0)
    pi_tau = mod.pinf + (pi_t - mod.pinf) * mod.lam**n_
    Vrow = myopic_V(mod, k)[dep] if myopic else V_tab[tau, dep]
    j0, p0 = _extend(pi_tau, mod, mcap)
    j0, p0 = j0[0], p0[0]
    base = float(np.sum(j0 * _V_at(Vrow, p0)))
    best = -np.inf
    for n in n_ok:
        cond, post = _extend(p0, mod, n)
        best = max(best, (base - float(np.sum(j0[:, None] * cond * _V_at(Vrow, post)))) / n)
    return best


def flip_prob(
    mod: Model,
    Q_tab,
    t: int,
    tau: int,
    dep: int,
    pi_t: float,
    m_pend: int,
    T: int,
    k: float,
    n_batch: int = 1,
    use_pending: bool = True,
) -> float:
    """P(n_batch extra labels change the greedy action at tau vs deciding without them)."""
    if tau > T:
        return 0.0
    O = len(mod.Zo)
    mcap = _cap_pending(O, m_pend, n_batch) if use_pending else 0
    n_ = max(tau - t, 0)
    pi_tau = mod.pinf + (pi_t - mod.pinf) * mod.lam**n_
    j0, p0 = _extend(pi_tau, mod, mcap)
    j0, p0 = j0[0], p0[0]
    sw = (k * (dep != 0), k * (dep != 1))

    def dec(p):
        return (_V_at(Q_tab[tau, 1], p) + sw[1] < _V_at(Q_tab[tau, 0], p) + sw[0]).astype(int)

    d0 = dec(p0)
    cond, post = _extend(p0, mod, n_batch)
    return float(np.sum(j0[:, None] * cond * (dec(post) != d0[:, None])))


def greedy_q(tabs, ws, t: int, pis, dep: int, k: float, extra_sw: float = 0.0):
    """Weighted Q over hypotheses; returns (action, q0+fee, q1+fee)."""
    q = np.zeros(2)
    for Qtab, w, pi in zip(tabs, ws, pis, strict=True):
        i, f = _interp_idx(np.asarray(pi, float))
        q[0] += w * lerp(Qtab[t, 0], i, f)
        q[1] += w * lerp(Qtab[t, 1], i, f)
    q[0] += (k + extra_sw) * (dep != 0)
    q[1] += (k + extra_sw) * (dep != 1)
    return int(q[1] < q[0]), q
