#!/usr/bin/env python3
"""Merge the Family-H Track-R grids without duplicating shared controls.

The original grid screens H2/H4 plus D2/A5b. The completion screen adds H1/H3 and repeats D2/A5b
under the same seed/alpha contract. This merger keeps the original controls once, unions H1-H4, and
recomputes the family-level empirical Pareto flags.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def merge(existing: dict, added: dict, rollback: dict | None = None) -> dict:
    keep_existing = {"H2", "H4", "D2", "A5b"}
    keep_added = {"H1", "H3"}
    keep_rollback = {"H5", "H6-r10", "H6-r15", "H6-r25"}
    curves: dict[str, dict] = {}
    targets = sorted(set(existing.get("curves", {})) | set(added.get("curves", {})))
    for target in targets:
        points = {}
        for policy, point in existing.get("curves", {}).get(target, {}).items():
            if policy in keep_existing:
                points[policy] = point.copy()
        for policy, point in added.get("curves", {}).get(target, {}).items():
            if policy in keep_added:
                if policy in points:
                    raise ValueError(f"duplicate candidate in merged curve: {target}/{policy}")
                points[policy] = point.copy()
        for policy, point in (rollback or {}).get("curves", {}).get(target, {}).items():
            if policy in keep_rollback:
                if policy in points:
                    raise ValueError(f"duplicate candidate in merged curve: {target}/{policy}")
                points[policy] = point.copy()
        if points:
            ordered = sorted(points.items(), key=lambda item: (item[1]["risk"], item[1]["cost"]))
            best_cost = float("inf")
            front = set()
            for policy, point in ordered:
                if point["cost"] < best_cost:
                    best_cost = point["cost"]
                    front.add(policy)
            for policy, point in points.items():
                point["pareto"] = policy in front
            curves[target] = points
    calibration = {}
    for source, selected in ((existing, keep_existing), (added, keep_added),
                             (rollback or {}, keep_rollback)):
        for policy, targets_map in source.get("calibration", {}).items():
            if policy in selected:
                if policy in calibration:
                    raise ValueError(f"duplicate calibration for {policy}")
                calibration[policy] = targets_map
    required = {"H1", "H2", "H3", "H4", "D2", "A5b"}
    if rollback is not None:
        required |= {"H5", "H6-r10", "H6-r15", "H6-r25"}
    present = set(calibration)
    if present != required:
        raise ValueError(f"expected calibrations for {sorted(required)}, got {sorted(present)}")
    return {"calibration": calibration, "curves": curves,
            "scope": "Family H; H1-H6 plus D2/A5b; empirical Track-R grid, not guarantees."}


def render(data: dict) -> str:
    lines = [
        "# Family H Track-R cost–risk curves",
        "",
        "Merged from the H1-H4 and H5/H6 completion screens. Shared D2 and A5b controls are retained",
        "once. Alpha calibration uses development records; estimates use separate evaluation seeds.",
        "Operating points are empirical and their intervals are not formal guarantees.",
        "",
        "| Target | Candidate | alpha | eval risk (95% CI) | net cost (95% CI) | Pareto |",
        "|---|---|---:|---:|---:|---|",
    ]
    for target, points in data["curves"].items():
        for policy, point in sorted(points.items(), key=lambda item: item[1]["cost"]):
            lo, hi = point["risk_ci"]
            clo, chi = point["cost_ci"]
            lines.append(f"| {target} | `{policy}` | {point['alpha']} | {point['risk']:.3f} [{lo:.3f},{hi:.3f}] | "
                         f"{point['cost']:.1f} [{clo:.1f},{chi:.1f}] | {'*' if point['pareto'] else ''} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--existing", type=Path, default=Path("docs/sprint2/family_h/track_R.json"))
    parser.add_argument("--added", type=Path, default=Path("docs/sprint2/family_h/track_R_remaining.json"))
    parser.add_argument("--rollback", type=Path, default=Path("docs/sprint2/family_h/track_R_rollback.json"))
    parser.add_argument("--out", type=Path, default=Path("docs/sprint2/family_h/track_R_all.json"))
    args = parser.parse_args()
    existing = json.loads(args.existing.read_text())
    added = json.loads(args.added.read_text())
    rollback = json.loads(args.rollback.read_text()) if args.rollback.exists() else None
    result = merge(existing, added, rollback)
    args.out.write_text(json.dumps(result, indent=1, default=float) + "\n")
    args.out.with_suffix(".md").write_text(render(result))
    print(f"merged {len(result['calibration'])} policies across {len(result['curves'])} targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
