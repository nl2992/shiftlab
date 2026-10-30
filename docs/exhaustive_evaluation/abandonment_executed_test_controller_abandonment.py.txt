"""Registered finite-class repair from exposed optimal-policy diagnostics."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from scripts.exhaustive_evaluation.pilot_controller_synthesis import (
    StreakController,
    alternative_cost,
    exact_root_mixture,
)
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


@dataclass(frozen=True)
class EvaluationController:
    start: int
    stride: int
    threshold: int
    mode: str

    @property
    def initial_state(self):
        return 0

    def step(self, memory, time, released, previous_action, remaining_queries):
        for y in released:
            if self.mode == "abort":
                memory = -1 if memory < 0 or not y else memory + 1
            else:
                memory += y
        action = int(previous_action or memory >= self.threshold)
        query = int(
            not action
            and memory >= 0
            and remaining_queries > 0
            and time >= self.start
            and (time - self.start) % self.stride == 0
        )
        return action, query, min(memory, self.threshold)


def embed(controller, game):
    def policy(history, outcomes):
        t = len(history) + 1
        memory = controller.initial_state
        for event in range(1, t + 1):
            released = tuple(y for issue, y in outcomes if issue + game.config.delay == event)
            old = history[event - 2][0] if event >= 2 else 0
            remaining = game.config.budget - sum(q for _, q in history[: event - 1])
            action, query, memory = controller.step(memory, event, released, old, remaining)
        return tuple(F(choice == (action, query)) for choice in game.choices(history))

    return policy


def main():
    regpath = DOC / "controller_abandonment_registration.json"
    if regpath.exists():
        raise FileExistsError("retain exposed-development repair evidence")
    parent = json.loads((DOC / "controller_value_comparison_results.json").read_text())
    base = [StreakController(a, b, k) for a, b, k in product([1, 2, 3], [1, 2], range(1, 6))] + [
        StreakController(1, 1, 1, "never"),
        StreakController(1, 1, 1, "always"),
    ]
    added = [
        EvaluationController(a, b, k, mode)
        for mode in ["abort", "count"]
        for a, b, k in product([1, 2, 3], [1, 2], range(1, 6))
    ]
    controllers = base + added
    sources = [
        Path(__file__),
        ROOT / "scripts/exhaustive_evaluation/pilot_controller_synthesis.py",
        ROOT / "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
        ROOT / "src/shiftlab/dive/causal_switching_game.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "mechanism-driven repair on exposed overlap cells, NOT confirmation or novelty",
        "hypothesis": "abort evaluation after first released zero avoids sunk queries; compare cumulative-positive and streak rules",
        "controllers": [{"type": type(c).__name__, **asdict(c)} for c in controllers],
        "count": 92,
        "cells": [r["cell"] for r in parent["rows"]],
        "alpha": "1/20",
        "contract": "same known IID4/5, query1/100,switch1/10; root mixture sufficient-risk bound; full causal null; same delayed clock",
        "reference_sha256": hashlib.sha256(
            (DOC / "controller_value_comparison_results.json").read_bytes()
        ).hexdigest(),
        "sources_sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    rows = []
    model = RegimeModel(
        transition01=0, transition10=0, emission0=F(1, 5), emission1=F(4, 5), prior1=1
    )
    for original in parent["rows"]:
        horizon, budget, delay = original["cell"]
        records = []
        for c in controllers:
            risk = verify_causal_null_risk(c, horizon=horizon, budget=budget, delay=delay).risk
            cost, _ = alternative_cost(c, horizon=horizon, budget=budget, delay=delay)
            records.append({"risk": risk, "cost": cost})
        subsets = {
            "streak": list(range(32)),
            "streak_plus_abort": list(range(62)),
            "streak_plus_count": list(range(32)) + list(range(62, 92)),
            "all": list(range(92)),
        }
        contrasts = {}
        game = CausalSwitchingGame(
            GameConfig(
                horizon=horizon,
                budget=budget,
                delay=delay,
                alpha=F(1, 20),
                query_cost=F(1, 100),
                switch_cost=F(1, 10),
            ),
            model,
        )
        for name, indices in subsets.items():
            cost, mix = exact_root_mixture([records[i] for i in indices], F(1, 20))
            translated = [(indices[i], weight) for i, weight in mix]
            risk = sum(records[i]["risk"] * w for i, w in translated)
            assert risk <= F(1, 20)
            for i, _ in translated:
                policy = embed(controllers[i], game)
                assert sum(game.expected_metrics(policy)[:3]) == records[i]["cost"]
                assert game.null_risk(policy) == records[i]["risk"]
            reference = F(original["game_report"]["calibrated_total_cost"])
            contrasts[name] = {
                "cost": str(cost),
                "risk_upper": str(risk),
                "difference_vs_verified_reference_policy": str(cost - reference),
                "mixture": [
                    {"id": i, "weight": str(w), "controller": reg["controllers"][i]}
                    for i, w in translated
                ],
            }
        assert contrasts["streak"]["cost"] == original["finite_class_cost"]
        rows.append({"cell": original["cell"], "contrasts": contrasts})
        print(original["cell"], contrasts["all"]["cost"], flush=True)
    (DOC / "controller_abandonment_results.json").write_text(
        json.dumps({"status": "completed", "rows": rows}, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
