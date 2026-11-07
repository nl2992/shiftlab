"""Known predictable betting, epoch alpha spending and budget pacing compositions."""

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class EpochConfig:
    allocation: str
    pace: str
    gamma: float
    bet: str
    cap: float
    epochs: int


def epoch_configurations():
    return [
        EpochConfig(*v)
        for v in product(
            ("uniform", "disagreement", "uncertainty"),
            ("free", "remaining", "quota"),
            (0.9, 0.98, 1.0),
            ("kelly", "ftl"),
            (0.5, 0.75),
            (1, 2, 4, 5, 10),
        )
        if not (v[1] == "quota" and v[5] == 1)
    ]


def epoch_screen(
    stream,
    configs,
    *,
    seed=0,
    frac=0.2,
    delay=5,
    alpha=0.05,
    margin=0.01,
    query_cost=0.001,
    switch_cost=1,
    trace=False,
):
    l0, l1 = stream["loss"], stream["candidate_loss"]
    if (
        l0.shape != l1.shape
        or l0.ndim != 2
        or not np.isfinite(l0).all()
        or not np.isfinite(l1).all()
        or np.any((l0 < 0) | (l0 > 1) | (l1 < 0) | (l1 > 1))
    ):
        raise ValueError("bounded paired matrices required")
    S, T = l0.shape
    C = len(configs)
    B = int(frac * T)
    if not C or not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1 or margin < 0:
        raise ValueError("invalid contract")
    alloc = np.array([c.allocation for c in configs])[:, None]
    pace = np.array([c.pace for c in configs])[:, None]
    gamma = np.array([c.gamma for c in configs])[:, None]
    bet = np.array([c.bet for c in configs])[:, None]
    cap = np.array([c.cap for c in configs])[:, None]
    epochs = np.array([c.epochs for c in configs])[:, None]
    if (
        np.any(~np.isin(alloc, ["uniform", "disagreement", "uncertainty"]))
        or np.any(~np.isin(pace, ["free", "remaining", "quota"]))
        or np.any(~np.isin(bet, ["kelly", "ftl"]))
        or np.any(
            (gamma <= 0) | (gamma > 1) | (cap <= 0) | (cap >= 1) | (epochs < 1) | (epochs > T)
        )
    ):
        raise ValueError("invalid configuration")
    floor = np.where((alloc == "uniform") & (pace == "free"), frac, frac / 4)
    maximum_stake = cap / (1 / floor + margin)
    first = np.full((C, S), T, dtype=int)
    spent = np.zeros((C, S), dtype=int)
    m1, m2, wealth = (np.zeros((C, S)) for _ in range(3))
    wealth[:] = 1
    X = np.zeros((delay + 1, C, S))
    F = np.ones_like(X)
    E = np.full(X.shape, -1, dtype=int)
    random = np.random.default_rng(seed).random((S, T))
    current = np.full((C, 1), -1, dtype=int)
    history = (
        {k: np.zeros((C, S, T)) for k in ["query", "wealth", "epoch", "stake", "x"]}
        if trace
        else None
    )
    for t in range(T):
        epoch = np.minimum(epochs - 1, t * epochs // T)
        reset = epoch != current
        m1 = np.where(reset, 0, m1)
        m2 = np.where(reset, 0, m2)
        wealth = np.where(reset, 1, wealth)
        current = epoch
        slot = t % (delay + 1)
        if t >= delay:
            same = E[slot] == epoch
            m1 = np.where(same, gamma * m1 + X[slot], m1)
            m2 = np.where(same, gamma * m2 + X[slot] ** 2, m2)
            wealth *= np.where(same, F[slot], 1)
        hit = (first == T) & (wealth >= epochs / alpha) & ((T - t) * margin >= switch_cost)
        first[hit] = t
        end = ((epoch + 1) * T + epochs - 1) // epochs
        quota = (B * (epoch + 1)) // epochs
        available = np.where(pace == "quota", quota - spent, B - spent)
        base = np.where(
            alloc == "uniform",
            frac,
            np.where(
                alloc == "disagreement",
                frac / 4 + 1.5 * frac * stream["disagree"][:, t],
                frac / 4 + 1.5 * frac * 4 * stream["score"][:, t] * (1 - stream["score"][:, t]),
            ),
        )
        rate = np.where(
            pace == "quota", available / np.maximum(end - t, 1), (B - spent) / max(T - t, 1)
        )
        q = np.where(pace == "free", base, np.clip(base * rate / frac, floor, 1))
        q = np.clip(q, floor, 1)
        active = (first == T) & (spent < B) & (available > 0)
        query = (random[:, t] < q) & active
        spent += query
        denom = np.where(bet == "ftl", m1 + m2, m2)
        stake = np.clip(
            np.divide(m1, denom, out=np.zeros_like(m1), where=denom != 0), 0, maximum_stake
        )
        x = np.where(active, query / q * (l0[:, t] - l1[:, t]) - margin, 0)
        factor = 1 + stake * x
        if np.any(~np.isfinite(factor) | (factor <= 0)):
            raise ArithmeticError("invalid epoch factor")
        due = (t + delay) % (delay + 1)
        X[due], F[due], E[due] = x, factor, np.broadcast_to(epoch, (C, S))
        if trace:
            for k, v in [
                ("query", query),
                ("wealth", wealth),
                ("epoch", epoch),
                ("stake", stake),
                ("x", x),
            ]:
                history[k][:, :, t] = v
    inc = np.pad(np.cumsum(l0, 1), ((0, 0), (1, 0)))
    cand = np.pad(np.cumsum(l1, 1), ((0, 0), (1, 0)))
    rows = np.arange(S)[None, :]
    decision = inc[rows, first] + cand[:, T] - cand[rows, first]
    total = decision + query_cost * spent + switch_cost * (first < T)
    result = {
        "first": first,
        "labels": spent,
        "total_cost": total,
        "delta_vs_incumbent": total - inc[:, T],
    }
    if trace:
        result["trace"] = history
    return result
