"""Exact finite computations: reversal impossibility, optional-continuation failure, CS validity."""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from fractions import Fraction

import numpy as np

# ---------------------------------------------------------------- reversal impossibility


def history_laws(
    tau: int,
    d: int,
    mean_fn: Callable[[int], Fraction],
    query_rule: Callable[[tuple], bool],
) -> dict[tuple, Fraction]:
    """Exact law of the decision-time history under Rademacher labels (P(Z=1)=(1+mu)/2).

    Round s in 1..tau: ``query_rule(released)`` (a deterministic function of the labels released so
    far, as a tuple of (request_time, z)) decides whether to request round s.  A request at s is
    released at s+d.  The history at the start of tau is the tuple of labels released by tau, i.e.
    those requested at s <= tau-d.  Queried labels of rounds > tau-d are unobserved at tau and
    marginalised out.
    """
    laws: dict[tuple, Fraction] = {}

    def rec(s: int, released: tuple, prob: Fraction, pending: tuple):
        # release pending labels whose arrival <= s
        new_pending, rel = [], list(released)
        for req, z in pending:
            if req + d <= s:
                rel.append((req, z))
            else:
                new_pending.append((req, z))
        released = tuple(sorted(rel))
        if s == tau:
            laws[released] = laws.get(released, Fraction(0)) + prob
            return
        if query_rule(released):
            mu = mean_fn(s)
            for z, pz in ((1, (1 + mu) / 2), (-1, (1 - mu) / 2)):
                rec(s + 1, released, prob * pz, tuple(new_pending) + ((s, z),))
        else:
            rec(s + 1, released, prob, tuple(new_pending))

    rec(1, (), Fraction(1), ())
    return laws


def min_error_sum(law_plus: dict, law_minus: dict) -> Fraction:
    """min over ALL (randomised) rules of P_plus(no-certify)+P_minus(certify) = sum_h min(p+,p-)."""
    keys = set(law_plus) | set(law_minus)
    return sum(
        (min(law_plus.get(h, Fraction(0)), law_minus.get(h, Fraction(0))) for h in keys),
        Fraction(0),
    )


def brute_force_min_error_sum(law_plus: dict, law_minus: dict) -> Fraction:
    """Same quantity by enumerating every deterministic rule (certify-set) -- small histories only."""
    keys = sorted(set(law_plus) | set(law_minus))
    best = Fraction(2)
    for mask in range(2 ** len(keys)):
        cert = {keys[i] for i in range(len(keys)) if mask >> i & 1}
        err = sum((law_plus.get(h, Fraction(0)) for h in keys if h not in cert), Fraction(0)) + sum(
            (law_minus.get(h, Fraction(0)) for h in cert), Fraction(0)
        )
        best = min(best, err)
    return best


def reversal_world_means(tau: int, d: int, base: Fraction, delta: Fraction, diverge_from: int):
    """Two worlds sharing mean ``base`` before ``diverge_from`` and +delta / -delta after (clipped)."""

    def plus(s):
        return base if s < diverge_from else delta

    def minus(s):
        return base if s < diverge_from else -delta

    return plus, minus


def payback_of(mean_fn, tau: int, h: int, k: Fraction) -> Fraction:
    return sum((mean_fn(tau + j) for j in range(h)), Fraction(0)) - k


# ---------------------------------------------------------------- crossing probabilities


def crossing_probability(
    trigger_sum: Callable[[int], float], M: int, mu0: float, return_curve: bool = False
):
    """P(exists m<=M: S_m > trigger_sum(m)) for S_m = sum of m iid +/-1 with mean mu0, exact DP
    (float64; absorbing).  ``trigger_sum(m)`` is a threshold on the *uncentred* sum S_m."""
    p = (1 + mu0) / 2
    prob = np.zeros(M + 2)
    prob[0] = 1.0  # index = number of +1 among m draws
    cum, curve = 0.0, []
    for m in range(1, M + 1):
        new = np.zeros(M + 2)
        new[: m + 1] = prob[: m + 1] * (1 - p)
        new[1 : m + 1] += prob[:m] * p
        prob = new
        ups = np.arange(m + 1)
        s = 2 * ups - m
        hit = s > trigger_sum(m)
        cum += float(prob[: m + 1][hit].sum())
        prob[: m + 1][hit] = 0.0
        if return_curve:
            curve.append(cum)
    return (cum, curve) if return_curve else cum


def crossing_probability_exact_fraction(
    trigger_sum: Callable[[int], float], M: int, mu0: Fraction
) -> Fraction:
    """Same quantity in exact rational arithmetic (thresholds compared as floats, probabilities exact)."""
    p = (1 + mu0) / 2
    prob = {0: Fraction(1)}
    cum = Fraction(0)
    for m in range(1, M + 1):
        new: dict[int, Fraction] = {}
        for u, w in prob.items():
            new[u] = new.get(u, Fraction(0)) + w * (1 - p)
            new[u + 1] = new.get(u + 1, Fraction(0)) + w * p
        prob = {}
        for u, w in new.items():
            if 2 * u - m > trigger_sum(m):
                cum += w
            else:
                prob[u] = w
    return cum


def hoeffding_naive_trigger(mu_thr: float, alpha: float) -> Callable[[int], float]:
    """Certify at look m iff Zbar_m - sqrt(2 ln(1/alpha)/m) > mu_thr  <=>  S_m > m mu_thr + sqrt(2 ln(1/alpha) m)."""
    c = 2 * math.log(1 / alpha)
    return lambda m: m * mu_thr + math.sqrt(c * m)


def wald_naive_trigger(mu_thr: float, z: float) -> Callable[[int], float]:
    return lambda m: m * mu_thr + z * math.sqrt(m)


def mixture_boundary(alpha: float, rho: float) -> Callable[[int], float]:
    """Two-sided normal-mixture sub-Gaussian(1) boundary u_m on the centred sum."""
    return lambda m: math.sqrt((m + rho) * (math.log((m + rho) / rho) + 2 * math.log(1 / alpha)))


def mixture_rho(alpha: float, m_star: float) -> float:
    la = 2 * math.log(1 / alpha)
    return m_star / (la + math.log(1 + la))


def mixture_trigger(mu_thr: float, alpha: float, rho: float) -> Callable[[int], float]:
    u = mixture_boundary(alpha, rho)
    return lambda m: m * mu_thr + u(m)


def all_rules_check_grid():
    """Convenience for tests: yield small (tau, d) pairs."""
    yield from itertools.product(range(2, 6), range(1, 3))
