"""Exploratory fixed-cohort comparison of monotone and unrestricted safe tests.

This is a small structural screen, not an efficacy study or novelty result. HMM
coefficients are formed with Fraction arithmetic; LP optimization is numerical.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

BITS = tuple(product((0, 1), repeat=2))
ENDPOINTS = (F(0), F(1, 2))
NULL_ROWS = tuple(
    (
        (1 - p1) * (1 - p20),
        (1 - p1) * p20,
        p1 * (1 - p21),
        p1 * p21,
    )
    for p1, p20, p21 in product(ENDPOINTS, repeat=3)
)
MONOTONE_ROWS = (
    (F(1), F(-1), F(0), F(0)),
    (F(1), F(0), F(-1), F(0)),
    (F(0), F(1), F(0), F(-1)),
    (F(0), F(0), F(1), F(-1)),
)


def alternative_coefficients(
    horizon: int,
    transition01: F,
    transition10: F,
    emission0: F,
    emission1: F,
    prior1: F,
    switch_cost: F,
) -> tuple[F, ...]:
    """P(Y1,Y2) times conditional post-decision net value for each tape."""
    result = []
    for y1, y2 in BITS:
        posterior1 = prior1
        tape_probability = F(1)
        for index, label in enumerate((y1, y2)):
            if index:
                posterior1 = (1 - posterior1) * transition01 + posterior1 * (1 - transition10)
            likelihood0 = emission0 if label else 1 - emission0
            likelihood1 = emission1 if label else 1 - emission1
            probability = (1 - posterior1) * likelihood0 + posterior1 * likelihood1
            tape_probability *= probability
            posterior1 = posterior1 * likelihood1 / probability

        gain = F(0)
        for _ in range(3, horizon + 1):
            posterior1 = (1 - posterior1) * transition01 + posterior1 * (1 - transition10)
            gain += (1 - posterior1) * (2 * emission0 - 1)
            gain += posterior1 * (2 * emission1 - 1)
        result.append(tape_probability * (gain - switch_cost))
    return tuple(result)


def solve(coefficients: tuple[F, ...], alpha: F, monotone: bool) -> float:
    risk = np.asarray([[float(value) for value in row] for row in NULL_ROWS])
    matrices = [risk]
    rhs = [np.full(len(NULL_ROWS), float(alpha))]
    if monotone:
        matrices.append(np.asarray([[float(value) for value in row] for row in MONOTONE_ROWS]))
        rhs.append(np.zeros(len(MONOTONE_ROWS)))
    result = linprog(
        -np.asarray([float(value) for value in coefficients]),
        A_ub=np.vstack(matrices),
        b_ub=np.concatenate(rhs),
        bounds=(0, 1),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"test LP failed: {result.message}")
    return float(-result.fun)


def main() -> None:
    transition_values = tuple(map(F, ("0.05", "0.1", "0.25", "0.4", "0.6", "0.75", "0.9")))
    transitions = tuple((a, b) for a in transition_values for b in transition_values if a + b <= 1)
    emissions0 = tuple(map(F, ("0.01", "0.1", "0.25", "0.4")))
    emissions1 = tuple(map(F, ("0.6", "0.75", "0.9", "0.99")))
    priors = tuple(map(F, ("0.05", "0.5", "0.95")))
    alphas = tuple(map(F, ("0.1", "0.3")))
    costs = tuple(map(F, ("0", "0.1", "0.5", "1")))

    checked = 0
    positive_utility_cells = 0
    gaps_over_tolerance = 0
    largest_gap = 0.0
    largest_gap_cell = None
    max_objective = 0.0
    for horizon, (a, b), e0, e1, prior, alpha, cost in product(
        (3, 6), transitions, emissions0, emissions1, priors, alphas, costs
    ):
        coefficients = alternative_coefficients(horizon, a, b, e0, e1, prior, cost)
        unrestricted = solve(coefficients, alpha, monotone=False)
        restricted = solve(coefficients, alpha, monotone=True)
        checked += 1
        max_objective = max(max_objective, unrestricted)
        if unrestricted > 1e-9:
            positive_utility_cells += 1
        gap = unrestricted - restricted
        if gap > 1e-7:
            gaps_over_tolerance += 1
        if gap > largest_gap:
            largest_gap = gap
            largest_gap_cell = {
                "horizon": horizon,
                "transition01": str(a),
                "transition10": str(b),
                "emission0": str(e0),
                "emission1": str(e1),
                "prior1": str(prior),
                "alpha": str(alpha),
                "switch_cost": str(cost),
                "unrestricted_value": unrestricted,
                "monotone_value": restricted,
            }

    result = {
        "status": "exploratory_fixed_cohort_structural_screen",
        "contract": {
            "queries": "fixed at events 1 and 2",
            "release_delay": 1,
            "decision": "one promotion at start of event 3, then hold through horizon",
            "pathwise_query_cap": 2,
            "causal_null": "P(Y_t=1 | full past and public choices) in [0,1/2]",
            "alpha_values": [str(value) for value in alphas],
            "scope": "No query cost because both test classes use the same fixed calendar.",
        },
        "grid": {
            "horizons": [3, 6],
            "transition_pairs": len(transitions),
            "emission0_values": [str(value) for value in emissions0],
            "emission1_values": [str(value) for value in emissions1],
            "prior_values": [str(value) for value in priors],
            "switch_costs": [str(value) for value in costs],
            "cells": checked,
        },
        "optimization": "Numerical LP over four terminal promotion probabilities; eight causal endpoint-null constraints; monotone class adds four cover inequalities.",
        "findings": {
            "positive_utility_cells": positive_utility_cells,
            "restricted_gaps_over_1e-7": gaps_over_tolerance,
            "largest_observed_unrestricted_minus_monotone": largest_gap,
            "largest_gap_cell": largest_gap_cell,
            "maximum_unrestricted_objective": max_objective,
        },
        "limitations": [
            "This is an exploratory development screen, not a preregistered efficacy study.",
            "LP optimal values use floating-point HiGHS and are not exact certificates.",
            "A two-label terminal test does not address adaptive acquisition or repeated reversals.",
            "A finite parameter grid is not a theorem about the model family.",
        ],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_hmm_monotone_terminal_test_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
