"""Comparison matrices: arms B and R versus every policy, nine datasets (reproduces analyze_all).

Delta = J(arm) - J(comparator) on seed-mean net cost per episode (negative = arm cheaper).
One-sided 95% upper bound U: episode bootstrap, 2000 resamples, np.random.default_rng(0) per cell,
exactly as scripts/qsg_methods_search/analyze_all.py. superior: U < 0; non-inferior: U < 1% of the
comparator's mean J.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import data

MARGIN, NBOOT = 0.01, 2000


def upper(x: np.ndarray, rng) -> float:
    idx = rng.integers(0, len(x), (NBOOT, len(x)))
    return float(np.quantile(x[idx].mean(1), 0.95))


def per_dataset(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stream, g in m.groupby(level="stream"):
        for arm, a in data.ARMS.items():
            for c in g.columns:
                if c == a:
                    continue
                x = (g[a] - g[c]).dropna().to_numpy()
                cj = g[c].mean()
                u = upper(x, np.random.default_rng(0))
                rows.append(
                    {
                        "dataset": stream, "arm": arm, "comp": c,
                        "class": data.policy_class(c), "n": len(x), "J_comp": cj,
                        "delta": x.mean(), "pct": 100 * x.mean() / cj, "U": u,
                        "superior": u < 0, "noninf": u < MARGIN * cj,
                    }
                )  # fmt: skip
    return pd.DataFrame(rows)


def pooled(r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (arm, c), q in r.groupby(["arm", "comp"]):
        k, mu, sd = len(q), q.delta.mean(), q.delta.std(ddof=1)
        h = stats.t.ppf(0.975, k - 1) * sd / np.sqrt(k)
        cj = q.J_comp.mean()
        rows.append(
            {
                "arm": arm, "comp": c, "class": q["class"].iloc[0], "K": k, "J_comp": cj,
                "mean_delta": mu, "mean_pct": q.pct.mean(), "t_lo": mu - h, "t_hi": mu + h,
                "n_neg": int((q.delta < 0).sum()), "t_p": stats.ttest_1samp(q.delta, 0).pvalue,
                "n_superior": int(q.superior.sum()), "n_noninf": int(q.noninf.sum()),
                "pooled_noninf": bool(mu + h < MARGIN * cj),
            }
        )  # fmt: skip
    return pd.DataFrame(rows)


def geq_counts(r: pd.DataFrame) -> pd.DataFrame:
    """Per arm and dataset: non-inferior to every uncertified comparator (25), superior counts."""
    u = r[r["class"].isin(["adapter", "control"])]
    g = u.groupby(["arm", "dataset"]).agg(
        n_comp=("comp", "size"), n_sup=("superior", "sum"), n_noninf=("noninf", "sum"),
        geq_all=("noninf", "all"),
    )  # fmt: skip
    return g.reset_index()


def crosscheck(r: pd.DataFrame, tol: float = 1e-9) -> dict:
    ref = pd.read_csv(data.ALL_TIER_CSV)
    ref = ref[ref.tier.isin(["S1", "S2"]) & ref.stream.isin(data.DATASETS)]
    mine = r.rename(columns={"dataset": "stream"})
    j = ref.merge(mine, on=["stream", "arm", "comp"], suffixes=("_ref", "_new"))
    out = {
        "reference_cells": len(ref), "matched_cells": len(j),
        "max_abs_diff_delta": float((j.delta_ref - j.delta_new).abs().max()),
        "max_abs_diff_pct": float((j.pct_ref - j.pct_new).abs().max()),
        "max_abs_diff_U": float((j.U_ref - j.U_new).abs().max()),
        "noninf_agree": int((j.noninf_ref == j.noninf_new).sum()),
        "sup_agree": int((j.sup == j.superior).sum()),
    }  # fmt: skip
    out["all_agree_within_tol"] = bool(
        out["matched_cells"] == out["reference_cells"]
        and max(out["max_abs_diff_delta"], out["max_abs_diff_U"]) < tol
        and out["noninf_agree"] == len(j)
        and out["sup_agree"] == len(j)
    )
    return out


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/paper1_eqsdp")
    a = ap.parse_args()
    d = data.load_records()
    m = data.episode_net(d)
    r = per_dataset(m)
    p = pooled(r)
    gq = geq_counts(r)
    cc = crosscheck(r)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r.to_csv(out / "matrix_per_dataset.csv", index=False, float_format="%.6g")
    p.to_csv(out / "matrix_pooled.csv", index=False, float_format="%.6g")
    gq.to_csv(out / "matrix_geq_counts.csv", index=False)
    (out / "matrix_crosscheck.json").write_text(json.dumps(cc, indent=1))
    print(json.dumps(cc, indent=1))
    print(gq.groupby("arm").geq_all.sum().to_dict(), "datasets with arm >= every uncertified")


if __name__ == "__main__":
    main()
