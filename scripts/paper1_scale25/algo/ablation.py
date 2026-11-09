# ruff: noqa
"""Brief section 10 ablation table. Reads the reused search60 / fresh records plus the new runs.

    python ablation.py --pool nine|fresh
J = net cost / T x 100 (pp of T); seed-averaged per (stream, episode); equal-dataset means; paired
stratified episode bootstrap (2000 resamples, rng seed 0); Delta = arm - comparator (negative better).
No tail statistics are used. Outputs CSVs in OUT/tables_<pool>/.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import s25_common as sc

ARMS_EQ = {
    "EQ+cut": sc.EQ_CUT,
    "EQ+cut+E48": "P1_E48_s0",
    "EQ+cut+F60": "P1_F60_s0",
    "EQ+cut+E48+F60": sc.EQ_PAIR,
}
ARMS_W = {
    "W+cut": sc.W_CUT,
    "W+cut+E48": "P4W__P1_E48_s0",
    "W+cut+F60": "P4W__P1_F60_s0",
    "W+cut+E48+F60": sc.W_PAIR,
}
COMP = ["late_adoption", "false_promotion", "reversal_churn", "label_spend", "residual"]


def load(pool):
    if pool == "nine":
        d = sc.load_nine_search60(
            [sc.EQ_CUT, sc.EQ_PAIR, "P1_E48_s0", "P1_F60_s0", sc.W_CUT, sc.W_PAIR]
        )
        new = sc.read_jsonl(sc.OUT / "abl_nine/records.jsonl")
        d = pd.concat([d, new[~new.config_id.isin(d.config_id.unique())]])
    else:
        fr = sc.load_fresh()
        new = sc.read_jsonl(sc.OUT / "abl_fresh/records.jsonl")
        d = pd.concat([fr, new[~new.config_id.isin(fr.config_id.unique())]])
    mt = sc.read_jsonl(sc.OUT / f"matched_{pool}/records.jsonl")
    mt["config_id"] = mt.config_id.str.replace(r"__.*$", "", regex=True)  # UNI_EQ__ds -> UNI_EQ
    d = pd.concat([d, mt]).drop_duplicates(["stream", "ep", "seed", "config_id"])
    return d


def combo(tab, coefs, col="net"):
    """Per-dataset arrays of sum_a w_a * J_a (pp of T), aligned by episode."""
    out = {}
    for ds in sorted(tab.index.get_level_values(0).unique()):
        v = 0
        for a, w in coefs.items():
            v = (
                v
                + w * tab.loc[ds].xs(a, level="config_id")[col].sort_index().to_numpy() / sc.T * 100
            )
        out[ds] = v
    return out


def stat(vs, ref_J=None, nb=2000):
    point = float(np.mean([v.mean() for v in vs.values()]))
    reps = sc.boot_eq(list(vs.values()), nb)
    lo, hi = sc.ci(reps)
    r = {"d": point, "lo": lo, "hi": hi}
    if ref_J:
        r.update(pct=100 * point / ref_J, pct_lo=100 * lo / ref_J, pct_hi=100 * hi / ref_J)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--parity", default="all", choices=["all", "even", "odd"])
    a = ap.parse_args()
    d = load(a.pool)
    if a.parity != "all":
        d = d[d.ep % 2 == (0 if a.parity == "even" else 1)]
    tag = f"{a.pool}_{a.parity}"
    od = sc.OUT / "tables"
    od.mkdir(exist_ok=True)
    tab = sc.ep_table(d)
    arms = {
        **ARMS_EQ,
        **ARMS_W,
        "UNI_EQ": "UNI_EQ",
        "UNC_EQ": "UNC_EQ",
        "UNI_W": "UNI_W",
        "UNC_W": "UNC_W",
    }
    arms = {k: v for k, v in arms.items() if v in tab.index.get_level_values("config_id")}
    tab = tab.swaplevel(0, 1).sort_index().swaplevel(0, 1) if False else tab
    t2 = tab.reset_index().set_index(["stream", "ep", "config_id"]).sort_index()
    t2 = t2.rename(index={v: k for k, v in arms.items()}, level="config_id")
    names = list(arms)
    # ---- per-arm level table (equal-dataset means) incl. decomposition
    rows = []
    for n in names:
        x = t2.xs(n, level="config_id")
        g = x.groupby("stream").mean()
        r = {
            "arm": n,
            "J": g.net.mean() / sc.T * 100,
            "L": g.loss.mean() / sc.T * 100,
            "labels": g.labels.mean(),
            "switches": g.switches.mean(),
            "n_ds": len(g),
            "n_ep": len(x),
        }
        for c in COMP:
            r[c] = g[c].mean() / sc.T * 100
        rows.append(r)
    lev = pd.DataFrame(rows)
    lev.to_csv(od / f"ablation_levels_{tag}.csv", index=False)
    # ---- paired contrasts vs parent (and vs each other)
    contr = []

    def add(label, coefs, ref):
        vs = combo(t2, coefs)
        s = stat(vs, float(lev.set_index("arm").J[ref]))
        per = {ds: float(v.mean()) for ds, v in vs.items()}
        contr.append(
            {
                "contrast": label,
                **s,
                "n_neg_ds": sum(v < 0 for v in per.values()),
                "per_dataset": json.dumps({k: round(v, 4) for k, v in per.items()}),
            }
        )

    for fam, base, arms_f in (("EQ", "EQ+cut", ARMS_EQ), ("W", "W+cut", ARMS_W)):
        if base not in names:
            continue
        e, f, p = (
            [n for n in arms_f if n != base][0],
            [n for n in arms_f if n != base][1],
            [n for n in arms_f if n != base][2],
        )
        for n in (e, f, p):
            add(f"{n} - {base}", {n: 1, base: -1}, base)
        add(
            f"INTERACTION[{fam}] = J({p}) - J({e}) - J({f}) + J({base})",
            {p: 1, e: -1, f: -1, base: 1},
            base,
        )
        add(f"{p} - {e}", {p: 1, e: -1}, base)
        add(f"{p} - {f}", {p: 1, f: -1}, base)
        for m in (f"UNI_{fam}", f"UNC_{fam}"):
            if m in names:
                add(f"{p} - {m} (label-matched)", {p: 1, m: -1}, base)
                add(f"{m} - {base}", {m: 1, base: -1}, base)
    if "W+cut+E48+F60" in names and "EQ+cut" in names:
        add("W+cut - EQ+cut", {"W+cut": 1, "EQ+cut": -1}, "EQ+cut")
        add("EQ+cut+E48+F60 - W+cut", {"EQ+cut+E48+F60": 1, "W+cut": -1}, "W+cut")
    cdf = pd.DataFrame(contr)
    cdf.to_csv(od / f"ablation_contrasts_{tag}.csv", index=False)
    # ---- component deltas vs parent (decomposition of where the change comes from)
    dec = []
    for fam, base, arms_f in (("EQ", "EQ+cut", ARMS_EQ), ("W", "W+cut", ARMS_W)):
        if base not in names:
            continue
        for n in list(arms_f) + [f"UNI_{fam}", f"UNC_{fam}"]:
            if n == base or n not in names:
                continue
            r = {"arm": n, "vs": base}
            for c in COMP + ["net", "labels", "switches"]:
                v = {}
                for ds in t2.index.get_level_values(0).unique():
                    x = t2.loc[ds]
                    v[ds] = (
                        x.xs(n, level="config_id")[c].to_numpy()
                        - x.xs(base, level="config_id")[c].to_numpy()
                    )
                sc_ = 1 if c in ("labels", "switches") else 100 / sc.T
                r[c] = float(np.mean([vv.mean() for vv in v.values()])) * sc_
            dec.append(r)
    pd.DataFrame(dec).to_csv(od / f"ablation_decomp_{tag}.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(lev.round(3).to_string(index=False))
    print(cdf.drop(columns="per_dataset").round(4).to_string(index=False))
    print(pd.DataFrame(dec).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
