import pytest

from shiftlab.data.streaming import (
    DecisionFeedback,
    DecisionRequest,
    OracleDecisionRecord,
    PolicyDecision,
    replay_decision_stream,
)


def _request(sample_id, time):
    return DecisionRequest(
        sample_id=sample_id,
        event_time=time,
        feature_available_time=time,
        prediction_time=time,
        features=(0.25, -0.5),
        entity_id="unit-1",
        domain_id="synthetic",
        decision_context='{"false_negative": 5, "false_positive": 1}',
        policy_version="deployed-v1",
        reference_policy_version="fallback-v1",
        decision_cost_version="binary-fn-fp-v1",
    )


def _decision(sample_id, time, *, query=True):
    return PolicyDecision(
        sample_id=sample_id,
        action_time=time,
        action=1,
        reference_action=0,
        query_label=query,
        query_probability=1.0 if query else None,
    )


def test_decision_replay_keeps_oracle_separate_and_orders_delayed_feedback():
    requests = [_request("a", 1), _request("b", 1), _request("c", 2)]
    decisions = [_decision("a", 1), _decision("b", 1), _decision("c", 2)]
    labels = [
        DecisionFeedback("a", label_event_time=1, available_time=3, target=1.0),
        DecisionFeedback("b", label_event_time=1, available_time=1, target=-1.0),
        DecisionFeedback("c", label_event_time=2, available_time=4, target=1.0),
    ]
    oracle = OracleDecisionRecord(
        sample_id="a",
        regime_id="hidden-regime",
        true_probability_positive=0.8,
        oracle_action=1,
        oracle_expected_cost=0.2,
        deployed_expected_cost=1.0,
        reference_expected_cost=4.0,
        true_change_time=10,
    )
    events = list(replay_decision_stream(requests, decisions, labels))
    assert [type(event).__name__ for event in events[:7]] == [
        "DecisionRequest",
        "PolicyDecision",
        "DecisionRequest",
        "PolicyDecision",
        "DecisionFeedback",
        "DecisionRequest",
        "PolicyDecision",
    ]
    assert [event.sample_id for event in events if isinstance(event, DecisionFeedback)] == [
        "b",
        "a",
        "c",
    ]
    visible_requests = [event for event in events if isinstance(event, DecisionRequest)]
    assert all(
        not hasattr(event, "target") and not hasattr(event, "regime_id")
        for event in visible_requests
    )
    assert not hasattr(oracle, "features")


def test_decision_replay_rejects_feedback_without_a_logged_query():
    with pytest.raises(ValueError, match="not queried"):
        list(
            replay_decision_stream(
                [_request("a", 1)],
                [_decision("a", 1, query=False)],
                [DecisionFeedback("a", 1, 1, 1.0)],
            )
        )


def test_decision_contract_rejects_future_features_and_invalid_cost_versions():
    with pytest.raises(ValueError, match="feature_available_time"):
        DecisionRequest("a", 1, 2, 1, (0.0,), None, None, None, "v1", "ref1", "cost1")
    with pytest.raises(ValueError, match="version"):
        DecisionRequest("a", 1, 1, 1, (0.0,), None, None, None, "", "ref1", "cost1")


def test_logged_query_requires_a_positive_propensity():
    with pytest.raises(ValueError, match="positive logged propensity"):
        PolicyDecision("a", 1, 1, 0, True, 0.0)
