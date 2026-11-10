"""J-pilot for candidate E: label-routing policies for a challenger trained and certified from the same
paid, delayed labels. Stationary synthetic stream (see sim.py). All policies share the same stream,
query coins and incumbent; differ only in how released labels are routed (train / certify / both) and
in the promotion rule. No evaluator truth is visible to a policy.

J = sum_t 0-1 loss of deployed model + c_q*#queries + c_r*#retrains + k*1{promoted}.
Query prob q=B/T per round until promotion (pending labels billed at request; hard cap B).
Promotion freezes the latest version (no rollback implemented: stated limitation).
Labels: IN_HOUSE_HEURISTIC for 'wald' (discounted Wald LCB with label cutoff, inspired by
origin/research/paper1-eqsdp-foundation-2026-11-08@5bda4e73:scripts/paper1_eqsdp/stage2_policies.py
Stage2Wald lam/gamma/stop_h; NOT a native port) and 'plugin' (Challenger-style accumulate-then-adopt).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from shiftlab.paper3.dualuse.sim import LAMS, _sig, _w0


@dataclass
class JCfg:
    d: int = 5
    T: int = 600
    B: int = 240
    delay: int = 10
    gamma: float = 2.0
    eta: float = 0.5
    m: int = 5
    alpha: float = 0.05
    w0_cos: float = 0.3
    c_q: float = 0.05
    c_r: float = 0.05
    k: float = 3.0
    wald_lam: float = 0.98
    wald_stop_h: int = 100  # no promotion in the last stop_h rounds
    plugin_n: int = 60
    policies: tuple = ("never", "preq_all", "split25", "split50", "split75", "wald", "plugin")


def _route_frac(name):
    return {"split25": 0.25, "split50": 0.5, "split75": 0.75}.get(name)


def run_j(cfg: JCfg, R: int, rng: np.random.Generator) -> dict:
    d, T = cfg.d, cfg.T
    X = rng.standard_normal((R, T, d)).astype(np.float32)
    Y = (rng.random((R, T)) < _sig(cfg.gamma * X[:, :, 0])).astype(np.float32)
    # query coins: q=B/T per round; hard cap enforced per policy via cumulative count
    Q = rng.random((R, T)) < cfg.B / T
    w0 = _w0(cfg).astype(np.float32)
    yh0 = (X @ w0 > 0).astype(np.float32)
    l0 = (yh0 != Y).astype(np.float32)
    nl = len(LAMS)
    out = {}
    for pol in cfg.policies:
        W = np.zeros((R, d), np.float32)
        Wp = np.zeros((R, d), np.float32)
        promoted = np.zeros(R, bool)
        nq = np.zeros(R, int)
        nrel = np.zeros(R, int)
        retr = np.zeros(R)
        loss = np.zeros(R)
        logw = np.zeros((R, nl))
        yhg = np.zeros((R, T), np.float32)
        isq = np.zeros((R, T), bool)
        role = np.zeros((R, T), np.int8)  # 1 train, 2 cert, 3 both
        pending_x = np.zeros((R, cfg.m, d), np.float32)
        pending_y = np.zeros((R, cfg.m), np.float32)
        npend = np.zeros(R, int)
        wsum = np.zeros(R)
        wsq = np.zeros(R)
        wn = np.zeros(R)
        f = _route_frac(pol)
        for t in range(T):
            x, y = X[:, t], Y[:, t]
            # --- release label of round s=t-delay (if it was queried) ---
            s = t - cfg.delay
            if s >= 0 and pol != "never":
                rel = isq[:, s] & ~promoted
                if rel.any():
                    ys = Y[:, s]
                    ro = role[:, s]
                    zg = l0[:, s] - (yhg[:, s] != ys).astype(np.float32)
                    cert = rel & (ro >= 2)
                    if pol in ("preq_all",) or f is not None:
                        logw[cert] += np.log1p(LAMS[None, :] * zg[cert, None])
                    if pol == "wald":
                        lam = cfg.wald_lam
                        wsum[cert] = lam * wsum[cert] + zg[cert]
                        wsq[cert] = lam * wsq[cert] + zg[cert] ** 2
                        wn[cert] = lam * wn[cert] + 1
                    if pol == "plugin":
                        # resubstitution comparison on training labels (post-hoc, data-dependent)
                        pass
                    trn = rel & ((ro & 1) > 0)
                    if trn.any():
                        ii = np.where(trn)[0]
                        c = npend[ii]
                        pending_x[ii, c] = X[ii, s]
                        pending_y[ii, c] = ys[ii]
                        npend[ii] += 1
                        full = ii[npend[ii] == cfg.m]
                        if len(full):
                            p = _sig(np.einsum("rmd,rd->rm", pending_x[full], W[full]))
                            W[full] += (
                                cfg.eta
                                * np.einsum("rm,rmd->rd", pending_y[full] - p, pending_x[full])
                                / cfg.m
                            )
                            retr[full] += 1
                            npend[full] = 0
                    nrel[rel] += 1
            # --- promotion decision (uses only released info) ---
            if pol != "never":
                can = ~promoted
                if pol == "preq_all" or f is not None:
                    fire = can & (np.exp(logw).mean(1) >= 1 / cfg.alpha)
                elif pol == "wald":
                    n = np.maximum(wn, 1e-9)
                    mu = wsum / n
                    var = np.maximum(wsq / n - mu**2, 1e-9)
                    neff = np.maximum(n, 1.0)
                    lcb = mu - 1.645 * np.sqrt(var / neff)
                    H = max(T - t, 1)
                    fire = can & (wn > 10) & (lcb > cfg.k / H) & (t <= T - cfg.wald_stop_h)
                else:  # plugin: after plugin_n released labels, adopt if g's resubstitution loss < f0's on them
                    fire = can & (nrel >= cfg.plugin_n) & (t % 1 == 0)
                    if fire.any():
                        # data-dependent adoption test on all released training samples seen so far
                        ii = np.where(fire)[0]
                        upto = max(0, t - cfg.delay + 1)
                        Xs, Ys = X[ii, :upto], Y[ii, :upto]
                        msk = isq[ii, :upto]
                        lg = ((np.einsum("rtd,rd->rt", Xs, W[ii]) > 0) != (Ys > 0.5)).astype(
                            np.float32
                        )
                        l0s = l0[ii, :upto]
                        better = ((l0s - lg) * msk).sum(1) > 0
                        fire[ii] = better
                        # irreversible: also stop deliberating once nrel>=n (discard if not better)
                        promoted_discard = ii[~better]
                        nrel[promoted_discard] = -(10**6)
                if fire.any():
                    promoted |= fire
                    Wp[fire] = W[fire]
            # --- deploy, loss ---
            wdep = np.where(promoted[:, None], Wp, w0[None, :])
            ydep = (np.einsum("rd,rd->r", x, wdep) > 0).astype(np.float32)
            loss += ydep != y
            yhg[:, t] = np.einsum("rd,rd->r", x, W) > 0
            # --- query decision (before promotion only) ---
            want = Q[:, t] & ~promoted & (nq < cfg.B) & (pol != "never")
            isq[:, t] = want
            if f is None:
                role[:, t] = 3
            else:
                u = (nq * 0.6180339887) % 1.0
                role[:, t] = np.where(u < f, 1, 2)
            nq += want
        J = loss + cfg.c_q * nq + cfg.c_r * retr + cfg.k * promoted
        out[pol] = {"J": J, "loss": loss, "nq": nq, "retr": retr, "promoted": promoted}
    return out
