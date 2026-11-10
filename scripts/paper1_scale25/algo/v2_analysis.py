# ruff: noqa
"""v2 search analysis: tune on EVEN episodes (nine + fresh windows), select-check on ODD episodes.

    python v2_analysis.py tune [--k 5]     # all candidates, even episodes, seeds 0-4 -> ledger + selected.json
    python v2_analysis.py check            # selected candidates, odd episodes, seeds 0-9 vs the even-selected reference
Reference R* = lowest equal-window mean J on EVEN episodes over the reference set (25 comparators, Wald
grid + cutoff, EQ cutoff grid, EQ+cut, W+cut, EQ+pair, W+pair, arm R). Also reported: per-window best
reference chosen on even episodes (R*_w), evaluated on odd. J in pp of T; Delta = candidate - reference
(negative better); % = 100 Delta / J_ref (equal-window means); stratified episode bootstrap 2000, rng 0.
No tail criteria anywhere.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd
import s25_common as sc
import s25_refs as rf

NB = 2000
COMP = ["late_adoption", "false_promotion", "reversal_churn", "label_spend", "residual"]


def tables(parity, seeds, cand_dirs):
    """ep-level seed-averaged table over refs + candidate records; window key 'pool:stream'."""
    ts = []
    for pool in ("nine", "fresh"):
        x = rf.load_refs(pool)
        for d in cand_dirs:
            f = sc.OUT / f"{d}_{pool}" / "records.jsonl"
            if f.exists() and (f.parent / "DONE").exists():
                x = pd.concat([x, sc.read_jsonl(f)]).drop_duplicates(
                    ["stream", "ep", "seed", "config_id"]
                )
        x = x[x.seed.isin(list(seeds))]
        x = x[x.ep % 2 == (0 if parity == "even" else 1)]
        t = sc.ep_table(x).reset_index()
        t["win"] = pool + ":" + t.stream
        ts.append(t)
    return pd.concat(ts, ignore_index=True)


def wide(t, col="net"):
    """win -> DataFrame(index ep, columns config_id) of J pp."""
    out = {}
    for w, g in t.groupby("win"):
        p = g.pivot(index="ep", columns="config_id", values=col)
        out[w] = p / sc.T * 100 if col in ("net", "loss") else p
    return out


def comb(W, a, b):
    """per-window arrays of J_a - J_b on common episodes."""
    out = {}
    for w, p in W.items():
        if a in p and b in p:
            v = (p[a] - p[b]).dropna().to_numpy()
            if len(v):
                out[w] = v
    return out


def stat(vs, ref_mean):
    pt = float(np.mean([v.mean() for v in vs.values()]))
    reps = sc.boot_eq(list(vs.values()), NB)
    lo, hi = sc.ci(reps)
    return {
        "dJ": pt,
        "lo": lo,
        "hi": hi,
        "pct": 100 * pt / ref_mean,
        "pct_lo": 100 * lo / ref_mean,
        "pct_hi": 100 * hi / ref_mean,
        "win_neg": int(sum(v.mean() < 0 for v in vs.values())),
        "n_win": len(vs),
    }


def eqmean(W, name):
    return float(np.mean([p[name].mean() for p in W.values() if name in p]))


def ref_names(W):
    return [n for n in rf.REF_NAMES if all(n in p for p in W.values())]


def tune(k):
    cand = [s["name"] for s in json.load(open(sc.OUT / "specs_v2.json"))]
    t = tables("even", range(5), ["v2_even"])
    W = wide(t)
    refs = ref_names(W)
    m = {n: eqmean(W, n) for n in refs}
    rstar = min(m, key=m.get)
    # per-window best reference (selected on even)
    rw = {w: min(refs, key=lambda n: p[n].mean()) for w, p in W.items()}
    rows = []
    allnames = [n for n in cand if all(n in p for p in W.values())]
    for n in ["v1:" + sc.EQ_PAIR] + allnames:
        nm = sc.EQ_PAIR if n.startswith("v1:") else n
        s = stat(comb(W, nm, rstar), m[rstar])
        sp = stat(comb(W, nm, sc.EQ_PAIR), eqmean(W, sc.EQ_PAIR)) if nm != sc.EQ_PAIR else {}
        sc_ = stat(comb(W, nm, sc.EQ_CUT), eqmean(W, sc.EQ_CUT))
        lab = float(np.mean([t[(t.config_id == nm) & (t.win == w)].labels.mean() for w in W]))
        swn = float(np.mean([t[(t.config_id == nm) & (t.win == w)].switches.mean() for w in W]))
        r = {
            "candidate": n,
            "J": eqmean(W, nm),
            "labels": lab,
            "switches": swn,
            **{f"vsRstar_{k_}": v for k_, v in s.items()},
            **{f"vsPair_{k_}": v for k_, v in sp.items()},
            **{f"vsEQcut_{k_}": v for k_, v in sc_.items()},
        }
        # per-window dJ vs the per-window best reference
        pw = [float((W[w][nm] - W[w][rw[w]]).mean()) for w in W]
        r["vsRw_dJ_mean"], r["vsRw_win_neg"] = float(np.mean(pw)), int(sum(x < 0 for x in pw))
        rows.append(r)
    L = pd.DataFrame(rows)
    fam = {s["name"]: n for s, n in []}
    ledger = pd.read_csv(sc.DOCS / "algo" / "V2_CANDIDATES.csv").set_index("name")
    L["family"] = [ledger.family.get(c, "v1") for c in L.candidate]
    L = L.sort_values("vsRstar_dJ")
    (sc.OUT / "tables").mkdir(exist_ok=True)
    L.to_csv(sc.OUT / "tables" / "v2_tune_even.csv", index=False)
    top = [c for c in L.candidate if not c.startswith("v1:")][:k]
    bestfam = L[~L.candidate.str.startswith("v1:")].groupby("family").candidate.first().tolist()
    sel = list(dict.fromkeys(top + bestfam))
    json.dump(
        {
            "rstar": rstar,
            "rstar_J": m[rstar],
            "per_window_ref": rw,
            "selected": sel,
            "ref_means_even": dict(sorted(m.items(), key=lambda kv: kv[1])[:10]),
        },
        open(sc.OUT / "tables" / "v2_selected.json", "w"),
        indent=1,
    )
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 100)
    print(
        "R* (even, pooled):",
        rstar,
        round(m[rstar], 4),
        " EQ+pair:",
        round(eqmean(W, sc.EQ_PAIR), 4),
    )
    print(
        L[
            [
                "candidate",
                "family",
                "J",
                "labels",
                "switches",
                "vsRstar_dJ",
                "vsRstar_pct",
                "vsRstar_lo",
                "vsRstar_hi",
                "vsRstar_win_neg",
                "vsPair_dJ",
                "vsRw_dJ_mean",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    print("selected:", sel)


def check():
    sel = json.load(open(sc.OUT / "tables" / "v2_selected.json"))
    rstar, rw = sel["rstar"], sel["per_window_ref"]
    t = tables("odd", range(10), ["v2_odd"])
    W = wide(t)
    m = eqmean(W, rstar)
    rows = []
    for n in [sc.EQ_PAIR, sc.EQ_CUT] + sel["selected"]:
        if not all(n in p for p in W.values()):
            print("missing", n)
            continue
        s = stat(comb(W, n, rstar), m)
        sp = stat(comb(W, n, sc.EQ_PAIR), eqmean(W, sc.EQ_PAIR)) if n != sc.EQ_PAIR else {}
        pw = [float((W[w][n] - W[w][rw[w]]).mean()) for w in W]
        # components vs R*
        r = {
            "candidate": n,
            "J": eqmean(W, n),
            "J_Rstar": m,
            **{f"vsRstar_{k_}": v for k_, v in s.items()},
            **{f"vsPair_{k_}": v for k_, v in sp.items()},
            "vsRw_dJ_mean": float(np.mean(pw)),
            "vsRw_win_neg": int(sum(x < 0 for x in pw)),
        }
        # per-pool split
        for pool in ("nine", "fresh"):
            vs = {w: v for w, v in comb(W, n, rstar).items() if w.startswith(pool)}
            r[f"vsRstar_{pool}_dJ"] = float(np.mean([v.mean() for v in vs.values()]))
        rows.append(r)
    L = pd.DataFrame(rows).sort_values("vsRstar_dJ")
    L.to_csv(sc.OUT / "tables" / "v2_check_odd.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print("R*:", rstar, "J on odd", round(m, 4))
    print(
        L[
            [
                "candidate",
                "J",
                "vsRstar_dJ",
                "vsRstar_pct",
                "vsRstar_lo",
                "vsRstar_hi",
                "vsRstar_win_neg",
                "vsPair_dJ",
                "vsRstar_nine_dJ",
                "vsRstar_fresh_dJ",
                "vsRw_dJ_mean",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "check"])
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    tune(a.k) if a.cmd == "tune" else check()
