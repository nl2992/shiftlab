#!/usr/bin/env python3
"""Check every displayed cost-risk Pareto row against its family Track-R JSON."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "Family R": "outputs/sprint2/R/analysis/risk_curves.json",
    "Family T": "outputs/sprint2/T/trackR.json",
    "Family H": "docs/sprint2/family_h/track_R_all.json",
    "Family P": "docs/sprint2/family_p/trackR.json",
    "Family P5": "outputs/sprint2/P/trackR_K/risk_curves.json",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("docs/sprint2/cost_risk_audit.json"))
    args = parser.parse_args()
    report = (ROOT / "docs/sprint2/COST_RISK_PARETO.md").read_text()
    failures: list[str] = []
    rows_checked = 0
    family = None
    for line_no, line in enumerate(report.splitlines(), 1):
        if line.startswith("## Family "):
            family = line[3:]
            if family not in SOURCES:
                failures.append(f"line {line_no}: unexpected family section {family}")
            continue
        if not line.startswith("| R") or family is None:
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            failures.append(f"line {line_no}: expected five table cells, found {len(cells)}")
            continue
        target, candidate, alpha_text, risk_text, cost_text = cells
        source = json.loads((ROOT / SOURCES[family]).read_text())
        point = source.get("curves", {}).get(target, {}).get(candidate)
        if family == "Family P5" and point is not None:
            point = {"alpha": point["alpha"], "risk": point["eval_risk"],
                     "risk_ci": point["eval_risk_ci"], "cost": point["alt_net"],
                     "cost_ci": point["alt_net_ci"]}
        if point is None:
            failures.append(f"line {line_no}: {family}/{target}/{candidate} missing from source")
            continue
        try:
            alpha = float(alpha_text)
            risk_vals = [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", risk_text)]
            cost_vals = [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", cost_text)]
        except ValueError:
            failures.append(f"line {line_no}: cannot parse numeric cells")
            continue
        expected_risk = [point["risk"], *point["risk_ci"]]
        expected_cost = [point["cost"], *point["cost_ci"]]
        if len(risk_vals) != 3 or len(cost_vals) != 3:
            failures.append(f"line {line_no}: malformed interval cells")
            continue
        observed = [alpha, *risk_vals, *cost_vals]
        expected = [point["alpha"], *expected_risk, *expected_cost]
        if any(round(a, 1 if i >= 4 else 3) != round(b, 1 if i >= 4 else 3)
               for i, (a, b) in enumerate(zip(observed, expected))):
            failures.append(f"line {line_no}: {family}/{target}/{candidate} values {observed} != {expected}")
        rows_checked += 1
    result = {
        "audit": "PASS" if not failures and rows_checked else "FAIL",
        "rows_checked": rows_checked,
        "source_files": SOURCES,
        "differences": failures,
        "difference_count": len(failures),
        "scope_limitations": [
            "Checks displayed rows only; it does not prove the selected grid, Pareto construction, or target calibration is scientifically appropriate.",
            "Empirical risk intervals are descriptive and are not formal risk guarantees.",
        ],
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["audit"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
