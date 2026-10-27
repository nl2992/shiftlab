import numpy as np
import pytest

from shiftlab.dive.stratified_harm_allocation import (
    minimax_support_allocation,
    minimax_uncapped_allocation,
)


@pytest.mark.parametrize("power", [1, 2])
def test_support_allocation_matches_unconstrained_closed_form(power):
    coefficients = np.array([1.2, 0.8, 2.1])
    frequency = np.array([0.2, 0.3, 0.25])  # omitted mass can be an agreement stratum
    tariff = np.array([1.4, 0.7, 1.1])
    budget = 0.3
    q, modeled_time = minimax_support_allocation(
        coefficients, frequency, tariff, budget, power=power
    )

    if power == 1:
        expected_q = budget * coefficients / (frequency * np.dot(tariff, coefficients))
        expected_time = np.dot(tariff, coefficients) / budget
    else:
        expected_q = (
            budget
            * np.sqrt(coefficients / frequency)
            / np.dot(tariff, np.sqrt(frequency * coefficients))
        )
        expected_time = (np.dot(tariff, np.sqrt(frequency * coefficients)) / budget) ** 2

    np.testing.assert_allclose(q, expected_q, rtol=1e-9, atol=1e-10)
    assert modeled_time == pytest.approx(expected_time, rel=1e-9)
    np.testing.assert_allclose(coefficients / (frequency * q**power), modeled_time, rtol=1e-9)
    assert np.dot(frequency * tariff, q) == pytest.approx(budget)


def test_support_allocation_honors_floor_that_binds_and_budget():
    frequency = np.array([0.5, 0.5])
    tariff = np.ones(2)
    q, modeled_time = minimax_support_allocation(
        np.array([1.0, 4.0]),
        frequency,
        tariff,
        0.35,
        power=2,
        floors=np.array([0.3, 0.1]),
        caps=np.array([0.6, 0.6]),
    )
    assert q[0] == pytest.approx(0.3)
    assert q[1] == pytest.approx(0.4)
    assert modeled_time == pytest.approx(50.0)
    assert np.dot(frequency * tariff, q) <= 0.35


def test_support_allocation_returns_caps_when_budget_covers_them():
    q, modeled_time = minimax_support_allocation(
        np.array([1.0, 2.0]),
        np.array([0.4, 0.4]),
        np.ones(2),
        0.5,
        floors=0.1,
        caps=np.array([0.5, 0.75]),
    )
    np.testing.assert_array_equal(q, np.array([0.5, 0.75]))
    assert modeled_time == pytest.approx(max(1 / (0.4 * 0.5), 2 / (0.4 * 0.75)))


@pytest.mark.parametrize("power", [1, 2])
def test_support_allocation_handles_tiny_budget(power):
    coefficients = np.array([1.0, 2.0])
    frequency = np.array([0.5, 0.5])
    budget = 1e-20
    q, modeled_time = minimax_support_allocation(
        coefficients, frequency, np.ones(2), budget, power=power
    )

    assert np.isfinite(q).all()
    assert np.all(q > 0)
    assert np.dot(frequency, q) <= budget * (1 + 1e-12)
    np.testing.assert_allclose(coefficients / (frequency * q**power), modeled_time, rtol=1e-12)


@pytest.mark.parametrize("power", [1, 2])
def test_support_allocation_returns_minimum_time_at_asymmetric_cap_bottleneck(power):
    coefficients = np.array([1.0, 100.0])
    frequency = np.array([0.5, 0.5])
    caps = np.array([1.0, 0.2])
    minimum_time = float(np.max(coefficients / (frequency * caps**power)))
    required = (coefficients / (frequency * minimum_time)) ** (1 / power)
    budget = 0.3

    # The full-cap allocation costs 0.6, while the minimum-time allocation
    # costs less than the budget because the second stratum sets the bottleneck.
    assert np.dot(frequency, caps) > budget
    assert np.dot(frequency, required) < budget
    q, modeled_time = minimax_support_allocation(
        coefficients, frequency, np.ones(2), budget, power=power, caps=caps
    )

    np.testing.assert_allclose(q, required)
    assert modeled_time == pytest.approx(minimum_time)


def test_support_allocation_rejects_infeasible_floor_spend():
    with pytest.raises(ValueError, match="floor allocation"):
        minimax_support_allocation(
            np.array([1.0, 2.0]),
            np.array([0.5, 0.5]),
            np.array([1.0, 2.0]),
            0.2,
            floors=np.array([0.2, 0.2]),
        )


def test_uncapped_allocation_equalizes_times_with_negative_offsets():
    offset = np.array([-0.4, 0.2, -0.1])
    inverse_query = np.array([0.8, 0.5, 0.7])
    frequency = np.array([0.4, 0.35, 0.25])
    tariff = np.array([1.5, 0.8, 1.2])
    budget = 0.25
    q, modeled_time = minimax_uncapped_allocation(offset, inverse_query, frequency, tariff, budget)
    np.testing.assert_allclose(offset + inverse_query / q, modeled_time, rtol=1e-9, atol=1e-9)
    assert np.dot(frequency * tariff, q) == pytest.approx(budget, abs=1e-10)
    assert np.all(q > 0)


def test_uncapped_allocation_handles_tiny_budget():
    offset = np.array([-0.4, 0.2])
    inverse_query = np.array([0.8, 0.5])
    frequency = np.array([0.5, 0.5])
    budget = 1e-20
    q, modeled_time = minimax_uncapped_allocation(
        offset, inverse_query, frequency, np.ones(2), budget
    )

    assert np.isfinite(q).all()
    assert np.all(q > 0)
    assert np.dot(frequency, q) <= budget * (1 + 1e-12)
    np.testing.assert_allclose(offset + inverse_query / q, modeled_time, rtol=1e-12)


def test_uncapped_allocation_returns_minimum_time_at_asymmetric_cap_bottleneck():
    offset = np.array([0.0, 0.0])
    inverse_query = np.array([1.0, 100.0])
    frequency = np.array([0.5, 0.5])
    caps = np.array([1.0, 0.2])
    minimum_time = float(np.max(offset + inverse_query / caps))
    required = inverse_query / (minimum_time - offset)
    budget = 0.3

    assert np.dot(frequency, caps) > budget
    assert np.dot(frequency, required) < budget
    q, modeled_time = minimax_uncapped_allocation(
        offset, inverse_query, frequency, np.ones(2), budget, caps=caps
    )

    np.testing.assert_allclose(q, required)
    assert modeled_time == pytest.approx(minimum_time)


def test_uncapped_allocation_honors_floor_and_upper_cap():
    offset = np.array([-0.5, 0.1])
    inverse_query = np.array([0.6, 0.9])
    frequency = np.array([0.5, 0.5])
    tariff = np.ones(2)
    q, modeled_time = minimax_uncapped_allocation(
        offset,
        inverse_query,
        frequency,
        tariff,
        0.35,
        floors=np.array([0.3, 0.1]),
        caps=np.array([0.7, 0.8]),
    )
    assert q[0] >= 0.3
    assert q[1] <= 0.8
    assert np.dot(frequency * tariff, q) <= 0.35
    assert modeled_time == pytest.approx(max(offset + inverse_query / q))


def test_uncapped_allocation_rejects_infeasible_floor_spend():
    with pytest.raises(ValueError, match="floor allocation"):
        minimax_uncapped_allocation(
            np.array([-0.2, 0.3]),
            np.array([0.5, 1.0]),
            np.array([0.5, 0.5]),
            np.array([1.0, 2.0]),
            0.2,
            floors=np.array([0.2, 0.2]),
        )


@pytest.mark.parametrize(
    "call",
    [
        lambda: minimax_support_allocation([0, 1], [0.5, 0.5], [1, 1], 0.2),
        lambda: minimax_support_allocation([1], [1.1], [1], 0.2),
        lambda: minimax_support_allocation([1], [1], [1], 0.2, power=3),
        lambda: minimax_support_allocation([1], [1], [1], 0.2, caps=0),
        lambda: minimax_uncapped_allocation([0], [0], [1], [1], 0.2),
        lambda: minimax_uncapped_allocation([0], [1], [1], [1], 0.2, floors=1.1),
    ],
)
def test_allocators_reject_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
