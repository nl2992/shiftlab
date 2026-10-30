"""Gate A (null-class audit) and Gate B (exact power ceiling under persistence). Synthetic only."""

import json
from pathlib import Path

import numpy as np

from shiftlab.gap import engine as E

OUT = Path("outputs/dep_sprint")
T, R0 = 2000, 0.3


def cp_upper(k, n, a=0.05):
    from scipy.stats import beta

    return float(beta.ppf(1 - a, k + 1, n - k)) if k < n else 1.0


def stream(L, r0=R0):
    S, Tn = L.shape
    z = np.full((S, Tn), r0)
    return {
        "x": L[..., None].astype(np.float32),
        "y": L.astype(np.int8),
        "p": z,
        "score": z,
        "loss": L,
        "brier": L,
        "proxy_cost": z,
        "proxy_brier": z,
        "r0": {"cost": r0, "brier": r0},
        "pmax": {"cost": 1.0, "brier": 1.0},
        "truth": {"harm": np.zeros(Tn), "thr": 0.1},
    }


def fa(L, cfg):
    r = E.run(stream(L), cfg, delay=0, qseed=1)
    k = int((r["alarm"] < L.shape[1]).sum())
    return k / L.shape[0], cp_upper(k, L.shape[0])


def lazy_chain(S, delta, pi, rng, T=T):
    """x_{t+1} = x_t w.p. 1-delta else fresh Bernoulli(pi): stationary Bernoulli(pi), hidden-regime-like persistence."""
    x = np.zeros((S, T))
    cur = (rng.random(S) < pi).astype(float)
    for t in range(T):
        sw = rng.random(S) < delta
        cur = np.where(sw, (rng.random(S) < pi).astype(float), cur)
        x[:, t] = cur
    return x


def cond_null_mds(S, rng, T=T):
    """Dependent but conditional mean EXACTLY r0: L = r0 + s_t xi_t, xi_t=+-1, s_t = min(r0, 1-r0) * (0.2 + 0.8 * |previous deviation| / s_max) (ARCH-like)."""
    smax = min(R0, 1 - R0)
    L = np.zeros((S, T))
    prev = np.zeros(S)
    for t in range(T):
        s = smax * (0.2 + 0.8 * prev)
        xi = np.where(rng.random(S) < 0.5, 1.0, -1.0)
        L[:, t] = R0 + s * xi
        prev = np.abs(xi) * s / smax
    return L


rng = np.random.default_rng(77)
S = 1000
cfgs = {
    "HG_f0.2": E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100),
    "HG+LRV100": E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100, lrv=True, lrv_lags=100),
    "HG+LRV300": E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100, lrv=True, lrv_lags=300),
}
res = {}
for delta in (0.5, 0.05, 0.01, 0.003):
    L = lazy_chain(S, delta, R0, rng)
    res[f"delta={delta}"] = {c: fa(L, cf) for c, cf in cfgs.items()}
    print(delta, res[f"delta={delta}"], flush=True)
(OUT / "lrv_transfer.json").write_text(json.dumps(res, indent=1, default=float))
