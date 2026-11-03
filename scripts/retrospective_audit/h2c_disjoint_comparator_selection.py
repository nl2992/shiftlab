"""Describe H2c comparator choice on disjoint halves of exposed G5 seeds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs" / "h2c_next" / "g5_confirmation_per_seed.parquet"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "H2C_DISJOINT_SELECTION.json"
ARMS = ("F1_H2c", "C1_cost_disc", "C2_cost_ONS")


def run() -> dict[str, object]:
    frame = pd.read_parquet(SOURCE)
    harm = frame[frame.role == "harm"]
    results = []
    for frac in (0.1, 0.2):
        effects = []
        for (cond, shift), group in harm[harm.frac == frac].groupby(["cond", "shift"]):
            panel = group[group.arm.isin(ARMS)].pivot(
                index="seed", columns="arm", values="detected"
            )
            if panel.shape != (600, 3) or panel.isna().any().any():
                raise AssertionError(f"Incomplete H2c cell: {cond}/{shift}/{frac}")
            if not np.array_equal(panel.index.to_numpy(), np.arange(600)):
                raise AssertionError("Unexpected seed keys")
            full = max(ARMS[1:], key=lambda arm: panel[arm].mean())
            held_out = np.empty(600, dtype=float)
            choices = []
            for train, test in ((slice(0, 300), slice(300, 600)), (slice(300, 600), slice(0, 300))):
                selected = max(ARMS[1:], key=lambda arm: panel[arm].iloc[train].mean())
                choices.append(selected)
                held_out[test] = panel["F1_H2c"].iloc[test].astype(float) - panel[selected].iloc[
                    test
                ].astype(float)
            original = (panel["F1_H2c"].astype(float) - panel[full].astype(float)).mean()
            effects.append((float(original), float(held_out.mean())))
            results.append(
                {
                    "frac": frac,
                    "cond": cond,
                    "shift": shift,
                    "full_selected": full,
                    "first_half_selected": choices[0],
                    "second_half_selected": choices[1],
                    "full_selected_effect": float(original),
                    "disjoint_selection_effect": float(held_out.mean()),
                }
            )
        print(
            frac,
            "full-selected",
            float(np.mean([e[0] for e in effects])),
            "disjoint-selection",
            float(np.mean([e[1] for e in effects])),
        )
    return {
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "scope": "Post hoc disjoint-half diagnostic on exposed G5 seeds; not independent confirmation",
        "cells": results,
    }


if __name__ == "__main__":
    DEST.write_text(json.dumps(run(), indent=2) + "\n", encoding="utf-8")
