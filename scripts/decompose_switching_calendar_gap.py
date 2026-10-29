"""Attribute causal-planner headroom to calendar timing vs. policy class."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class CalendarOpportunityGame(CausalSwitchingGame):
    """Causal game where queries may occur only at declared calendar slots."""

    def __init__(self, config, model, calendar):
        super().__init__(config, model)
        self.calendar = frozenset(calendar)

    def choices(self, history):
        remaining = self.config.budget - sum(query for _, query in history)
        assert remaining >= 0
        time = len(history) + 1
        query_choices = (0, 1) if remaining and time in self.calendar else (0,)
        return tuple(product((0, 1), query_choices))


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
        calendar for size in range(config.budget + 1) for calendar in combinations(eligible, size)
    ]
    previous = json.loads(
        Path("outputs/switching_episode_composition_grid_v1/results.json").read_text(
            encoding="utf-8"
        )
    )
    episode_results = {
        (
            row["model"]["transition"],
            row["model"]["emission0"],
            row["model"]["emission1"],
        ): row["best_composition"]
        for row in previous["cells"]
    }
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
            unrestricted = CausalSwitchingGame(config, model)
            unrestricted_report, _, _ = unrestricted.solve()
            calendar_rows = []
            for calendar in calendars:
                game = CalendarOpportunityGame(config, model, calendar)
                report, _, _ = game.solve()
                assert F(report["calibrated_risk_bound"]) <= config.alpha
                calendar_rows.append(
                    {
                        "calendar": list(calendar),
                        "calibrated_cost": report["calibrated_total_cost"],
                        "calibrated_risk": report["calibrated_risk_bound"],
                        "raw_policy_cost": report["raw_recovered_cost"],
                        "raw_policy_risk": report["raw_causal_null_risk"],
                        "activation_probability": report["activation_probability"],
                        "solver_objective": report["solver_objective"],
                        "nodes": report["nodes"],
                    }
                )
            best = min(calendar_rows, key=lambda row: F(row["calibrated_cost"]))
            key = (str(transition), str(emission0), str(emission1))
            episode = episode_results[key]
            unrestricted_cost = F(unrestricted_report["calibrated_total_cost"])
            fixed_cost = F(best["calibrated_cost"])
            episode_cost = F(episode["total_cost"])
            cells.append(
                {
                    "model": {
                        "transition": str(transition),
                        "emission0": str(emission0),
                        "emission1": str(emission1),
                    },
                    "unrestricted_recovered_policy_cost": str(unrestricted_cost),
                    "unrestricted_policy_risk": unrestricted_report["calibrated_risk_bound"],
                    "best_fixed_calendar_robust_planner": best,
                    "best_episode_composition_cost": str(episode_cost),
                    "fixed_calendar_minus_unrestricted": str(fixed_cost - unrestricted_cost),
                    "episode_composition_minus_fixed_calendar": str(episode_cost - fixed_cost),
                    "calendar_lp_rows": calendar_rows,
                }
            )
    result = {
        "status": "completed_registered_mechanism_attribution_screen",
        "protocol": "docs/switching_episode_composition_grid_protocol_v1.md",
        "interpretation": "Unrestricted minus best fixed-calendar planner estimates query-opportunity timing value. Best fixed-calendar planner minus episode composition estimates policy/test-class value within a calendar. Each LP result is numerical; recovered policies are safety calibrated and independently evaluated.",
        "cells": cells,
        "sha256": {
            source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
            for source in (
                "scripts/decompose_switching_calendar_gap.py",
                "scripts/screen_switching_episode_composition_grid.py",
                "scripts/compare_switching_episode_composition.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_episode_composition_grid_protocol_v1.md",
            )
        },
        "scope": "Finite model-class attribution only; not a theorem, candidate efficacy result, or certified oracle comparison.",
    }
    target = Path("outputs/switching_calendar_gap_decomposition_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
