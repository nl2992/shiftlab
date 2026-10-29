"""Exact check of adaptive, fixed-delay likelihoods for a small hidden-state HMM.

This verifies a registered confidence-set baseline, not a new acquisition method.
All probabilities are rational and the complete state/outcome path space is enumerated.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

T = 8
DELAY = 2
BUDGET = 4
ALPHA = F(1, 20)
PRIOR = (F(1, 2), F(1, 2))

# Each model is a two-state HMM with Bernoulli emissions.
MODELS = (
    {
        "initial": (F(1, 2), F(1, 2)),
        "transition": ((F(4, 5), F(1, 5)), (F(1, 5), F(4, 5))),
        "emission_one": (F(1, 10), F(1, 4)),
    },
    {
        "initial": (F(2, 3), F(1, 3)),
        "transition": ((F(3, 4), F(1, 4)), (F(1, 4), F(3, 4))),
        "emission_one": (F(3, 4), F(9, 10)),
    },
)


def path_probability(model: dict, states: tuple[int, ...], outcomes: tuple[int, ...]) -> F:
    p = model["initial"][states[0]]
    for t, (state, outcome) in enumerate(zip(states, outcomes)):
        emission = model["emission_one"][state]
        p *= emission if outcome else 1 - emission
        if t + 1 < T:
            p *= model["transition"][state][states[t + 1]]
    return p


def policy_prefixes(
    outcomes: tuple[int, ...],
) -> list[tuple[tuple[int, ...], tuple[tuple[int, int], ...]]]:
    """Return observed (past query choices, released labels) at each decision time."""
    queries: list[int] = []
    released: dict[int, int] = {}
    prefixes = []
    for t in range(1, T + 1):
        due = t - DELAY
        if due >= 1 and due <= len(queries) and queries[due - 1]:
            released[due] = outcomes[due - 1]
        visible = tuple(sorted((s, y) for s, y in released.items()))
        prefixes.append((tuple(queries), visible))

        if t <= DELAY:
            q = 1
        else:
            due = t - DELAY
            q = int(sum(queries) < BUDGET and queries[due - 1] == 1 and outcomes[due - 1] == 1)
        if sum(queries) + q > BUDGET:
            raise AssertionError("policy exceeded its pathwise query cap")
        queries.append(q)
    return prefixes


def observed_hmm_likelihood(model: dict, visible: tuple[tuple[int, int], ...]) -> F:
    """HMM likelihood with unobserved and pending outcomes marginalized."""
    observed = dict(visible)
    alpha = [model["initial"][z] for z in range(2)]
    if 1 in observed:
        y = observed[1]
        alpha = [
            p * (model["emission_one"][z] if y else 1 - model["emission_one"][z])
            for z, p in enumerate(alpha)
        ]
    for t in range(2, T + 1):
        predicted = [
            sum(alpha[z] * model["transition"][z][z2] for z in range(2)) for z2 in range(2)
        ]
        if t in observed:
            y = observed[t]
            alpha = [
                p * (model["emission_one"][z] if y else 1 - model["emission_one"][z])
                for z, p in enumerate(predicted)
            ]
        else:
            alpha = predicted
    return sum(alpha)


def fmt(x: F) -> str:
    return f"{x.numerator}/{x.denominator}"


def main() -> None:
    likelihood_cache: dict[tuple[int, tuple[tuple[int, int], ...]], F] = {}

    def likelihood(model_index: int, visible: tuple[tuple[int, int], ...]) -> F:
        key = (model_index, visible)
        if key not in likelihood_cache:
            likelihood_cache[key] = observed_hmm_likelihood(MODELS[model_index], visible)
        return likelihood_cache[key]

    all_paths = []
    for states in product(range(2), repeat=T):
        for outcomes in product(range(2), repeat=T):
            all_paths.append((states, outcomes))

    transcript_masses: list[list[dict[tuple, F]]] = [[{} for _ in range(T)] for _ in MODELS]
    path_masses = [[F(0) for _ in all_paths] for _ in MODELS]
    prefix_cache = {}
    for path_index, (states, outcomes) in enumerate(all_paths):
        prefixes = policy_prefixes(outcomes)
        prefix_cache[outcomes] = prefixes
        for m, model in enumerate(MODELS):
            p = path_probability(model, states, outcomes)
            path_masses[m][path_index] = p
            for t, transcript in enumerate(prefixes):
                masses = transcript_masses[m][t]
                masses[transcript] = masses.get(transcript, F(0)) + p

    # Exact joint transcript masses must equal the fixed-mask HMM likelihood for every
    # compatible observable history. Query choices are predictable functions of released data.
    likelihood_checks = 0
    for m, model in enumerate(MODELS):
        for t, masses in enumerate(transcript_masses[m], start=1):
            for transcript, exact_mass in masses.items():
                qprefix, visible = transcript
                if sum(qprefix) > BUDGET:
                    raise AssertionError("observable query prefix exceeds budget")
                filter_mass = likelihood(m, visible)
                if exact_mass != filter_mass:
                    raise AssertionError(
                        f"likelihood mismatch at t={t}, model={m}: {exact_mass} != {filter_mass}"
                    )
                likelihood_checks += 1

    # Compute exact probability, under each true model, that the mixture/true likelihood
    # ratio ever reaches 1/alpha on this adaptive delayed schedule.
    coverage_failure = []
    maximum_query_count = 0
    for true_index, model in enumerate(MODELS):
        failure_mass = F(0)
        for path_index, (_states, outcomes) in enumerate(all_paths):
            p_path = path_masses[true_index][path_index]
            if not p_path:
                continue
            prefixes = prefix_cache[outcomes]
            failed = False
            for t, (_qprefix, visible) in enumerate(prefixes):
                l_true = likelihood(true_index, visible)
                mixture = sum(PRIOR[m] * likelihood(m, visible) for m in range(len(MODELS)))
                if l_true == 0:
                    raise AssertionError("true-model likelihood vanished on its own path")
                if mixture / l_true >= 1 / ALPHA:
                    failed = True
                    break
            if failed:
                failure_mass += p_path
            maximum_query_count = max(
                maximum_query_count, max(sum(qprefix) for qprefix, _ in prefixes)
            )
        coverage_failure.append(failure_mass)
        if failure_mass > ALPHA:
            raise AssertionError(f"coverage failure {failure_mass} exceeds alpha={ALPHA}")

    script_path = Path(__file__)
    output_dir = Path("outputs/switching_delayed_hmm_likelihood_v1")
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "horizon": T,
        "delay": DELAY,
        "budget": BUDGET,
        "alpha": fmt(ALPHA),
        "models": 2,
        "complete_state_outcome_paths": len(all_paths),
        "transcript_likelihood_equalities_checked": likelihood_checks,
        "max_queries_in_any_observed_prefix": maximum_query_count,
        "coverage_failure_probability_by_true_model": [fmt(x) for x in coverage_failure],
        "coverage_failure_decimal_by_true_model": [float(x) for x in coverage_failure],
        "source_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "scope": "exact likelihood and confidence-set mechanism check; not efficacy evidence",
    }
    (output_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
