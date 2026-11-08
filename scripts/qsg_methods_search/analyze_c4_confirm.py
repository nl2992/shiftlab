"""Locked C4 analysis (c4_plan.md §5 with Amendment A1). Usage: analyze_c4_confirm.py records.jsonl

Per dataset: Δ_e = seed-mean over policy seeds of J(arm B) − J(gongT_w100_m10) per episode;
SUPPORTS iff the one-sided 95% upper bound of mean Δ_e (2,000 episode-bootstrap resamples,
rng seed 0) is < 0. Count rule: C4 PASS iff supporting datasets ≥ 8, one per data-generating
organisation (registration field `org`); the sensitivity count keeps at most one per `city`.
Also reported: X/K, one-sided sign test over all K on mean Δ, and the pooled secondary
one-sided t-test of per-dataset mean J(B) − J(qiu_delayed_movement) across all K.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REG = Path(
    os.environ.get(
        "C4_REG",
        Path(__file__).resolve().parents[2] / "docs/qsg_methods_search/c4_registration.json",
    )
)
ARM, PRIMARY, SECONDARY = "EQSDp_l0.9_g0.2", "gongT_w100_m10", "qiu_delayed_movement"


def main(path):
    reg = {d["name"]: d for d in json.loads(REG.read_text())["datasets"]}
    d = pd.read_json(path, lines=True)
    e = d.groupby(["stream", "ep", "policy"]).net.mean().unstack()
    rng = np.random.default_rng(0)
    rows = []
    for name in reg:
        x = e.loc[name]
        dl = (x[ARM] - x[PRIMARY]).to_numpy()
        bs = np.array([dl[rng.integers(0, len(dl), len(dl))].mean() for _ in range(2000)])
        ub = float(np.percentile(bs, 95))
        rows.append(
            {
                "dataset": name,
                "org": reg[name]["org"],
                "city": reg[name]["city"],
                "episodes": len(dl),
                "delta_primary": dl.mean(),
                "ub95": ub,
                "supports": ub < 0,
                "delta_secondary": float((x[ARM] - x[SECONDARY]).mean()),
                "delta_never": float((x[ARM] - x["CONTROL_never_switch"]).mean()),
            }
        )
    r = pd.DataFrame(rows)
    print(r.round(3).to_string(index=False))
    sup = r[r.supports]
    n_org = sup.org.nunique()
    n_city = sup.drop_duplicates("city").shape[0]
    K = len(r)
    neg = int((r.delta_primary < 0).sum())
    sign_p = stats.binomtest(neg, K, 0.5, alternative="greater").pvalue
    t = stats.ttest_1samp(r.delta_secondary, 0.0, alternative="less")
    print(f"\nsupporting (distinct orgs): {n_org} / {K}   sensitivity (one per city): {n_city}")
    print(f"sign test: {neg}/{K} negative, one-sided p={sign_p:.3g}")
    print(
        f"pooled secondary vs Qiu-style: mean {r.delta_secondary.mean():+.2f}, one-sided p={t.pvalue:.3g}"
    )
    print("C4 VERDICT:", "PASS" if n_org >= 8 else "NOT PASS")


if __name__ == "__main__":
    main(sys.argv[1])
