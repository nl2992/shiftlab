"""Registered exact-arithmetic screen of promotion dominance bounds."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cell(horizon: int) -> dict:
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    config = GameConfig(
        horizon=horizon,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    game = FirstPromotionDecomposedGame(config, model)
    game.build()
    counts = {
        "histories": 0,
        "strictly_dominated": 0,
        "ties": 0,
        "one_cent_near_dominated": 0,
        "continuation_checks": 0,
    }
    min_slack = None
    for history, released in game.learner.infos:
        if any(action for action, _ in history):
            continue
        time = len(history) + 1
        remaining = config.budget - sum(query for _, query in history)
        belief = game._belief_from_history(history, released)
        p1 = sum((mass for state, _, mass in belief if state == 1), F(0))
        stay = F(0)
        lower = config.switch_cost
        for event in range(time, horizon + 1):
            positive = model.emission(p1)
            stay += positive
            if event == time:
                lower += 1 - positive
            else:
                lower += (1 - p1) * min(model.emission0, 1 - model.emission0)
                lower += p1 * min(model.emission1, 1 - model.emission1)
            p1 = model.propagate(p1, 1)
        counts["histories"] += 1
        counts["strictly_dominated"] += lower > stay
        counts["ties"] += lower == stay
        counts["one_cent_near_dominated"] += lower >= stay - F(1, 100)
        for query in (0, 1) if remaining else (0,):
            exact = game._promote_value(time, remaining, belief, query)
            slack = exact - lower
            if slack < 0:
                raise AssertionError((horizon, history, released, query, str(slack)))
            min_slack = slack if min_slack is None else min(min_slack, slack)
            counts["continuation_checks"] += 1
    return {
        "horizon": horizon,
        **counts,
        "minimum_exact_minus_bound": str(min_slack),
        "builder_nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "continuation_decision_cache": len(game._decision_cache),
    }


def main() -> None:
    source = Path(__file__)
    protocol = ROOT / "docs/risk_preserving_approx/PROMOTION_DOMINANCE_PROTOCOL_V1.md"
    result = {
        "protocol": protocol.relative_to(ROOT).as_posix(),
        "source_sha256": sha(source),
        "protocol_sha256": sha(protocol),
        "reference_source_sha256": sha(ROOT / "src/shiftlab/dive/first_promotion_decomposition.py"),
        "starting_commit": "169d17e",
        "seed": None,
        "rows": [run_cell(horizon) for horizon in (5, 6, 7)],
    }
    path = ROOT / "docs/risk_preserving_approx/promotion_dominance_screen_v1.json"
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
