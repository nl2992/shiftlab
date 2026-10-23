import numpy as np
import pytest

from shiftlab.dive.query import (
    AdaptiveQueryPolicy,
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
