import random

import numpy as np
import pytest

from shiftlab.dive.hard_budget_delayed_online_picker import HardBudgetDelayedOnlinePicker


def test_label_updates_only_when_fixed_delay_expires():
    picker = HardBudgetDelayedOnlinePicker(model_count=2, budget=1, delay=2, beta=0.9, epsilon=0.5)
    first = picker.begin_event((0, 1), rng=random.Random(2))
    assert first.query_requested
    picker.submit_queried_losses((0.0, 1.0))
    np.testing.assert_array_equal(picker.cumulative_loss, (0.0, 0.0))

    second = picker.begin_event((0, 1), rng=random.Random(2))
    assert second.released_labels == 0
    np.testing.assert_array_equal(picker.cumulative_loss, (0.0, 0.0))

    third = picker.begin_event((0, 1), rng=random.Random(2))
    assert third.released_labels == 1
    np.testing.assert_allclose(picker.cumulative_loss, (0.0, 1.0))
    assert third.recommended_model == 0


def test_pathwise_cap_reserves_pending_requests_at_request_time():
    picker = HardBudgetDelayedOnlinePicker(model_count=2, budget=2, delay=4, beta=0.9, epsilon=1e-8)
    rng = random.Random(0)
    first = picker.begin_event((0, 1), rng=rng)
    assert first.query_requested
    picker.submit_queried_losses((0.0, 1.0))
    second = picker.begin_event((0, 1), rng=rng)
    assert second.query_requested
    picker.submit_queried_losses((1.0, 0.0))

    third = picker.begin_event((0, 1), rng=rng)
    assert not third.query_requested
    assert third.query_probability == 0
    assert third.requests_used == 2
    assert third.pending_labels == 2
    assert picker.remaining_budget == 0

    for _ in range(2):
        picker.begin_event((0, 1), rng=rng)
    assert picker.pending_labels == 1
    sixth = picker.begin_event((0, 1), rng=rng)
    assert sixth.released_labels == 1
    assert picker.pending_labels == 0


def test_identical_candidate_outputs_never_trigger_queries():
    picker = HardBudgetDelayedOnlinePicker(model_count=2, budget=3, delay=1)
    decision = picker.begin_event(("same", "same"), rng=random.Random(0))
    assert not decision.query_requested
    assert decision.query_probability == 0
    assert decision.requests_used == 0


def test_query_label_lifecycle_and_loss_validation():
    picker = HardBudgetDelayedOnlinePicker(model_count=2, budget=1, delay=1)
    decision = picker.begin_event((0, 1), rng=random.Random(0))
    assert decision.query_requested
    with pytest.raises(RuntimeError, match="before the next event"):
        picker.begin_event((0, 1), rng=random.Random(0))
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        picker.submit_queried_losses((0.0, 2.0))
    picker.submit_queried_losses((0.0, 1.0))
    with pytest.raises(RuntimeError, match="no requested label"):
        picker.submit_queried_losses((0.0, 1.0))
