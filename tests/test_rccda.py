import pytest

from shiftlab.dive.rccda import RCCDAState


def test_rccda_uses_previous_loss_and_updates_virtual_queue():
    state = RCCDAState(
        update_cost=1.0,
        average_update_budget=0.1,
        tradeoff=10.0,
        proportional_gain=1.0,
        derivative_gain=1.0,
    )
    result = state.decide(
        current_loss=0.3,
        previous_loss=0.1,
        best_observed_loss=0.1,
    )

    assert result.estimated_gain == pytest.approx(0.4)
    assert result.threshold == pytest.approx(0.4)
    assert result.update is True  # Paper rule uses >= at equality.
    assert result.queue_before == pytest.approx(0.0)
    assert result.queue_after == pytest.approx(0.9)


def test_rccda_no_update_releases_average_resource_debt():
    state = RCCDAState(average_update_budget=0.2)
    state.queue = 0.5
    result = state.decide(
        current_loss=0.2,
        previous_loss=0.2,
        best_observed_loss=0.2,
    )

    assert result.update is False
    assert result.queue_after == pytest.approx(0.3)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"update_cost": 0},
        {"average_update_budget": 0},
        {"tradeoff": 0},
        {"proportional_gain": -1},
        {"derivative_gain": float("nan")},
    ],
)
def test_rccda_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        RCCDAState(**kwargs)


def test_rccda_rejects_best_loss_above_current_loss():
    state = RCCDAState()
    with pytest.raises(ValueError, match="best_observed_loss"):
        state.decide(
            current_loss=0.2,
            previous_loss=0.3,
            best_observed_loss=0.25,
        )
