"""Certified-tolerance profile upper bounds for refresh-or-hold Markov likelihoods.

This is an exploratory denominator-tightening component. The interval relaxation is valid because
each binary transition probability is monotone in persistence on a rho interval; after taking those
per-factor rho maxima, the log likelihood is concave in the shared stationary mean p. A concave
tangent bounds its p maximum, and branch-and-bound covers rho in [0, 1].
"""

from __future__ import annotations

import heapq
import math

import numpy as np
from scipy.optimize import minimize_scalar


def _loglik(
    z: np.ndarray, gaps: np.ndarray, p: float, rho: float, *, initial: bool, prev0: int | None
) -> float:
    if prev0 is None:
        a = np.power(rho, gaps[1:])
        prev, cur = z[:-1], z[1:]
        m = a * prev + (1.0 - a) * p
        probs = np.where(cur == 1, m, 1.0 - m)
        if initial:
            probs = np.r_[p if z[0] else 1.0 - p, probs]
    else:
        a = rho ** int(gaps[0])
        m = a * prev0 + (1.0 - a) * p
        probs = np.asarray([m if z[0] else 1.0 - m])
        if len(z) > 1:
            a2 = np.power(rho, gaps[1:])
            m2 = a2 * z[:-1] + (1.0 - a2) * p
            probs = np.r_[probs, np.where(z[1:] == 1, m2, 1.0 - m2)]
    return float(np.log(probs).sum()) if np.all(probs > 0) else -math.inf


def _rho_box_upper(
    z: np.ndarray, gaps: np.ndarray, r0: float, r1: float, *, initial: bool, prev0: int | None
) -> float:
    if prev0 is None:
        prev, hit, g = z[:-1], z[1:], gaps[1:]
    else:
        prev, hit, g = np.r_[prev0, z[:-1]], z, gaps
    ahi, alo = r1**g, r0**g
    typ = prev * 2 + hit
    _n00, n01, n10, n11 = (int(np.sum(typ == k)) for k in range(4))
    Ahi, Alo = 1.0 - ahi, 1.0 - alo
    m00, m01, m10, m11 = (typ == k for k in range(4))

    def val_deriv(p: float) -> tuple[float, float]:
        if p <= 0.0:
            if (initial and prev0 is None and z[0]) or n01:
                return -math.inf, math.inf
            v = float(np.log(Alo[m10]).sum()) + float(np.log(ahi[m11]).sum())
            d = -float(n10) - float(np.sum(Ahi[m00])) + float(np.sum(Ahi[m11] / ahi[m11]))
            return v, d
        v = math.log(p) if initial and prev0 is None and z[0] else 0.0
        if initial and prev0 is None and not z[0]:
            v += math.log1p(-p)
        v += float(np.log1p(-Ahi[m00] * p).sum())
        if n01:
            v += float(n01) * math.log(p) + float(np.log(Alo[m01]).sum())
        if n10:
            v += float(np.log(Alo[m10]).sum()) + float(n10) * math.log1p(-p)
        if n11:
            v += float(np.log(ahi[m11] + Ahi[m11] * p).sum())
        d = 1.0 / p if initial and prev0 is None and z[0] else 0.0
        if initial and prev0 is None and not z[0]:
            d -= 1.0 / (1.0 - p)
        d -= float(np.sum(Ahi[m00] / (1.0 - Ahi[m00] * p)))
        d += float(n01) / p - float(n10) / (1.0 - p)
        d += float(np.sum(Ahi[m11] / (ahi[m11] + Ahi[m11] * p)))
        return v, d

    lo, hi = 0.0, 0.5
    _, dlo = val_deriv(lo)
    _, dhi = val_deriv(hi)
    if dlo <= 0:
        pstar = lo
    elif dhi >= 0:
        pstar = hi
    else:
        for _ in range(64):
            mid = (lo + hi) / 2.0
            _, dm = val_deriv(mid)
            if dm > 0:
                lo = mid
            else:
                hi = mid
        pstar = (lo + hi) / 2.0
    v, d = val_deriv(pstar)
    # Concavity makes this tangent an upper bound on the shared-p profile over [0, .5].
    slack = max(d * (0.0 - pstar), d * (0.5 - pstar), 0.0)
    return v + slack + 1e-10 * max(len(z), 1)


def profile_null_upper(
    z: list[int], gaps: list[int], prev0: int | None, *, tol: float = 0.05, max_boxes: int = 5000
) -> float:
    """Return an upper bound on the null likelihood, within ``tol`` when converged.

    ``z[i]`` is an outcome in the tested direction and ``gaps[i]`` is the event gap to the
    preceding queried outcome. ``prev0=None`` denotes the first observation of a test; otherwise
    it conditions on the known preceding outcome.
    """
    zz, gg = np.asarray(z, int), np.asarray(gaps, int)
    if len(zz) == 0 or len(gg) != len(zz):
        raise ValueError("z and gaps must have the same non-zero length")
    best = -math.inf

    def profile_at(rho: float) -> float:
        opt = minimize_scalar(
            lambda p: -_loglik(zz, gg, float(p), rho, initial=True, prev0=prev0),
            bounds=(1e-10, 0.5),
            method="bounded",
            options={"xatol": 1e-9},
        )
        return max(
            _loglik(zz, gg, p, rho, initial=True, prev0=prev0) for p in (0.0, 0.5, float(opt.x))
        )

    for r in (0.0, 0.5, 0.9, 0.99, 1.0):
        best = max(best, profile_at(r))
    ub = _rho_box_upper(zz, gg, 0.0, 1.0, initial=True, prev0=prev0)
    heap: list[tuple[float, int, tuple[float, float]]] = [(-ub, 0, (0.0, 1.0))]
    serial = 1
    evaluated = 1
    while heap and evaluated < max_boxes:
        global_ub = -heap[0][0]
        if global_ub - best <= tol:
            return max(global_ub, best + tol)
        _, _, (r0, r1) = heapq.heappop(heap)
        mid = (r0 + r1) / 2.0
        for a, b in ((r0, mid), (mid, r1)):
            for r in (a, (a + b) / 2.0, b):
                best = max(best, profile_at(r))
            bound = _rho_box_upper(zz, gg, a, b, initial=True, prev0=prev0)
            if bound > best + tol:
                heapq.heappush(heap, (-bound, serial, (a, b)))
                serial += 1
            evaluated += 1
    return max((-heap[0][0] if heap else -math.inf), best + tol)
