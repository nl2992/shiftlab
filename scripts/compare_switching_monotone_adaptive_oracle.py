"""Compare unrestricted and monotone-promotion causal planners on one HMM cell."""

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


def solve(config: GameConfig, model: RegimeModel, monotone: bool) -> dict:
    game = CausalSwitchingGame(config, model)
    report, policy, records = game.solve(monotone_promotion=monotone)
    tapes = tuple(product((0, 1), repeat=config.horizon))
    promotion_probability_by_tape = {}
    for tape in tapes:

        @cache
        def visit(history, outcomes):
            time = len(history) + 1
            if time > config.horizon:
                return F(0)
            total = F(0)
            for (action, query), probability in zip(
                game.choices(history), policy(history, outcomes), strict=True
            ):
                if action:
                    total += probability
                    continue
                next_outcomes = outcomes
                if query:
                    next_outcomes += ((time, tape[time - 1]),)  # noqa: B023 - Consumed synchronously within this loop iteration.
                total += probability * visit(history + ((action, query),), next_outcomes)
            return total

        promotion_probability_by_tape[tape] = visit((), ())

    monotonicity_violations = []
    for tape in tapes:
        for index, bit in enumerate(tape):
            if bit:
                continue
            successor = tape[:index] + (1,) + tape[index + 1 :]
            if promotion_probability_by_tape[tape] > promotion_probability_by_tape[successor]:
                monotonicity_violations.append((tape, successor))
    decisions = []
    for record in records:
        probabilities = tuple(F(value) for value in record["probabilities"])
        pairs = tuple(zip(record["choices"], probabilities, strict=True))
        query_probability = sum(probability for (_, query), probability in pairs if query)
        previous_action = record["history"][-1][0] if record["history"] else 0
        rollback_probability = sum(
            probability for (action, _), probability in pairs if previous_action and not action
        )
        if query_probability or rollback_probability:
            decisions.append(
                {
                    "history": record["history"],
                    "released": record["released"],
                    "query_probability": str(query_probability),
                    "rollback_probability": str(rollback_probability),
                }
            )
    report["query_and_rollback_decisions"] = decisions
    report["promotion_probability_by_tape"] = {
        "".join(map(str, tape)): str(probability)
        for tape, probability in promotion_probability_by_tape.items()
    }
    report["recovered_event_is_monotone"] = not monotonicity_violations
    report["recovered_event_monotonicity_violations"] = monotonicity_violations
    return report


def main() -> None:
    config = GameConfig(
        horizon=6,
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
    unrestricted = solve(config, model, monotone=False)
    monotone = solve(config, model, monotone=True)
    paths = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/compare_switching_monotone_adaptive_oracle.py",
    )
    result = {
        "status": "single_cell_adaptive_acquisition_monotone_class_diagnostic",
        "config": asdict(config),
        "working_model": asdict(model),
        "comparison": {
            "unrestricted": unrestricted,
            "monotone_first_promotion_event": monotone,
            "recovered_cost_difference_monotone_minus_unrestricted": str(
                F(monotone["calibrated_total_cost"]) - F(unrestricted["calibrated_total_cost"])
            ),
        },
        "interpretation": (
            "Finite known-HMM causal-game diagnostic; both costs are exact evaluations of "
            "numerically recovered policies, not certified optima."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths
        },
    }
    target = Path("outputs/switching_monotone_adaptive_oracle_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(
        json.dumps(result, default=str, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                name: {
                    key: report[key]
                    for key in (
                        "calibrated_total_cost",
                        "raw_causal_null_risk",
                        "calibrated_metrics",
                        "monotone_promotion_constraint",
                    )
                }
                | {"query_decision_count": len(report["query_and_rollback_decisions"])}
                for name, report in (
                    ("unrestricted", unrestricted),
                    ("monotone", monotone),
                )
            }
            | {
                "cost_difference": result["comparison"][
                    "recovered_cost_difference_monotone_minus_unrestricted"
                ]
            },
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
