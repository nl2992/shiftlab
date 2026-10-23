from itertools import pairwise

import numpy as np
import pytest

from shiftlab.dive.query import (
    AdaptiveQueryPolicy,
    EvidenceGrowthQueryPolicy,
    cost_mixture_weight_for_tolerance,
    cost_neutral_propensities,
    expected_cost_drift_bound,
    expected_rate_drift_bound,
    mix_with_cost_neutral,
    mix_with_uniform,
)


@pytest.mark.parametrize(
    "method", ["uniform", "uncertainty", "variance", "cost_variance", "decision_value"]
)
def test_query_probabilities_are_bounded_and_calibrate_on_validation(method):
    proxy = np.linspace(-1, 1, 500)
    variance = np.linspace(0.1, 2.0, 500)
    uncertainty = np.linspace(0.01, 0.69, 500)
    policy = AdaptiveQueryPolicy(method, target_rate=0.2, q_min=0.05, q_max=0.5).fit_multiplier(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
    )
    probabilities = policy.probabilities(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
    )
    assert np.all((probabilities >= 0.05) & (probabilities <= 0.5))
    assert probabilities.mean() == pytest.approx(0.2, abs=1e-8)


def test_cost_variance_allocation_calibrates_expected_spend_and_beats_other_powers():
    variance = np.array([0.1, 0.4, 1.2, 3.0, 5.0])
    costs = np.array([3.0, 1.0, 2.0, 0.7, 2.5])
    proxy = np.zeros_like(variance)
    uncertainty = np.zeros_like(variance)
    target_rate, q_min, q_max = 0.3, 0.01, 0.9
    policy = AdaptiveQueryPolicy(
        "cost_variance", target_rate=target_rate, q_min=q_min, q_max=q_max
    ).fit_multiplier(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
        label_costs=costs,
    )
    probabilities = policy.probabilities(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
        label_costs=costs,
    )
    assert np.mean(probabilities * costs) == pytest.approx(target_rate * costs.mean(), abs=1e-8)

    def objective(q):
        return float(np.mean((1 / q - 1) * variance))

    assert objective(probabilities) < objective(
        AdaptiveQueryPolicy("variance", target_rate=target_rate, q_min=q_min, q_max=q_max)
        .fit_multiplier(
            proxy=proxy,
            residual_second_moment=variance,
            uncertainty=uncertainty,
            label_costs=costs,
        )
        .probabilities(
            proxy=proxy,
            residual_second_moment=variance,
            uncertainty=uncertainty,
            label_costs=costs,
        )
    )


def test_cost_variance_rejects_invalid_or_misaligned_label_costs():
    policy = AdaptiveQueryPolicy("cost_variance", target_rate=0.2)
    with pytest.raises(ValueError, match="label costs"):
        policy.fit_multiplier(
            proxy=np.zeros(2),
            residual_second_moment=np.ones(2),
            uncertainty=np.ones(2),
            label_costs=np.array([1.0, 0.0]),
        )


@pytest.mark.parametrize("method", ["uncertainty", "variance", "cost_variance", "decision_value"])
def test_adaptive_designs_match_expected_validation_spend(method):
    proxy = np.linspace(-1, 1, 100)
    variance = np.linspace(0.05, 2.0, 100)
    uncertainty = np.linspace(0.01, 0.69, 100)
    costs = np.linspace(0.5, 2.5, 100) ** 2
    target_rate = 0.2
    policy = AdaptiveQueryPolicy(
        method, target_rate=target_rate, q_min=0.05, q_max=0.7
    ).fit_multiplier(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
        label_costs=costs,
    )
    q = policy.probabilities(
        proxy=proxy,
        residual_second_moment=variance,
        uncertainty=uncertainty,
        label_costs=costs,
    )
    assert np.mean(q * costs) == pytest.approx(target_rate * np.mean(costs), abs=1e-8)


def test_cost_neutral_mixture_has_exact_budget_branch_and_bounded_shifted_spend():
    costs = np.array([0.5, 0.75, 1.5, 2.5])
    budget, q_min, q_max, rho = 0.15, 0.05, 0.5, 0.4
    neutral = cost_neutral_propensities(costs, budget_per_event=budget, q_min=q_min, q_max=q_max)
    assert costs * neutral == pytest.approx(np.full(len(costs), budget))
    adaptive = np.array([0.06, 0.48, 0.10, 0.49])
    mixed = mix_with_cost_neutral(
        adaptive,
        costs,
        budget_per_event=budget,
        mixture_weight=rho,
        q_min=q_min,
        q_max=q_max,
    )
    assert np.all((mixed >= q_min) & (mixed <= q_max))
    bound = expected_cost_drift_bound(
        budget_per_event=budget,
        mixture_weight=rho,
        cost_min=0.5,
        cost_max=2.5,
        q_min=q_min,
        q_max=q_max,
    )
    assert np.all(np.abs(costs * mixed - budget) <= bound + 1e-12)


def test_cost_neutral_propensity_rejects_infeasible_budget():
    with pytest.raises(ValueError, match="infeasible"):
        cost_neutral_propensities(np.array([0.5, 2.5]), budget_per_event=0.1, q_min=0.05, q_max=0.5)


def test_cost_mixture_weight_satisfies_requested_worst_case_drift():
    settings = {
        "budget_per_event": 0.15,
        "cost_min": 0.5,
        "cost_max": 2.5,
        "q_min": 0.05,
        "q_max": 0.5,
    }
    weight = cost_mixture_weight_for_tolerance(**settings, drift_tolerance=0.05)
    bound = expected_cost_drift_bound(**settings, mixture_weight=weight)
    assert 0 <= weight < 1
    assert bound == pytest.approx(0.05)
    assert cost_mixture_weight_for_tolerance(**settings, drift_tolerance=2.0) == 1.0


def test_adaptive_query_policy_requires_pre_monitor_calibration():
    policy = AdaptiveQueryPolicy("variance")
    with pytest.raises(RuntimeError, match="pre-monitor"):
        policy.probabilities(
            proxy=np.array([0.0]),
            residual_second_moment=np.array([1.0]),
            uncertainty=np.array([0.2]),
        )


@pytest.mark.parametrize("power", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_variance_allocation_power_grid_is_calibrated(power):
    values = np.linspace(0.05, 3.0, 200)
    policy = AdaptiveQueryPolicy(
        "variance", target_rate=0.15, q_min=0.03, q_max=0.6, variance_power=power
    ).fit_multiplier(
        proxy=np.zeros_like(values),
        residual_second_moment=values,
        uncertainty=np.zeros_like(values),
    )
    probs = policy.probabilities(
        proxy=np.zeros_like(values),
        residual_second_moment=values,
        uncertainty=np.zeros_like(values),
    )
    assert np.mean(probs) == pytest.approx(0.15, abs=1e-8)


def test_uniform_mixture_preserves_validation_rate_and_bounds_shifted_rate():
    target, q_min, q_max, rho = 0.1, 0.025, 0.5, 0.25
    adaptive_validation = np.array([q_min, 0.05, 0.15, 0.175])
    mixed = mix_with_uniform(adaptive_validation, target_rate=target, mixture_weight=rho)
    assert mixed.mean() == pytest.approx(target)
    drift_bound = expected_rate_drift_bound(
        target_rate=target, mixture_weight=rho, q_min=q_min, q_max=q_max
    )
    assert mixed.min() > 0
    assert drift_bound == pytest.approx(0.1)
    assert rho * (q_max - target) <= drift_bound


def test_uniform_mixture_rejects_invalid_weight():
    with pytest.raises(ValueError, match="mixture_weight"):
        mix_with_uniform(np.array([0.1]), target_rate=0.1, mixture_weight=1.1)


def test_evidence_growth_policy_matches_expected_validation_budget_with_heterogeneous_costs():
    n = 180
    proxy = np.linspace(-0.15, 0.15, n)
    p = np.linspace(0.15, 0.85, n)
    z0 = np.where(np.arange(n) % 2, 0.3, -0.2)
    z1 = np.where(np.arange(n) % 2, -0.2, 0.3)
    costs = np.linspace(0.5, 2.5, n)
    policy = EvidenceGrowthQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.7,
        bound=20.0,
    ).fit_multiplier(
        proxy=proxy,
        probability_positive=p,
        contrast_zero=z0,
        contrast_one=z1,
        label_costs=costs,
    )
    q = policy.probabilities(
        proxy=proxy,
        probability_positive=p,
        contrast_zero=z0,
        contrast_one=z1,
        label_costs=costs,
    )
    assert np.all((q >= 0.05) & (q <= 0.7))
    assert np.mean(q * costs) == pytest.approx(0.2 * costs.mean(), abs=1e-7)
    assert np.std(q) > 0.01


def test_evidence_growth_propensity_has_concave_conditional_objective():
    policy = EvidenceGrowthQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.7,
        bound=20.0,
    )
    h = np.array([-0.12, 0.02, 0.1])
    p = np.array([0.2, 0.5, 0.8])
    z0 = np.array([-0.3, -0.2, 0.1])
    z1 = np.array([0.2, 0.3, 0.4])
    derivatives = [
        policy._derivative(np.full(3, q), h, p, z0, z1) for q in (0.06, 0.12, 0.25, 0.5, 0.69)
    ]
    assert all(np.all(later <= earlier + 1e-12) for earlier, later in pairwise(derivatives))


def test_evidence_growth_derivative_matches_finite_difference():
    policy = EvidenceGrowthQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.7,
        bound=20.0,
    )
    h = np.array([0.04])
    p = np.array([0.63])
    z0 = np.array([-0.3])
    z1 = np.array([0.4])
    q = 0.31
    analytic = policy._derivative(np.array([q]), h, p, z0, z1)[0]

    def utility(value: float) -> float:
        stake = policy.stakes[None, :]
        weights = policy.weights[None, :]
        base = 1 + stake * h[:, None] / policy.bound
        no_query = np.sum(weights * np.log(base), axis=1)[0]
        estimate_zero = h + (z0 - h) / value
        estimate_one = h + (z1 - h) / value
        query_zero = np.sum(
            weights * np.log(1 + stake * estimate_zero[:, None] / policy.bound), axis=1
        )[0]
        query_one = np.sum(
            weights * np.log(1 + stake * estimate_one[:, None] / policy.bound), axis=1
        )[0]
        return (1 - value) * no_query + value * ((1 - p[0]) * query_zero + p[0] * query_one)

    step = 1e-6
    finite_difference = (utility(q + step) - utility(q - step)) / (2 * step)
    assert analytic == pytest.approx(finite_difference, rel=1e-6, abs=1e-8)
