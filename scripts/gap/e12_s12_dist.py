"""S12: calibration, power (benign vs harmful shifts), runtime, memory and approximation error of drift tests."""

import itertools
import time
from multiprocessing import get_context

import numpy as np
import pandas as pd

from shiftlab.gap import dist_tests as DT

N_REF, R_CAL, R_EVAL, ALPHA = 512, 150, 100, 0.05
SHIFT = 0.25  # v2: moderate shifts (v1 used 1.2 sigma: every test saturated at power 1 and the 'harmful' direction had NEGATIVE decision harm)


def world_y_harm(d, shift_dir, delta, rng, n=40000):
    """Evaluator-side: decision-cost increase of a fixed linear model when the covariates shift (nonlinear truth)."""
    w = np.zeros(d)
    w[0], w[1] = 1.5, 1.0

    def cost(mu):
        x = rng.standard_normal((n, d)) + mu
        p_true = 1 / (1 + np.exp(-(x @ w + 1.5 * (x[:, 1] ** 2 - 1))))
        y = rng.random(n) < p_true
        act = (1 / (1 + np.exp(-(x @ w)))) >= 1 / 6
        return np.mean(act * (1 - y) * 1.0 + (1 - act) * y * 5.0)

    mu = np.zeros(d)
    mu[shift_dir] = delta
    return cost(mu) - cost(np.zeros(d))


def one_setting(args):
    d, wlen = args
    rng = np.random.default_rng(1000 * d + wlen)
    score_w = np.zeros(d)
    score_w[0], score_w[1] = 1.5, 1.0
    mu_b, mu_h = np.zeros(d), np.zeros(d)
    mu_b[d - 1] = 0.3  # nuisance coordinate (no effect on the label law)
    mu_h[1] = -0.3  # informative coordinate where the linear model is misspecified
    harm_b = world_y_harm(d, d - 1, 0.3, rng)
    harm_h = world_y_harm(d, 1, -0.3, rng)
    rows = []
    ref0 = rng.standard_normal((N_REF, d))
    for name in DT.METHODS:
        cal = []
        for _ in range(R_CAL):
            ref = rng.standard_normal((N_REF, d))
            win = rng.standard_normal((wlen, d))
            v, _, _ = DT.time_method(name, ref, win, rng, score_w)
            cal.append(v)
        cal = np.array(cal)  # (R, nbw)
        sd = cal.std(0) + 1e-12
        thr = np.quantile((cal / sd).max(1), 1 - ALPHA)
        for scen, mu in (("null", np.zeros(d)), ("benign", mu_b), ("harmful", mu_h)):
            rej, ts, ms = [], [], []
            for _ in range(R_EVAL):
                ref = rng.standard_normal((N_REF, d))
                win = rng.standard_normal((wlen, d)) + mu
                v, wall, peak = DT.time_method(name, ref, win, rng, score_w)
                rej.append((v / sd).max() >= thr)
                ts.append(wall)
                ms.append(peak)
            rows.append(
                {
                    "d": d,
                    "window": wlen,
                    "method": name,
                    "scenario": scen,
                    "reject": float(np.mean(rej)),
                    "ms_per_test": 1e3 * float(np.mean(ts)),
                    "peak_kb": float(np.max(ms)) / 1e3,
                    "decision_harm_scenario": {"null": 0.0, "benign": harm_b, "harmful": harm_h}[
                        scen
                    ],
                }
            )
    # approximation error of RFF vs exact MMD (harmful shift) and incremental-vs-batch agreement
    errs = []
    for _ in range(30):
        ref = rng.standard_normal((N_REF, d))
        win = rng.standard_normal((wlen, d)) + mu_h
        ex = DT.mmd_exact(ref, win, np.random.default_rng(1))[0]
        ap = DT.mmd_rff(ref, win, np.random.default_rng(1))[0]
        errs.append(abs(ap - ex) / (abs(ex) + 1e-12))
    # streaming cost: exact windowed recompute vs incremental RFF over 600 observations
    stream = rng.standard_normal((600, d))
    t0 = time.perf_counter()
    inc = DT.IncrementalRFF(ref0, wlen, np.random.default_rng(2))
    for x in stream:
        inc.update(x)
    t_inc = time.perf_counter() - t0
    t0 = time.perf_counter()
    for i in range(wlen, 600, 20):  # recompute every 20 steps only (generous to the exact method)
        DT.mmd_exact(ref0, stream[i - wlen : i], np.random.default_rng(3))
    t_exact = time.perf_counter() - t0
    rows.append(
        {
            "d": d,
            "window": wlen,
            "method": "approx_error_rff_vs_exact",
            "scenario": "harmful",
            "reject": float(np.mean(errs)),
            "ms_per_test": 1e3 * t_inc / 600,
            "peak_kb": 1e3 * t_exact / ((600 - wlen) / 20),
            "decision_harm_scenario": harm_h,
        }
    )
    return rows


if __name__ == "__main__":
    t0 = time.time()
    with get_context("fork").Pool(4) as pool:
        parts = pool.map(
            one_setting, list(itertools.product((5, 20, 100), (32, 64, 128, 256))), chunksize=1
        )
    df = pd.DataFrame([r for p in parts for r in p])
    df.to_csv("outputs/gap_closure/e12_s12_dist.csv", index=False)
    print("seconds", round(time.time() - t0))
