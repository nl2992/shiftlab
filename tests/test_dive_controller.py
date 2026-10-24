import pytest

from shiftlab.dive.controller import (
    ActionEstimate,
    CertifiedPromotionRollback,
    Intervention,
    InterventionController,
)


def test_promotion_never_overrides_missing_certificate():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.PROMOTE: ActionEstimate(10.0, switching_cost=0.1),
    }
    assert InterventionController().choose(estimates) == Intervention.CONTINUE
    assert (
        InterventionController().choose(estimates, promotion_certified=True) == Intervention.PROMOTE
    )


def test_controller_accounts_for_label_compute_and_switching_costs():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.QUERY: ActionEstimate(0.2, label_cost=0.05),
        Intervention.RETRAIN: ActionEstimate(0.5, compute_cost=0.1, switching_cost=0.6),
    }
    assert InterventionController().choose(estimates) == Intervention.QUERY


def test_controller_does_not_take_actions_with_negative_net_value():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.QUERY: ActionEstimate(0.01, label_cost=0.05),
    }
    assert InterventionController().choose(estimates) == Intervention.CONTINUE


def test_certified_promotion_rollback_requires_promotion_and_then_falls_back():
    controller = CertifiedPromotionRollback(
        promotion_bound=1.0,
        rollback_bound=1.0,
        deployment_horizon=100,
        promotion_cost=0.05,
        rollback_cost=0.05,
        alpha_total=0.05,
    )
    with pytest.raises(ValueError, match="certified"):
        controller.observe_deployment(event_index=100, estimated_gain=-0.9, queried=True)

    for event_index in range(100):
        step = controller.observe_shadow(
            event_index=event_index,
            estimated_gain=0.9,
            queried=event_index % 2 == 0,
        )
        if step.action == Intervention.PROMOTE:
            break
    assert controller.promoted
    assert controller.promotion_event == event_index

    for deployment_index in range(100, 200):
        step = controller.observe_deployment(
            event_index=deployment_index,
            estimated_gain=-0.9,
            queried=deployment_index % 2 == 0,
        )
        if step.action == Intervention.FALLBACK:
            break
    assert controller.rolled_back
    assert controller.rollback_event == deployment_index
    with pytest.raises(ValueError, match="after fallback"):
        controller.observe_deployment(
            event_index=deployment_index + 1,
            estimated_gain=0.9,
            queried=True,
        )


def test_certified_promotion_rollback_preserves_continue_on_no_evidence():
    controller = CertifiedPromotionRollback(
        promotion_bound=1.0,
        rollback_bound=1.0,
        deployment_horizon=20,
        promotion_cost=0.1,
        rollback_cost=0.1,
    )
    for event_index in range(10):
        step = controller.observe_shadow(
            event_index=event_index,
            estimated_gain=0.0,
            queried=False,
        )
        assert step.action == Intervention.CONTINUE
        assert not step.queried
    assert not controller.promoted
    with pytest.raises(ValueError, match="must sum"):
        CertifiedPromotionRollback(
            promotion_bound=1.0,
            rollback_bound=1.0,
            deployment_horizon=20,
            promotion_cost=0.1,
            rollback_cost=0.1,
            alpha_total=0.05,
            promotion_alpha=0.03,
            rollback_alpha=0.03,
        )
