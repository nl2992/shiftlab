"""Paired-benefit control compositions: known betting/certification ingredients.

The certificate tests E[L_inc-L_cand | full event past] <= margin. Queries
are predictable with respect to available features, with IPW correction and a
global propensity bound. A certificate is not a guarantee of future benefit
under reversal. Frozen candidate, common outcome, one promotion per path.
"""

from dataclasses import dataclass
from itertools import product

import numpy as np

from .combination_screen import make_world


@dataclass(frozen=True)
class PairedConfig:
    mode: str
    allocation: str
    gamma: float
    cap: float
    restart: bool
    pace: str
    bet: str


def paired_configurations():
    return [
        PairedConfig(*v)
        for v in product(
            ("direct", "and_alarm", "after_alarm"),
            ("uniform", "uncertainty", "disagreement"),
            (0.9, 0.98, 1.0),
            (0.5, 0.75),
            (False, True),
            ("none", "remaining", "reserve"),
            ("kelly", "ftl"),
        )
    ]


def paired_world(kind, *, paths, horizon, seed):
    """Frozen actions and evaluator-only truth, with same observed binary outcome."""
    mapping = {
        "useful": "abrupt",
        "late": "late",
        "small": "small",
        "reversal": "recurring",
        "harmful": "null",
        "tie": "null",
        "identical": "abrupt",
        "useful_initial": "abrupt",
        "harmful_after_shift": "abrupt",
    }
    if kind not in mapping:
        raise ValueError("unknown paired world")
    s = make_world(mapping[kind], paths=paths, horizon=horizon, seed=seed)
    rng = np.random.default_rng(seed + 400000)
    p = s["score"]
    onset = horizon // 3
    alt = np.clip(p + np.where(p < 1 / 6, 0.6, -0.6), 0, 1)
    if kind == "harmful_after_shift":
        active = np.arange(horizon) >= onset
        damaged = np.clip(p + np.where(p < 1 / 6, 0.15, -0.15), 0, 1)
        truth = np.where(active, damaged, p)
    elif kind == "useful_initial":
        truth = alt
    elif kind == "tie":
        truth = np.full(p.shape, 1 / 6)
    elif kind == "harmful":
        truth = p
    else:
        active = np.arange(horizon) >= (3 * horizon // 4 if kind == "late" else onset)
        if kind == "reversal":
            active = (np.arange(horizon) >= onset) & (np.arange(horizon) < 2 * onset)
        shift = np.clip(
            p
            + np.where(
                p < 1 / 6, 0.25 if kind == "small" else 0.6, -0.25 if kind == "small" else -0.6
            ),
            0,
            1,
        )
        truth = np.where(active, shift, p)
    y = rng.random(p.shape) < truth
    cand = p if kind == "identical" else alt
    if kind == "harmful_after_shift":
        cand = np.where(p >= 1 / 6, 0.01, 0.99)
    a0, a1 = p >= 1 / 6, cand >= 1 / 6
    loss0 = np.where(a0, (1 - y) / 5, y)
    loss1 = np.where(a1, (1 - y) / 5, y)
    s.update(
        loss=loss0,
        candidate_loss=loss1,
        disagree=a0 != a1,
        candidate_score=cand,
        proxy=np.where(a0, (1 - p) / 5, p),
        brier=(p - y) ** 2,
        proxy_brier=p * (1 - p),
    )
    s["r0"] = float(1 / 6) if kind == "tie" else s["r0"]
    if kind == "useful_initial":
        grid = np.array([0.1, 0.3, 0.6, 0.9])
        alt_grid = np.clip(grid + np.where(grid < 1 / 6, 0.6, -0.6), 0, 1)
        s["r0"] = float(np.mean(np.where(grid >= 1 / 6, (1 - alt_grid) / 5, alt_grid)))
    s["evaluator"] = {
        "kind": kind,
        "mean_gain": np.where(a0, (1 - truth) / 5, truth) - np.where(a1, (1 - truth) / 5, truth),
    }
    return s


def paired_screen(
    stream,
    configs,
    *,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    alpha=0.05,
    margin=0.01,
    query_cost=0.001,
    switch_cost=1.0,
    return_wealth=False,
    skip_known_zero=False,
):
    """One-switch control with delayed paired IPW certificate and optional alarm gate.

    Cost/FTL learning is separate from the fixed maximum-stake constraint.
    Post-alarm mode seals factor=1 for every request issued before alarm, so
    unreleased pre-trigger labels cannot leak into fresh certification.
    """
    if not configs or not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1 or margin < 0:
        raise ValueError("invalid configuration or feedback parameters")
    l0, l1 = np.asarray(stream["loss"]), np.asarray(stream["candidate_loss"])
    if l0.shape != l1.shape or l0.ndim != 2 or np.any((l0 < 0) | (l0 > 1) | (l1 < 0) | (l1 > 1)):
        raise ValueError("paired costs must share shape and range [0,1]")
    S, T = l0.shape
    C = len(configs)
    B = int(frac * T) if budget is None else budget
    if not 0 <= B <= T:
        raise ValueError("invalid hard budget")
    mode = np.array([c.mode for c in configs])[:, None]
    alloc = np.array([c.allocation for c in configs])[:, None]
    pace = np.array([c.pace for c in configs])[:, None]
    bet = np.array([c.bet for c in configs])[:, None]
    gamma = np.array([c.gamma for c in configs])[:, None]
    cap = np.array([c.cap for c in configs])[:, None]
    restart = np.array([c.restart for c in configs])[:, None]
    if np.any(~np.isin(mode, ["direct", "and_alarm", "after_alarm"])) or np.any(
        ~np.isin(alloc, ["uniform", "uncertainty", "disagreement"])
    ):
        raise ValueError("unknown control/allocation")
    if skip_known_zero:
        if np.any(mode != "direct"):
            raise ValueError(
                "known-zero query removal is only valid for direct paired control here"
            )
        if np.any((~stream["disagree"]) & (l0 != l1)):
            raise ValueError("declared agreement does not have identical paired losses")
    if np.any(~np.isin(pace, ["none", "remaining", "reserve"])) or np.any(
        ~np.isin(bet, ["kelly", "ftl"])
    ):
        raise ValueError("unknown pace/bet")
    if np.any((gamma <= 0) | (gamma > 1) | (cap <= 0) | (cap >= 1)):
        raise ValueError("invalid gamma/cap")
    floor = np.where((alloc == "uniform") & (pace == "none"), frac, frac / 4)
    hi = cap / (1 / floor + margin)
    hc = cap / (stream["proxy_max"] * (1 / floor - 1) + stream["r0"])
    m1, m2, c1, c2 = (np.zeros((C, S)) for _ in range(4))
    X, Y, F, G = (np.zeros((delay + 1, C, S)) for _ in range(4))
    cert, cost, mixture = np.ones((C, S)), np.ones((C, S)), np.zeros((C, S))
    spent = np.zeros((C, S), dtype=int)
    first = np.full((C, S), T, dtype=int)
    cost_alarm = np.full((C, S), T, dtype=int)
    labels_at = np.zeros((C, S), dtype=int)
    U = np.random.default_rng(seed).random((S, T))
    weights = {t: 0.25 for t in (0, T // 4, T // 2, 3 * T // 4)}
    tail = 1.0
    history = np.zeros((C, S, T)) if return_wealth else None
    for t in range(T):
        slot = t % (delay + 1)
        if t >= delay:
            m1 = gamma * m1 + X[slot]
            m2 = gamma * m2 + X[slot] ** 2
            c1 = gamma * c1 + Y[slot]
            c2 = gamma * c2 + Y[slot] ** 2
            cert *= F[slot]
            cost *= G[slot]
            mixture *= F[slot]
        start = t - delay
        if start in weights:
            mixture += weights[start] * F[slot]
            tail -= weights[start]
        visible = np.where(restart, mixture + max(tail, 0), cert)
        cost_alarm[(cost_alarm == T) & (cost >= 1 / alpha)] = t
        gated = (mode == "direct") | (cost_alarm < T)
        # A positive per-event margin only covers the switch fee if enough
        # horizon remains under a persistent-benefit assumption. No future claim.
        practical = (T - t) * margin >= switch_cost
        hit = (first == T) & gated & (visible >= 1 / alpha) & practical
        first[hit] = t
        labels_at[hit] = spent[hit]
        if history is not None:
            history[:, :, t] = np.log(np.maximum(visible, 1e-300))
        denom = np.where(bet == "ftl", m1 + m2, m2)
        lam = np.clip(np.divide(m1, denom, out=np.zeros_like(m1), where=denom != 0), 0, hi)
        lc = np.minimum(np.maximum(c1, 0) / np.maximum(c2, 1e-12), hc)
        p = stream["score"][:, t]
        disagree = stream["disagree"][:, t]
        q = np.where(
            alloc == "uniform",
            frac,
            np.where(
                alloc == "disagreement",
                frac / 4 + 1.5 * frac * disagree,
                frac / 4 + 1.5 * frac * 4 * p * (1 - p),
            ),
        )
        rate = np.where(pace == "reserve", frac * (0.25 + 1.5 * t / T), (B - spent) / max(T - t, 1))
        q = np.where(pace == "none", q, np.clip(q * rate / frac, floor, 1))
        q = np.clip(q, floor, 1)
        if skip_known_zero:
            q = np.where(stream["disagree"][:, t], q, 0)
        active = (spent < B) & (first == T)
        query = (U[:, t] < q) & active
        spent += query
        gain = l0[:, t] - l1[:, t]
        inverse = query / np.where(q > 0, q, 1)
        x = inverse * gain - margin
        x = np.where(active & ((mode != "after_alarm") | (cost_alarm < T)), x, 0)
        proxy = stream["proxy"][:, t]
        xc = np.where(active & (q > 0), proxy + inverse * (l0[:, t] - proxy) - stream["r0"], 0)
        f = 1 + lam * x
        g = 1 + lc * xc
        if np.any((f <= 0) | (g <= 0) | ~np.isfinite(f) | ~np.isfinite(g)):
            raise ArithmeticError("invalid paired/cost betting factor")
        due = (t + delay) % (delay + 1)
        X[due], Y[due], F[due], G[due] = x, xc, f, g
    labels_at = np.where(first < T, labels_at, spent)
    prefix0 = np.pad(np.cumsum(l0, axis=1), ((0, 0), (1, 0)))
    prefix1 = np.pad(np.cumsum(l1, axis=1), ((0, 0), (1, 0)))
    rows = np.arange(S)[None, :]
    decision = prefix0[rows, first] + prefix1[rows, T] - prefix1[rows, first]
    total = decision + query_cost * labels_at + switch_cost * (first < T)
    result = {
        "first": first,
        "labels": labels_at,
        "decision_cost": decision,
        "total_cost": total,
        "delta_vs_incumbent": total - prefix0[:, T],
        "cost_alarm": cost_alarm,
    }
    if history is not None:
        result["logwealth"] = history
    return result
