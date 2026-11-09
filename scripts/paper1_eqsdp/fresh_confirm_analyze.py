"""Analysis of the doc-19 fresh confirmation (exactly the protocol's section 3).

    python fresh_confirm_analyze.py --records DIR/records.jsonl --out outputs/paper1_eqsdp/fresh

J = net cost per episode / T x 100 (pp of T); L likewise. Per-(stream, episode) values are averaged over
the 10 matched policy seeds before pairing. Equal-dataset mean = mean over datasets of per-dataset means.
Verdict rules: H1 passes iff delta < 0, bootstrap 95% CI upper bound < 0 and dL <= +0.1 pp. H2/H3 pass iff
delta < 0, Holm-adjusted (two tests) two-sided bootstrap p < .05 and dL <= +0.1 pp.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "qsg_methods_search"))
from analyze_all import ADAPTERS, CONTROLS

T = 2000
NBOOT = 2000
EQ_PAIR, W_PAIR = "P2_K2__E48_F60", "P4W__P2_K2__E48_F60"
EQ_CUT, W_CUT, ARM_R = "s2armr_H1100", "s2wald_l0.98_g0.3_H1100", "EQSDp_l0.98_g0.3"
SOTA = ADAPTERS + CONTROLS
MARGIN = 0.01


def load(path):
    d = pd.read_json(path, lines=True, dtype={"config_id": str})
    d = d.drop_duplicates(["stream", "ep", "seed", "config_id"])
    cols = ["net", "loss", "labels", "switches"]
    m = d.groupby(["stream", "ep", "config_id"])[cols].mean()
    return m, d.groupby(["stream", "config_id"]).seed.nunique()


def paired(m, cand, ref):
    a, b = m.xs(cand, level="config_id"), m.xs(ref, level="config_id")
    g = pd.DataFrame(
        {
            "J": a.net / T * 100,
            "Jr": b.net / T * 100,
            "dJ": (a.net - b.net) / T * 100,
            "dL": (a.loss - b.loss) / T * 100,
            "lab": a.labels,
            "sw": a.switches,
            "dlab": a.labels - b.labels,
            "dsw": a.switches - b.switches,
        }
    )
    return g.reset_index()


def eqmean(g, col):
    return float(g.groupby("stream")[col].mean().mean())


def boot(g, col="dJ", nb=NBOOT, seed=0):
    """Stratified episode bootstrap of the equal-dataset mean (and of the % of reference J)."""
    rng = np.random.default_rng(seed)
    num = den = 0
    for _, x in g.groupby("stream"):
        idx = rng.integers(0, len(x), size=(nb, len(x)))
        num = num + x[col].to_numpy()[idx].mean(1)
        den = den + x["Jr"].to_numpy()[idx].mean(1)
    k = g.stream.nunique()
    return num / k, 100 * num / den


def summary(g):
    r = {c: eqmean(g, c) for c in ("dJ", "dL", "J", "Jr", "lab", "sw", "dlab", "dsw")}
    r["pct"] = 100 * r["dJ"] / r["Jr"]
    reps, preps = boot(g)
    r["dJ_lo"], r["dJ_hi"] = (float(v) for v in np.quantile(reps, [0.025, 0.975]))
    r["dJ_lo975"], r["dJ_hi975"] = (float(v) for v in np.quantile(reps, [0.0125, 0.9875]))
    r["pct_lo"], r["pct_hi"] = (float(v) for v in np.quantile(preps, [0.025, 0.975]))
    r["p_boot"] = float(min(1.0, 2 * min((reps >= 0).mean(), (reps <= 0).mean())))
    x = np.sort(g.dJ.to_numpy())[::-1]
    k = max(1, int(np.ceil(0.05 * len(x))))
    r["cvar95_dJ"], r["worst_dJ"] = float(x[:k].mean()), float(x[0])
    pdm = g.groupby("stream").dJ.mean()
    r["K"], r["n_ep"] = len(pdm), len(g)
    r["neg_ds"] = int((pdm < 0).sum())
    r["t_p_one_sided"] = (
        float(stats.ttest_1samp(pdm, 0, alternative="less").pvalue) if len(pdm) > 1 else np.nan
    )
    r["per_dataset"] = {k: float(v) for k, v in pdm.items()}
    return r


def size_grade(pct):
    a = abs(pct)
    return "substantial" if a >= 2 else "meaningful" if a >= 0.5 else "small"


def noninf_table(m, arm, label):
    rows = []
    for stream, ms in m.groupby(level="stream"):
        ms = ms.droplevel("stream")
        for c in [*SOTA, ARM_R]:
            x = (ms.xs(arm, level="config_id").net - ms.xs(c, level="config_id").net).to_numpy()
            x = x / T * 100
            cj = ms.xs(c, level="config_id").net.mean() / T * 100
            rng = np.random.default_rng(0)
            idx = rng.integers(0, len(x), (NBOOT, len(x)))
            u = float(np.quantile(x[idx].mean(1), 0.95))
            rows.append(
                {
                    "arm": label,
                    "stream": stream,
                    "comp": c,
                    "n": len(x),
                    "delta": float(x.mean()),
                    "pct": float(100 * x.mean() / cj),
                    "U": u,
                    "margin": MARGIN * cj,
                    "sup": u < 0,
                    "noninf": u < MARGIN * cj,
                }
            )
    return pd.DataFrame(rows)


def pooled_vs(m, arm, label):
    rows = []
    for c in [*SOTA, ARM_R]:
        s = summary(paired(m, arm, c))
        pdm = pd.Series(s["per_dataset"])
        k = len(pdm)
        h = stats.t.ppf(0.975, k - 1) * pdm.std(ddof=1) / np.sqrt(k) if k > 1 else np.nan
        rows.append(
            {
                "arm": label,
                "comp": c,
                "K": k,
                "dJ": s["dJ"],
                "pct": s["pct"],
                "boot_lo": s["dJ_lo"],
                "boot_hi": s["dJ_hi"],
                "t_lo": pdm.mean() - h,
                "t_hi": pdm.mean() + h,
                "neg_ds": s["neg_ds"],
                "t_p_one_sided": s["t_p_one_sided"],
            }
        )
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", default="outputs/paper1_eqsdp/fresh")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    m, nseeds = load(a.records)
    res = {"seeds_min": int(nseeds.min()), "streams": sorted(m.index.levels[0])}
    rows = []
    for nm, c, r in (("H1", EQ_PAIR, EQ_CUT), ("H2", W_PAIR, W_CUT), ("H3", EQ_PAIR, W_CUT)):
        s = summary(paired(m, c, r))
        s.update(hyp=nm, cand=c, ref=r)
        rows.append(s)
    order = sorted([(rows[1]["p_boot"], 1), (rows[2]["p_boot"], 2)])
    adj, prev = {}, 0.0
    for i, (p, idx) in enumerate(order):
        prev = max(prev, min(1.0, (2 - i) * p))
        adj[idx] = prev
    pd_rows = []
    for i, s in enumerate(rows):
        s["acc_ok"] = bool(s["dL"] <= 0.1)
        s["size"] = size_grade(s["pct"])
        if s["hyp"] == "H1":
            s["p_adj"] = s["p_boot"]
            s["pass"] = bool(s["dJ"] < 0 and s["dJ_hi"] < 0 and s["acc_ok"])
        else:
            s["p_adj"] = adj[i]
            s["pass"] = bool(s["dJ"] < 0 and s["p_adj"] < 0.05 and s["acc_ok"])
        pd_rows += [{"hyp": s["hyp"], "dataset": k, "dJ": v} for k, v in s["per_dataset"].items()]
    flat = pd.DataFrame([{k: v for k, v in s.items() if k != "per_dataset"} for s in rows])
    flat.to_csv(out / "hypotheses.csv", index=False)
    pd.DataFrame(pd_rows).to_csv(out / "hypotheses_per_dataset.csv", index=False)
    pooled = pd.concat([pooled_vs(m, EQ_PAIR, "EQ+pair"), pooled_vs(m, EQ_CUT, "EQ+cut")])
    pooled.to_csv(out / "panel_pooled.csv", index=False)
    ni = pd.concat([noninf_table(m, EQ_PAIR, "EQ+pair"), noninf_table(m, EQ_CUT, "EQ+cut")])
    ni.to_csv(out / "panel_per_dataset.csv", index=False)
    cnt = []
    for arm, g in ni[ni.comp.isin(SOTA)].groupby("arm"):
        for stream, q in g.groupby("stream"):
            cnt.append(
                {
                    "arm": arm,
                    "stream": stream,
                    "noninf_all25": bool(q.noninf.all()),
                    "n_sup": int(q.sup.sum()),
                    "n_fail": int((~q.noninf).sum()),
                    "fails": ";".join(q[~q.noninf].comp),
                }
            )
    cnt = pd.DataFrame(cnt)
    cnt.to_csv(out / "panel_geq_sota.csv", index=False)
    jt = (m.net / T * 100).groupby(["stream", "config_id"]).mean().unstack("config_id")
    jt.to_csv(out / "mean_J_by_dataset_policy.csv")
    res["hypotheses"] = json.loads(flat.to_json(orient="records"))
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(flat.T)
    print(cnt.to_string())
    print(pooled.round(3).to_string())


if __name__ == "__main__":
    main()
