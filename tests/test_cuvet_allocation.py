import numpy as np
import pytest

from shiftlab.dive.cuvet import (
    CuvetQuantileTree,
    PowerLawBucket,
    allocate_marginal_cost_equalization,
    fit_power_law_bucket,
)


def test_single_bucket_allocation_satisfies_cost_budget() -> None:
    bucket = PowerLawBucket(10.0, 4.0, 0.8, 1.3)
    allocation = allocate_marginal_cost_equalization([bucket], budget=5.0)

    expected_alpha = (5.0 / 4.0) ** (1.0 / 1.3)
    assert allocation.multipliers[0] == pytest.approx(expected_alpha, rel=1e-8)
    assert allocation.total_cost == pytest.approx(5.0, rel=1e-8)
    assert allocation.total_value == pytest.approx(bucket.value(expected_alpha), rel=1e-8)


def test_multiple_buckets_equalize_marginal_cost_per_value() -> None:
    buckets = [
        # Appendix F uses X ~ Uniform(0, 1), so its regions have masses
        # 0.1, 0.4, and 0.5. Weight the listed conditional totals by mass.
        PowerLawBucket(0.1 * 6.5, 0.1 * 0.4, 1.0, 1.5),
        PowerLawBucket(0.4 * 1.63, 0.4 * 0.1, 1.0, 1.5),
        PowerLawBucket(0.5 * 1.19, 0.5 * 0.1, 1.0, 1.5),
    ]
    allocation = allocate_marginal_cost_equalization(buckets, budget=0.13)

    marginal_costs = [
        bucket.marginal_cost_per_value(alpha)
        for bucket, alpha in zip(buckets, allocation.multipliers, strict=True)
    ]
    assert allocation.total_cost == pytest.approx(0.13, rel=1e-8)
    assert max(marginal_costs) - min(marginal_costs) < 1e-8
    assert allocation.shadow_price == pytest.approx(0.1, abs=0.01)
    assert allocation.multipliers[0] == pytest.approx(1.2, abs=0.06)
    assert allocation.multipliers[1] == pytest.approx(1.2, abs=0.06)
    assert allocation.multipliers[2] == pytest.approx(0.63, abs=0.02)


def test_clipped_allocation_respects_bounds_and_budget() -> None:
    buckets = [
        PowerLawBucket(6.5, 0.4, 1.0, 1.5),
        PowerLawBucket(1.63, 0.1, 1.0, 1.5),
        PowerLawBucket(1.19, 0.1, 1.0, 1.5),
    ]
    allocation = allocate_marginal_cost_equalization(buckets, budget=0.6, alpha_bounds=(0.5, 1.5))

    assert all(0.5 <= alpha <= 1.5 for alpha in allocation.multipliers)
    assert allocation.total_cost == pytest.approx(0.6, rel=1e-8)


def test_clipped_allocation_rejects_infeasible_budget() -> None:
    bucket = PowerLawBucket(10.0, 4.0, 0.8, 1.3)
    with pytest.raises(ValueError, match="infeasible"):
        allocate_marginal_cost_equalization([bucket], budget=1.0, alpha_bounds=(0.8, 1.2))


def test_invalid_power_law_elasticities_are_rejected() -> None:
    with pytest.raises(ValueError, match="must exceed"):
        PowerLawBucket(10.0, 4.0, 1.1, 1.1)


def test_arm_mean_power_law_fit_recovers_known_elasticities() -> None:
    rng = np.random.default_rng(23)
    arms = np.tile(np.asarray([0.8, 0.9, 1.0, 1.1, 1.2]), 200)
    rng.shuffle(arms)
    values = 3.0 * arms**0.8
    costs = 0.7 * arms**1.4

    fitted = fit_power_law_bucket(arms, values, costs, population_size=len(arms))

    assert fitted.value_elasticity == pytest.approx(0.8, abs=1e-10)
    assert fitted.cost_elasticity == pytest.approx(1.4, abs=1e-10)
    assert fitted.value_at_one == pytest.approx(3.0 * len(arms), rel=1e-10)
    assert fitted.cost_at_one == pytest.approx(0.7 * len(arms), rel=1e-10)


def test_power_law_fit_allows_nonpositive_rows_when_arm_means_are_positive() -> None:
    arms = np.repeat(np.asarray([0.8, 0.9, 1.0, 1.1, 1.2]), 4)
    values = np.repeat(np.asarray([1.0, 2.0, 3.0, 4.0, 5.0]), 4).astype(float)
    costs = values * 0.5
    values[0] = -1.0
    costs[0] = -0.5

    fitted = fit_power_law_bucket(arms, values, costs, population_size=len(arms), minimum_per_arm=4)

    assert fitted.value_at_one > 0
    assert fitted.cost_at_one > 0


def test_quantile_tree_finds_known_heterogeneous_allocation() -> None:
    rng = np.random.default_rng(51)
    n = 50_000
    features = rng.uniform(size=(n, 1))
    arms = rng.choice(np.asarray([0.8, 0.9, 1.0, 1.1, 1.2]), size=n)
    low_value_cost_ratio = features[:, 0] < 0.5
    base_value = np.where(low_value_cost_ratio, 2.0, 1.0)
    base_cost = np.where(low_value_cost_ratio, 1.0, 0.2)
    values = base_value * arms
    costs = base_cost * arms**1.5

    tree = CuvetQuantileTree(
        max_depth=1,
        candidate_count=1,
        min_samples_leaf=5_000,
        min_samples_per_arm=100,
    ).fit(features, arms, values, costs)
    predictions = tree.predict(np.asarray([[0.25], [0.75]]))

    assert tree._root is not None and tree._root.feature == 0
    assert tree._root.threshold == pytest.approx(0.5, abs=0.01)
    assert np.all((predictions >= 0.8) & (predictions <= 1.2))
    assert predictions[0] != pytest.approx(predictions[1], abs=1e-4)
