"""Candidate A screen A2: allocation from *learned* moments (see SYNTHETIC_PROTOCOL_A2.md).

Burn-in at uniform propensity, per-context IPW estimates from resolved events, hard budget shared.
Synthetic only; no claim. Reuses the A1 generator, bets and delay mechanics.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_next.growth_alloc import allocate, neyman
from shiftlab.dive.rpoq_next.screen_a import (
    ALPHA,
    BOUND,
    BUDGET,
    DELAY,
    Q_MIN,
    SETTINGS,
    K,
    N,
    exact_moments,
)

N0, BURN, REALLOC = 400, 100, 400
SETTINGS = {**SETTINGS, "const": (np.full(K, 0.05), np.full(K, 0.5))}
ARMS = ("uniform", "neyman", "rasi", "growth_fixed", "growth_online")


def _rasi(r_hat, total):
    """Active-to-uniform path with the L2-robust variance objective (adapted, not a reproduction)."""
    q_n, q_u = neyman(r_hat, total, Q_MIN), np.full(K, total / K)
    c = 0.5 * np.sqrt(np.mean(r_hat**2))
    best, best_q = np.inf, q_u
    for s in np.linspace(0, 1, 21):
        q = q_n ** (1 - s) * q_u**s
        q = np.clip(q * total / q.sum(), Q_MIN, 1)
        obj = np.mean(r_hat / q) + c * np.sqrt(np.mean(q**-2.0))
        if obj < best:
            best, best_q = obj, q
    return best_q


def _realloc(kind, mu_hat, r_hat, h, brem, nrem):
    total = K * max(brem, 1) / max(nrem, 1)
    if kind == "uniform":
        return np.full(K, np.clip(total / K, Q_MIN, 1))
    if kind == "neyman":
        return neyman(r_hat, total, Q_MIN)
    if kind == "rasi":
        return _rasi(r_hat, total)
    return allocate(mu_hat, h, r_hat, total, BOUND, Q_MIN)


def run_arm(y, ctx, u, h_ctx, kind):
    S = y.shape[0]
    s_idx = np.arange(S)
    h = h_ctx[ctx]
    q_ctx = np.full((S, K), BURN / N0)
    x, lam, q_ev = np.zeros((S, N)), np.zeros((S, N)), np.zeros((S, N))
    active = np.zeros((S, N), bool)
    z2 = np.zeros((S, N))
    spent = np.zeros(S, int)
    m1, m2, cnt, rs = (np.zeros((S, K)) for _ in range(4))
    log_w, crossed = np.zeros(S), np.zeros(S, bool)
    thr = np.log(1 / ALPHA)

    def resolve(s):
        nonlocal log_w, crossed
        a = active[:, s]
        log_w = log_w + np.where(a, np.log1p(lam[:, s] * x[:, s]), 0.0)
        crossed |= log_w >= thr
        k = ctx[:, s]
        np.add.at(m1, (s_idx, k), np.where(a, x[:, s], 0.0))
        np.add.at(m2, (s_idx, k), np.where(a, x[:, s] ** 2, 0.0))
        np.add.at(rs, (s_idx, k), np.where(a, z2[:, s], 0.0))
        np.add.at(cnt, (s_idx, k), a.astype(float))

    for t in range(N):
        if t >= DELAY:
            resolve(t - DELAY)
        due = t == N0 or (kind == "growth_online" and t > N0 and (t - N0) % REALLOC == 0)
        if due:
            n = np.maximum(cnt, 1)
            mu_hat = np.clip(m1 / n, 0, 1)
            r_hat = np.maximum(rs / n, 1e-3)
            for i in range(S):
                q_ctx[i] = _realloc(kind, mu_hat[i], r_hat[i], h_ctx, BUDGET - spent[i], N - t)
        k = ctx[:, t]
        q = q_ctx[s_idx, k]
        q_ev[:, t] = q
        n_k = cnt[s_idx, k]
        mean, second = m1[s_idx, k] / (n_k + 1), m2[s_idx, k] / (n_k + 1)
        cap = 0.5 / (BOUND * (2.0 / q - 1.0))
        lam[:, t] = np.minimum(
            np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap
        )
        a = spent < BUDGET
        query = a & (u[:, t] < q)
        x[:, t] = np.where(a, h[:, t] + query * (y[:, t] - h[:, t]) / q, 0.0)
        z2[:, t] = np.where(a & query, (y[:, t] - h[:, t]) ** 2 / q, 0.0)
        active[:, t] = a
        spent += query
    for s in range(N - DELAY, N):
        resolve(s)
    return crossed, log_w, spent


def simulate(setting, rho, n_seeds, seed=11, arms=ARMS):
    mu_true, sigma = SETTINGS[setting]
    _, h, _ = exact_moments(mu_true if setting != "null" else SETTINGS["het"][0], sigma, rho)
    rng = np.random.default_rng(seed)
    ctx = rng.integers(0, K, (n_seeds, N))
    y = np.clip(mu_true[ctx] + sigma[ctx] * rng.standard_normal((n_seeds, N)), -1, 1)
    u = rng.random((n_seeds, N))
    return {a: run_arm(y, ctx, u, h, a) for a in arms}


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    res, t0 = {}, time.time()
    for setting in ("null", "const", "hom", "het", "anti"):
        for rho in (0.0, 0.6):
            sim = simulate(setting, rho, n_seeds)
            key = f"{setting}|rho={rho}"
            res[key] = {
                a: {
                    "power": float(c.mean()),
                    "mean_log_wealth": float(w.mean()),
                    "mean_spent": float(s.mean()),
                    "crossed": c.astype(int).tolist(),
                }
                for a, (c, w, s) in sim.items()
            }
            print(
                key,
                {a: round(v["power"], 3) for a, v in res[key].items()},
                f"{time.time() - t0:.0f}s",
                flush=True,
            )
    out = Path("outputs/rpoq_next/screen_a2")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps(
            {
                "n_seeds": n_seeds,
                "protocol": "docs/rpoq_next/SYNTHETIC_PROTOCOL_A2.md",
                "results": res,
            }
        )
    )


if __name__ == "__main__":
    main()
