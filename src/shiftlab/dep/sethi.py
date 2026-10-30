"""Binary-chain implementation of Algorithm 1 of Sethi et al. (arXiv:2602.17587v3): sequential Markov chain test.

Null set P = {P : stationary P(state 1) <= r0}, i.e. a(1-r0) <= r0 b with a = P(0->1), b = P(1->0). The statistic
L_t = inf_{P in P} sum_x N_x KL(Qhat(x,.) || P(x,.)) is a 1-D convex problem on the boundary; reject when
L_t >= beta_t = log(1/alpha) + (m-1) psi_t, psi_t = sum_x log(e (1 + N_x/(m-1))), m = 2. Vectorised over paths.
Reimplemented from the paper's pseudo-code; alpha-correctness is the paper's Theorem 4.1 (proof not re-checked here).
"""

from __future__ import annotations

import numpy as np

EPS = 1e-12


def _kl(p, q):
    p = np.clip(p, EPS, 1 - EPS)
    q = np.clip(q, EPS, 1 - EPS)
    return p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))


def statistic(n00, n01, n10, n11, r0: float, iters: int = 40):
    """L_t for count arrays (any shape). Zero if the empirical kernel already lies in the null set."""
    n0, n1 = n00 + n01, n10 + n11
    a_hat = np.where(n0 > 0, n01 / np.maximum(n0, 1), 0.5)
    b_hat = np.where(n1 > 0, n10 / np.maximum(n1, 1), 0.5)
    inside = a_hat * (1 - r0) <= r0 * b_hat
    lo = np.full(a_hat.shape, 1e-9)
    hi = np.full(a_hat.shape, min(1.0, r0 / (1 - r0)) - 1e-9)

    def f(a):
        b = a * (1 - r0) / r0
        return n0 * _kl(a_hat, a) + n1 * _kl(b_hat, b)

    for _ in range(iters):  # ternary search of a convex function
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        left = f(m1) < f(m2)
        hi = np.where(left, m2, hi)
        lo = np.where(left, lo, m1)
    return np.where(inside, 0.0, f(0.5 * (lo + hi)))


def threshold(n0, n1, alpha: float):
    psi = np.log(np.e * (1 + n0)) + np.log(np.e * (1 + n1))
    return np.log(1 / alpha) + psi
