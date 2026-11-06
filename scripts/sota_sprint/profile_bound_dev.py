"""Development diagnostic: certified adaptive upper bound for a Markov null profile.

This is deliberately not wired into a policy. It compares the current factorwise cell bound
with a branch-and-bound likelihood upper bound on fixed synthetic queried-outcome sequences.
"""

from __future__ import annotations

import heapq
import math

import numpy as np
from scipy.optimize import minimize_scalar


def loglik(z: np.ndarray, gaps: np.ndarray, p: float, rho: float, *, initial: bool = True) -> float:
    a = np.power(rho, gaps[1:])
    m = a * z[:-1] + (1.0 - a) * p
    probs = np.where(z[1:] == 1, m, 1.0 - m)
    if initial:
        probs = np.r_[p if z[0] else 1.0 - p, probs]
    return float(np.log(probs).sum()) if np.all(probs > 0) else -math.inf


def box_upper(z: np.ndarray, gaps: np.ndarray, p0: float, p1: float, r0: float, r1: float) -> float:
    """Product upper bound from monotonicity of each factor on a parameter rectangle."""
    prev, hit, g = z[:-1], z[1:], gaps[1:]
    ahi, alo = r1**g, r0**g
    probs = np.where(
        (prev == 1) & (hit == 1),
        ahi + (1.0 - ahi) * p1,
        np.where(
            (prev == 1) & (hit == 0),
            (1.0 - alo) * (1.0 - p0),
            np.where((prev == 0) & (hit == 1), (1.0 - alo) * p1, 1.0 - (1.0 - ahi) * p0),
        ),
    )
    first = p1 if z[0] else 1.0 - p0
    return (
        float(np.log(first) + np.log(probs).sum()) if first > 0 and np.all(probs > 0) else -math.inf
    )


def rho_box_upper(
    z: np.ndarray, gaps: np.ndarray, r0: float, r1: float, *, initial: bool = True
) -> float:
    """Upper bound on a rho interval while optimizing over one shared p.

    Each transition probability is first maximized over rho in [r0,r1] using its known
    monotonicity. The resulting log likelihood is concave in the shared p; bisection finds its
    stationary point. A concave tangent at that point is an upper bound on the maximum, with the
    residual derivative times the parameter diameter added as a numerical bracket allowance.
    """
    prev, hit, g = z[:-1], z[1:], gaps[1:]
    ahi, alo = r1**g, r0**g
    # Probabilities for each observed transition, after maximizing over rho in the interval.
    typ = prev * 2 + hit
    # Counts make the shared-p profile and its derivative stable even near p=0.
    _n00, n01, n10, n11 = (int(np.sum(typ == k)) for k in range(4))
    Ahi, Alo = 1.0 - ahi, 1.0 - alo
    m00, m01, m10, m11 = (typ == k for k in range(4))

    def val_deriv(p: float) -> tuple[float, float]:
        if p <= 0.0:
            if (initial and z[0]) or n01:
                return -math.inf, math.inf
            v = float(np.log(Alo[m10]).sum()) + float(np.log(ahi[m11]).sum())
            der = -float(n10) - float(np.sum(Ahi[m00])) + float(np.sum(Ahi[m11] / ahi[m11]))
            return v, der
        v = (math.log(p) if z[0] else math.log1p(-p)) if initial else 0.0
        v += float(np.log1p(-Ahi[m00] * p).sum())
        if n01:
            v += float(n01) * math.log(p) + float(np.log(Alo[m01]).sum())
        if n10:
            v += float(np.log(Alo[m10]).sum()) + float(n10) * math.log1p(-p)
        if n11:
            v += float(np.log(ahi[m11] + Ahi[m11] * p).sum())
        der = (1.0 / p if z[0] else -1.0 / (1.0 - p)) if initial else 0.0
        der += -float(np.sum(Ahi[m00] / (1.0 - Ahi[m00] * p)))
        der += float(n01) / p - float(n10) / (1.0 - p)
        der += float(np.sum(Ahi[m11] / (ahi[m11] + Ahi[m11] * p)))
        return v, der

    lo, hi = 0.0, 0.5
    _, dlo = val_deriv(lo)
    _, dhi = val_deriv(hi)
    if dlo <= 0:
        pstar = lo
    elif dhi >= 0:
        pstar = hi
    else:
        for _ in range(80):
            mid = (lo + hi) / 2
            _, dm = val_deriv(mid)
            if dm > 0:
                lo = mid
            else:
                hi = mid
        pstar = (lo + hi) / 2
    v, d = val_deriv(pstar)
    # Concavity: f(p) <= f(p*) + f'(p*)(p-p*); maximize this tangent on [0,.5].
    tangent_slack = max(d * (0.0 - pstar), d * (0.5 - pstar), 0.0)
    return v + tangent_slack + 1e-10 * len(z)


def profile_upper_rho(
    z: np.ndarray,
    gaps: np.ndarray,
    *,
    tol: float = 0.02,
    max_boxes: int = 20_000,
    initial: bool = True,
) -> tuple[float, float, int]:
    """One-dimensional rho branch-and-bound using rho_box_upper."""

    def exact_profile(rho: float) -> float:
        # The exact log likelihood is concave in p at fixed rho; scalar optimization gives an
        # attained value for this development diagnostic.
        opt = minimize_scalar(
            lambda p: -loglik(z, gaps, float(p), rho, initial=initial),
            bounds=(1e-10, 0.5),
            method="bounded",
            options={"xatol": 1e-10},
        )
        return max(loglik(z, gaps, p, rho, initial=initial) for p in (0.0, 0.5, opt.x))

    best = max(exact_profile(r) for r in (0.0, 0.5, 0.9, 0.99, 1.0))
    ub = rho_box_upper(z, gaps, 0.0, 1.0, initial=initial)
    heap: list[tuple[float, int, tuple[float, float]]] = [(-ub, 0, (0.0, 1.0))]
    serial, evaluated = 1, 1
    while heap and evaluated < max_boxes:
        global_ub = -heap[0][0]
        if global_ub - best <= tol:
            # Previously pruned intervals were each within tol of the best value at pruning time;
            # the best can only increase, so best+tol also covers them.
            return max(global_ub, best + tol), best, evaluated
        _negub, _, (r0, r1) = heapq.heappop(heap)
        mid = (r0 + r1) / 2
        for box in ((r0, mid), (mid, r1)):
            a, b = box
            for r in (a, (a + b) / 2, b):
                best = max(best, exact_profile(r))
            bound = rho_box_upper(z, gaps, a, b, initial=initial)
            if bound > best + tol:
                heapq.heappush(heap, (-bound, serial, box))
                serial += 1
            evaluated += 1
    return (max(-heap[0][0], best + tol) if heap else best + tol), best, evaluated


def profile_upper(
    z: np.ndarray, gaps: np.ndarray, *, tol: float = 0.02, max_boxes: int = 20_000
) -> tuple[float, float, int]:
    """Return (certified upper, attained lower, number of evaluated boxes)."""
    best = max(loglik(z, gaps, p, r) for p in (0.0, 0.25, 0.5) for r in (0.0, 0.5, 1.0))
    root = (0.0, 0.5, 0.0, 1.0)
    ub = box_upper(z, gaps, *root)
    heap: list[tuple[float, int, tuple[float, float, float, float]]] = [(-ub, 0, root)]
    serial, evaluated = 1, 1
    while heap and evaluated < max_boxes:
        global_ub = -heap[0][0]
        if global_ub - best <= tol:
            return global_ub, best, evaluated
        negub, _, (p0, p1, r0, r1) = heapq.heappop(heap)
        if -negub <= best + tol:
            continue
        # Alternate dimensions to avoid a scale-induced bias in [0,.5] x [0,1].
        if evaluated % 2:
            mid = (p0 + p1) / 2.0
            boxes = ((p0, mid, r0, r1), (mid, p1, r0, r1))
        else:
            mid = (r0 + r1) / 2.0
            boxes = ((p0, p1, r0, mid), (p0, p1, mid, r1))
        for box in boxes:
            a, b, c, d = box
            for p, r in (((a + b) / 2, (c + d) / 2), (a, c), (b, d)):
                best = max(best, loglik(z, gaps, p, r))
            bound = box_upper(z, gaps, *box)
            if bound > best + tol:
                heapq.heappush(heap, (-bound, serial, box))
                serial += 1
            evaluated += 1
    return (-heap[0][0] if heap else best), best, evaluated


def grid_upper(
    z: np.ndarray, gaps: np.ndarray, n_p: int, n_rho: int, *, initial: bool = True
) -> float:
    """Reproduce MarkovSUI's factorwise cell upper bound, without started-mixture state."""
    pe = np.unique(
        np.r_[np.linspace(0, 0.3, 7), np.linspace(0.3, 0.45, 16), np.linspace(0.45, 0.5, n_p + 1)]
    )
    rr = np.geomspace(1e-4, 8, n_rho)
    re = np.unique(np.r_[0.0, np.exp(-rr[::-1]), 1.0])
    # Maximize each cell's factor separately, then maximize the sum over cells.
    vals = np.zeros((len(re) - 1, len(pe) - 1))
    if initial:
        hit = z[0]
        plo, phi = pe[:-1][None, :], pe[1:][None, :]
        rlo, rhi = re[:-1, None], re[1:, None]
        fac = np.broadcast_to(phi if hit else 1.0 - plo, vals.shape)
        with np.errstate(divide="ignore"):
            vals += np.log(fac)
    for i in range(1, len(z)):
        hit, g, prev = z[i], int(gaps[i]), int(z[i - 1])
        plo, phi = pe[:-1][None, :], pe[1:][None, :]
        rlo, rhi = re[:-1, None], re[1:, None]
        ahi, alo = rhi**g, rlo**g
        if prev and hit:
            fac = ahi + (1 - ahi) * phi
        elif prev:
            fac = (1 - alo) * (1 - plo)
        elif hit:
            fac = (1 - alo) * phi
        else:
            fac = 1 - (1 - ahi) * plo
        with np.errstate(divide="ignore"):
            vals += np.log(fac)
    return float(np.max(vals))


def main() -> None:
    rows = []
    for rho in (0.0, 0.5, 0.8):
        for seed in range(3):
            rng = np.random.default_rng(2026110701 + seed + int(100 * rho))
            z = np.empty(120, dtype=int)
            z[0] = rng.binomial(1, 0.65)
            for i in range(1, len(z)):
                z[i] = z[i - 1] if rng.random() < rho else rng.binomial(1, 0.65)
            gaps = np.ones_like(z)
            bnb, lower, nbox = profile_upper(z, gaps)
            rho_bnb, rho_lower, rho_boxes = profile_upper_rho(z, gaps)
            grid = grid_upper(z, gaps, 100, 300)
            rows.append((rho, seed, grid, bnb, lower, nbox, rho_bnb, rho_lower, rho_boxes))
    print(
        "rho seed factorwise_grid rectangle_bnb rectangle_lower boxes shared_p_rho_bnb lower boxes"
    )
    for rho, seed, grid, bnb, lower, nbox, rb, rl, rn in rows:
        print(f"{rho:.1f} {seed} {grid:.4f} {bnb:.4f} {lower:.4f} {nbox} {rb:.4f} {rl:.4f} {rn}")


if __name__ == "__main__":
    main()
