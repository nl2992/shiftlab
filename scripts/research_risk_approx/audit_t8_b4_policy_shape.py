"""Audit the recovered T=8, B=4 adaptive planner's query structure."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/T8_B4_POLICY_SHAPE_PROTOCOL_V1.md"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_b4_policy_shape_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recover_alt_policy_shape(game, policy):
    info_mass = defaultdict(F)
    choices_mass = defaultdict(lambda: defaultdict(F))

    def visit(history, outcomes, posterior1, mass):
        time_index = len(history) + 1
        if time_index > game.config.horizon or not mass:
            return
        belief = game._belief_from_history(history, outcomes)
        posterior = sum((p for state, _pending, p in belief if state), F(0))
        info = game.information(history, outcomes)
        probabilities = policy(history, outcomes)
        choices = game.choices(history)
        info_mass[info] += mass
        for choice, action_mass in zip(choices, probabilities, strict=True):
            if not action_mass:
                continue
            action, query = choice
            choices_mass[info][choice] += mass * action_mass
            if action:
                continue
            following = history + (choice,)
            state1 = game.model.propagate(posterior, 1)
            positive = game.model.emission(state1)
            if query:
                for label, probability in ((0, 1 - positive), (1, positive)):
                    likelihood = game.model.emission1 if label else 1 - game.model.emission1
                    next_posterior = state1 * likelihood / probability
                    visit(
                        following,
                        outcomes + ((time_index, label),),
                        next_posterior,
                        mass * action_mass * probability,
                    )
            elif time_index < game.config.horizon:
                visit(following, outcomes, state1, mass * action_mass)

    visit((), (), game.model.prior1, F(1))
    rows = []
    grouped = defaultdict(lambda: {"mass": F(0), "query_mass": F(0), "promotion_mass": F(0)})
    for (history, released), total_mass in sorted(info_mass.items()):
        time_index = len(history) + 1
        query_events = tuple(
            event for event, (_action, query) in enumerate(history, start=1) if query
        )
        posterior1 = sum(
            (p for state, _pending, p in game._belief_from_history(history, released) if state),
            F(0),
        )
        action_probs = {
            choice: value / total_mass
            for choice, value in choices_mass[(history, released)].items()
        }
        query_probability = sum((prob for choice, prob in action_probs.items() if choice[1]), F(0))
        promotion_probability = sum(
            (prob for choice, prob in action_probs.items() if choice[0]), F(0)
        )
        key = (time_index, sum(query for _, query in history), query_events, released)
        grouped[key]["mass"] += total_mass
        grouped[key]["query_mass"] += total_mass * query_probability
        grouped[key]["promotion_mass"] += total_mass * promotion_probability
        rows.append(
            {
                "history": [list(choice) for choice in history],
                "released": [list(item) for item in released],
                "alt_reach_mass": str(total_mass),
                "alternative_posterior_state1": str(posterior1),
                "query_probability": str(query_probability),
                "promotion_probability": str(promotion_probability),
            }
        )
    grouped_rows = []
    for key, stats in sorted(grouped.items()):
        time_index, count, query_events, released = key
        grouped_rows.append(
            {
                "time": time_index,
                "queries_so_far": count,
                "query_events": list(query_events),
                "released": [list(item) for item in released],
                "alt_reach_mass": str(stats["mass"]),
                "mean_query_probability": str(stats["query_mass"] / stats["mass"]),
                "mean_promotion_probability": str(stats["promotion_mass"] / stats["mass"]),
            }
        )
    return rows, grouped_rows


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    config = GameConfig(
        horizon=8,
        budget=4,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    game = FirstPromotionDecomposedGame(config, model)
    started = time.perf_counter()
    report, policy, records = game.solve()
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    shape, grouped = recover_alt_policy_shape(game, policy)
    if max((sum(query for _, query in row["history"]) for row in shape), default=0) > config.budget:
        raise AssertionError("reconstructed path exceeded the hard query budget")
    payload = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "source_hashes": {
            path: sha(ROOT / path)
            for path in (
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/first_promotion_decomposition.py",
            )
        },
        "solver_objective": report["solver_objective"],
        "exact_cost": str(sum(metrics[:3])),
        "exact_risk": str(risk),
        "metrics": [str(value) for value in metrics],
        "nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "alternative_reachable_infos": len(shape),
        "policy_shape": shape,
        "grouped_query_summary": grouped,
        "behavior_records": records,
        "runtime_seconds": time.perf_counter() - started,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "cost": payload["exact_cost"],
                "risk": payload["exact_risk"],
                "reachable_infos": len(shape),
                "grouped_rows": len(grouped),
                "runtime_seconds": payload["runtime_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
