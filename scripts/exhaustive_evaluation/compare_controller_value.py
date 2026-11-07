"""Matched known-model finite-class upper values versus unrestricted numerical LP."""

import hashlib
import json
import time
from dataclasses import asdict
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


def main():
    regpath = DOC / "controller_value_comparison_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing process before restart")
    configs = [StreakController(a, b, k) for a, b, k in product([1, 2, 3], [1, 2], range(1, 6))] + [
        StreakController(1, 1, 1, "never"),
        StreakController(1, 1, 1, "always"),
    ]
    sources = [
        "scripts/exhaustive_evaluation/compare_controller_value.py",
        "scripts/exhaustive_evaluation/pilot_controller_synthesis.py",
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "matched model-quality diagnostic, not new synthesis theorem",
        "cells": [[4, 3, 1], [4, 3, 2], [5, 4, 1], [5, 4, 2]],
        "alpha": "1/20",
        "alternative_positive": "4/5",
        "query_cost": "1/100",
        "switch_cost": "1/10",
        "controllers": [asdict(c) for c in configs],
        "node_cap": 200000,
        "primary": "finite-class exact feasible cost minus numerical unrestricted LP objective; no certified lower value claim from solver objective alone",
        "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    statuspath = DOC / "controller_value_comparison_status.json"
    status = {"status": "running", "completed": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    rows = []
    model = RegimeModel(
        transition01=0, transition10=0, emission0=F(1, 5), emission1=F(4, 5), prior1=1
    )
    for horizon, budget, delay in reg["cells"]:
        records = []
        start = time.perf_counter()
        for controller in configs:
            risk = verify_causal_null_risk(
                controller, horizon=horizon, budget=budget, delay=delay
            ).risk
            cost, _ = alternative_cost(controller, horizon=horizon, budget=budget, delay=delay)
            records.append({"risk": risk, "cost": cost})
        upper, mix = exact_root_mixture(records, F(1, 20))
        class_seconds = time.perf_counter() - start
        game = CausalSwitchingGame(
            GameConfig(
                horizon=horizon,
                budget=budget,
                delay=delay,
                alpha=F(1, 20),
                query_cost=F(1, 100),
                switch_cost=F(1, 10),
                max_nodes=200000,
            ),
            model,
        )
        start = time.perf_counter()
        try:
            report, _policy, _ = game.solve()
            runtime = time.perf_counter() - start
            assert F(report["calibrated_risk_bound"]) <= F(1, 20)
            assert report["solver_objective"] <= float(upper) + 1e-7

            # A class member belongs to the same extensive-form policy set.
            def as_game_policy(controller, *, delay=delay, budget=budget, game=game):
                def value(history, outcomes):
                    t = len(history) + 1
                    memory = 0
                    for event in range(1, t + 1):
                        released = tuple(y for issue, y in outcomes if issue + delay == event)
                        old = history[event - 2][0] if event >= 2 else 0
                        remaining = budget - sum(q for _, q in history[: event - 1])
                        action, query, memory = controller.step(
                            memory, event, released, old, remaining
                        )
                    return tuple(F(choice == (action, query)) for choice in game.choices(history))

                return value

            for i, _weight in mix:
                metrics = game.expected_metrics(as_game_policy(configs[i]))
                assert sum(metrics[:3]) == records[i]["cost"]
                assert game.null_risk(as_game_policy(configs[i])) == records[i]["risk"]
            rows.append(
                {
                    "cell": [horizon, budget, delay],
                    "status": "completed",
                    "finite_class_cost": str(upper),
                    "class_seconds": class_seconds,
                    "unrestricted_seconds": runtime,
                    "numerical_objective_difference": float(upper) - report["solver_objective"],
                    "relative_difference": (float(upper) - report["solver_objective"])
                    / report["solver_objective"],
                    "finite_class_mixture": [
                        {"id": i, "weight": str(w), "controller": asdict(configs[i])}
                        for i, w in mix
                    ],
                    "game_report": report,
                    "matched_class_policy_forward_checks": True,
                }
            )
        except RuntimeError as exc:
            rows.append(
                {
                    "cell": [horizon, budget, delay],
                    "status": "capped_or_solver_failure",
                    "message": str(exc),
                    "finite_class_cost": str(upper),
                    "class_seconds": class_seconds,
                }
            )
        (DOC / "controller_value_comparison_results.json").write_text(
            json.dumps({"rows": rows}, indent=2), encoding="utf-8"
        )
        status["completed"].append([horizon, budget, delay])
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(rows[-1]["cell"], rows[-1]["status"], flush=True)
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    main()
