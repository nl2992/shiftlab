"""SOTA expansion analysis (sota_expansion/03_EXPERIMENT_PROTOCOL.md sections 4-8).

analyze_sota.py select DEV_RECORDS            -> prints the nine-dataset policy list
analyze_sota.py nine   NINE_RECORDS [C4_RECORDS]
analyze_sota.py synth  SYNTH_RECORDS
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sota_extra import FAMILIES, FIXED, FROZEN, SYNTH_SELECTED

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
DESCRIPTIVE = ["EQSDp_l0.95_g0.2", "EQSDp_l0.9_g0.5"]


def holm(ps):
    ps = np.asarray(ps, float)
    order, adj, run = np.argsort(ps), np.empty(len(ps)), 0.0
    for i, j in enumerate(order):
        run = max(run, (len(ps) - i) * ps[j])
        adj[j] = min(1.0, run)
    return adj


def grade(pct):
    a = abs(pct)
    return (
        "negligible" if a < 1 else "small" if a < 3 else "meaningful" if a < 10 else "substantial"
    )


def select(path):
    d = pd.read_json(path, lines=True)
    st = d.groupby(["policy", "stream"]).net.mean().unstack()
    score = st.mean(axis=1)  # equal stream weight
    chosen = {}
    for fam, grid in FAMILIES.items():
        g = score.reindex(grid).dropna()
        chosen[fam] = g.idxmin()
        print(
            f"# {fam}: RD={chosen[fam]} ({g.min():.2f}); SD={SYNTH_SELECTED[fam]} "
            f"({score.get(SYNTH_SELECTED[fam], np.nan):.2f}); top3={g.nsmallest(3).round(2).to_dict()}",
            file=sys.stderr,
        )
    print(
        f"# arm B dev score {score[FROZEN]:.2f}; arm A {score.get('EQSDp_l0.95_g0.2', np.nan):.2f}",
        file=sys.stderr,
    )
    print("# dev ranking (all):", file=sys.stderr)
    print(score.sort_values().round(2).to_string(), file=sys.stderr)
    pols = [FROZEN, *DESCRIPTIVE, *FIXED]
    for fam in FAMILIES:
        for p in (SYNTH_SELECTED[fam], chosen[fam]):
            if p not in pols:
                pols.append(p)
    print("\n".join(pols))
    return chosen


def _boot_pooled(eps, rng, n=2000):
    """eps: list of per-dataset arrays of episode deltas. Stratified bootstrap of equal-weight mean."""
    out = np.empty(n)
    for b in range(n):
        out[b] = np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in eps])
    return out


def nine(path, c4=None):
    d = pd.read_json(path, lines=True)
    if c4:
        old = pd.read_json(c4, lines=True)
        key = ["stream", "ep", "seed", "policy"]
        pols = ["EQSDp_l0.9_g0.2", "gongT_w100_m10", "qiu_delayed_movement"]
        m = old[old.policy.isin(pols)].merge(d[d.policy.isin(pols)], on=key, suffixes=("_c4", ""))
        diff = (m.net_c4 - m.net).abs().max()
        print(f"REPRO CHECK vs C4 records: {len(m)} matched rows, max |Δnet| = {diff}")
    e = d.groupby(["stream", "ep", "policy"]).net.mean().unstack()
    streams = list(dict.fromkeys(d.stream))
    comps = [p for p in e.columns if p != FROZEN]
    rows, per = [], []
    for c in comps:
        eps, rng = [], np.random.default_rng(0)
        for s in streams:
            x = e.loc[s]
            dl = (x[FROZEN] - x[c]).to_numpy()
            eps.append(dl)
            bs = np.array([dl[rng.integers(0, len(dl), len(dl))].mean() for _ in range(2000)])
            per.append(
                {
                    "comp": c,
                    "stream": s,
                    "delta": dl.mean(),
                    "pct": 100 * dl.mean() / x[c].mean(),
                    "lo": np.percentile(bs, 2.5),
                    "hi": np.percentile(bs, 97.5),
                    "J_comp": x[c].mean(),
                    "J_B": x[FROZEN].mean(),
                }
            )
        means = np.array([x.mean() for x in eps])
        pooled = means.mean()
        bs = _boot_pooled(eps, np.random.default_rng(1))
        p = max(1 / 2000, 2 * min((bs >= 0).mean(), (bs <= 0).mean()))
        jc = np.mean([e.loc[s][c].mean() for s in streams])
        neg = int((means < 0).sum())
        rows.append(
            {
                "comp": c,
                "delta": pooled,
                "lo": np.percentile(bs, 2.5),
                "hi": np.percentile(bs, 97.5),
                "pct": 100 * pooled / jc,
                "p_boot": p,
                "neg": neg,
                "sign_p": stats.binomtest(neg, len(means), 0.5).pvalue,
                "t_p_datasets": stats.ttest_1samp(means, 0).pvalue,
                "fav_B": sum(r["hi"] < 0 for r in per if r["comp"] == c),
                "fav_C": sum(r["lo"] > 0 for r in per if r["comp"] == c),
            }
        )
    r = pd.DataFrame(rows)
    r["p_holm"] = holm(r.p_boot)

    def verdict(x):
        if x.p_holm < 0.05 and x.delta < 0 and x.neg >= 6:
            return f"WIN ({grade(x.pct)})"
        if x.p_holm < 0.05 and x.delta > 0 and (9 - x.neg) >= 6:
            return f"LOSS ({grade(x.pct)})"
        return "COMPETITIVE"

    r["cost_verdict"] = r.apply(verdict, axis=1)
    sec = _secondary(d)
    print("\nPOOLED (equal dataset weight) Δ = J(arm B) − J(comp); negative favours arm B")
    print(r.sort_values("delta").round(4).to_string(index=False))
    print("\nSECONDARY (pooled over datasets, equal weight)")
    print(sec.round(3).to_string())
    pr = pd.DataFrame(per)
    print("\nPER-DATASET Δ (rows comp, cols dataset)")
    print(pr.pivot(index="comp", columns="stream", values="delta").round(2).to_string())
    print("\nPER-DATASET % of comparator cost")
    print(pr.pivot(index="comp", columns="stream", values="pct").round(2).to_string())
    print("\nPER-DATASET mean J")
    print(e.groupby(level=0).mean().T.round(2).to_string())
    print("\nΔ SPLIT by evaluator-side episode type (gain>0: challenger better in hindsight)")
    print(_split(d).round(2).to_string())
    out = {
        "pooled": r.to_dict("records"),
        "per": pr.to_dict("records"),
        "secondary": sec.reset_index().to_dict("records"),
    }
    with open(path.replace("records.jsonl", "analysis.json"), "w") as f:
        json.dump(out, f, default=float, indent=1)


def _secondary(d):
    g = d.groupby(["stream", "policy"])
    s = pd.DataFrame(
        {
            "J": g.net.mean(),
            "loss": g.loss.mean(),
            "labels": g.labels.mean(),
            "switches": g.switches.mean(),
        }
    )
    s["switch_cost"] = 5 * s.switches
    worse = d[d.mean_gain < 0].groupby(["stream", "policy"]).ever_promote.mean()
    better = (
        d[(d.mean_gain > 0) & (d.first_deploy >= 0)]
        .groupby(["stream", "policy"])
        .first_deploy.mean()
    )
    s["false_promo"] = worse
    s["delay_better"] = better
    s["never_better_promo"] = d[d.mean_gain > 0].groupby(["stream", "policy"]).ever_promote.mean()
    return s.groupby(level="policy").mean().sort_values("J")


def _split(d):
    d = d.assign(kind=np.where(d.mean_gain > 0, "better", "notbetter"))
    e = d.groupby(["stream", "kind", "ep", "policy"]).net.mean().unstack()
    out = {}
    for c in e.columns:
        if c == FROZEN:
            continue
        dl = (
            (e[FROZEN] - e[c]).groupby(level=["stream", "kind"]).mean().groupby(level="kind").mean()
        )
        out[c] = dl
    frac = (
        d.drop_duplicates(["stream", "ep"])
        .groupby("stream")
        .kind.apply(lambda k: (k == "better").mean())
    )
    print("fraction of episodes with challenger better (by dataset):", frac.round(2).to_dict())
    return pd.DataFrame(out).T


def synth(path):
    from analyze_d2 import CHANGE, GUARD, seedmean

    d = pd.read_json(path, lines=True)
    fam = seedmean(d, CHANGE + GUARD)
    eo = d[d.regime.isin(CHANGE + GUARD)].groupby("policy").regret_expected_oracle.mean()
    rows = []
    for c in fam.columns:
        if c == FROZEN:
            continue
        x = (fam[FROZEN] - fam[c]).to_numpy()
        m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
        h = stats.t.ppf(0.975, len(x) - 1) * se
        rows.append(
            {
                "comp": c,
                "delta": m,
                "lo": m - h,
                "hi": m + h,
                "p": 2 * stats.t.sf(abs(m / se), len(x) - 1) if se > 0 else 1.0,
                "pct_cost": 100 * m / fam[c].mean(),
                "pct_regret": 100 * m / eo[c],
            }
        )
    r = pd.DataFrame(rows)
    r["p_holm"] = holm(r.p)
    summ = pd.DataFrame(
        {
            "family": fam.mean(),
            "change": seedmean(d, CHANGE).mean(),
            "guard": seedmean(d, GUARD).mean(),
            "exp_oracle_regret": eo,
        }
    )
    summ["null_prom"] = (
        d[d.regime.isin(["F0_null", "V_null", "V_worse"])].groupby("policy").ever_promote.mean()
    )
    summ["sw_null"] = d[d.regime.isin(["F0_null", "V_null"])].groupby("policy").switches.mean()
    summ["labels"] = d.groupby("policy").labels.mean()
    print(f"seeds={fam.shape[0]}")
    print(r.sort_values("delta").round(3).to_string(index=False))
    print(summ.sort_values("family").round(2).to_string())
    pv = d.pivot_table(index="policy", columns="regime", values="net", aggfunc="mean")
    print(pv[CHANGE + GUARD].round(1).to_string())
    with open(path.replace("records.jsonl", "analysis.json"), "w") as f:
        json.dump(
            {"contrasts": r.to_dict("records"), "summary": summ.reset_index().to_dict("records")},
            f,
            default=float,
            indent=1,
        )


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"select": select, "nine": nine, "synth": synth}[cmd](*sys.argv[2:])
