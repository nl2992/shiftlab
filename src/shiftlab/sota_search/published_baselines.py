"""Source-audited components; full-paper reproductions are separately labelled.

Active RCPS: Xu et al., arXiv:2406.10490, author code revision
a67f85d603df2bb3e32ef007f445191923ebd990, IwUpperMartingale.py.
With rho=1-loss, theta=1-mu, cv=1-proxy, its PartialIwUpper
increment is exactly proxy + Q/q*(loss-proxy) - mu. Its FTL bet
is sum(x)/(sum(x)+sum(x*x)), clipped at half the reciprocal
of the worst negative increment. This adapter fixes a single risk target;
it does not reproduce RCPS grid inversion or the author's learned query policy.
"""

import numpy as np


def active_rcps_cost(
    stream,
    *,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    tolerance=0.0,
    alpha=0.05,
    return_wealth=False,
):
    S, T = stream["loss"].shape
    if not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1:
        raise ValueError("invalid frac, delay or alpha")
    budget = int(frac * T) if budget is None else budget
    if not 0 <= budget <= T:
        raise ValueError("invalid budget")
    mu = stream["r0"] + tolerance
    hi = 0.5 / (stream["proxy_max"] * (1 / frac - 1) + mu)
    U = np.random.default_rng(seed).random((S, T))
    ring = np.zeros((delay + 1, S))
    factor_ring = np.ones_like(ring)
    sx, sx2, lw = np.zeros(S), np.zeros(S), np.zeros(S)
    spent = np.zeros(S, dtype=int)
    first = np.full(S, T, dtype=int)
    maxlog = np.zeros(S)
    history = np.zeros((S, T)) if return_wealth else None
    for t in range(T):
        slot = t % (delay + 1)
        if t >= delay:
            sx += ring[slot]
            sx2 += ring[slot] ** 2
            lw += np.log(factor_ring[slot])
        first[(first == T) & (lw >= np.log(1 / alpha))] = t
        maxlog = np.maximum(maxlog, lw)
        if history is not None:
            history[:, t] = lw
        denom = sx + sx2
        lam = np.clip(np.divide(sx, denom, out=np.zeros_like(sx), where=denom != 0), 0, hi)
        available = spent < budget
        queried = (U[:, t] < frac) & available
        spent += queried
        proxy = stream["proxy"][:, t]
        x = np.where(available, proxy + queried / frac * (stream["loss"][:, t] - proxy) - mu, 0)
        due = (t + delay) % (delay + 1)
        ring[due] = x
        factor_ring[due] = 1 + lam * x
    result = {"first": first, "labels": spent, "maxlog": maxlog}
    if history is not None:
        result["logwealth"] = history
    return result
