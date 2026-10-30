"""Registered cost-null development screen; composition candidates, not new theorems.

Vectorizes independent configurations and paths. Bets depend on released history
only; the cap uses a context-independent proxy bound and propensity floor.
All event factors are released in order at a fixed positive delay. Hard query
exhaustion sets subsequent factors to one, rather than pretending q remains positive.
"""

from dataclasses import asdict, dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class Combination:
    guidance: float
    gamma: float
    cap: float
    allocation: str
    restart: bool


def combinations():
    # Every parameter is active; zero/one guidance are the matched cost/Brier parents.
    return [
        Combination(*v)
        for v in product(
            (0.0, 0.25, 0.5, 0.75, 1.0),
            (0.8, 0.9, 0.95, 0.98, 0.995, 1.0),
            (0.25, 0.5, 0.75),
            ("uniform", "uncertainty", "boundary"),
            (False, True),
        )
    ]


def config_dicts():
    return [dict(id=f"R1_{i:04d}", **asdict(c)) for i, c in enumerate(combinations())]


def make_world(kind, *, paths, horizon, seed, onset=None):
    """Finite-support iid contexts with exact nominal moments (no estimated oracle baseline).

    Truth arrays are returned for evaluator scoring only. Learner arrays contain
    predictions and outcomes whose consumption is controlled by `screen`.
    """
    onset = horizon // 3 if onset is None else onset
    rng = np.random.default_rng(seed)
    context = rng.integers(0, 4, (paths, horizon))
    p0 = np.array([0.1, 0.3, 0.6, 0.9])
    p = p0[context]
    truth = p.copy()
    active = np.arange(horizon) >= onset
    if kind in ("abrupt", "late", "guidance_failure", "recurring", "small"):
        if kind == "late":
            active = np.arange(horizon) >= 3 * horizon // 4
        elif kind == "recurring":
            active = (np.arange(horizon) >= onset) & (
                (np.arange(horizon) // (horizon // 6)) % 2 == 0
            )
        amount = 0.25 if kind == "small" else 0.6
        # Degrade every context in the direction increasing the fixed action's cost.
        alt = np.clip(p + np.where(p < 1 / 6, amount, -amount), 0.0, 1.0)
        truth = np.where(active, alt, p)
    elif kind not in ("null", "nuisance"):
        raise ValueError(kind)
    y = (rng.random(p.shape) < truth).astype(float)
    act = p >= 1 / 6
    loss = np.where(act, (1 - y) / 5, y)
    proxy = np.where(act, (1 - p) / 5, p)
    brier = (p - y) ** 2
    proxy_brier = p * (1 - p)
    # Failure control corrupts auxiliary predictions only, not the cost task.
    if kind == "guidance_failure":
        proxy_brier = np.where(active, 1 - proxy_brier, proxy_brier)
    if kind == "nuisance":
        # Observable nuisance has no effect on actions, query features or outcomes.
        nuisance = rng.normal(size=p.shape) + 5 * active
    else:
        nuisance = rng.normal(size=p.shape)
    r0 = float(np.where(p0 >= 1 / 6, (1 - p0) / 5, p0).mean())
    return {
        "loss": loss,
        "proxy": proxy,
        "brier": brier,
        "proxy_brier": proxy_brier,
        "score": p,
        "r0": r0,
        "b0": float(np.mean(p0 * (1 - p0))),
        "proxy_max": 1 / 6,
        "bproxy_max": 1.0 if kind == "guidance_failure" else 0.25,
        "nuisance": nuisance,
        "evaluator": {
            "harm": np.where(act, (1 - truth) / 5, truth) - np.where(act, (1 - p) / 5, p),
            "active": np.broadcast_to(active, p.shape),
            "kind": kind,
        },
    }


def screen(
    stream,
    configs,
    *,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    tolerance=0.0,
    alpha=0.05,
    return_wealth=False,
):
    """Evaluate configurations using the same uniform query randomness.

    Returns per-config/path outcomes. Cost here measures monitoring performance:
    cumulative positive evaluator expected excess cost until first alarm. It is
    NOT net switching cost. That requires the separate frozen-policy replay.
    """
    if not configs or not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1:
        raise ValueError("require configs, positive query rate/delay and alpha in (0,1)")
    loss = np.asarray(stream["loss"])
    if loss.ndim != 2 or np.any((loss < 0) | (loss > 1)):
        raise ValueError("loss must be paths x time in [0,1]")
    S, T = loss.shape
    budget = int(frac * T) if budget is None else budget
    if not 0 <= budget <= T or tolerance < 0:
        raise ValueError("invalid budget/tolerance")
    C = len(configs)
    for c in configs:
        if not 0 <= c.guidance <= 1 or not 0 < c.gamma <= 1 or not 0 < c.cap < 1:
            raise ValueError("invalid guidance/gamma/cap")
        if c.allocation not in ("uniform", "uncertainty", "boundary"):
            raise ValueError("unknown allocation")
    gam = np.array([c.gamma for c in configs])[:, None]
    cap = np.array([c.cap for c in configs])[:, None]
    guide = np.array([c.guidance for c in configs])[:, None]
    alloc = np.array([c.allocation for c in configs])[:, None]
    restart = np.array([c.restart for c in configs])[:, None]
    qfloor = np.where(alloc == "uniform", frac, frac / 4)
    bc = stream["proxy_max"] * (1 / qfloor - 1) + stream["r0"] + tolerance
    bb = stream["bproxy_max"] * (1 / qfloor - 1) + stream["b0"]
    hc, hb = cap / bc, cap / bb
    U = np.random.default_rng(seed).random((S, T))
    # Ring buffer stores hidden event factors; only the due slot updates the learner.
    X, Y, F = (np.zeros((delay + 1, C, S)) for _ in range(3))
    m1, m2, b1, b2 = (np.zeros((C, S)) for _ in range(4))
    wealth, mix_wealth = np.ones((C, S)), np.zeros((C, S))
    spent = np.zeros((C, S), dtype=int)
    first = np.full((C, S), T, dtype=int)
    maxlog = np.zeros((C, S))
    history = np.zeros((C, S, T)) if return_wealth else None
    starts = sorted({0, T // 4, T // 2, 3 * T // 4})
    weights = {t: 1 / len(starts) for t in starts}
    future_mass = 1.0
    threshold = 1 / alpha
    for t in range(T):
        slot = t % (delay + 1)
        if t >= delay:
            xc, xb = X[slot], Y[slot]
            m1, m2 = gam * m1 + xc, gam * m2 + xc * xc
            b1, b2 = gam * b1 + xb, gam * b2 + xb * xb
            factor = F[slot]
            wealth *= factor
            mix_wealth *= factor
        # Restart capital enters before the next generated event factor, delayed
        # exactly as the first factor of that event. Add at its release index.
        start_event = t - delay
        if start_event in weights:
            w = weights[start_event]
            mix_wealth += w * F[slot]
            future_mass -= w
        visible = np.where(restart, mix_wealth + max(future_mass, 0), wealth)
        hit = (first == T) & (visible >= threshold)
        first[hit] = t
        logs = np.log(np.maximum(visible, 1e-300))
        maxlog = np.maximum(maxlog, logs)
        if history is not None:
            history[:, :, t] = logs
        # New bets use only factors released by t. They do not see current loss.
        relc = np.clip(np.maximum(m1, 0) / np.maximum(m2, 1e-12) / hc, 0, 1)
        relb = np.clip(np.maximum(b1, 0) / np.maximum(b2, 1e-12) / hb, 0, 1)
        lam = ((1 - guide) * relc + guide * relb) * hc
        p = stream["score"][:, t]
        uncertainty = np.clip(4 * p * (1 - p), 0, 1)
        boundary = np.exp(-12 * np.abs(p - 1 / 6))
        q = np.where(
            alloc == "uniform",
            frac,
            frac / 4 + 1.5 * frac * np.where(alloc == "uncertainty", uncertainty, boundary),
        )
        q = np.minimum(q, 1)
        available = spent < budget
        queried = (U[:, t] < q) & available
        spent += queried
        xc = (
            stream["proxy"][:, t]
            + queried / q * (loss[:, t] - stream["proxy"][:, t])
            - stream["r0"]
            - tolerance
        )
        xb = (
            stream["proxy_brier"][:, t]
            + queried / q * (stream["brier"][:, t] - stream["proxy_brier"][:, t])
            - stream["b0"]
        )
        xc, xb = np.where(available, xc, 0), np.where(available, xb, 0)
        factor = 1 + lam * xc
        if np.any(factor <= 0) or not np.all(np.isfinite(factor)):
            raise ArithmeticError("invalid betting factor")
        due = (t + delay) % (delay + 1)
        X[due], Y[due], F[due] = xc, xb, factor
    result = {"first": first, "labels": spent, "maxlog": maxlog}
    if history is not None:
        result["logwealth"] = history
    return result
