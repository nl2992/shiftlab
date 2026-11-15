"""Evaluator-side harm metrics (use the full tape; never passed to a policy)."""

from __future__ import annotations

import numpy as np


def harm_path(tape, rec, k: float) -> np.ndarray:
    """H_t = k * (#action changes through t) + sum_{s<=t} -a_s (ell0_s - ell1_s), a_0 = 0."""
    a = np.asarray(rec.a, int)
    prev = np.r_[0, a[:-1]]
    z = tape.ell[:, 0] - tape.ell[:, 1]
    return k * np.cumsum(a != prev) + np.cumsum(-(a * z))


def harm_summary(tape, rec, k: float) -> dict:
    h = harm_path(tape, rec, k)
    return {
        "sup_harm": float(max(0.0, h.max())) if len(h) else 0.0,
        "final_harm": float(h[-1]) if len(h) else 0.0,
    }
