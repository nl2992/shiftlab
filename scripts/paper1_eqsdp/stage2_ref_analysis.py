"""Stage 2 step 1 analysis: pick the fair re-tuned reference on even episodes.

  python stage2_ref_analysis.py
New reference = lowest equal-dataset mean J subject to dL/T <= +0.1 pp versus ``wald_l0.97_g0.2``
(paired, equal-dataset mean of per-dataset episode-mean loss differences). Also reports the
unconstrained best. Writes docs/paper1_eqsdp/tables/stage2_ref_grid.csv and
outputs/paper1_eqsdp/stage2/ref_summary.json (+ ref_episode.csv, per-episode seed means of the
reference policies, used as the paired baseline by the BO).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_analysis as s0a
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
REF0 = "wald_l0.97_g0.2"
T = 2000
DS = list(tr.NINE)
COLS = ["net", "loss", "labels", "switches"]
LIM_PP = 0.1


def load_all() -> pd.DataFrame:
    parts = [pd.read_json(OUT / "stage0/p1/records.jsonl", lines=True)]
    for sub in ("ref_grid", "ref_thin"):
        p = OUT / "stage2" / sub / "records.jsonl"
        if p.exists():
            parts.append(pd.read_json(p, lines=True))
    d = pd.concat(parts, ignore_index=True)
    keep = d.policy.isin(
        [tr.ARM_R, *tr.WALD_GRID] + [x for x in d.policy.unique() if x.startswith("s2")]
    )
    return d[keep]


def episode_cols(d: pd.DataFrame) -> pd.DataFrame:
    return d.groupby(["stream", "ep", "policy"])[COLS].mean().reset_index()


def per_ep(e: pd.DataFrame, pol: str) -> dict:
    w = e[e.policy == pol].set_index(["stream", "ep"]).sort_index()
    return {ds: w.loc[ds, COLS].values.astype(float) for ds in DS}


def pooled_level(e, pol):
    x = per_ep(e, pol)
    return np.mean([x[ds].mean(0) for ds in DS], axis=0)  # net, loss, labels, switches


def paired(e, a, b, ci=False):
    xa, xb = per_ep(e, a), per_ep(e, b)
    diff = {ds: xa[ds] - xb[ds] for ds in DS}
    if ci:
        r = s0a.boot(diff)
        return r
    return np.mean([diff[ds].mean(0) for ds in DS], axis=0)


def main():
    d = load_all()
    e = episode_cols(d)
    jref = pooled_level(e, REF0)[0]
    rows = []
    for pol in sorted(e.policy.unique()):
        lv = pooled_level(e, pol)
        dd = paired(e, pol, REF0)
        rows.append(
            {
                "policy": pol,
                "J": lv[0],
                "loss_per_T_pp": 100 * lv[1] / T,
                "labels": lv[2],
                "switches": lv[3],
                "dJ_vs_ref": dd[0],
                "dJ_pct": 100 * dd[0] / jref,
                "dL_pp": 100 * dd[1] / T,
                "feasible": bool(100 * dd[1] / T <= LIM_PP + 1e-12),
            }
        )
    tab = pd.DataFrame(rows).sort_values("J").reset_index(drop=True)
    feas = tab[tab.feasible]
    new_ref = feas.iloc[0].policy
    best_unc = tab.iloc[0].policy
    tab.to_csv(TABLES / "stage2_ref_grid.csv", index=False)
    cis = {}
    for pol in dict.fromkeys([new_ref, best_unc, tr.ARM_R]):
        r = paired(e, pol, REF0, ci=True)["POOLED"]
        cis[pol] = {
            "dJ": float(r[0][0]), "dJ_lo": float(r[1][0]), "dJ_hi": float(r[2][0]),
            "dL_pp": float(100 * r[0][1] / T), "dL_pp_lo": float(100 * r[1][1] / T),
            "dL_pp_hi": float(100 * r[2][1] / T),
            "ds_better": int(sum(paired_ds(e, pol, REF0, ds) < 0 for ds in DS)),
        }  # fmt: skip
    summ = {
        "J_ref0": float(jref),
        "new_reference": new_ref,
        "new_reference_row": tab[tab.policy == new_ref].iloc[0].to_dict(),
        "unconstrained_best": best_unc,
        "unconstrained_best_row": tab[tab.policy == best_unc].iloc[0].to_dict(),
        "ci_vs_ref0": cis,
        "n_policies": len(tab),
        "n_feasible": len(feas),
        "armR_row": tab[tab.policy == tr.ARM_R].iloc[0].to_dict(),
    }
    (OUT / "stage2/ref_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    keepp = [REF0, tr.ARM_R, new_ref, best_unc]
    e[e.policy.isin(keepp)].to_csv(OUT / "stage2/ref_episode.csv", index=False)
    print(tab.head(15).to_string())
    print(json.dumps(summ, indent=1, default=str))


def paired_ds(e, a, b, ds):
    return (per_ep(e, a)[ds] - per_ep(e, b)[ds]).mean(0)[0]


if __name__ == "__main__":
    main()
