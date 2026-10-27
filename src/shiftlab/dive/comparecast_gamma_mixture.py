"""Numerically safe reference implementation of Comparecast's GE mixture.

This independently evaluates Appendix C, equation (49), with initialized
masked-log buffers and uses the paper's conservative bound when z <= 0.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import gammainc, loggamma


def gamma_exponential_log_mixture_paper(
    sums: ArrayLike,
    intrinsic_times: ArrayLike,
    rho: float,
    c: float,
) -> NDArray[np.float64]:
    """Evaluate the paper's gamma-exponential mixture in log space.

    ``sums`` and ``intrinsic_times`` are the cumulative score differential and
    empirical intrinsic-time sequences. ``c`` and ``rho`` follow equation (49)
    in Appendix C of Choe & Ramdas, *Comparing Sequential Forecasters*.
    """
    s = np.asarray(sums, dtype=np.float64)
    v = np.asarray(intrinsic_times, dtype=np.float64)
    if s.shape != v.shape:
        raise ValueError("sums and intrinsic_times must have the same shape")
    if not (np.isfinite(s).all() and np.isfinite(v).all()):
        raise ValueError("sums and intrinsic_times must be finite")
    if np.any(v < 0):
        raise ValueError("intrinsic_times must be nonnegative")
    if not (np.isfinite(rho) and rho > 0 and np.isfinite(c) and c > 0):
        raise ValueError("rho and c must be finite and positive")

    c2 = c * c
    rho_scaled = rho / c2
    a = (v + rho) / c2
    z = (c * s + v + rho) / c2
    leading = (
        rho_scaled * np.log(rho_scaled)
        - loggamma(rho_scaled)
        - np.log(gammainc(rho_scaled, rho_scaled))
    )
    result = np.empty_like(s)
    positive = z > 0
    log_regularized_gamma = np.zeros_like(s)
    np.log(
        gammainc(a, z, out=np.ones_like(s), where=positive),
        out=log_regularized_gamma,
        where=positive,
    )
    result[positive] = (
        leading
        + loggamma(a[positive])
        + log_regularized_gamma[positive]
        - a[positive] * np.log(z[positive])
        + (c * s[positive] + v[positive]) / c2
    )
    result[~positive] = leading - rho_scaled - np.log(a[~positive])
    return result
