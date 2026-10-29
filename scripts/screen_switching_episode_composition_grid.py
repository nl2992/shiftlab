"""Run the pre-registered six-cell episode-composition sensitivity screen."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

from compare_switching_episode_composition import episode_policy

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    transitions = (F(1, 10), F(1, 4), F(9, 20))
    emission_pairs = ((F(1, 10), F(9, 10)), (F(1, 50), F(49, 50)))
    eligible = tuple(range(1, config.horizon - config.delay + 1))
    calendars = [
        schedule for count in range(config.budget + 1) for schedule in combinations(eligible, count)
    ]
    cells = []
    for transition in transitions:
        for emission0, emission1 in emission_pairs:
            model = RegimeModel(
                transition01=transition,
                transition10=transition,
                emission0=emission0,
                emission1=emission1,
                prior1=F(1, 2),
            )
            contenders = []
            for spending in ("geometric", "equal", "frontloaded"):
                for calendar in calendars:
                    game = CausalSwitchingGame(config, model)
                    policy = episode_policy(game, calendar, spending)
                    metrics = game.expected_metrics(policy)
                    risk = game.null_risk(policy)
                    if risk > config.alpha or len(calendar) > config.budget:
                        raise AssertionError("composition violated registered risk or cap")
                    contenders.append(
                        {
                            "calendar": list(calendar),
                            "spending": spending,
                            "risk": str(risk),
                            "metrics": dict(
                                zip(
                                    (
                                        "decision_cost",
                                        "query_cost",
                                        "switch_cost",
                                        "queries",
                                        "switches",
                                    ),
                                    map(str, metrics),
                                    strict=True,
                                )
                            ),
                            "total_cost": str(sum(metrics[:3])),
                        }
                    )
            best = min(contenders, key=lambda row: F(row["total_cost"]))
            oracle = CausalSwitchingGame(config, model)
            oracle_report, _, _ = oracle.solve()
            cells.append(
                {
                    "model": {
                        "transition": str(transition),
                        "emission0": str(emission0),
                        "emission1": str(emission1),
                        "prior1": str(model.prior1),
                    },
                    "candidate_count": len(contenders),
                    "best_composition": best,
                    "oracle_policy_cost": oracle_report["raw_recovered_cost"],
                    "oracle_policy_risk": oracle_report["raw_causal_null_risk"],
                    "composition_minus_oracle_policy_cost": str(
                        F(best["total_cost"]) - F(oracle_report["raw_recovered_cost"])
                    ),
                    "oracle_solver_objective": oracle_report["solver_objective"],
                    "oracle_nodes": oracle_report["nodes"],
                }
            )
    result = {
        "status": "completed_registered_comparator_sensitivity_screen",
        "protocol": "docs/switching_episode_composition_grid_protocol_v1.md",
        "configuration": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "calendar_count": len(calendars),
            "spending_rules": ["geometric", "equal", "frontloaded"],
        },
        "cells": cells,
        "sha256": {
            source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
            for source in (
                "scripts/screen_switching_episode_composition_grid.py",
                "scripts/compare_switching_episode_composition.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_episode_composition_grid_protocol_v1.md",
            )
        },
        "scope": "Model-aware finite comparator screen; not method efficacy, oracle-gap certification, or real-data validation.",
    }
    target = Path("outputs/switching_episode_composition_grid_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
