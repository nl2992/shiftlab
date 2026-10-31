"""Re-run of the ICML-2024 (Ryu & Wornell) multivariate experiments with the repo's own classes
(MultiHorseRaceCI = KT mixture portfolio eq.8, Sanov baseline, MultiStockInvestmentCI = universal portfolio, Sec 4.1).
The repo ships no notebook for these (only tit_exps.ipynb), so the setups follow the paper's text (Fig.1/3); parameters not stated
in the text are OUR choices (mu, Dirichlet concentration, simplex grid resolution).
Usage: python gambling_cs_multivariate_run.py <repo_dir> <out_json> [reduced|full]
  reduced: K=3, 20 categorical runs (T=100), Dirichlet(8,8,8) T=40 x 3 runs.
  full   : Fig.1 sizes K in {3,4,5}, T=100, 100 runs; Fig.3 Dirichlet K in {3,4}, T=50, 20 runs (K=4 UP is O(t^3) per step).
Not covered: Fig.2 (sampling without replacement) has no driver code in the repo."""

import json
import os
import sys
import time

repo, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "reduced"
os.chdir(repo)
sys.path.insert(0, repo)
import numpy as np
from methods.kt import MultiHorseRaceCI
from methods.sanov import Sanov
from methods.up import MultiStockInvestmentCI

delta = 0.05
thr = np.log(1 / delta)


def simplex_grid(K, G):
    def rec(k, left):
        if k == 1:
            yield (left,)
            return
        for i in range(1, left - (k - 1) + 1):
            for rest in rec(k - 1, left - i):
                yield (i,) + rest

    return np.array(list(rec(K, G)), float) / G


GRID_RES = {3: 60, 4: 30, 5: 18}
cat_K, cat_R, dir_K, dir_T, dir_R = (
    ([3], 20, [3], 40, 3) if mode == "reduced" else ([3, 4, 5], 100, [3, 4], 50, 20)
)
res = {"mode": mode, "delta": delta, "categorical": {}, "dirichlet": {}}
T = 100
for K in cat_K:
    grid = simplex_grid(K, GRID_RES[K])
    mu = np.arange(K, 0, -1.0)
    mu /= mu.sum()
    kt_area, sn_area, kt_cov, sn_cov = [], [], [], []
    for r in range(cat_R):
        rng = np.random.default_rng(r)
        z = rng.choice(K, size=T, p=mu)
        ys = np.eye(K)[z].T
        kt = MultiHorseRaceCI(M=K)
        fk = [kt.f(grid, ys[:, :t], only_last=True) for t in (10, 30, 100)]
        kt_area.append([(f < thr).mean() for f in fk])
        kt_cov.append(bool((kt.f(mu[None, :], ys)[0] < thr).all()))
        fs = [Sanov.f(grid, ys[:, :t], delta, only_last=True) for t in (10, 30, 100)]
        sn_area.append([(~(f >= thr)).mean() for f in fs])
        sn_cov.append(bool((~(Sanov.f(mu[None, :], ys, delta)[0] >= thr)).all()))
    res["categorical"][f"K{K}"] = {
        "mu": mu.tolist(),
        "T": T,
        "runs": cat_R,
        "grid_points": len(grid),
        "t_checked": [10, 30, 100],
        "KT_mean_set_fraction": np.mean(kt_area, 0).tolist(),
        "Sanov_mean_set_fraction": np.mean(sn_area, 0).tolist(),
        "KT_coverage_all_t": float(np.mean(kt_cov)),
        "Sanov_coverage_all_t": float(np.mean(sn_cov)),
    }
    print(K, res["categorical"][f"K{K}"], flush=True)
for K in dir_K:
    grid = simplex_grid(K, GRID_RES[K])
    alpha = np.full(K, 8.0)
    mu2 = alpha / alpha.sum()
    up_area, kt_area, up_cov, kt_cov, secs = [], [], [], [], []
    for r in range(dir_R):
        np.random.seed(r)
        ys = np.random.dirichlet(alpha, size=dir_T).T
        t0 = time.time()
        up = MultiStockInvestmentCI(M=K)
        up.update_logsumprod_batch(ys)
        fu = up.f(grid)
        secs.append(time.time() - t0)
        up_area.append(float((fu < thr).mean()))
        up_cov.append(bool(up.f(mu2[None, :])[0] < thr))
        kt = MultiHorseRaceCI(M=K)  # KT run on the simplex-valued data used as fractional counts
        fk = kt.f(grid, ys, only_last=True)
        kt_area.append(float((fk < thr).mean()))
        kt_cov.append(bool(kt.f(mu2[None, :], ys, only_last=True)[0] < thr))
    res["dirichlet"][f"K{K}"] = {
        "alpha": alpha.tolist(),
        "T": dir_T,
        "runs": dir_R,
        "grid_points": len(grid),
        "UP_set_fraction_at_T": float(np.mean(up_area)),
        "KT_set_fraction_at_T": float(np.mean(kt_area)),
        "UP_cover_at_T": float(np.mean(up_cov)),
        "KT_cover_at_T": float(np.mean(kt_cov)),
        "UP_secs_per_run": float(np.mean(secs)),
    }
    print(K, res["dirichlet"][f"K{K}"], flush=True)
with open(out, "w") as fh:
    json.dump(res, fh, indent=1)
