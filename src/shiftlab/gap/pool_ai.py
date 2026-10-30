"""S07: pool-based active inference benchmark (synthetic). The learner sees the unlabeled covariate pool and picks
items without replacement. The pool is split into B random blocks in advance; block j's items are selected by
Poisson sampling with probabilities computed from labels of blocks < j, and the estimate is the average of the
per-block prediction-powered estimators (a martingale, unbiased for the pool mean of y for any adaptive rule).

Methods: uniform; batch_asi (probabilities from one pilot block); seq_asi (updated every block); robust_asi
(sequential, (1-eps) ASI + eps uniform); pai_inspired (sequential ASI with the predictor re-fitted on all labels so
far; SOURCE_INSPIRED_NOT_VERIFIED: the primary source/code were not accessible, so this is not a reproduction);
conservative (sequential ASI with the uncertainty model shrunk to its prior by label count + exploration floor).
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PoolWorld:
    N: int = 5000
    d: int = 5
    n: int = 300  # expected label budget
    n0: int = 30  # initial labeled pilot (uniform), counted in the budget
    hetero: float = 1.0  # strength of noise heterogeneity
    misspec: str = (
        "none"  # 'none' | 'wrong_uncertainty' (uncertainty model cannot represent the noise law)
    )
    blocks: int = 5
    eps: float = 0.25


def gen(w: PoolWorld, rng):
    x = rng.standard_normal((w.N, w.d))
    g = np.sin(x[:, 0]) + 0.5 * x[:, 1] * x[:, 2] + 0.3 * x[:, 3]
    sd = 0.3 + w.hetero * 1.2 * (
        1 / (1 + np.exp(-3 * (x[:, 0] - 0.5)))
    )  # noise heteroscedastic in x_0
    if w.misspec == "wrong_uncertainty":
        sd = 0.3 + w.hetero * 1.2 * (
            np.abs(x[:, 4]) > 1.0
        )  # depends on a feature the uncertainty model downweights
    y = g + sd * rng.standard_normal(w.N)
    return x, y


def _feat(x):
    return np.c_[np.ones(len(x)), x, np.abs(x), x**2]


def _fit(F, t, lam=1.0, wts=None):
    wt = np.ones(len(F)) if wts is None else wts
    return np.linalg.solve(
        (F * wt[:, None]).T @ F + lam * np.eye(F.shape[1]), (F * wt[:, None]).T @ t
    )


def run_method(w: PoolWorld, method: str, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    x, y = gen(w, rng)
    N = w.N
    F = _feat(x)
    blocks = np.array_split(rng.permutation(N), w.blocks)
    adaptive = method != "uniform"
    per_block = (w.n - w.n0) / (w.blocks - 1) if adaptive else w.n / w.blocks
    cols = slice(0, 1 + w.d) if w.misspec == "wrong_uncertainty" else slice(None)
    lab, lab_w = [], []
    f_coef = u_coef = None
    ests, vars_, n_lab, t_sel = [], [], 0, 0.0
    for j, blk in enumerate(blocks):
        t0 = time.perf_counter()
        if not adaptive or j == 0 or f_coef is None:
            pi = np.full(len(blk), min((w.n0 if adaptive else per_block) / len(blk), 1.0))
            f = np.zeros(len(blk)) if f_coef is None else F[blk] @ f_coef
        else:
            refit = method != "batch_asi" or j == 1
            if refit:
                idx, wt = np.concatenate(lab), np.concatenate(lab_w)
                ww = (
                    wt if method == "pai_inspired" else None
                )  # PAI-inspired: importance-weighted refits
                f_coef = _fit(F[idx], y[idx], wts=ww)
                u_coef = _fit(F[idx][:, cols], np.abs(y[idx] - F[idx] @ f_coef), lam=3.0, wts=ww)
            f = F[blk] @ f_coef
            u = np.maximum(F[blk][:, cols] @ u_coef, 0.05)
            if method == "conservative":
                shrink = len(np.concatenate(lab)) / (len(np.concatenate(lab)) + 50.0)
                u = shrink * u + (1 - shrink) * u.mean()
            pi = per_block * u / u.sum()
            e = {"robust_asi": w.eps, "conservative": 0.25}.get(method, 0.0)
            pi = np.clip((1 - e) * pi + e * per_block / len(blk), 0.01, 1.0)
        t_sel += time.perf_counter() - t0
        xi = rng.random(len(blk)) < pi
        terms = f + xi * (y[blk] - f) / pi
        ests.append(terms.mean())
        vars_.append(terms.var(ddof=1) / len(blk))
        n_lab += int(xi.sum())
        lab.append(blk[xi])
        lab_w.append(1.0 / pi[xi])
        if f_coef is None and xi.sum() >= 5:  # first fit after the pilot block
            f_coef = _fit(F[blk[xi]], y[blk[xi]])
            u_coef = _fit(F[blk[xi]][:, cols], np.abs(y[blk[xi]] - F[blk[xi]] @ f_coef), lam=3.0)
    sizes = np.array([len(b) for b in blocks], dtype=float)
    return {
        "est": float(np.sum(sizes * ests) / N),
        "truth": float(y.mean()),
        "var": float(np.sum(sizes**2 * np.array(vars_)) / N**2),
        "labels": n_lab,
        "sel_time": t_sel,
    }


METHODS = ("uniform", "batch_asi", "seq_asi", "robust_asi", "pai_inspired", "conservative")


def evaluate(w: PoolWorld, method: str, reps: int, seed0: int) -> dict:
    t0 = time.perf_counter()
    tracemalloc.start()
    rs = [run_method(w, method, seed0 + i) for i in range(reps)]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall = time.perf_counter() - t0
    err = np.array([r["est"] - r["truth"] for r in rs])
    se = np.sqrt([r["var"] for r in rs])
    cover = np.mean(np.abs(err) <= 1.96 * se)
    return {
        "mse": float(np.mean(err**2)),
        "bias": float(err.mean()),
        "ci_width": float(np.mean(2 * 1.96 * se)),
        "coverage": float(cover),
        "labels": float(np.mean([r["labels"] for r in rs])),
        "sel_time_ms": 1e3 * float(np.mean([r["sel_time"] for r in rs])),
        "e2e_ms": 1e3 * wall / reps,
        "peak_mb": peak / 1e6,
    }
