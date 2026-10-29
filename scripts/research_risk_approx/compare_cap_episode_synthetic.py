"""Registered known-model comparison of capped planner and episode baseline."""

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
from compare_switching_episode_composition import episode_policy

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

OUT = ROOT / "docs/risk_preserving_approx/cap_episode_synthetic_v1.json"


def evaluate(game, policy):
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    noquery = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    base = sum(game.expected_metrics(noquery)[:3])
    activation = min(F(1), game.config.alpha / risk) if risk else F(1)
    cost = sum(metrics[:3])
    return {
        "raw_cost": str(cost),
        "raw_risk": str(risk),
        "activation": str(activation),
        "safe_cost": str(activation * cost + (1 - activation) * base),
        "safe_risk_bound": str(activation * risk),
        "metrics": [str(x) for x in metrics],
    }


def solver(config, model, cap):
    game = (
        FirstPromotionDecomposedGame(config, model)
        if cap is None
        else PrePromotionCapGame(config, model, pre_cap=cap)
    )
    start = time.perf_counter()
    report, policy, _ = game.solve()
    elapsed = time.perf_counter() - start
    result = evaluate(game, policy)
    result.update(
        {
            "numeric_objective": report["solver_objective"],
            "nodes": game.nodes,
            "learner_sequences": game.learner.count,
            "null_sequences": game.opponent.count,
            "solve_including_build_and_internal_eval_s": elapsed,
            "equality_residual": report["equality_residual"],
            "inequality_violation": report["inequality_violation"],
        }
    )
    if (
        F(result["safe_risk_bound"]) > config.alpha
        or abs(float(F(result["raw_cost"])) - report["solver_objective"]) > 1e-7
    ):
        raise ValueError("Solver risk or recovered cost failed")
    return result


def run_cell(transition, emissions):
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
    full = solver(config, model, None)
    cap = solver(config, model, 2)
    eligible = tuple(range(1, config.horizon - config.delay + 1))
    calendars = [c for n in range(config.budget + 1) for c in combinations(eligible, n)]
    baseline = []
    for calendar, spending in product(calendars, ("geometric", "equal", "frontloaded")):
        game = CausalSwitchingGame(config, model)
        result = evaluate(game, episode_policy(game, calendar, spending))
        if F(result["raw_risk"]) > config.alpha or len(calendar) > config.budget:
            raise ValueError(f"Baseline violates contract: {calendar} {spending}")
        result.update({"calendar": calendar, "spending": spending})
        baseline.append(result)
    best = min(baseline, key=lambda x: F(x["safe_cost"]))
    return {
        "transition": str(transition),
        "emissions": [str(x) for x in emissions],
        "full": full,
        "cap2": cap,
        "best_episode": best,
        "baseline_candidates": len(baseline),
        "episode_minus_cap": str(F(best["safe_cost"]) - F(cap["safe_cost"])),
        "cap_minus_full": str(F(cap["safe_cost"]) - F(full["safe_cost"])),
    }


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    sources = [
        Path(__file__),
        ROOT / "scripts/compare_switching_episode_composition.py",
        ROOT / "src/shiftlab/dive/prepromotion_cap.py",
        ROOT / "src/shiftlab/dive/first_promotion_decomposition.py",
        ROOT / "src/shiftlab/dive/causal_switching_game.py",
        ROOT / "docs/risk_preserving_approx/CAP_EPISODE_SYNTHETIC_PROTOCOL_V1.md",
    ]
    payload = {
        "hashes": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
        "cells": [],
    }
    for transition, emissions in product(
        (F(1, 10), F(1, 4), F(9, 20)), ((F(1, 10), F(9, 10)), (F(1, 50), F(49, 50)))
    ):
        try:
            row = run_cell(transition, emissions)
            row["status"] = "completed"
        except Exception as exc:  # noqa: BLE001 - Preserve registered cell failures.
            row = {
                "transition": str(transition),
                "emissions": [str(x) for x in emissions],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        payload["cells"].append(row)
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "transition": str(transition),
                    "emissions": [str(x) for x in emissions],
                    "status": row["status"],
                    "episode_minus_cap": row.get("episode_minus_cap"),
                    "cap_minus_full": row.get("cap_minus_full"),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
