"""Belief filter b~_t(d)=sum_d' T[d',d] b_{t-1}(d'); b_t(d) ∝ p(z_t|d) b~_t(d)  (paper Sec 3.3 Eq. 10)."""

from __future__ import annotations

import itertools
from typing import Protocol

import numpy as np

DRIFTS = ("none", "covariate", "concept", "subgroup")


class EvidenceModel(Protocol):
    """Q1 hook: swap this layer (e.g. gap-aware evidence).  ``gap`` = t_i - t_{i-1} (default 1)."""

    def log_lik(self, z: np.ndarray, gap: int = 1) -> np.ndarray: ...  # shape (4,)


class GaussianEvidence:
    """Diagonal-Gaussian p(z|d) (App. E.2.5 option); fit on labelled synthetic drift episodes."""

    def __init__(self, mu, var, beta: float = 1.0):
        self.mu, self.var, self.beta = np.asarray(mu, float), np.asarray(var, float), beta

    @classmethod
    def fit(cls, Z, D, var_floor=1e-4, beta=1.0):
        Z, D = np.asarray(Z, float), np.asarray(D)
        mu = np.stack([Z[D == d].mean(0) for d in range(4)])
        var = np.stack([np.maximum(Z[D == d].var(0), var_floor) for d in range(4)])
        return cls(mu, var, beta)

    def log_lik(self, z, gap=1):
        z = np.asarray(z, float)
        ll = -0.5 * (((z - self.mu) ** 2) / self.var + np.log(2 * np.pi * self.var)).sum(1)
        return self.beta * ll


def estimate_T(D_episodes, smooth=0.02):
    """Count-based transition estimate (paper Eq. 121 form) + uniform smoothing (our choice)."""
    C = np.full((4, 4), 1e-3)
    for D in D_episodes:
        for a, b in itertools.pairwise(D):
            C[a, b] += 1
    T = C / C.sum(1, keepdims=True)
    return (1 - smooth) * T + smooth / 4


class BeliefFilter:
    def __init__(self, T, evidence: EvidenceModel):
        self.T, self.evidence = np.asarray(T, float), evidence
        assert np.allclose(self.T.sum(1), 1)
        self.b = np.full(4, 0.25)  # Alg 1: b_0 uniform

    def update(self, z, gap: int = 1):
        pred = self.T.T @ self.b
        ll = self.evidence.log_lik(z, gap)
        w = np.log(np.maximum(pred, 1e-300)) + ll
        w -= w.max()
        b = np.exp(w)
        self.b = b / b.sum()
        return self.b
