"""Verify the saved main-cell policy without re-solving or using posterior filtering."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import pairwise, product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def enumerate_world_metrics(game, policy):
    horizon = game.config.horizon
    assert horizon <= 5, "registered explicit enumeration is bounded at T=5"
    totals = [F(0)] * 5
    world_count = 0

    def act(history, queried, outcomes, weight, cost):
        time = len(history) + 1
        if time > horizon:
            for i, value in enumerate(cost):
                totals[i] += weight * value
            return
        old = history[-1][0] if history else 0
        for (action, query), probability in zip(
            game.choices(history), policy(history, queried), strict=True
        ):
            if probability == 0:
                continue
            stage = (
                F(outcomes[time - 1] if action == 0 else 1 - outcomes[time - 1]),
                game.config.query_cost * query,
                game.config.switch_cost * (action != old),
                F(query),
                F(action != old),
            )
            following = queried + ((time, outcomes[time - 1]),) if query else queried
            act(
                history + ((action, query),),
                following,
                outcomes,
                weight * probability,
                tuple(v + s for v, s in zip(cost, stage, strict=True)),
            )

    for states in product((0, 1), repeat=horizon + 1):
        state_probability = game.model.prior1 if states[0] else 1 - game.model.prior1
        for before, after in pairwise(states):
            positive = game.model.transition01 if before == 0 else 1 - game.model.transition10
            state_probability *= positive if after else 1 - positive
        for outcomes in product((0, 1), repeat=horizon):
            world_count += 1
            probability = state_probability
            for state, outcome in zip(states[1:], outcomes, strict=True):
                positive = game.model.emission1 if state else game.model.emission0
                probability *= positive if outcome else 1 - positive
            if probability:
                act((), (), outcomes, probability, (F(0),) * 5)
    return tuple(totals), world_count


def cohort_rule(game, active):
    def policy(history, queried):
        time = len(history) + 1
        visible = dict(game.information(history, queried)[1])
        query = active and time in (1, 2)
        action = active and time >= 4 and visible.get(1) == visible.get(2) == 1
        choice = int(action), int(query)
        return tuple(F(c == choice) for c in game.choices(history))

    return policy


if __name__ == "__main__":
    root = Path("outputs/switching_causal_game_v1")
    result = json.loads((root / "results.json").read_text(encoding="utf-8"))
    for path, digest in result["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    records = json.loads((root / "policy.json").read_text(encoding="utf-8"))
    mapping = {
        (tuple(map(tuple, row["history"])), tuple(map(tuple, row["released"]))): tuple(
            map(F, row["probabilities"])
        )
        for row in records
    }
    game = CausalSwitchingGame(GameConfig(), RegimeModel(emission0=F(1, 20), emission1=F(19, 20)))

    def policy(history, outcomes):
        return mapping[game.information(history, outcomes)]

    explicit, world_count = enumerate_world_metrics(game, policy)
    filtered = game.expected_metrics(policy)
    assert explicit == filtered
    saved = tuple(
        F(result["calibrated_metrics"][k])
        for k in ("decision_cost", "query_cost", "switch_cost", "queries", "switches")
    )
    assert result["activation_probability"] == "1" and explicit == saved
    active, inactive = cohort_rule(game, True), cohort_rule(game, False)
    activation = F(2, 5)
    active_metrics, inactive_metrics = (
        game.expected_metrics(active),
        game.expected_metrics(inactive),
    )
    cohort_metrics = tuple(
        activation * a + (1 - activation) * b
        for a, b in zip(active_metrics, inactive_metrics, strict=True)
    )
    cohort_risk = activation * game.null_risk(active)
    assert cohort_metrics == explicit
    assert cohort_risk == F(result["calibrated_risk_bound"]) == F(1, 10)
    report = {
        "status": "explicit_world_verification_and_fixed_cohort_simplification_passed",
        "hidden_state_outcome_worlds": world_count,
        "all_five_metrics_equal": True,
        "cohort_all_five_metrics_equal": True,
        "cohort_worst_risk": str(cohort_risk),
        "cohort_pathwise_max_queries": 2,
        "cohort_rule": "Activate with probability 2/5; query events 1,2; promote at 4 iff both positive; hold to 5.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_policy_sha256": hashlib.sha256((root / "policy.json").read_bytes()).hexdigest(),
        "scope": "Post-solve simplification, not independent efficacy evidence or a new algorithm.",
    }
    (root / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
