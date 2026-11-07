"""ELEC2 loader and semi-synthetic injectors (Sec 5). Injector details beyond the paper text are
reconstruction choices (recorded in docs/d2a_rar/baselines/RAR.md)."""

from __future__ import annotations

import hashlib

import numpy as np

ELEC2_SHA256 = "c10a416790ef8ab96089e5adfd2febb7c9cec72bd80dfecb2342f2283b86b88a"


def load_elec2(path, verify=True):
    with open(path, "rb") as fh:
        raw = fh.read()
    h = hashlib.sha256(raw).hexdigest()
    if verify and h != ELEC2_SHA256:
        raise ValueError(f"ELEC2 checksum mismatch: {h}")
    rows = raw.decode().strip().splitlines()[1:]
    X = np.array([[float(v) for v in r.split(",")[:8]] for r in rows])
    y = np.array([1 if r.split(",")[8].strip() == "UP" else 0 for r in rows])
    return X, y, h


def semi_abrupt(X, y, seed, warmup=1000):
    """Label flip at onset u ~ U[0.4T, 0.8T] (Sec 5). Returns X, y', onset."""
    rng = np.random.default_rng(10_000 + seed)
    T = len(y)
    u = int(rng.uniform(0.4 * T, 0.8 * T))
    y2 = y.copy()
    y2[u:] = 1 - y2[u:]
    return X, y2, {"onset": u}


def semi_rollback_then_drift(X, y, seed, warmup=1000, block_frac=0.05, gap=1500):
    """Transient blatant corruption (uniform resampling per feature from the warm-up domain) of
    block_frac*T instances, then after ``gap`` instances an abrupt label flip.  Block/onset placement
    is a reconstruction choice."""
    rng = np.random.default_rng(20_000 + seed)
    T = len(y)
    L = int(block_frac * T)
    s = int(rng.uniform(0.25 * T, 0.45 * T))
    lo, hi = X[:warmup].min(0), X[:warmup].max(0)
    X2 = X.copy()
    X2[s : s + L] = rng.uniform(lo, hi, size=(L, X.shape[1]))
    u = s + L + gap
    y2 = y.copy()
    y2[u:] = 1 - y2[u:]
    return X2, y2, {"corrupt_start": s, "corrupt_len": L, "onset": u}
