"""Analyze a D1-style run: family-mean net cost per policy, paired CIs vs a comparator."""

import sys

import numpy as np
import pandas as pd
from scipy import stats

FAM = [
    "F0_better",
    "V_better_a",
    "V_better_b",
    "V_better_c",
    "V_bursty",
    "V_dep_better_r5",
    "F7_near_better",
    "F0_null",
    "V_null",
    "V_worse",
    "V_null_dep_r8",
]
GUARD = ["F1_late_800", "F3_reversal_800"]


def load(path):
    d = pd.read_json(path, lines=True)
    return d


def fam_by_seed(d):
    f = d[d.regime.isin(FAM)]
    return f.pivot_table(index="seed", columns="policy", values="net", aggfunc="mean")


def paired(fs, a, b):
    x = fs[a] - fs[b]
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(0.975, len(x) - 1) * se
    return m, m - h, m + h


if __name__ == "__main__":
    d = load(sys.argv[1])
    oracle = (d.net - d.regret_hindsight).groupby(d.regime).mean()
    fs = fam_by_seed(d)
    pv = d.pivot_table(index="policy", columns="regime", values="net", aggfunc="mean")
    reg = pv[FAM].sub(oracle[FAM], axis=1)
    out = pd.DataFrame(
        {"fam_net": fs.mean(), "fam_regret": reg.mean(1), "worst_regret": reg.max(1)}
    )
    for g in GUARD:
        if g in pv:
            out[g] = pv[g]
    pr = (
        d[d.regime.isin(["F0_null", "V_null", "V_worse", "V_null_dep_r8"])]
        .groupby("policy")
        .ever_promote.mean()
    )
    out["null_promote"] = pr
    out["labels_null"] = d[d.regime.isin(["F0_null", "V_null"])].groupby("policy").labels.mean()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 300)
    print(
        out.sort_values("fam_net")
        .round(2)
        .head(int(sys.argv[2]) if len(sys.argv) > 2 else 40)
        .to_string()
    )
