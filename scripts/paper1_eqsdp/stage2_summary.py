"""Stage 2 descriptive numbers for docs/paper1_eqsdp/13_STAGE2_FREEZE.md (reads stage2_final outputs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage1_analysis as s1a
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage2"
TABLES = ROOT / "docs/paper1_eqsdp/tables"


def main():
    s = json.loads((OUT / "final/summary.json").read_text())
    bo = pd.read_csv(TABLES / "stage2_bo_evals.csv")
    f = bo[bo.feasible]
    d = pd.read_csv(OUT / "final/rows_even.csv.gz")
    e = s1a.episode_table(d)
    ref = s["new_reference"]
    per_ds, tt = {}, {}
    for vs in (ref, tr.ARM_R, s1a.REF):
        wa, wb = s1a.wide(e, s["final_name"]), s1a.wide(e, vs)
        diffs = np.array([(wa.loc[ds, "net"] - wb.loc[ds, "net"]).mean() for ds in s1a.DS])
        per_ds[vs] = dict(zip(s1a.DS, map(float, diffs)))
        t = stats.ttest_1samp(diffs, 0.0)
        tt[vs] = {"t": float(t.statistic), "p_two_sided": float(t.pvalue),
                  "n_better": int((diffs < 0).sum()), "n_worse": int((diffs > 0).sum())}  # fmt: skip
    out = {
        "n_evals": len(bo), "n_feasible": len(f), "n_infeasible": int(len(bo) - len(f)),
        "sobol_best_feasible_J": float(f[f.kind == "sobol"].J.min()),
        "bo_best_feasible_J": float(f[f.kind == "bo"].J.min()),
        "feasible_dJ_vs_newref_quantiles": {
            str(q): float(f.dJ_vs_newref.quantile(q)) for q in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)},
        "n_feasible_beating_newref": int((f.dJ_vs_newref < 0).sum()),
        "top5_feasible_mean_dJ": float(f.sort_values("J").head(5).dJ_vs_newref.mean()),
        "total_eval_secs": float(bo.eval_secs.sum()), "mean_eval_secs": float(bo.eval_secs.mean()),
        "per_dataset_dJ_final_minus": per_ds, "dataset_level_ttest_even": tt,
        "bo_best_mean_secs_per_run": float(d[d.policy == "s2f_full"].secs.mean()),
        "final_mean_secs_per_run": float(d[d.policy == "s2f_final"].secs.mean()),
        "newref_mean_secs_per_run": float(d[d.policy == ref].secs.mean()),
        "armR_mean_secs_per_run": float(d[d.policy == tr.ARM_R].secs.mean()),
    }  # fmt: skip
    (OUT / "final/summary_extra.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
