"""Amendment A1: select Arm-5 fixed pacing for neighbour families from tune_nb rows (tuning seeds only).

Same rule as tune_select.py: per (B/T, d) family, the grid config with the lowest equal-weight
mean over cells of mean J/T. Writes configs/methods_recovery/gapmix_plus_frozen_nb.json (+ sha256).
The original frozen config and its hash are not modified.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts" / "methods_recovery")]
from run_gmplus import ARM5_GRID, FROZEN_NB

rows = pd.read_csv(ROOT / "outputs/methods_recovery/tune_nb/rows.csv")
rows["fam"] = rows.cell.map(
    lambda c: (
        "b" + re.search(r"_b([\d.]+)_", c).group(1) + "_d" + re.search(r"_d(\d+)_", c).group(1)
    )
)
cm = rows.groupby(["arm", "fam", "cell"]).cost.mean().reset_index()
best = {}
for fam in sorted(cm.fam.unique()):
    sub = cm[cm.fam == fam]
    sc = {k: sub[sub.arm == f"gmp:gapmix:pace:{k}"].cost.mean() for k in ARM5_GRID}
    best[fam] = min(sc, key=sc.get)
    print(fam, best[fam], round(sc[best[fam]], 4))
cfg = {
    "arm5": best,
    "note": "Amendment A1: neighbour families, tuning seeds 101306000-101309999 only",
}
FROZEN_NB.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
sha = hashlib.sha256(FROZEN_NB.read_bytes()).hexdigest()
FROZEN_NB.with_suffix(".json.sha256").write_text(f"{sha}  {FROZEN_NB.name}\n", encoding="utf-8")
print("sha256", sha)
