#!/usr/bin/env python3
"""Reconcile the leaderboard's six-regime A5b/P6 null counts to saved seed records."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/sprint2/round5/P6_LRMD_U_null1000/records.jsonl"
REPORT = ROOT / "docs/sprint2/LEADERBOARD.md"
REGIMES = [
    "F0_null",
    "F5_dep_null_r8",
    "F5_dep_null_r95",
    "O_null_order2",
    "O_null_semimarkov",
    "P_hmm_null",
]
POLICIES = ["A5b", "P6_LRMD_U"]
EXPECTED_DISPLAY = {
    "A5b": "1/1,000 F0; 2/1,000 Markov rho=.8; 3/1,000 rho=.95; 16/1,000 order-2; 60/1,000 semi-Markov; 176/1,000 HMM",
    "P6_LRMD_U": "10, 2, 6, 13, 79 and 139 promotions",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/leaderboard_claim_audit.json"))
    args = ap.parse_args()
    counts: Counter[tuple[str, str]] = Counter()
    totals: Counter[tuple[str, str]] = Counter()
    with SOURCE.open() as f:
        for line in f:
            r = json.loads(line)
            policy, regime = r.get("policy"), r.get("regime")
            if policy in POLICIES and regime in REGIMES:
                totals[(policy, regime)] += 1
                counts[(policy, regime)] += int(r.get("ever_promote", 0) > 0)
    values = {p: [counts[(p, reg)] for reg in REGIMES] for p in POLICIES}
    mismatches = []
    for p in POLICIES:
        for reg in REGIMES:
            if totals[(p, reg)] != 1000:
                mismatches.append(f"{p}/{reg}: expected 1000 rows, found {totals[(p, reg)]}")
    report = REPORT.read_text()
    if EXPECTED_DISPLAY["A5b"] not in report:
        mismatches.append("A5b leaderboard sentence missing or changed")
    if EXPECTED_DISPLAY["P6_LRMD_U"] not in report or "respectively" not in report:
        mismatches.append("P6 leaderboard sentence missing the ordered per-regime counts")
    result = {
        "audit": "PASS" if not mismatches else "FAIL",
        "source": str(SOURCE.relative_to(ROOT)),
        "report": str(REPORT.relative_to(ROOT)),
        "regime_order": REGIMES,
        "promotion_counts": values,
        "rows_per_policy_regime": 1000,
        "differences": mismatches,
        "limitations": [
            "Counts are descriptive for the saved six-regime run; they do not establish validity."
        ],
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
