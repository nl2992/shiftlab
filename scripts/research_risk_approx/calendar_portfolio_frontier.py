"""Optimize a safe root portfolio over calendar risk-cost frontiers."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from decompose_switching_calendar_gap import CalendarOpportunityGame

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

PROTOCOL = ROOT / "docs/risk_preserving_approx/T8_B4_CALENDAR_PORTFOLIO_PROTOCOL_V1.md"
GRID = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_portfolio_v1.json"
ALPHAS = (F(1, 40), F(1, 20), F(1, 10), F(1, 5), F(2, 5), F(1))
TARGET_ALPHA = F(1, 10)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible(outcomes, decision_time: int, delay: int):
    return tuple(row for row in outcomes if row[0] + delay <= decision_time)


def probabilities_on_full_actions(component_game, policy, history, outcomes, full_game):
    local_choices = component_game.choices(history)
    local_probabilities = policy(
        history, visible(outcomes, len(history) + 1, full_game.config.delay)
    )
    full_choices = full_game.choices(history)
    result = [F(0)] * len(full_choices)
    for choice, probability in zip(local_choices, local_probabilities, strict=True):
        result[full_choices.index(choice)] += probability
    return tuple(result)


def portfolio_policy(full_game, components, weights):
    """Behavioral form of a root mixture under perfect recall."""

    def posterior_weights(history, outcomes):
        masses = []
        for (component_game, policy, _metrics, _risk, _metadata, _records), prior in zip(
            components, weights, strict=True
        ):
            likelihood = prior
            for index, observed_choice in enumerate(history):
                prefix_history = history[:index]
                prefix_outcomes = visible(outcomes, index + 1, full_game.config.delay)
                probabilities = probabilities_on_full_actions(
                    component_game, policy, prefix_history, prefix_outcomes, full_game
                )
                likelihood *= probabilities[
                    full_game.choices(prefix_history).index(observed_choice)
                ]
                if not likelihood:
                    break
            masses.append(likelihood)
        total = sum(masses, F(0))
        if not total:
            return tuple(F(0) for _ in components)
        return tuple(value / total for value in masses)

    def mixture(history, outcomes):
        posterior = posterior_weights(history, outcomes)
        if not sum(posterior, F(0)):
            return tuple(F(choice == (0, 0)) for choice in full_game.choices(history))
        result = [F(0)] * len(full_game.choices(history))
        for (component_game, policy, _metrics, _risk, _metadata, _records), weight in zip(
            components, posterior, strict=True
        ):
            if not weight:
                continue
            probabilities = probabilities_on_full_actions(
                component_game, policy, history, outcomes, full_game
            )
            for index, probability in enumerate(probabilities):
                result[index] += weight * probability
        return tuple(result)

    return mixture


def exact_frontier(candidates):
    """Solve the one-risk-resource mixture master by exact two-column enumeration."""
    best = None
    for index, candidate in enumerate(candidates):
        if candidate["risk"] <= TARGET_ALPHA:
            proposal = (candidate["cost"], ((index, F(1)),))
            if best is None or proposal[0] < best[0]:
                best = proposal
    for left in range(len(candidates)):
        for right in range(left + 1, len(candidates)):
            a, b = candidates[left], candidates[right]
            if a["risk"] == b["risk"]:
                continue
            low, high = (left, right) if a["risk"] < b["risk"] else (right, left)
            low_row, high_row = candidates[low], candidates[high]
            if not low_row["risk"] <= TARGET_ALPHA <= high_row["risk"]:
                continue
            low_weight = (high_row["risk"] - TARGET_ALPHA) / (high_row["risk"] - low_row["risk"])
            high_weight = 1 - low_weight
            cost = low_weight * low_row["cost"] + high_weight * high_row["cost"]
            proposal = (cost, ((low, low_weight), (high, high_weight)))
            if best is None or proposal[0] < best[0]:
                best = proposal
    if best is None:
        raise ValueError("safe portfolio master has no feasible solution")
    return best


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    saved_grid = json.loads(GRID.read_text(encoding="utf-8"))
    registered_cell = next(
        cell
        for cell in saved_grid["cells"]
        if cell["transition"] == "1/10" and cell["emissions"] == ["1/50", "49/50"]
    )
    config = GameConfig(
        horizon=8,
        budget=4,
        delay=2,
        alpha=TARGET_ALPHA,
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
    dates = [combo for size in range(5) for combo in combinations(range(1, 7), size)]
    components = []
    metadata = []
    started = time.perf_counter()
    for calendar in dates:
        for working_alpha in ALPHAS:
            candidate_config = GameConfig(
                horizon=config.horizon,
                budget=config.budget,
                delay=config.delay,
                alpha=working_alpha,
                query_cost=config.query_cost,
                switch_cost=config.switch_cost,
                max_nodes=config.max_nodes,
            )
            game = CalendarOpportunityGame(candidate_config, model, calendar)
            report, policy, records = game.solve()
            metrics = game.expected_metrics(policy)
            risk = game.null_risk(policy)
            cost = sum(metrics[:3])
            component_metadata = {
                "calendar": list(calendar),
                "working_alpha": str(working_alpha),
            }
            components.append((game, policy, metrics, risk, component_metadata, records))
            metadata.append(
                {
                    **component_metadata,
                    "cost": str(cost),
                    "risk": str(risk),
                    "solver_objective": report["solver_objective"],
                    "equality_residual": report["equality_residual"],
                    "inequality_violation": report["inequality_violation"],
                    "nodes": game.nodes,
                    "learner_sequences": game.learner.count,
                    "null_sequences": game.opponent.count,
                }
            )
    safe_game = CausalSwitchingGame(config, model)
    safe_policy = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in safe_game.choices(history)
    )
    safe_metrics = safe_game.expected_metrics(safe_policy)
    safe_risk = safe_game.null_risk(safe_policy)
    safe_component = (
        safe_game,
        safe_policy,
        safe_metrics,
        safe_risk,
        {"kind": "never_promote"},
        [],
    )
    components.append(safe_component)
    candidates = [
        {"cost": sum(metrics[:3]), "risk": risk}
        for _game, _policy, metrics, risk, _info, _records in components
    ]
    optimum_cost, selected = exact_frontier(candidates)
    weights = [F(0)] * len(components)
    for index, weight in selected:
        weights[index] = weight
    mixture = portfolio_policy(full_game, components, weights)
    metrics = full_game.expected_metrics(mixture)
    risk = full_game.null_risk(mixture)
    weighted_metrics = tuple(
        sum(
            (
                weight * component[2][metric]
                for weight, component in zip(weights, components, strict=True)
            ),
            F(0),
        )
        for metric in range(5)
    )
    risk_bound = sum(
        (weight * component[3] for weight, component in zip(weights, components, strict=True)),
        F(0),
    )
    if metrics != weighted_metrics:
        raise AssertionError("behavioral portfolio failed exact metric realization")
    if risk > TARGET_ALPHA or risk > risk_bound or risk_bound > TARGET_ALPHA:
        raise AssertionError("portfolio exact causal-null risk bound failed")
    if metrics[3] > config.budget:
        raise AssertionError("portfolio violates expected hard-budget bound")
    best_calendar_cost = F(registered_cell["best_calendar_cost"])
    full_reference_cost = F(registered_cell["methods"]["reference"]["calibrated_cost"])
    selected_components = []
    for index, weight in selected:
        _game, _policy, component_metrics, component_risk, info, records = components[index]
        selected_components.append(
            {
                "weight": str(weight),
                "metadata": info,
                "cost": str(sum(component_metrics[:3])),
                "risk": str(component_risk),
                "records": records,
            }
        )
    payload = {
        "status": "completed",
        "protocol_sha256": sha(PROTOCOL),
        "grid_sha256": sha(GRID),
        "runner_sha256": sha(Path(__file__)),
        "source_hashes": {
            path: sha(ROOT / path)
            for path in (
                "scripts/decompose_switching_calendar_gap.py",
                "src/shiftlab/dive/causal_switching_game.py",
            )
        },
        "component_count": len(metadata),
        "risk_frontier": metadata,
        "selected_components": selected_components,
        "portfolio_cost_master": str(optimum_cost),
        "portfolio_exact_cost": str(sum(metrics[:3])),
        "portfolio_exact_risk": str(risk),
        "portfolio_weighted_worst_risk_bound": str(risk_bound),
        "portfolio_metrics": [str(value) for value in metrics],
        "portfolio_weighted_metrics": [str(value) for value in weighted_metrics],
        "best_single_calendar_cost": str(best_calendar_cost),
        "full_reference_cost": str(full_reference_cost),
        "portfolio_minus_best_calendar": str(sum(metrics[:3]) - best_calendar_cost),
        "portfolio_minus_full_reference": str(sum(metrics[:3]) - full_reference_cost),
        "runtime_seconds": time.perf_counter() - started,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "component_count": len(metadata),
                "selected": [
                    {"weight": item["weight"], "metadata": item["metadata"]}
                    for item in selected_components
                ],
                "portfolio_cost": payload["portfolio_exact_cost"],
                "portfolio_risk": payload["portfolio_exact_risk"],
                "best_calendar_cost": payload["best_single_calendar_cost"],
                "full_reference_cost": payload["full_reference_cost"],
                "runtime_seconds": payload["runtime_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
