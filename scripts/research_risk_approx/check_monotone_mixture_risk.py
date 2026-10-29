"""Exact two-branch check: aggregate monotonicity need not certify causal risk."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/MONOTONE_MIXTURE_RISK_PROTOCOL_V1.md"
OUTPUT = ROOT / "docs/risk_preserving_approx/monotone_mixture_risk_v1.json"


def event_a(y2: int, y3: int) -> F:
    return F(int((y2, y3) == (0, 1)))


def event_b(y2: int, y3: int) -> F:
    return F(y2)


def causal_risk(event) -> F:
    """Max probability of a terminal event under p_t(history) in {0, 1/2}."""

    def visit(prefix: tuple[int, ...]) -> F:
        if len(prefix) == 2:
            return event(*prefix)
        zero = visit(prefix + (0,))
        one = visit(prefix + (1,))
        return max(zero, (zero + one) / 2)

    return visit(())


def main() -> None:
    rows = []
    mixed = {}
    for y2, y3 in product((0, 1), repeat=2):
        a, b = event_a(y2, y3), event_b(y2, y3)
        mixed[f"{y2}{y3}"] = (a + b) / 2
        rows.append(
            {
                "tape_y2y3": f"{y2}{y3}",
                "branch_a": str(a),
                "branch_b": str(b),
                "mixture_event": str(mixed[f"{y2}{y3}"]),
            }
        )
    iid_risk = sum(mixed[f"{a}{b}"] for a, b in product((0, 1), repeat=2)) / 4
    risk_a, risk_b = causal_risk(event_a), causal_risk(event_b)
    mixture_causal_risk = (risk_a + risk_b) / 2
    if (
        list(mixed.values()) != [F(0), F(1, 2), F(1, 2), F(1, 2)]
        or iid_risk != F(3, 8)
        or risk_a != F(1, 2)
        or risk_b != F(1, 2)
        or mixture_causal_risk != F(1, 2)
    ):
        raise AssertionError("the registered exact counterexample did not reproduce")
    payload = {
        "protocol": PROTOCOL.relative_to(ROOT).as_posix(),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "table": rows,
        "iid_risk_of_aggregate_event": str(iid_risk),
        "branch_a_causal_risk": str(risk_a),
        "branch_b_causal_risk": str(risk_b),
        "public_branch_mixture_causal_risk": str(mixture_causal_risk),
        "query_cap": 3,
        "maximum_queries_branch_a": 3,
        "maximum_queries_branch_b": 2,
    }
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
