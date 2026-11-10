"""Certifiability frontier for hold-for-h payback certificates (theory helpers).

Setting (see 03B/06 docs).  Labels Z in {-1,+1} (Rademacher family inside [-1,1]) with mean mu_s;
class C(v,J,hd); decision at tau sees requests s <= tau-d only; at most B requested labels; a
certifier is alpha-valid if P(certify and sum_{j<h} mu_{tau+j} <= k) <= alpha for every path in
the class.  gamma := L - k/h - irreducible_slack  is the "excess gap" of a world with constant
mean L.  gamma_lb : necessary excess gap for power 1-beta (any valid certifier, pure drift class).
gamma_ub : excess gap sufficient for the Hoeffding window certificate (single batch).
"""

from __future__ import annotations

import math

import numpy as np

from .envelope import Envelope


def kl_rad(mu_p: float, mu_q: float) -> float:
    """KL( Rad(mu_p) || Rad(mu_q) ) in nats for +/-1 labels with means mu."""
    a, b = (1 + mu_p) / 2, (1 + mu_q) / 2
    if not (0 < b < 1):
        return math.inf
    out = 0.0
    if a > 0:
        out += a * math.log(a / b)
    if a < 1:
        out += (1 - a) * math.log((1 - a) / (1 - b))
    return out


def kl_ber(p: float, q: float) -> float:
    out = 0.0
    if p > 0:
        out += p * math.log(p / q)
    if p < 1:
        out += (1 - p) * math.log((1 - p) / (1 - q))
    return out


def kappa(alpha: float, beta: float) -> float:
    """Data-processing price kl(1-beta || alpha) of valid-at-alpha, power-1-beta certification."""
    return kl_ber(1 - beta, alpha)


def total_kl(gamma: float, base: float, v: float, n_labels: int) -> float:
    """KL(P+||P-) of the B most recent labels: label m back differs by (gamma - v m)_+, L=gamma+base."""
    L = gamma + base
    if v == 0:
        return n_labels * kl_rad(L, L - gamma)
    m = np.arange(min(n_labels, math.ceil(gamma / v) + 1))
    dlt = np.maximum(gamma - v * m, 0.0)
    dlt = dlt[dlt > 0]
    q = L - dlt
    a, b = (1 + L) / 2, (1 + q) / 2
    return float(np.sum(a * np.log(a / b) + (1 - a) * np.log((1 - a) / (1 - b))))


def gamma_lb(B: int, v: float, base: float, alpha: float, beta: float) -> float:
    """Smallest gamma at which the constructed pair is KL-distinguishable by B labels.
    Returns inf if L=gamma+base would exceed 1 before that happens."""
    kap = kappa(alpha, beta)
    hi = 1.0 - base - 1e-12
    if hi <= 0 or total_kl(hi, base, v, B) < kap:
        return math.inf
    lo = 0.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if total_kl(mid, base, v, B) >= kap:
            hi = mid
        else:
            lo = mid
    return hi


def window_bias(env: Envelope, n: int) -> float:
    """Average over a consecutive window of n labels (ages 0..n-1 before the newest) of drop(age)."""
    return sum(env.drop(i) for i in range(n)) / n


def gamma_ub(B: int, env: Envelope, alpha: float, beta: float) -> tuple[float, int]:
    """min over window size n<=B of Hoeffding(alpha)+Hoeffding(beta)+window bias; returns (gamma, n)."""
    n = np.arange(1, B + 1, dtype=float)
    if env.jump == env.v:
        bias = env.v * (n - 1) / 2
    else:
        idx = np.arange(B)
        k_ = np.ceil(idx / env.hd)
        dr = env.jump * k_ + env.v * (idx - k_)
        bias = np.cumsum(dr) / n
    c = math.sqrt(2 * math.log(1 / alpha)) + math.sqrt(2 * math.log(1 / beta))
    val = c / np.sqrt(n) + bias
    i = int(np.argmin(val))
    return float(val[i]), i + 1


def saturation_budget(v: float, alpha: float, beta: float) -> float:
    """Continuous minimiser n* of sqrt(2(la+lb)... ) bias trade-off; budgets above this do not help."""
    c = math.sqrt(2 * math.log(1 / alpha)) + math.sqrt(2 * math.log(1 / beta))
    return (c / v) ** (2 / 3) if v > 0 else math.inf


def exact_np_gamma(B: int, v: float, base: float, alpha: float, beta: float) -> float:
    """Exact Neyman-Pearson (randomised) minimal gamma for the constructed pair, B<=20 labels.
    This is a valid (tighter) lower bound on the minimax excess gap than gamma_lb."""
    if B > 20:
        raise ValueError("enumeration limited to B<=20")

    def power(gamma: float) -> float:
        L = gamma + base
        if L >= 1:
            return 1.0
        mus_p = np.full(B, L)
        mus_q = np.array([L - max(0.0, gamma - v * m) for m in range(B)])
        signs = ((np.arange(2**B)[:, None] >> np.arange(B)) & 1).astype(float) * 2 - 1

        def logp(mu):
            return np.sum(np.log((1 + signs * mu) / 2), axis=1)

        lp, lq = logp(mus_p), logp(mus_q)
        pp, pq = np.exp(lp), np.exp(lq)
        order = np.argsort(-(lp - lq), kind="stable")
        cum_q = np.cumsum(pq[order])
        cum_p = np.cumsum(pp[order])
        idx = int(np.searchsorted(cum_q, alpha, side="right"))
        pw = cum_p[idx - 1] if idx > 0 else 0.0
        used = cum_q[idx - 1] if idx > 0 else 0.0
        if idx < len(order) and pq[order[idx]] > 0:
            pw += (alpha - used) / pq[order[idx]] * pp[order[idx]]
        return float(pw)

    if power(1 - base - 1e-9) < 1 - beta:
        return math.inf
    lo, hi = 0.0, 1 - base - 1e-9
    for _ in range(50):
        mid = (lo + hi) / 2
        if power(mid) >= 1 - beta:
            hi = mid
        else:
            lo = mid
    return hi
