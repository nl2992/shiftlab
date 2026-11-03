"""Check A1b's archived rational gaps and registered continuation rule."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/a1b/cells.jsonl"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/A1B_GATE_RECOMPUTATION.json"


def run(source: Path = SOURCE) -> dict[str, object]:
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 10:
        raise ValueError("unexpected A1b row count")
    by_alpha: dict[str, list[tuple[int, Fraction]]] = {"1/5": [], "1/10": []}
    failed = []
    for row in rows:
        alpha = row["params"]["alpha"]
        horizon = int(row["params"]["T"])
        if alpha not in by_alpha:
            raise ValueError("unexpected alpha")
        if row.get("status") == "failed":
            failed.append({"alpha": alpha, "T": horizon, "error": row["error"]})
            continue
        joint = Fraction(row["J"])
        calendar = Fraction(row["C_star"])
        gap = (calendar - joint) / joint
        if calendar - joint != Fraction(row["abs_gap"]) or gap != Fraction(row["rel_gap"]):
            raise ValueError(f"stored rational gap mismatch: {alpha}/T{horizon}")
        if abs(float(gap) - float(row["rel_gap_float"])) > 1e-15:
            raise ValueError("stored float gap mismatch")
        by_alpha[alpha].append((horizon, gap))
    if len(failed) != 1 or (failed[0]["alpha"], failed[0]["T"]) != ("1/5", 12):
        raise ValueError("failed horizon mismatch")
    primary = sorted(by_alpha["1/5"])
    secondary = sorted(by_alpha["1/10"])
    if [h for h, _ in primary] != list(range(6, 12)) or [h for h, _ in secondary] != [9, 10, 11]:
        raise ValueError("solved horizon coverage mismatch")
    increments = [primary[i][1] - primary[i - 1][1] for i in range(1, len(primary))]
    largest = primary[-1][1]
    continue_rule = any(gap >= Fraction(1, 10) for _, gap in primary) or (
        all(delta >= Fraction(1, 200) for delta in increments[-3:]) and largest >= Fraction(1, 20)
    )
    kill_rule = (
        increments[-1] < Fraction(1, 400)
        and max(gap for _, gap in primary) < Fraction(1, 20)
        and all(gap == 0 for _, gap in secondary)
    )
    if continue_rule or kill_rule:
        raise ValueError("archived A1b classification differs from INCONCLUSIVE")
    return {
        "status": "ARCHIVED_EXPOSED_RATIONAL_ARITHMETIC_ONLY",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "solved_rows": len(primary) + len(secondary),
        "failed_rows": failed,
        "primary_gaps": [
            {"T": h, "fraction": str(g), "percent": 100 * float(g)} for h, g in primary
        ],
        "last_three_increments": [float(x) for x in increments[-3:]],
        "largest_solved_primary_gap_percent": 100 * float(largest),
        "shortfall_to_5_percent_percentage_points": 100 * float(Fraction(1, 20) - largest),
        "secondary_all_zero": all(gap == 0 for _, gap in secondary),
        "registered_continue": continue_rule,
        "registered_kill": kill_rule,
        "registered_verdict": "INCONCLUSIVE",
        "limitations": "Checks stored exact rational outputs and gate logic, not independent J/C* solver certificates or unsolved T=12.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['solved_rows']} solved rows verified; {result['registered_verdict']}")
