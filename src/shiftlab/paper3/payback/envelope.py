"""Persistence class C(v, J, hd) and its exact worst-case drop function.

Class: mean path mu_t in [-1,1]; |mu_{t+1}-mu_t| <= v except on "jump steps", where it is <= J
(J >= v); consecutive jump steps are >= hd apart (hd = dwell/persistence).  hd=1 with J=v is the
pure bounded-drift class.  Over any a consecutive steps the largest possible decrease is
drop(a) = J*ceil(a/hd) + v*(a - ceil(a/hd))   (jumps at the first step of the window, every hd).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Envelope:
    v: float
    J: float | None = None  # None -> J = v (no extra jumps)
    hd: int = 1

    def __post_init__(self):
        if self.v < 0 or self.hd < 1 or (self.J is not None and self.J < self.v):
            raise ValueError("need v>=0, hd>=1, J>=v")

    @property
    def jump(self) -> float:
        return self.v if self.J is None else self.J

    def drop(self, a: int) -> float:
        """Maximum decrease of the mean over a consecutive steps (unclipped)."""
        if a <= 0:
            return 0.0
        nj = math.ceil(a / self.hd)
        return self.jump * nj + self.v * (a - nj)

    def future_drop_sum(self, a0: int, h: int) -> float:
        """sum_{j=0}^{h-1} drop(a0 + j)."""
        return sum(self.drop(a0 + j) for j in range(h))

    def irreducible_slack(self, d: int, h: int) -> float:
        """Average over the horizon of the worst-case drop from the last observable mean level
        (request time tau-d) to rounds tau..tau+h-1.  Equals v*(d+(h-1)/2) for pure drift."""
        return self.future_drop_sum(d, h) / h

    def future_drop_table(self, h: int, amax: int) -> np.ndarray:
        """F[a] = sum_{j<h} drop(a+j) for a=0..amax (vectorised; cached on the instance dict)."""
        cache = self.__dict__.setdefault("_ftab", {})
        key = (h, amax)
        if key not in cache:
            n = np.arange(amax + h + 1)
            nj = np.ceil(n / self.hd)
            drop = self.jump * nj + self.v * (n - nj)
            c = np.concatenate([[0.0], np.cumsum(drop)])
            cache[key] = c[h : h + amax + 1] - c[: amax + 1]
        return cache[key]
