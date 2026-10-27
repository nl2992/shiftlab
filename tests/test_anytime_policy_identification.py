import numpy as np
import pytest

from shiftlab.dive.anytime_policy_identification import (
    bounded_dr_pseudo_outcomes,
    lil_value_bounds,
    optimal_policy_set,
    optimal_policy_stopping_time,
)


def test_truncated_dr_pseudo_outcomes_have_correct_conditional_means() -> None:
    h = np.array([[0.5, 0.5]])
    policies = np.array([[1.0, 0.0], [0.5, 0.5], [0.0, 1.0]])
    predictions = np.array([[0.8, 0.4]])
    expected_lower = np.zeros(3)
    expected_upper = np.zeros(3)
    for action in (0, 1):
        action_mean = 0.3 if action == 0 else 0.7
        for reward, reward_probability in (
            (0.0, 1.0 - action_mean),
            (1.0, action_mean),
        ):
            probability = 0.5 * reward_probability
            lower, upper = bounded_dr_pseudo_outcomes(
                np.array([action]),
                np.array([reward]),
                h,
                policies,
                predictions,
                truncation=1.0,
            )
            expected_lower += probability * lower[0]
            expected_upper += probability * upper[0]
    np.testing.assert_allclose(expected_lower, [0.3, 0.5, 0.7], atol=1e-12)
    np.testing.assert_allclose(expected_upper, [0.7, 0.5, 0.3], atol=1e-12)


def test_target_action_without_logging_support_is_rejected() -> None:
    with pytest.raises(ValueError, match="not supported"):
        bounded_dr_pseudo_outcomes(
            actions=np.array([0]),
            rewards=np.array([0.0]),
            logging_probabilities=np.array([[1.0, 0.0]]),
            target_policies=np.array([[0.0, 1.0]]),
            reward_predictions=np.array([[0.2, 0.8]]),
            truncation=1.0,
        )


def test_lil_bounds_are_finite_and_value_bounded() -> None:
    phi = np.array([-0.25, 0.5, 1.25, 0.5] * 25, dtype=float)
    lower = lil_value_bounds(phi, alpha=0.025, truncation=1.0)
    assert lower.shape == phi.shape
    assert np.all(np.isfinite(lower))
    assert np.all((lower >= 0.0) & (lower <= 1.0))


def test_lil_rejects_scores_outside_the_theorem_lower_bound() -> None:
    with pytest.raises(ValueError, match="lower bound"):
        lil_value_bounds(np.array([-1.01]), alpha=0.05, truncation=1.0)


def test_policy_set_and_strict_stopping_rule() -> None:
    lower = np.array([[0.2, 0.5], [0.2, 0.1]])
    upper = np.array([[0.8, 0.9], [0.8, 0.4]])
    candidate_set = optimal_policy_set(lower, upper)
    assert candidate_set[:, 0].tolist() == [True, True]
    assert candidate_set[:, 1].tolist() == [True, False]
    assert optimal_policy_stopping_time(lower, upper) == 2
    assert optimal_policy_stopping_time(lower[:, :1], upper[:, :1]) == 2


def test_single_policy_does_not_claim_pairwise_identification() -> None:
    assert optimal_policy_stopping_time(np.array([[0.4, 0.5]]), np.array([[0.8, 0.7]])) == 3
