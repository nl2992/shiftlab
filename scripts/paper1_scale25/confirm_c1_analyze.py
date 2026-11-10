"""Protocol C1 step 5: analysis exactly per docs/paper1_scale25/07a_PROTOCOL_C1_V1_22.md section 4.

    python confirm_c1_analyze.py --records-dir outputs/paper1_scale25/c1/run [--open-ledger]

J(d,p) = 100 * mean over episodes of the seed-averaged net/T;  r_d = 100*(J_ref - J_v1)/J_ref.
Primary reference: W+cut. Outputs (small CSV/JSON): docs/paper1_scale25/confirm_C1_results/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/stats"))
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/confirm"))
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))
import ledger as lg
from analyze_all import ADAPTERS, CONTROLS

T = 2000
NBOOT = 2000
MARGIN = 0.01
EQ_PAIR, W_PAIR = "P2_K2__E48_F60", "P4W__P2_K2__E48_F60"
EQ_CUT, W_CUT, ARM_R = "s2armr_H1100", "s2wald_l0.98_g0.3_H1100", "EQSDp_l0.98_g0.3"
V1 = EQ_PAIR
SOTA = ADAPTERS + CONTROLS
CUT = [f"{n}_H1100" for n in SOTA if n != "model_selector_causal"]
CUT_PANEL = [f"{n}_H1100" if n != "model_selector_causal" else n for n in SOTA]
PORTS_RAW = ["mp_paper_recommend", "mp_paper_sample", "cams_paper", "cams_paper_gated"]
PORTS_CUT = [f"{n}_H1100" for n in PORTS_RAW]
LEDGER = ROOT / "docs/paper1_scale25/confirmation_attempts.csv"
REG = ROOT / "docs/paper1_scale25/confirm_registration_C1.json"
OUT = ROOT / "docs/paper1_scale25/confirm_C1_results"
ORG_PAIRS = [
    ("nyc_ems_response", "nyc_fire_response"),
    ("divvy_chicago", "capitalbikeshare_dc"),
    ("mc311_montgomery", "montgomery_police_dispatch"),
]


def load(rdir, names):
    fr = []
    for ds in names:
        f = Path(rdir) / ds / "records.jsonl"
        fr.append(pd.read_json(f, lines=True, dtype={"config_id": str}))
    d = pd.concat(fr).drop_duplicates(["stream", "ep", "seed", "config_id"])
    cols = [
        "net",
        "loss",
        "labels",
        "switches",
        "late_adoption",
        "false_promotion",
        "reversal_churn",
        "label_spend",
        "residual",
        "regret",
    ]
    m = d.groupby(["stream", "ep", "config_id"])[cols].mean()
    return d, m


def ttest_greater(x):
    x = np.asarray(x, float)
    k = len(x)
    if k < 2:
        return {
            "K": k,
            "mean": float(x.mean()) if k else np.nan,
            "lo": np.nan,
            "hi": np.nan,
            "p": np.nan,
            "t": np.nan,
        }
    h = stats.t.ppf(0.975, k - 1) * x.std(ddof=1) / np.sqrt(k)
    res = stats.ttest_1samp(x, 0.0, alternative="greater")
    return {
        "K": k,
        "mean": float(x.mean()),
        "lo": float(x.mean() - h),
        "hi": float(x.mean() + h),
        "p": float(res.pvalue),
        "t": float(res.statistic),
    }


def Jtab(m):
    return (m.net / T * 100).groupby(["stream", "config_id"]).mean().unstack("config_id")


def r_of(J, cand, ref):
    return 100 * (J[ref] - J[cand]) / J[ref]


def dL_of(m, cand, ref):
    a = m.loss.groupby(["stream", "config_id"]).mean().unstack("config_id")
    return (a[cand] - a[ref]) / T * 100


def noninf(m, cand, comps, streams):
    rows = []
    for s in streams:
        ms = m.xs(s, level="stream")
        a = ms.xs(cand, level="config_id").net
        for c in comps:
            b = ms.xs(c, level="config_id").net
            x = ((a - b) / T * 100).to_numpy()
            cj = b.mean() / T * 100
            idx = np.random.default_rng(0).integers(0, len(x), (NBOOT, len(x)))
            u = float(np.quantile(x[idx].mean(1), 0.95))
            rows.append(
                {
                    "stream": s,
                    "comp": c,
                    "delta": float(x.mean()),
                    "pct": float(100 * x.mean() / cj),
                    "U": u,
                    "margin": MARGIN * cj,
                    "sup": u < 0,
                    "noninf": u < MARGIN * cj,
                }
            )
    return pd.DataFrame(rows)


def pooled(J, cand, comps, label):
    rows = []
    for c in comps:
        r = r_of(J, cand, c)
        t = ttest_greater(r)
        rows.append(
            {
                "set": label,
                "comp": c,
                "K": t["K"],
                "mean_r_pct": t["mean"],
                "ci_lo": t["lo"],
                "ci_hi": t["hi"],
                "p_one_sided": t["p"],
                "n_pos": int((r > 0).sum()),
                "n_neg": int((r < 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records-dir", required=True)
    ap.add_argument("--open-ledger", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    reg = json.loads(REG.read_text(encoding="utf-8"))
    el = [d for d in reg["datasets"] if d["eligibility"]["eligible"]]
    names = [d["name"] for d in el]
    {d["name"]: d for d in el}
    raw, m = load(a.records_dir, names)
    nseeds = raw.groupby(["stream", "config_id"]).seed.nunique()
    assert nseeds.min() == 10, nseeds.min()
    J = Jtab(m)
    J = J.loc[names]
    res = {"datasets": names, "K": len(names), "seeds": 10}

    # ---------------- primary
    r = r_of(J, V1, W_CUT)
    dl = dL_of(m, V1, W_CUT).loc[names]
    prim = ttest_greater(r)
    prim["n_pos"], prim["n_neg"], prim["n_zero"] = (
        int((r > 0).sum()),
        int((r < 0).sum()),
        int((r == 0).sum()),
    )
    prim["mean_dL_pp"] = float(dl.mean())
    prim["dJ_pp_mean"] = float((J[V1] - J[W_CUT]).mean())
    prim["accuracy_constraint_dL_le_0.1pp"] = bool(dl.mean() <= 0.1)
    prim["passes"] = bool(prim["p"] < 0.05 and prim["mean"] > 0 and dl.mean() <= 0.1)
    groups = []
    used = set()
    for p1, p2 in ORG_PAIRS:
        if p1 in r.index and p2 in r.index:
            groups.append(float(r[[p1, p2]].mean()))
            used |= {p1, p2}
        elif p1 in r.index or p2 in r.index:
            groups.append(float(r[next(x for x in (p1, p2) if x in r.index)]))
            used |= {p1, p2}
    groups += [float(v) for k, v in r.items() if k not in used]
    prim_org = ttest_greater(groups)
    prim_org["note"] = "within-organisation pairs averaged first: " + "; ".join(
        "+".join(p) for p in ORG_PAIRS
    )
    res["primary"] = prim
    res["primary_org_merged"] = prim_org

    # ---------------- per-dataset table + certification (design B)
    rows = []
    for d in el:
        n = d["name"]
        x = m.xs(n, level="stream")
        e = {}
        for tag, c in (("v1", V1), ("W", W_CUT), ("EQ", EQ_CUT), ("Wpair", W_PAIR)):
            e[f"labels_{tag}"] = float(x.xs(c, level="config_id").labels.mean())
            e[f"switches_{tag}"] = float(x.xs(c, level="config_id").switches.mean())
        rows.append(
            dict(
                protocol_order=d["protocol_order"],
                ledger_index=d["ledger_index"],
                dataset=n,
                domain=d["domain"],
                episodes=d["episodes"],
                delay=d["delay"],
                J_v1=J.loc[n, V1],
                J_Wcut=J.loc[n, W_CUT],
                J_EQcut=J.loc[n, EQ_CUT],
                J_Wpair=J.loc[n, W_PAIR],
                r_v1_vs_Wcut_pct=r[n],
                dL_pp=dl[n],
                dJ_pp=J.loc[n, V1] - J.loc[n, W_CUT],
                **e,
            )
        )
    pdf = pd.DataFrame(rows).sort_values("protocol_order")
    ep_series = {}
    for d in el:
        n = d["name"]
        ms = m.xs(n, level="stream")
        ep_series[n] = (
            ms.xs(V1, level="config_id").net.sort_index().to_numpy() * 100 / T,
            ms.xs(W_CUT, level="config_id").net.sort_index().to_numpy() * 100 / T,
        )
    lows, alphas = [], []
    if a.open_ledger:
        tab = {x["index"]: x for x in lg.attempt_table(LEDGER)}
        for d in sorted(el, key=lambda z: z["ledger_index"]):
            i = d["ledger_index"]
            assert not tab[i]["opened"], f"attempt {i} already opened"
            aa, bb = ep_series[d["name"]]
            out = lg.open_attempt(
                LEDGER,
                i,
                aa,
                bb,
                note="C1 primary: v1 vs W+cut, block-Fieller min over two block lengths",
            )
            lows.append(out["L"])
            alphas.append(out["alpha"])
        pdf["alpha_i"] = alphas
        pdf["L_lower_pct"] = lows
    else:
        tab = {x["index"]: x for x in lg.attempt_table(LEDGER)}
        pdf["alpha_i"] = [tab[i]["alpha"] for i in pdf.ledger_index]
        pdf["L_lower_pct"] = [tab[i]["L"] for i in pdf.ledger_index]
    pdf.to_csv(OUT / "per_dataset.csv", index=False, float_format="%.5f")
    cert = lg.certify_cohort(LEDGER, min_datasets=25, min_R=2.5)
    res["certify_cohort"] = cert
    res["ledger_problems"] = lg.validate(LEDGER)
    res["n_L_gt_0"] = int((pdf.L_lower_pct.astype(float) > 0).sum())

    # ---------------- secondary (Holm over two)
    sec = {}
    for nm, cand, ref in (("v1_vs_EQcut", V1, EQ_CUT), ("Wpair_vs_Wcut", W_PAIR, W_CUT)):
        rr = r_of(J, cand, ref)
        t = ttest_greater(rr)
        t |= {
            "n_pos": int((rr > 0).sum()),
            "n_neg": int((rr < 0).sum()),
            "mean_dL_pp": float(dL_of(m, cand, ref).loc[names].mean()),
        }
        sec[nm] = t
    ps = sorted((sec[k]["p"], k) for k in sec)
    prev = 0.0
    for i, (p, k) in enumerate(ps):
        prev = max(prev, min(1.0, (len(ps) - i) * p))
        sec[k]["p_holm"] = prev
    res["secondary"] = sec

    # ---------------- descriptive: v1 vs panels
    panels = {
        "raw25": SOTA,
        "armR": [ARM_R],
        "cut25": CUT_PANEL,
        "ports_raw": PORTS_RAW,
        "ports_cut": PORTS_CUT,
    }
    pooled_df = pd.concat([pooled(J, V1, c, k) for k, c in panels.items()])
    pooled_df.to_csv(OUT / "panel_pooled.csv", index=False, float_format="%.5f")
    ni = pd.concat([noninf(m, V1, c, names).assign(set=k) for k, c in panels.items()])
    ni.to_csv(OUT / "panel_per_dataset.csv", index=False, float_format="%.5f")
    cnt = []
    for k in panels:
        g = ni[ni.set == k]
        for s, q in g.groupby("stream"):
            cnt.append(
                {
                    "set": k,
                    "stream": s,
                    "noninf_all": bool(q.noninf.all()),
                    "n_sup": int(q.sup.sum()),
                    "n_fail": int((~q.noninf).sum()),
                    "fails": ";".join(q[~q.noninf].comp),
                }
            )
    cnt = pd.DataFrame(cnt)
    cnt.to_csv(OUT / "panel_geq_sota.csv", index=False)
    res["geq_sota_counts"] = {k: int(cnt[(cnt.set == k)].noninf_all.sum()) for k in panels}
    res["geq_sota_counts"]["raw25_and_cut25"] = int(
        (
            cnt[cnt.set == "raw25"].set_index("stream").noninf_all
            & cnt[cnt.set == "cut25"].set_index("stream").noninf_all
        ).sum()
    )
    # best of panel (optimistic: reference chosen after seeing the confirmation data)
    pool = [c for c in J.columns if c not in (V1, W_PAIR)]
    best = J[pool].min(axis=1)
    rb = 100 * (best - J[V1]) / best
    tb = ttest_greater(rb)
    tb |= {
        "n_pos": int((rb > 0).sum()),
        "n_neg": int((rb < 0).sum()),
        "best_policy": J[pool].idxmin(axis=1).to_dict(),
        "label": "OPTIMISTIC: per-dataset best of all panel/control/port policies selected after the results",
    }
    res["best_of_panel"] = tb
    J.to_csv(OUT / "mean_J_by_dataset_policy.csv", float_format="%.5f")

    # ---------------- labels / switches / decomposition (equal-dataset means)
    dec = []
    for c in (V1, W_CUT, EQ_CUT, W_PAIR, ARM_R):
        x = m.xs(c, level="config_id").groupby("stream").mean().loc[names]
        dec.append(dict(policy=c, **{k: float(x[k].mean()) for k in x.columns}))
    pd.DataFrame(dec).to_csv(OUT / "decomposition.csv", index=False, float_format="%.5f")

    # ---------------- by domain
    bd = (
        pdf.groupby("domain")
        .agg(
            K=("r_v1_vs_Wcut_pct", "size"),
            mean_r=("r_v1_vs_Wcut_pct", "mean"),
            n_pos=("r_v1_vs_Wcut_pct", lambda v: int((v > 0).sum())),
            mean_dL=("dL_pp", "mean"),
        )
        .reset_index()
    )
    bd.to_csv(OUT / "by_domain.csv", index=False, float_format="%.5f")
    (OUT / "summary.json").write_text(json.dumps(res, indent=1, default=str))
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "primary",
                    "primary_org_merged",
                    "secondary",
                    "geq_sota_counts",
                    "n_L_gt_0",
                )
            },
            indent=1,
            default=str,
        )
    )
    print(json.dumps(cert, indent=1, default=str))


if __name__ == "__main__":
    main()
