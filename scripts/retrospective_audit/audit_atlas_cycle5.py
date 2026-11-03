"""Locate and check historical cycle-5 aggregate arithmetic; no solver/MC rerun."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    source = (
        ROOT.parent
        / "shift-research-starter/outputs/failure_atlas_v1_cycle5/exact_cov/results.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    failures = []
    for x in data["cells"]:
        derived = {
            "CoV": x["V_valid"] - x["V_free"],
            "RC": x["methods"]["ref_valid"]["cost_rb"][0] - x["V_valid"],
            "best_safe_gap": x["methods"][x["best_safe"]]["cost_rb"][0] - x["V_valid"],
        }
        for key, value in derived.items():
            if abs(value - x[key]) > 1e-9:
                failures.append([x["id"], key])
        if bool(derived["RC"] > derived["CoV"]) != x["RC_gt_CoV"]:
            failures.append([x["id"], "decision"])
        if x["V_valid"] < x["V_free"] - 1e-9:
            failures.append([x["id"], "risk monotonicity"])
    count = sum(x["RC_gt_CoV"] for x in data["cells"])
    report = {
        "source": str(source.resolve()),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_meta": data["meta"],
        "cells": len(data["cells"]),
        "skipped": len(data["skipped"]),
        "RC_gt_CoV_count": count,
        "arithmetic_mismatches": failures,
        "majority_rule_reopens": count > len(data["cells"]) / 2,
        "scope": "Aggregate arithmetic only; source records 5000-seed MC and LP values. Neither raw MC nor LP solves rerun; no primal/dual certificates present in inspected aggregate. Cannot extrapolate tiny horizons to T1000.",
    }
    (ROOT / "docs/retrospective_audit_2026_11_01/ATLAS_CYCLE5_ARITHMETIC.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "cells": report["cells"],
                "skipped": report["skipped"],
                "RC_gt_CoV": count,
                "arithmetic_mismatches": len(failures),
            }
        )
    )


if __name__ == "__main__":
    main()
