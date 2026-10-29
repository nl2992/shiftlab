import numpy as np
import pytest

from shiftlab.dive.stratified_harm_design import (
    binary_outcome_probability,
    null_centered_means,
    pilot_alpha_weights,
)


@pytest.mark.parametrize("dtype", [bool, np.uint8])
def test_binary_action_storage_type_does_not_change_cost_orientation(dtype):
    result = binary_outcome_probability(
        np.array([0, 1], dtype=dtype),
        np.array([1, 0], dtype=dtype),
        5.0,
        1.0,
        0.1,
        [0.0, 0.0],
    )
    np.testing.assert_allclose(result, [1.1 / 6, 0.9 / 6], atol=1e-12)


def test_pilot_weights_match_existing_two_stratum_contract_and_generalize():
    weights = pilot_alpha_weights([480, 20])
    assert set(weights) == {
        "equal_alpha",
        "volume_weighted_alpha",
        "rare_protected_alpha",
    }
    expected_volume = (np.array([480.0, 20.0]) + 0.5) / 501.0
    expected_rare = 1.0 / (np.array([480.0, 20.0]) + 0.5)
    expected_rare /= expected_rare.sum()
    np.testing.assert_array_equal(weights["equal_alpha"], [0.5, 0.5])
    np.testing.assert_allclose(weights["volume_weighted_alpha"], expected_volume, rtol=0, atol=0)
    np.testing.assert_allclose(weights["rare_protected_alpha"], expected_rare, rtol=0, atol=0)

    general = pilot_alpha_weights([10, 0, 2, 7])
    for allocation in general.values():
        assert allocation.shape == (4,)
        assert np.all(allocation > 0)
        assert np.isclose(allocation.sum(), 1.0)
    assert general["rare_protected_alpha"][1] > general["equal_alpha"][1]


@pytest.mark.parametrize(
    ("action", "reference", "expected_probability"),
    [(0, 1, (1.0 + 0.2) / 6.0), (1, 0, (1.0 - 0.2) / 6.0)],
)
def test_binary_probability_gives_null_paired_mean_for_both_action_orientations(
    action, reference, expected_probability
):
    epsilon = 0.2
    probability = binary_outcome_probability(
        action,
        reference,
        false_negative_cost=5.0,
        false_positive_cost=1.0,
        epsilon=epsilon,
        centered_mean=0.0,
    )
    assert float(probability) == pytest.approx(expected_probability)

    y0_gross = 1.0 * (action - reference)
    y1_gross = 5.0 * (reference - action)
    enumerated_mean = (1.0 - float(probability)) * (y0_gross - epsilon) + float(probability) * (
        y1_gross - epsilon
    )
    assert enumerated_mean == pytest.approx(0.0, abs=1e-12)


def test_mixed_sign_stratum_means_can_cancel_under_fixed_weights():
    actions = np.array([0, 1])
    references = np.array([1, 0])
    requested_means = np.array([0.4, -0.4])
    weights = np.array([0.5, 0.5])
    probability = binary_outcome_probability(
        actions,
        references,
        false_negative_cost=5.0,
        false_positive_cost=1.0,
        epsilon=0.1,
        centered_mean=requested_means,
    )
    z0 = 1.0 * (actions - references)
    z1 = 5.0 * (references - actions)
    enumerated_means = (1.0 - probability) * (z0 - 0.1) + probability * (z1 - 0.1)
    np.testing.assert_allclose(enumerated_means, requested_means, rtol=0, atol=1e-12)
    assert np.dot(weights, enumerated_means) == pytest.approx(0.0, abs=1e-12)


def test_null_mean_helper_uses_zero_for_disagreement_and_negative_margin_for_agreement():
    actions = np.array([0, 1, 1])
    references = np.array([1, 0, 1])
    epsilon = 0.15
    means = null_centered_means(actions, references, epsilon)
    np.testing.assert_array_equal(means, [0.0, 0.0, -epsilon])
    probabilities = binary_outcome_probability(
        actions,
        references,
        false_negative_cost=5.0,
        false_positive_cost=1.0,
        epsilon=epsilon,
        centered_mean=means,
    )
    assert probabilities[2] == 0.5


@pytest.mark.parametrize(
    "counts",
    [[], [[1, 2]], [0, 0], [1.5, 2], [-1, 2], [np.inf, 1], [np.nan, 1], ["x", 1]],
)
def test_pilot_weights_reject_invalid_counts(counts):
    with pytest.raises(ValueError):
        pilot_alpha_weights(counts)


def test_binary_probability_rejects_infeasible_and_invalid_inputs():
    with pytest.raises(ValueError, match="infeasible outcome probability"):
        binary_outcome_probability(0, 1, 5, 1, epsilon=0.1, centered_mean=10.0)
    with pytest.raises(ValueError, match="constant paired cost"):
        binary_outcome_probability(1, 1, 5, 1, epsilon=0.1, centered_mean=0.0)
    with pytest.raises(ValueError, match="binary"):
        binary_outcome_probability(2, 1, 5, 1, epsilon=0.1, centered_mean=0.0)
    with pytest.raises(ValueError, match="nonnegative"):
        binary_outcome_probability(0, 1, 5, -1, epsilon=0.1, centered_mean=0.0)
    with pytest.raises(ValueError, match="broadcast-compatible"):
        binary_outcome_probability([0, 1], [1, 0], 5, 1, epsilon=0.1, centered_mean=[0.0, 0.0, 0.0])
