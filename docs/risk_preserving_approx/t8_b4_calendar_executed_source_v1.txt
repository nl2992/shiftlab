"""Run the registered T=8, B=4 adaptive-reservation comparison."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from decompose_switching_calendar_gap import CalendarOpportunityGame

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.eprocess_gated_planner import EProcessGatedPlanner, mix_with_never_promote
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

PROTOCOL = ROOT / "docs/risk_preserving_approx/T8_B4_CALENDAR_PROTOCOL_V1.md"
INPUT = ROOT / "docs/risk_preserving_approx/cap_calendar_synthetic_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(game) -> dict:
    started = time.perf_counter()
    report, policy, _ = game.solve()
    elapsed = time.perf_counter() - started
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    safe = lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    safe_metrics = game.expected_metrics(safe)
    raw_cost = sum(metrics[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    cost = activation * raw_cost + (1 - activation) * sum(safe_metrics[:3])
    if activation * risk > game.config.alpha:
        raise AssertionError("root calibration violated alpha")
    if abs(float(raw_cost) - report["solver_objective"]) > 1e-7:
        raise AssertionError("LP and exact recovered policy costs disagree")
    calibrated_metrics = tuple(
        activation * value + (1 - activation) * safe_value
        for value, safe_value in zip(metrics, safe_metrics, strict=True)
    )
    return {
        "status": "completed",
        "raw_cost": str(raw_cost),
        "raw_risk": str(risk),
        "activation": str(activation),
        "calibrated_cost": str(cost),
        "calibrated_risk": str(activation * risk),
        "metrics": [str(value) for value in calibrated_metrics],
        "nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "solver_objective": report["solver_objective"],
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "solve_seconds": elapsed,
    }


def evaluate_gate(config, model, threshold: F) -> dict:
    game = EProcessGatedPlanner(config, model, stake=F(1), threshold=threshold)
    started = time.perf_counter()
    dynamic_cost, raw_policy = game.solve_gated()
    elapsed = time.perf_counter() - started
    raw_metrics = game.expected_metrics(raw_policy)
    raw_risk = game.null_risk(raw_policy)
    if sum(raw_metrics[:3]) != dynamic_cost:
        raise AssertionError("gated planner and exact evaluation disagree")
    activation = min(F(1), config.alpha / raw_risk) if raw_risk else F(1)
    policy = mix_with_never_promote(game, raw_policy, activation)
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    if risk > config.alpha or activation * raw_risk > config.alpha:
        raise AssertionError("calibrated gate exceeds exact null-risk level")
    return {
        "status": "completed",
        "threshold": str(threshold),
        "raw_cost": str(sum(raw_metrics[:3])),
        "raw_risk": str(raw_risk),
        "activation": str(activation),
        "calibrated_cost": str(sum(metrics[:3])),
        "calibrated_risk": str(risk),
        "metrics": [str(value) for value in metrics],
        "state_counts": game.state_counts(),
        "solve_seconds": elapsed,
    }


def run_method(method: str, config, model):
    try:
        if method == "reference":
            return evaluate(FirstPromotionDecomposedGame(config, model))
        if method == "cap_m3":
            return evaluate(PrePromotionCapGame(config, model, pre_cap=3))
        if method.startswith("gate_"):
            return evaluate_gate(config, model, F(method.removeprefix("gate_")))
        raise ValueError(f"unknown method {method}")
    except Exception as exc:  # noqa: BLE001 - Preserve every registered failure.
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def run_calendar(config, model, dates):
    try:
        result = evaluate(CalendarOpportunityGame(config, model, dates))
        result["calendar"] = list(dates)
        return result
    except Exception as exc:  # noqa: BLE001 - Preserve every registered failure.
        return {
            "status": "failed",
            "calendar": list(dates),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    payload = {
        "protocol_sha256": sha(PROTOCOL),
        "input_sha256": sha(INPUT),
        "runner_sha256": sha(Path(__file__)),
        "source_hashes": {
            path: sha(ROOT / path)
            for path in (
                "scripts/decompose_switching_calendar_gap.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/first_promotion_decomposition.py",
                "src/shiftlab/dive/prepromotion_cap.py",
                "src/shiftlab/dive/eprocess_gated_planner.py",
            )
        },
        "cells": [],
    }
    dates = [combo for size in range(5) for combo in combinations(range(1, 7), size)]
    methods = ("reference", "cap_m3", "gate_4", "gate_8", "gate_16")
    for registered in source["cells"]:
        transition = F(registered["transition"])
        emission0, emission1 = map(F, registered["emissions"])
        config = GameConfig(
            horizon=8,
            budget=4,
            delay=2,
            alpha=F(1, 10),
            query_cost=F(1, 100),
            switch_cost=F(1, 10),
        )
        model = RegimeModel(
            transition01=transition,
            transition10=transition,
            emission0=emission0,
            emission1=emission1,
            prior1=F(1, 2),
        )
        row = {
            "transition": str(transition),
            "emissions": [str(emission0), str(emission1)],
            "methods": {name: run_method(name, config, model) for name in methods},
            "calendars": [],
        }
        payload["cells"].append(row)
        for dates_subset in dates:
            row["calendars"].append(run_calendar(config, model, dates_subset))
            OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        valid = [item for item in row["calendars"] if item["status"] == "completed"]
        if valid:
            best = min(valid, key=lambda item: F(item["calibrated_cost"]))
            row["best_calendar"] = best["calendar"]
            row["best_calendar_cost"] = best["calibrated_cost"]
            for result in row["methods"].values():
                if result["status"] == "completed":
                    result["gap_to_best_calendar"] = str(
                        F(result["calibrated_cost"]) - F(best["calibrated_cost"])
                    )
        row["status"] = "completed" if len(valid) == len(dates) else "partial"
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "transition": row["transition"],
                    "emission0": str(emission0),
                    "status": row["status"],
                    "best_calendar": row.get("best_calendar"),
                    "gaps": {
                        name: result.get("gap_to_best_calendar")
                        for name, result in row["methods"].items()
                    },
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
