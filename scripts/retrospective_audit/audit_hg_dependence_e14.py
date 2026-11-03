"""Trace the reported 23% HG dependence null to the e14 development seeds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "branch-research-shiftlab-mandate-gap-closure-2026-10-30/outputs/gap_closure/e14_fixes_dev2"
)
DEST = ROOT / "docs/retrospective_audit_2026_11_01/HG_E14_DEPENDENCE_AUDIT.json"
HASHES = {
    "perseed.parquet": "07df920437ca3e09aa0d6097fda69038fd37ec5b3f61ad87dfce763033d9cc8b",
    "summary_by_world.csv": "12898403b86030bcd75e14e037ca92c96a00f581430179cda2d8b7d8e6fdebe5",
    "fix_decisions.csv": "0d009deb37b76c66c5a30999f2c2e74fe576baa8116afa0cd06f860e148c8ef0",
}


def run() -> dict[str, object]:
    for name, expected in HASHES.items():
        if hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"e14 hash mismatch {name}")
    frame = pd.read_parquet(SOURCE / "perseed.parquet")
    summary = pd.read_csv(SOURCE / "summary_by_world.csv")
    decisions = pd.read_csv(SOURCE / "fix_decisions.csv")
    if len(frame) != 108000 or frame.duplicated(["world", "config", "seed"]).any():
        raise AssertionError("e14 row/key contract")
    null_worlds = sorted(world for world in frame.world.unique() if "|null|" in world)
    if len(null_worlds) != 7:
        raise AssertionError("e14 null world count")
    parent = frame.loc[(frame.config == "HG|parent") & frame.world.isin(null_worlds)]
    fix = frame.loc[(frame.config == "HG|F2_lrv100") & frame.world.isin(null_worlds)]
    by_parent = parent.groupby("world").false_alarm.agg(["sum", "count", "mean"])
    by_fix = fix.groupby("world").false_alarm.agg(["sum", "count", "mean"])
    if not (by_parent["count"] == 400).all() or not (by_fix["count"] == 400).all():
        raise AssertionError("e14 null stream count")
    if by_parent["mean"].max() != 0.2325 or by_fix["mean"].max() != 0.0475:
        raise AssertionError("e14 maximum null error")
    for config, values in (("HG|parent", by_parent), ("HG|F2_lrv100", by_fix)):
        archived = summary.loc[
            (summary.config == config) & summary.world.isin(null_worlds)
        ].set_index("world")
        if not (archived.fa.loc[values.index].to_numpy() == values["mean"].to_numpy()).all():
            raise AssertionError(f"e14 summary false alarms {config}")
    harm_worlds = sorted(world for world in frame.world.unique() if world.startswith("D2|harm|"))
    if len(harm_worlds) != 4:
        raise AssertionError("e14 original harm world count")
    frame["has_harm"] = frame.first_harm < frame["T"]
    power = frame.loc[
        frame.world.isin(harm_worlds)
        & frame.has_harm
        & frame.config.isin(["HG|parent", "HG|F2_lrv100"])
    ]
    power_means = power.groupby(["world", "config"]).detected.mean().unstack()
    loss = float((power_means["HG|F2_lrv100"] - power_means["HG|parent"]).mean())
    decision = decisions.loc[(decisions.parent == "HG") & (decisions.variant == "F2_lrv100")].iloc[
        0
    ]
    if abs(loss - float(decision.d_power_iid_harm)) > 1e-12:
        raise AssertionError("e14 power-loss mismatch")
    if abs(float(decision.max_fa_dep_parent) - 0.2325) > 1e-12:
        raise AssertionError("e14 parent maximum mismatch")
    if abs(float(decision.max_fa_dep_fix) - 0.0475) > 1e-12:
        raise AssertionError("e14 fix maximum mismatch")
    return {
        "scope": "Archived 400-seed development nulls; no simulator replay or dependence-validity proof",
        "hashes_verified": len(HASHES),
        "rows": len(frame),
        "null_worlds": len(null_worlds),
        "hg_parent_max_null_world": str(by_parent["mean"].idxmax()),
        "hg_parent_max_false_alarms": int(by_parent.loc[by_parent["mean"].idxmax(), "sum"]),
        "hg_parent_max_denominator": 400,
        "hg_parent_max_rate": float(by_parent["mean"].max()),
        "hg_f2_lrv100_max_rate": float(by_fix["mean"].max()),
        "hg_f2_iid_harm_power_change": loss,
        "hg_f2_registered_power_loss_limit": -0.05,
        "hg_f2_meets_power_loss_limit": loss >= -0.05,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["hg_parent_max_rate"], result["hg_f2_iid_harm_power_change"])
