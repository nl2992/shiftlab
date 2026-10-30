"""Reproduce a declared historical G5 cell against preserved per-path results."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    output = DOC / "historical_h2c_anchor_reproduction.json"
    if output.exists():
        raise FileExistsError("anchor already reproduced; retain existing record")
    original = ROOT / "outputs/h2c_next/g5_confirmation_per_seed.parquet"
    cond, shift, N = "accurate", "concept2", 600
    cellindex = list(g.G5_CONDITIONS).index(cond) * len(g.G5_SHIFTS) + list(g.G5_SHIFTS).index(
        shift
    )
    registration = {
        "kind": "historical reproduction, not fresh confirmation",
        "condition": cond,
        "shift": shift,
        "N": N,
        "world_seed": 90000 + cellindex,
        "query_seed": 95000 + cellindex + 1,
        "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "arms": ["F1_H2c", "C1_cost_disc", "C2_cost_ONS"],
    }
    (DOC / "historical_h2c_anchor_registration.json").write_text(
        json.dumps(registration, indent=2), encoding="utf-8"
    )
    historical = pd.read_parquet(original)
    sim = g.simulate_g5(cond, shift, N, registration["world_seed"])
    results = []
    arms = {
        "F1_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
        "C1_cost_disc": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
        "C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    }
    for frac in (0.1, 0.2):
        for name, (fn, kw) in arms.items():
            al = det.first_cross(
                det.DETECTORS[fn](
                    sim, frac=frac, delay=5, lseed=registration["query_seed"], tol=0, **kw
                ),
                np.log(20),
            )
            detected = (al < 2000) & (al >= 700)
            false = al < 700
            old = historical[
                (historical.cond == cond)
                & (historical["shift"] == shift)
                & (historical.frac == frac)
                & (historical.arm == name)
            ].sort_values("seed")
            assert len(old) == N
            assert np.array_equal(detected, old.detected.to_numpy())
            assert np.array_equal(false, old.false_alarm.to_numpy())
            results.append(
                {
                    "arm": name,
                    "frac": frac,
                    "power": float(detected.mean()),
                    "false_alarm": float(false.mean()),
                    "per_path_equal": True,
                }
            )
            print(name, frac, "all 600 paths match", flush=True)
    output.write_text(
        json.dumps({"status": "pass", "registration": registration, "results": results}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
