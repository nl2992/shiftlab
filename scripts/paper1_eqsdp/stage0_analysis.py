"""Stage 0 analysis: reproduction check, reference baseline, decomposition, ceiling, stop rule.

Reads traced-run records (stage0_headroom.py run) and the existing nine-dataset records (read only).
Writes small CSVs to docs/paper1_eqsdp/tables/stage0_*.csv and a JSON of headline numbers to
outputs/paper1_eqsdp/stage0/summary.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import trace_run as tr

import data

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage0"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
NBOOT = 2000
DS = list(tr.NINE)
KEY = ["stream", "ep", "seed", "policy"]


def load_jsonl(p):
    return pd.read_json(Path(p) / "records.jsonl", lines=True)


def ep_mean(d: pd.DataFrame, cols) -> pd.DataFrame:
    """Seed-mean per (stream, ep, policy)."""
    return d.groupby(["stream", "ep", "policy"])[list(cols)].mean().reset_index()


def boot(per_ep: dict[str, np.ndarray], seed=0):
    """Per-dataset and pooled (equal-dataset) mean with episode-bootstrap 95% CI.

    per_ep: dataset -> (n_ep, k) array. Returns dataset -> (mean, lo, hi) arrays of length k,
    plus 'POOLED'. One shared resample per dataset across the k columns.
    """
    res, boots = {}, []
    for i, ds in enumerate(DS):
        x = per_ep[ds]
        rng = np.random.default_rng([seed, i])
        idx = rng.integers(0, len(x), (NBOOT, len(x)))
        b = x[idx].mean(1)  # NBOOT x k
        boots.append(b)
        res[ds] = (x.mean(0), *np.percentile(b, [2.5, 97.5], axis=0))
    pb = np.mean(boots, axis=0)
    pm = np.mean([per_ep[ds].mean(0) for ds in DS], axis=0)
    res["POOLED"] = (pm, *np.percentile(pb, [2.5, 97.5], axis=0))
    return res


def reproduction(p1: pd.DataFrame, orig: pd.DataFrame) -> dict:
    even = orig[orig.ep % 2 == 0]
    m = p1.merge(even[[*KEY, "net"]], on=KEY, how="inner", suffixes=("", "_orig_rec"))
    diff = (m.net - m.net_orig_rec).abs()
    out = {"policies_rerun": sorted(p1.policy.unique())}
    per = m.assign(d=diff).groupby("policy").agg(n=("d", "size"), max_abs=("d", "max"))
    out["overlap_with_original_records"] = {
        k: {"n": int(v.n), "max_abs_net_diff": float(v.max_abs)} for k, v in per.iterrows()
    }
    out["total_compared"] = len(m)
    out["total_mismatched"] = int((diff > 1e-9).sum())
    out["armR_expected_rows"] = len(even[even.policy == tr.ARM_R])
    out["armR_rerun_rows"] = int((p1.policy == tr.ARM_R).sum())
    if "net_orig" in p1:
        c = p1[p1.policy == tr.ARM_R]
        out["armR_traced_vs_run_metrics_max_abs"] = float((c.net - c.net_orig).abs().max())
    out["decomposition_max_abs_gap"] = float(
        (p1.regret - p1[tr.COMPONENTS].sum(axis=1)).abs().max()
    )
    return out


def ranking(p1: pd.DataFrame, orig: pd.DataFrame) -> pd.DataFrame:
    """Equal-dataset mean J on even episodes: panel from records, new Wald configs from rerun."""
    even = orig[orig.ep % 2 == 0]
    a = ep_mean(even, ["net"]).assign(src="panel_records")
    b = ep_mean(p1, ["net"])
    b = b[~b.policy.isin(set(a.policy))].assign(src="rerun")
    x = pd.concat([a, b])
    ds = x.groupby(["policy", "src", "stream"]).net.mean().reset_index()
    pool = ds.groupby(["policy", "src"]).net.agg(["mean", "count"]).reset_index()
    pool = pool[pool["count"] == len(DS)].rename(columns={"mean": "J_equal_dataset"})
    known = data.UNCERTIFIED + data.CERTIFIED + [data.NEVER]
    pool["class"] = [
        "wald_grid" if p in tr.WALD_GRID else (data.policy_class(p) if p in known else "own")
        for p in pool.policy
    ]
    return pool.sort_values("J_equal_dataset").reset_index(drop=True)


def per_ep_matrix(d: pd.DataFrame, policy: str, cols) -> dict[str, np.ndarray]:
    e = ep_mean(d[d.policy == policy], cols).sort_values(["stream", "ep"])
    return {ds: e[e.stream == ds][list(cols)].to_numpy() for ds in DS}


def decomposition(d: pd.DataFrame, policy: str, jref: dict) -> pd.DataFrame:
    cols = [*tr.COMPONENTS, "regret", "net"]
    res = boot(per_ep_matrix(d, policy, cols))
    rows = []
    for ds in [*DS, "POOLED"]:
        mean, lo, hi = res[ds]
        for k, c in enumerate(cols):
            rows.append(
                {
                    "policy": policy, "dataset": ds, "component": c, "mean": mean[k],
                    "lo": lo[k], "hi": hi[k], "pct_Jref": 100 * mean[k] / jref[ds],
                    "pct_lo": 100 * lo[k] / jref[ds], "pct_hi": 100 * hi[k] / jref[ds],
                }
            )  # fmt: skip
    return pd.DataFrame(rows)


def ceiling(p200: pd.DataFrame, p400: pd.DataFrame, policy: str, jref: dict) -> pd.DataFrame:
    """Delta J (B=400 minus B=200), excluding and including label fees; negative = improvement."""
    cols = ["loss", "switches", "labels", "net"]
    out = []
    quantities = (
        ("excl_label_fees", lambda e: e.loss + tr.CS * e.switches),
        ("incl_label_fees", lambda e: e.net),
        ("label_fees_only", lambda e: tr.CQ * e.labels),
    )
    for nm, f in quantities:
        mats = {}
        for ds in DS:
            a = ep_mean(p200[(p200.policy == policy) & (p200.stream == ds)], cols).sort_values("ep")
            b = ep_mean(p400[(p400.policy == policy) & (p400.stream == ds)], cols).sort_values("ep")
            assert (a.ep.values == b.ep.values).all()
            mats[ds] = (f(b).to_numpy() - f(a).to_numpy())[:, None]
        r = boot(mats)
        for ds in [*DS, "POOLED"]:
            m, lo, hi = r[ds]
            out.append(
                {
                    "policy": policy, "quantity": nm, "dataset": ds, "delta_J": m[0],
                    "lo": lo[0], "hi": hi[0], "pct_Jref": 100 * m[0] / jref[ds],
                    "pct_lo": 100 * lo[0] / jref[ds], "pct_hi": 100 * hi[0] / jref[ds],
                }
            )  # fmt: skip
    return pd.DataFrame(out)


def analyze(a):
    TABLES.mkdir(parents=True, exist_ok=True)
    p1 = load_jsonl(a.p1)
    assert set(p1.stream) == set(DS) and (p1.ep % 2 == 0).all()
    orig = data.load_records()
    summ = {"reproduction": reproduction(p1, orig)}
    rk = ranking(p1, orig)
    rk.to_csv(TABLES / "stage0_ranking_even.csv", index=False)
    ref = rk.policy.iloc[0]
    wald_best = rk[rk.policy.str.startswith("wald_l")].policy.iloc[0]
    summ.update(
        reference_baseline=ref,
        reference_J=float(rk.J_equal_dataset.iloc[0]),
        reference_src=rk.src.iloc[0],
        best_wald=wald_best,
        best_wald_J=float(rk[rk.policy == wald_best].J_equal_dataset.iloc[0]),
        armR_J=float(rk[rk.policy == tr.ARM_R].J_equal_dataset.iloc[0]),
        armR_rank=int(rk.index[rk.policy == tr.ARM_R][0]) + 1,
        n_ranked=len(rk),
    )
    # J_ref per dataset: reference baseline's even-episode mean J (records or rerun)
    src = orig[orig.ep % 2 == 0] if rk.src.iloc[0] == "panel_records" else p1
    e = ep_mean(src[src.policy == ref], ["net"])
    jref = e.groupby("stream").net.mean().to_dict()
    jref["POOLED"] = float(np.mean([jref[d] for d in DS]))
    summ["Jref_per_dataset"] = jref
    pd.DataFrame({"dataset": list(jref), "J_ref": list(jref.values())}).to_csv(
        TABLES / "stage0_jref.csv", index=False
    )
    pols = [p for p in dict.fromkeys([tr.ARM_R, ref, wald_best]) if (p1.policy == p).any()]
    dec = pd.concat([decomposition(p1, p, jref) for p in pols])
    dec.to_csv(TABLES / "stage0_decomposition.csv", index=False)
    summ["traced_policies"] = pols
    cdir = Path(a.ceiling)
    if (cdir / "records.jsonl").exists():
        p400 = load_jsonl(cdir)
        cl = pd.concat([ceiling(p1, p400, p, jref) for p in pols if (p400.policy == p).any()])
        cl.to_csv(TABLES / "stage0_ceiling_b400.csv", index=False)
        summ["ceiling_policies"] = sorted(p400.policy.unique())
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1, default=float))
    shown = {k: v for k, v in summ.items() if k != "Jref_per_dataset"}
    print(json.dumps(shown, indent=1, default=float))


def _f(m, lo, hi, nd=2):
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def markdown_tables(path=None) -> str:
    """Markdown fragments for 11_STAGE0_HEADROOM.md built from the stage0_*.csv tables."""
    dec = pd.read_csv(TABLES / "stage0_decomposition.csv")
    cl = pd.read_csv(TABLES / "stage0_ceiling_b400.csv")
    comps = [*tr.COMPONENTS, "regret"]
    out = []
    for pol in dec.policy.unique():
        for unit, cols in (("mean per episode (loss units)", ("mean", "lo", "hi")),
                           ("% of J_ref", ("pct_Jref", "pct_lo", "pct_hi"))):  # fmt: skip
            out += [f"\n**{pol}: {unit}** (pooled row = equal-dataset mean; brackets = 95% episode-bootstrap CI)\n",
                    "| dataset | " + " | ".join(comps) + " |", "|---|" + "---|" * len(comps)]  # fmt: skip
            for ds in [*DS, "POOLED"]:
                g = dec[(dec.policy == pol) & (dec.dataset == ds)].set_index("component")
                cells = [_f(*g.loc[c, list(cols)]) for c in comps]
                out.append(
                    f"| {'**POOLED**' if ds == 'POOLED' else ds} | " + " | ".join(cells) + " |"
                )
    out += ["\n**Free-label ceiling, B=400 minus B=200 (negative = improvement)**\n",
            "| policy | quantity | dataset | delta J | % of J_ref |", "|---|---|---|---|---|"]  # fmt: skip
    for _, r in cl.iterrows():
        if r.dataset == "POOLED" or r.quantity == "excl_label_fees":
            out.append(f"| {r.policy} | {r.quantity} | {r.dataset} | {_f(r.delta_J, r.lo, r.hi)} | "
                       f"{_f(r.pct_Jref, r.pct_lo, r.pct_hi, 3)} |")  # fmt: skip
    text = "\n".join(out)
    if path:
        Path(path).write_text(text, encoding="utf8")
    return text
