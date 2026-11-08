"""Select and freeze Gap-Mix+ (Arm 4) and fixed-pacing (Arm 5) configs from tuning rows only."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts" / "methods_recovery")]
from run_gmplus import ARM4_GRID, ARM5_GRID, FROZEN

rows = pd.read_csv(ROOT / "outputs/methods_recovery/tune/rows.csv")
rows["fam"] = rows.cell.map(
    lambda c: (
        "b" + re.search(r"_b([\d.]+)_", c).group(1) + "_d" + re.search(r"_d(\d+)_", c).group(1)
    )
)
n_cells, n_seeds = rows.cell.nunique(), rows.groupby("cell").seed.nunique().min()
cm = rows.groupby(["arm", "fam", "cell"]).cost.mean().reset_index()  # per-cell means
dss = cm[cm.arm == "gaver:gapmix:dss"].cost.mean()

a4 = {k: cm[cm.arm == f"gmp:gapmix:plus:{k}"].cost.mean() for k in ARM4_GRID}
best4 = min(a4, key=a4.get)
a5 = {}
best5 = {}
for fam in sorted(cm.fam.unique()):
    sub = cm[cm.fam == fam]
    a5[fam] = {k: sub[sub.arm == f"gmp:gapmix:pace:{k}"].cost.mean() for k in ARM5_GRID}
    best5[fam] = min(a5[fam], key=a5[fam].get)
pooled5 = {k: cm[cm.arm == f"gmp:gapmix:pace:{k}"].cost.mean() for k in ARM5_GRID}

cfg = {
    "arm4": best4,
    "arm5": best5,
    "note": "chosen on tuning seeds 101300000-101309999 only; Arm 4 global (equal-weight cell mean J/T); Arm 5 per (B/T,d) family",
}
FROZEN.parent.mkdir(parents=True, exist_ok=True)
FROZEN.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
sha = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
(FROZEN.with_suffix(".json.sha256")).write_text(f"{sha}  {FROZEN.name}\n", encoding="utf-8")

L = ["# Gap-Mix+ tuning (tuning seeds only)", ""]
L += [
    f"Seeds: gapmix_plus_tuning 101300000-101309999; {n_cells} target-family cells x {n_seeds} seeds (seed = 101300000 + 100*cell_index + k).",
    "Metric: equal-weight mean over cells of mean J/T (lower is better). No eval seed has been run.",
    "",
    "Design note (recorded for honesty): the Arm 4 grid was shifted once, before the real tuning run, after an",
    "8-cell x 1-seed smoke on tuning seeds showed the best configs at the old grid edge (kappa=2, phi=1.5):",
    "old grid kappa{0.5,1,2} x phi{0.75,1,1.5} x omega{0,.5,1}; used grid kappa{1,2,4} x phi{1,1.5,2.5} x omega{0,.5,1}.",
    "Both grids have 27 configs (<= 30).",
    "",
    f"Reference on tuning seeds: Gap-Mix with existing acquisition (Arm 2) mean J/T = {dss:.4f}.",
    "",
    f"## Arm 4 (Gap-Mix+, 3 parameters, {len(ARM4_GRID)} configs)",
    "",
    "| config (kappa_phi_omega) | mean J/T |",
    "|---|---|",
]
for k in sorted(a4, key=a4.get):
    L.append(f"| {k}{' **(chosen)**' if k == best4 else ''} | {a4[k]:.4f} |")
L += [
    "",
    f"## Arm 5 (fixed pacing, {len(ARM5_GRID)} configs per family, >= Arm 4's {len(ARM4_GRID)})",
    "",
]
L += ["Pooled over all families (information only):", "", "| config | mean J/T |", "|---|---|"]
for k in sorted(pooled5, key=pooled5.get)[:10]:
    L.append(f"| {k} | {pooled5[k]:.4f} |")
L += [
    "",
    "Chosen per (B/T, d) family:",
    "",
    "| family | chosen | best J/T | 2nd best |",
    "|---|---|---|---|",
]
for fam, d in a5.items():
    o = sorted(d, key=d.get)
    L.append(f"| {fam} | {o[0]} | {d[o[0]]:.4f} | {o[1]} ({d[o[1]]:.4f}) |")
L += [
    "",
    "## Frozen config",
    "",
    f"`configs/methods_recovery/gapmix_plus_frozen.json`, sha256 `{sha}`.",
    "",
    "```json",
    json.dumps(cfg, indent=2, sort_keys=True),
    "```",
    "",
    f"Arm 4 chosen: `{best4}` (kappa, phi, omega) = {best4}. Ablation 4a and the Markov-LR hybrid use the same parameters.",
]
(ROOT / "docs/methods_recovery/10_TUNING.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(best4, best5, sha)
