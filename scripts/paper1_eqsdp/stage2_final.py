"""Stage 2 closing analysis: BO best feasible config, module ablations, selection rule, comparisons.

  python stage2_final.py
Selection rule (fixed before the BO ran, in the task brief): the final candidate is the BO best
feasible configuration with every active module whose single ablation does not hurt (paired
dJ = ablated - full has a 95% CI that includes 0 or lies below 0) removed. Simpler wins.
Outputs: docs/paper1_eqsdp/tables/stage2_{bo_evals,pareto,ablation,final_vs}.csv,
outputs/paper1_eqsdp/stage2/final/{summary.json,rows_even.csv.gz}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage1_analysis as s1a
import stage2_eval as ev
import stage2_space as sps
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage2"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
REF0, ARM = s1a.REF, tr.ARM_R
T = 2000
ACTIVE = {
    "B": lambda c: c["bw"] > 0 and c["rho0"] > 0,
    "G": lambda c: c["gs"] > 0,
    "stop": lambda c: c["stop_h"] is not None,
    "gate": lambda c: c["rho0"] > 0,
}


def bo_table() -> pd.DataFrame:
    rows = [json.loads(x) for x in (OUT / "bo/evals.jsonl").read_text().splitlines() if x.strip()]
    recs = []
    for r in rows:
        c = r["cfg"]
        src = r.get("dup_of", r["i"])
        e = pd.read_csv(OUT / f"bo/evals/eval_{src:03d}.csv.gz")
        recs.append(
            {"i": r["i"], "kind": r["kind"], **c, "J": r["J"], "dJ_vs_newref": r["dJ"],
             "dL_pp_vs_newref": r["dL_pp"], "LT_pp": 100 * ev.pooled(e, "loss") / T,
             "labels": r["labels"], "switches": r["switches"], "feasible": r["feasible"],
             "eval_secs": r["eval_secs"], "dup_of": r.get("dup_of")}
        )  # fmt: skip
    return pd.DataFrame(recs)


def pareto(df: pd.DataFrame) -> pd.Series:
    flag = []
    for _, a in df.iterrows():
        dom = ((df.J <= a.J) & (df.LT_pp <= a.LT_pp) & ((df.J < a.J) | (df.LT_pp < a.LT_pp))).any()
        flag.append(not dom)
    return pd.Series(flag, index=df.index)


def main():
    (OUT / "final").mkdir(exist_ok=True)
    summ = json.loads((OUT / "ref_summary.json").read_text())
    new_ref = summ["new_reference"]
    jref0 = summ["J_ref0"]
    bo = bo_table()
    bo["pareto_all"] = pareto(bo)
    bo["pareto_feasible"] = False
    f = bo[bo.feasible]
    bo.loc[f.index, "pareto_feasible"] = pareto(f).values
    bo.to_csv(TABLES / "stage2_bo_evals.csv", index=False)
    # joint frontier with the step-1 reference grid
    g = pd.read_csv(TABLES / "stage2_ref_grid.csv")
    jt = pd.concat(
        [
            bo[["i", "J", "LT_pp", "feasible"]].assign(source="bo", name=bo.i.map(lambda i: f"s2bo_{i:03d}")),
            g.rename(columns={"loss_per_T_pp": "LT_pp", "policy": "name"})[["name", "J", "LT_pp", "feasible"]].assign(source="ref_grid"),
        ],
        ignore_index=True,
    )  # fmt: skip
    jt["pareto"] = pareto(jt).values
    jt.to_csv(TABLES / "stage2_pareto.csv", index=False)

    best = bo[bo.feasible].sort_values("J").iloc[0]
    cfg_best = {
        k: best[k] for k in ("lam", "gamma", "rho0", "s", "h", "floor", "stop_h", "bw", "gs")
    }
    cfg_best["h"] = int(cfg_best["h"])
    cfg_best["stop_h"] = None if pd.isna(cfg_best["stop_h"]) else int(cfg_best["stop_h"])
    cfg_best = {
        k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in cfg_best.items()
    }
    cfgs = {"s2f_full": cfg_best}
    for m, act in ACTIVE.items():
        if act(cfg_best):
            cfgs[f"s2f_no{m}"] = sps.ablate(cfg_best, m)
    named = [new_ref, ARM, REF0]
    evl = ev.Evaluator(workers=16)
    d, _, secs = evl.evaluate(cfgs, named=named)
    e = s1a.episode_table(d)
    ab = []
    removable = []
    for m in ACTIVE:
        nm = f"s2f_no{m}"
        if nm not in cfgs:
            ab.append({"module": m, "active_in_best": False})
            continue
        r = s1a.pol_row(e, nm, "s2f_full", jref0)
        hurts = r["dJ_lo"] > 0  # removal hurts only if the paired CI is entirely above 0
        if not hurts:
            removable.append(m)
        ab.append({"module": m, "active_in_best": True, "removal_hurts": bool(hurts), **r})
    pd.DataFrame(ab).to_csv(TABLES / "stage2_ablation.csv", index=False)
    final_cfg = dict(cfg_best)
    for m in removable:
        final_cfg = sps.ablate(final_cfg, m)
    # B is meaningful only with the gate; keep configuration literal otherwise
    rows = d
    if final_cfg != cfg_best:
        d2, _, _ = evl.evaluate({"s2f_final": final_cfg})
        rows = pd.concat([d, d2[d2.policy == "s2f_final"]], ignore_index=True)
        final_name = "s2f_final"
    else:
        final_name = "s2f_full"
    evl.close()
    e = s1a.episode_table(rows)
    comps = []
    for vs, label in [(new_ref, "new_reference"), (ARM, "arm_R"), (REF0, "wald_l0.97_g0.2")]:
        comps.append(
            {"cand": final_name, "comparator": label, **s1a.pol_row(e, final_name, vs, jref0)}
        )
        if final_name != "s2f_full":
            comps.append(
                {"cand": "s2f_full", "comparator": label, **s1a.pol_row(e, "s2f_full", vs, jref0)}
            )
    for pol in (new_ref, ARM):
        comps.append(
            {"cand": pol, "comparator": "wald_l0.97_g0.2", **s1a.pol_row(e, pol, REF0, jref0)}
        )
    pd.DataFrame(comps).to_csv(TABLES / "stage2_final_vs.csv", index=False)
    rows.to_csv(OUT / "final/rows_even.csv.gz", index=False)
    out = {
        "best_feasible_i": int(best.i), "cfg_best": cfg_best, "removable": removable,
        "final_name": final_name, "cfg_final": final_cfg, "new_reference": new_ref,
        "J_ref0": jref0, "n_evals": len(bo), "n_feasible": int(bo.feasible.sum()),
        "n_pareto_feasible": int(bo.pareto_feasible.sum()), "final_eval_secs": secs,
    }  # fmt: skip
    (OUT / "final/summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    cols = [
        "cand",
        "comparator",
        "dJ",
        "dJ_lo",
        "dJ_hi",
        "dJ_pct",
        "n_ds_better",
        "dLT_pp",
        "J",
        "labels",
        "switches",
    ]
    print(pd.DataFrame(comps)[cols].to_string())
    print(pd.DataFrame(ab).to_string())


if __name__ == "__main__":
    main()
