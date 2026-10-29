"""Exact finite checks for the monotone-event causal-null reduction lemma."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def event_index(bits: tuple[int, ...]) -> int:
    return sum(bit << i for i, bit in enumerate(bits))


def monotone(table: tuple[int, ...], horizon: int) -> bool:
    tapes = tuple(product((0, 1), repeat=horizon))
    for low in tapes:
        for high in tapes:
            if all(x <= y for x, y in zip(low, high, strict=True)) and (
                table[event_index(low)] > table[event_index(high)]
            ):
                return False
    return True


def iid_risk(table: tuple[int, ...]) -> F:
    return F(sum(table), len(table))


def causal_risk(table: tuple[int, ...], horizon: int) -> F:
    def visit(prefix: tuple[int, ...]) -> F:
        if len(prefix) == horizon:
            return F(table[event_index(prefix)])
        zero = visit(prefix + (0,))
        one = visit(prefix + (1,))
        # A linear function of the next conditional success probability is maximized
        # at one of the admissible endpoints p=0 or p=1/2.
        return max(zero, (zero + one) / 2)

    return visit(())


def run() -> dict[str, object]:
    summaries = []
    increasing_count = 0
    for horizon in range(1, 4):
        count = 0
        total = 0
        for table in product((0, 1), repeat=2**horizon):
            total += 1
            if monotone(table, horizon):
                count += 1
                increasing_count += 1
                assert causal_risk(table, horizon) == iid_risk(table)
        summaries.append(
            {
                "horizon": horizon,
                "all_event_tables": total,
                "monotone_event_tables": count,
                "monotone_tables_with_boundary_equality": count,
            }
        )

    # Construct the witness through the tape map to avoid an indexing convention mismatch.
    mapped = [0] * 4
    for y1, y2 in product((0, 1), repeat=2):
        mapped[event_index((y1, y2))] = int(y1 == 0 and y2 == 1)
    witness_table = tuple(mapped)
    witness_iid = iid_risk(witness_table)
    witness_robust = causal_risk(witness_table, 2)
    assert (witness_iid, witness_robust) == (F(1, 4), F(1, 2))

    # Adaptive acquisition example: query Y1; after Y1=1, promote and stop;
    # after Y1=0, spend a second query on Y2 and promote iff Y2=1. The query
    # decision is decreasing in Y1, but the promotion event is Y1 OR Y2.
    adaptive_table = [0] * 4
    for y1, y2 in product((0, 1), repeat=2):
        adaptive_table[event_index((y1, y2))] = int(bool(y1 or y2))
    adaptive_table = tuple(adaptive_table)
    adaptive_iid = iid_risk(adaptive_table)
    adaptive_robust = causal_risk(adaptive_table, 2)
    assert adaptive_iid == adaptive_robust == F(3, 4)
    return {
        "status": "monotone_event_reduction_checks_passed_no_method_claim",
        "summaries": summaries,
        "monotone_tables_checked": increasing_count,
        "nonmonotone_witness": {
            "event": "Y1=0 and Y2=1",
            "iid_boundary_risk": str(witness_iid),
            "causal_null_risk": str(witness_robust),
            "maximizing_conditional_probabilities": ["0", "1/2"],
        },
        "adaptive_query_monotone_event_example": {
            "query_rule": "query Y2 only when Y1=0",
            "promotion_event": "Y1=1 or Y2=1",
            "iid_boundary_risk": str(adaptive_iid),
            "causal_null_risk": str(adaptive_robust),
            "maximum_queries": 2,
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact event-table checks for horizons 1-3; the coupling proof covers arbitrary finite horizon.",
    }


if __name__ == "__main__":
    result = run()
    target = Path("outputs/switching_monotone_promotion_reduction_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summaries"], indent=2))
