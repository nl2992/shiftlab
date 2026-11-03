"""Recheck stored A1d rational grids and reproduce the existing bound algorithm."""

import importlib.util
import json
from collections import defaultdict
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/a1d"


def main():
    spec = importlib.util.spec_from_file_location(
        "mixture_bounds", ROOT / "scripts/promising_directions/mixture_bounds.py"
    )
    bounds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bounds)
    grid = defaultdict(lambda: defaultdict(list))
    for line in (SOURCE / "calendar_values.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["status"] != "completed":
            raise ValueError("unfinished solve")
        grid[row["prior1"]][tuple(row["calendar"])].append(
            (Fraction(row["a"]), Fraction(row["cost"]))
        )
    curves = 0
    for calendars in grid.values():
        for values in calendars.values():
            values.sort()
            if len({a for a, c in values}) != len(values):
                raise ValueError("duplicate risk point")
            slopes = [(d - b) / (c - a) for (a, b), (c, d) in pairwise(values)]
            if any(s > 0 for s in slopes) or any(a > b for a, b in pairwise(slopes)):
                raise ValueError("stored grid not monotone convex")
            curves += 1
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    records = []
    for prior, table in summary["tables"].items():
        for row in table["rows"]:
            alpha = Fraction(row["alpha"])
            joint = Fraction(row["J"])
            lo, hi = bounds.mixture_bounds(grid[prior], alpha)
            records.append(
                {
                    "prior": prior,
                    "alpha": str(alpha),
                    "J": str(joint),
                    "mixture_lower": str(lo),
                    "mixture_upper": str(hi),
                    "relative_gap_lower": float((lo - joint) / joint),
                    "relative_gap_upper": float((hi - joint) / joint),
                    "stored_upper_matches": hi == Fraction(row["C_mix"]),
                }
            )
    report = {
        "scope": "Stored rational grid arithmetic; existing bound algorithm reproduced; original LP solves and continuous convexity theorem not independently rerun/proved",
        "curves_checked": curves,
        "rows": records,
    }
    (ROOT / "docs/retrospective_audit_2026_11_01/A1D_BOUND_RECOMPUTATION.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "curves_checked": curves,
                "rows": len(records),
                "all_stored_upper_match": all(r["stored_upper_matches"] for r in records),
                "highlighted": [
                    r
                    for r in records
                    if (r["prior"], r["alpha"]) in [("1/10", "1/4"), ("1/5", "1/2")]
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
