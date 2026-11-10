"""H3 confirmation: atlas pilot (unchanged run_pilot.py) with seed base 5303200000, seeds 0-59, all 32 cells,
then the unchanged analyze_inversions.run() on the registered 12-method set. Resumable (per-cell files).
usage: h3_atlas.py [--workers 8] [--analyze-only]"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "atlas"))
from _common import OUT as COUT
from _common import ROOT, ledger
from analyze_inversions import CORE, run

from shiftlab.paper3.atlas.cells import design
from shiftlab.paper3.atlas.runner import MAIN, REPAIR

OUT = COUT / "h3"
BASE = 5303200000
METHODS = list(dict.fromkeys(MAIN + ["iid_gate"] + REPAIR + ["edetector_cal", "cusum_cal"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    if not a.analyze_only:
        subprocess.run(
            [
                sys.executable,
                "scripts/paper3/atlas/run_pilot.py",
                "--seeds",
                "60",
                "--seed-base",
                str(BASE),
                "--tag",
                "../confirm/h3",
                "--workers",
                str(a.workers),
                "--methods",
                ",".join(METHODS),
            ],
            cwd=ROOT,
            check=True,
        )
    df = pd.concat(
        [pd.read_json(OUT / f"cell_{i:02d}.jsonl", lines=True) for i in range(32)],
        ignore_index=True,
    )
    df = df[df.cell.notna()]
    res = {
        "n_rows": len(df),
        "n_seeds": int(df.seed.nunique()),
        "n_cells": int(df.cell.nunique()),
        "methods": METHODS,
    }
    for label, ms in [("core12", CORE), ("core12+never", CORE + ["never_switch"])]:
        tab, inv, pt, ci = run(df, ms)
        res[label] = {
            "pooled": pt,
            "ci": ci,
            "n_dom_pairs": int(inv.n_dom.sum()),
            "n_inv_pairs": int(inv.n_inv.sum()),
        }
        if label == "core12":
            cs = design()
            dw = pd.DataFrame(
                [
                    {"cell": c.cid, "dwell": min(c.dwell, 2000 - c.onset) / (2000 - c.onset)}
                    for c in cs
                ]
            )
            m = inv.merge(dw, on="cell")
            r1 = spearmanr(m.dwell, m.tau_edd, nan_policy="omit")
            r2 = spearmanr(m.dwell, m.tau_comp, nan_policy="omit")
            res["spearman_dwell_tau_edd"] = [float(r1[0]), float(r1[1])]
            res["spearman_dwell_tau_comp"] = [float(r2[0]), float(r2[1])]
            res["tau_fa_mean"] = float(inv.tau_fa.mean())
            tab.to_csv(OUT / "cell_method_table.csv", index=False)
            inv.to_csv(OUT / "cell_inversions.csv", index=False)
    c = res["core12"]
    res["H3_inv_lo"] = c["ci"]["inv_rate"][0]
    res["H3_tau_hi"] = c["ci"]["tau_edd"][1]
    res["H3_SUPPORTED"] = bool(c["ci"]["inv_rate"][0] > 0.25 and c["ci"]["tau_edd"][1] < 0)
    (OUT / "summary.json").write_text(json.dumps(res, indent=1, default=float))
    ledger(
        "H3",
        "confirm_run",
        {"base": BASE, "seeds": 60, "cells": 32, "n_boot": 300},
        res,
        time.time() - t0,
    )
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
