import numpy as np
import pytest

from shiftlab.dive.hard_budget_delayed_cams import HardBudgetDelayedCams


class ZeroRandom:
    def random(self) -> float:
        return 0.0


def test_cams_updates_policy_losses_only_on_fixed_delay_release():
    cams = HardBudgetDelayedCams(model_count=2, class_count=2, budget=1, delay=2)
    rng = ZeroRandom()

    first = cams.begin_event("x1", (0, 1), rng=rng)
    assert first.query_requested
    assert first.recommended_model == 0
    cams.submit_queried_label(0)
    np.testing.assert_array_equal(cams.cumulative_policy_loss, (0.0, 0.0))

    second = cams.begin_event("x2", (0, 1), rng=rng)
    assert second.released_labels == 0
    np.testing.assert_array_equal(cams.cumulative_policy_loss, (0.0, 0.0))

    third = cams.begin_event("x3", (0, 1), rng=rng)
    assert third.released_labels == 1
    np.testing.assert_allclose(cams.cumulative_policy_loss, (0.0, 1.0))
    assert third.policy_weights[0] > third.policy_weights[1]


def test_cams_hard_cap_reserves_pending_labels_and_preserves_source_query_floor():
    cams = HardBudgetDelayedCams(model_count=2, class_count=2, budget=2, delay=4)
    rng = ZeroRandom()
    first = cams.begin_event("x1", (0, 1), rng=rng)
    assert first.query_probability == pytest.approx(1.0)
    assert first.query_requested
    cams.submit_queried_label(0)

    second = cams.begin_event("x2", (0, 1), rng=rng)
    assert second.query_probability >= 1 / np.sqrt(2)
    assert second.query_requested
    cams.submit_queried_label(1)

    third = cams.begin_event("x3", (0, 1), rng=rng)
    assert third.query_probability == 0
    assert not third.query_requested
    assert third.requests_used == 2
    assert third.pending_labels == 2
    assert cams.remaining_budget == 0

    cams.begin_event("x4", (0, 1), rng=rng)
    fifth = cams.begin_event("x5", (0, 1), rng=rng)
    assert fifth.released_labels == 1
    assert cams.pending_labels == 1
    sixth = cams.begin_event("x6", (0, 1), rng=rng)
    assert sixth.released_labels == 1
    assert cams.pending_labels == 0


def test_contextual_policy_and_constant_experts_are_aggregated():
    policy = lambda context: (1.0, 0.0) if context == "left" else (0.0, 1.0)
    cams = HardBudgetDelayedCams(
        model_count=2, class_count=2, budget=0, delay=1, policies=(policy,)
    )
    left = cams.begin_event("left", (0, 1), rng=ZeroRandom())
    right = cams.begin_event("right", (0, 1), rng=ZeroRandom())
    assert left.recommended_model == 0
    assert right.recommended_model == 1
    assert len(left.policy_weights) == 3
    assert left.query_probability == 0


def test_cams_query_submission_lifecycle_and_label_validation():
    cams = HardBudgetDelayedCams(model_count=2, class_count=2, budget=1, delay=1)
    decision = cams.begin_event("x", (0, 1), rng=ZeroRandom())
    assert decision.query_requested
    with pytest.raises(RuntimeError, match="before the next event"):
        cams.begin_event("x2", (0, 1), rng=ZeroRandom())
    with pytest.raises(ValueError, match="class index"):
        cams.submit_queried_label(2)
    cams.submit_queried_label(1)
    with pytest.raises(RuntimeError, match="no requested label"):
        cams.submit_queried_label(0)
