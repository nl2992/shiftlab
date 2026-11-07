"""Learned active-RCPS components adapted to one delayed paired-cost question.

No RCPS grid inversion or original expected-budget theorem is asserted. Fixed
global propensity bound; all issue-time betting quantities are frozen in queue.
"""

import numpy as np

from .active_rcps_learning import FixedRiskPredictor, QueryNormalizer, fixed_question_features


def learned_paired_rcps(
    stream,
    *,
    variance_target="source",
    normalization="source",
    frac=0.2,
    floor=0.05,
    budget=None,
    delay=5,
    seed=0,
    margin=0.01,
    alpha=0.05,
    query_cost=0.001,
    switch_cost=1,
    return_trace=False,
    cap_mode="global",
):
    if cap_mode not in ("global", "query", "predictor"):
        raise ValueError("unknown predictable range bound")
    if variance_target not in ("source", "residual") or normalization not in (
        "source",
        "paper",
        "uniform",
    ):
        raise ValueError("unknown learned-policy adaptation")
    loss, candidate = np.asarray(stream["loss"]), np.asarray(stream["candidate_loss"])
    p = np.asarray(stream["score"])
    candidate_p = np.asarray(stream["candidate_score"])
    if (
        loss.ndim != 2
        or any(v.shape != loss.shape for v in [candidate, p, candidate_p])
        or any(
            not np.isfinite(v).all() or np.any((v < 0) | (v > 1))
            for v in [loss, candidate, p, candidate_p]
        )
    ):
        raise ValueError("finite bounded same-shape losses and scores required")
    paths, horizon = loss.shape
    budget = int(frac * horizon) if budget is None else budget
    if not 0 < alpha < 1 or not 0 <= margin < 1 or delay < 1 or not 0 <= budget <= horizon:
        raise ValueError("invalid feedback or risk contract")
    normalizer = QueryNormalizer(
        paths,
        target=frac,
        floor=floor,
        objective="source" if normalization == "uniform" else normalization,
    )
    mean, variance = FixedRiskPredictor(paths), FixedRiskPredictor(paths)
    theta = (1 - margin) / 2
    cap = 0.5 / (1 / floor - theta)
    total, square, wealth = np.zeros(paths), np.zeros(paths), np.ones(paths)
    spent, first = np.zeros(paths, dtype=int), np.full(paths, horizon, dtype=int)
    rng = np.random.default_rng(seed).random(loss.shape)
    pending = [None] * (delay + 1)
    trace = (
        {
            k: np.zeros(loss.shape)
            for k in [
                "q",
                "cv",
                "lambda",
                "xi",
                "logwealth",
                "query",
                "q_bound",
                "cv_min",
                "stake_cap",
            ]
        }
        if return_trace
        else None
    )
    for t in range(horizon):
        slot = t % (delay + 1)
        if t >= delay:
            x, factor, features_mean, features_var, risk, var_target, queried = pending[slot]
            total += x
            square += x * x
            wealth *= factor
            # Predictor optimization sees only released queried outcomes.
            mean.update(features_mean, risk, queried)
            variance.update(features_var, var_target, queried)
        hit = (first == horizon) & (wealth >= 1 / alpha) & ((horizon - t) * margin >= switch_cost)
        first[hit] = t
        active = (first == horizon) & (spent < budget)
        # These extrema depend on released history, before the current covariates.
        q_bound = np.full(paths, floor)
        cv_min = np.zeros(paths)
        live_cap = np.full(paths, cap)
        if cap_mode != "global":
            if normalization == "uniform":
                q_bound = np.full(paths, frac)
            else:
                q_bound = np.maximum(floor, normalizer.predict(variance.bounds()[0])[0] - 0.001)
            if cap_mode == "predictor":
                cv_min = mean.bounds()[0]
            minimum = theta + (1 / q_bound - 1) * cv_min - 1 / q_bound
            live_cap = 0.5 / np.abs(minimum)
        lam = np.clip(
            np.divide(total, total + square, out=np.zeros(paths), where=total + square != 0),
            0,
            live_cap,
        )
        a0, a1 = p[:, t] >= 1 / 6, candidate_p[:, t] >= 1 / 6
        # Model-derived proxy uses incumbent probability, never evaluator truth.
        gain_if_zero = (a0.astype(float) - a1.astype(float)) / 5
        gain_if_one = a1.astype(float) - a0.astype(float)
        proxy_risk = (1 - ((1 - p[:, t]) * gain_if_zero + p[:, t] * gain_if_one)) / 2
        proxy_variance = 0.25 * p[:, t] * (1 - p[:, t]) * (gain_if_one - gain_if_zero) ** 2
        fm, fv = fixed_question_features(proxy_risk), fixed_question_features(proxy_variance)
        cv, var = mean.predict(fm), variance.predict(fv)
        q, raw, inverse = normalizer.predict(var)
        if normalization == "uniform":
            q = np.full(paths, frac)
        if np.any(q < q_bound - 1e-12) or np.any(cv < cv_min - 1e-12):
            raise ArithmeticError("predictable query or CV range violated")
        queried = (rng[:, t] < q) & active
        spent += queried
        if normalization != "uniform":
            normalizer.update(q, raw, inverse, active)
        risk = (1 - loss[:, t] + candidate[:, t]) / 2
        x = np.where(active, theta - cv + queried / q * (cv - risk), 0)
        factor = 1 + lam * x
        if np.any(~np.isfinite(factor) | (factor <= 0)):
            raise ArithmeticError("nonpositive learned RCPS factor")
        target = risk if variance_target == "source" else (risk - cv) ** 2
        pending[(t + delay) % (delay + 1)] = (x, factor, fm, fv, risk, target, queried)
        if trace is not None:
            for k, v in [
                ("q", q),
                ("cv", cv),
                ("lambda", lam),
                ("xi", x),
                ("logwealth", np.log(wealth)),
                ("query", queried),
                ("q_bound", q_bound),
                ("cv_min", cv_min),
                ("stake_cap", live_cap),
            ]:
                trace[k][:, t] = v
    inc = np.pad(np.cumsum(loss, axis=1), ((0, 0), (1, 0)))
    cand = np.pad(np.cumsum(candidate, axis=1), ((0, 0), (1, 0)))
    rows = np.arange(paths)
    decision = inc[rows, first] + cand[:, horizon] - cand[rows, first]
    total_cost = decision + query_cost * spent + switch_cost * (first < horizon)
    result = {
        "first": first,
        "labels": spent,
        "decision_cost": decision,
        "total_cost": total_cost,
        "delta_vs_incumbent": total_cost - inc[:, horizon],
    }
    if trace is not None:
        result["trace"] = trace
    return result
