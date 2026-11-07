from __future__ import annotations

import numpy as np
from simulator import Event, ReleasedFeedback

from scripts.sota_sprint.run_mnds_contextual_transfer import StratifiedGate


def _send_gain(gate: StratifiedGate, *, event_id: int, gain: int) -> None:
    event = Event(
        event_id=event_id,
        t=event_id,
        horizon=1000,
        model_predictions=np.asarray([0, 1]),
        context="sputnik",
    )
    assert gate.predict(event) == int(gate.states["sputnik"]["deployed"])
    request = gate.request_labels(event, remaining_budget=200)
    assert request.requested
    losses = np.asarray([1, 0] if gain > 0 else [0, 1], dtype=np.int8)
    gate.observe(
        [
            ReleasedFeedback(
                event_id=event_id,
                t_requested=event_id,
                t_released=event_id + 1,
                label=0,
                model_losses=losses,
                query_probability=1.0,
                extra=request.extra,
            )
        ]
    )


def test_context_gate_promotes_and_rolls_back_only_after_released_evidence() -> None:
    gate = StratifiedGate(
        horizon=1000,
        context_rates={
            "eveningstandard": 0.25,
            "sputnik": 0.25,
            "tass": 0.25,
            "other": 0.25,
        },
    )
    event = Event(
        event_id=0,
        t=0,
        horizon=1000,
        model_predictions=np.asarray([0, 1]),
        context="sputnik",
    )
    request = gate.request_labels(event, remaining_budget=200)
    assert request.requested
    assert not gate.states["sputnik"]["promoted"]
    gate.observe(
        [
            ReleasedFeedback(
                event_id=0,
                t_requested=0,
                t_released=1,
                label=0,
                model_losses=np.asarray([1, 0], dtype=np.int8),
                query_probability=1.0,
                extra=request.extra,
            )
        ]
    )
    assert not gate.states["sputnik"]["promoted"]

    for event_id in range(1, 26):
        if gate.states["sputnik"]["promoted"]:
            break
        _send_gain(gate, event_id=event_id, gain=1)
    assert gate.states["sputnik"]["promoted"]
    assert (
        gate.predict(
            Event(
                event_id=1,
                t=1,
                horizon=1000,
                model_predictions=np.asarray([0, 1]),
                context="sputnik",
            )
        )
        == 1
    )

    next_event_id = event_id + 1
    for rollback_event_id in range(next_event_id, next_event_id + 26):
        if gate.states["sputnik"]["rolled_back"]:
            break
        _send_gain(gate, event_id=rollback_event_id, gain=-1)
    assert gate.states["sputnik"]["rolled_back"]
    assert gate.states["sputnik"]["deployed"] == 0
