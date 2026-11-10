"""Causal task embedding from an observation window of the reference policy's operational log.

Inputs are exactly what a deployed monitor could have logged in the window: released paired
outcomes ``rel`` (E, T) in {-1, 0, +1} (0 = nothing released that step), the prediction-side
disagreement indicator ``dis`` (E, T), the label delay and the declared costs. Nothing from episodes
outside [a, b) is touched (see tests/paper3/transfer/test_leakage.py).
"""

from __future__ import annotations

import numpy as np

from .sim import Costs

FEATURES = [
    "released_per_episode",
    "p_hat_challenger",
    "abs_p_hat_margin",
    "std_p_hat_across_episodes",
    "lag1_autocorr_released",
    "disagree_rate",
    "std_disagree_rate",
    "delay_over_T",
    "intra_episode_drift",
    "mean_release_time",
    "log_cs",
    "log_cq",
]


def embed_window(rel, dis, delay: int, costs: Costs) -> np.ndarray:
    rel = np.asarray(rel)
    dis = np.asarray(dis)
    E, T = rel.shape
    got = rel != 0
    n_rel = got.sum(1)
    pos = rel > 0
    allp = pos[got]
    p_hat = float(allp.mean()) if allp.size else 0.5
    per_ep = np.array([pos[e][got[e]].mean() for e in range(E) if n_rel[e] >= 3])
    std_p = float(per_ep.std()) if per_ep.size >= 2 else 0.0
    # lag-1 autocorrelation of consecutive released outcomes within episodes
    xs, ys = [], []
    for e in range(E):
        v = rel[e][got[e]].astype(float)
        if v.size >= 3:
            xs.append(v[:-1])
            ys.append(v[1:])
    if xs:
        x, y = np.concatenate(xs), np.concatenate(ys)
        den = x.std() * y.std()
        ac = float(((x - x.mean()) * (y - y.mean())).mean() / den) if den > 1e-9 else 0.0
    else:
        ac = 0.0
    dr = dis.mean(1)
    drifts = []
    for e in range(E):
        idx = np.nonzero(got[e])[0]
        if idx.size >= 6:
            h = idx.size // 2
            a = (rel[e][idx[:h]] > 0).mean()
            b = (rel[e][idx[h:]] > 0).mean()
            drifts.append(abs(a - b))
    drift = float(np.mean(drifts)) if drifts else 0.0
    ts = np.nonzero(got)[1]
    mrt = float(ts.mean() / T) if ts.size else 0.5
    return np.array(
        [
            n_rel.mean() / costs.B,
            p_hat,
            abs(p_hat - 0.5),
            std_p,
            ac,
            float(dr.mean()),
            float(dr.std()),
            delay / T,
            drift,
            mrt,
            np.log(costs.cs),
            np.log(costs.cq),
        ]
    )
