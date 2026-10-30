"""Measure exact alternative-mass pruning potential on the registered T=10 cell."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/CANDIDATE_E_PRUNING_FEASIBILITY_PROTOCOL_V1.md"
REFERENCE_PROTOCOL = ROOT / "docs/risk_preserving_approx/IID_RELAXATION_T10_STRESS_PROTOCOL_V1.md"
OUTPUT = ROOT / "docs/risk_preserving_approx/candidate_e_pruning_feasibility_v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_pre_promotion_envelopes(game: CausalSwitchingGame) -> tuple[dict, int]:
    """Enumerate public histories while summing hidden pending-label likelihoods."""
    envelopes: dict[tuple, F] = defaultdict(F)
    hidden_nodes = 0

    def visit(history, outcomes, posterior, weight):
        nonlocal hidden_nodes
        hidden_nodes += 1
        time = len(history) + 1
        if time > game.config.horizon:
            return
        key = game.information(history, outcomes)
        envelopes[key] += weight
        state1 = game.model.propagate(posterior, 1)
        positive = game.model.emission(state1)
        for action, query in game.choices(history):
            if action:
                continue
            next_history = history + ((action, query),)
            if query:
                for y, probability in ((0, 1 - positive), (1, positive)):
                    if not probability:
                        continue
                    likelihood1 = game.model.emission1 if y else 1 - game.model.emission1
                    next_posterior = state1 * likelihood1 / probability
                    visit(
                        next_history,
                        outcomes + ((time, y),),
                        next_posterior,
                        weight * probability,
                    )
            else:
                visit(next_history, outcomes, state1, weight)

    visit((), (), game.model.prior1, F(1))
    return envelopes, hidden_nodes


def candidate_ancestor(key: tuple, depth: int, delay: int) -> tuple | None:
    history, outcomes = key
    if len(history) < depth - 1:
        return None
    prefix = history[: depth - 1]
    released_at_depth = tuple((s, y) for s, y in outcomes if s + delay <= depth)
    return prefix, released_at_depth


def screen_depth(envelopes: dict, horizon: int, budget: int, delay: int, depth: int, delta: F):
    candidates = {
        key: probability
        for key, probability in envelopes.items()
        if len(key[0]) == depth - 1 and all(action == 0 for action, _ in key[0])
    }
    epsilon = delta / (F(111, 100) * (horizon - depth + 1))
    target_envelope = epsilon
    ordered = sorted(candidates.items(), key=lambda item: (item[1], repr(item[0])))
    selected = set()
    mass = F(0)
    for key, probability in ordered:
        if mass + probability > target_envelope:
            continue
        selected.add(key)
        mass += probability

    full_columns = sum(
        len(tuple(product((0, 1), (0, 1) if budget - sum(q for _, q in key[0]) else (0,))))
        for key in candidates
    )
    removed_columns = 0
    removed_infos = 0
    for key in envelopes:
        ancestor = candidate_ancestor(key, depth, delay)
        if ancestor in selected:
            removed_infos += 1
            history = key[0]
            remaining = budget - sum(q for _, q in history)
            removed_columns += len(tuple(product((0, 1), (0, 1) if remaining else (0,))))

    return {
        "decision_event": depth,
        "loss_budget": str(delta),
        "selected_safe_histories": len(selected),
        "candidate_histories_at_depth": len(candidates),
        "policy_uniform_alt_probability_upper_bound": str(mass),
        "certified_value_loss_upper_bound": str(F(111, 100) * (horizon - depth + 1) * mass),
        "collapsed_information_sets": removed_infos,
        "prepromotion_realization_columns_removed": removed_columns,
        "prepromotion_realization_columns_total": full_columns,
        "fraction_prepromotion_columns_removed": (
            str(F(removed_columns, full_columns)) if full_columns else "0"
        ),
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    config = GameConfig(
        horizon=10,
        budget=4,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    game = CausalSwitchingGame(config, model)
    envelopes, hidden_nodes = collect_pre_promotion_envelopes(game)
    total_columns = sum(
        len(tuple(product((0, 1), (0, 1) if config.budget - sum(q for _, q in key[0]) else (0,))))
        for key in envelopes
        if all(action == 0 for action, _ in key[0])
    )
    results = [
        screen_depth(envelopes, config.horizon, config.budget, config.delay, depth, delta)
        for depth in (5, 6, 7, 8)
        for delta in (F(1, 100), F(1, 20))
    ]
    payload = {
        "protocol": PROTOCOL.name,
        "protocol_sha256": digest(PROTOCOL),
        "reference_protocol_sha256": digest(REFERENCE_PROTOCOL),
        "runner_sha256": digest(Path(__file__)),
        "game_source_sha256": digest(ROOT / "src/shiftlab/dive/causal_switching_game.py"),
        "config": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "transition": "1/10",
            "emissions": ["1/50", "49/50"],
            "prior1": "1/2",
        },
        "exact_pre_promotion_public_histories": len(envelopes),
        "pre_promotion_realization_columns": total_columns,
        "hidden_alternative_recursion_nodes_for_envelope_pass": hidden_nodes,
        "screens": results,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
