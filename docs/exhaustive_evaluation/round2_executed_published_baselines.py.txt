"""Source-audited components; full-paper reproductions are separately labelled.

Active RCPS: Xu et al., arXiv:2406.10490, author code revision
a67f85d603df2bb3e32ef007f445191923ebd990, IwUpperMartingale.py.
With rho=1-loss, theta=1-mu, cv=1-proxy, its PartialIwUpper
increment is exactly proxy + Q/q*(loss-proxy) - mu. Its FTL bet
is sum(x)/(sum(x)+sum(x*x)), clipped at half the reciprocal
of the worst negative increment. This adapter fixes a single risk target;
it does not reproduce RCPS grid inversion or the author's learned query policy.
"""

import numpy as np
from scipy.special import logsumexp


def pr_empirical_bernstein(
    stream,
    *,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    tolerance=0.0,
    alpha=0.05,
    return_wealth=False,
):
    """PR Appendix E PM-EB formula, labelled stream, fixed cost-risk target.

    Uses the paper's cap .5 and predictable variance/mean estimates. Uniform
    querying preserves the conditional cost-null; delaying publication is a
    wrapper. Known/externally estimated source upper bound enters as r0.
    """
    loss = stream["loss"]
    S, T = loss.shape
    if not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1:
        raise ValueError("invalid query rate/delay/alpha")
    budget = int(frac * T) if budget is None else budget
    if not 0 <= budget <= T:
        raise ValueError("invalid budget")
    U = np.random.default_rng(seed).random((S, T))
    mask = U < frac
    mask &= np.cumsum(mask, axis=1) <= budget
    n, total, residual, weighted, weight, penalty = (np.zeros(S) for _ in range(6))
    first = np.full(S, T, dtype=int)
    maxlog = np.zeros(S)
    hist = np.zeros((S, T)) if return_wealth else None
    mu = stream["r0"] + tolerance
    for t in range(T):
        r = t - delay
        if r >= 0:
            observed = mask[:, r]
            mean_prev = (0.5 + total) / (n + 1)
            variance = (0.25 + residual) / (n + 1)
            lam = np.minimum(
                0.5, np.sqrt(2 * np.log(1 / alpha) / (variance * (n + 1) * np.log(n + 2)))
            )
            z = loss[:, r]
            weighted += observed * lam * z
            weight += observed * lam
            penalty += observed * (z - mean_prev) ** 2 * (-np.log1p(-lam) - lam)
            n += observed
            total += observed * z
            mean_now = (0.5 + total) / (n + 1)
            residual += observed * (z - mean_now) ** 2
        evidence = weighted - mu * weight - penalty
        first[(first == T) & (evidence >= np.log(1 / alpha))] = t
        maxlog = np.maximum(maxlog, evidence)
        if hist is not None:
            hist[:, t] = evidence
    result = {"first": first, "labels": mask.sum(1), "maxlog": maxlog}
    if hist is not None:
        result["logwealth"] = hist
    return result


def ppi_batch_estimate(label_loss, label_synthetic, unlabel_synthetic, eta):
    """PPRM equation 19, one labelled example and a separate unlabelled batch."""
    return label_loss + eta * (np.mean(unlabel_synthetic, axis=-1) - label_synthetic)


def pprm_batch_cost(
    stream,
    *,
    batch_size=5,
    budget=None,
    delay=5,
    seed=0,
    tolerance=0.0,
    alpha=0.05,
    eta_max=1.0,
    window=32,
    return_wealth=False,
):
    """PPRM eqs 19/22/27 with a declared discrete CM-EB mixing distribution.

    One uniformly chosen label in each nonempty batch, other examples unlabelled.
    Eta uses only previously released batches. Predictions are hard synthetic
    labels (eq16). This is a formula-based bounded-cost/batch adaptation, not
    author-code or full experimental reproduction. Source r0 is shared externally.
    """
    loss = stream["loss"]
    S, T = loss.shape
    if batch_size < 2 or delay < 1 or not 0 < alpha < 1 or eta_max < 0 or window < 2:
        raise ValueError("invalid batch/delay/alpha/eta/window")
    budget = T // batch_size if budget is None else budget
    if not 0 <= budget <= T:
        raise ValueError("invalid budget")
    n_batches = min(T // batch_size, budget)
    chosen = np.random.default_rng(seed).integers(batch_size, size=(S, n_batches))
    p = stream["score"]
    synthetic_y = p >= 0.5
    synthetic_loss = np.where(p >= 1 / 6, (1 - synthetic_y) / 5, synthetic_y).astype(float)
    lambdas = np.geomspace(0.001, 0.9, 32)
    psi = -np.log1p(-lambdas) - lambdas
    scale = 1 + 2 * eta_max
    mu = (stream["r0"] + tolerance + eta_max) / scale
    count, total, V = (np.zeros(S) for _ in range(3))
    first, maxlog = np.full(S, T, dtype=int), np.zeros(S)
    hist = np.zeros((S, T)) if return_wealth else None
    issued = np.zeros(S, dtype=int)
    past = []
    sealed_eta = {}
    for t in range(T):
        b = (t - delay + 1) // batch_size - 1
        if t >= batch_size - 1 + delay and (t - delay + 1) % batch_size == 0 and b < n_batches:
            start = b * batch_size
            yy = loss[np.arange(S), start + chosen[:, b]]
            syn = synthetic_loss[:, start : start + batch_size]
            lab_syn = syn[np.arange(S), chosen[:, b]]
            unlab_mean = (syn.sum(1) - lab_syn) / (batch_size - 1)
            eta = sealed_eta[b]
            estimate = yy + eta * (unlab_mean - lab_syn)
            z = (estimate + eta_max) / scale
            if np.any((z < -1e-12) | (z > 1 + 1e-12)):
                raise ArithmeticError("PPI normalization violated")
            pred = np.where(count > 0, total / np.maximum(count, 1), 0.5)
            V += (z - pred) ** 2
            total += z
            count += 1
            past.append((yy, lab_syn, syn))
            past = past[-window:]
        evidence = logsumexp(
            (total - count * mu)[:, None] * lambdas - V[:, None] * psi, axis=1
        ) - np.log(len(lambdas))
        first[(first == T) & (evidence >= np.log(1 / alpha))] = t
        maxlog = np.maximum(maxlog, evidence)
        if hist is not None:
            hist[:, t] = evidence
        b = t // batch_size
        if t % batch_size == 0 and b < n_batches:
            eta = np.zeros(S)
            if len(past) >= 3:
                y = np.stack([v[0] for v in past], axis=1)
                s = np.stack([v[1] for v in past], axis=1)
                covariance = np.mean(
                    (y - y.mean(1, keepdims=True)) * (s - s.mean(1, keepdims=True)), axis=1
                )
                # Equation27 uses unlabelled history only in the variance.
                # Keep each actual unlabelled value, not the variance of its mean.
                sum_u = sum(v[2].sum(1) - v[1] for v in past)
                sum_u2 = sum((v[2] ** 2).sum(1) - v[1] ** 2 for v in past)
                n_u = len(past) * (batch_size - 1)
                var_u = np.maximum(sum_u2 / n_u - (sum_u / n_u) ** 2, 0)
                eta = np.clip(
                    np.divide(
                        covariance,
                        (1 + 1 / (batch_size - 1)) * var_u,
                        out=np.zeros(S),
                        where=var_u > 1e-12,
                    ),
                    0,
                    eta_max,
                )
            sealed_eta[b] = eta
        if b < n_batches:
            issued += (t % batch_size) == chosen[:, b]
    result = {"first": first, "labels": issued, "maxlog": maxlog}
    if hist is not None:
        result["logwealth"] = hist
    return result


def active_rcps_cost(
    stream,
    *,
    frac=0.2,
    budget=None,
    delay=5,
    seed=0,
    tolerance=0.0,
    alpha=0.05,
    return_wealth=False,
):
    S, T = stream["loss"].shape
    if not 0 < frac <= 1 or delay < 1 or not 0 < alpha < 1:
        raise ValueError("invalid frac, delay or alpha")
    budget = int(frac * T) if budget is None else budget
    if not 0 <= budget <= T:
        raise ValueError("invalid budget")
    mu = stream["r0"] + tolerance
    hi = 0.5 / (stream["proxy_max"] * (1 / frac - 1) + mu)
    U = np.random.default_rng(seed).random((S, T))
    ring = np.zeros((delay + 1, S))
    factor_ring = np.ones_like(ring)
    sx, sx2, lw = np.zeros(S), np.zeros(S), np.zeros(S)
    spent = np.zeros(S, dtype=int)
    first = np.full(S, T, dtype=int)
    maxlog = np.zeros(S)
    history = np.zeros((S, T)) if return_wealth else None
    for t in range(T):
        slot = t % (delay + 1)
        if t >= delay:
            sx += ring[slot]
            sx2 += ring[slot] ** 2
            lw += np.log(factor_ring[slot])
        first[(first == T) & (lw >= np.log(1 / alpha))] = t
        maxlog = np.maximum(maxlog, lw)
        if history is not None:
            history[:, t] = lw
        denom = sx + sx2
        lam = np.clip(np.divide(sx, denom, out=np.zeros_like(sx), where=denom != 0), 0, hi)
        available = spent < budget
        queried = (U[:, t] < frac) & available
        spent += queried
        proxy = stream["proxy"][:, t]
        x = np.where(available, proxy + queried / frac * (stream["loss"][:, t] - proxy) - mu, 0)
        due = (t + delay) % (delay + 1)
        ring[due] = x
        factor_ring[due] = 1 + lam * x
    result = {"first": first, "labels": spent, "maxlog": maxlog}
    if history is not None:
        result["logwealth"] = history
    return result
