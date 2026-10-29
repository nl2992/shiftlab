"""Run the registered T=8 cap, calendar and e-process comparison."""

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

PROTOCOL = ROOT / "docs/risk_preserving_approx/T8_STRONG_CALENDAR_PROTOCOL_V1.md"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_strong_calendar_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(game) -> dict:
    start = time.perf_counter()
    report, policy, _ = game.solve()
    solve_seconds = time.perf_counter() - start
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    safe = lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    safe_metrics = game.expected_metrics(safe)
    raw_cost = sum(metrics[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    calibrated_cost = activation * raw_cost + (1 - activation) * sum(safe_metrics[:3])
    if activation * risk > game.config.alpha:
        raise AssertionError("root calibration failed")
    if abs(float(raw_cost) - report["solver_objective"]) > 1e-7:
        raise AssertionError("LP objective and exact recovered-policy cost disagree")
    calibrated_metrics = tuple(
        activation * raw + (1 - activation) * safe_value
        for raw, safe_value in zip(metrics, safe_metrics, strict=True)
    )
    return {
        "raw_cost": str(raw_cost),
        "raw_risk": str(risk),
        "activation": str(activation),
        "calibrated_cost": str(calibrated_cost),
        "calibrated_risk_bound": str(activation * risk),
        "metrics": [str(value) for value in calibrated_metrics],
        "nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "solver_objective": report["solver_objective"],
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "solve_seconds": solve_seconds,
    }


def evaluate_gate(config, model, threshold: F) -> dict:
    game = EProcessGatedPlanner(config, model, stake=F(1), threshold=threshold)
    start = time.perf_counter()
    dynamic_cost, raw_policy = game.solve_gated()
    solve_seconds = time.perf_counter() - start
    raw_metrics = game.expected_metrics(raw_policy)
    raw_risk = game.null_risk(raw_policy)
    if sum(raw_metrics[:3]) != dynamic_cost:
        raise AssertionError("planner and independent cost evaluation disagree")
    activation = min(F(1), config.alpha / raw_risk) if raw_risk else F(1)
    mixture = mix_with_never_promote(game, raw_policy, activation)
    metrics = game.expected_metrics(mixture)
    risk = game.null_risk(mixture)
    if risk > config.alpha or activation * raw_risk > config.alpha:
        raise AssertionError("exact causal-null risk exceeds alpha")
    return {
        "threshold": str(threshold),
        "raw_cost": str(sum(raw_metrics[:3])),
        "raw_risk": str(raw_risk),
        "activation": str(activation),
        "calibrated_cost": str(sum(metrics[:3])),
        "calibrated_risk": str(risk),
        "metrics": [str(value) for value in metrics],
        "state_counts": game.state_counts(),
        "solve_seconds": solve_seconds,
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    config = GameConfig(
        horizon=8,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    payload = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "sources": {
            path: sha(ROOT / path)
            for path in (
                "scripts/decompose_switching_calendar_gap.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/first_promotion_decomposition.py",
                "src/shiftlab/dive/prepromotion_cap.py",
                "src/shiftlab/dive/eprocess_gated_planner.py",
            )
        },
        "reference": None,
        "cap_m2": None,
        "eprocess_threshold4": None,
        "eprocess_threshold8": None,
        "calendars": [],
    }
    try:
        payload["reference"] = evaluate(FirstPromotionDecomposedGame(config, model))
        payload["cap_m2"] = evaluate(PrePromotionCapGame(config, model, pre_cap=2))
        payload["eprocess_threshold4"] = evaluate_gate(config, model, F(4))
        payload["eprocess_threshold8"] = evaluate_gate(config, model, F(8))
        for calendar in (combo for size in range(4) for combo in combinations(range(1, 8), size)):
            row = evaluate(CalendarOpportunityGame(config, model, calendar))
            row["calendar"] = list(calendar)
            payload["calendars"].append(row)
            OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        best = min(payload["calendars"], key=lambda row: F(row["calibrated_cost"]))
        payload["best_calendar"] = best["calendar"]
        payload["best_calendar_cost"] = best["calibrated_cost"]
        for name in ("reference", "cap_m2", "eprocess_threshold4", "eprocess_threshold8"):
            payload[name]["gap_to_best_calendar"] = str(
                F(payload[name]["calibrated_cost"]) - F(best["calibrated_cost"])
            )
        payload["status"] = "completed"
    except Exception as exc:  # noqa: BLE001 - Preserve registered failures.
        payload["status"] = "failed"
        payload["error"] = f"{type(exc).__name__}: {exc}"
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "calendar_count": len(payload["calendars"]),
                "best_calendar": payload.get("best_calendar"),
                "best_calendar_cost": payload.get("best_calendar_cost"),
                "gaps": {
                    name: row.get("gap_to_best_calendar")
                    for name, row in payload.items()
                    if name in ("reference", "cap_m2", "eprocess_threshold4", "eprocess_threshold8")
                    and row
                },
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
