import numpy as np
import pytest

from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.adaptation import (
    ComputeBudget,
    gaussian_interval_score_expectation,
    interval_recalibration_reference,
    intervention_reference,
    oblivious_change_times,
)
from shiftlab.data.synthetic.generators import generate_chunks, schedule


def test_budget_charges_atomic_and_distinct_from_loss_cost():
    budget = ComputeBudget(5)
    assert budget.charge(3)
    assert not budget.charge(3)
    assert budget.remaining == 2
    assert budget.charge(2)
    assert budget.remaining == 0
    with pytest.raises(ValueError):
        budget.charge(np.nan)


def test_oracle_reference_matches_enumerated_counterfactuals():
    rng = np.random.default_rng(42)
    stale, updated = rng.uniform(1, 4, (2, 30))
    result = intervention_reference(
        stale,
        updated,
        horizon=9,
        update_cost=0.5,
        resource_cost=2,
        remaining_budget=3,
        deployment_delay=2,
        transient_penalties=[3, 2, 1],
    )
    for t, row in result.iterrows():
        end = min(t + 9, 30)
        deploy = min(t + 2, end)
        expected = (
            stale[t:deploy].sum() + updated[deploy:end].sum() + sum([3, 2, 1][: end - deploy]) + 0.5
        )
        assert row.update_expected_loss == pytest.approx(expected)
        assert row.hold_expected_loss == pytest.approx(stale[t:end].sum())


def test_gaussian_interval_score_expectation_matches_monte_carlo():
    rng = np.random.default_rng(102)
    sigma, radius, alpha = 1.7, 2.1, 0.1
    residual = rng.normal(scale=sigma, size=500_000)
    empirical = 2 * radius + (2 / alpha) * np.maximum(np.abs(residual) - radius, 0)
    expected = gaussian_interval_score_expectation(sigma, radius, alpha)
    assert np.mean(empirical) == pytest.approx(float(expected), abs=0.04)


def test_interval_recalibration_reference_uses_interval_score_units():
    sigma = np.array([0.3, 0.3, 0.9, 0.9])
    z = 1.6448536269514722
    stale = gaussian_interval_score_expectation(sigma, 0.3 * z)
    recalibrated = gaussian_interval_score_expectation(sigma, 0.9 * z)
    result = interval_recalibration_reference(
        stale,
        recalibrated,
        horizon=4,
        update_cost=0,
        resource_cost=1,
        remaining_budget=1,
    )
    assert "hold_expected_interval_score" in result
    assert "recalibrated_expected_interval_score" in result
    assert result.attrs["loss"] == "expected central Gaussian Winkler interval score"
    assert result.oracle_action.iloc[0] == "update"


def test_update_can_temporarily_hurt_then_help_and_budget_blocks():
    short = intervention_reference(np.ones(20), np.zeros(20), horizon=2, transient_penalties=[4, 2])
    long = intervention_reference(np.ones(20), np.zeros(20), horizon=10, transient_penalties=[4, 2])
    assert short.oracle_action.iloc[0] == "hold"
    assert long.oracle_action.iloc[0] == "update"
    blocked = intervention_reference(np.ones(20), np.zeros(20), resource_cost=2, remaining_budget=1)
    assert (blocked.oracle_action == "hold").all()
    assert (blocked.net_update_benefit > 0).all()


def test_adversarial_schedule_fixed_ex_ante_and_zero_strength_null():
    config = SyntheticConfig(
        n=1000, scenario="concept", pattern="oblivious_adversarial", review_period=100
    )
    expected = np.array([501, 601, 701, 801, 901])
    np.testing.assert_array_equal(oblivious_change_times(1000, 100, 500), expected)
    _, truth = schedule(config)
    assert truth["change_times"] == expected.tolist()
    w, truth = schedule(config.model_copy(update={"severity": 0}))
    assert not w.any() and not truth["change_times"]


def test_fixed_predictor_analytic_risks_match_independent_generated_losses():
    config = SyntheticConfig(n=50000, d=2, scenario="concept", severity=2, seed=123)
    losses, weights = [], []
    for frame, oracle in generate_chunks(config):
        X = np.stack(frame.features.to_numpy())
        target = frame.target.to_numpy()
        stale = X[:, 0] - 0.9 * X[:, 1]
        updated = -X[:, 0] - 0.9 * X[:, 1]
        losses.append(np.column_stack([(target - stale) ** 2, (target - updated) ** 2]))
        weights.append(oracle.weight.to_numpy())
    losses, weights = np.concatenate(losses), np.concatenate(weights)
    for regime in [0, 1]:
        observed = losses[weights == regime].mean(axis=0)
        expected = [config.noise**2 + (2 * regime) ** 2, config.noise**2 + (2 * (1 - regime)) ** 2]
        np.testing.assert_allclose(observed, expected, atol=0.15)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizon": 0},
        {"deployment_delay": -1},
        {"update_cost": -1},
        {"remaining_budget": np.nan},
        {"transient_penalties": [-1]},
    ],
)
def test_invalid_reference_parameters(kwargs):
    with pytest.raises(ValueError):
        intervention_reference([1, 1], [0, 0], **kwargs)
