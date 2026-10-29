"""Separate contingent-query and rollback value in the registered exact cell."""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class NoRollbackGame(CausalSwitchingGame):
    def choices(self, history):
        choices = super().choices(history)
        if history and history[-1][0] == 1:
            return tuple(choice for choice in choices if choice[0] == 1)
        return choices


def compact_full_policy(game: CausalSwitchingGame):
    activation = F(2, 5)

    def policy(history, outcomes):
        time = len(history) + 1
        choices = game.choices(history)
        if time == 1:
            return tuple(
                activation if choice == (0, 1) else F(1) - activation if choice == (0, 0) else F(0)
                for choice in choices
            )
        active = bool(history[0][1])
        visible = dict(game.information(history, outcomes)[1])
        if not active:
            chosen = (0, 0)
        elif time == 2:
            chosen = (0, 1) if visible.get(1) == 1 else (0, 0)
        elif time == 3:
            chosen = (1, 0) if visible.get(1) == visible.get(2) == 1 else (0, 0)
        elif time == 4:
            chosen = (1, 1) if history[-1][0] == 1 else (0, 0)
        elif time == 5:
            chosen = (0, 0) if history[-1][0] == 1 and visible.get(4) == 0 else (history[-1][0], 0)
        else:
            chosen = (history[-1][0], 0)
        return tuple(F(choice == chosen) for choice in choices)

    return policy


def compact_no_rollback_policy(game: CausalSwitchingGame):
    activation = F(4, 5)

    def policy(history, outcomes):
        time = len(history) + 1
        choices = game.choices(history)
        if time == 1:
            return tuple(
                activation if choice == (0, 1) else F(1) - activation if choice == (0, 0) else F(0)
                for choice in choices
            )
        active = bool(history[0][1])
        visible = dict(game.information(history, outcomes)[1])
        if not active:
            chosen = (0, 0)
        elif time == 2:
            chosen = (0, 1) if visible.get(1) == 1 else (0, 0)
        elif time == 3:
            chosen = (0, 1) if visible.get(1) == visible.get(2) == 1 else (0, 0)
        elif time == 4:
            chosen = (1, 0) if all(visible.get(s) == 1 for s in (1, 2, 3)) else (0, 0)
        else:
            chosen = (history[-1][0], 0)
        return tuple(F(choice == chosen) for choice in choices)

    return policy


def run():
    folder = Path("outputs/switching_reversal_diagnostic_v1")
    unrestricted = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    fixed = json.loads((folder / "fixed_cohort_frontier.json").read_text(encoding="utf-8"))
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    unrestricted_game = CausalSwitchingGame(config, model)
    full_rule = compact_full_policy(unrestricted_game)
    full_rule_metrics = unrestricted_game.expected_metrics(full_rule)
    full_rule_risk = unrestricted_game.null_risk(full_rule)
    saved_full_metrics = unrestricted["oracle"]["risk_calibrated_metrics"]
    assert full_rule_risk == F(unrestricted["oracle"]["lp_report"]["raw_causal_null_risk"])
    assert {
        key: str(value)
        for key, value in zip(
            ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
            full_rule_metrics,
            strict=True,
        )
    } == saved_full_metrics
    game = NoRollbackGame(config, model)
    report, policy, policy_records = game.solve()
    raw_risk = game.null_risk(policy)
    assert raw_risk <= config.alpha
    compact = compact_no_rollback_policy(game)
    compact_metrics = game.expected_metrics(compact)
    compact_risk = game.null_risk(compact)
    assert compact_metrics == game.expected_metrics(policy)
    assert compact_risk == raw_risk
    full_cost = F(unrestricted["oracle"]["lp_report"]["calibrated_total_cost"])
    fixed_cost = F(fixed["metrics"]["total_cost"])
    no_rollback_cost = F(report["calibrated_total_cost"])
    output = {
        "status": "completed_no_rollback_ablation",
        "configuration_matches_registered_cell": True,
        "compact_full_oracle_policy_verified": {
            "rule": "activate with probability 2/5; query again only after positive; promote after two positives; query once post-promotion; rollback on a negative maintenance label",
            "metrics": {
                key: str(value)
                for key, value in zip(
                    ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
                    full_rule_metrics,
                    strict=True,
                )
            },
            "causal_null_risk": str(full_rule_risk),
        },
        "no_rollback_oracle": report,
        "independent_recovered_causal_null_risk": str(raw_risk),
        "compact_no_rollback_policy_verified": {
            "rule": "activate with probability 4/5; query next label only after positives; promote after three positives; never rollback",
            "metrics": {
                key: str(value)
                for key, value in zip(
                    ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
                    compact_metrics,
                    strict=True,
                )
            },
            "causal_null_risk": str(compact_risk),
        },
        "costs": {
            "fixed_cohort_frontier": str(fixed_cost),
            "adaptive_query_no_rollback": str(no_rollback_cost),
            "unrestricted_query_and_rollback": str(full_cost),
        },
        "improvement_fixed_to_adaptive_no_rollback": str(fixed_cost - no_rollback_cost),
        "incremental_improvement_from_rollback": str(no_rollback_cost - full_cost),
        "scope": "Numerical finite-game decomposition for one registered cell; no novelty or efficacy claim.",
    }
    (folder / "rollback_ablation.json").write_text(
        json.dumps(output, default=str, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "no_rollback_policy.json").write_text(
        json.dumps(policy_records, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    print(json.dumps(run(), default=str, indent=2))
