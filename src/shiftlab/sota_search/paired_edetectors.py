"""Known SR/CUSUM e-detector recurrences on queried paired-cost factors.

Finite-horizon H/alpha and ARL-style 1/alpha thresholds are distinct contracts.
"""

import numpy as np

from .paired_references import finish_paired_result


def paired_edetectors(
    stream,
    *,
    seed=0,
    frac=0.2,
    budget=400,
    delay=5,
    margin=0.01,
    alpha=0.05,
    query_cost=0.001,
    switch_cost=1,
    return_statistics=False,
):
    loss, candidate = np.asarray(stream["loss"]), np.asarray(stream["candidate_loss"])
    if (
        loss.ndim != 2
        or loss.shape != candidate.shape
        or not np.isfinite(loss).all()
        or not np.isfinite(candidate).all()
        or np.any((loss < 0) | (loss > 1) | (candidate < 0) | (candidate > 1))
    ):
        raise ValueError("bounded paired losses required")
    S, T = loss.shape
    if not 0 < frac <= 1 or not 0 <= budget <= T or delay < 1 or not 0 < alpha < 1 or margin < 0:
        raise ValueError("invalid feedback contract")
    stakes = np.array([0.2, 0.5, 0.8])
    q = np.random.default_rng(seed).random(loss.shape) < frac
    q &= np.cumsum(q, axis=1) <= budget
    active = np.pad(np.cumsum(q, axis=1), ((0, 0), (1, 0)))[:, :-1] < budget
    x = np.where(active, q / frac * (loss - candidate) - margin, 0)
    sr = np.zeros((3, S))
    cus = np.zeros_like(sr)
    names = [
        f"{kind}_{stake}_{contract}"
        for contract in ["horizon", "arl"]
        for kind in ["sr", "cusum"]
        for stake in [".2", ".5", ".8", "mixture"]
    ]
    first = np.full((16, S), T, dtype=int)
    history = np.zeros((8, S, T)) if return_statistics else None
    for t in range(T):
        # Publication at event t reveals only the issued event t-delay.
        factors = (
            np.ones((3, S))
            if t < delay
            else 1 + stakes[:, None] * x[:, t - delay] / (1 / frac + margin)
        )
        sr = (1 + sr) * factors
        cus = np.maximum(1, cus) * factors
        values = np.concatenate([sr, sr.mean(0, keepdims=True), cus, cus.mean(0, keepdims=True)])
        if return_statistics:
            history[:, :, t] = values
        doubled = np.concatenate([values, values])
        thresholds = np.r_[np.full(8, T / alpha), np.full(8, 1 / alpha)][:, None]
        hit = (first == T) & (doubled >= thresholds) & ((T - t) * margin >= switch_cost)
        first[hit] = t
    results = [
        finish_paired_result(stream, row, q, query_cost=query_cost, switch_cost=switch_cost)
        for row in first
    ]
    result = {k: np.stack([r[k] for r in results]) for k in results[0]}
    result["names"] = names
    if return_statistics:
        result["statistics"] = history
    return result
