"""Shared data for the budget-violation figures: per-regime exceedance (M, order, stress, cols) and real-stream counts (cnt, tot)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from shiftlab.paper3.riskbudget.real_streams import STREAMS
from style import CONFIGS, OUT, PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

conf = load_json(RES / "confirm_summary.json")
c3, c1, c2 = conf["C3"]["arms"], conf["C1"]["arms"], conf["C2"]["arms"]
cols = [("wald_cut", c3, "Wald\ncutoff"), ("cusum", c3, "CUSUM"), ("gate_wald", c3, "e-proc.\ngate"),
        ("cusum_rb_h8", c3, "CUSUM\nrb"), ("stoploss_R20", c3, "stop-\nloss"),
        ("f3f_pi1_R20", None, None), ("f3_pi1_R20", c1, "shield\nfull"), ("f3v2d_R20", c2, "shield\npaced")]
cols = [c for c in cols if c[1] is not None]
stress = [r["id"] for r in load_json(CONFIGS / "regimes_f3_v1.json")["regimes"]]
regs = list(c3["wald_cut"]["per_regime"])
orig = [r for r in regs if r not in stress]
order = orig + stress
M = np.array([[src[a]["per_regime"][g]["rate"] for a, src, _ in cols] for g in order])

# real streams: runs with sup_harm above R=24 (budget arms: above own R = 24 at h=14)
conds = ["clean", "dropout_adverse", "delay_adverse"]
rarms = [("wald_cut", "Wald cutoff", P["red_strong"], "o"), ("cusum_rb_h8", "CUSUM rollback", "#D98880", "D"),
         ("stoploss_h14", "stop-loss", "#E08E45", "v"), ("f3_pi1_h14", "shield (full)", P["blue_main"], "s"),
         ("f3v2d_h14", "shield (paced)", P["teal"], "^")]
cnt = {a: [] for a, *_ in rarms}; tot = []
for c in conds:
    n = {a: 0 for a in cnt}; N = 0
    for f in sorted((OUT / "real" / c).glob("*.json")):
        if f.stem not in STREAMS: continue  # streams dropped for missing provenance
        d = load_json(f); sh = np.array(d["fields"]["sup_harm"], float)
        N += sh[0].size
        for a in cnt:
            n[a] += int((sh[d["arms"].index(a)] > 24).sum())
    for a in cnt: cnt[a].append(n[a])
    tot.append(N)

