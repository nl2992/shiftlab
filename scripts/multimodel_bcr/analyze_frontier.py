"""Frontier analysis for the BCR follow-up (label price x budget grid).

Per (cq, B) cell: in-sample best config per family (development selection, same grid for every
family), its net cost, labels, switches and recovery regret (E2/E3/E4 environments); paired 95%
CIs over seeds (family-mean over environments) of best `emp` and best `bcr` vs the principal
comparator = the better of best kw_anydis and best kw_mp in that cell.
usage: analyze_frontier.py OUTPUT_ROOT
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

FAMS = ("kw_anydis", "kw_mp", "bcr", "emp", "model_picker", "never")
RECOV = ("E2_late", "E3_reversal", "E4_specialist", "E2_late_K5")


def ci(x):
    x = np.asarray(x, float)
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), x.mean() - h, x.mean() + h


def main(root):
    out = []
    for f in sorted(Path(root).glob("cq*_B*/records.jsonl")):
        d = pd.read_json(f, lines=True)
        cq, B = d.cq.iloc[0], d.B.iloc[0]
        fam = d.pivot_table(index="seed", columns="policy", values="net", aggfunc="mean")
        m = fam.mean()
        best = {k: m[[c for c in m.index if c.startswith(k)]].idxmin() for k in FAMS}
        comp = min((best["kw_anydis"], best["kw_mp"]), key=lambda c: m[c])
        rec = d[d.env.isin(RECOV)].groupby("policy").regret.mean()
        for k in FAMS:
            b = best[k]
            sub = d[d.policy == b]
            row = {
                "cq": cq,
                "B": B,
                "family": k,
                "config": b,
                "net": m[b],
                "labels": sub.labels.mean(),
                "switches": sub.switches.mean(),
                "recovery_regret": rec[b],
            }
            if k in ("bcr", "emp", "kw_anydis", "kw_mp") and b != comp:
                row["d_vs_comp"], row["lo"], row["hi"] = ci(fam[b] - fam[comp])
            out.append(row)
    r = pd.DataFrame(out)
    pd.set_option("display.width", 200)
    print(r.round(2).to_string(index=False))
    w = r.pivot_table(index=["cq", "B"], columns="family", values="net")
    print("\nnet by cell:\n", w.round(1).to_string())
    print("\nemp/bcr vs principal comparator (d, lo, hi):")
    print(
        r[r.family.isin(["emp", "bcr"])][["cq", "B", "family", "d_vs_comp", "lo", "hi", "labels"]]
        .round(2)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main(sys.argv[1])
