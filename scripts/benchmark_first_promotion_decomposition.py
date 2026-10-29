"""Compare the exact first-promotion reduction with the generic two-law oracle."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "first_promotion_decomposition_scaling_v1"


def summarize(game, report, policy):
    metrics = game.expected_metrics(policy)
    return {
        "nodes": report["nodes"],
        "learner_sequences": report["learner_sequences"],
        "learner_information_sets": len(game.learner.infos),
        "opponent_sequences": report["opponent_sequences"],
        "solver_objective": report["solver_objective"],
        "recovered_cost": str(sum(metrics[:3])),
        "metrics": [str(value) for value in metrics],
        "causal_null_risk": str(game.null_risk(policy)),
        "pathwise_query_cap": game.config.budget,
    }


def main() -> dict[str, object]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    rows = []
    for horizon in (6, 7, 8):
        config = GameConfig(
            horizon=horizon,
            budget=3,
            delay=1,
            alpha=F(1, 10),
            query_cost=F(1, 100),
            switch_cost=F(1, 10),
            max_nodes=200_000,
        )
        row: dict[str, object] = {"horizon": horizon, "budget": 3, "delay": 1}
        try:
            full = CausalSwitchingGame(config, model)
            full_report, full_policy, _ = full.solve()
            reduced = FirstPromotionDecomposedGame(config, model)
            reduced_report, reduced_policy, _ = reduced.solve()
            full_summary = summarize(full, full_report, full_policy)
            reduced_summary = summarize(reduced, reduced_report, reduced_policy)
            full_cost = F(full_summary["recovered_cost"])
            reduced_cost = F(reduced_summary["recovered_cost"])
            assert full.null_risk(full_policy) <= config.alpha
            assert reduced.null_risk(reduced_policy) <= config.alpha
            assert abs(float(full_cost) - full_report["solver_objective"]) <= 1e-7
            assert abs(float(reduced_cost) - reduced_report["solver_objective"]) <= 1e-7
            assert abs(float(full_cost) - float(reduced_cost)) <= 1e-7
            row.update(
                {
                    "status": "completed",
                    "full": full_summary,
                    "decomposed": reduced_summary,
                }
            )
        except RuntimeError as error:  # Preserve registered node/time-limit failures as data.
            row.update({"status": "failed", "failure": f"{type(error).__name__}: {error}"})
        rows.append(row)
        (OUTPUT / "results.json").write_text(
            json.dumps(
                {
                    "protocol": "docs/switching_first_promotion_scaling_protocol_v1.md",
                    "model": {
                        "transition01": "1/4",
                        "transition10": "1/4",
                        "emission0": "1/20",
                        "emission1": "19/20",
                        "prior1": "1/2",
                    },
                    "rows": rows,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if row["status"] != "completed":
            break
    hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in (
            ROOT / "scripts" / "benchmark_first_promotion_decomposition.py",
            ROOT / "src" / "shiftlab" / "dive" / "first_promotion_decomposition.py",
            ROOT / "src" / "shiftlab" / "dive" / "causal_switching_game.py",
            ROOT / "docs" / "switching_first_promotion_scaling_protocol_v1.md",
        )
    }
    result: dict[str, object] = {"rows": rows, "sha256": hashes}
    (OUTPUT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
