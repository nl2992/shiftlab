"""Direct paired-benefit references reusing existing bounded-risk components."""

import numpy as np
from scipy.special import logsumexp

from shiftlab.dive.eprocess import bounded_betting_factors

from .published_baselines import active_rcps_cost, pr_empirical_bernstein


def paired_fixed_mixture(
    stream,
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
):
    """Existing CandidatePromotionTest stakes with a constant IPW range bound."""
    S, T = stream["loss"].shape
    B = int(frac * T) if budget is None else budget
    if not 0 < frac <= 1 or delay < 1 or not 0 <= B <= T:
        raise ValueError("invalid query contract")
    q = np.random.default_rng(seed).random((S, T)) < frac
    q &= np.cumsum(q, axis=1) <= B
    active = np.pad(np.cumsum(q, axis=1), ((0, 0), (1, 0)))[:, :-1] < B
    x = np.where(active, q / frac * (stream["loss"] - stream["candidate_loss"]) - margin, 0)
    logs = []
    for row in x:
        factors = bounded_betting_factors(
            row, np.full(T, 1 / frac + margin), np.array([0.05, 0.1, 0.2, 0.4, 0.8])
        )
        logs.append(logsumexp(np.cumsum(np.log(factors), axis=0), axis=1) - np.log(5))
    logs = np.asarray(logs)
    visible = np.zeros_like(logs)
    visible[:, delay:] = logs[:, :-delay]
    eligible = np.arange(T)[None, :] <= (T - switch_cost / max(margin, 1e-12))
    hit = (visible >= np.log(1 / alpha)) & eligible
    first = np.where(hit.any(1), hit.argmax(1), T)
    value = finish_paired_result(stream, first, q, query_cost=query_cost, switch_cost=switch_cost)
    if return_wealth:
        value["logwealth"] = visible
    return value


def finish_paired_result(stream, first, queries, *, query_cost=0.001, switch_cost=1):
    S, T = stream["loss"].shape
    labels = np.pad(np.cumsum(queries, axis=1), ((0, 0), (1, 0)))[np.arange(S), first]
    inc = np.pad(np.cumsum(stream["loss"], axis=1), ((0, 0), (1, 0)))
    cand = np.pad(np.cumsum(stream["candidate_loss"], axis=1), ((0, 0), (1, 0)))
    decision = inc[np.arange(S), first] + cand[:, T] - cand[np.arange(S), first]
    total = decision + query_cost * labels + switch_cost * (first < T)
    return {
        "first": first,
        "labels": labels,
        "decision_cost": decision,
        "total_cost": total,
        "delta_vs_incumbent": total - inc[:, T],
    }


def paired_paper_reference(
    stream,
    *,
    method,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    alpha=0.05,
    margin=0.01,
    query_cost=0.001,
    switch_cost=1,
):
    """PR/RCPS bounded-risk formula adaptation to Z=(1+paired_gain)/2.

    Uniform query, same hard maximum. Analytic target (1+margin)/2 replaces
    absolute source-risk calibration. This changes the estimand explicitly.
    """
    if method not in ("pr", "rcps"):
        raise ValueError("unknown paired reference")
    S, T = stream["loss"].shape
    B = int(frac * T) if budget is None else budget
    transformed = {
        **stream,
        "loss": (1 + stream["loss"] - stream["candidate_loss"]) / 2,
        "proxy": np.full((S, T), 0.5),
        "proxy_max": 0.5,
        "r0": (1 + margin) / 2,
    }
    fn = pr_empirical_bernstein if method == "pr" else active_rcps_cost
    result = fn(transformed, frac=frac, budget=B, delay=delay, seed=seed, alpha=alpha)
    first = result["first"]
    first = np.where((T - first) * margin >= switch_cost, first, T)
    q = np.random.default_rng(seed).random((S, T)) < frac
    q &= np.cumsum(q, axis=1) <= B
    return finish_paired_result(stream, first, q, query_cost=query_cost, switch_cost=switch_cost)
