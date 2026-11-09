"""CPU smoke: the paper ports and their matched-cutoff versions on a few registered sf_311 episodes.

Plumbing check only (descriptive, 3 episodes x 2 seeds on a development-exposed registered window).
Usage: python smoke_sf311.py [--eps 0 2 4] [--seeds 0 1]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/paper1_eqsdp"))
import numpy as np
import paper_ports as pp
import trace_run as tr

_orig = tr.registry
tr.registry = lambda: {**_orig(), **pp.registry_entries(1100)}

NAMES = [
    "model_picker_adapter",
    "cams_adapter",
    "wald_l0.98_g0.3",
    "EQSDp_l0.98_g0.3",
    "mp_paper_recommend",
    "mp_paper_sample",
    "cams_paper",
    "cams_paper_gated",
    "mp_paper_recommend_H1100",
    "mp_paper_sample_H1100",
    "cams_paper_H1100",
    "cams_paper_gated_H1100",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=int, nargs="+", default=[0, 2, 4])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    a = ap.parse_args()
    path, delay, sb = tr.sealed_paths()["sf_311"]
    z = np.load(path)
    rows = []
    for ep in a.eps:
        losses = np.stack([z["l0"][ep], z["l1"][ep]], 1).astype(np.int8)
        for seed in a.seeds:
            rows += tr.run_policies(NAMES, losses, delay, ep, seed, sb, "sf_311", 200)
    d = pd.DataFrame(rows)
    out = d.groupby("policy")[["net", "loss", "labels", "switches", "secs"]].mean().loc[NAMES]
    pd.set_option("display.width", 200)
    print(out.round(2))
    d.to_csv(HERE / "smoke_sf311_results.csv", index=False)


if __name__ == "__main__":
    main()
