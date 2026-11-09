"""Stage 1 analysis: paired deltas vs the reference Wald and vs arm R, matched controls, verdicts.

  python stage1_analysis.py            # all finished candidates -> docs/paper1_eqsdp/tables/stage1_*.csv
All numbers are computed from records written by stage1_run.py and the Stage 0 records.
Delta J < 0 is an improvement. Pooled = equal-dataset mean of per-dataset episode means (seeds
averaged within episode first); CI = percentile interval of independent per-dataset episode
bootstraps (2000 resamples) averaged with equal weight (stage0_analysis.boot).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_analysis as s0a
import stage1_policies as sp
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
REF = "wald_l0.97_g0.2"
ARM = tr.ARM_R
T = 2000
DS = list(tr.NINE)
COMP = tr.COMPONENTS
METRICS = ["net", "loss", "labels", "switches", *COMP]
TARGET = {"c1": "d_label_spend", "c2": "d_false_promotion", "c5": "d_late_adoption"}


def load(cand: str) -> pd.DataFrame:
    parts = [pd.read_json(OUT / "stage1" / cand / "records.jsonl", lines=True)]
    ext = OUT / "stage1" / f"{cand}_ext" / "records.jsonl"
    if ext.exists():  # extended control grids: add only policies not already present
        x = pd.read_json(ext, lines=True)
        parts.append(x[x.policy != ARM])
    d = pd.concat(parts, ignore_index=True)
    ref = pd.read_json(OUT / "stage0/p1/records.jsonl", lines=True)
    ref = ref[ref.policy == REF].assign(first_deploy=np.nan, better=np.nan, secs=np.nan)
    return pd.concat([d, ref[d.columns]], ignore_index=True)


def episode_table(d: pd.DataFrame) -> pd.DataFrame:
    """Seed-mean per (stream, ep, policy) plus promoted flag and censored adoption time."""
    d = d.copy()
    d["promoted"] = (d.switches >= 1).astype(float)
    d["t_adopt"] = np.where(d.first_deploy >= 0, d.first_deploy, T).astype(float)
    cols = [*METRICS, "promoted", "t_adopt", "secs"]
    e = d.groupby(["stream", "ep", "policy"])[cols].mean().reset_index()
    better = d[d.better.notna()].groupby(["stream", "ep"]).better.max().rename("better_ep")
    return e.merge(better.reset_index(), on=["stream", "ep"], how="left")


def wide(e: pd.DataFrame, pol: str) -> pd.DataFrame:
    return e[e.policy == pol].set_index(["stream", "ep"]).sort_index()


def delta_boot(e, a: str, b: str, cols=METRICS):
    """a - b paired by (stream, ep); {dataset|POOLED: (mean, lo, hi)} over cols."""
    wa, wb = wide(e, a), wide(e, b)
    idx = wa.index.intersection(wb.index)
    per = {}
    for ds in DS:
        ix = [i for i in idx if i[0] == ds]
        per[ds] = (wa.loc[ix, cols].values - wb.loc[ix, cols].values).astype(float)
    return s0a.boot(per)


def level(e, pol, col, restrict=None):
    """Equal-dataset mean of a per-episode column (optionally on better_ep == restrict)."""
    w = wide(e, pol)
    w = w[w.better_ep.notna()] if restrict is not None else w
    vals = []
    for ds in DS:
        x = w.loc[ds]
        if restrict is not None:
            x = x[x.better_ep == restrict]
        if len(x):
            vals.append(x[col].mean())
    return float(np.mean(vals))


def pol_row(e, pol, vs: str, jref: float) -> dict:
    r = delta_boot(e, pol, vs)
    ix = {m: i for i, m in enumerate(METRICS)}
    m, lo, hi = r["POOLED"]
    j = ix["net"]
    out = {
        "policy": pol,
        "vs": vs,
        "dJ": m[j],
        "dJ_lo": lo[j],
        "dJ_hi": hi[j],
        "dJ_pct": 100 * m[j] / jref,
        "dJ_pct_lo": 100 * lo[j] / jref,
        "dJ_pct_hi": 100 * hi[j] / jref,
        "n_ds_better": int(sum(r[ds][0][j] < 0 for ds in DS)),
        "n_ds_worse": int(sum(r[ds][0][j] > 0 for ds in DS)),
        "dLT_pp": 100 * m[ix["loss"]] / T,
        "dLT_pp_lo": 100 * lo[ix["loss"]] / T,
        "dLT_pp_hi": 100 * hi[ix["loss"]] / T,
    }
    for c in ["labels", "switches", *COMP]:
        out[f"d_{c}"] = m[ix[c]]
        out[f"d_{c}_lo"] = lo[ix[c]]
        out[f"d_{c}_hi"] = hi[ix[c]]
    out["J"] = level(e, pol, "net")
    out["labels"] = level(e, pol, "labels")
    out["switches"] = level(e, pol, "switches")
    out["mean_secs"] = level(e, pol, "secs") if pol != REF else np.nan
    out["notbetter_promo_rate"] = level(e, pol, "promoted", restrict=0)
    out["t_adopt_better"] = level(e, pol, "t_adopt", restrict=1)
    return out


def nearest(rows: pd.DataFrame, col: str, target: float) -> str:
    return rows.iloc[(rows[col] - target).abs().argsort().iloc[0]].policy


def verdict(row: dict, comp_col: str) -> str:
    """Plan 4 Stage 1: continue if dJ<0 with CI excluding 0, or <= -0.5% with a clear signal on the
    target component (component CI excludes 0 in the helpful, i.e. negative, direction)."""
    if row["dJ_hi"] < 0:
        return "continue (dJ<0, CI excludes 0)"
    if row["dJ_pct"] <= -0.5 and row[f"{comp_col}_hi"] < 0:
        return "continue (<= -0.5% with clear component signal)"
    return "stop"


def analyze_cand(cand: str, jref: float) -> dict:
    d = load(cand)
    e = episode_table(d)
    g = sp.grid_names(cand)
    chk = d[d.policy.isin([ARM, *g["check"]])].pivot_table(
        index=["stream", "ep", "seed"], columns="policy", values="net"
    )
    checks = {c: float((chk[c] - chk[ARM]).abs().max()) for c in g["check"]}
    s0 = pd.read_json(OUT / "stage0/p1/records.jsonl", lines=True).query("policy == @ARM")
    m = d[d.policy == ARM].merge(s0, on=["stream", "ep", "seed"], suffixes=("", "_s0"))
    checks["armR_vs_stage0_records_max_abs"] = float((m.net - m.net_s0).abs().max())
    checks["armR_vs_stage0_n"] = len(m)
    if cand == "c1" and "s1wald_inert" in set(d.policy):
        wc = d[d.policy.isin([REF, "s1wald_inert"])].pivot_table(
            index=["stream", "ep", "seed"], columns="policy", values="net"
        )
        checks["wald_inert_vs_ref_max_abs"] = float((wc["s1wald_inert"] - wc[REF]).abs().max())
    rows_ref = pd.DataFrame([pol_row(e, p, REF, jref) for p in [ARM, *g["grid"]]])
    rows_arm = pd.DataFrame([pol_row(e, p, ARM, jref) for p in g["grid"]])
    grid = rows_ref[rows_ref.policy.isin(g["grid"])]
    best = grid.sort_values("dJ").iloc[0]
    bp = best.policy
    pool = pd.DataFrame([pol_row(e, p, REF, jref) for p in g["control_a"] + g["control_b"]])
    if cand == "c1":
        ca = pool[pool.policy.isin(g["control_a"])]
        cb = pool[pool.policy.isin(g["control_b"])]
        ctl = {
            "uniform_thinning": nearest(ca, "labels", best.labels),
            "hard_stop": nearest(cb, "labels", best.labels),
        }
    elif cand == "c2":
        ctl = {"raised_hurdle": nearest(pool, "notbetter_promo_rate", best.notbetter_promo_rate)}
    else:
        ctl = {"larger_gamma": nearest(pool, "t_adopt_better", best.t_adopt_better)}
    detail = []
    for label, p in [("best", bp), ("armR", ARM), *[(f"control:{k}", v) for k, v in ctl.items()]]:
        detail.append({**pol_row(e, p, REF, jref), "role": label})
        if p != ARM:
            detail.append({**pol_row(e, p, ARM, jref), "role": label})
    for k, v in ctl.items():
        detail.append({**pol_row(e, bp, v, jref), "role": f"best_minus_control:{k}"})
    if cand == "c1":  # supplementary: the reference with the same hard label stop
        for p in sorted(x for x in set(d.policy) if x.startswith("s1wald_stop_")):
            detail.append({**pol_row(e, p, REF, jref), "role": "suppl:ref+stop"})
            detail.append({**pol_row(e, bp, p, jref), "role": f"suppl:best_minus:{p}"})
    detail = pd.DataFrame(detail)
    best_dict = rows_ref[rows_ref.policy == bp].iloc[0].to_dict()
    med = grid.iloc[(grid.dJ - grid.dJ.median()).abs().argsort().iloc[0]].policy
    pd.concat([rows_ref.assign(cmp="vs_ref"), rows_arm.assign(cmp="vs_armR")]).to_csv(
        TABLES / f"stage1_{cand}_grid.csv", index=False
    )
    pool.to_csv(TABLES / f"stage1_{cand}_control_grid.csv", index=False)
    detail.to_csv(TABLES / f"stage1_{cand}_best.csv", index=False)
    return {
        "best": bp,
        "median_config": med,
        "grid_median_dJ": float(grid.dJ.median()),
        "grid_median_dJ_pct": float(grid.dJ_pct.median()),
        "grid_worst_dJ": float(grid.dJ.max()),
        "n_grid": len(grid),
        "n_grid_better_than_ref": int((grid.dJ < 0).sum()),
        "verdict_best": verdict(best_dict, TARGET[cand]),
        "controls": ctl,
        "checks": checks,
        "armR_vs_ref_dJ": float(rows_ref[rows_ref.policy == ARM].dJ.iloc[0]),
    }


def main():
    out = {}
    for cand in ("c1", "c2", "c5"):
        if not (OUT / "stage1" / cand / "records.jsonl").exists():
            continue
        if "J_ref_pooled" not in out:
            out["J_ref_pooled"] = level(episode_table(load(cand)), REF, "net")
        out[cand] = analyze_cand(cand, out["J_ref_pooled"])
    (OUT / "stage1" / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
