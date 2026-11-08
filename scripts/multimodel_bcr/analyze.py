"""BCR pilot analysis. usage: analyze.py records.jsonl [env1,env2,...]

Family-mean net cost (equal env weights) per policy; in-sample best config per family
(kw_uniform, kw_anydis, kw_mp, bcr, model_picker, never); paired t CIs over seeds for the best
BCR vs each family's best; per-env table of the family winners with labels and switches.
"""

import sys

import numpy as np
import pandas as pd
from scipy import stats

FAMS = ("kw_uniform", "kw_anydis", "kw_mp", "bcr", "model_picker", "never")


def ci(x):
    x = np.asarray(x, float)
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(0.975, len(x) - 1) * se
    return m, m - h, m + h, stats.ttest_1samp(x, 0).pvalue


def main(path, envs=None):
    d = pd.read_json(path, lines=True)
    if envs:
        d = d[d.env.isin(envs)]
    fam = d.pivot_table(index="seed", columns="policy", values="net", aggfunc="mean")
    m = fam.mean()
    best = {f: m[[c for c in m.index if c.startswith(f)]].idxmin() for f in FAMS}
    print(f"envs={sorted(d.env.unique())} seeds={fam.shape[0]}")
    for f, b in best.items():
        sub = d[d.policy == b]
        print(
            f"{f:13s} {b:34s} net={m[b]:.2f} labels={sub.labels.mean():.0f} "
            f"switches={sub.switches.mean():.2f} regret={sub.regret.mean():.2f}"
        )
    b = best["bcr"]
    print("\nbest BCR vs each family best (paired over seeds):")
    for f in FAMS:
        if f != "bcr":
            mm, lo, hi, p = ci(fam[b] - fam[best[f]])
            print(f"  vs {f:13s} {mm:+.2f} [{lo:+.2f},{hi:+.2f}] p={p:.2g}")
    pe = d[d.policy.isin(best.values())].pivot_table(index="env", columns="policy", values="net")
    print("\nper-env net (family winners):")
    print(pe[list(dict.fromkeys(best.values()))].round(1).to_string())
    for col in ("labels", "switches", "frac_best"):
        pv = d[d.policy.isin(best.values())].pivot_table(index="env", columns="policy", values=col)
        print(f"\nper-env {col}:")
        print(pv[list(dict.fromkeys(best.values()))].round(2).to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2].split(",") if len(sys.argv) > 2 else None)
