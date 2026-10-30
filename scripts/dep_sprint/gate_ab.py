"""Gate A (null-class audit) and Gate B (exact power ceiling under persistence). Synthetic only."""

import itertools
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


rng = np.random.default_rng(2026)
S = 2000
cfgs = {
    "pprm": E.Cfg(risk="brier", frac=1.0),
    "pprm_f0.2": E.Cfg(risk="brier", frac=0.2),
    "HG_f0.2": E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100),
}
res = {"gateA": {}, "gateB": {}}
# A1: iid (all theorem assumptions)
A = {
    "iid_bernoulli": (rng.random((S, T)) < R0).astype(float),
    "cond_null_dependent_ARCH": cond_null_mds(S, rng),
}
for nm, L in A.items():
    res["gateA"][nm] = {c: fa(L, cf) for c, cf in cfgs.items()}
    print("A", nm, res["gateA"][nm], flush=True)
# A2: marginal null true, conditional null false (persistent hidden regime); sweep persistence
for delta in (0.5, 0.05, 0.01, 0.003, 0.001):
    L = lazy_chain(S, delta, R0, rng)
    res["gateA"][f"marginal_null_persistent_delta={delta}"] = {
        c: fa(L, cf) for c, cf in cfgs.items()
    }
    # quantify conditional excess: E[L_t - r0 | past 50-mean] regression slope
    past = np.stack([L[:, t - 50 : t].mean(1) for t in range(50, T, 10)], 1)
    cur = L[:, 50:T:10]
    slope = np.cov((past - past.mean()).ravel(), (cur - cur.mean()).ravel())[0, 1] / past.var()
    res["gateA"][f"marginal_null_persistent_delta={delta}"]["cond_excess_slope"] = float(slope)
    print(
        "A persistent", delta, res["gateA"][f"marginal_null_persistent_delta={delta}"], flush=True
    )


# B: exact Neyman-Pearson power ceiling for null pi=r0 vs alt pi=r0+eps on the lazy chain, horizon n (full enumeration)
def path_probs(n, delta, pi):
    paths = np.array(list(itertools.product((0, 1), repeat=n)), dtype=np.int8)
    p = np.where(paths[:, 0] == 1, pi, 1 - pi).astype(float)
    for t in range(1, n):
        same = paths[:, t] == paths[:, t - 1]
        fresh = np.where(paths[:, t] == 1, pi, 1 - pi)
        p = p * ((1 - delta) * same + delta * fresh)
    return p


def np_power(p0, p1, alpha):
    order = np.argsort(-(p1 / np.maximum(p0, 1e-300)))
    c0, c1 = np.cumsum(p0[order]), np.cumsum(p1[order])
    k = np.searchsorted(c0, alpha, side="right")
    tail = alpha - (c0[k - 1] if k > 0 else 0.0)
    return float(
        (c1[k - 1] if k > 0 else 0.0) + tail * (p1[order][k] / p0[order][k] if k < len(p0) else 0.0)
    )


n, eps, alpha = 16, 0.1, 0.05
for delta in (0.0005, 0.01, 0.03, 0.1, 0.3, 1.0):
    p0, p1 = path_probs(n, delta, R0), path_probs(n, delta, R0 + eps)
    tv = 0.5 * np.abs(p0 - p1).sum()
    res["gateB"][f"delta={delta}"] = {
        "NP_power_at_alpha": np_power(p0, p1, alpha),
        "TV": float(tv),
        "bound_alpha_plus_eps_(1+n*delta)": alpha + eps * (1 + n * delta),
        "coupling_TV_bound_eps_(1+n*delta)": eps * (1 + n * delta),
    }
    print("B", delta, res["gateB"][f"delta={delta}"], flush=True)
(OUT / "gate_ab.json").write_text(json.dumps(res, indent=1, default=float))
