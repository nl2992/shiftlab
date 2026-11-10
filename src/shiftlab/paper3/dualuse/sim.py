"""Candidate E kill test: prequential (test-then-train) certification of an online challenger.

Vectorised over R replications (numpy). Evaluator-side truth (regime schedule, conditional label
probabilities) is used ONLY in `forward_gap` and never by the gates.

Stream: x~N(0,I_d); y~Bern(sigmoid(gamma * r_t * x[0])); r_t=+1 (stationary) or a periodic +-1
schedule of half-period L with random phase per replication. Loss = 0-1, Z_t = l0 - lg in [-1,1].
Challenger g: logistic regression, minibatch SGD every m labels (version = parameter vector).
Gates use e = mean_j prod_t (1+lam_j Z_t), lam_j in a fixed grid <= .5 (valid mixture e-process).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

LAMS = np.array([0.05, 0.1, 0.2, 0.3, 0.4, 0.5])


@dataclass
class KillCfg:
    d: int = 5
    T: int = 600
    gamma: float = 2.0
    eta: float = 0.5  # SGD step on the batch-mean gradient
    m: int = 5  # labels per version (retrain batch)
    alpha: float = 0.05
    periodic_L: int = 0  # 0 => stationary
    w0_cos: float = 1.0  # incumbent direction: cos angle to the true axis e1 (1.0 => Bayes-optimal)
    horizons: tuple = (25, 50, 100, 200)
    gates: tuple = ("preq", "resub", "peek_z", "restart_naive", "restart_spend", "split", "holdout")
    n_train_hold: int = (
        40  # holdout gate: version frozen after this many rounds, certified afterwards
    )


def _sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _w0(cfg: KillCfg):
    w = np.zeros(cfg.d)
    w[0] = cfg.w0_cos
    if cfg.d > 1:
        w[1] = np.sqrt(max(0.0, 1 - cfg.w0_cos**2))
    return w


def run_chunk(cfg: KillCfg, R: int, rng: np.random.Generator) -> dict:
    d, T, m, a = cfg.d, cfg.T, cfg.m, cfg.alpha
    w0 = _w0(cfg)
    X = rng.standard_normal((R, T, d)).astype(np.float32)
    U = rng.random((R, T))
    phase = rng.integers(0, max(2 * cfg.periodic_L, 1), size=R)
    t_idx = np.arange(T)
    if cfg.periodic_L:
        r = np.where(((t_idx[None, :] + phase[:, None]) // cfg.periodic_L) % 2 == 0, 1.0, -1.0)
    else:
        r = np.ones((R, T))
    Y = (U < _sig(cfg.gamma * r * X[:, :, 0])).astype(np.float32)
    yhat0 = (X @ w0.astype(np.float32) > 0).astype(np.float32)
    l0 = (yhat0 != Y).astype(np.float32)

    W = np.zeros((R, d), np.float32)  # running version (all-label training)
    Ws = np.zeros((R, d), np.float32)  # split-gate version (trained on odd rounds only)
    nl = len(LAMS)
    logw = {g: np.zeros((R, nl)) for g in cfg.gates}
    promo = {g: np.full(R, -1) for g in cfg.gates}
    snap_pre = np.zeros((R, d), np.float32)
    snap_post = np.zeros((R, d), np.float32)
    Wh = None
    sumZ = np.zeros(R)
    sumZ2 = np.zeros(R)
    n_ev = np.zeros(R)
    bx, by, sx, sy = [], [], [], []

    def upd(Wc, xs, ys):
        xs = np.stack(xs, 1)
        ys = np.stack(ys, 1)
        p = _sig(np.einsum("rmd,rd->rm", xs, Wc))
        return Wc + cfg.eta * np.einsum("rm,rmd->rd", ys - p, xs) / xs.shape[1]

    for t in range(T):
        x, y = X[:, t], Y[:, t]
        if t == cfg.n_train_hold:
            Wh = W.copy()  # frozen external-style candidate (trained on rounds < n, never again)
        yg = (np.einsum("rd,rd->r", x, W) > 0).astype(np.float32)
        Z = l0[:, t] - (yg != y).astype(np.float32)
        v = t // m
        for g in cfg.gates:
            if g == "peek_z":
                continue
            if g == "preq" or g in ("restart_naive", "restart_spend"):
                Zg = Z
            elif (
                g == "resub"
            ):  # NOT predictable: version updated with this very label, then evaluated
                Wv = W + cfg.eta * (y - _sig((x * W).sum(1)))[:, None] * x
                Zg = l0[:, t] - ((np.einsum("rd,rd->r", x, Wv) > 0).astype(np.float32) != y).astype(
                    np.float32
                )
            elif g == "holdout":
                if t < cfg.n_train_hold:
                    continue
                Zg = l0[:, t] - ((np.einsum("rd,rd->r", x, Wh) > 0).astype(np.float32) != y).astype(
                    np.float32
                )
            elif g == "split":
                if t % 2 == 1:
                    continue  # odd rounds: training only; even rounds: certification only
                ygs = (np.einsum("rd,rd->r", x, Ws) > 0).astype(np.float32)
                Zg = l0[:, t] - (ygs != y).astype(np.float32)
            else:
                raise ValueError(g)
            if g in ("restart_naive", "restart_spend") and t % m == 0:
                logw[g] = np.zeros((R, nl))
            logw[g] = logw[g] + np.log1p(LAMS[None, :] * Zg[:, None])
            E = np.exp(logw[g]).mean(axis=1)
            thr = (v + 1) * (v + 2) / a if g == "restart_spend" else 1.0 / a
            fire = (E >= thr) & (promo[g] < 0)
            promo[g][fire] = t
            if g == "preq":
                snap_pre[fire] = W[fire]
        if "peek_z" in cfg.gates:
            sumZ += Z
            sumZ2 += Z**2
            n_ev += 1
            if t >= 30:
                mu = sumZ / n_ev
                sd = np.sqrt(np.maximum(sumZ2 / n_ev - mu**2, 1e-12))
                fire = (mu / (sd / np.sqrt(n_ev)) >= 1.645) & (promo["peek_z"] < 0)
                promo["peek_z"][fire] = t
        # train after evaluation (predictable)
        bx.append(x)
        by.append(y)
        if len(bx) == m:
            W = upd(W, bx, by)
            bx, by = [], []
        if t % 2 == 1:
            sx.append(x)
            sy.append(y)
            if len(sx) == m:
                Ws = upd(Ws, sx, sy)
                sx, sy = [], []
        fire = promo["preq"] == t
        if fire.any():
            snap_post[fire] = W[fire]  # latest version after any update closed at t
    return {
        "promo": promo,
        "snap_pre": snap_pre,
        "snap_post": snap_post,
        "snap_hold": Wh,
        "phase": phase,
        "w0": w0,
    }


def forward_gap(cfg: KillCfg, out: dict, bank: np.ndarray, which="snap_post", gate="preq"):
    """Evaluator-side exact (Rao-Blackwellised on a shared x-bank) expected forward excess of the
    frozen promoted version over the incumbent, summed over h rounds after promotion.
    Returns dict h -> array (nan where not promoted)."""
    pr = out["promo"][gate]
    idx = np.where(pr >= 0)[0]
    Wp = out[which]
    pb = _sig(cfg.gamma * bank[:, 0])
    w0hat = (bank @ out["w0"].astype(np.float32) > 0).astype(np.float32)[:, None]
    delta = {1: np.full(len(pr), np.nan), -1: np.full(len(pr), np.nan)}
    if len(idx):
        yh = (bank @ Wp[idx].T > 0).astype(np.float32)
        for s in (1, -1):
            p = (pb if s == 1 else 1 - pb)[:, None]
            r0 = (w0hat * (1 - p) + (1 - w0hat) * p).mean(0)
            rg = (yh * (1 - p) + (1 - yh) * p).mean(0)
            delta[s][idx] = r0 - rg
    res = {}
    for h in cfg.horizons:
        vals = np.full(len(pr), np.nan)
        for i in idx:
            if cfg.periodic_L:
                s_now = np.arange(pr[i] + 1, pr[i] + 1 + h)
                reg = np.where(((s_now + out["phase"][i]) // cfg.periodic_L) % 2 == 0, 1, -1)
                vals[i] = (reg == 1).sum() * delta[1][i] + (reg == -1).sum() * delta[-1][i]
            else:
                vals[i] = h * delta[1][i]
        res[h] = vals
    return res


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(c - hw), float(c + hw)
