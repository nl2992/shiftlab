"""Registered restricted-LP verification of the promotion dominance screen."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from scipy.optimize import linprog

import shiftlab.dive.causal_switching_game as reference
from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(epsilon: F | None) -> dict:
    config = GameConfig(horizon=6, budget=3, delay=1, alpha=F(1, 10))
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    game = FirstPromotionDecomposedGame(config, model)
    game.build()
    columns: list[int] = []
    histories = 0
    if epsilon is not None:
        for (history, released), (_, children, choices) in game.learner.infos.items():
            if any(action for action, _ in history):
                continue
            time = len(history) + 1
            belief = game._belief_from_history(history, released)
            p1 = sum((mass for state, _, mass in belief if state == 1), F(0))
            stay, lower = F(0), config.switch_cost
            for event in range(time, config.horizon + 1):
                positive = model.emission(p1)
                stay += positive
                if event == time:
                    lower += 1 - positive
                else:
                    lower += (1 - p1) * min(model.emission0, 1 - model.emission0)
                    lower += p1 * min(model.emission1, 1 - model.emission1)
                p1 = model.propagate(p1, 1)
            if lower >= stay - epsilon:
                histories += 1
                columns.extend(
                    child for child, (action, _) in zip(children, choices, strict=True) if action
                )

    def restricted_linprog(*args, **kwargs):
        bounds = list(kwargs["bounds"])
        for column in columns:
            bounds[column] = (0, 0)
        kwargs["bounds"] = bounds
        return linprog(*args, **kwargs)

    original = reference.linprog
    try:
        reference.linprog = restricted_linprog
        report, policy, _ = game.solve()
    finally:
        reference.linprog = original
    risk = game.null_risk(policy)
    return {
        "epsilon": None if epsilon is None else str(epsilon),
        "marked_histories": histories,
        "fixed_promotion_columns": len(columns),
        "solver_objective": report["solver_objective"],
        "recovered_cost": report["raw_recovered_cost"],
        "causal_null_risk": str(risk),
        "risk_feasible": risk <= config.alpha,
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "builder_nodes": report["nodes"],
    }


def main() -> None:
    rows = [evaluate(epsilon) for epsilon in (None, F(0), F(1, 100))]
    full = F(rows[0]["recovered_cost"])
    for row in rows:
        row["recovered_gap"] = str(F(row["recovered_cost"]) - full)
    assert all(row["risk_feasible"] for row in rows), rows
    assert abs(float(F(rows[1]["recovered_gap"]))) <= 1e-7, rows
    assert float(F(rows[2]["recovered_gap"])) <= 0.01 + 1e-7, rows
    protocol = ROOT / "docs/risk_preserving_approx/PROMOTION_RESTRICTED_ORACLE_PROTOCOL_V1.md"
    payload = {
        "protocol": protocol.relative_to(ROOT).as_posix(),
        "protocol_sha256": digest(protocol),
        "source_sha256": digest(Path(__file__)),
        "reference_source_sha256": digest(
            ROOT / "src/shiftlab/dive/first_promotion_decomposition.py"
        ),
        "rows": rows,
    }
    path = ROOT / "docs/risk_preserving_approx/promotion_restricted_oracle_v1.json"
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
