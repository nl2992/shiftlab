"""Execute the registered six-cell e-process-gated planner comparison."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.eprocess_gated_planner import EProcessGatedPlanner, mix_with_never_promote

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/EPROCESS_GATED_PLANNER_PROTOCOL_V1.md"
REFERENCE = ROOT / "docs/risk_preserving_approx/cap_calendar_synthetic_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/eprocess_gated_planner_synthetic_v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_policy(game):
    return lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))


def run_cell(source: dict) -> dict:
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    transition = F(source["transition"])
    emission0, emission1 = map(F, source["emissions"])
    model = RegimeModel(
        transition01=transition,
        transition10=transition,
        emission0=emission0,
        emission1=emission1,
        prior1=F(1, 2),
    )
    game = EProcessGatedPlanner(config, model, stake=F(1), threshold=F(4))
    start = time.perf_counter()
    dynamic_cost, raw_policy = game.solve_gated()
    solve_seconds = time.perf_counter() - start
    raw_metrics = game.expected_metrics(raw_policy)
    raw_cost = sum(raw_metrics[:3])
    raw_risk = game.null_risk(raw_policy)
    if dynamic_cost != raw_cost:
        raise AssertionError(f"planner/evaluator cost mismatch: {dynamic_cost} != {raw_cost}")
    if raw_risk > F(1, 4):
        raise AssertionError(f"Ville crossing bound violated: {raw_risk} > 1/4")

    activation = min(F(1), config.alpha / raw_risk) if raw_risk else F(1)
    policy = mix_with_never_promote(game, raw_policy, activation)
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    safe_metrics = game.expected_metrics(safe_policy(game))
    predicted_metrics = tuple(
        activation * raw + (1 - activation) * safe
        for raw, safe in zip(raw_metrics, safe_metrics, strict=True)
    )
    if metrics != predicted_metrics:
        raise AssertionError("behavioral root-lottery metrics differ from exact branch mixture")
    if risk > config.alpha or activation * raw_risk > config.alpha:
        raise AssertionError(f"calibrated null risk exceeds alpha: {risk}")
    if metrics[3] > config.budget:
        raise AssertionError(f"expected queries exceed pathwise budget: {metrics[3]}")

    oracle_cost = F(source["full"]["safe_cost"])
    calendar_cost = F(source["best_calendar_cost"])
    cost = sum(metrics[:3])
    return {
        "transition": str(transition),
        "emissions": [str(emission0), str(emission1)],
        "status": "completed",
        "raw_cost": str(raw_cost),
        "raw_risk": str(raw_risk),
        "ville_risk_bound": "1/4",
        "activation": str(activation),
        "calibrated_cost": str(cost),
        "calibrated_risk": str(risk),
        "metrics": [str(value) for value in metrics],
        "oracle_cost": str(oracle_cost),
        "oracle_gap": str(cost - oracle_cost),
        "best_calendar": source["best_calendar"],
        "best_calendar_cost": str(calendar_cost),
        "calendar_gap": str(cost - calendar_cost),
        "state_counts": game.state_counts(),
        "solve_seconds": solve_seconds,
        "independent_metrics_match": True,
        "maximum_queries_bounded_by": config.budget,
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    payload = {
        "protocol": PROTOCOL.name,
        "protocol_sha256": digest(PROTOCOL),
        "reference_sha256": digest(REFERENCE),
        "runner_sha256": digest(Path(__file__)),
        "planner_sha256": digest(ROOT / "src/shiftlab/dive/eprocess_gated_planner.py"),
        "cells": [],
    }
    for source in reference["cells"]:
        try:
            row = run_cell(source)
        except Exception as exc:  # noqa: BLE001 - Preserve every registered failed cell.
            row = {
                "transition": source["transition"],
                "emissions": source["emissions"],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        payload["cells"].append(row)
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "transition": row["transition"],
                    "emissions": row["emissions"],
                    "status": row["status"],
                    "calibrated_risk": row.get("calibrated_risk"),
                    "calendar_gap": row.get("calendar_gap"),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
