"""Coverage simulations for the block-Fieller lower bound and the Design-B simultaneous procedure.

    python sim_coverage.py single  --reps 200000 --out results/coverage_single.csv
    python sim_coverage.py joint   --reps 20000  --out results/coverage_joint.csv
    python sim_coverage.py mbb     --reps 1500   --out results/coverage_mbb.csv

Generator (per dataset): reference b_k = mu_b (1 + cv_b x_k), paired gain D_k = mu_D + sd_D mu_b y_k, where
x, y are unit-variance AR(1) with coefficients phi_b, phi_D and innovation correlation kappa; innovations are
Gaussian or heavy-tailed (Student t5 scaled to unit variance) or skewed (centred lognormal sigma=.8).
True r = 100 mu_D / mu_b. Defaults are taken from the real fresh data (cv_b .12-.32, phi_b .3-.7,
sd_D/mu_b .01-.03 (up to .08), phi_D ~ 0, kappa unknown -> .3).
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from certify import (
    alpha_i,
    block_length,
    fieller_lower_batch,
    mbb_lower,
    primary_lower_batch,
)


def _innov(rng, shape, kind):
    if kind == "gauss":
        return rng.standard_normal(shape)
    if kind == "t5":
        return rng.standard_t(5, shape) / np.sqrt(5 / 3)
    if kind == "lognorm":
        s = 0.8
        z = rng.lognormal(0, s, shape)
        mean, var = np.exp(s * s / 2), (np.exp(s * s) - 1) * np.exp(s * s)
        return (z - mean) / np.sqrt(var)
    raise ValueError(kind)


def _ar1(rng, R, n, phi, e):
    x = np.empty((R, n))
    x[:, 0] = e[:, 0]
    sc = np.sqrt(1 - phi**2)
    for k in range(1, n):
        x[:, k] = phi * x[:, k - 1] + sc * e[:, k]
    return x


def simulate(
    rng,
    R,
    n,
    r_true=2.5,
    cv_b=0.15,
    phi_b=0.55,
    sd_d=0.02,
    phi_d=0.0,
    kappa=0.3,
    kind="gauss",
    mu_b=100.0,
):
    e1, e2 = _innov(rng, (R, n), kind), _innov(rng, (R, n), kind)
    ex, ey = e1, kappa * e1 + np.sqrt(1 - kappa**2) * e2
    x, y = _ar1(rng, R, n, phi_b, ex), _ar1(rng, R, n, phi_d, ey)
    b = mu_b * (1 + cv_b * x)
    d = mu_b * (r_true / 100 + sd_d * y)
    return b - d, b


def single(reps, out, chunk=50000, seed=1):
    rows = []
    grid = list(itertools.product([40, 100], [0.0, 0.3, 0.6], ["gauss", "t5", "lognorm"], [0.02]))
    for n, phi_d, kind, sd_d in grid:
        rng = np.random.default_rng(seed + n * 7 + int(phi_d * 10))
        miss = {
            (meth, al): 0
            for meth in ("primary_min", "t_block", "t_block_sqrt", "normal_block", "t_iid")
            for al in (0.05, 1e-3, 1e-4)
        }
        done = 0
        while done < reps:
            R = min(chunk, reps - done)
            a, b = simulate(rng, R, n, phi_d=phi_d, kind=kind, sd_d=sd_d)
            for al in (0.05, 1e-3, 1e-4):
                miss[("primary_min", al)] += int((primary_lower_batch(a, b, al)[0] > 2.5).sum())
                for meth, (m, crit) in {
                    "t_block": (None, "t"),
                    "t_block_sqrt": (int(np.ceil(np.sqrt(n))), "t"),
                    "normal_block": (None, "normal"),
                    "t_iid": (1, "t"),
                }.items():
                    L, _, _ = fieller_lower_batch(a, b, al, m, crit)
                    miss[(meth, al)] += int((L > 2.5).sum())
            done += R
        for (meth, al), k in miss.items():
            rows.append(
                {
                    "n": n,
                    "phi_D": phi_d,
                    "innov": kind,
                    "sd_D": sd_d,
                    "method": meth,
                    "alpha": al,
                    "reps": reps,
                    "misses": k,
                    "miss_rate": k / reps,
                    "ratio_to_alpha": k / reps / al,
                    "block_len": block_length(n),
                }
            )
        print(n, phi_d, kind, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


def joint(reps, out, seed=2, K=25, max_index=25, chunk=2000):
    """Simultaneous coverage: K datasets with heterogeneous generators and attempt indices 1..K (or a random
    increasing subset of 1..max_index). P(any dataset's bound exceeds its true r) must be <= .05."""
    rows = []
    for scen, kind, phi_hi in [
        ("typical", "gauss", 0.3),
        ("stress", "lognorm", 0.6),
        ("stress_t5", "t5", 0.6),
    ]:
        for idx_mode in ("1..K", "spread_to_60"):
            rng = np.random.default_rng(seed)
            idx = (
                list(range(1, K + 1))
                if idx_mode == "1..K"
                else sorted(rng.choice(np.arange(1, 61), K, replace=False))
            )
            par = [
                {
                    "n": int(rng.integers(30, 101)),
                    "phi_b": float(rng.uniform(0.3, 0.7)),
                    "cv_b": float(rng.uniform(0.1, 0.3)),
                    "sd_d": float(rng.uniform(0.01, 0.05)),
                    "phi_d": float(rng.uniform(0, phi_hi)),
                    "r_true": float(rng.uniform(0, 5)),
                }
                for _ in range(K)
            ]
            any_miss, per_miss = 0, np.zeros(K)
            done = 0
            while done < reps:
                R = min(chunk, reps - done)
                hit = np.zeros(R, bool)
                for j, (i, p) in enumerate(zip(idx, par)):
                    a, b = simulate(rng, R, kind=kind, **p)
                    L = primary_lower_batch(a, b, alpha_i(int(i)))[0]
                    mj = L > p["r_true"]
                    per_miss[j] += mj.sum()
                    hit |= mj
                any_miss += int(hit.sum())
                done += R
            rows.append(
                {
                    "scenario": scen,
                    "innov": kind,
                    "indices": idx_mode,
                    "K": K,
                    "reps": reps,
                    "any_miss": any_miss,
                    "simultaneous_miss_rate": any_miss / reps,
                    "sum_alpha": float(sum(alpha_i(int(i)) for i in idx)),
                    "worst_single_ratio": float(
                        max(per_miss / reps / np.array([alpha_i(int(i)) for i in idx]))
                    ),
                }
            )
            print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


def mbb(reps, out, seed=3, B=2000):
    rows = []
    for n, phi_d, kind in [
        (100, 0.0, "gauss"),
        (100, 0.6, "gauss"),
        (40, 0.3, "gauss"),
        (100, 0.3, "lognorm"),
    ]:
        rng = np.random.default_rng(seed + n)
        a, b = simulate(rng, reps, n, phi_d=phi_d, kind=kind)
        for al in (0.05, 0.01):
            mm = {"mbb_studentised": 0, "t_block": 0}
            for k in range(reps):
                mm["mbb_studentised"] += mbb_lower(a[k], b[k], al, B=B, seed=k)["L"] > 2.5
            L, _, _ = fieller_lower_batch(a, b, al)
            mm["t_block"] = int((L > 2.5).sum())
            for meth, kk in mm.items():
                rows.append(
                    {
                        "n": n,
                        "phi_D": phi_d,
                        "innov": kind,
                        "alpha": al,
                        "method": meth,
                        "reps": reps,
                        "misses": int(kk),
                        "miss_rate": kk / reps,
                    }
                )
        print(n, phi_d, kind, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["single", "joint", "mbb"])
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    {"single": single, "joint": joint, "mbb": mbb}[a.mode](a.reps, a.out)
