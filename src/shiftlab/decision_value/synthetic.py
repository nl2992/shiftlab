"""Synthetic families S1-S3 (+ no-change null). Bernoulli losses, CRN via Generator(seed).

Independent sub-streams (structure, losses, acquisition) are spawned from one SeedSequence so the
same seed gives identical data irrespective of the monitor being evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .contracts import EpisodeBatch, EvaluatorTruth, FeedbackContract
from .feedback import make_mask

DEFAULTS = {
    "s1": {
        "T": 3000,
        "p0": 0.2,
        "delta": 0.05,
        "Delta": 0.15,
        "L": 400,
        "tau_lo": 800,
        "tau_hi": 1200,
    },
    "s2": {
        "T": 3000,
        "p0": 0.2,
        "delta": 0.05,
        "Delta": 0.15,
        "rho": 0.99,
        "challenger_bad": "useful",
        "harm_extra": 0.05,
    },
    "s3": {
        "T": 3000,
        "p0": 0.2,
        "delta": 0.05,
        "Delta": 0.15,
        "L": 400,
        "tau_lo": 800,
        "tau_hi": 1200,
        "challenger": "strong",
        "weak_frac": 0.3,
    },
}


@dataclass
class Family:
    name: str
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.name not in DEFAULTS:
            raise ValueError(f"unknown family {self.name}")
        self.params = {**DEFAULTS[self.name], **self.params}

    @property
    def T(self) -> int:
        return int(self.params["T"])

    def generate(self, seed: int, n: int, feedback: FeedbackContract, null: bool = False):
        """Return (EpisodeBatch, EvaluatorTruth). ``null=True``: no change (calibration)."""
        ss = np.random.SeedSequence(int(seed))
        r_struct, r_loss, r_mask = (np.random.default_rng(c) for c in ss.spawn(3))
        p, T = self.params, self.T
        t = np.arange(T)[None, :]
        regime = np.zeros((n, T), dtype=np.int8)
        tau = np.full(n, np.nan)
        if self.name in ("s1", "s3"):
            tau_i = r_struct.integers(
                p["tau_lo"], p["tau_hi"] + 1, size=n
            )  # drawn even for null (CRN)
            tt = tau_i[:, None]
            post = t >= tt
            win = post & (t < tt + p["L"])
            if null:
                post = win = np.zeros((n, T), bool)
            else:
                tau = tau_i.astype(float)
                regime = (post if self.name == "s3" else win).astype(np.int8)
            base1 = np.full((n, T), p["p0"] + p["delta"])
            if self.name == "s1":
                mu0, mu1 = p["p0"] + p["Delta"] * win, base1
            else:
                mu0 = p["p0"] + p["Delta"] * post
                c = p["challenger"]
                if c == "strong":
                    mu1 = base1
                elif c == "weak":
                    mu1 = base1 + (1 - p["weak_frac"]) * (p["Delta"] - p["delta"]) * post
                elif c == "reversing":  # good on [tau, tau+L), then worse than incumbent by delta
                    mu1 = np.where(post & ~win, mu0 + p["delta"], base1)
                elif c == "none":  # challenger = incumbent after the change
                    mu1 = np.where(post, mu0, base1)
                elif c == "common_shock":  # both degrade by Delta; challenger still worse by delta
                    mu1 = base1 + p["Delta"] * post
                else:
                    raise ValueError(f"unknown challenger type {c}")
        else:  # s2: stationary symmetric two-state Markov chain, stay prob rho
            rg, rb = p.get("rho_g"), p.get("rho_b")
            asym = (
                rg is not None or rb is not None
            )  # optional asymmetric chain (default: symmetric, unchanged)
            if asym:
                rg = p["rho"] if rg is None else rg
                rb = p["rho"] if rb is None else rb
                pi_b = (1 - rg) / (2 - rg - rb)  # stationary bad-state probability
                s0 = (r_struct.random(n) < pi_b).astype(np.int64)  # stationary initial state
            else:
                s0 = (r_struct.random(n) < 0.5).astype(np.int64)
            u = r_struct.random((n, T))
            if asym:
                if not null:  # state-dependent stay probability; same uniforms/flip rule as the symmetric path
                    reg = np.empty((n, T), dtype=np.int8)
                    st = s0.astype(np.int8)
                    for tt in range(T):
                        if tt > 0:
                            st = np.where(u[:, tt] > np.where(st == 1, rb, rg), 1 - st, st).astype(
                                np.int8
                            )
                        reg[:, tt] = st
                    regime = reg
                    tau = np.where(regime.any(axis=1), regime.argmax(axis=1), np.nan)
                flips = None
            else:
                flips = u > p["rho"]
                flips[:, 0] = False
            if not null and not asym:
                regime = ((s0[:, None] + np.cumsum(flips, axis=1)) % 2).astype(np.int8)
                tau = np.where(regime.any(axis=1), regime.argmax(axis=1), np.nan)
            bad = regime == 1
            mu0 = p["p0"] + p["Delta"] * bad
            bad1 = {
                "useful": p["p0"],
                "useless": p["p0"] + p["Delta"],
                "harmful": p["p0"] + p["Delta"] + p["harm_extra"],
            }[p["challenger_bad"]]
            mu1 = np.where(bad, bad1, p["p0"] + p["delta"])
        mu0 = np.clip(np.asarray(mu0, float), 0, 1) * np.ones((n, T))
        mu1 = np.clip(np.asarray(mu1, float), 0, 1) * np.ones((n, T))
        l0 = (r_loss.random((n, T)) < mu0).astype(np.float32)
        l1 = (r_loss.random((n, T)) < mu1).astype(np.float32)
        mask = make_mask(r_mask, n, T, feedback.q, feedback.max_queries)
        truth = EvaluatorTruth(mu0, mu1, regime, tau, {"family": self.name, "null": null, **p})
        return EpisodeBatch(l0, l1, mask), truth
