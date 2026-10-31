"""Hindsight oracles (evaluator-side, never deployable). Oracle costs exclude query cost c_q (they use no
labels). The dynamic class contains the static class, hence dynamic <= static <= never-switch.
The initial action is the incumbent, so being on the challenger at t=0 costs one c_s."""

from __future__ import annotations

import numpy as np

from .contracts import CostContract, EpisodeBatch, EvaluatorTruth
from .evaluation import count_switches


def dp_two_state(m0: np.ndarray, m1: np.ndarray, c_s: float) -> np.ndarray:
    """Min over action paths of sum_t m_{a_t}(t) + c_s * #switches; m0, m1 shape (n, T)."""
    n, T = m0.shape
    f0, f1 = np.zeros(n), np.full(n, np.inf)
    for t in range(T):
        f0, f1 = np.minimum(f0, f1 + c_s) + m0[:, t], np.minimum(f1, f0 + c_s) + m1[:, t]
    return np.minimum(f0, f1)


def static_costs(m0, m1, c_s):
    never, always = m0.sum(axis=1), m1.sum(axis=1) + c_s
    return never, always, np.minimum(never, always)


def oracle_costs(batch: EpisodeBatch, truth: EvaluatorTruth, cost: CostContract) -> dict:
    out = {}
    for tag, m0, m1 in (
        ("exp", truth.mu0, truth.mu1),
        ("real", batch.l0.astype(float), batch.l1.astype(float)),
    ):
        never, always, static = static_costs(m0, m1, cost.c_s)
        dyn = dp_two_state(m0, m1, cost.c_s)
        out[f"never_{tag}"], out[f"always_{tag}"], out[f"static_{tag}"], out[f"dynamic_{tag}"] = (
            never,
            always,
            static,
            dyn,
        )
        out[f"headroom_{tag}"] = never - dyn  # H_T >= 0
        out[f"headroom_static_{tag}"] = static - dyn
    # regime-aware clairvoyant (S2): challenger iff bad regime and challenger useful (mu1 < mu0)
    a = (truth.regime == 1) & (truth.mu1 < truth.mu0)
    ns = count_switches(a.astype(np.int8))
    out["clairvoyant_exp"] = np.where(a, truth.mu1, truth.mu0).sum(axis=1) + cost.c_s * ns
    return out
