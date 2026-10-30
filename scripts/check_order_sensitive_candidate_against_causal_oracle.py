"""Check the rejected local acquisition example against the exact causal-game oracle."""

from __future__ import annotations

import json
from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class LocalDecisionGame(CausalSwitchingGame):
    """Force the example's first three queries and allow only its local choices."""

    def choices(self, history):
        time = len(history) + 1
        if time <= 3:
            return ((0, 1),)
        if time == 4:
            return ((0, 0), (0, 1), (1, 0))
        if time == 5:
            action, query = history[-1]
            if action:
                return ((1, 0),)
            return ((0, 0), (1, 0)) if query else ((0, 0),)
        if time == 6:
            return ((history[-1][0], 0),)
        return ((0, 0),)


def main() -> None:
    config = GameConfig(
        horizon=6,
        budget=4,
        delay=1,
        alpha=F(1, 20),
        query_cost=F(1, 1000),
        switch_cost=F(13, 20),
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 10),
        emission1=F(9, 10),
        prior1=F(1, 2),
    )
    game = LocalDecisionGame(config, model)
    report, _policy, records = game.solve()

    decisions = {}
    for record in records:
        if len(record["history"]) != 3:
            continue
        labels = tuple(y for _event, y in record["released"])
        if labels in ((1, 0, 1), (0, 1, 1)):
            decisions["".join(map(str, labels))] = {
                "choices": [list(choice) for choice in record["choices"]],
                "probabilities": record["probabilities"],
            }

    stay = ["1", "0", "0"]
    assert decisions == {
        "101": {"choices": [[0, 0], [0, 1], [1, 0]], "probabilities": stay},
        "011": {"choices": [[0, 0], [0, 1], [1, 0]], "probabilities": stay},
    }
    assert report["calibrated_total_cost"] == "3003/1000"
    assert report["calibrated_metrics"]["queries"] == "3"
    assert report["calibrated_metrics"]["switches"] == "0"
    assert report["raw_causal_null_risk"] == "0"

    print(
        json.dumps(
            {
                "status": "exact_restricted_causal_oracle_rejects_order_sensitive_query_example",
                "contract": {
                    "horizon": 6,
                    "budget": 4,
                    "delay": 1,
                    "alpha": "1/20",
                    "query_cost": "1/1000",
                    "switch_cost": "13/20",
                    "queries_forced": [1, 2, 3],
                    "last_query_opportunity": 4,
                    "promotion_opportunities": [4, 5],
                },
                "oracle": {
                    "total_cost": report["calibrated_total_cost"],
                    "queries": report["calibrated_metrics"]["queries"],
                    "switches": report["calibrated_metrics"]["switches"],
                    "causal_null_risk": report["raw_causal_null_risk"],
                    "nodes": report["nodes"],
                },
                "history_actions": decisions,
                "claim_scope": "Exact finite oracle check for the restricted example only; no scalable algorithm or novelty claim.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
