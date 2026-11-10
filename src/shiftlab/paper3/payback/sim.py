"""Evaluator-side streams and the certification simulator (one switch, hold-for-h)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .certificates import plan_batch_size
from .envelope import Envelope

DEV_BASE = (
    5301500000  # inside the registered dev block [5301000000, 5301999999] of seed_registry_v1
)
SMOKE_BASE = 5300500000


@dataclass(frozen=True)
class Spec:
    T: int
    B: int
    d: int
    h: int
    k: float
    alpha: float
    env: Envelope
    h_grid: tuple = ()  # optional set of hold horizons the certifier may adaptively choose from

    @property
    def hs(self) -> tuple:
        return self.h_grid or (self.h,)


def make_stream(kind: str, spec: Spec, seed_parts: tuple, v_true: float | None = None):
    """Return (mu, z).  ``kind`` in {drift, boundary, dwell, stress_reversal, stress_fastdrift, stress_dep}."""
    rng = np.random.default_rng(np.random.SeedSequence(list(seed_parts)))
    T, v = spec.T, spec.env.v
    mu = np.empty(T + 1)  # index 1..T
    L0 = rng.uniform(0.35, 0.95)
    mu[0] = mu[1] = L0
    if kind == "drift":
        sl, stay = 0, 0.95
        for t in range(2, T + 1):
            if rng.random() > stay:
                sl = rng.choice([-1, 0, 1])
            mu[t] = np.clip(mu[t - 1] + sl * v, -1, 1)
    elif kind == "boundary":  # adversarial: flat then max-rate decline from a random onset
        on = int(rng.integers(5, 80))
        for t in range(2, T + 1):
            mu[t] = np.clip(mu[t - 1] - (v if t > on else 0.0), -1, 1)
    elif kind == "dwell":
        J, hd = spec.env.jump, spec.env.hd
        nxt = int(rng.integers(5, 5 + 2 * hd))
        for t in range(2, T + 1):
            step = rng.uniform(-v, v)
            if t == nxt:
                step = J * rng.choice([-1, 1])
                nxt = t + hd + int(rng.geometric(1 / hd))
            mu[t] = np.clip(mu[t - 1] + step, -1, 1)
    elif kind == "stress_reversal":  # abrupt reversal of size 0.9 at a random time: violates J
        on = int(rng.integers(20, 120))
        for t in range(2, T + 1):
            mu[t] = mu[t - 1] - (0.9 if t == on else 0.0) + (rng.uniform(-v, v))
            mu[t] = np.clip(mu[t], -1, 1)
    elif kind == "stress_fastdrift":  # true drift 3x the declared v
        on = int(rng.integers(5, 80))
        for t in range(2, T + 1):
            mu[t] = np.clip(mu[t - 1] - (3 * v if t > on else 0.0), -1, 1)
    elif kind == "stress_dep":  # same mean path as 'boundary' but dependent labels (MDS violated)
        on = int(rng.integers(5, 80))
        for t in range(2, T + 1):
            mu[t] = np.clip(mu[t - 1] - (v if t > on else 0.0), -1, 1)
    elif kind.startswith(("null_flat", "null_decline")):
        # true hold payback <= 0 for every start t >= t_ref and every h in the grid (tight for hmax)
        base, hm = spec.k / max(spec.hs), max(spec.hs)
        t_ref = int(kind.split(":")[1]) if ":" in kind else 5
        for t in range(1, T + 1):
            mu[t] = (
                base
                if kind.startswith("null_flat")
                else np.clip(base + v * (hm - 1) / 2 + v * (t_ref - t), -1, 1)
            )
        mu[0] = mu[1]
    elif kind == "stress_flip":  # E-kill case: square-wave mean, half-period 100, abrupt sign flips
        amp, ph = rng.uniform(0.4, 0.9), int(rng.integers(0, 200))
        for t in range(1, T + 1):
            mu[t] = amp if ((t - 1 + ph) // 100) % 2 == 0 else -amp
        mu[0] = mu[1]
    else:
        raise ValueError(kind)
    p = (1 + mu[1:]) / 2
    u = rng.random(T)
    z = np.where(u < p, 1.0, -1.0)
    if kind == "stress_dep":
        keep = rng.random(T) < 0.7
        for t in range(1, T):
            if keep[t]:
                z[t] = z[t - 1]
    full_mu = np.concatenate([[mu[1]], mu[1:]])  # 1-indexed: full_mu[t]
    full_z = np.concatenate([[0.0], z])
    return full_mu, full_z


def run_one(
    spec: Spec, mu: np.ndarray, z: np.ndarray, make_cert: Callable, n_plan: int | None = None
) -> dict:
    """Single-switch run.  The certifier is given only (request time, z, arrival time)."""
    T, B, d, _h, k = spec.T, spec.B, spec.d, spec.h, spec.k
    cert = make_cert()
    if n_plan is None:
        n_plan = plan_batch_size(spec.env, spec.alpha / 2, B)
    spent, batch_end, pending = 0, 0, {}
    req_count = 0
    for t in range(1, T + 1):
        for s, val in pending.pop(t, []):
            cert.observe(s, val, t)
        cands = [(cert.lcb_sum(t, hh), hh) for hh in spec.hs if t + hh - 1 <= T]
        if cands:
            lcb, hh = max(cands)
            if lcb > k:
                net_mean = float(mu[t : t + hh].sum() - k)
                net_real = float(z[t : t + hh].sum() - k)
                return {
                    "certified": True,
                    "t": t,
                    "h": hh,
                    "labels": req_count,
                    "net_mean": net_mean,
                    "net_real": net_real,
                    "wrong": net_mean <= 1e-9,
                }
        # query schedule (depends on nothing but budget and clock)
        if t > batch_end and spent < B:
            n = min(n_plan, B - spent)
            spent += n  # reserved at commitment
            cert.start_batch(t, n)
            batch_end = t + n - 1
        if t <= batch_end:
            req_count += 1
            if t + d <= T:
                pending.setdefault(t + d, []).append((t, float(z[t])))
    return {
        "certified": False,
        "t": T,
        "labels": req_count,
        "net_mean": 0.0,
        "net_real": 0.0,
        "wrong": False,
    }
