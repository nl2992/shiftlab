"""Verify the saved exact calendar portfolio and its finite candidate frontier."""

from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from decompose_switching_calendar_gap import CalendarOpportunityGame

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

RESULT = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_portfolio_v1.json"
RUNNER = ROOT / "scripts/research_risk_approx/calendar_portfolio_frontier.py"
ALPHA = F(1, 10)


def restore_calendar_policy(game, records):
    behavior = {}
    for row in records:
        history = tuple(tuple(choice) for choice in row["history"])
        released = tuple(tuple(item) for item in row["released"])
        choices = tuple(tuple(choice) for choice in row["choices"])
        probabilities = tuple(F(value) for value in row["probabilities"])
        if choices != game.choices(history) or sum(probabilities) != 1:
            raise ValueError("invalid saved component behavior")
        key = (history, released)
        if key in behavior:
            raise ValueError("duplicate component information set")
        behavior[key] = probabilities
    if set(behavior) != set(game.learner.infos):
        raise ValueError("component behavior does not cover its learner tree")

    def policy(history, outcomes):
        return behavior[game.information(history, outcomes)]

    return policy


def full_action_probabilities(component_game, component_policy, history, outcomes, full_game):
    local = component_game.choices(history)
    p = component_policy(history, outcomes)
    result = [F(0)] * len(full_game.choices(history))
    for choice, probability in zip(local, p, strict=True):
        result[full_game.choices(history).index(choice)] += probability
    return tuple(result)


def portfolio_policy(full_game, components, weights):
    def policy(history, outcomes):
        posterior = []
        for game, component_policy, _weight in components:
            likelihood = _weight
            for index, choice in enumerate(history):
                prefix = history[:index]
                visible = tuple(
                    row for row in outcomes if row[0] + full_game.config.delay <= index + 1
                )
                probabilities = full_action_probabilities(
                    game, component_policy, prefix, visible, full_game
                )
                likelihood *= probabilities[full_game.choices(prefix).index(choice)]
                if not likelihood:
                    break
            posterior.append(likelihood)
        total = sum(posterior, F(0))
        if not total:
            return tuple(F(choice == (0, 0)) for choice in full_game.choices(history))
        posterior = [weight / total for weight in posterior]
        result = [F(0)] * len(full_game.choices(history))
        for (game, component_policy, _prior), weight in zip(components, posterior, strict=True):
            if not weight:
                continue
            p = full_action_probabilities(game, component_policy, history, outcomes, full_game)
            for index, probability in enumerate(p):
                result[index] += weight * probability
        return tuple(result)

    return policy


def frontier_minimum(rows):
    points = [(F(row["cost"]), F(row["risk"])) for row in rows]
    points.append((F(4), F(0)))
    best = None
    for cost, risk in points:
        if risk <= ALPHA and (best is None or cost < best):
            best = cost
    for i, (cost_i, risk_i) in enumerate(points):
        for j, (cost_j, risk_j) in enumerate(points[i + 1 :], start=i + 1):
            if risk_i == risk_j:
                continue
            low, high = (i, j) if risk_i < risk_j else (j, i)
            low_cost, low_risk = points[low]
            high_cost, high_risk = points[high]
            if low_risk <= ALPHA <= high_risk:
                low_weight = (high_risk - ALPHA) / (high_risk - low_risk)
                value = low_weight * low_cost + (1 - low_weight) * high_cost
                if best is None or value < best:
                    best = value
    if best is None:
        raise ValueError("no feasible portfolio in saved frontier")
    return best


def verify():
    saved = json.loads(RESULT.read_text(encoding="utf-8"))
    if hashlib.sha256(RUNNER.read_bytes()).hexdigest() != saved["runner_sha256"]:
        raise ValueError("runner hash mismatch")
    if len(saved["risk_frontier"]) != 342 or saved["component_count"] != 342:
        raise ValueError("unexpected risk-frontier component count")
    if frontier_minimum(saved["risk_frontier"]) != F(saved["portfolio_cost_master"]):
        raise ValueError("saved portfolio is not optimal over the finite component set")

    config = GameConfig(
        horizon=8,
        budget=4,
        delay=2,
        alpha=ALPHA,
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
    full_game = CausalSwitchingGame(config, model)
    components = []
    weighted_metrics = [F(0)] * 5
    weighted_risk = F(0)
    total_weight = F(0)
    for row in saved["selected_components"]:
        weight = F(row["weight"])
        metadata = row["metadata"]
        if metadata.get("kind") == "never_promote":
            game = CausalSwitchingGame(config, model)
            component_policy = never_promote_policy(game)
        else:
            component_config = GameConfig(
                horizon=8,
                budget=4,
                delay=2,
                alpha=F(metadata["working_alpha"]),
                query_cost=F(1, 100),
                switch_cost=F(1, 10),
            )
            game = CalendarOpportunityGame(component_config, model, metadata["calendar"])
            game.build()
            component_policy = restore_calendar_policy(game, row["records"])
        metrics = game.expected_metrics(component_policy)
        risk = game.null_risk(component_policy)
        if sum(metrics[:3]) != F(row["cost"]) or risk != F(row["risk"]):
            raise ValueError("selected component exact metric mismatch")
        for index, value in enumerate(metrics):
            weighted_metrics[index] += weight * value
        weighted_risk += weight * risk
        total_weight += weight
        components.append((game, component_policy, weight))
    if total_weight != 1 or weighted_risk > ALPHA:
        raise ValueError("root weights or conservative risk bound invalid")
    mixed = portfolio_policy(full_game, components, [item[2] for item in components])
    metrics = full_game.expected_metrics(mixed)
    risk = full_game.null_risk(mixed)
    if metrics != tuple(weighted_metrics) or risk > weighted_risk or risk > ALPHA:
        raise ValueError("behavioral root portfolio failed independent exact verification")
    if str(sum(metrics[:3])) != saved["portfolio_exact_cost"]:
        raise ValueError("portfolio exact cost does not match saved artifact")
    if str(risk) != saved["portfolio_exact_risk"]:
        raise ValueError("portfolio exact risk does not match saved artifact")
    return {
        "components": len(saved["risk_frontier"]),
        "selected_branches": len(components),
        "portfolio_cost": str(sum(metrics[:3])),
        "portfolio_risk": str(risk),
        "weighted_risk_bound": str(weighted_risk),
        "best_single_calendar": saved["best_single_calendar_cost"],
        "full_reference": saved["full_reference_cost"],
    }


def never_promote_policy(game):
    def policy(history, outcomes):
        return tuple(F(choice == (0, 0)) for choice in game.choices(history))

    return policy


if __name__ == "__main__":
    print(json.dumps(verify()))
