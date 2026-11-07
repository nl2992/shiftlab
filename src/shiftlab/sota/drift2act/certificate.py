"""Exact certificate of Drift2Act App. D.  Valid only under the conditions in Certificate.CONDITIONS."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def rad(n: int, delta: float) -> float:
    """rad(n,delta) = sqrt(log(pi^2 n^2 / (6 delta)) / (2 n)); Hoeffding + stitched delta_n = 6 delta/(pi^2 n^2)."""
    if n <= 0:
        return math.inf
    return math.sqrt(math.log(math.pi**2 * n * n / (6.0 * delta)) / (2.0 * n))


def rad_fp(n: int, delta: float, N: int) -> float:
    """Finite-population (without replacement) variant quoted in App. D: factor (1-(n-1)/N)."""
    if n <= 0:
        return math.inf
    return math.sqrt(
        max(0.0, 1.0 - (n - 1) / N) * math.log(math.pi**2 * n * n / (6.0 * delta)) / (2.0 * n)
    )


@dataclass
class CertResult:
    t: int
    n: int
    risk_hat: float
    radius: float
    U: float
    delta_used: float
    gate_ok: bool


class Certificate:
    """U_t = R^_t + rad(n, delta_t); gate U_t <= tau.  Independent of how n / which labels were requested.

    CONDITIONS (paper App. D, Condition A): labelled indices are a UNIFORM random sample of the window,
    selection independent of unobserved labels given history; losses in [0,1]; i.i.d. draws (with
    replacement; fp variant for without replacement).  NOT valid under informative selection, serial
    dependence breaking the window-population view, or non-uniform / label-dependent index choice.
    delta_mode 'alg1': delta_t = 6 delta/(pi^2 t^2) as in Alg. 1 (union over t on top of the n-stitching;
    conservative).  'mandate': delta used directly (Sec A2 of the mandate).
    """

    CONDITIONS = (
        "uniform index sampling from the window",
        "independent of unobserved labels given history",
        "losses in [0,1]",
        "iid draws from finite-window population",
    )

    def __init__(
        self, tau: float = 0.20, delta: float = 0.05, delta_mode: str = "alg1", fp: bool = False
    ):
        assert delta_mode in ("alg1", "mandate")
        self.tau, self.delta, self.delta_mode, self.fp = tau, delta, delta_mode, fp

    def delta_t(self, t: int) -> float:
        return (
            6.0 * self.delta / (math.pi**2 * max(t, 1) ** 2)
            if self.delta_mode == "alg1"
            else self.delta
        )

    def compute(self, losses, t: int, window_size: int | None = None) -> CertResult:
        losses = np.asarray(losses, float)
        if losses.size and (losses.min() < 0 or losses.max() > 1):
            raise ValueError("losses must lie in [0,1]")
        n = int(losses.size)
        dt = self.delta_t(t)
        if n == 0:
            return CertResult(t, 0, float("nan"), math.inf, math.inf, dt, False)
        r = rad_fp(n, dt, window_size) if (self.fp and window_size) else rad(n, dt)
        rh = float(losses.mean())
        U = rh + r
        return CertResult(t, n, rh, r, U, dt, U <= self.tau)
