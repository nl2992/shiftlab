"""R1 driver: payback certificates on real paired-loss episodes (registration R1).

Same single-switch driver as ``sim.run_one`` (query schedule, request-time booking, label arrival
at s+d, certify iff ``lcb_sum(t,h) > k``), with two registered differences: a certification is
allowed at every round t <= T and the hold window is truncated to the rounds that exist
(protocol: episodes too short are truncated to the available rounds, reported, not excluded).
Certificates only ever receive ``(s, z[s], t)`` for ``t = s + d``; the future ``z`` is touched
solely by the scorer.
"""

from __future__ import annotations

import numpy as np

from .certificates import (
    B0Forecast,
    B0Window,
    B1Certificate,
    B2Certificate,
    plan_batch_size,
)
from .envelope import Envelope

V, ALPHA, B, K = 0.002, 0.1, 150, 3.0
CERTS = ("B0a", "B0w", "B0b", "B1", "B2")


def make_cert(name: str, env: Envelope, alpha: float, n_plan: int):
    return {
        "B0a": lambda: B0Window(env, alpha, n_plan),
        "B0w": lambda: B0Window(env, alpha, n_plan, gauss=True),
        "B0b": lambda: B0Forecast(env, alpha, n_plan),
        "B1": lambda: B1Certificate(env, alpha),
        "B2": lambda: B2Certificate(env, alpha),
    }[name]()


def score_hold(z: np.ndarray, t: int, h: int, k: float) -> tuple[float, int]:
    """Realised hold payback (before label cost) for a switch at round t (1-indexed, z[0] unused).
    Returns (sum_{j<h', t+j<=T} z[t+j] - k, h') with h' the truncated hold length."""
    T = len(z) - 1
    hh = min(h, T - t + 1)
    return float(z[t : t + hh].sum() - k), hh


def run_episode(z, cert, *, h: int, d: int, B: int = B, k: float = K, n_plan: int):
    """z: length T+1 array, z[0] unused (evaluator-side). Returns dict."""
    T = len(z) - 1
    spent, batch_end, pending, req = 0, 0, {}, 0
    for t in range(1, T + 1):
        for s, val in pending.pop(t, []):
            cert.observe(s, val, t)
        if cert.lcb_sum(t, h) > k:
            gross, hh = score_hold(z, t, h, k)
            return {"certified": True, "t": t, "labels": req, "gross": gross, "hold": hh}
        if t > batch_end and spent < B:
            n = min(n_plan, B - spent)
            spent += n
            cert.start_batch(t, n)
            batch_end = t + n - 1
        if t <= batch_end:
            req += 1
            if t + d <= T:
                pending.setdefault(t + d, []).append((t, float(z[t])))
    return {"certified": False, "t": T, "labels": req, "gross": 0.0, "hold": 0}


def net(r: dict, cq: float) -> float:
    """Realised net payback: hold sum - k - cq*labels (uncertified: -cq*labels)."""
    return r["gross"] - cq * r["labels"]


def episode_z(l0_row, l1_row) -> np.ndarray:
    return np.concatenate([[0.0], l0_row.astype(float) - l1_row.astype(float)])


def run_all(l0_row, l1_row, *, h: int, d: int, alpha: float = ALPHA, names=CERTS) -> dict:
    env = Envelope(V)
    n_plan = plan_batch_size(env, alpha / 2, B)
    z = episode_z(l0_row, l1_row)
    return {
        n: run_episode(z, make_cert(n, env, alpha, n_plan), h=h, d=d, n_plan=n_plan) for n in names
    }
