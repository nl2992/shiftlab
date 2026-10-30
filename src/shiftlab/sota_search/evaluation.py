"""Evaluator-owned streaming execution and explicit endpoint diagnostics.

No oracle quantity is passed to an adapter. Metrics are descriptive until a
separate protocol establishes null calibration and confirmatory uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .adapters import AdapterConfig, SourceCalibration, StreamingAdapter
from .feedback import FeedbackStream
from .generators import SyntheticWorld


@dataclass(frozen=True)
class Evaluation:
    metrics: dict
    trajectory: dict[str, np.ndarray]


def evaluate(
    world: SyntheticWorld,
    source: SyntheticWorld,
    config: AdapterConfig,
    *,
    query_seed: int,
) -> Evaluation:
    if world.config.family != source.config.family:
        raise ValueError("source and deployment must use the same family")
    if np.any(source.truth.regime_weight):
        raise ValueError("source calibration must be nominal")
    calibration = SourceCalibration(
        source.events, source.truth.predictive_losses, source.truth.decision_losses
    )
    n = len(world.events)
    budget = int(n * config.budget_fraction)
    learner = StreamingAdapter(config, calibration, horizon=n)
    broker = FeedbackStream(world, budget=budget, query_seed=query_seed)
    actions, requested, effective, purchased, pending, evidence = [], [], [], [], [], []
    switch_charges, label_charges = [], []
    previous_action = 0
    for time in range(n):
        event, arrived = broker.open_round(time)
        learner.receive(arrived, time=time)
        action = learner.choose_model(event)
        switch_charges.append(event.switch_cost if action != previous_action else 0.0)
        previous_action = action
        q = learner.propensity(event, remaining=budget - broker.labels_purchased)
        receipt, immediate = broker.request(q)
        learner.register(event, receipt)
        learner.receive(immediate, time=time)
        actions.append(action)
        requested.append(q)
        effective.append(receipt.effective_propensity)
        purchased.append(receipt.purchased)
        pending.append(broker.pending_count)
        label_charges.append(receipt.paid)
        evidence.append(learner.log_e_values.copy())
    actions = np.asarray(actions, dtype=int)
    truth = world.truth
    deployed = truth.decision_losses[np.arange(n), actions]
    expected = truth.expected_decision_losses[np.arange(n), actions]
    oracle = truth.expected_decision_losses.min(axis=1)
    first = learner.first_crossing
    # Positive conditional excess cost, kept separate from paired certification.
    deterioration = truth.expected_decision_losses[:, 0] - truth.nominal_decision_losses[:, 0]
    harmful = np.flatnonzero(deterioration > config.margin)
    onset = int(harmful[0]) if len(harmful) else None
    end = first if first is not None else n
    certification_time = first - 1 if first is not None else None
    candidate = learner.certified_candidate if config.track != "Q1" else None
    benefit = None
    if certification_time is not None and candidate is not None:
        benefit = float(
            truth.expected_decision_losses[certification_time, 0]
            - truth.expected_decision_losses[certification_time, candidate]
        )
    # An alarm before onset is not counted as successful harmful-change detection.
    detected = onset is not None and first is not None and first > onset
    metrics = {
        "track": config.track,
        "alarm_by_horizon": first is not None,
        "first_alarm_round": first,
        "harm_onset_event": onset,
        "harm_detected_after_onset": bool(detected),
        "pre_harm_alarm": first is not None and (onset is None or first <= onset),
        "censored_detection_delay": None
        if onset is None
        else (first - onset if detected else n - onset),
        "positive_decision_harm_before_alarm": float(np.maximum(deterioration[:end], 0).sum()),
        "certified_candidate": candidate,
        "candidate_conditional_benefit_at_certification": benefit,
        "nonimproving_certification_diagnostic": benefit is not None and benefit <= config.margin,
        "realized_deployed_loss": float(deployed.sum()),
        "expected_deployed_loss": float(expected.sum()),
        "expected_available_model_regret": float((expected - oracle).sum()),
        "label_expenditure": float(sum(label_charges)),
        "switch_expenditure": float(sum(switch_charges)),
        "realized_net_cost": float(deployed.sum() + sum(label_charges) + sum(switch_charges)),
        "expected_net_cost": float(expected.sum() + sum(label_charges) + sum(switch_charges)),
        "switches": int(np.count_nonzero(np.diff(np.r_[0, actions]))),
        "labels_used": broker.labels_purchased,
        "hard_label_cap": budget,
        "pending_at_horizon": broker.pending_count,
        "source_labels": len(source.events),
        "source_label_expenditure": float(sum(e.label_cost for e in source.events)),
        "validity_status": "development_diagnostic_null_and_operating_point_not_calibrated",
        "certification_diagnostic_scope": "instantaneous_conditional_benefit_not_running_mean_null",
    }
    trajectory = {
        "deployed_model": actions,
        "requested_propensity": np.array(requested),
        "effective_propensity": np.array(effective),
        "queried": np.array(purchased),
        "pending": np.array(pending),
        "log_e_values": np.array(evidence),
        "label_charge": np.array(label_charges),
        "switch_charge": np.array(switch_charges),
        "realized_deployed_loss": deployed,
        "expected_deployed_loss": expected,
        "evaluator_expected_model_losses": truth.expected_decision_losses,
        "evaluator_nominal_model_losses": truth.nominal_decision_losses,
    }
    return Evaluation(metrics, trajectory)
