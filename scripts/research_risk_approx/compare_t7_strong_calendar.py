"""Run the registered T=7 cap, calendar and e-process comparison."""

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

PROTOCOL = ROOT / "docs/risk_preserving_approx/T7_STRONG_CALENDAR_PROTOCOL_V1.md"
CERTIFICATE = ROOT / "docs/risk_preserving_approx/full_t7_certificate_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/t7_strong_calendar_v1.json"


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
    safe_cost = sum(safe_metrics[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    calibrated_cost = activation * raw_cost + (1 - activation) * safe_cost
    calibrated_metrics = tuple(
        activation * raw + (1 - activation) * safe_value
        for raw, safe_value in zip(metrics, safe_metrics, strict=True)
    )
    if activation * risk > game.config.alpha:
        raise AssertionError("root calibration failed")
    if abs(float(raw_cost) - report["solver_objective"]) > 1e-7:
        raise AssertionError("LP objective and exact recovered-policy cost disagree")
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


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    config = GameConfig(
        horizon=7,
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
    cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    lower = F(cert["certificate"]["lower"])
    payload = {
        "protocol_sha256": sha(PROTOCOL),
        "certificate_sha256": sha(CERTIFICATE),
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
        "full_oracle_lower_bound": str(lower),
        "full": None,
        "cap_m2": None,
        "eprocess_threshold4": None,
        "calendars": [],
    }
    try:
        full = FirstPromotionDecomposedGame(config, model)
        payload["full"] = evaluate(full)
        capped = PrePromotionCapGame(config, model, pre_cap=2)
        payload["cap_m2"] = evaluate(capped)
        evidence = EProcessGatedPlanner(config, model, stake=F(1), threshold=F(4))
        raw_value, raw_policy = evidence.solve_gated()
        raw_metrics = evidence.expected_metrics(raw_policy)
        raw_risk = evidence.null_risk(raw_policy)
        activation = min(F(1), config.alpha / raw_risk) if raw_risk else F(1)
        mixed = mix_with_never_promote(evidence, raw_policy, activation)
        mixed_metrics = evidence.expected_metrics(mixed)
        mixed_risk = evidence.null_risk(mixed)
        if sum(raw_metrics[:3]) != raw_value or mixed_risk > config.alpha:
            raise AssertionError("e-process planner cost/risk check failed")
        payload["eprocess_threshold4"] = {
            "raw_cost": str(sum(raw_metrics[:3])),
            "raw_risk": str(raw_risk),
            "activation": str(activation),
            "calibrated_cost": str(sum(mixed_metrics[:3])),
            "calibrated_risk": str(mixed_risk),
            "metrics": [str(value) for value in mixed_metrics],
            "state_counts": evidence.state_counts(),
        }
        for calendar in (combo for size in range(4) for combo in combinations(range(1, 7), size)):
            row = evaluate(CalendarOpportunityGame(config, model, calendar))
            row["calendar"] = list(calendar)
            payload["calendars"].append(row)
            OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        best_calendar = min(payload["calendars"], key=lambda row: F(row["calibrated_cost"]))
        payload["best_calendar"] = best_calendar["calendar"]
        payload["best_calendar_cost"] = best_calendar["calibrated_cost"]
        for name in ("full", "cap_m2", "eprocess_threshold4"):
            if name != "eprocess_threshold4":
                cost = F(payload[name]["calibrated_cost"])
                payload[name]["gap_to_full_certificate_lower"] = str(cost - lower)
                payload[name]["gap_to_best_calendar"] = str(
                    cost - F(best_calendar["calibrated_cost"])
                )
        payload["eprocess_threshold4"]["gap_to_best_calendar"] = str(
            F(payload["eprocess_threshold4"]["calibrated_cost"])
            - F(best_calendar["calibrated_cost"])
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
                "cap_gap": payload.get("cap_m2", {}).get("gap_to_best_calendar"),
                "eprocess_gap": payload.get("eprocess_threshold4", {}).get("gap_to_best_calendar"),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
