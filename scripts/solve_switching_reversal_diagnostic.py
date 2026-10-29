"""Run the pre-registered one-cell causal reversal oracle comparison."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def cohort_policy(game: CausalSwitchingGame):
    activation = F(4, 5)

    def policy(history, outcomes):
        time = len(history) + 1
        choices = game.choices(history)
        if time == 1:
            return tuple(
                activation if choice == (0, 1) else F(1, 5) if choice == (0, 0) else F(0)
                for choice in choices
            )
        active = bool(history[0][1])
        if not active:
            chosen = (0, 0)
        elif time <= 3:
            chosen = (0, 1)
        elif time == 4:
            visible = dict(game.information(history, outcomes)[1])
            chosen = (int(all(visible.get(s) == 1 for s in (1, 2, 3))), 0)
        else:
            chosen = (history[-1][0], 0)
        return tuple(F(choice == chosen) for choice in choices)

    return policy


def metric_dict(values):
    return {
        key: str(value)
        for key, value in zip(
            ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
            values,
            strict=True,
        )
    }


def main() -> dict[str, object]:
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
    target = Path("outputs/switching_reversal_diagnostic_v1")
    target.mkdir(parents=True, exist_ok=True)
    game = CausalSwitchingGame(config, model)
    oracle_report, oracle_policy, oracle_records = game.solve()
    raw_metrics = game.expected_metrics(oracle_policy)

    def continue_policy(history, outcomes):
        return tuple(F(choice == (0, 0)) for choice in game.choices(history))

    continue_metrics = game.expected_metrics(continue_policy)
    activation = F(oracle_report["activation_probability"])
    safe_oracle_metrics = tuple(
        activation * raw + (1 - activation) * stay
        for raw, stay in zip(raw_metrics, continue_metrics, strict=True)
    )

    reference = CausalSwitchingGame(config, model)
    cohort = cohort_policy(reference)
    cohort_metrics = reference.expected_metrics(cohort)
    cohort_risk = reference.null_risk(cohort)
    assert cohort_risk <= config.alpha
    cohort_cost = sum(cohort_metrics[:3])
    oracle_cost = sum(safe_oracle_metrics[:3])
    report = {
        "status": "completed_exact_causal_oracle_diagnostic",
        "configuration": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "model": {
                "transition01": str(model.transition01),
                "transition10": str(model.transition10),
                "emission0": str(model.emission0),
                "emission1": str(model.emission1),
                "prior1": str(model.prior1),
            },
        },
        "oracle": {
            "lp_report": oracle_report,
            "raw_metrics": metric_dict(raw_metrics),
            "risk_calibrated_metrics": metric_dict(safe_oracle_metrics),
            "behavior_records": oracle_records,
        },
        "fixed_cohort": {
            "activation_probability": "4/5",
            "rule": "active paths query 1,2,3; promote at start of 4 iff all positive; hold; inactive paths stay at 0",
            "causal_null_risk": str(cohort_risk),
            "metrics": metric_dict(cohort_metrics),
            "total_cost": str(cohort_cost),
            "pathwise_queries_at_most": config.budget,
        },
        "oracle_minus_cohort_total_cost": str(oracle_cost - cohort_cost),
        "oracle_cost_is_strictly_lower": oracle_cost < cohort_cost,
        "scope": "One registered finite known-model oracle diagnostic; not a new method or efficacy confirmation.",
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                "scripts/solve_switching_reversal_diagnostic.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_reversal_diagnostic_v1.md",
            )
        },
    }
    (target / "results.json").write_text(
        json.dumps(report, default=str, indent=2) + "\n", encoding="utf-8"
    )
    (target / "oracle_policy.json").write_text(
        json.dumps(oracle_records, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    try:
        print(json.dumps(main(), default=str, indent=2))
    except RuntimeError as error:
        target = Path("outputs/switching_reversal_diagnostic_v1")
        target.mkdir(parents=True, exist_ok=True)
        failure = {"status": "registered_reference_failed", "reason": str(error)}
        (target / "failure.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        raise
