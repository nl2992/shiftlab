from itertools import product
from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.special import logsumexp

from shiftlab.dive.budgeted_promotion import (
    ALPHA_ALLOCATIONS,
    MONITORING_RULES,
    BudgetedPromotionConfig,
    _candidate_outcome_contrasts,
    _decision_local_bounds,
    _monitor_family,
    _paired_bootstrap_contrasts,
)
from shiftlab.dive.eprocess import bounded_betting_factors
from shiftlab.dive.promotion_grid import _candidate_alpha_allocations


def test_candidate_alpha_allocations_respect_each_family_budget():
    candidates = [
        {
            "candidate_id": f"candidate-{i}",
            "validation_gain": 0.1 / (i + 1),
            "validation_gain_se": 0.02,
        }
        for i in range(5)
    ]
    allocations = _candidate_alpha_allocations(candidates, alpha=0.05)
    for name in ALPHA_ALLOCATIONS:
        values = [row[name] for row in allocations.values()]
        assert all(value > 0 for value in values)
        assert sum(values) <= 0.05 + 1e-12


def test_identical_actions_have_zero_counterfactual_cost_contrast():
    incumbent = np.asarray([0, 1, 0, 1])
    candidates = np.stack([incumbent, incumbent])
    z0, z1 = _candidate_outcome_contrasts(incumbent, candidates, fn=5.0, fp=1.0)
    assert np.array_equal(z0, np.zeros_like(z0))
    assert np.array_equal(z1, np.zeros_like(z1))


def test_decision_local_bounds_are_candidate_specific_and_cover_all_outcomes():
    family = {
        "h_proxy": np.asarray([[0.0], [0.0]]),
        "z0": np.asarray([[-1.0], [0.0]]),
        "z1": np.asarray([[1.0], [0.0]]),
    }
    bounds = _decision_local_bounds(
        family=family,
        event_index=0,
        propensity=0.2,
        estimator="prediction_powered",
        switch_rate=0.05,
    )
    assert bounds[0] == 5.05
    assert bounds[1] == 0.05
    for h, z0, z1, bound in zip(
        family["h_proxy"][:, 0], family["z0"][:, 0], family["z1"][:, 0], bounds, strict=True
    ):
        outcomes = np.asarray([h, h + (z0 - h) / 0.2, h + (z1 - h) / 0.2]) - 0.05
        assert np.max(np.abs(outcomes)) <= bound + 1e-12


def test_predictable_event_bounds_retain_null_control_in_heterogeneous_cost_simulation():
    rng = np.random.default_rng(26102026)
    streams = 500
    time_steps = 400
    q = 0.25
    alpha = 0.05
    stakes = np.asarray([0.1, 0.2, 0.4, 0.8])
    weights = np.full(len(stakes), 1 / len(stakes))
    log_e = {"global": np.zeros((streams, len(stakes))), "local": np.zeros((streams, len(stakes)))}
    crossed = {key: np.zeros(streams, dtype=bool) for key in log_e}
    for _ in range(time_steps):
        stratum = rng.integers(0, 2, size=streams)
        costs = np.where(stratum == 0, 1.0, 5.0)
        outcomes = rng.binomial(1, 0.5, size=streams)
        queried = rng.random(streams) < q
        paired_gain = np.where(outcomes == 1, costs, -costs)
        estimate = queried * paired_gain / q
        scales = {"global": np.full(streams, 5.0 / q), "local": costs / q}
        for mode, bound in scales.items():
            factors = bounded_betting_factors(estimate, bound, stakes)
            log_e[mode] += np.log(factors)
            log_value = logsumexp(log_e[mode] + np.log(weights), axis=1)
            crossed[mode] |= log_value >= -np.log(alpha)
    # This finite simulation checks implementation behavior under a nondegenerate
    # pointwise null; the guarantee comes from the conditional betting argument.
    assert crossed["local"].mean() < 0.08
    assert crossed["global"].mean() < 0.08


def test_monitor_obeys_common_hard_label_cap_and_uses_only_certified_candidates():
    candidate_rows = [
        {"candidate_id": f"copy-{i}", "validation_gain": 0.0, "validation_gain_se": 0.0}
        for i in range(2)
    ]
    alpha = _candidate_alpha_allocations(candidate_rows, alpha=0.05)
    config = BudgetedPromotionConfig(
        n=1000,
        d=2,
        seeds=1,
        budget_rates=(0.2,),
        query_policies=("uniform",),
        alpha_allocations=ALPHA_ALLOCATIONS,
        device="cpu",
    )
    family = {
        "validation_end": 10,
        "monitor_end": 20,
        "monitor_length": 10,
        "deployment_length": 5,
        "train_end": 5,
        "candidate_ids": ["copy-0", "copy-1"],
        "actions": np.zeros((2, 1000), dtype=int),
        "incumbent": np.zeros(1000, dtype=int),
        "z0": np.zeros((2, 1000)),
        "z1": np.zeros((2, 1000)),
        "h_proxy": np.zeros((2, 1000)),
        "h_truth": np.zeros((2, 1000)),
        "alpha_matrix": np.asarray(
            [[alpha[f"copy-{i}"][method] for method in ALPHA_ALLOCATIONS] for i in range(2)]
        ),
        "q_paths": {("uniform", 0.2): np.full(10, 0.5)},
        "q_min": {0.2: 0.1},
    }
    config.validate()
    for rule in MONITORING_RULES:
        rows = _monitor_family(
            family=family,
            y=np.zeros(1000, dtype=int),
            scenario=SimpleNamespace(name="copy_null", fn_cost=5.0, fp_cost=1.0),
            config=config,
            query_name="uniform",
            budget_rate=0.2,
            estimator="prediction_powered",
            query_uniforms=np.zeros(10),
            monitoring_rule=rule,
        )
        assert len(rows) == len(ALPHA_ALLOCATIONS)
        for row in rows:
            assert row["monitoring_rule"] == rule
            assert row["label_budget"] == 2
            assert row["labels_queried"] == 2
            assert row["labels_queried"] <= row["label_budget"]
            assert row["monitor_events_processed"] == 2
            assert row["candidate_id"] is None
            assert row["familywise_alpha_sum"] <= config.alpha + 1e-12

    direct_rows = _monitor_family(
        family=family,
        y=np.zeros(1000, dtype=int),
        scenario=SimpleNamespace(name="copy_null", fn_cost=5.0, fp_cost=1.0),
        config=config,
        query_name="uniform",
        budget_rate=0.2,
        estimator="direct_ipw",
        query_uniforms=np.zeros(10),
    )
    assert all(row["process_bound"] < rows[0]["process_bound"] for row in direct_rows)


def test_paired_bootstrap_contrasts_preserve_matched_seed_differences():
    rows = []
    for query, estimator, allocation, seed in product(
        ("uniform", "variance", "decision_value"),
        ("prediction_powered", "direct_ipw"),
        ALPHA_ALLOCATIONS,
        (1, 2),
    ):
        query_effect = {"uniform": 0.0, "variance": 1.0, "decision_value": 2.0}[query]
        estimator_effect = 3.0 if estimator == "direct_ipw" else 0.0
        alpha_effect = {"rank": 4.0, "equal": 1.0, "validation_power": 2.0}[allocation]
        rows.append(
            {
                "scenario": "stationary",
                "budget_rate": 0.20,
                "query_policy": query,
                "estimator": estimator,
                "alpha_allocation": allocation,
                "seed": seed,
                "expected_postpromotion_net_gain": query_effect + estimator_effect + alpha_effect,
                "promoted": bool(seed == 2 and query == "decision_value"),
                "labels_queried": 10 + seed,
                "monitor_fraction_processed": 1.0,
            }
        )
    paired = _paired_bootstrap_contrasts(pd.DataFrame(rows), draws=1000)
    row = paired[
        paired.contrast.eq("direct_ipw_minus_prediction_powered")
        & paired.metric.eq("expected_net_gain")
        & paired.query_policy.eq("uniform")
    ].iloc[0]
    assert row.mean_paired_difference == 3.0
    assert row.bootstrap_ci_low == 3.0
    assert row.bootstrap_ci_high == 3.0
