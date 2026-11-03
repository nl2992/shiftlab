"""Recompute HG e15 comparison means and comparator information parity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "branch-research-shiftlab-mandate-gap-closure-2026-10-30/outputs/gap_closure/e15_confirm"
)
DEST = ROOT / "docs/retrospective_audit_2026_11_01/HG_E15_ARCHIVE_AUDIT.json"
HASHES = {
    "perseed.parquet": "9741a566f427cadd4c7a44826460e78c6df803e731f7fa44b252265d6f9f0eaa",
    "comparisons.csv": "cf0ffa794ad9945b81776c2ae88b50aa55c424a4efd315ffb32dd8205eddd556",
    "arm_summary.csv": "8c9a84405fd09a7c2981619bbf8c838bf9100990aa9778ff4aee176a69a7afdd",
}


def run() -> dict[str, object]:
    for name, expected in HASHES.items():
        actual = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"e15 source hash mismatch: {name}")
    frame = pd.read_parquet(SOURCE / "perseed.parquet")
    comparisons = pd.read_csv(SOURCE / "comparisons.csv")
    summary = pd.read_csv(SOURCE / "arm_summary.csv").set_index("config")
    if len(frame) != 168000 or frame.duplicated(["world", "config", "seed"]).any():
        raise AssertionError("e15 panel completeness/uniqueness")
    frame["has_harm"] = frame.first_harm < frame["T"]
    world_rate = frame.groupby("world").has_harm.mean()
    harm_worlds = list(world_rate[world_rate > 0.5].index)
    null_worlds = list(world_rate[world_rate <= 0.5].index)
    if len(harm_worlds) != 15 or len(null_worlds) != 6 or frame.config.nunique() != 14:
        raise AssertionError("e15 world/arm count")
    if len(comparisons) != 30:
        raise AssertionError("e15 comparison family count")
    max_error = 0.0
    for record in comparisons.itertuples(index=False):
        a, b, metric = record[0], record[1], record[2]
        worlds = harm_worlds if metric == "power" else harm_worlds + null_worlds
        differences = []
        for world in worlds:
            left = frame.loc[(frame.world == world) & (frame.config == a)].set_index("seed")
            right = frame.loc[(frame.world == world) & (frame.config == b)].set_index("seed")
            if len(left) != len(right) or set(left.index) != set(right.index):
                raise AssertionError(f"unpaired e15 seeds {a}/{b}/{world}")
            right = right.loc[left.index]
            if metric == "power":
                selected = left.has_harm
                diff = left.loc[selected, "detected"].astype(float) - right.loc[
                    selected, "detected"
                ].astype(float)
            elif metric == "fa":
                diff = left.false_alarm.astype(float) - right.false_alarm.astype(float)
            elif metric == "harm_before":
                diff = left.harm_before - right.harm_before
            else:
                raise AssertionError("unexpected e15 metric")
            differences.append(float(diff.mean()))
        value = float(np.mean(differences))
        error = abs(value - float(record[3]))
        max_error = max(max_error, error)
        if error > 1e-12:
            raise AssertionError(f"e15 comparison mean mismatch {a}/{b}/{metric}")
    harm = frame.loc[frame.world.isin(harm_worlds)]
    null = frame.loc[frame.world.isin(null_worlds)]
    parity = {}
    effects = {}
    for fraction in ("0.1", "0.2"):
        names = [f"{arm}@{fraction}" for arm in ("HG", "pprm", "ph", "cusum")]
        wide = frame.loc[frame.config.isin(names)].pivot(
            index=["world", "seed"], columns="config", values="labels"
        )
        parity[fraction] = all((wide[names[0]] == wide[name]).all() for name in names[1:])
        if not parity[fraction]:
            raise AssertionError(f"same-fraction pathwise label mismatch {fraction}")
        hg = harm.loc[harm.config == names[0]]
        pprm = harm.loc[harm.config == names[1]]
        ph = harm.loc[harm.config == names[2]]
        relative_harm = float(hg.harm_before.mean() / pprm.harm_before.mean() - 1)
        effects[fraction] = {
            "hg_power": float(hg.detected.mean()),
            "pprm_power": float(pprm.detected.mean()),
            "ph_power": float(ph.detected.mean()),
            "hg_minus_pprm_power": float(hg.detected.mean() - pprm.detected.mean()),
            "hg_minus_ph_power": float(hg.detected.mean() - ph.detected.mean()),
            "hg_relative_harm_before_vs_pprm": relative_harm,
            "hg_null_fa_max": float(
                null.loc[null.config == names[0]].groupby("world").false_alarm.mean().max()
            ),
        }
        for name, field, value in (
            (names[0], "power (harm worlds, mean)", effects[fraction]["hg_power"]),
            (names[0], "harm before alarm", float(hg.harm_before.mean())),
            (names[0], "FA (null worlds, max)", effects[fraction]["hg_null_fa_max"]),
        ):
            if abs(float(summary.loc[name, field]) - value) > 1e-12:
                raise AssertionError(f"e15 arm summary mismatch {name}/{field}")
    return {
        "scope": "Archived e15 paired point estimates and label parity; bootstrap intervals and simulator not rerun",
        "hashes_verified": len(HASHES),
        "rows": len(frame),
        "harm_worlds": len(harm_worlds),
        "null_worlds": len(null_worlds),
        "comparison_point_rows_checked": len(comparisons),
        "max_point_error": max_error,
        "same_fraction_pathwise_label_parity": parity,
        "effects": effects,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["rows"], result["comparison_point_rows_checked"], result["max_point_error"])
