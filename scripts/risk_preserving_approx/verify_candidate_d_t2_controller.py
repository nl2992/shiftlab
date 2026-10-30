"""Rationalize and independently verify an extracted Candidate D controller."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def read_controller(path: Path):
    nodes = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        fields = row.split("\t")
        if fields[0] == "NODES":
            expected_nodes = int(fields[1])
        elif fields[0] == "N":
            _, node_id, partition, residual = fields
            nodes[int(node_id)] = {
                "partition": int(partition),
                "residual": float(residual),
                "actions": {},
                "children": {},
            }
        elif fields[0] == "A":
            _, node_id, action, probability = fields
            nodes[int(node_id)]["actions"][int(action)] = float(probability)
        elif fields[0] == "C":
            _, node_id, action, observation, child_id = fields
            nodes[int(node_id)]["children"][int(action), int(observation)] = int(child_id)
        else:
            raise ValueError(f"unknown controller record: {row}")
    if len(nodes) != expected_nodes:
        raise ValueError(f"controller header says {expected_nodes} nodes, found {len(nodes)}")
    return nodes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    metadata = json.loads((args.run_dir / "partition_metadata.json").read_text(encoding="utf-8"))
    nodes = read_controller(args.run_dir / "controller.tsv")
    info_to_distribution = {}
    max_partition_residual = 0.0
    max_normalization_error = 0.0
    max_rounding_l1 = F(0)

    for node in nodes.values():
        max_partition_residual = max(max_partition_residual, node["residual"])
        part = metadata["partitions"][str(node["partition"])]
        if part["phase"] != "request":
            continue
        history = tuple(tuple(x) for x in part["history"])
        visible = tuple(tuple(x) for x in part["visible_outcomes"])
        key = (history, visible)
        raw = {a: p for a, p in node["actions"].items() if a in (0, 1, 2, 3)}
        total = sum(raw.values())
        if abs(total - 1.0) > 1e-7:
            raise ValueError(f"request partition action mass {total} at {key}")
        choices = tuple((action, query) for action in (0, 1) for query in (0, 1))
        rational = [
            F(raw.get(2 * action + query, 0.0)).limit_denominator(10**9)
            for action, query in choices
        ]
        rational_total = sum(rational)
        if rational_total == 0:
            raise ValueError(f"rationalization erased all action mass at {key}")
        rational = tuple(x / rational_total for x in rational)
        rounding_l1 = sum(
            abs(p - F(raw.get(2 * action + query, 0.0)))
            for (action, query), p in zip(choices, rational, strict=True)
        )
        max_rounding_l1 = max(max_rounding_l1, rounding_l1)
        if key in info_to_distribution and info_to_distribution[key] != rational:
            raise ValueError(f"controller assigns inconsistent distributions to {key}")
        info_to_distribution[key] = rational
        max_normalization_error = max(max_normalization_error, abs(float(sum(rational) - 1)))

    config = GameConfig(
        horizon=int(metadata["horizon"]),
        budget=int(metadata["budget"]),
        delay=int(metadata["delay"]),
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    game = CausalSwitchingGame(config, RegimeModel())
    game.build()

    def policy(history, outcomes):
        key = game.information(history, outcomes)
        try:
            distribution = info_to_distribution[key]
        except KeyError as error:
            raise ValueError(
                f"missing extracted controller node for reachable history {key}"
            ) from error
        choices = game.choices(history)
        return tuple(
            distribution[choices.index(choice)] if choice in choices else F(0) for choice in choices
        )

    # Enumerate the support tree independently and verify the hard query cap on
    # every possible label history, not only under the alternative HMM average.
    seen = set()
    max_queries = 0

    def audit(history, outcomes, query_count):
        nonlocal max_queries
        if len(history) >= config.horizon:
            max_queries = max(max_queries, query_count)
            return
        key = game.information(history, outcomes)
        if key in seen:
            return
        seen.add(key)
        choices = game.choices(history)
        probs = policy(history, outcomes)
        for choice, mass in zip(choices, probs, strict=True):
            if mass <= 0:
                continue
            action, query = choice
            next_history = history + (choice,)
            next_count = query_count + query
            if next_count > config.budget:
                raise ValueError(f"pathwise query budget exceeded on {next_history}")
            max_queries = max(max_queries, next_count)
            if action and not query:
                # Promotion under the null terminates risk evaluation; the
                # alternative continuation is still checked by expected_metrics.
                continue
            if query:
                audit(next_history, outcomes + ((len(history) + 1, 0),), next_count)
                audit(next_history, outcomes + ((len(history) + 1, 1),), next_count)
            else:
                audit(next_history, outcomes, next_count)

    audit((), (), 0)
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    cost = sum(metrics[:3])
    scalarized = cost + risk
    result = {
        "status": "verified",
        "cost_components": {
            "decision": str(metrics[0]),
            "query": str(metrics[1]),
            "switch": str(metrics[2]),
        },
        "alternative_cost": str(cost),
        "causal_null_risk": str(risk),
        "lambda": 1,
        "scalarized_cost": str(scalarized),
        "max_pathwise_queries": max_queries,
        "budget": config.budget,
        "learner_information_sets_visited": len(seen),
        "controller_request_partitions": len(info_to_distribution),
        "max_gadget_residual": max_partition_residual,
        "max_action_normalization_error": max_normalization_error,
        "max_rationalization_l1": str(max_rounding_l1),
    }
    if not F(1) <= scalarized <= F(1) + F(5, 1000):
        raise SystemExit(f"scalarized value check failed: {scalarized}")
    if max_partition_residual > 1e-7:
        raise SystemExit(f"gadget residual check failed: {max_partition_residual}")
    if max_queries > config.budget:
        raise SystemExit(f"pathwise budget check failed: {max_queries}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
