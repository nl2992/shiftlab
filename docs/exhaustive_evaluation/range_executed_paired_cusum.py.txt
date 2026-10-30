"""Classical CUSUM adapted to delayed, uniformly queried paired costs.

Thresholds are simulation calibrated, not anytime-valid under arbitrary nulls.
"""

import numpy as np

from .paired_references import finish_paired_result


def paired_cusum(
    stream,
    slacks,
    thresholds=None,
    *,
    frac=0.2,
    budget=400,
    delay=5,
    seed=0,
    margin=0.01,
    query_cost=0.001,
    switch_cost=1,
):
    loss, candidate = np.asarray(stream["loss"]), np.asarray(stream["candidate_loss"])
    if (
        loss.shape != candidate.shape
        or loss.ndim != 2
        or not np.isfinite(loss).all()
        or not np.isfinite(candidate).all()
    ):
        raise ValueError("finite paired matrices required")
    if np.any((loss < 0) | (loss > 1) | (candidate < 0) | (candidate > 1)):
        raise ValueError("costs outside [0,1]")
    paths, horizon = loss.shape
    slacks = np.asarray(slacks, dtype=float)
    if slacks.ndim != 1 or len(slacks) == 0 or np.any(~np.isfinite(slacks) | (slacks < 0)):
        raise ValueError("nonnegative finite slacks required")
    if not 0 < frac <= 1 or delay < 1 or not 0 <= budget <= horizon or margin < 0:
        raise ValueError("invalid query contract")
    thresholds = np.full(len(slacks), np.inf) if thresholds is None else np.asarray(thresholds)
    if thresholds.shape != slacks.shape or np.any(np.isnan(thresholds) | (thresholds <= 0)):
        raise ValueError("positive matching thresholds required")
    queries = np.random.default_rng(seed).random(loss.shape) < frac
    queries &= np.cumsum(queries, axis=1) <= budget
    state = np.zeros((len(slacks), paths))
    maximum = state.copy()
    first = np.full(state.shape, horizon, dtype=int)
    for t in range(delay, horizon):
        issued = t - delay
        update = queries[:, issued]
        increment = loss[:, issued] - candidate[:, issued] - margin
        state = np.where(update, np.maximum(0, state + increment - slacks[:, None]), state)
        maximum = np.maximum(maximum, state)
        # Same persistence-based economic eligibility as the paired betting controls.
        eligible = (horizon - t) * margin >= switch_cost
        hit = (state > thresholds[:, None]) & (first == horizon) & eligible
        first[hit] = t
    results = [
        finish_paired_result(stream, row, queries, query_cost=query_cost, switch_cost=switch_cost)
        for row in first
    ]
    return {"maximum": maximum, **{k: np.stack([r[k] for r in results]) for k in results[0]}}
