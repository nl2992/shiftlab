"""S12: two-sample / drift tests, exact and efficient (synthetic). Runtime includes all preprocessing and model fitting."""

from __future__ import annotations

import time
import tracemalloc

import numpy as np
from sklearn.linear_model import LogisticRegression

D_RFF = 256


def median_bw(ref, rng, m=200):
    s = ref[rng.choice(len(ref), min(m, len(ref)), replace=False)]
    d2 = ((s[:, None] - s[None]) ** 2).sum(-1)
    return float(np.sqrt(np.median(d2[d2 > 0]) / 2))


def _rbf(a, b, bw):
    d2 = (a**2).sum(1)[:, None] + (b**2).sum(1)[None] - 2 * a @ b.T
    return np.exp(-np.maximum(d2, 0) / (2 * bw**2))


def mmd_exact(ref, win, rng, bws=(1.0,)):
    bw0 = median_bw(ref, rng)
    out = []
    for f in bws:
        bw = bw0 * f
        krr, kww, krw = _rbf(ref, ref, bw), _rbf(win, win, bw), _rbf(ref, win, bw)
        n, m = len(ref), len(win)
        out.append(
            (krr.sum() - np.trace(krr)) / (n * (n - 1))
            + (kww.sum() - np.trace(kww)) / (m * (m - 1))
            - 2 * krw.mean()
        )
    return np.array(out)


def _rff(d, bw, rng):
    return rng.standard_normal((d, D_RFF)) / bw, rng.uniform(0, 2 * np.pi, D_RFF)


def _phi(x, W, b):
    return np.sqrt(2.0 / D_RFF) * np.cos(x @ W + b)


def mmd_rff(ref, win, rng, bws=(1.0,)):
    bw0 = median_bw(ref, rng)
    out = []
    for f in bws:
        W, b = _rff(ref.shape[1], bw0 * f, rng)
        pr, pw = _phi(ref, W, b), _phi(win, W, b)
        n, m = len(ref), len(win)
        sr, sw = pr.sum(0), pw.sum(0)
        out.append(
            (sr @ sr - (pr**2).sum()) / (n * (n - 1))
            + (sw @ sw - (pw**2).sum()) / (m * (m - 1))
            - 2 * (sr @ sw) / (n * m)
        )
    return np.array(out)


class IncrementalRFF:
    """Sliding-window RFF-MMD: O(D) per observation. The reference feature sums are computed once."""

    def __init__(self, ref, win_len, rng):
        self.bw = median_bw(ref, rng)
        self.W, self.b = _rff(ref.shape[1], self.bw, rng)
        pr = _phi(ref, self.W, self.b)
        self.n = len(ref)
        self.sr = pr.sum(0)
        self.rr = (self.sr @ self.sr - (pr**2).sum()) / (self.n * (self.n - 1))
        self.L, self.buf = win_len, []
        self.sw, self.sq = np.zeros(D_RFF), 0.0

    def update(self, x):
        p = _phi(x[None], self.W, self.b)[0]
        self.buf.append(p)
        self.sw += p
        self.sq += p @ p
        if len(self.buf) > self.L:
            o = self.buf.pop(0)
            self.sw -= o
            self.sq -= o @ o
        m = len(self.buf)
        if m < 2:
            return 0.0
        return (
            self.rr
            + (self.sw @ self.sw - self.sq) / (m * (m - 1))
            - 2 * (self.sr @ self.sw) / (self.n * m)
        )


def c2st_lr(ref, win, rng, **_):
    n = min(len(ref), len(win) * 2)
    r = ref[rng.choice(len(ref), n, replace=False)]
    X = np.vstack([r, win])
    y = np.r_[np.zeros(len(r)), np.ones(len(win))]
    idx = rng.permutation(len(X))
    h = len(X) // 2
    tr, te = idx[:h], idx[h:]
    clf = LogisticRegression(max_iter=200, C=1.0).fit(X[tr], y[tr])
    w = np.where(
        y[te] == 1,
        len(te) / (2 * max((y[te] == 1).sum(), 1)),
        len(te) / (2 * max((y[te] == 0).sum(), 1)),
    )
    bal_acc = np.average(clf.predict(X[te]) == y[te], weights=w)
    return np.array([(bal_acc - 0.5) * np.sqrt(len(te))])


def c2st_lda(ref, win, rng, **_):
    """Closed-form LDA direction (efficient C2ST approximation), held-out t statistic."""
    h = len(win) // 2
    r = ref[rng.choice(len(ref), 2 * h, replace=False)]
    tr_r, te_r, tr_c, te_c = r[:h], r[h:], win[:h], win[h:]
    mu_r, mu_c = tr_r.mean(0), tr_c.mean(0)
    cen = np.vstack([tr_r - mu_r, tr_c - mu_c])
    cov = cen.T @ cen / (2 * h - 2) + 1e-2 * np.eye(ref.shape[1])
    w = np.linalg.solve(cov, mu_c - mu_r)
    zr, zc = te_r @ w, te_c @ w
    return np.array([(zc.mean() - zr.mean()) / (np.sqrt(zr.var() / h + zc.var() / h) + 1e-12)])


def bbsd(ref, win, rng, score_w=None, **_):
    s_r, s_w = 1 / (1 + np.exp(-ref @ score_w)), 1 / (1 + np.exp(-win @ score_w))
    grid = np.sort(np.r_[s_r, s_w])
    return np.array(
        [
            np.abs(
                np.searchsorted(np.sort(s_r), grid, "right") / len(s_r)
                - np.searchsorted(np.sort(s_w), grid, "right") / len(s_w)
            ).max()
        ]
    )


METHODS = {
    "mmd_exact": lambda r, w, g, **k: mmd_exact(r, w, g),
    "mmd_rff": lambda r, w, g, **k: mmd_rff(r, w, g),
    "mmd_multi_exact": lambda r, w, g, **k: mmd_exact(r, w, g, bws=(0.5, 1.0, 2.0)),
    "mmd_multi_rff": lambda r, w, g, **k: mmd_rff(r, w, g, bws=(0.5, 1.0, 2.0)),
    "c2st_lr": c2st_lr,
    "c2st_lda": c2st_lda,
    "bbsd": bbsd,
}


def time_method(name, ref, win, rng, score_w):
    """Wall time and peak traced memory of one test including every preprocessing / fitting step."""
    tracemalloc.start()
    t0 = time.perf_counter()
    val = METHODS[name](ref, win, rng, score_w=score_w)
    wall = time.perf_counter() - t0
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return val, wall, peak
