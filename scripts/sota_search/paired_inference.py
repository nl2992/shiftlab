"""Goal 3: per-seed rerun of the frozen parent/HG arms (same seeds as the held-out runs) plus paired inference."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

spec = json.loads(Path("configs/sota_search/frozen_finalists_v1.json").read_text())
THR = float(np.log(1 / 0.05))
ARMS = {
    "parent": ("pprm_tight", {}),
    "HG": ("fix_brier", {"gamma": 0.99, "gate_w": 100}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
}
POOLS = {"G1": (h.heldout_pool(), 5000, 5500), "G2": (h.heldout_g2_pool(), 7000, 7500)}
rows = []
for fam, (worlds, sb, lb) in POOLS.items():
    for i, w in enumerate(worlds):
        sim = g.simulate(w, spec["heldout"]["seeds"], sb + i)
        tr = g.truth(w)
        T = w.T
        fh = int(tr["harmful"].argmax()) if tr["harmful"].any() else T
        cum = np.cumsum(np.maximum(tr["harm"], 0.0))
        for frac in spec["fracs"]:
            for arm, (name, extra) in ARMS.items():
                p = {"frac": frac, "delay": spec["delay"], "tol": spec["tol"], **extra}
                stat = det.DETECTORS[name](sim, lseed=lb + i, **p)
                labels = sim.pop("_labels", None)
                al = det.first_cross(np.where(np.isfinite(stat), stat, -np.inf), THR)
                n = len(al)
                lab = (
                    labels[np.arange(n), np.minimum(al, T - 1)]
                    if labels is not None
                    else frac * np.minimum(al, T)
                )
                for s in range(n):
                    rows.append(
                        {
                            "family": fam,
                            "world": f"{w.kind}/{w.shape}/{w.delta:g}",
                            "role": h.role(w),
                            "frac": frac,
                            "arm": arm,
                            "seed": s,
                            "alarm": int(al[s]),
                            "fired": bool(al[s] < T),
                            "detected": bool(al[s] < T and al[s] >= fh and tr["harmful"].any()),
                            "false_alarm": bool(al[s] < fh),
                            "harm_before": float(cum[min(al[s], T - 1)]),
                            "labels": float(lab[s]),
                        }
                    )
        print(fam, i, flush=True)
df = pd.DataFrame(rows)
Path("outputs/hg_validation").mkdir(parents=True, exist_ok=True)
df.to_parquet("outputs/hg_validation/03_PER_SEED_RESULTS.parquet")
w = (
    df.groupby(["family", "frac", "arm", "world", "role"])[
        ["detected", "false_alarm", "harm_before", "labels"]
    ]
    .mean()
    .reset_index()
)
w.to_csv("outputs/hg_validation/03_PER_WORLD_RESULTS.csv", index=False)
print("saved", len(df))
