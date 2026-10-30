"""Registered finite-grid falsification screen for monotone first promotions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from fractions import Fraction as F
from functools import cache
from itertools import product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

CELLS = (
    ("M1", 5, 3, 1, F(1, 10), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M2", 5, 3, 1, F(1, 20), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M3", 5, 3, 1, F(1, 5), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M4", 5, 3, 2, F(1, 10), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M5", 5, 2, 1, F(1, 10), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M6", 5, 3, 1, F(1, 10), F(1, 10), F(1, 10), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M7", 5, 3, 1, F(1, 10), F(1, 100), F(1), F(1, 4), F(1, 4), F(1, 10), F(9, 10)),
    ("M8", 5, 3, 1, F(1, 10), F(1, 100), F(1, 10), F(1, 10), F(3, 10), F(1, 10), F(9, 10)),
    ("M9", 5, 3, 1, F(1, 10), F(1, 100), F(1, 10), F(1, 4), F(1, 4), F(1, 4), F(3, 4)),
)


def promotion_tape_probabilities(game, policy):
    values = {}
    for tape in product((0, 1), repeat=game.config.horizon):

        @cache
        def visit(history, outcomes):
            time = len(history) + 1
            if time > game.config.horizon:
                return F(0)
            total = F(0)
            for (action, query), mass in zip(
                game.choices(history), policy(history, outcomes), strict=True
            ):
                if action:
                    total += mass
                    continue
                next_outcomes = outcomes + (((time, tape[time - 1]),) if query else ())  # noqa: B023 - Consumed synchronously within this loop iteration.
                total += mass * visit(history + ((action, query),), next_outcomes)
            return total

        values[tape] = visit((), ())
    return values


def is_increasing(tape_values):
    for tape, probability in tape_values.items():
        for index, bit in enumerate(tape):
            if bit:
                continue
            successor = tape[:index] + (1,) + tape[index + 1 :]
            if probability > tape_values[successor]:
                return False, (tape, successor)
    return True, None


def run_cell(cell):
    name, horizon, budget, delay, alpha, query_cost, switch_cost, p01, p10, emission0, emission1 = (
        cell
    )
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=alpha,
        query_cost=query_cost,
        switch_cost=switch_cost,
    )
    model = RegimeModel(
        transition01=p01,
        transition10=p10,
        emission0=emission0,
        emission1=emission1,
        prior1=F(1, 2),
    )
    comparisons = {}
    for label, constrained in (("unrestricted", False), ("monotone", True)):
        game = CausalSwitchingGame(config, model)
        report, policy, _ = game.solve(monotone_promotion=constrained)
        tape_values = promotion_tape_probabilities(game, policy)
        monotonicity, witness = is_increasing(tape_values)
        if constrained and not monotonicity:
            raise AssertionError(f"{name}: constrained policy violates monotonicity at {witness}")
        comparisons[label] = {
            "solver_objective": report["solver_objective"],
            "equality_residual": report["equality_residual"],
            "inequality_violation": report["inequality_violation"],
            "raw_recovered_cost": report["raw_recovered_cost"],
            "raw_causal_null_risk": report["raw_causal_null_risk"],
            "iid_boundary_risk": report["iid_boundary_risk"],
            "activation_probability": report["activation_probability"],
            "calibrated_risk_bound": report["calibrated_risk_bound"],
            "calibrated_total_cost": report["calibrated_total_cost"],
            "recovered_event_is_monotone": monotonicity,
            "monotonicity_witness": witness,
            "promotion_probability_by_tape": {
                "".join(map(str, tape)): str(probability)
                for tape, probability in tape_values.items()
            },
        }
    unrestricted_cost = F(comparisons["unrestricted"]["calibrated_total_cost"])
    monotone_cost = F(comparisons["monotone"]["calibrated_total_cost"])
    gap = monotone_cost - unrestricted_cost
    if gap < -F(1, 100_000_000):
        raise AssertionError(f"{name}: constrained optimum improved by {gap}; solver inconsistency")
    residual = max(
        comparisons[label][key]
        for label in comparisons
        for key in ("equality_residual", "inequality_violation")
    )
    return {
        "cell": name,
        "config": asdict(config),
        "model": asdict(model),
        "comparisons": comparisons,
        "monotone_minus_unrestricted_cost": str(gap),
        "solver_residual_max": residual,
        "registered_gap_falsifier_fires": gap > F(1, 100_000),
    }


def main():
    results = [run_cell(cell) for cell in CELLS]
    sources = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/screen_switching_monotone_promotion_grid.py",
    )
    payload = {
        "status": "registered_structural_falsification_grid",
        "protocol": "docs/switching_monotone_promotion_grid_protocol_v1.md",
        "cells": results,
        "summary": {
            "cell_count": len(results),
            "falsifier_cells": [
                result["cell"] for result in results if result["registered_gap_falsifier_fires"]
            ],
            "max_cost_gap": str(
                max(F(result["monotone_minus_unrestricted_cost"]) for result in results)
            ),
            "all_unrestricted_policies_monotone": all(
                result["comparisons"]["unrestricted"]["recovered_event_is_monotone"]
                for result in results
            ),
        },
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sources
        },
    }
    output = Path("outputs/switching_monotone_promotion_grid_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
