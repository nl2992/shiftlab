"""Registered strong calendar-opportunity comparison on six known HMM cells."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from decompose_switching_calendar_gap import CalendarOpportunityGame

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

OUT = ROOT / "docs/risk_preserving_approx/cap_calendar_synthetic_v1.json"


def evaluate(game):
    start = time.perf_counter()
    report, policy, _ = game.solve()
    elapsed = time.perf_counter() - start
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    noquery = lambda h, o: tuple(F(choice == (0, 0)) for choice in game.choices(h))
    safe_cost = sum(game.expected_metrics(noquery)[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    cost = activation * sum(metrics[:3]) + (1 - activation) * safe_cost
    if (
        activation * risk > game.config.alpha
        or abs(float(sum(metrics[:3])) - report["solver_objective"]) > 1e-7
    ):
        raise ValueError("Recovered risk or cost validation failed")
    return {
        "safe_cost": str(cost),
        "raw_cost": str(sum(metrics[:3])),
        "raw_risk": str(risk),
        "activation": str(activation),
        "safe_risk_bound": str(activation * risk),
        "metrics": [str(v) for v in metrics],
        "objective": report["solver_objective"],
        "nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "elapsed_s": elapsed,
    }


def cell(transition, emissions):
    config = GameConfig(
        horizon=6, budget=3, delay=2, alpha=F(1, 10), query_cost=F(1, 100), switch_cost=F(1, 10)
    )
    model = RegimeModel(
        transition01=transition,
        transition10=transition,
        emission0=emissions[0],
        emission1=emissions[1],
        prior1=F(1, 2),
    )
    full = evaluate(FirstPromotionDecomposedGame(config, model))
    cap = evaluate(PrePromotionCapGame(config, model, pre_cap=2))
    schedules = [c for n in range(4) for c in combinations(range(1, 5), n)]
    calendars = []
    for schedule in schedules:
        result = evaluate(CalendarOpportunityGame(config, model, schedule))
        result["calendar"] = schedule
        calendars.append(result)
    best = min(calendars, key=lambda r: F(r["safe_cost"]))
    return {
        "transition": str(transition),
        "emissions": [str(v) for v in emissions],
        "full": full,
        "cap2": cap,
        "calendars": calendars,
        "best_calendar": best["calendar"],
        "best_calendar_cost": best["safe_cost"],
        "calendar_minus_cap": str(F(best["safe_cost"]) - F(cap["safe_cost"])),
        "cap_minus_full": str(F(cap["safe_cost"]) - F(full["safe_cost"])),
    }


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    paths = [
        Path(__file__),
        ROOT / "scripts/decompose_switching_calendar_gap.py",
        ROOT / "src/shiftlab/dive/prepromotion_cap.py",
        ROOT / "src/shiftlab/dive/causal_switching_game.py",
        ROOT / "docs/risk_preserving_approx/CAP_CALENDAR_PROTOCOL_V1.md",
    ]
    payload = {
        "hashes": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        },
        "cells": [],
    }
    for transition, emissions in product(
        (F(1, 10), F(1, 4), F(9, 20)), ((F(1, 10), F(9, 10)), (F(1, 50), F(49, 50)))
    ):
        try:
            row = cell(transition, emissions)
            row["status"] = "completed"
        except Exception as exc:  # noqa: BLE001 - Preserve failures for registered cells.
            row = {
                "transition": str(transition),
                "emissions": [str(v) for v in emissions],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        payload["cells"].append(row)
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "transition": str(transition),
                    "emission0": str(emissions[0]),
                    "status": row["status"],
                    "calendar_minus_cap": row.get("calendar_minus_cap"),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
