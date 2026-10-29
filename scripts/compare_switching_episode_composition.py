"""Compare a simple safe episode composition with the finite causal-game oracle."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def posterior_at(model: RegimeModel, outcomes, delay: int, time: int):
    posterior = model.prior1
    last_event = 0
    for event, outcome in sorted(outcomes):
        if event + delay > time:
            continue
        prior_at_event = model.propagate(posterior, event - last_event)
        prediction = model.emission(prior_at_event)
        likelihood1 = model.emission1 if outcome else 1 - model.emission1
        posterior = prior_at_event * likelihood1 / (prediction if outcome else 1 - prediction)
        last_event = event
    return posterior, last_event


def episode_policy(
    game: CausalSwitchingGame, calendar: tuple[int, ...], spending: str = "geometric"
):
    config, model = game.config, game.model

    def policy(history, outcomes):
        time = len(history) + 1
        old_action = history[-1][0] if history else 0
        posterior, last_event = posterior_at(model, outcomes, config.delay, time)
        current_gain = F(0)
        for future_time in range(time, config.horizon + 1):
            state_probability = model.propagate(posterior, future_time - last_event)
            current_gain += 2 * model.emission(state_probability) - 1

        # The action controller uses the current HMM forecast only. This forecast is
        # economically predictive and is not part of the global-null safety argument.
        if old_action:
            action = int(current_gain >= -config.switch_cost)
        else:
            action = 0
            rollbacks = sum(
                int(history[i - 1][0] == 1 and history[i][0] == 0) for i in range(1, len(history))
            )
            episode_index = rollbacks
            current_episode_start = 1
            for i in range(1, len(history)):
                if history[i - 1][0] == 1 and history[i][0] == 0:
                    current_episode_start = i + 1

            episode_queries = [
                (event, outcome)
                for event, outcome in outcomes
                if event >= current_episode_start
                and event < time
                and event + config.delay <= time
                and history[event - 1][0] == 0
                and history[event - 1][1] == 1
            ]
            # Only the first eligible calendar slot in an inactive episode can
            # initiate its randomized one-label test.
            test_positive = any(outcome == 1 for _, outcome in episode_queries)
            if test_positive and current_gain > config.switch_cost:
                action = 1

        query_probability = F(0)
        if time in calendar:
            if action:
                query_probability = F(1)
            else:
                rollbacks = sum(
                    int(history[i - 1][0] == 1 and history[i][0] == 0)
                    for i in range(1, len(history))
                )
                if old_action:
                    rollbacks += 1  # this round starts the next inactive test episode
                episode_index = rollbacks
                attempted = any(
                    event in calendar
                    for event in range(1, time)
                    if history[event - 1][0] == 0
                    and sum(
                        int(history[j - 1][0] == 1 and history[j][0] == 0) for j in range(1, event)
                    )
                    == episode_index
                )
                if not attempted:
                    if spending == "geometric":
                        alpha_episode = config.alpha / (2 ** (episode_index + 1))
                    elif spending == "equal":
                        alpha_episode = config.alpha / (config.budget + 1)
                    elif spending == "frontloaded":
                        alpha_episode = config.alpha if episode_index == 0 else F(0)
                    else:
                        raise ValueError(f"unknown alpha spending rule: {spending}")
                    query_probability = min(F(1), 2 * alpha_episode)

        choices = game.choices(history)
        return tuple(
            (1 - query_probability if query == 0 else query_probability)
            if choice_action == action
            else F(0)
            for choice_action, query in choices
        )

    return policy


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    eligible = tuple(range(1, config.horizon - config.delay + 1))
    schedules = [
        schedule for count in range(config.budget + 1) for schedule in combinations(eligible, count)
    ]
    rule_results = {}
    for spending in ("geometric", "equal", "frontloaded"):
        rows = []
        for schedule in schedules:
            assert len(schedule) <= config.budget
            game = CausalSwitchingGame(config, model)
            policy = episode_policy(game, schedule, spending)
            metrics = game.expected_metrics(policy)
            risk = game.null_risk(policy)
            assert risk <= config.alpha
            assert metrics[3] <= config.budget
            rows.append(
                {
                    "calendar": list(schedule),
                    "risk": str(risk),
                    "metrics": dict(
                        zip(
                            ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
                            map(str, metrics),
                            strict=True,
                        )
                    ),
                    "total_cost": str(sum(metrics[:3])),
                }
            )
        rule_results[spending] = {
            "best_calendar": min(rows, key=lambda row: F(row["total_cost"])),
            "all_calendars": rows,
        }
    best = min(
        (value["best_calendar"] for value in rule_results.values()),
        key=lambda row: F(row["total_cost"]),
    )
    oracle_game = CausalSwitchingGame(config, model)
    oracle_report, _, _ = oracle_game.solve()
    result = {
        "status": "completed_matched_contract_comparator_screen",
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
        "episode_composition": {
            "rule": "fixed calendar of up to B eligible query events; each inactive episode activates a one-label positive-only test with probability 2 alpha_j under geometric/equal/frontloaded alpha spending; active episodes query on scheduled events for HMM rollback forecasts; rollback uses remaining-horizon HMM predictive gain; promotion requires a positive test label and forecast gain above switch cost",
            "number_of_calendars": len(schedules),
            "pathwise_query_bound": "at most the calendar size, hence at most B on every policy path",
            "alpha_spending_comparisons": rule_results,
            "best_over_screened_compositions": best,
        },
        "causal_game_oracle": oracle_report,
        "composition_cost_minus_recovered_oracle_policy_cost": str(
            F(best["total_cost"]) - F(oracle_report["raw_recovered_cost"])
        ),
        "scope": "Development comparator screen only; oracle is numerical and best calendar is not a new algorithm.",
        "sha256": {
            source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
            for source in (
                "scripts/compare_switching_episode_composition.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
            )
        },
    }
    target = Path("outputs/switching_episode_composition_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
