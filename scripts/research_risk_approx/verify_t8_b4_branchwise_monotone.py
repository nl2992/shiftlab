"""Verify the two monotone deterministic branches in the saved T8/B4 policy."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from functools import cache
from itertools import product
from pathlib import Path

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/T8_B4_BRANCHWISE_MONOTONE_PROTOCOL_V1.md"
INPUT = ROOT / "docs/risk_preserving_approx/t8_b4_policy_shape_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_b4_branchwise_monotone_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    saved = json.loads(INPUT.read_text(encoding="utf-8"))
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
    _report, solved_policy, fresh_records = game.solve()

    behavior = {}
    for row in saved["behavior_records"]:
        key = (
            tuple(tuple(choice) for choice in row["history"]),
            tuple(tuple(item) for item in row["released"]),
        )
        behavior[key] = tuple(F(value) for value in row["probabilities"])
    fresh = {
        (
            tuple(tuple(choice) for choice in row["history"]),
            tuple(tuple(item) for item in row["released"]),
        ): tuple(F(value) for value in row["probabilities"])
        for row in fresh_records
    }
    if behavior != fresh:
        raise AssertionError("fresh solve did not recover the saved pre-promotion behavior")

    target_history = ((0, 1), (0, 1), (0, 1))
    target_released = ((1, 1), (2, 1))
    target_info = (target_history, target_released)
    target_probs = behavior[target_info]
    choices_at_target = game.choices(target_history)
    target_support = [
        (choice, prob) for choice, prob in zip(choices_at_target, target_probs, strict=True) if prob
    ]
    if target_support != [((0, 0), F(3, 5)), ((0, 1), F(2, 5))]:
        raise AssertionError(f"unexpected unique randomization: {target_support}")

    def make_policy(branch: str):
        if branch not in ("wait", "query"):
            raise ValueError(branch)

        def policy(history, outcomes):
            if any(action for action, _query in history):
                return solved_policy(history, outcomes)
            info = game.information(history, outcomes)
            choices = game.choices(history)
            if info == target_info:
                chosen = (0, 0) if branch == "wait" else (0, 1)
                return tuple(F(choice == chosen) for choice in choices)
            return behavior[info]

        return policy

    def risk(policy, *, iid: bool) -> F:
        @cache
        def visit(history, outcomes):
            time = len(history) + 1
            if time > config.horizon:
                return F(0)
            total = F(0)
            probabilities = policy(history, outcomes)
            choices = game.choices(history)
            for (action, query), action_mass in zip(choices, probabilities, strict=True):
                if not action_mass:
                    continue
                if action:
                    continuation = F(1)
                elif query:
                    following = history + ((action, query),)
                    zero = visit(following, outcomes + ((time, 0),))
                    one = visit(following, outcomes + ((time, 1),))
                    continuation = (zero + one) / 2 if iid else max(zero, (zero + one) / 2)
                else:
                    continuation = visit(history + ((action, query),), outcomes)
                total += action_mass * continuation
            return total

        return visit((), ())

    def tape_promotion(policy, tape):
        history = ()
        outcomes = ()
        query_count = 0
        for time in range(1, config.horizon + 1):
            probabilities = policy(history, outcomes)
            choices = game.choices(history)
            support = [
                choice
                for choice, probability in zip(choices, probabilities, strict=True)
                if probability
            ]
            if len(support) != 1 or probabilities[choices.index(support[0])] != 1:
                raise AssertionError("branch has randomized pre-promotion behavior")
            action, query = support[0]
            query_count += query
            if query_count > config.budget:
                raise AssertionError("branch violated the pathwise query cap")
            if action:
                return 1, query_count
            history += ((action, query),)
            if query:
                outcomes += ((time, tape[time - 1]),)
        return 0, query_count

    branch_results = {}
    for branch in ("wait", "query"):
        policy = make_policy(branch)
        tape_events = {}
        max_queries = 0
        for tape in product((0, 1), repeat=config.horizon):
            event, query_count = tape_promotion(policy, tape)
            tape_events[tape] = event
            max_queries = max(max_queries, query_count)
        violations = []
        for tape, event in tape_events.items():
            for index, bit in enumerate(tape):
                if bit:
                    continue
                successor = tape[:index] + (1,) + tape[index + 1 :]
                if event > tape_events[successor]:
                    violations.append((tape, successor))
        if violations:
            raise AssertionError(f"{branch} branch is not monotone: {violations[:3]}")
        iid_tape_risk = F(sum(tape_events.values()), 2**config.horizon)
        iid_recursion = risk(policy, iid=True)
        robust = risk(policy, iid=False)
        framework_risk = game.null_risk(policy)
        if not (iid_tape_risk == iid_recursion == robust == framework_risk):
            raise AssertionError(
                f"{branch} risk mismatch: tape={iid_tape_risk}, iid={iid_recursion}, "
                f"robust={robust}, game={framework_risk}"
            )
        metrics = game.expected_metrics(policy)
        branch_results[branch] = {
            "iid_tape_risk": str(iid_tape_risk),
            "iid_recursion_risk": str(iid_recursion),
            "independent_robust_risk": str(robust),
            "game_robust_risk": str(framework_risk),
            "monotonicity_violations": 0,
            "potential_tapes_checked": len(tape_events),
            "maximum_queries": max_queries,
            "expected_metrics": [str(value) for value in metrics],
            "expected_cost": str(sum(metrics[:3])),
        }

    mixture_risk = risk(solved_policy, iid=False)
    mixture_game_risk = game.null_risk(solved_policy)
    mixture_metrics = game.expected_metrics(solved_policy)
    mixture_cost = sum(mixture_metrics[:3])
    wait_cost = F(branch_results["wait"]["expected_cost"])
    query_cost = F(branch_results["query"]["expected_cost"])
    weighted_cost = F(3, 5) * wait_cost + F(2, 5) * query_cost
    wait_risk = F(branch_results["wait"]["independent_robust_risk"])
    query_risk = F(branch_results["query"]["independent_robust_risk"])
    weighted_risk = F(3, 5) * wait_risk + F(2, 5) * query_risk
    if mixture_risk != F(1, 10) or mixture_game_risk != F(1, 10):
        raise AssertionError(f"mixture robust risk mismatch: {mixture_risk}, {mixture_game_risk}")
    if weighted_cost != mixture_cost or mixture_cost != F(saved["exact_cost"]):
        raise AssertionError(
            f"mixture cost mismatch: weighted={weighted_cost}, policy={mixture_cost}, saved={saved['exact_cost']}"
        )
    if weighted_risk != mixture_risk:
        raise AssertionError(f"weighted component risk mismatch: {weighted_risk} != {mixture_risk}")

    payload = {
        "protocol_sha256": sha(PROTOCOL),
        "input_sha256": sha(INPUT),
        "runner_sha256": sha(Path(__file__)),
        "config": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
        },
        "randomization_state": {
            "history": [list(choice) for choice in target_history],
            "released": [list(item) for item in target_released],
            "wait_weight": "3/5",
            "query_fourth_weight": "2/5",
        },
        "branches": branch_results,
        "mixture": {
            "cost": str(mixture_cost),
            "weighted_component_cost": str(weighted_cost),
            "robust_risk": str(mixture_risk),
            "framework_robust_risk": str(mixture_game_risk),
            "weighted_component_risk": str(weighted_risk),
            "expected_metrics": [str(value) for value in mixture_metrics],
        },
        "status": "PASS",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "branches": branch_results,
                "mixture": payload["mixture"],
                "status": payload["status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
