"""D0 baselines, D1/D2 recommenders, D4 OOD fallback. All operate on the J table.

A selector for a held-out stream sees: its own early-window episodes [0, n_early) (embedding from
the reference policy's operational log; 'replay' methods also see the early-window J of every
configuration, i.e. counterfactual replay, which is charged), the training streams' tables, and
costs. It never sees episodes >= n_early of the held-out stream (except Hedge, which receives
full-information feedback for *past* episodes only, charged).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from .data import SRec, embed, windows
from .sim import GRID, NCFG, REF_CFG, SCENARIOS


@dataclass
class TrainCtx:
    scope: str
    X: np.ndarray
    Y: np.ndarray
    w: np.ndarray
    groups: np.ndarray
    mu: np.ndarray = None
    sd: np.ndarray = None
    streams: list = field(default_factory=list)  # real training SRecs
    all_streams: list = field(default_factory=list)  # real + synthetic
    models: dict = field(default_factory=dict)


def build_ctx(train_real, train_synth, scope: str) -> TrainCtx:
    X, Y, w, g = [], [], [], []
    allr = list(train_real) + list(train_synth)
    for gi, r in enumerate(allr):
        for scn, costs in SCENARIOS.items():
            ws = windows(r, scope)
            for a, b, tsl in ws:
                X.append(embed(r, a, b, costs))
                Y.append(r.J[scn][tsl].mean(0))
                w.append(1.0 / (len(ws) * 2))
                g.append(gi)
    X, Y = np.array(X), np.array(Y)
    c = TrainCtx(scope, X, Y, np.array(w), np.array(g))
    c.mu, c.sd = X.mean(0), X.std(0) + 1e-6
    c.streams, c.all_streams = list(train_real), allr
    return c


def zs(ctx, x):
    return (x - ctx.mu) / ctx.sd


def chosen_J(Y, pred, w=None):
    idx = pred.argmin(1)
    return float(np.average(Y[np.arange(len(Y)), idx], weights=w))


# ----------------------------------------------------------------------------- baselines
def curve(r: SRec, scn: str, scope: str):
    sl = slice(0, r.n_early) if scope == "early" else slice(0, r.K)
    return r.J[scn][sl].mean(0)


def global_fixed(ctx, scn):
    c = np.mean([curve(r, scn, ctx.scope) for r in ctx.streams], 0)
    return int(c.argmin())


def nearest_family(ctx, scn, x):
    fams = {}
    for r in ctx.streams:
        fams.setdefault(r.family, []).append(r)
    best, bd = None, 1e18
    for rs in fams.values():
        cen = np.mean([zs(ctx, embed(r, 0, r.n_early, SCENARIOS[scn])) for r in rs], 0)
        d = np.linalg.norm(cen - zs(ctx, x))
        if d < bd:
            bd, best = d, int(np.mean([curve(r, scn, ctx.scope) for r in rs], 0).argmin())
    return best


def per_stream_tuning(r: SRec, scn):
    return int(r.J[scn][: r.n_early].mean(0).argmin())


def ess_heuristic(ctx, scn, x):
    rho = float(np.clip(x[4], -0.5, 0.95))
    lam_t = 1.0 - 1.0 / (20.0 * (1 + rho) / (1 - rho))
    lv = np.array(sorted(set(GRID[:, 0])))
    lam = lv[np.abs(lv - lam_t).argmin()]
    g = global_fixed(ctx, scn)
    return int(np.where((GRID == (lam, GRID[g, 1], GRID[g, 2])).all(1))[0][0])


def hedge_expected_J(r: SRec, scn):
    """Expected eval-window J of Hedge over the grid; full-information feedback on past episodes."""
    J = r.J[scn]
    eta = np.sqrt(8 * np.log(NCFG) / r.K)
    cum = np.zeros(NCFG)
    out = []
    for e in range(r.K):
        wts = np.exp(-eta * (cum - cum.min()))
        wts /= wts.sum()
        if e >= r.n_early:
            out.append(float(wts @ J[e]))
        scale = max(J[e, REF_CFG], 50.0)
        cum += np.clip((J[e] - J[e, REF_CFG]) / scale, -1, 1)
    return float(np.mean(out))


def hier_pool(ctx, r: SRec, scn):
    sm = np.array([(t.J[scn] - t.J[scn][:, [REF_CFG]]).mean(0) for t in ctx.streams])
    mu, tau2 = sm.mean(0), np.maximum(sm.var(0), 1e-3)
    d = (r.J[scn] - r.J[scn][:, [REF_CFG]])[: r.n_early]
    y = d.mean(0)
    s2 = np.maximum(d.var(0, ddof=1) / r.n_early, 1e-3)
    return int(((y / s2 + mu / tau2) / (1 / s2 + 1 / tau2)).argmin())


def knn_meta(ctx, scn, x, k=3):
    zt = np.array([zs(ctx, embed(t, 0, t.n_early, SCENARIOS[scn])) for t in ctx.streams])
    nb = np.argsort(np.linalg.norm(zt - zs(ctx, x), axis=1))[:k]
    return int(np.mean([curve(ctx.streams[i], scn, ctx.scope) for i in nb], 0).argmin())


# ----------------------------------------------------------------------------- recommenders
def _cfeat():
    return np.column_stack([GRID[:, 0], GRID[:, 1], GRID[:, 2] / 1000.0])


def fit_ridge(ctx, alphas=(0.1, 1, 10, 100, 1000, 10000)):
    Z = zs(ctx, ctx.X)
    Yc = ctx.Y - ctx.Y.mean(1, keepdims=True)
    perm = np.random.default_rng(0).permutation(np.unique(ctx.groups))
    folds = np.array_split(perm, 5)
    best, ba = 1e18, alphas[0]
    for a in alphas:
        tot = wsum = 0.0
        for f in folds:
            te = np.isin(ctx.groups, f)
            if te.sum() == 0 or (~te).sum() == 0:
                continue
            m = Ridge(alpha=a).fit(Z[~te], Yc[~te], sample_weight=ctx.w[~te])
            tot += chosen_J(ctx.Y[te], m.predict(Z[te]), ctx.w[te]) * ctx.w[te].sum()
            wsum += ctx.w[te].sum()
        if tot / wsum < best:
            best, ba = tot / wsum, a
    ctx.models["ridge"] = Ridge(alpha=ba).fit(Z, Yc, sample_weight=ctx.w)
    ctx.models["ridge_alpha"] = ba


def fit_gbdt(ctx):
    Z = zs(ctx, ctx.X)
    Yc = ctx.Y - ctx.Y.mean(1, keepdims=True)
    rows = np.hstack([np.repeat(Z, NCFG, 0), np.tile(_cfeat(), (len(Z), 1))])
    m = HistGradientBoostingRegressor(
        max_iter=150, max_depth=4, learning_rate=0.08, min_samples_leaf=40, random_state=0
    )
    m.fit(rows, Yc.reshape(-1), sample_weight=np.repeat(ctx.w, NCFG))
    ctx.models["gbdt"] = m


def fit_mlp(ctx, n_ens=5, epochs=400, hidden=64, seed=0):
    Z = torch.tensor(zs(ctx, ctx.X), dtype=torch.float32)
    Y = torch.tensor(ctx.Y - ctx.Y.mean(1, keepdims=True), dtype=torch.float32)
    w = torch.tensor(ctx.w / ctx.w.sum(), dtype=torch.float32)
    nets = []
    for e in range(n_ens):
        torch.manual_seed(seed + e)
        net = torch.nn.Sequential(
            torch.nn.Linear(Z.shape[1], hidden),
            torch.nn.Tanh(),
            torch.nn.Dropout(0.1),
            torch.nn.Linear(hidden, hidden),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden, NCFG),
        )
        opt = torch.optim.Adam(net.parameters(), lr=3e-3, weight_decay=1e-3)
        for _ in range(epochs):
            net.train()
            loss = (w * (torch.softmax(net(Z), 1) * Y).sum(1)).sum()  # expected economic cost
            opt.zero_grad()
            loss.backward()
            opt.step()
        net.eval()
        nets.append(net)
    ctx.models["mlp"] = nets


def predict(ctx, name, x):
    z = zs(ctx, x)[None]
    if name == "ridge":
        return ctx.models["ridge"].predict(z)[0]
    if name == "gbdt":
        return ctx.models["gbdt"].predict(np.hstack([np.repeat(z, NCFG, 0), _cfeat()]))
    if name == "mlp":
        with torch.no_grad():
            t = torch.tensor(z, dtype=torch.float32)
            lg = torch.stack([torch.log_softmax(n(t), 1)[0] for n in ctx.models["mlp"]]).mean(0)
        return -lg.numpy()
    raise KeyError(name)


# ----------------------------------------------------------------------------- OOD (D4)
def _maha(rest, z):
    P = np.linalg.inv(np.cov(rest.T) + 0.5 * np.eye(rest.shape[1]))
    v = z - rest.mean(0)
    return float(np.sqrt(v @ P @ v))


class OOD:
    """Fallback trigger: Mahalanobis distance of the embedding exceeds the 95th percentile of
    leave-one-stream-out distances of the training streams."""

    def __init__(self, ctx, q=0.95):
        Z = np.array(
            [zs(ctx, embed(r, 0, r.n_early, SCENARIOS["primary"])) for r in ctx.all_streams]
        )
        self.Z, self.ctx = Z, ctx
        self.thr = float(np.quantile([_maha(np.delete(Z, i, 0), Z[i]) for i in range(len(Z))], q))

    def is_ood(self, x):
        d = _maha(self.Z, zs(self.ctx, x))
        return d > self.thr, d
