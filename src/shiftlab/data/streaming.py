"""Capability-style messages. This is API separation, not a hostile-code sandbox."""

import heapq
from collections.abc import Iterator
from dataclasses import dataclass
from math import isfinite

import pandas as pd


@dataclass(frozen=True)
class Request:
    sample_id: str
    prediction_time: int | float
    features: tuple[float, ...]
    entity_id: str | None
    domain_id: str | None
    decision_context: str | None
    feature_reference: str | None = None


@dataclass(frozen=True)
class Label:
    sample_id: str
    available_time: int | float
    target: float


@dataclass(frozen=True)
class DecisionRequest:
    """Learner-visible request and declared decision context; no outcome or oracle fields."""

    sample_id: str
    event_time: int | float
    feature_available_time: int | float
    prediction_time: int | float
    features: tuple[float, ...]
    entity_id: str | None
    domain_id: str | None
    decision_context: str | None
    policy_version: str
    reference_policy_version: str
    decision_cost_version: str

    def __post_init__(self):
        times = (self.event_time, self.feature_available_time, self.prediction_time)
        if not self.sample_id or not all(isfinite(float(value)) for value in times):
            raise ValueError("Decision request needs an ID and finite event timestamps")
        if not self.event_time <= self.feature_available_time <= self.prediction_time:
            raise ValueError("Require event_time <= feature_available_time <= prediction_time")
        if not self.features or not all(isfinite(float(value)) for value in self.features):
            raise ValueError("Decision request features must be a nonempty finite vector")
        if (
            not self.policy_version
            or not self.reference_policy_version
            or not self.decision_cost_version
        ):
            raise ValueError("Policy and decision-cost versions must be explicit")


@dataclass(frozen=True)
class PolicyDecision:
    """Logged deployed/reference actions and the pre-outcome label-query decision."""

    sample_id: str
    action_time: int | float
    action: int
    reference_action: int
    query_label: bool
    query_probability: float | None

    def __post_init__(self):
        if not self.sample_id or not isfinite(float(self.action_time)):
            raise ValueError("Policy decision needs an ID and finite action_time")
        if self.action not in (0, 1) or self.reference_action not in (0, 1):
            raise ValueError("Binary policy actions must be 0 or 1")
        if self.query_probability is not None and (
            not isfinite(self.query_probability) or not 0 <= self.query_probability <= 1
        ):
            raise ValueError("query_probability must be finite and in [0,1]")
        if self.query_label and (self.query_probability is None or self.query_probability <= 0):
            raise ValueError("A queried label requires a positive logged propensity")


@dataclass(frozen=True)
class DecisionFeedback:
    """Outcome feedback visible only when its recorded availability time is reached."""

    sample_id: str
    label_event_time: int | float
    available_time: int | float
    target: float

    def __post_init__(self):
        if (
            not self.sample_id
            or not isfinite(float(self.label_event_time))
            or not isfinite(float(self.available_time))
            or not isfinite(float(self.target))
        ):
            raise ValueError("Decision feedback needs an ID and finite times and target")
        if self.label_event_time > self.available_time:
            raise ValueError("A label cannot be available before its event time")


@dataclass(frozen=True)
class OracleDecisionRecord:
    """Evaluator-only truth; never yielded by replay_decision_stream."""

    sample_id: str
    regime_id: str | None
    true_probability_positive: float
    oracle_action: int
    oracle_expected_cost: float
    deployed_expected_cost: float
    reference_expected_cost: float
    true_change_time: int | float | None = None

    def __post_init__(self):
        values = (
            self.true_probability_positive,
            self.oracle_expected_cost,
            self.deployed_expected_cost,
            self.reference_expected_cost,
        )
        if (
            not self.sample_id
            or not all(isfinite(float(value)) for value in values)
            or not 0 <= self.true_probability_positive <= 1
            or self.oracle_action not in (0, 1)
        ):
            raise ValueError("Invalid evaluator-only decision truth")
        if self.true_change_time is not None and not isfinite(float(self.true_change_time)):
            raise ValueError("true_change_time must be finite when known")


DecisionStreamEvent = DecisionRequest | PolicyDecision | DecisionFeedback


def replay_decision_stream(
    requests: list[DecisionRequest],
    decisions: list[PolicyDecision],
    feedback: list[DecisionFeedback],
) -> Iterator[DecisionStreamEvent]:
    """Replay actions and delayed/queried labels without exposing evaluator-only truth.

    All requests and their pre-outcome actions at one prediction time precede labels becoming
    available at that same time. Unqueried outcomes are rejected; missing queried labels are
    allowed. OracleDecisionRecord objects are deliberately not an argument to this function.
    """
    request_by_id = {item.sample_id: item for item in requests}
    decision_by_id = {item.sample_id: item for item in decisions}
    feedback_by_id = {item.sample_id: item for item in feedback}
    if len(request_by_id) != len(requests) or len(decision_by_id) != len(decisions):
        raise ValueError("Request and decision sample IDs must be unique")
    if len(feedback_by_id) != len(feedback):
        raise ValueError("Feedback sample IDs must be unique")
    if request_by_id.keys() != decision_by_id.keys():
        raise ValueError("Every request must have exactly one logged policy decision")
    if not feedback_by_id.keys() <= request_by_id.keys():
        raise ValueError("Feedback references an unknown sample")

    for sample_id, outcome in feedback_by_id.items():
        request, decision = request_by_id[sample_id], decision_by_id[sample_id]
        if not decision.query_label:
            raise ValueError("Feedback supplied for a label that was not queried")
        if outcome.label_event_time < request.event_time:
            raise ValueError("Label event precedes its request event")
        if outcome.available_time < decision.action_time:
            raise ValueError("Label feedback cannot precede the action")
    for sample_id, request in request_by_id.items():
        if decision_by_id[sample_id].action_time != request.prediction_time:
            raise ValueError("This replay contract requires action_time == prediction_time")

    ordered = sorted(requests, key=lambda item: (item.prediction_time, item.sample_id))
    pending: list[tuple[float, str]] = []
    for now in sorted({item.prediction_time for item in ordered}):
        while pending and pending[0][0] < now:
            _available, sample_id = heapq.heappop(pending)
            yield feedback_by_id[sample_id]
        group = [item for item in ordered if item.prediction_time == now]
        for request in group:
            decision = decision_by_id[request.sample_id]
            yield request
            yield decision
            available_outcome = feedback_by_id.get(request.sample_id)
            if available_outcome is not None:
                heapq.heappush(
                    pending,
                    (float(available_outcome.available_time), request.sample_id),
                )
        while pending and pending[0][0] == now:
            _, sample_id = heapq.heappop(pending)
            yield feedback_by_id[sample_id]
    while pending:
        _, sample_id = heapq.heappop(pending)
        yield feedback_by_id[sample_id]


def replay(frame: pd.DataFrame):
    """Yield request then labels available by this time; unknown availability is withheld.

    All requests at the same timestamp precede all feedback at that timestamp.
    Oracle regime, split, provenance and targets are absent from requests.
    """
    if frame.prediction_time.isna().any():
        raise ValueError("Unknown prediction times; define an explicit availability protocol first")
    pending: list[tuple[float, str, float]] = []
    ordered = frame.sort_values(["prediction_time", "sample_id"])
    for now, group in ordered.groupby("prediction_time", sort=True):
        while pending and pending[0][0] < now:
            available, identifier, target = heapq.heappop(pending)
            yield Label(identifier, available, target)
        for row in group.itertuples():
            if pd.isna(row.feature_available_time) or row.feature_available_time > now:
                raise ValueError("Features unavailable at prediction time")
            yield Request(
                row.sample_id,
                now,
                tuple(row.features),
                row.entity_id,
                row.domain_id,
                row.decision_context,
                getattr(row, "feature_reference", None),
            )
            if pd.notna(row.target) and pd.notna(row.label_available_time):
                if row.label_available_time < now:
                    raise ValueError(
                        "Target already observable before prediction; audit task construction"
                    )
                heapq.heappush(
                    pending,
                    (float(row.label_available_time), row.sample_id, float(row.target)),
                )
        while pending and pending[0][0] == now:
            available, identifier, target = heapq.heappop(pending)
            yield Label(identifier, available, target)
    # The final request may precede the last delayed outcomes. The stream continues through
    # those feedback arrivals even when no later prediction request is scheduled.
    while pending:
        available, identifier, target = heapq.heappop(pending)
        yield Label(identifier, available, target)
