"""Compile a finite causal switching game into the pinned HSVI OS-POSG format."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path

from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


@dataclass(frozen=True)
class Node:
    phase: str
    time: int
    mode: str
    history: tuple[tuple[int, int], ...]
    outcomes: tuple[tuple[int, int], ...]
    hidden_state: int | None
    request: tuple[int, int] | None = None


class SwitchingOSPOSGCompiler:
    def __init__(self, config: GameConfig, model: RegimeModel, lam: F, gamma: F):
        if lam <= 0:
            raise ValueError("this compiler check requires lambda > 0")
        self.config, self.model, self.lam, self.gamma = config, model, lam, gamma
        self.action_labels = [
            "incumbent_q0",
            "incumbent_q1",
            "challenger_q0",
            "challenger_q1",
            "wait",
            "stop",
        ]
        self.player2_labels = ["dummy", "null_p0", "null_phalf"]
        self.observation_labels = ["await", "none", "y0", "y1", "terminal"]
        self.partition_keys: dict[tuple, int] = {}
        self.partition_actions: dict[int, set[int]] = defaultdict(set)
        self.states: list[Node] = []
        self.state_ids: dict[Node, int] = {}
        self.player2_actions: dict[int, tuple[int, ...]] = {}
        self.transitions: dict[tuple[int, int, int, int, int], F] = defaultdict(F)
        self.rewards: dict[tuple[int, int, int], F] = defaultdict(F)
        self.root_belief: dict[int, F] = {}
        self.terminal_state = self._add_state(
            Node("terminal", config.horizon + 1, "terminal", (), (), None)
        )
        self.terminal_partition = self._partition(("terminal",))
        self._build_root()

    def _partition(self, key: tuple) -> int:
        if key not in self.partition_keys:
            self.partition_keys[key] = len(self.partition_keys)
        return self.partition_keys[key]

    def _visible_outcomes(self, node: Node) -> tuple[tuple[int, int], ...]:
        decision_time = node.time
        return tuple((s, y) for s, y in node.outcomes if s + self.config.delay <= decision_time)

    def _learner_partition(self, node: Node) -> int:
        if node.phase == "terminal":
            return self.terminal_partition
        return self._partition(
            (node.phase, node.time, node.history, self._visible_outcomes(node), node.request)
        )

    def _add_state(self, node: Node) -> int:
        if node in self.state_ids:
            return self.state_ids[node]
        state_id = len(self.states)
        self.states.append(node)
        self.state_ids[node] = state_id
        return state_id

    def _add_transition(self, s, a1, a2, obs, sp, prob):
        self.transitions[(s, a1, a2, obs, sp)] += F(prob)

    def _build_root(self):
        p1 = self.model.propagate(self.model.prior1, 1)
        alternative_mass = F(1, 1) / (1 + self.lam)
        null_mass = self.lam / (1 + self.lam)
        for hidden, probability in ((0, 1 - p1), (1, p1)):
            state = self._add_state(Node("request", 1, "alternative", (), (), hidden))
            self.root_belief[state] = alternative_mass * probability
        null = self._add_state(Node("request", 1, "null", (), (), None))
        self.root_belief[null] = null_mass
        self._expand_request_states()

    def _expand_request_states(self):
        cursor = 0
        while cursor < len(self.states):
            state_id = cursor
            node = self.states[state_id]
            cursor += 1
            if node.phase == "request":
                self._expand_request(state_id, node)
            elif node.phase == "response":
                self._expand_response(state_id, node)
            elif node.phase == "terminal":
                self.player2_actions[state_id] = (0,)
                self.partition_actions[self.terminal_partition].add(5)
                self._add_transition(state_id, 5, 0, 4, state_id, 1)
                self.rewards[(state_id, 5, 0)] += F(0)

    def _legal_choices(self, history):
        remaining = self.config.budget - sum(query for _, query in history)
        query_options = (0, 1) if remaining else (0,)
        return tuple((action, query) for action in (0, 1) for query in query_options)

    def _expand_request(self, state_id: int, node: Node):
        partition = self._learner_partition(node)
        self.player2_actions[state_id] = (0,)
        old_action = node.history[-1][0] if node.history else 0
        for action, query in self._legal_choices(node.history):
            a1 = 2 * action + query
            self.partition_actions[partition].add(a1)
            if node.mode == "null" and action == 1:
                reward = -(1 + self.lam) * self.gamma ** (-2 * (node.time - 1))
                self.rewards[(state_id, a1, 0)] += reward
                self._add_transition(state_id, a1, 0, 4, self.terminal_state, 1)
                continue

            if node.mode == "alternative":
                positive = self.model.emission1 if node.hidden_state else self.model.emission0
                decision_cost = positive if action == 0 else 1 - positive
                decision_cost += self.config.query_cost * query
                decision_cost += self.config.switch_cost * (action != old_action)
                self.rewards[(state_id, a1, 0)] += (
                    -(1 + self.lam) * self.gamma ** (-2 * (node.time - 1)) * decision_cost
                )

            next_history = node.history + ((action, query),)
            response = Node(
                "response",
                node.time,
                node.mode,
                next_history,
                node.outcomes,
                node.hidden_state,
                (action, query),
            )
            response_id = self._add_state(response)
            self._add_transition(state_id, a1, 0, 0, response_id, 1)

    def _transition_hmm(self, state: int):
        if state == 0:
            return ((0, 1 - self.model.transition01), (1, self.model.transition01))
        return ((0, self.model.transition10), (1, 1 - self.model.transition10))

    def _expand_response(self, state_id: int, node: Node):
        wait = 4
        partition = self._learner_partition(node)
        self.partition_actions[partition].add(wait)
        _action, query = node.request
        self.player2_actions[state_id] = (1, 2) if node.mode == "null" and query else (0,)
        if node.time == self.config.horizon:
            for a2 in self.player2_actions[state_id]:
                self._add_transition(state_id, wait, a2, 4, self.terminal_state, 1)
            return

        if node.mode == "alternative":
            current_p = self.model.emission1 if node.hidden_state else self.model.emission0
            label_dist = ((0, 1 - current_p), (1, current_p)) if query else ((-1, 1),)
            for label, p_label in label_dist:
                for next_state, p_transition in self._transition_hmm(node.hidden_state):
                    outcomes = node.outcomes + (((node.time, label),) if label >= 0 else ())
                    target = Node(
                        "request", node.time + 1, node.mode, node.history, outcomes, next_state
                    )
                    target_id = self._add_state(target)
                    obs = 1 if label < 0 else 2 + label
                    self._add_transition(state_id, wait, 0, obs, target_id, p_label * p_transition)
        else:
            for a2 in self.player2_actions[state_id]:
                null_p = F(0) if a2 == 1 else F(1, 2)
                label_dist = ((0, 1 - null_p), (1, null_p)) if query else ((-1, F(1)),)
                for label, probability in label_dist:
                    outcomes = node.outcomes + (((node.time, label),) if label >= 0 else ())
                    target = Node("request", node.time + 1, node.mode, node.history, outcomes, None)
                    target_id = self._add_state(target)
                    obs = 1 if label < 0 else 2 + label
                    self._add_transition(state_id, wait, a2, obs, target_id, probability)

    def write(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        partition_ids = {
            state: self._learner_partition(node) for state, node in enumerate(self.states)
        }
        # The pinned HSVI implementation indexes a reward for every legal
        # (state, learner action, opponent action), including zero rewards.
        # Preserve the v1 compiler and make this conformance repair versioned.
        for state, partition in enumerate(partition_ids.values()):
            for a1 in self.partition_actions[partition]:
                for a2 in self.player2_actions[state]:
                    self.rewards.setdefault((state, a1, a2), F(0))
        transition_rows = [
            (*key, float(prob)) for key, prob in sorted(self.transitions.items()) if prob
        ]
        reward_rows = [(*key, float(value)) for key, value in sorted(self.rewards.items())]
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(
                f"{len(self.states)} {len(self.partition_keys)} {len(self.action_labels)} "
                f"{len(self.player2_labels)} {len(self.observation_labels)} "
                f"{len(transition_rows)} {len(reward_rows)} {float(self.gamma)}\n"
            )
            for index, node in enumerate(self.states):
                stream.write(f"s{index} {partition_ids[index]}\n")
            stream.write("\n".join(self.action_labels) + "\n")
            stream.write("\n".join(self.player2_labels) + "\n")
            stream.write("\n".join(self.observation_labels) + "\n")
            for state in range(len(self.states)):
                stream.write(" ".join(str(a) for a in self.player2_actions[state]) + "\n")
            for partition in range(len(self.partition_keys)):
                actions = self.partition_actions[partition]
                if not actions:
                    actions = {5}
                stream.write(" ".join(str(a) for a in sorted(actions)) + "\n")
            for s, a1, a2, obs, sp, prob in transition_rows:
                stream.write(f"{s} {a1} {a2} {obs} {sp} {prob}\n")
            for s, a1, a2, value in reward_rows:
                stream.write(f"{s} {a1} {a2} {value}\n")
            root_partition = partition_ids[next(iter(self.root_belief))]
            root_states = [s for s in range(len(self.states)) if partition_ids[s] == root_partition]
            stream.write(
                f"{root_partition} {' '.join(str(float(self.root_belief.get(s, 0))) for s in root_states)}\n"
            )
        return {
            "states": len(self.states),
            "partitions": len(self.partition_keys),
            "transitions": len(transition_rows),
            "rewards": len(reward_rows),
            "root_partition": root_partition,
            "root_state_count": len(root_states),
        }


def scalarized_sequence_value(config: GameConfig, model: RegimeModel, lam: F):
    game = CausalSwitchingGame(config, model)
    game.build()
    e_matrix, e = game.learner.matrix()
    f_matrix, f = game.opponent.matrix()
    n_x, n_y = game.learner.count, game.opponent.count
    null_payoff = csr_matrix(
        ([game.risk[k] for k in game.risk], ([k[0] for k in game.risk], [k[1] for k in game.risk])),
        shape=(n_x, n_y),
    )
    cost = [0.0] * n_x
    for seq, value in game.cost.items():
        cost[seq] = float(value)
    objective = cost + [float(lam * value) for value in f]
    inequalities = hstack([null_payoff.T, -f_matrix.T]).tocsr()
    equality = hstack([e_matrix, csr_matrix((len(e), len(f)))]).tocsr()
    rhs_eq = e.copy()
    rhs_ub = [0.0] * n_y
    result = linprog(
        objective,
        A_ub=inequalities,
        b_ub=rhs_ub,
        A_eq=equality,
        b_eq=rhs_eq,
        bounds=[(0, None)] * n_x + [(None, None)] * len(f),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"scalarized sequence LP failed: {result.message}")
    return -float(result.fun), {
        "learner_sequences": n_x,
        "null_sequences": n_y,
        "flow_nodes": game.nodes,
        "linprog_status": result.message,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=2)
    parser.add_argument("--budget", type=int, default=1)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--lambda", dest="lam", type=F, default=F(1))
    parser.add_argument("--gamma", type=F, default=F(9, 10))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".aris/runs/candidate_d_osposg_conversion_t2_repair_v2"),
    )
    args = parser.parse_args()
    config = GameConfig(horizon=args.horizon, budget=args.budget, delay=args.delay)
    model = RegimeModel()
    compiler = SwitchingOSPOSGCompiler(config, model, args.lam, args.gamma)
    game_path = args.output_dir / "switching.osposg"
    counts = compiler.write(game_path)
    exact_value, exact_meta = scalarized_sequence_value(config, model, args.lam)
    source_hash = __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()
    result = {
        "status": "compiled_for_hsvi",
        "config": {
            "horizon": args.horizon,
            "budget": args.budget,
            "delay": args.delay,
            "alpha": "1/10",
            "query_cost": "1/100",
            "switch_cost": "1/10",
            "lambda": str(args.lam),
            "gamma": str(args.gamma),
        },
        "osposg": counts,
        "exact_scalarized_game_value": exact_value,
        "exact_sequence_lp": exact_meta,
        "compiler_sha256": source_hash,
        "model_sha256": __import__("hashlib").sha256(game_path.read_bytes()).hexdigest(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "compile.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
