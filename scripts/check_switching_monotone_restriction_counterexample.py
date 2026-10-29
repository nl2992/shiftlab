"""Exact primal/dual screen for the cost of monotone terminal promotion."""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

TAPES = tuple(itertools.product((0, 1), repeat=3))
ALPHA = F(1, 20)
QUERY_COST = F(1, 100)
SWITCH_COST = F(1, 10)
P01 = F(1)
P10 = F(9, 10)
THETA0 = F(1, 100)
THETA1 = F(99, 100)
PRIOR1 = F(0)


def _transition(state: int) -> tuple[tuple[int, F], ...]:
    if state == 0:
        return ((0, 1 - P01), (1, P01))
    return ((0, P10), (1, 1 - P10))


def _emission(state: int, outcome: int) -> F:
    p = THETA1 if state else THETA0
    return p if outcome else 1 - p


def alternative_tape_law() -> tuple[list[F], list[F]]:
    """Return P(Y1:3=y) and P(Y4=1|Y1:3=y) by exact hidden-path sum."""
    tape_mass = {tape: F(0) for tape in TAPES}
    joint_y4 = {tape: F(0) for tape in TAPES}
    initial = ((0, 1 - PRIOR1), (1, PRIOR1))
    for states in itertools.product((0, 1), repeat=4):
        state_mass = dict(initial)[states[0]]
        for t in range(3):
            state_mass *= dict(_transition(states[t]))[states[t + 1]]
        for tape in TAPES:
            mass = state_mass
            for t, y in enumerate(tape):
                mass *= _emission(states[t], y)
            if mass:
                tape_mass[tape] += mass
                joint_y4[tape] += mass * _emission(states[3], 1)
    probabilities, p_y4 = [], []
    for tape in TAPES:
        probabilities.append(tape_mass[tape])
        p_y4.append(joint_y4[tape] / tape_mass[tape])
    assert sum(probabilities) == 1
    return probabilities, p_y4


def null_endpoint_rows() -> list[list[F]]:
    """Enumerate all 2^(1+2+4) causal endpoint response trees."""
    rows: list[list[F]] = []
    for choices in itertools.product((F(0), F(1, 2)), repeat=7):
        p1 = choices[0]
        p2 = {y1: choices[1 + y1] for y1 in (0, 1)}
        p3 = {(y1, y2): choices[3 + 2 * y1 + y2] for y1 in (0, 1) for y2 in (0, 1)}
        probabilities = []
        for y1, y2, y3 in TAPES:
            p = p1 if y1 else 1 - p1
            p *= p2[y1] if y2 else 1 - p2[y1]
            p *= p3[y1, y2] if y3 else 1 - p3[y1, y2]
            probabilities.append(p)
        assert sum(probabilities) == 1
        rows.append(probabilities)
    assert len(rows) == 128
    return rows


def _cover_rows() -> list[list[F]]:
    index = {tape: i for i, tape in enumerate(TAPES)}
    rows = []
    for tape in TAPES:
        for bit, value in enumerate(tape):
            if value:
                continue
            successor = tape[:bit] + (1,) + tape[bit + 1 :]
            row = [F(0)] * len(TAPES)
            row[index[tape]] = 1
            row[index[successor]] = -1
            rows.append(row)
    assert len(rows) == 12
    return rows


def _matvec(row: list[F], vector: list[F]) -> F:
    return sum((a * b for a, b in zip(row, vector, strict=True)), F(0))


def _max_risk(rows: list[list[F]], q: list[F]) -> F:
    return max(_matvec(row, q) for row in rows)


def _rational_primal(values: np.ndarray, rows: list[list[F]], monotone: bool) -> list[F]:
    q = [F(float(value)).limit_denominator(10**7) for value in values]
    cover = _cover_rows()
    assert all(0 <= value <= 1 for value in q)
    if monotone:
        assert all(_matvec(row, q) <= 0 for row in cover)
    risk = _max_risk(rows, q)
    if risk > ALPHA:
        q = [value * ALPHA / risk for value in q]
    assert _max_risk(rows, q) <= ALPHA
    if monotone:
        assert all(_matvec(row, q) <= 0 for row in cover)
    return q


def _solve(
    objective: list[F], null_rows: list[list[F]], monotone: bool
) -> tuple[list[F], F, dict[str, object]]:
    cover = _cover_rows() if monotone else []
    rows = null_rows + cover + [[F(int(i == j)) for j in range(8)] for i in range(8)]
    rhs = [ALPHA] * len(null_rows) + [F(0)] * len(cover) + [F(1)] * 8
    result = linprog(
        -np.array([float(value) for value in objective]),
        A_ub=np.array([[float(value) for value in row] for row in rows]),
        b_ub=np.array([float(value) for value in rhs]),
        bounds=[(0, None)] * 8,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    q = _rational_primal(result.x, null_rows, monotone)
    primal = _matvec(objective, q)

    # Convert HiGHS' dual to rationals; add any residual to the q_i<=1
    # multipliers, which preserves dual feasibility and yields an exact upper bound.
    dual = [
        max(F(0), F(float(-value)).limit_denominator(10**9)) for value in result.ineqlin.marginals
    ]
    for column in range(8):
        lhs = sum((rows[i][column] * dual[i] for i in range(len(rows))), F(0))
        if lhs < objective[column]:
            dual[len(null_rows) + len(cover) + column] += objective[column] - lhs
    assert all(
        sum((rows[i][j] * dual[i] for i in range(len(rows))), F(0)) >= objective[j]
        for j in range(8)
    )
    upper = sum((rhs[i] * dual[i] for i in range(len(rows))), F(0))
    assert primal <= upper
    certificate = {
        "primal_exact": str(primal),
        "dual_upper_exact": str(upper),
        "dual_gap_exact": str(upper - primal),
        "dual_multipliers": [str(value) for value in dual],
        "solver_status": result.message,
    }
    return q, primal, certificate


def run() -> dict[str, object]:
    p_alt, p4 = alternative_tape_law()
    gain = [2 * p - 1 - SWITCH_COST for p in p4]
    utility = [p * g for p, g in zip(p_alt, gain, strict=True)]
    null_rows = null_endpoint_rows()
    q_full, full_value, full_certificate = _solve(utility, null_rows, monotone=False)
    q_mono, mono_value, mono_certificate = _solve(utility, null_rows, monotone=True)
    full_risk = _max_risk(null_rows, q_full)
    mono_risk = _max_risk(null_rows, q_mono)
    mono_upper = F(mono_certificate["dual_upper_exact"])
    gap = full_value - mono_upper
    assert gap > 0, (full_value, mono_certificate)
    assert full_risk <= ALPHA and mono_risk <= ALPHA
    assert all(_matvec(row, q_mono) <= 0 for row in _cover_rows())
    query_charge = 3 * QUERY_COST
    return {
        "status": "exact_primal_dual_monotone_restriction_gap",
        "protocol": "docs/switching_monotone_restriction_counterexample_v1.md",
        "contract": {
            "horizon": 4,
            "budget": 3,
            "delay": 1,
            "query_schedule": [1, 2, 3],
            "promotion_decision_event": 4,
            "alpha": str(ALPHA),
            "query_cost": str(QUERY_COST),
            "switch_cost": str(SWITCH_COST),
            "endpoint_null_count": len(null_rows),
        },
        "alternative_model": {
            "prior1": str(PRIOR1),
            "transition01": str(P01),
            "transition10": str(P10),
            "emission0": str(THETA0),
            "emission1": str(THETA1),
        },
        "tape_order": ["".join(map(str, tape)) for tape in TAPES],
        "alternative_tape_probabilities": [str(value) for value in p_alt],
        "conditional_future_positive_probabilities": [str(value) for value in p4],
        "net_gain_if_promoted_by_tape": [str(value) for value in gain],
        "unrestricted_safe_policy": {
            "promotion_probabilities": [str(value) for value in q_full],
            "causal_null_risk": str(full_risk),
            "expected_net_savings_before_common_query_cost": str(full_value),
            "certificate": full_certificate,
        },
        "monotone_safe_policy": {
            "promotion_probabilities": [str(value) for value in q_mono],
            "causal_null_risk": str(mono_risk),
            "expected_net_savings_before_common_query_cost": str(mono_value),
            "certificate": mono_certificate,
        },
        "certified_unrestricted_minus_monotone_gap": str(gap),
        "common_query_charge": str(query_charge),
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                __file__,
                "docs/switching_monotone_restriction_counterexample_v1.md",
                "src/shiftlab/dive/causal_switching_game.py",
            )
        },
        "scope": "One exact three-label terminal-testing separation; not an algorithm or empirical efficacy result.",
    }


if __name__ == "__main__":
    report = run()
    target = Path("outputs/switching_monotone_restriction_counterexample_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
