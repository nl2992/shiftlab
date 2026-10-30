"""Exact finite-state check of the author soft-rank statistic and simulator scope."""

import hashlib
import importlib.util
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


class ProxyOnlyLearner:
    def fit_predict(self, _labels, features):
        return np.asarray(features)


def main():
    vendor = ROOT / "outputs/exhaustive_evaluation/betting_on_predictions"
    sys.path.insert(0, str(vendor))
    path = vendor / "sequential_tests/imputed.py"
    spec = importlib.util.spec_from_file_location("author_imputed_statistic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    author = module.Imputed(
        M=3, alg=ProxyOnlyLearner(), null_sampler=None, n_test=1, n_training=1, seed=17
    )
    author.gamma = np.log(2)
    rows = []
    error = 0.0
    for actual in [Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)]:
        for simulated in [Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)]:
            expectation = Fraction(0)
            for states in itertools.product([0, 1], repeat=4):
                scores = [1 + s for s in states]
                value = Fraction(4 * scores[0], sum(scores))
                probability = actual if states[0] else 1 - actual
                for state in states[1:]:
                    probability *= simulated if state else 1 - simulated
                expectation += probability * value
                result = author.calc_statistic_finite_sample(
                    None, sum(scores[1:]), np.array([states[0]])
                )
                error = max(error, abs(float(value) - result["statistic"]))
            if actual == simulated:
                assert expectation == 1
            rows.append(
                {
                    "observed_proxy_probability": str(actual),
                    "null_simulator_proxy_probability": str(simulated),
                    "exact_expected_factor": str(expectation),
                    "expected_factor": float(expectation),
                    "matched_null": actual == simulated,
                }
            )
    assert error < 1e-14
    mismatched = next(
        r
        for r in rows
        if r["observed_proxy_probability"] == "4/5"
        and r["null_simulator_proxy_probability"] == "1/5"
    )
    assert mismatched["expected_factor"] > 1
    result = {
        "status": "passed",
        "author_commit": "f99e196b0087128d7ffe0291df9e68042255eae8",
        "null_replicates": 3,
        "states_per_case": 16,
        "maximum_author_formula_error": error,
        "scope": "Eq2 author-statistic parity and exact exchangeability diagnostic; proxy-only learner is allowed but not paper experiment reproduction; mismatch lies outside matched-null guarantee",
        "rows": rows,
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [path, Path(__file__)]
        },
    }
    output = ROOT / "docs/exhaustive_evaluation/prediction_betting_exact_check.json"
    if output.exists():
        raise FileExistsError("retain original check")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
