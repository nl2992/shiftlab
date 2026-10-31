"""Reduced re-run of notebooks/tit_exps.ipynb (cell 13) without Cython/LBUP/Hybrid (no C compiler).
Usage: python gambling_cs_run.py <repo_dir> <out_json> [T] [n_seeds] [problems=3|all]   (all = notebook's six problems; T=10000, 5 seeds = notebook sizes)
Methods: CB, HR, PRECiSE_CO96/A_CO96/R70 (Beta problems), UP (Beta problems). Reports final CI width and
whether mu left [lower, upper] at any time (anytime-coverage violation)."""

import json
import os
import sys
import time

repo, out = sys.argv[1], sys.argv[2]
T = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
S = int(sys.argv[4]) if len(sys.argv) > 4 else 2
os.chdir(repo)
sys.path.insert(0, repo)
import numpy as np
from methods.kt import CoinBettingCI, HorseRaceCI
from methods.precise.a_co96 import PRECiSE_A_CO96
from methods.precise.co96 import PRECiSE_CO96
from methods.precise.r70 import PRECiSE_R70
from methods.up import StockInvestmentCI

delta = 0.05


def bern(p, s):
    np.random.seed(s)
    return (np.random.uniform(size=T) <= p).astype(int)


def beta(b, s):
    np.random.seed(s)
    return np.random.beta(*b, size=T)


problems = {
    "bern0.25": (0.25, lambda s: bern(0.25, s)),
    "beta1,3": (0.25, lambda s: beta([1, 3], s)),
    "beta10,10": (0.5, lambda s: beta([10, 10], s)),
}
# NOTE: notebook lists mu=0.2 for Beta(1,3); true mean is 0.25 (notebook typo) -> 0.25 used here.
if len(sys.argv) > 5 and sys.argv[5] == "all":
    problems.update(
        {
            "beta10,30": (0.25, lambda s: beta([10, 30], s)),
            "bern0.5": (0.5, lambda s: bern(0.5, s)),
            "beta1,1": (0.5, lambda s: beta([1, 1], s)),
        }
    )
res = {"T": T, "seeds": S, "delta": delta, "problems": {}}
for k, (mu, samp) in problems.items():
    r = {}
    for s in range(S):
        xs = samp(s)
        runs = {
            "CB": lambda xs=xs: CoinBettingCI().construct(delta, xs, wor=False),
            "HR": lambda xs=xs: HorseRaceCI().construct(delta, xs, wor=False),
            "PRECiSE_CO96": lambda xs=xs: PRECiSE_CO96().construct(delta, xs, wor=False),
            "PRECiSE_A_CO96": lambda xs=xs: PRECiSE_A_CO96().construct(delta, xs, wor=False),
        }
        if "bern" not in k:
            runs["PRECiSE_R70"] = lambda xs=xs: PRECiSE_R70().construct(delta, xs, wor=False)
            runs["UP"] = lambda xs=xs: StockInvestmentCI().construct(delta, xs, wor=False)
        for name, f in runs.items():
            t0 = time.time()
            try:
                o = f()
                lo, up = np.asarray(o[0]), np.asarray(o[1])
                d = r.setdefault(name, {"width_T": [], "violation": [], "secs": []})
                d["width_T"].append(float(up[-1] - lo[-1]))
                d["violation"].append(bool(((mu < lo - 1e-9) | (mu > up + 1e-9)).any()))
                d["secs"].append(time.time() - t0)
            except Exception as e:  # noqa: BLE001 - third-party CI constructors may raise anything; record and continue
                r.setdefault(name, {})["error"] = repr(e)[:200]
            print(k, s, name, r[name], flush=True)
    res["problems"][k] = r
with open(out, "w") as fh:
    json.dump(res, fh, indent=1)
print("DONE")
