"""Value functions and oracle for The Challenger (Digalakis et al., arXiv 2512.18390, Secs 2-3).

Paper definitions (read from the arXiv HTML):
  G(t)            = E[loss of challenger trained at epoch t] - E[loss of incumbent]   (a *gain* when >0)
  V_switch(t)     = -c n T - c_s + n (T - t) G(t)                                      (Eq. 2)
  V_discard(t)    = -c n t
  DeltaV(t)       = V_switch - V_discard = -c_s + n (T - t) (G(t) - c)
  discounted      V^b_switch(t) = -sum_{tau<=t} b^tau c n - b^t c_s + sum_{tau>t} b^tau n (G(t) - c)
                  V^b_discard(t) = -sum_{tau<=t} b^tau c n
  oracle          V_ORACLE = max{0, max_t V_switch(t)}
  Thm 3.1         Phi(t) = (T - t) G(t); switch optimal iff max_t Phi(t) >= c T + c_s / n;
                  stopping rule t*_int = min{t in T : Phi(t) >= Phi(t+1) or t = T}
  Prop 3.2        under G(t) = g* - g0 N_t^-alpha:  t_dagger ~ (g0 alpha T / (g* n^alpha))^(1/(1+alpha)).

The discounted form was transcribed from the paper's Remark 2.4 text; the paper's discounted stopping rule
(Thm 7.3) is NOT implemented (UNVERIFIED).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Economics:
    """Batch size n per step, horizon T (steps), per-sample cost c, one-off switching cost c_s, discount beta."""

    n: float
    T: int
    c: float
    c_s: float = 0.0
    beta: float = 1.0

    def __post_init__(self) -> None:
        if not (self.n > 0 and self.T > 0 and 0 < self.beta <= 1 and self.c_s >= 0):
            raise ValueError("need n>0, T>0, 0<beta<=1, c_s>=0")

    def _disc(self, lo: int, hi: int) -> float:
        """sum_{tau=lo}^{hi} beta^tau (empty -> 0)."""
        if hi < lo:
            return 0.0
        if self.beta == 1.0:
            return float(hi - lo + 1)
        tau = np.arange(lo, hi + 1)
        return float(np.sum(self.beta**tau))

    def v_switch(self, t: float, G: float) -> float:
        if self.beta == 1.0:  # Eq. (2), valid for real t
            return -self.c * self.n * self.T - self.c_s + self.n * (self.T - t) * G
        ti = int(t)
        return (
            -self.c * self.n * self._disc(1, ti)
            - self.beta**ti * self.c_s
            + self.n * (G - self.c) * self._disc(ti + 1, self.T)
        )

    def v_discard(self, t: float) -> float:
        if self.beta == 1.0:
            return -self.c * self.n * t
        return -self.c * self.n * self._disc(1, int(t))

    def delta_v(self, t: float, G: float) -> float:
        return self.v_switch(t, G) - self.v_discard(t)


def oracle_value(econ: Economics, t_grid, G_grid) -> tuple[float, int | None]:
    """V_ORACLE = max{0, max_t V_switch(t)} over decision epochs; returns (value, argmax idx or None=discard)."""
    vs = np.array([econ.v_switch(t, g) for t, g in zip(t_grid, G_grid)])
    k = int(np.argmax(vs))
    return (float(vs[k]), k) if vs[k] > 0 else (0.0, None)


def integer_oracle_epoch(econ: Economics, t_grid, G_grid) -> int | None:
    """Epoch index maximising V_switch among candidate epochs; None when discarding is oracle-optimal."""
    return oracle_value(econ, t_grid, G_grid)[1]


def stopping_epoch_thm31(econ: Economics, t_grid, G_grid) -> int:
    """Thm 3.1(3) on a unit-step grid: first k with Phi(t_k) >= Phi(t_{k+1}) (else last)."""
    ph = (econ.T - np.asarray(t_grid, float)) * np.asarray(G_grid, float)
    for k in range(len(ph) - 1):
        if ph[k] >= ph[k + 1]:
            return k
    return len(ph) - 1


def t_dagger_asymptotic(T: float, n: float, g_star: float, g0: float, alpha: float) -> float:
    """Prop 3.2: (g0 alpha T / (g* n^alpha))^(1/(1+alpha))."""
    return (g0 * alpha * T / (g_star * n**alpha)) ** (1.0 / (1.0 + alpha))
