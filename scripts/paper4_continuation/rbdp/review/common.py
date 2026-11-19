"""Independent model primitives (exact Fractions) for the RB-DP proof review.

Model (read from src/shiftlab/dive/causal_switching_game.py):
  beta_1 = prop(prior1); at time t the alternative cost of action 0 is pos(beta), of action 1 is 1-pos(beta);
  query cost c, switch cost k on a != previous action (previous action 0 at t=1); hard budget B.
  delay d=1: a label queried at t is seen before the decision at t+1.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache


@dataclass(frozen=True)
class Cell:
    T: int
    B: int
    t01: F
    t10: F
    e0: F
    e1: F
    prior: F = F(1, 2)
    c: F = F(0)
    k: F = F(0)
    alpha: F = F(1, 10)

    def prop(self, b: F) -> F:
        return self.t01 * (1 - b) + (1 - self.t10) * b

    def pos(self, b: F) -> F:
        return self.e0 + (self.e1 - self.e0) * b

    def post(self, b: F, y: int) -> F:
        """Posterior on S_t after label y at t (not yet propagated)."""
        p = self.pos(b)
        return b * self.e1 / p if y else b * (1 - self.e1) / (1 - p)

    @property
    def beta1(self) -> F:
        return self.prop(self.prior)


def post_value_fn(cell: Cell):
    """Exact optimal post-promotion cost, delay 1. Vpost(t, old, n, beta) from t on; 0 after T."""

    @lru_cache(maxsize=None)
    def V(t: int, old: int, n: int, b: F) -> F:
        if t > cell.T:
            return F(0)
        best = None
        for a in (0, 1):
            for q in ((0, 1) if n else (0,)):
                v = promote_like(t, old, n, b, a, q)
                if best is None or v < best:
                    best = v
        return best

    def promote_like(t, old, n, b, a, q):
        p = cell.pos(b)
        v = (p if a == 0 else 1 - p) + cell.c * q + cell.k * (a != old)
        if q:
            v += (1 - p) * V(t + 1, a, n - 1, cell.prop(cell.post(b, 0))) + p * V(
                t + 1, a, n - 1, cell.prop(cell.post(b, 1))
            )
        else:
            v += V(t + 1, a, n, cell.prop(b))
        return v

    @lru_cache(maxsize=None)
    def P(t: int, n: int, b: F) -> F:
        """Cost from t on when the first promotion happens at t (old action 0)."""
        return min(promote_like(t, 0, n, b, 1, q) for q in ((0, 1) if n else (0,)))

    return V, P
