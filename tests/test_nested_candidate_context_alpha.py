import numpy as np
import pytest

from shiftlab.dive.nested_candidate_context_alpha import (
    METHODS,
    nested_alpha_weights,
    simulate_block,
)


def test_nested_candidate_context_weights_compose_to_familywise_alpha():
    order = np.array([4, 1, 0, 3, 2])
    allocations = nested_alpha_weights(order, np.array([80, 20]), alpha=0.05)

    assert set(allocations) == set(METHODS)
    assert allocations["rank_only"].sum() <= 0.05
    assert allocations["nested_equal"].sum() <= 0.05
    assert allocations["nested_volume"].sum() <= 0.05
    np.testing.assert_allclose(allocations["nested_equal"].sum(axis=1), allocations["rank_only"])
    np.testing.assert_allclose(allocations["nested_volume"].sum(axis=1), allocations["rank_only"])
    np.testing.assert_allclose(
        allocations["nested_volume"][:, 0] / allocations["rank_only"], 80.5 / 101
    )


@pytest.mark.parametrize("counts", [np.array([0, 0]), np.array([-1, 4]), np.array([1, np.nan])])
def test_nested_candidate_context_weights_reject_invalid_pilot_counts(counts):
    with pytest.raises(ValueError):
        nested_alpha_weights(np.array([0, 1]), counts)


def test_cpu_smoke_respects_budget_and_reports_all_paired_methods():
    result = simulate_block(
        profile="specialists",
        seeds=3,
        seed=124_999_001,
        prevalence=0.1,
        proxy_error=0.05,
        budget_rate=0.2,
        device="cpu",
    )

    assert set(result.method) == set(METHODS)
    assert len(result) == 3 * len(METHODS)
    assert result.hard_cap_respected.all()
    assert (result.labels_queried <= result.label_budget).all()
