"""Registered generator-contract diagnostic; not an algorithm search result."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from .feedback import FeedbackStream
from .generators import WorldConfig, make_world, summarize_world


def check_world(config: WorldConfig, seed: int, result_path: Path) -> dict:
    world = make_world(config, seed=seed)
    truth = world.truth
    for values in (
        truth.predictive_losses,
        truth.decision_losses,
        truth.expected_predictive_losses,
        truth.expected_decision_losses,
    ):
        if not np.isfinite(values).all() or values.min() < 0 or values.max() > 1:
            raise ValueError("generator produced unbounded or invalid loss")
    broker = FeedbackStream(world, budget=64, query_seed=seed + 900000)
    received = []
    for t in range(config.horizon):
        event, arrived = broker.open_round(t)
        received.extend(arrived)
        # This fixed diagnostic acquisition rule sees public events only.
        assert event is not None
        receipt, immediate = broker.request(0.2)
        received.extend(immediate)
        if receipt.remaining_labels < 0:
            raise ValueError("hard label budget was exceeded")
    if any(row.available_time < row.event_index for row in received):
        raise ValueError("feedback arrived before its event")
    if len({row.event_index for row in received}) != len(received):
        raise ValueError("feedback was delivered twice")
    summary = summarize_world(world)
    raw_path = result_path.with_name("evaluator_world.npz")
    with raw_path.open("xb") as raw:
        np.savez_compressed(
            raw,
            features=np.array([e.features for e in world.events]),
            outcomes=truth.outcomes,
            expected_predictive_losses=truth.expected_predictive_losses,
            expected_decision_losses=truth.expected_decision_losses,
            nominal_predictive_losses=truth.nominal_predictive_losses,
            nominal_decision_losses=truth.nominal_decision_losses,
            predictive_losses=truth.predictive_losses,
            decision_losses=truth.decision_losses,
            regime_weight=truth.regime_weight,
            hidden_state=truth.hidden_state,
            availability=truth.availability,
            missing=truth.missing,
        )
    return {
        "primary_metric": {"generator_contract_passed": True},
        "secondary_metrics": {
            **summary,
            "purchased_labels": broker.labels_purchased,
            "received_labels_by_horizon": len(received),
            "pending_at_horizon": broker.pending_count,
            "label_spend": broker.money_spent,
        },
        "uncertainty_estimates": None,
        "labels_used": broker.labels_purchased,
        "validity_status": "generator_contract_diagnostic_no_statistical_claim",
        # Evaluator data stay in the artifact archive, never an adapter input.
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--horizon", required=True, type=int)
    args = parser.parse_args()
    result_path = Path(os.environ["SOTA_RESULT_PATH"])
    config = WorldConfig(
        family=args.family,
        scenario=args.scenario,
        horizon=args.horizon,
        delay=3,
        delay_model="independent_random",
    )
    result = check_world(config, args.seed, result_path)
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
