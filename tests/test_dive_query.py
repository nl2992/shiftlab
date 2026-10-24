from itertools import pairwise

import numpy as np
import pytest

from shiftlab.dive.query import (
    AdaptiveQueryPolicy,
    EvidenceDirectedQueryPolicy,
    EvidenceGrowthQueryPolicy,
    ExactMixtureGrowthQueryPolicy,
    RobustActiveInferenceQueryPolicy,
    RobustMixtureGrowthQueryPolicy,
    cost_mixture_weight_for_tolerance,
    cost_neutral_propensities,
    expected_cost_drift_bound,
    expected_rate_drift_bound,
    mix_with_cost_neutral,
    mix_with_uniform,
)


def test_evidence_directed_query_is_predictable_bounded_and_spend_tapered():
    policy = EvidenceDirectedQueryPolicy(q_min=0.05, q_max=0.8, alpha=0.05)
    threshold = -np.log(0.05)
    assert policy.propensity(log_e_value=0.0, remaining_fraction=1.0) == pytest.approx(0.05)
    assert policy.propensity(log_e_value=threshold / 2, remaining_fraction=1.0) == pytest.approx(
        0.425
    )
    assert policy.propensity(log_e_value=threshold, remaining_fraction=1.0) == pytest.approx(0.8)
    assert policy.propensity(log_e_value=threshold, remaining_fraction=0.25) == pytest.approx(
        0.2375
    )
    for evidence in (-100.0, 0.0, threshold, 1e6):
        for remaining in (0.0, 0.1, 0.5, 1.0):
            q = policy.propensity(log_e_value=evidence, remaining_fraction=remaining)
            assert 0.05 <= q <= 0.8
    with pytest.raises(ValueError, match="remaining_fraction"):
        policy.propensity(log_e_value=0.0, remaining_fraction=1.1)


def test_evidence_directed_query_rejects_invalid_significance_and_support():
    with pytest.raises(ValueError, match="alpha"):
        EvidenceDirectedQueryPolicy(q_min=0.05, q_max=0.8, alpha=1.0)
    with pytest.raises(ValueError, match="q_min"):
        EvidenceDirectedQueryPolicy(q_min=0.0, q_max=0.8, alpha=0.05)
    with pytest.raises(ValueError, match="activation_fraction"):
        EvidenceDirectedQueryPolicy(q_min=0.05, q_max=0.8, alpha=0.05, activation_fraction=1.1)
    with pytest.raises(ValueError, match="urgency_power"):
        EvidenceDirectedQueryPolicy(q_min=0.05, q_max=0.8, alpha=0.05, urgency_power=0.0)


def test_concave_evidence_curve_uses_activation_offset_and_taper_parameters():
    policy = EvidenceDirectedQueryPolicy(
        q_min=0.05,
        q_max=0.5,
        alpha=0.05,
        activation_fraction=0.04,
        urgency_power=0.5,
        budget_taper_power=0.5,
    )
    at_start = policy.propensity(log_e_value=0.0, remaining_fraction=1.0)
    after_spend = policy.propensity(log_e_value=0.0, remaining_fraction=0.25)
    assert at_start == pytest.approx(0.05 + 0.45 * 0.2)
    assert after_spend == pytest.approx(0.05 + 0.45 * 0.2 * 0.5)
    assert policy.propensity(log_e_value=-1e6, remaining_fraction=1.0) == pytest.approx(0.05)


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


def test_robust_active_inference_path_is_precalibrated_bounded_and_minimax_selected():
    variance = np.linspace(0.05, 2.0, 200)
    costs = np.linspace(0.7, 2.2, 200)
    proxy = np.zeros_like(variance)
    uncertainty = np.zeros_like(variance)
    policy = RobustActiveInferenceQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.5,
        radius_fraction=0.4,
        path_grid=(0.0, 0.25, 0.5, 0.75, 1.0),
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
    assert policy.rho in (0.0, 0.25, 0.5, 0.75, 1.0)
    assert policy.uncertainty_radius == pytest.approx(0.4 * np.linalg.norm(variance))
    assert np.all((q >= 0.05) & (q <= 0.5))
    assert np.mean(q * costs) == pytest.approx(0.2 * np.mean(costs), abs=1e-8)

    def objective(probabilities):
        return float(
            np.mean(variance / probabilities)
            + policy.uncertainty_radius * np.linalg.norm(1 / probabilities) / len(probabilities)
        )

    scores = []
    for rho in policy.path_grid:
        raw = np.power(np.sqrt(variance / costs), 1 - rho) * 0.2**rho
        low, high = 0.0, 0.5 / max(float(raw.min()), 1e-12)
        for _ in range(80):
            middle = (low + high) / 2
            spend = np.mean(np.clip(middle * raw, 0.05, 0.5) * costs)
            if spend < 0.2 * np.mean(costs):
                low = middle
            else:
                high = middle
        candidate_q = np.clip(((low + high) / 2) * raw, 0.05, 0.5)
        scores.append(objective(candidate_q))
    assert objective(q) == pytest.approx(min(scores))


def test_robust_active_inference_rejects_invalid_radius():
    with pytest.raises(ValueError, match="radius_fraction"):
        RobustActiveInferenceQueryPolicy(
            target_rate=0.2, q_min=0.05, q_max=0.5, radius_fraction=-0.1
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


def test_exact_mixture_growth_matches_expected_log_evalue_and_validation_spend():
    n = 90
    proxy = np.linspace(-0.2, 0.2, n)
    p = np.linspace(0.1, 0.9, n)
    z0 = np.where(np.arange(n) % 2, -0.35, -0.1)
    z1 = np.where(np.arange(n) % 2, 0.1, 0.35)
    costs = np.linspace(0.5, 2.5, n)
    policy = ExactMixtureGrowthQueryPolicy(
        target_rate=0.2, q_min=0.05, q_max=0.7, bound=20.0, initial_stake=0.3
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
        effective_stake=0.3,
        label_costs=costs,
    )
    assert np.all((q >= 0.05) & (q <= 0.7))
    assert np.mean(q * costs) == pytest.approx(0.2 * costs.mean(), abs=1e-7)

    i = 17
    eta = 0.3

    def expected_log_growth(value: float) -> float:
        def log_factor(z: float) -> float:
            estimate = proxy[i] + (z - proxy[i]) / value
            return np.log1p(eta * estimate / policy.bound)

        no_query = np.log1p(eta * proxy[i] / policy.bound)
        return (1 - value) * no_query + value * (
            (1 - p[i]) * log_factor(z0[i]) + p[i] * log_factor(z1[i])
        )

    # The one-dimensional concave objective minus its fitted label price is
    # globally maximized by the reported propensity.
    optimum = expected_log_growth(q[i]) - policy.dual * costs[i] * q[i]
    grid = np.linspace(0.05, 0.7, 2001)
    alternatives = np.array(
        [expected_log_growth(value) - policy.dual * costs[i] * value for value in grid]
    )
    assert optimum >= alternatives.max() - 1e-10


def test_exact_mixture_growth_objective_is_concave_in_query_probability():
    policy = ExactMixtureGrowthQueryPolicy(
        target_rate=0.2, q_min=0.05, q_max=0.7, bound=20.0, initial_stake=0.3
    )
    h = np.array([-0.12, 0.02, 0.1])
    p = np.array([0.2, 0.5, 0.8])
    z0 = np.array([-0.3, -0.2, 0.1])
    z1 = np.array([0.2, 0.3, 0.4])
    eta = np.full(3, 0.3)
    derivatives = [
        policy._derivative(np.full(3, q), h, p, z0, z1, eta) for q in (0.06, 0.12, 0.25, 0.5, 0.69)
    ]
    assert all(np.all(later <= earlier + 1e-12) for earlier, later in pairwise(derivatives))


def test_exact_mixture_growth_derivative_matches_finite_difference():
    policy = ExactMixtureGrowthQueryPolicy(
        target_rate=0.2, q_min=0.05, q_max=0.7, bound=20.0, initial_stake=0.3
    )
    h, p, z0, z1, eta = (
        np.array([0.04]),
        np.array([0.63]),
        np.array([-0.3]),
        np.array([0.4]),
        np.array([0.3]),
    )
    q = np.array([0.31])
    analytic = policy._derivative(q, h, p, z0, z1, eta)[0]

    def objective(value: float) -> float:
        no_query = np.log1p(eta[0] * h[0] / policy.bound)
        queried = (1 - p[0]) * np.log1p(
            eta[0] * (h[0] + (z0[0] - h[0]) / value) / policy.bound
        ) + p[0] * np.log1p(eta[0] * (h[0] + (z1[0] - h[0]) / value) / policy.bound)
        return (1 - value) * no_query + value * queried

    step = 1e-6
    finite_difference = (objective(q[0] + step) - objective(q[0] - step)) / (2 * step)
    assert analytic == pytest.approx(finite_difference, rel=1e-6, abs=1e-8)


def test_robust_growth_zero_radius_matches_exact_growth_policy():
    n = 60
    proxy = np.linspace(-0.1, 0.1, n)
    p = np.linspace(0.2, 0.8, n)
    z0 = np.linspace(-0.3, 0.1, n)
    z1 = -z0
    costs = np.linspace(0.5, 2.5, n)
    common = {
        "target_rate": 0.2,
        "q_min": 0.05,
        "q_max": 0.7,
        "bound": 20.0,
        "initial_stake": 0.3,
    }
    exact = ExactMixtureGrowthQueryPolicy(**common).fit_multiplier(
        proxy=proxy,
        probability_positive=p,
        contrast_zero=z0,
        contrast_one=z1,
        label_costs=costs,
    )
    robust = RobustMixtureGrowthQueryPolicy(probability_radius=0.0, **common).fit_multiplier(
        proxy=proxy,
        probability_positive=p,
        contrast_zero=z0,
        contrast_one=z1,
        label_costs=costs,
    )
    arguments = {
        "proxy": proxy,
        "probability_positive": p,
        "contrast_zero": z0,
        "contrast_one": z1,
        "effective_stake": 0.3,
        "label_costs": costs,
    }
    assert robust.probabilities(**arguments) == pytest.approx(exact.probabilities(**arguments))


def test_robust_growth_objective_is_concave_under_probability_interval():
    policy = RobustMixtureGrowthQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.7,
        bound=20.0,
        initial_stake=0.3,
        probability_radius=0.2,
    )
    h = np.array([-0.12, 0.02, 0.1])
    p = np.array([0.2, 0.5, 0.8])
    z0 = np.array([-0.3, -0.2, 0.1])
    z1 = np.array([0.2, 0.3, 0.4])
    eta = np.full(3, 0.3)
    derivatives = [
        policy._derivative(np.full(3, q), h, p, z0, z1, eta) for q in (0.06, 0.12, 0.25, 0.5, 0.69)
    ]
    assert all(np.all(later <= earlier + 1e-12) for earlier, later in pairwise(derivatives))


def test_robust_growth_calibrates_cost_and_is_optimal_for_interval_objective():
    n = 80
    proxy = np.linspace(-0.15, 0.15, n)
    p = np.linspace(0.15, 0.85, n)
    z0 = np.where(np.arange(n) % 2, -0.35, -0.1)
    z1 = np.where(np.arange(n) % 2, 0.1, 0.35)
    costs = np.linspace(0.5, 2.5, n)
    policy = RobustMixtureGrowthQueryPolicy(
        target_rate=0.2,
        q_min=0.05,
        q_max=0.7,
        bound=20.0,
        initial_stake=0.3,
        probability_radius=0.15,
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
        effective_stake=0.3,
        label_costs=costs,
    )
    assert np.all((q >= 0.05) & (q <= 0.7))
    assert np.mean(q * costs) == pytest.approx(0.2 * costs.mean(), abs=1e-7)

    i = 11

    def robust_objective(value: float) -> float:
        def expected_log(probability: float) -> float:
            no_query = np.log1p(0.3 * proxy[i] / policy.bound)
            factor0 = np.log1p(0.3 * (proxy[i] + (z0[i] - proxy[i]) / value) / policy.bound)
            factor1 = np.log1p(0.3 * (proxy[i] + (z1[i] - proxy[i]) / value) / policy.bound)
            return (1 - value) * no_query + value * (
                (1 - probability) * factor0 + probability * factor1
            )

        p_low, p_high = max(0, p[i] - 0.15), min(1, p[i] + 0.15)
        return min(expected_log(p_low), expected_log(p_high)) - policy.dual * costs[i] * value

    grid = np.linspace(0.05, 0.7, 4001)
    assert robust_objective(q[i]) >= max(map(robust_objective, grid)) - 1e-8
