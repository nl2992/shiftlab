"""Optimize a fixed delayed-reversal FSC graph by exact two-component LP."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def fixed_graph_policy(game: CausalSwitchingGame, activation: F):
    """Two-query certification FSM, then one maintenance query after promotion."""

    def policy(history, outcomes):
        time = len(history) + 1
        visible = dict(game.information(history, outcomes)[1])
        active = bool(history and history[0][1])
        old_action = history[-1][0] if history else 0

        if time == 1:
            weights = {
                (0, 0): 1 - activation,
                (0, 1): activation,
            }
        elif time == 2:
            query = int(active and visible.get(1) == 1)
            weights = {(0, query): F(1)}
        elif time == 3:
            promote = int(active and visible.get(1) == 1 and visible.get(2) == 1)
            weights = {(promote, 0): F(1)}
        elif time == 4:
            weights = {(1, 1): F(1)} if old_action else {(0, 0): F(1)}
        elif time == 5:
            rollback = old_action and visible.get(4) == 0
            weights = {(0 if rollback else old_action, 0): F(1)}
        else:
            weights = {(old_action, 0): F(1)}

        return tuple(weights.get(choice, F(0)) for choice in game.choices(history))

    return policy


def metrics_dict(values):
    names = ("decision_cost", "query_cost", "switch_cost", "queries", "switches")
    return {name: str(value) for name, value in zip(names, values, strict=True)}


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
    reference_path = Path("outputs/switching_reversal_diagnostic_v1/results.json")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    game = CausalSwitchingGame(config, model)

    active_policy = fixed_graph_policy(game, F(1))
    inactive_policy = fixed_graph_policy(game, F(0))
    active_metrics = game.expected_metrics(active_policy)
    inactive_metrics = game.expected_metrics(inactive_policy)
    active_risk = game.null_risk(active_policy)
    inactive_risk = game.null_risk(inactive_policy)
    assert active_risk == F(1, 4) and inactive_risk == 0

    # Exact LP in x = mass on the active FSC; the other mass stays on incumbent.
    # The two policies share one fixed graph; the root coin selects the component.
    if sum(active_metrics[:3]) < sum(inactive_metrics[:3]):
        activation = min(F(1), config.alpha / active_risk)
    else:
        activation = F(0)
    mixed_policy = fixed_graph_policy(game, activation)
    mixed_metrics = game.expected_metrics(mixed_policy)
    mixed_risk = game.null_risk(mixed_policy)
    assert mixed_risk <= config.alpha
    oracle = reference["oracle"]["lp_report"]
    oracle_cost = F(oracle["calibrated_total_cost"])
    oracle_metrics = {key: F(value) for key, value in oracle["calibrated_metrics"].items()}
    mixture_cost = sum(mixed_metrics[:3])
    assert mixture_cost == oracle_cost
    assert mixed_risk == F(oracle["raw_causal_null_risk"])
    assert metrics_dict(mixed_metrics) == {key: str(value) for key, value in oracle_metrics.items()}

    payload = {
        "status": "fixed_fsc_two_component_lp_matches_registered_recovered_oracle",
        "contract": {
            "horizon": config.horizon,
            "hard_query_budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "alternative": "registered recurrent HMM transition 1/4, emissions 1/20 and 19/20",
            "null": "full-history conditional success probability at most 1/2",
        },
        "controller_graph": "inactive incumbent; active mode queries at event 1, queries event 2 only after Y1=1, promotes at event 3 after two positives, queries event 4 while deployed, rolls back at event 5 if Y4=0, then holds",
        "component_values": {
            "active_cost": str(sum(active_metrics[:3])),
            "active_risk": str(active_risk),
            "active_metrics": metrics_dict(active_metrics),
            "inactive_cost": str(sum(inactive_metrics[:3])),
            "inactive_risk": str(inactive_risk),
            "inactive_metrics": metrics_dict(inactive_metrics),
        },
        "mixture_lp": {
            "objective": "min x*C_active + (1-x)*C_inactive",
            "constraint": "x*R_active + (1-x)*R_inactive <= alpha; 0<=x<=1",
            "activation_weight": str(activation),
            "risk": str(mixed_risk),
            "cost": str(mixture_cost),
            "metrics": metrics_dict(mixed_metrics),
        },
        "registered_unrestricted_recovered_oracle": {
            "cost": str(oracle_cost),
            "risk": str(oracle["raw_causal_null_risk"]),
            "metrics": {key: str(value) for key, value in oracle_metrics.items()},
            "optimality_status": "numerical sequence-form LP; no exact dual certificate",
        },
        "recovered_policy_gap": str(mixture_cost - oracle_cost),
        "evidence_status": "post-hoc exact distillation of a previously registered oracle cell; not an independent efficacy confirmation",
        "reference_results_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_two_component_fsc_lp_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
