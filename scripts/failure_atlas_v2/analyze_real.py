"""Registered real-data analysis (protocol Amendment 2): episode-level paired inference only.

    uv run --with tabulate python scripts/failure_atlas_v2/analyze_real.py

Seeds vary only policy randomness, so each episode's seeds are averaged first and the episode is
the resampling unit. Powered set: datasets with >= 8 episodes. Writes docs/failure_atlas_v2/validation_real.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze_atlas_v2 import boot_ci  # noqa: E402

OUT = HERE.parents[1] / "outputs/failure_atlas_v2"
POWERED = ["openml_ldpa", "airlines", "criteo", "rialto", "bank"]
DESCRIPTIVE = ["spam", "uci_occupancy", "weather", "elec2"]
PUB = ["gated_deployment", "gated_adaptive_range", "discern_style", "discern_design_floor",
       "xu_acquisition_only", "SMCS+retain-incumbent"]
UNCERT = ["model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
          "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity"]
PAIRS = [("gated_deployment", "gated_deployment+QCE+front"), ("discern_style", "discern_style+QCE+front"),
         ("SMCS+retain-incumbent", "SMCS+QCE+front"), ("xu_acquisition_only", "xu_acquisition_only+QCE+front"),
         ("gated_adaptive_range", "gated_adaptive_range+front"),
         ("discern_design_floor", "discern_design_floor+front")]


def main():
    d = pd.read_json(OUT / "validation_real/records.jsonl", lines=True)
    u = d.groupby(["regime", "ep", "policy"], as_index=False)[
        ["net", "switches", "labels", "ever_promote"]].mean()
    W = u.pivot_table(index=["regime", "ep"], columns="policy", values="net")
    D = (d.groupby("regime")["ep"].nunique()).to_dict()
    lines = ["# Failure Atlas v2: real-data validation", "",
             "Seed base 2026110398, 10 policy seeds per episode, QSG v1, strong re-ports included. "
             "Episode-level paired bootstrap (seeds averaged within episode). Powered: >= 8 episodes. "
             "The nine cached streams were exposed to earlier ShiftLab work (B3/B3+) but not to the "
             "development of this repair.", "",
             "## Repaired minus host (episode-level)", "",
             "| host -> repaired | " + " | ".join(f"{r} (K={D[r]})" for r in POWERED + DESCRIPTIVE) + " |",
             "|---" * (len(POWERED + DESCRIPTIVE) + 1) + "|"]

    def cell(reg, a, b):
        x = W.loc[reg]
        diff = (x[b] - x[a]).to_numpy()
        lo, hi = boot_ci(diff) if len(diff) > 1 else (np.nan, np.nan)
        star = "*" if hi < 0 else ("!" if lo > 0 else "")
        return f"{diff.mean():+.1f} [{lo:+.1f},{hi:+.1f}]{star}" if len(diff) > 1 else f"{diff.mean():+.1f}"

    for a, b in PAIRS:
        lines.append(f"| {a} -> {b} | " + " | ".join(cell(r, a, b) for r in POWERED + DESCRIPTIVE) + " |")
    lines += ["", "## QSG and best repaired host vs the strongest published certified method", "",
              "Strongest published = lowest mean net among " + ", ".join(PUB) + " on these episodes "
              "(selected on the same data, which favours the comparator).", "",
              "| dataset | K | strongest published | QSG - published | best repaired | repaired - published | "
              "best uncertified | never |", "|---|---|---|---|---|---|---|---|"]
    m = W.groupby(level=0).mean()
    reps = [b for _, b in PAIRS]
    for r in POWERED + DESCRIPTIVE:
        pb = m.loc[r, PUB].idxmin()
        rb = m.loc[r, reps].idxmin()
        ub = m.loc[r, UNCERT].idxmin()
        lines.append(f"| {r} | {D[r]} | {pb} ({m.loc[r, pb]:.1f}) | {cell(r, pb, 'QSG')} | {rb} "
                     f"({m.loc[r, rb]:.1f}) | {cell(r, pb, rb)} | {ub} ({m.loc[r, ub]:.1f}) | "
                     f"{m.loc[r, 'CONTROL_never_switch']:.1f} |")
    lines += ["", "## Mean net cost per dataset (episode-averaged)", "", m.round(1).T.to_markdown()]
    (HERE.parents[1] / "docs/failure_atlas_v2/validation_real.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
