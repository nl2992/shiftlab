"""Exact adaptive-delay check for the finite-model predictive confidence gate."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

P0 = F(1, 10)
P1 = F(9, 10)
PRIOR = F(1, 2)
ALPHA = F(1, 8)
BUDGET = 2
DELAY = 1


def likelihood(probability: F, observations: tuple[int, ...]) -> F:
    value = F(1)
    for outcome in observations:
        value *= probability if outcome else 1 - probability
    return value


def e_value(true_candidate: F, observations: tuple[int, ...]) -> F:
    denominator = likelihood(true_candidate, observations)
    numerator = PRIOR * likelihood(P0, observations) + PRIOR * likelihood(P1, observations)
    return numerator / denominator


def paths():
    """Enumerate source labels; query event 2 iff Y1=1, else query event 3."""
    rows = []
    for y1, y2, y3 in product((0, 1), repeat=3):
        # Event 1 is always queried. Y1 is released before the event-2 decision.
        q2 = y1
        q3 = 1 - y1
        observed = (y1, y2 if q2 else y3)
        assert 1 + q2 + q3 == BUDGET
        # Delay one: event 1 releases at 2; event 2 or 3 releases at 3 or 4.
        release_rounds = (2, 3 if q2 else 4)
        assert release_rounds[0] < release_rounds[1]
        assert e_value(P0, (y1,)) < 1 / ALPHA
        assert e_value(P1, (y1,)) < 1 / ALPHA
        rows.append((observed, (q2, q3), release_rounds))
    return rows


def summarize(true_probability: F):
    excluded_mass = F(0)
    paths_checked = 0
    for observations, _choices, _release_rounds in paths():
        # Distinct unqueried labels are integrated out. Sum their full-path probability
        # only once per observed pair by weighting all compatible paths below.
        prob = likelihood(true_probability, observations)
        # Each observed pair has two completions for the unqueried event.
        if e_value(true_probability, observations) >= 1 / ALPHA:
            excluded_mass += prob / 2
        paths_checked += 1
    return excluded_mass, paths_checked


if __name__ == "__main__":
    results = {}
    for p in (P0, P1):
        failure, n_paths = summarize(p)
        assert failure == F(1, 100)
        assert failure <= ALPHA
        results[str(p)] = {
            "confidence_set_failure_probability": str(failure),
            "alpha": str(ALPHA),
            "paths_enumerated": n_paths,
        }
    rows = paths()
    assert all(1 + q2 + q3 == BUDGET for _, (q2, q3), _ in rows)
    results["contract"] = {
        "parameter_models": [str(P0), str(P1)],
        "prior": str(PRIOR),
        "delay": DELAY,
        "pathwise_query_count": BUDGET,
        "adaptive_rule": "query event 2 iff released Y1=1; otherwise query event 3",
        "scope": "exact two-point IID (one-state HMM) mechanism check, not an efficacy or novelty result",
    }
    source = Path(__file__).read_bytes()
    results["sha256"] = hashlib.sha256(source).hexdigest()
    target = Path("outputs/switching_hmm_predictive_cs_candidate_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "exact_adaptive_delay_check.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, indent=2))
