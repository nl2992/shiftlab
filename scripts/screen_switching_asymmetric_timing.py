"""Registered asymmetric-HMM adaptive query-timing development screen."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class CalendarGame(CausalSwitchingGame):
    def __init__(self, config, model, calendar):
        super().__init__(config, model)
        self.calendar = frozenset(calendar)

    def choices(self, history):
        remaining = self.config.budget - sum(query for _, query in history)
        time = len(history) + 1
        query_options = (0, 1) if remaining and time in self.calendar else (0,)
        return tuple(product((0, 1), query_options))


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
    transitions = (
        (F(1, 10), F(3, 10), F(1, 2)),
        (F(3, 10), F(1, 10), F(1, 2)),
        (F(1, 10), F(3, 10), F(4, 5)),
        (F(3, 10), F(1, 10), F(1, 5)),
    )
    eligible = tuple(range(1, config.horizon - config.delay + 1))
    calendars = tuple(
        calendar for size in range(config.budget + 1) for calendar in combinations(eligible, size)
    )
    cells = []
    for p01, p10, prior1 in transitions:
        model = RegimeModel(
            transition01=p01,
            transition10=p10,
            emission0=F(1, 20),
            emission1=F(19, 20),
            prior1=prior1,
        )
        full_report, _, _ = CausalSwitchingGame(config, model).solve()
        rows = []
        for calendar in calendars:
            report, _, _ = CalendarGame(config, model, calendar).solve()
            assert F(report["calibrated_risk_bound"]) <= config.alpha
            rows.append(
                {
                    "calendar": list(calendar),
                    "raw_cost": report["raw_recovered_cost"],
                    "raw_risk": report["raw_causal_null_risk"],
                    "calibrated_cost": report["calibrated_total_cost"],
                    "calibrated_risk": report["calibrated_risk_bound"],
                    "queries": report["calibrated_metrics"]["queries"],
                    "switches": report["calibrated_metrics"]["switches"],
                    "nodes": report["nodes"],
                    "learner_sequences": report["learner_sequences"],
                    "solver_objective": report["solver_objective"],
                    "solver_residual": report["inequality_violation"],
                }
            )
        best = min(rows, key=lambda row: F(row["calibrated_cost"]))
        cells.append(
            {
                "model": {
                    "transition01": str(p01),
                    "transition10": str(p10),
                    "prior1": str(prior1),
                },
                "adaptive_raw_cost": full_report["raw_recovered_cost"],
                "adaptive_raw_risk": full_report["raw_causal_null_risk"],
                "adaptive_calibrated_cost": full_report["calibrated_total_cost"],
                "adaptive_calibrated_risk": full_report["calibrated_risk_bound"],
                "adaptive_queries": full_report["calibrated_metrics"]["queries"],
                "adaptive_switches": full_report["calibrated_metrics"]["switches"],
                "adaptive_nodes": full_report["nodes"],
                "adaptive_sequences": full_report["learner_sequences"],
                "best_fixed_calendar": best,
                "fixed_minus_adaptive_cost": str(
                    F(best["calibrated_cost"]) - F(full_report["calibrated_total_cost"])
                ),
                "calendar_rows": rows,
            }
        )
    report = {
        "status": "completed_registered_asymmetric_timing_screen",
        "protocol": "docs/switching_asymmetric_timing_protocol_v1.md",
        "config": {key: str(value) for key, value in vars(config).items()},
        "eligible_events": eligible,
        "fixed_calendars": len(calendars),
        "cells": cells,
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                "scripts/screen_switching_asymmetric_timing.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_asymmetric_timing_protocol_v1.md",
            )
        },
        "scope": "Numerical finite development screen with exact recovered-policy risk checks; not certified optimum, novelty or efficacy evidence.",
    }
    out = Path("outputs/switching_asymmetric_timing_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
