"""Check exact A2 screen gaps and A3c reported rational mixture bounds."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/promising_directions/results"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/A2_A3C_ARCHIVE_CHECK.json"


def run() -> dict[str, object]:
    a2 = BASE / "a2"
    a3c = BASE / "a3c"
    a2_summary = json.loads((a2 / "summary.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line) for line in (a2 / "screen.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    if len(rows) != 162 or a2_summary["screen_cells_completed"] != 162:
        raise AssertionError("A2 screen cell count")
    if a2_summary["screen_cells_failed"] != 0 or a2_summary["survivors"]:
        raise AssertionError("A2 screen completion/survivors")
    keys: set[tuple[str, str]] = set()
    tight = 0
    unconstrained_positive = 0
    for row in rows:
        if row["status"] != "completed":
            raise AssertionError("A2 incomplete row")
        p = row["params"]
        family = "|".join(f"{k}={p[k]}" for k in ("e1", "trans", "prior1", "cs"))
        alpha = p["alpha"]
        key = (family, alpha)
        if key in keys:
            raise AssertionError("A2 duplicate family/alpha")
        keys.add(key)
        joint, calendar = Fraction(row["J"]), Fraction(row["C_star"])
        if joint <= 0 or calendar < joint:
            raise AssertionError("A2 optimization order")
        gap = (calendar - joint) / joint
        if abs(float(gap) - float(row["rel_gap_float"])) > 1e-12:
            raise AssertionError("A2 relative gap")
        if abs(float(gap) - float(a2_summary["screen_g_by_family"][family][alpha])) > 1e-12:
            raise AssertionError("A2 summary gap")
        if alpha in {"1/20", "1/10"}:
            tight += 1
            if gap != 0:
                raise AssertionError("A2 tight-alpha nonzero gap")
        elif alpha == "1":
            unconstrained_positive += int(gap > 0)
        else:
            raise AssertionError("unexpected A2 alpha")
    if len({family for family, _ in keys}) != 54 or tight != 108:
        raise AssertionError("A2 family/tight count")
    a3c_hashes = {
        "calendar_values.jsonl": "a7e0ce3a834a9e44b8aca126c6472208c39a83638131bd49d910639deec962af",
        "summary.json": "e78bb867453e2c2a4ac4658eacccfa6293fdd2e2cbe11315a4e1bf22d1acb298",
    }
    for name, expected in a3c_hashes.items():
        if hashlib.sha256((a3c / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"A3c archived hash mismatch: {name}")
    a3c_summary = json.loads((a3c / "summary.json").read_text(encoding="utf-8"))
    families = a3c_summary["families"]
    if len(families) != 6:
        raise AssertionError("A3c family count")
    bounds = []
    for row in families:
        lower, upper, g1 = Fraction(row["g_lo"]), Fraction(row["g_up"]), Fraction(row["g1_exact"])
        if not (0 < lower <= upper < g1):
            raise AssertionError("A3c bound ordering")
        for key, value in (("g_lo_float", lower), ("g_up_float", upper), ("g1", g1)):
            if abs(float(value) - float(row[key])) > 1e-12:
                raise AssertionError(f"A3c rational/float mismatch: {key}")
        bounds.append(
            {
                "family": row["family"],
                "lower": float(lower),
                "upper": float(upper),
                "unconstrained_gap": float(g1),
            }
        )
    return {
        "scope": "Stored rational arithmetic and archived hashes; no independent LP or theorem proof",
        "a2_cells": len(rows),
        "a2_families": 54,
        "a2_tight_zero_gap_cells": tight,
        "a2_unconstrained_positive_gap_cells": unconstrained_positive,
        "a2_historical_decision": a2_summary["decision"],
        "a3c_families": bounds,
        "a3c_historical_decision": a3c_summary["decision"],
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["a2_cells"], result["a2_tight_zero_gap_cells"], len(result["a3c_families"]))
