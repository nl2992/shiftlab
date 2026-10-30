"""Valid restart mixtures of e-processes (docs/h2c_restart/VALID_RESTART_MIXTURE.md)."""

import numpy as np


def start_weights(kind: str, T: int) -> np.ndarray:
    """Predetermined start-time capital weights w_0..w_{T-1}, summing to 1."""
    w = np.zeros(T)
    if kind == "single":
        w[0] = 1.0
    elif kind == "uniform":
        w[:] = 1.0 / T
    elif kind == "front":
        w[:] = 0.5 / T
        w[0] += 0.5
    elif kind == "geometric":
        w = 0.995 ** np.arange(T)
        w /= w.sum()
    elif kind == "coarse8":
        w[np.arange(0, T, max(T // 8, 1))[:8]] = 1.0 / 8
        w /= w.sum()
    else:
        raise ValueError(kind)
    return w


def log_factors(cum_logw: np.ndarray) -> np.ndarray:
    """Per-step log betting factors from a cumulative log-wealth array (release-time axis)."""
    return np.diff(cum_logw, axis=1, prepend=0.0)


def restart_mixture(logf: np.ndarray, w: np.ndarray) -> np.ndarray:
    """M_t = S_t + sum_{j>t} w_j with S_t = (S_{t-1} + w_t) f_t (shared betting factors). Returns M (S, T)."""
    S, T = logf.shape
    f = np.exp(logf)
    tail = np.cumsum(w[::-1])[::-1]  # tail[t] = sum_{j>=t} w_j
    out = np.empty((S, T))
    s = np.zeros(S)
    for t in range(T):
        s = (s + w[t]) * f[:, t]
        out[:, t] = s + (tail[t + 1] if t + 1 < T else 0.0)
    return out


def sr_statistic(logf: np.ndarray) -> np.ndarray:
    """Shiryaev-Roberts recursion R_t = (1 + R_{t-1}) f_t (unnormalised)."""
    S, T = logf.shape
    f = np.exp(logf)
    out = np.empty((S, T))
    r = np.zeros(S)
    for t in range(T):
        r = (1.0 + r) * f[:, t]
        out[:, t] = r
    return out
