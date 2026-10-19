"""Synthetic stream: decision weights, noise, and concept change at known changepoint."""

from dataclasses import dataclass

import numpy as np


@dataclass
class Stream:
    X: np.ndarray
    y: np.ndarray
    regime: np.ndarray
    noise: np.ndarray


def make_stream(n=3000, d=8, change_at=1500, seed=42, shift_strength=1.0):
    if not 0 < change_at < n:
        raise ValueError("change_at must be inside the stream")
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    regime = (np.arange(n) >= change_at).astype(int)
    beta0 = np.r_[1.0, -0.9, np.zeros(d - 2)]
    beta1 = beta0.copy()
    beta1[0] -= 1.6 * shift_strength
    beta1[1] += 1.3 * shift_strength
    noise = rng.normal(scale=0.3, size=n)
    y = np.where(regime == 0, X @ beta0, X @ beta1) + noise
    return Stream(X=X, y=y, regime=regime, noise=noise)
