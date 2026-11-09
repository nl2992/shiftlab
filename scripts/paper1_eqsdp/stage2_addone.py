"""Stage 2 supplementary (not selection): add each inactive module back to the final configuration.

  python stage2_addone.py
Even episodes only. Selection is already fixed by stage2_final.py; this only shows whether the
modules the BO left off would have helped (paired dJ = with-module minus final).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage1_analysis as s1a
import stage2_eval as ev
import trace_run as tr

OUT = tr.ROOT / "outputs/paper1_eqsdp/stage2"
TABLES = tr.ROOT / "docs/paper1_eqsdp/tables"


def main():
    s = json.loads((OUT / "final/summary.json").read_text())
    fin = s["cfg_final"]
    cfgs = {
        "s2a_final": fin,
        "s2a_addB1": {**fin, "bw": 1.0},
        "s2a_addB05": {**fin, "bw": 0.5},
        "s2a_addG1": {**fin, "gs": 1.0},
        "s2a_addG15": {**fin, "gs": 1.5},
        "s2a_addStop1300": {**fin, "stop_h": 1300},
        "s2a_addStop1600": {**fin, "stop_h": 1600},
    }
    evl = ev.Evaluator(workers=16)
    d, _, _ = evl.evaluate(cfgs)
    evl.close()
    e = s1a.episode_table(d)
    rows = [
        {"variant": p, **s1a.pol_row(e, p, "s2a_final", s["J_ref0"])}
        for p in cfgs
        if p != "s2a_final"
    ]
    pd.DataFrame(rows).to_csv(TABLES / "stage2_addone.csv", index=False)
    print(
        pd.DataFrame(rows)[["variant", "dJ", "dJ_lo", "dJ_hi", "n_ds_better", "dLT_pp", "d_labels"]]
        .round(3)
        .to_string()
    )


if __name__ == "__main__":
    main()
