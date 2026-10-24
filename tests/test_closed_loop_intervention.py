import numpy as np

from shiftlab.dive.closed_loop_intervention import _simulate_gate
from shiftlab.dive.controller import CertifiedPromotionRollback, Intervention


def test_vectorized_gate_matches_public_controller_and_respects_total_budget():
    horizon = 100
    gains = np.concatenate((np.full(horizon, 0.9), np.full(horizon, -0.9)))[None, :]
    query_uniforms = np.zeros_like(gains)
    promotion_cost = rollback_cost = 0.05
    query_rate = 1.0
    gate = _simulate_gate(
        gains,
        query_uniforms,
        query_rate=query_rate,
        label_budget=200,
        alpha=0.05,
        promotion_cost=promotion_cost,
        rollback_cost=rollback_cost,
        horizon=horizon,
    )

    controller = CertifiedPromotionRollback(
        promotion_bound=1 + promotion_cost / horizon,
        rollback_bound=1 + rollback_cost / horizon,
        deployment_horizon=horizon,
        promotion_cost=promotion_cost,
        rollback_cost=rollback_cost,
        alpha_total=0.05,
    )
    promotion_time = None
    for event in range(horizon):
        step = controller.observe_shadow(
            event_index=event,
            estimated_gain=gains[0, event],
            queried=True,
        )
        if step.action == Intervention.PROMOTE:
            promotion_time = event
            break
    assert promotion_time == gate["promotion_time"][0]

    rollback_time = None
    for elapsed in range(horizon):
        event = horizon + elapsed
        step = controller.observe_deployment(
            event_index=event,
            estimated_gain=gains[0, event],
            queried=True,
        )
        if step.action == Intervention.FALLBACK:
            rollback_time = elapsed
            break
    assert rollback_time == gate["rollback_time"][0]
    assert gate["labels_queried"][0] <= 200
    assert (
        gate["shadow_labels_queried"][0] + gate["deployment_labels_queried"][0]
        == gate["labels_queried"][0]
    )


def test_vectorized_gate_stops_querying_at_total_label_cap():
    horizon = 100
    gains = np.zeros((2, 2 * horizon), dtype=float)
    query_uniforms = np.zeros_like(gains)
    gate = _simulate_gate(
        gains,
        query_uniforms,
        query_rate=1.0,
        label_budget=10,
        alpha=0.05,
        promotion_cost=0.05,
        rollback_cost=0.05,
        horizon=horizon,
    )
    assert gate["labels_queried"].tolist() == [10, 10]
    assert gate["shadow_labels_queried"].tolist() == [10, 10]
    assert gate["deployment_labels_queried"].tolist() == [0, 0]
    assert not gate["promoted"].any()
    assert gate["budget_respected"].all()
