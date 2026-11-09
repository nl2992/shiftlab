"""Stage 3 analysis (odd episodes): fixed rule from 10_JOINTBAYES_PLAN.md Stage 3 / 13_STAGE2_FREEZE.md.

  python stage3_analysis.py
Primary: frozen candidate minus frozen new reference, paired by (dataset, episode), pooled with equal
dataset weights, 95% percentile CI over per-dataset episode bootstraps. Verdict "freeze-to-confirm" iff
dJ < 0 with the CI upper end < 0 AND dL/T <= +0.1 pp (point estimate). Also the dataset-level paired
t-test and sign count. Writes docs/paper1_eqsdp/tables/stage3_*.csv and outputs/.../stage3/summary.json.
"""

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
OUT = ROOT / "outputs/paper1_eqsdp/stage3"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
CAND, ARM, REF0 = "s3_candidate", tr.ARM_R, s1a.REF
DS = s1a.DS


def ds_level_test(e, a, b):
    wa, wb = s1a.wide(e, a), s1a.wide(e, b)
    diffs = np.array([(wa.loc[ds, "net"] - wb.loc[ds, "net"]).mean() for ds in DS])
    t = stats.ttest_1samp(diffs, 0.0)
    return {
        "ds_diffs": dict(zip(DS, map(float, diffs))),
        "t": float(t.statistic), "p_two_sided": float(t.pvalue),
        "p_one_sided_better": float(t.pvalue / 2 if t.statistic < 0 else 1 - t.pvalue / 2),
        "n_better": int((diffs < 0).sum()), "n_worse": int((diffs > 0).sum()),
    }  # fmt: skip


def main():
    fz = json.loads((ROOT / "docs/paper1_eqsdp/stage2_frozen_config.json").read_text())
    ref = fz["new_reference"]
    d = pd.read_json(OUT / "run/records.jsonl", lines=True)
    meta = json.loads((OUT / "run/meta.json").read_text())
    assert meta["split"] == "odd" and d.ep.mod(2).eq(1).all()
    assert d.groupby("policy").size().nunique() == 1, "unequal job counts"
    e = s1a.episode_table(d)
    jref0 = s1a.level(e, REF0, "net")
    rows, tests = [], {}
    for vs, label in [(ref, "new_reference"), (ARM, "arm_R"), (REF0, "wald_l0.97_g0.2")]:
        rows.append({"cand": CAND, "comparator": label, **s1a.pol_row(e, CAND, vs, jref0)})
        tests[label] = ds_level_test(e, CAND, vs)
    for pol, vs in [(ref, REF0), (ARM, REF0), (ref, ARM)]:
        rows.append({"cand": pol, "comparator": vs, **s1a.pol_row(e, pol, vs, jref0)})
    tab = pd.DataFrame(rows)
    tab.to_csv(TABLES / "stage3_comparisons.csv", index=False)
    p = tab.iloc[0]
    freeze_ok = bool(p.dJ < 0 and p.dJ_hi < 0 and p.dLT_pp <= 0.1)
    out = {
        "n_jobs": len(d), "episodes_per_dataset": d.groupby("stream").ep.nunique().to_dict(),
        "J_ref0_odd": jref0, "verdict": "freeze-to-confirm" if freeze_ok else "fail",
        "primary": {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in p.to_dict().items()},
        "dataset_level": tests, "new_reference": ref,
        "J_levels": {x: s1a.level(e, x, "net") for x in (CAND, ref, ARM, REF0)},
    }  # fmt: skip
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    e.to_csv(OUT / "episode_table.csv", index=False)
    print(json.dumps(out, indent=1, default=str))
    cols = ["cand", "comparator", "dJ", "dJ_lo", "dJ_hi", "dJ_pct", "dJ_pct_lo", "dJ_pct_hi",
            "n_ds_better", "n_ds_worse", "dLT_pp", "dLT_pp_lo", "dLT_pp_hi", "J", "labels", "switches"]  # fmt: skip
    print(tab[cols].to_string())


if __name__ == "__main__":
    main()
