"""Growth-aware label allocation for prediction-powered e-process monitoring (Candidate A).

For a context with signal mean ``mu``, proxy ``h`` and residual second moment
``r = E[(Y-h)^2]``, a query at propensity ``q`` gives increment ``X = h + Q (Y-h)/q`` with
``E[X] = mu`` and ``E[X^2] = c + r/q``, ``c = 2*h*mu - h^2``. With the Kelly bet
``lam = min(mu/E[X^2], cap(q))`` and the bounded-bet cap ``cap(q) = 0.5/(M*(2/q - 1))``,
the per-event quadratic log-growth is ``mu*lam - 0.5*E[X^2]*lam^2``. Validity does not
depend on this model: any predictable ``q`` and bet keep the null supermartingale.
"""

from __future__ import annotations

import numpy as np

GRID = 64  # shortcut: 1-D grid search per event, error O(1/GRID); upgrade to closed-form KKT if profiling shows it matters


def growth(mu, h, r, q, bound):
    """Quadratic-approximation log-growth per event at propensity ``q`` (arrays broadcast)."""
    m2 = 2 * h * mu - h**2 + r / q
    cap = 0.5 / (bound * (2.0 / q - 1.0))
    lam = np.clip(mu / np.maximum(m2, 1e-12), 0.0, cap)
    return mu * lam - 0.5 * m2 * lam**2


def allocate(mu, h, r, budget, bound, q_min=0.02):
    """Propensities maximizing ``sum growth - nu * q`` with ``nu`` set so ``sum q = budget``."""
    mu, h, r = (np.asarray(a, float) for a in (mu, h, r))
    qs = np.linspace(q_min, 1.0, GRID)
    g = growth(mu[:, None], h[:, None], r[:, None], qs[None, :], bound)

    def pick(nu):
        return qs[np.argmax(g - nu * qs[None, :], axis=1)]

    lo, hi = 0.0, float(np.max(g / qs[None, :])) + 1.0
    if pick(0.0).sum() <= budget:
        return pick(0.0)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pick(mid).sum() > budget else (lo, mid)
    under, over = pick(hi), pick(lo)  # bang-bang when g is linear in q: split the marginal events
    gap = over.sum() - under.sum()
    t = 0.0 if gap <= 0 else (budget - under.sum()) / gap
    return under + t * (over - under)


def neyman(r, budget, q_min=0.02):
    """Variance-optimal allocation ``q ∝ sqrt(r)`` clipped to ``[q_min, 1]`` with ``sum q ≈ budget``."""
    s = np.sqrt(np.asarray(r, float))
    lo, hi = 0.0, 1e6
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if np.clip(mid * s, q_min, 1).sum() < budget else (lo, mid)
    return np.clip(hi * s, q_min, 1)
