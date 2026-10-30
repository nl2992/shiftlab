"""Independent structural checks for a compiled ShiftLab OS-POSG text model."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def validate(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    cursor = 0

    def take():
        nonlocal cursor
        value = lines[cursor]
        cursor += 1
        return value

    n_states, n_parts, n_a1, n_a2, n_obs, n_trans, n_rewards, discount = take().split()
    n_states, n_parts, n_a1, n_a2, n_obs, n_trans, n_rewards = map(
        int, (n_states, n_parts, n_a1, n_a2, n_obs, n_trans, n_rewards)
    )
    states = []
    for _ in range(n_states):
        label, part = take().split()
        states.append((label, int(part)))
    a1_labels = [take() for _ in range(n_a1)]
    a2_labels = [take() for _ in range(n_a2)]
    obs_labels = [take() for _ in range(n_obs)]
    state_a2 = [set(map(int, take().split())) for _ in range(n_states)]
    part_a1 = [set(map(int, take().split())) for _ in range(n_parts)]

    transition_rows = [take().split() for _ in range(n_trans)]
    reward_rows = [take().split() for _ in range(n_rewards)]
    root_line = take().split()
    root_part = int(root_line[0])
    root_belief = [float(x) for x in root_line[1:]]
    if cursor != len(lines):
        raise ValueError(f"unexpected trailing rows: {len(lines) - cursor}")

    transitions = defaultdict(float)
    target_partitions = defaultdict(set)
    for row in transition_rows:
        s, a1, a2, obs, sp = map(int, row[:5])
        prob = float(row[5])
        transitions[s, a1, a2] += prob
        target_partitions[states[s][1], a1, obs].add(states[sp][1])

    rewards = set()
    for row in reward_rows:
        key = tuple(map(int, row[:3]))
        if key in rewards:
            raise ValueError(f"duplicate reward row {key}")
        rewards.add(key)

    expected = {
        (s, a1, a2)
        for s, (_, part) in enumerate(states)
        for a1 in part_a1[part]
        for a2 in state_a2[s]
    }
    missing_reward = sorted(expected - rewards)
    missing_transition = sorted(key for key in expected if key not in transitions)
    nonunit_transition = sorted(
        (key, mass) for key, mass in transitions.items() if abs(mass - 1.0) > 1e-12
    )
    multi_target = sorted(
        (key, sorted(values)) for key, values in target_partitions.items() if len(values) != 1
    )
    root_states = [s for s, (_, part) in enumerate(states) if part == root_part]
    if len(root_states) != len(root_belief):
        raise ValueError("root belief length does not match initial partition states")
    if abs(sum(root_belief) - 1.0) > 1e-12:
        raise ValueError(f"root belief mass is {sum(root_belief)}")
    if any(x < -1e-12 for x in root_belief):
        raise ValueError("root belief contains negative mass")

    result = {
        "states": n_states,
        "partitions": n_parts,
        "transitions": n_trans,
        "rewards": n_rewards,
        "player1_actions": a1_labels,
        "player2_actions": a2_labels,
        "observations": obs_labels,
        "discount": float(discount),
        "legal_action_triples": len(expected),
        "missing_reward_triples": missing_reward,
        "missing_transition_triples": missing_transition,
        "nonunit_transition_masses": nonunit_transition,
        "multi_target_partition_observations": multi_target,
        "root_partition": root_part,
        "root_belief_mass": sum(root_belief),
        "passed": not (missing_reward or missing_transition or nonunit_transition or multi_target),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.model)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
