# ruff: noqa
"""Task 2: headroom by dataset for EQ+pair and the strongest reference, with within-episode oracles.

    python headroom.py            (needs the abl_* runs and oracle csv)
All J in pp of T (net cost / T x 100), equal episode weights within a dataset window.
Oracles (evaluator-side, hindsight, label-free): J_fix = min(L0, L1); J_orcK = best <= K switches paying
c_s each from the initial incumbent (model 0). 'strongest reference' = per dataset the lowest all-episode
mean J over the reference set (descriptive and optimistic for the reference; the odd-episode check
of a dev-selected reference is in v2_analysis.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import s25_common as sc
import s25_refs as rf

COMP = ["late_adoption", "false_promotion", "reversal_churn", "label_spend", "residual"]


def run(pool):
    x = rf.load_refs(pool)
    tab = sc.ep_table(x)
    orc = pd.read_csv(sc.OUT / f"oracle_{pool}.csv").set_index(["stream", "ep"])
    rows = []
    for ds in sorted(tab.index.get_level_values(0).unique()):
        t = tab.loc[ds]
        cnt = t.reset_index().groupby("config_id").ep.nunique()
        full = cnt.max()
        names = [n for n in rf.REF_NAMES if n in cnt.index and cnt[n] == full]
        means = {n: t.xs(n, level="config_id").net.mean() / sc.T * 100 for n in names}
        # strongest reference = best over the reference set excluding the pair arms (v1 itself)
        pool_names = [n for n in names if n not in (sc.EQ_PAIR, sc.W_PAIR)]
        best = min(pool_names, key=means.get)
        o = orc.loc[ds]
        for arm, nm in (("EQ+pair", sc.EQ_PAIR), ("strongest_ref", best), ("EQ+cut", sc.EQ_CUT)):
            a = t.xs(nm, level="config_id").sort_index()
            Jm = a.net.mean() / sc.T * 100
            r = {
                "pool": pool,
                "stream": ds,
                "arm": arm,
                "policy": nm,
                "n_ep": len(a),
                "J": Jm,
                "labels": a.labels.mean(),
                "switches": a.switches.mean(),
            }
            for c in COMP:
                r[c] = a[c].mean() / sc.T * 100
                r[c + "_pct"] = 100 * r[c] / Jm
            oo = o.reindex(a.index)
            r["J_fix"], r["J_orc1"], r["J_orc2"], r["J_orc3"] = (
                float(oo[k].mean()) for k in ("J_fix", "J_orc1", "J_orc2", "J_orc3")
            )
            r["regret_vs_fix_pct"] = 100 * (Jm - r["J_fix"]) / Jm
            r["gap_to_orc1_pct"] = 100 * (Jm - r["J_orc1"]) / Jm
            r["gap_to_orc3_pct"] = 100 * (Jm - r["J_orc3"]) / Jm
            # same-label-spend oracle: hindsight timing but the arm's own labels are still paid
            r["gap_to_orc1_labelpaid_pct"] = 100 * (Jm - r["J_orc1"] - r["label_spend"]) / Jm
            r["timing_regret_pct"] = (
                r["late_adoption_pct"] + r["false_promotion_pct"] + r["reversal_churn_pct"]
            )
            r["orc1_minus_fix_pct_of_J"] = 100 * (r["J_orc1"] - r["J_fix"]) / Jm
            r["midep_gain_orc3_vs_fix_pct"] = 100 * (r["J_fix"] - r["J_orc3"]) / Jm
            rows.append(r)
        # reduction the strongest ref would need to beat: pair vs ref
    return pd.DataFrame(rows)


def main():
    out = pd.concat([run("nine"), run("fresh")], ignore_index=True)
    td = sc.OUT / "tables"
    td.mkdir(exist_ok=True)
    out.to_csv(td / "headroom_by_dataset.csv", index=False)
    # equal-dataset means per pool and arm
    num = out.select_dtypes("number").columns
    summ = out.groupby(["pool", "arm"])[list(num)].mean()
    summ.to_csv(td / "headroom_pool_means.csv")
    pd.set_option("display.width", 250, "display.max_columns", 40)
    cols = [
        "pool",
        "stream",
        "arm",
        "policy",
        "J",
        "J_fix",
        "J_orc1",
        "J_orc3",
        "late_adoption_pct",
        "false_promotion_pct",
        "reversal_churn_pct",
        "label_spend_pct",
        "residual_pct",
        "gap_to_orc1_pct",
        "gap_to_orc1_labelpaid_pct",
        "timing_regret_pct",
    ]
    print(out[out.arm != "EQ+cut"][cols].round(2).to_string(index=False))
    print(
        summ[
            [
                "J",
                "gap_to_orc1_pct",
                "gap_to_orc1_labelpaid_pct",
                "timing_regret_pct",
                "late_adoption_pct",
            ]
        ].round(2)
    )


if __name__ == "__main__":
    main()
