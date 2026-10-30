"""C1 mechanism test: does Brier-guided bet selection (H2c) beat plain predictable betting?

Status of results: DEVELOPMENT_ONLY (stylised, designed by the auditor to probe the mechanism; not a frozen
confirmation).  Increments are two bounded statistics from the same labelled event:
  cost loss  Lc = 5*Bernoulli(pc)           (null mean r0c = 5*pc0), increment Xc = Lc - r0c
  Brier loss Lb = Bernoulli(pb)             (null mean r0b = pb0),   increment Xb = Lb - r0b
with a controllable positive dependence (Gaussian-copula-free: shared uniform with prob rho).
Bets are the repository's own formulas (detectors.pp_cost_guided 'guided_disc' and pp_fix gamma<1), applied to
fully observed increments (q=1) so the experiment isolates the *bet-selection* mechanism from label sampling.
"""
import json, sys
import numpy as np
sys.path.insert(0, "src")
from shiftlab.sota_search.detectors import _ewm_cumsum, shift_time, first_cross

T, T0, DELAY, GAMMA, CAP, ALPHA = 1500, 500, 5, 0.995, 0.5, 0.05
THR = np.log(1 / ALPHA)
PC0, PB0 = 0.10, 0.20
R0C, R0B = 5 * PC0, PB0
Q = 1.0  # label rate; set by CLI (1.0 = fully observed)


def make(S, pc1, pb1, rho, seed):
    rng = np.random.default_rng(seed)
    u = rng.random((S, T)); v = rng.random((S, T))
    shared = rng.random((S, T)) < rho
    u2 = np.where(shared, u, v)  # corr(u,u2)=rho on uniforms
    post = (np.arange(T) >= T0)[None, :]
    pc = np.where(post, pc1, PC0); pb = np.where(post, pb1, PB0)
    Lc = 5.0 * (u < pc); Lb = 1.0 * (u2 < pb)
    mask = (rng.random((S, T)) < Q).astype(float)
    # prediction-powered/IPW increment with the null mean as (uninformative) proxy: x = (Q/q)(L - r0)
    xc = mask / Q * (Lc - R0C)
    xb = mask / Q * (Lb - R0B)
    return xc, xb


def caps():
    # repository uniform support caps: tight = proxy_ub*(1/q-1)+r0
    return (5/6*(1/Q-1)+R0C, 0.25*(1/Q-1)+R0B)


def logw_disc(x, lo_neg):
    """Cost-only (or any single-statistic) discounted Kelly: lam=min(max(m1,0)/m2, CAP/lo_neg)."""
    ones = np.ones_like(x)
    n = shift_time(_ewm_cumsum(ones, GAMMA), DELAY + 1)
    m1 = shift_time(_ewm_cumsum(x, GAMMA), DELAY + 1) / (n + 1)
    m2 = shift_time(_ewm_cumsum(x**2, GAMMA), DELAY + 1) / (n + 1)
    hi = CAP / lo_neg
    lam = np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hi)
    return np.cumsum(shift_time(np.log1p(lam * x), DELAY), 1), lam


def logw_h2c(xc, xb):
    """Repository 'guided_disc': relative position of the Brier Kelly bet in its interval, mapped to the cost interval."""
    ones = np.ones_like(xb)
    n = shift_time(_ewm_cumsum(ones, GAMMA), DELAY + 1)
    m1 = shift_time(_ewm_cumsum(xb, GAMMA), DELAY + 1) / (n + 1)
    m2 = shift_time(_ewm_cumsum(xb**2, GAMMA), DELAY + 1) / (n + 1)
    tc, tb = caps(); hib, hic = CAP / tb, CAP / tc
    rel = np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hib) / hib
    lam = rel * hic
    return np.cumsum(shift_time(np.log1p(lam * xc), DELAY), 1), lam


def stats(lw):
    al = first_cross(lw, THR)
    det = (al >= T0) & (al < T)
    false = al < T0
    return det.mean(), false.mean()


def run(name, pc1, pb1, rho, S=1000, seed=0):
    xc, xb = make(S, pc1, pb1, rho, seed)
    c1, _ = logw_disc(xc, caps()[0])
    h2c, _ = logw_h2c(xc, xb)
    pc, fc = stats(c1); ph, fh = stats(h2c)
    return dict(world=name, pc1=pc1, pb1=pb1, rho=rho, S=S, cost_only_power=pc, cost_only_false=fc,
                h2c_power=ph, h2c_false=fh,
                final_logw_cost_only=float(c1[:, -1].mean()), final_logw_h2c=float(h2c[:, -1].mean()))


def identity_test():
    """Exact reduction: guiding with the cost statistic itself (hib := hic) reproduces cost-only discounted Kelly."""
    xc, _ = make(200, 0.13, 0.4, 0.8, 7)
    a, _ = logw_disc(xc, caps()[0])
    ones = np.ones_like(xc)
    n = shift_time(_ewm_cumsum(ones, GAMMA), DELAY + 1)
    m1 = shift_time(_ewm_cumsum(xc, GAMMA), DELAY + 1) / (n + 1)
    m2 = shift_time(_ewm_cumsum(xc**2, GAMMA), DELAY + 1) / (n + 1)
    hic = CAP / caps()[0]
    rel = np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hic) / hic
    b = np.cumsum(shift_time(np.log1p(rel * hic * xc), DELAY), 1)
    return float(np.abs(a - b).max())


if __name__ == "__main__":
    Q = float(sys.argv[1]); TAG = sys.argv[2]
    out = {"identity_max_abs_diff": identity_test(), "worlds": [], "sweep": []}
    named = [
        ("aligned (cost up, Brier up, rho .8)", 0.13, 0.30, 0.8),
        ("masked (cost up, Brier flat)", 0.13, 0.20, 0.8),
        ("opposed (cost up, Brier DOWN)", 0.13, 0.12, 0.8),
        ("misleading null (cost flat, Brier up)", 0.10, 0.30, 0.8),
        ("null (nothing changes)", 0.10, 0.20, 0.8),
        ("aligned but independent (rho 0)", 0.13, 0.30, 0.0),
    ]
    for i, (n, pc1, pb1, rho) in enumerate(named):
        out["worlds"].append(run(n, pc1, pb1, rho, S=2000, seed=100 + i))
        print(out["worlds"][-1])
    for i, pc1 in enumerate([0.12, 0.14, 0.17, 0.20]):
        for j, pb1 in enumerate([0.20, 0.24, 0.28, 0.34]):
            r = run("sweep", pc1, pb1, 0.8, S=600, seed=900 + 10 * i + j)
            out["sweep"].append(r)
    json.dump(out, open("research/novelty_validation_2026-10-30/outputs/x1_guidance_mechanism_q"+TAG+".json", "w"), indent=1)
    print("identity", out["identity_max_abs_diff"])
    import pandas as pd
    d = pd.DataFrame(out["sweep"]); d["diff"] = d.h2c_power - d.cost_only_power
    print(d.pivot(index="pc1", columns="pb1", values="diff").round(3))
    print(d.pivot(index="pc1", columns="pb1", values="cost_only_power").round(3))
