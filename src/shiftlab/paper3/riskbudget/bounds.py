"""Lemma 1 (Bennett mixture) confidence width D(V) for the IPW martingale M_t."""

from __future__ import annotations

import numpy as np


class BennettMixture:
    """D(V) = min_lam [ln(1/(delta w_lam)) + phi(lam) V] / lam, D(0) = 0.

    b = max(1, 1/pi_min - 1); phi(lam) = (e^{lam b} - 1 - lam b) / b^2; uniform weights on a
    log-spaced grid with lam*b in [0.03, 2] (16 points by default), so D(V) is within a few
    percent of sqrt(2 V ln(1/delta')) for V in roughly [10, 500].
    With delta == 0 only pi_min == 1 is allowed (then V == 0 always and D == 0).
    """

    def __init__(self, delta: float, pi_min: float = 1.0, lams=None, n_grid: int = 16):
        if not 0.0 <= delta < 1.0:
            raise ValueError("delta must be in [0, 1)")
        if not 0.0 < pi_min <= 1.0:
            raise ValueError("pi_min must be in (0, 1]")
        if delta == 0.0 and pi_min != 1.0:
            raise ValueError("delta = 0 requires pi_min = 1 (deterministic regime)")
        self.delta, self.pi_min = float(delta), float(pi_min)
        self.b = max(1.0, 1.0 / pi_min - 1.0)
        if delta == 0.0:
            self.lams = np.array([])
            self._c = np.array([])
            self._phi = np.array([])
            return
        if lams is None:
            lams = np.geomspace(0.03, 2.0, n_grid) / self.b
        self.lams = np.asarray(lams, float)
        if np.any(self.lams <= 0):
            raise ValueError("lams must be positive")
        w = 1.0 / len(self.lams)
        lb = self.lams * self.b
        self._phi = (np.expm1(lb) - lb) / self.b**2
        self._c = np.log(1.0 / (delta * w)) / self.lams  # intercepts
        self._slope = self._phi / self.lams

    def D(self, V: float) -> float:
        if V < 0:
            raise ValueError("V must be >= 0")
        if V == 0.0:
            return 0.0
        if self.delta == 0.0:
            raise ValueError("delta = 0 admits only V = 0")
        return float(np.min(self._c + self._slope * V))

    __call__ = D
