"""Compare a fixed compact switching controller with the decomposed causal oracle."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.switching_fsc_risk import DeterministicFSC, worst_case_promotion_risk


def active_controller() -> DeterministicFSC:
    def on_release(memory, request_time, outcome):
        labels, deployed = memory
        return labels + ((request_time, outcome),), deployed

    def decide(time, memory, _remaining):
        labels, deployed = memory
        observed = dict(labels)
        if time == 1:
            action, query = 0, 1
        elif time == 2:
            action, query = 0, int(observed.get(1) == 1)
        elif time == 3:
            action = int(observed.get(1) == 1 and observed.get(2) == 1)
            query = 0
        elif time == 4:
            action, query = int(deployed), int(deployed)
        elif time == 5:
            action = int(deployed and observed.get(4) != 0)
            query = 0
        else:
            action, query = int(deployed), 0
        return action, query, (labels, bool(action))

    return DeterministicFSC(initial_memory=((), False), on_release=on_release, decide=decide)


def fixed_graph_policy(game, activation):
    """Persistent active/inactive root mixture; the first query reveals the mode."""

    def policy(history, outcomes):
        time = len(history) + 1
        visible = dict(game.information(history, outcomes)[1])
        active = bool(history and history[0][1])
        old_action = history[-1][0] if history else 0
        if time == 1:
            weights = {(0, 0): 1 - activation, (0, 1): activation}
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


def main() -> None:
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    active = active_controller()
    rows = []
    for horizon in (6, 7, 8, 9):
        config = GameConfig(
            horizon=horizon,
            budget=3,
            delay=1,
            alpha=F(1, 10),
            query_cost=F(1, 100),
            switch_cost=F(1, 10),
            max_nodes=250_000,
        )
        compact_risk = worst_case_promotion_risk(
            active, horizon=horizon, budget=config.budget, delay=config.delay
        ).risk
        assert compact_risk == F(1, 4)

        game = CausalSwitchingGame(config, model)
        policy = fixed_graph_policy(game, F(2, 5))
        compact_metrics = game.expected_metrics(policy)
        compact_cost = sum(compact_metrics[:3])
        compact_full_history_risk = game.null_risk(policy)
        assert compact_full_history_risk == F(1, 10)

        oracle = FirstPromotionDecomposedGame(config, model)
        report, oracle_policy, _records = oracle.solve()
        oracle_risk = oracle.null_risk(oracle_policy)
        oracle_metrics = oracle.expected_metrics(oracle_policy)
        oracle_raw_cost = sum(oracle_metrics[:3])
        rows.append(
            {
                "horizon": horizon,
                "budget": config.budget,
                "delay": config.delay,
                "compact_controller_cost": str(compact_cost),
                "compact_controller_risk": str(compact_full_history_risk),
                "compact_component_risk": str(compact_risk),
                "decomposed_solver_cost": str(oracle_raw_cost),
                "decomposed_solver_risk": str(oracle_risk),
                "cost_difference": str(compact_cost - oracle_raw_cost),
                "decomposed_nodes": report["nodes"],
                "decomposed_learner_sequences": report["learner_sequences"],
                "oracle_status": "numerical LP policy; only T=6 has a saved rational optimum bracket",
            }
        )

    payload = {
        "status": "targeted_compact_controller_horizon_screen",
        "contract": {
            "alpha": "1/10",
            "budget": 3,
            "delay": 1,
            "query_cost": "1/100",
            "switch_cost": "1/10",
            "alternative": "two-state recurrent HMM with transition 1/4 and emissions 1/20, 19/20",
            "null": "full-history conditional success probability in [0,1/2]",
        },
        "controller": "2/5 persistent activation lottery; query at t=1, query t=2 iff Y1=1, promote at t=3 iff Y1=Y2=1, query maintenance t=4, rollback at t=5 iff maintenance label is 0, then hold",
        "rows": rows,
        "scope": "small deterministic family screen; exact rational policy metrics and risks, numerical decomposed oracle; no novelty or efficacy claim",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_fixed_fsc_horizon_growth_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
