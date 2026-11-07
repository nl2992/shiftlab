"""X3: margin-aligned guidance (MAG) vs H2c vs cost-only discounted Kelly, with ESTIMATED nominal risk.

Protocol: research/discovery_v2_2026-11-07/X3_MAG_REGISTRATION.md (committed before this ran). EXPLORATORY.
Increments/caps follow research/novelty_validation_2026-10-30/scripts/x1_guidance_mechanism.py; the PP proxy is the
calibration point estimate, and every statistic is centred at its own nominal bound U0 (cost: UCB; guide: point
estimate for H2c, UCB for MAG).
"""
import itertools, json, sys
import numpy as np
sys.path.insert(0, "src")
from shiftlab.sota_search.detectors import _ewm_cumsum, shift_time, first_cross

T, T0, DELAY, GAMMA, CAP = 1500, 500, 5, 0.995, 0.5
ALPHA_T, DELTA_S = 0.04, 0.01
THR = float(np.log(1 / ALPHA_T))
PC0, PB0 = 0.10, 0.20


def disc_lambda(x, hi):
    ones = np.ones_like(x)
    n = shift_time(_ewm_cumsum(ones, GAMMA), DELAY + 1)
    m1 = shift_time(_ewm_cumsum(x, GAMMA), DELAY + 1) / (n + 1)
    m2 = shift_time(_ewm_cumsum(x**2, GAMMA), DELAY + 1) / (n + 1)
    return np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hi)


def logw(lam, x):
    return np.cumsum(shift_time(np.log1p(lam * x), DELAY), 1)


def cell(q, n_cal, pc1, pb1, rho, S, seed):
    rng = np.random.default_rng(seed)
    # calibration sample (fully labelled, pre-onset law), one per path
    uc = rng.random((S, n_cal)); vc = rng.random((S, n_cal)); sh = rng.random((S, n_cal)) < rho
    cal_c = 5.0 * (uc < PC0); cal_b = 1.0 * (np.where(sh, uc, vc) < PB0)
    r0c, r0b = cal_c.mean(1, keepdims=True), cal_b.mean(1, keepdims=True)
    hw = np.sqrt(np.log(1 / DELTA_S) / (2 * n_cal))
    U0c, U0b_point, U0b_mag = r0c + 5.0 * hw, r0b, r0b + 1.0 * hw
    # monitored stream
    u = rng.random((S, T)); v = rng.random((S, T)); shared = rng.random((S, T)) < rho
    u2 = np.where(shared, u, v)
    post = (np.arange(T) >= T0)[None, :]
    Lc = 5.0 * (u < np.where(post, pc1, PC0)); Lb = 1.0 * (u2 < np.where(post, pb1, PB0))
    Q = (rng.random((S, T)) < q).astype(float)
    pc_, pb_ = np.clip(r0c, 0, 5 / 6), np.clip(r0b, 0, 0.25)            # predictable proxies within uniform bounds
    xc = pc_ + Q / q * (Lc - pc_) - U0c
    tc = 5 / 6 * (1 / q - 1) + U0c; hic = CAP / tc
    out = {}
    lam_c1 = disc_lambda(xc, hic)
    out["C1_cost_disc"] = logw(lam_c1, xc)
    for name, U0b in (("H2c", U0b_point), ("MAG", U0b_mag)):
        xb = pb_ + Q / q * (Lb - pb_) - U0b
        tb = 0.25 * (1 / q - 1) + U0b; hib = CAP / tb
        rel = disc_lambda(xb, hib) / hib
        out[name] = logw(rel * hic, xc)
    res = {}
    for k, lw in out.items():
        al = first_cross(lw, THR)
        res[k] = dict(power=float(((al >= T0) & (al < T)).mean()), pre_onset_alarm=float((al < T0).mean()),
                      al=al)
    return res


WORLDS = [("aligned_rho.8", 0.13, 0.30, 0.8), ("aligned_rho0", 0.13, 0.30, 0.0), ("masked", 0.13, 0.20, 0.8),
          ("opposed", 0.13, 0.12, 0.8), ("misleading_null", 0.10, 0.30, 0.8), ("null", 0.10, 0.20, 0.8),
          ("aligned_strong", 0.16, 0.34, 0.8)]

if __name__ == "__main__":
    rows, seed = [], 700000
    rng_boot = np.random.default_rng(1)
    for q, n_cal in itertools.product((0.1, 0.2), (500, 2000, 10000)):
        for w, pc1, pb1, rho in WORLDS:
            seed += 1
            r = cell(q, n_cal, pc1, pb1, rho, 2000, seed)
            harm = pc1 > PC0
            row = dict(q=q, n_cal=n_cal, world=w, harmful=harm, seed=seed)
            for k in ("C1_cost_disc", "H2c", "MAG"):
                row[f"{k}_power"] = r[k]["power"]; row[f"{k}_pre"] = r[k]["pre_onset_alarm"]
            for a, b in (("MAG", "H2c"), ("MAG", "C1_cost_disc")):
                det_a = ((r[a]["al"] >= T0) & (r[a]["al"] < T)).astype(float)
                det_b = ((r[b]["al"] >= T0) & (r[b]["al"] < T)).astype(float)
                d = det_a - det_b
                bs = d[rng_boot.integers(0, len(d), (2000, len(d)))].mean(1)
                row[f"{a}-{b}"] = float(d.mean()); row[f"{a}-{b}_ci"] = [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]
            rows.append(row)
            print(f"q={q} n_cal={n_cal:5d} {w:16s} C1 {row['C1_cost_disc_power']:.3f} H2c {row['H2c_power']:.3f} "
                  f"MAG {row['MAG_power']:.3f} | pre {max(row['C1_cost_disc_pre'], row['H2c_pre'], row['MAG_pre']):.3f}")
    json.dump(rows, open("research/discovery_v2_2026-11-07/outputs/x3_mag.json", "w"), indent=1)
