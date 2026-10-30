"""Candidate A development screen (see docs/rpoq_next/SYNTHETIC_PROTOCOL.md).

Vectorized over seeds. Exact-estimate allocation, per-context or pooled Kelly bets, fixed label
delay, hard budget, evidence through the resolved prefix. Synthetic only; no claim.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_next.growth_alloc import allocate, neyman

K, N, BUDGET, DELAY, ALPHA, Q_MIN, BOUND = 8, 4000, 400, 20, 0.05, 0.02, 1.0
SIGMA = np.linspace(0.2, 0.8, K)
MU_HET = np.array([0, 0, 0, 0.02, 0.04, 0.06, 0.10, 0.14])
SETTINGS = {
    "hom": (np.full(K, 0.05), SIGMA),
    "het": (MU_HET, SIGMA[[3, 0, 6, 1, 7, 2, 5, 4]]),
    "anti": (MU_HET, SIGMA),
    "null": (np.zeros(K), SIGMA[[3, 0, 6, 1, 7, 2, 5, 4]]),
}


def exact_moments(mu, sigma, rho):
    """Mean and residual second moment of the clipped law, by fixed-seed Monte Carlo."""
    eps = np.random.default_rng(1).standard_normal((K, 1_000_000))
    y = np.clip(mu[:, None] + sigma[:, None] * eps, -1, 1)
    m = y.mean(1)
    h = rho * m
    return m, h, ((y - h[:, None]) ** 2).mean(1)


def propensities(kind, mu, h, r):
    if kind == "uniform":
        return np.full(K, BUDGET / N)
    if kind == "neyman":
        return neyman(r, K * BUDGET / N, Q_MIN)
    return allocate(mu, h, r, K * BUDGET / N, BOUND, Q_MIN)


def run_arm(y, ctx, u, h_ctx, q_ctx, bet, n_seeds):
    """Return (crossed[S], final log-wealth[S], spent[S]) for one arm."""
    s_idx = np.arange(n_seeds)
    q = q_ctx[ctx]
    h = h_ctx[ctx]
    cap = 0.5 / (BOUND * (2.0 / q - 1.0))
    x = np.zeros((n_seeds, N))
    lam = np.zeros((n_seeds, N))
    active = np.zeros((n_seeds, N), bool)
    spent = np.zeros(n_seeds, int)
    m1, m2, cnt = (np.zeros((n_seeds, K)), np.zeros((n_seeds, K)), np.zeros((n_seeds, K)))
    log_w = np.zeros(n_seeds)
    crossed = np.zeros(n_seeds, bool)
    thr = np.log(1 / ALPHA)

    def resolve(s):
        nonlocal log_w, crossed
        a = active[:, s]
        log_w = log_w + np.where(a, np.log1p(lam[:, s] * x[:, s]), 0.0)
        crossed |= log_w >= thr
        k = ctx[:, s]
        np.add.at(m1, (s_idx, k), np.where(a, x[:, s], 0.0))
        np.add.at(m2, (s_idx, k), np.where(a, x[:, s] ** 2, 0.0))
        np.add.at(cnt, (s_idx, k), a.astype(float))

    for t in range(N):
        if t >= DELAY:
            resolve(t - DELAY)
        k = ctx[:, t]
        if bet == "ctx":
            a1, a2, n = m1[s_idx, k], m2[s_idx, k], cnt[s_idx, k]
        else:
            a1, a2, n = m1.sum(1), m2.sum(1), cnt.sum(1)
        mean, second = a1 / (n + 1), a2 / (n + 1)
        lam[:, t] = np.minimum(
            np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap[:, t]
        )
        a = spent < BUDGET
        query = a & (u[:, t] < q[:, t])
        x[:, t] = np.where(a, h[:, t] + query * (y[:, t] - h[:, t]) / q[:, t], 0.0)
        active[:, t] = a
        spent += query
    for s in range(N - DELAY, N):
        resolve(s)
    return crossed, log_w, spent


def simulate(
    setting, rho, n_seeds, seed=7, bets=("ctx", "common"), kinds=("uniform", "neyman", "growth")
):
    mu_true, sigma = SETTINGS[setting]
    mu, h, r = exact_moments(mu_true, sigma, rho)
    rng = np.random.default_rng(seed)
    ctx = rng.integers(0, K, (n_seeds, N))
    y = np.clip(mu_true[ctx] + sigma[ctx] * rng.standard_normal((n_seeds, N)), -1, 1)
    u = rng.random((n_seeds, N))
    out = {}
    for kind in kinds:
        # allocator gets the alternative's exact moments, also on the null stream (calibration check)
        alt_mu, alt_h, alt_r = (
            exact_moments(SETTINGS["het"][0], SETTINGS["het"][1], rho)
            if setting == "null"
            else (mu, h, r)
        )
        q_ctx = propensities(kind, alt_mu, alt_h, alt_r)
        for bet in bets:
            out[f"{kind}+{bet}"] = run_arm(y, ctx, u, h, q_ctx, bet, n_seeds)
    return out


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    res, t0 = {}, time.time()
    for setting in ("null", "hom", "het", "anti"):
        for rho in (0.0, 0.6):
            sim = simulate(setting, rho, n_seeds)
            res[f"{setting}|rho={rho}"] = {
                a: {
                    "power": float(c.mean()),
                    "mean_log_wealth": float(w.mean()),
                    "mean_spent": float(s.mean()),
                    "crossed": c.astype(int).tolist(),
                }
                for a, (c, w, s) in sim.items()
            }
            print(
                setting,
                rho,
                {a: round(v["power"], 3) for a, v in res[f"{setting}|rho={rho}"].items()},
                f"{time.time() - t0:.0f}s",
                flush=True,
            )
    out = Path("outputs/rpoq_next/screen_a1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps(
            {"n_seeds": n_seeds, "protocol": "docs/rpoq_next/SYNTHETIC_PROTOCOL.md", "results": res}
        )
    )


if __name__ == "__main__":
    main()
