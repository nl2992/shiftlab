"""Run the registered exact scalarized-DP implementation screen."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from collections import defaultdict, deque
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/research_risk_approx"))

PROTOCOL = ROOT / "docs/risk_preserving_approx/CANDIDATE_G_SCALARIZED_DP_SCREEN_PROTOCOL_V1.md"
BASELINE = ROOT / "docs/risk_preserving_approx/iid_relaxation_t10_stress_v1.json"
BELIEF_SCREEN = ROOT / "docs/risk_preserving_approx/candidate_g_iid_belief_screen_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/candidate_g_scalarized_dp_screen_v1.json"
MULTIPLIERS = tuple(map(F, (0, 1, 2, 4, 8, 16, 32)))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_hot(choices, selected):
    return tuple(F(choice == selected) for choice in choices)


def exact_risk(game, policy, *, iid: bool) -> tuple[F, int]:
    from functools import cache

    @cache
    def visit(history, outcomes):
        time_index = len(history) + 1
        if time_index > game.config.horizon:
            return F(0)
        result = F(0)
        for choice, mass in zip(game.choices(history), policy(history, outcomes), strict=True):
            if not mass:
                continue
            action, query = choice
            if action:
                continuation = F(1)
            elif query:
                following = history + ((action, query),)
                zero = visit(following, outcomes + ((time_index, 0),))
                one = visit(following, outcomes + ((time_index, 1),))
                continuation = (zero + one) / 2 if iid else max(zero, (zero + one) / 2)
            else:
                continuation = visit(history + ((action, query),), outcomes)
            result += mass * continuation
        return result

    value = visit((), ())
    return value, visit.cache_info().currsize


def root_mixture(game, first, second, weight: F):
    """Behavioral realization of a private root coin between two plans."""
    if not 0 <= weight <= 1:
        raise ValueError("mixture weight outside [0,1]")

    def consistent(plan, history, outcomes):
        for index, observed_choice in enumerate(history):
            prefix_history = history[:index]
            decision_time = index + 1
            visible_prefix = tuple(
                row for row in outcomes if row[0] + game.config.delay <= decision_time
            )
            choices = game.choices(prefix_history)
            probabilities = plan(prefix_history, visible_prefix)
            if (
                sum(
                    probability
                    for choice, probability in zip(choices, probabilities, strict=True)
                    if choice == observed_choice
                )
                == 0
            ):
                return False
        return True

    def policy(history, outcomes):
        active = []
        if weight and consistent(first, history, outcomes):
            active.append((weight, first))
        if weight < 1 and consistent(second, history, outcomes):
            active.append((1 - weight, second))
        total = sum((mass for mass, _ in active), F(0))
        if not total:
            return one_hot(game.choices(history), (0, 0))
        result = [F(0)] * len(game.choices(history))
        for mass, plan in active:
            for index, probability in enumerate(plan(history, outcomes)):
                result[index] += mass * probability / total
        return tuple(result)

    return policy


def max_path_queries(game, policy) -> int:
    maximum = 0
    for tape_bits in range(1 << game.config.horizon):
        history = ()
        outcomes = ()
        count = 0
        for event in range(1, game.config.horizon + 1):
            choices = game.choices(history)
            probabilities = policy(history, outcomes)
            selected = [choice for choice, mass in zip(choices, probabilities, strict=True) if mass]
            if len(selected) != 1:
                raise ValueError("pathwise budget check requires a deterministic component")
            action, query = selected[0]
            count += query
            if query:
                outcomes += ((event, (tape_bits >> (event - 1)) & 1),)
            if action:
                break
            history += ((action, query),)
        maximum = max(maximum, count)
    return maximum


class RSSSampler:
    def __init__(self, process, interval=0.01):
        self.process = process
        self.interval = interval
        self.peak = process.memory_info().rss
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self.stop.wait(self.interval):
            self.peak = max(self.peak, self.process.memory_info().rss)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()
        self.peak = max(self.peak, self.process.memory_info().rss)


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")

    import psutil
    from iid_relaxation_certified_pipeline import learner_only_game
    from screen_candidate_g_iid_beliefs import canonical, continue_after_action

    from shiftlab.dive.causal_switching_game import GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    baseline_sha = sha(BASELINE)
    belief_sha = sha(BELIEF_SCREEN)
    cfg = baseline["config"]
    config = GameConfig(
        horizon=cfg["horizon"],
        budget=cfg["budget"],
        delay=cfg["delay"],
        alpha=F(cfg["alpha"]),
        query_cost=F(cfg["query_cost"]),
        switch_cost=F(cfg["switch_cost"]),
        max_nodes=cfg["max_nodes"],
    )
    model = RegimeModel(
        transition01=F(cfg["transition"]),
        transition10=F(cfg["transition"]),
        emission0=F(cfg["emissions"][0]),
        emission1=F(cfg["emissions"][1]),
        prior1=F(cfg["prior"]),
    )
    start = time.perf_counter()
    process = psutil.Process(os.getpid())
    rss_start = process.memory_info().rss
    rss_sampler = RSSSampler(process)
    rss_sampler.__enter__()
    game = learner_only_game(config, model)
    initial_alt = model.propagate(model.prior1, 1)
    root_belief = canonical(
        (
            (0, 0, (), F(1, 2) * (1 - initial_alt)),
            (0, 1, (), F(1, 2) * initial_alt),
            (1, -1, (), F(1, 2)),
        )
    )
    root = (1, config.budget, root_belief)

    histories_by_state = defaultdict(set)
    histories_by_state[root].add(((), ()))
    queue = deque([root])
    visited = {root}
    transitions = {}
    while queue:
        time_index, remaining, belief = queue.popleft()
        state = (time_index, remaining, belief)
        if time_index >= config.horizon:
            transitions[state] = {}
            continue
        branches_by_query = {}
        for query in (0, 1) if remaining else (0,):
            branches = continue_after_action(belief, time_index, query, config.delay, model)
            if sum((branch[0] for branch in branches), F(0)) != 1:
                raise AssertionError("belief transition probabilities do not sum to one")
            branches_by_query[query] = branches
            for _probability, observations, following_belief in branches:
                child = (time_index + 1, remaining - query, following_belief)
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
                for history, visible in histories_by_state[state]:
                    following_history = history + ((0, query),)
                    due_rows = tuple(
                        (release - config.delay, value) for release, value in observations
                    )
                    following_visible = tuple(sorted((*visible, *due_rows)))
                    histories_by_state[child].add((following_history, following_visible))
                # Histories are propagated once per state/query/observation branch.
            # Query-transition children have a separate key per released observation.
        transitions[state] = branches_by_query

    expected_states = json.loads(BELIEF_SCREEN.read_text(encoding="utf-8"))[
        "exact_reachable_belief_decision_states"
    ]
    if len(visited) != expected_states:
        raise AssertionError(f"graph state count {len(visited)} != registered {expected_states}")

    from functools import cache

    rows = []
    policies = []
    for multiplier in MULTIPLIERS:

        @cache
        def value(state, multiplier=multiplier):
            time_index, remaining, belief = state
            alt_mass = sum((mass for mode, _s, _p, mass in belief if mode == 0), F(0))
            iid_mass = sum((mass for mode, _s, _p, mass in belief if mode == 1), F(0))
            alt_entries = [
                (hidden_state, pending, mass)
                for mode, hidden_state, pending, mass in belief
                if mode == 0
            ]
            if alt_mass:
                alt_belief = tuple(
                    (hidden_state, pending, mass / alt_mass)
                    for hidden_state, pending, mass in alt_entries
                )
                alt_positive_mass = sum(
                    (
                        mass * (model.emission1 if hidden_state else model.emission0)
                        for hidden_state, _pending, mass in alt_entries
                    ),
                    F(0),
                )
            else:
                alt_belief = ()
                alt_positive_mass = F(0)

            legal_queries = (0, 1) if remaining else (0,)
            options = []
            for action in (0, 1):
                for query in legal_queries:
                    if action:
                        alt_cost = (
                            game._promote_value(time_index, remaining, alt_belief, query)
                            if alt_mass
                            else F(0)
                        )
                        scalar = 2 * alt_mass * alt_cost + 2 * multiplier * iid_mass
                    else:
                        scalar = 2 * (alt_positive_mass + alt_mass * config.query_cost * query)
                        if time_index < config.horizon:
                            for probability, _observations, following_belief in transitions[state][
                                query
                            ]:
                                child = (time_index + 1, remaining - query, following_belief)
                                scalar += probability * value(child)[0]
                    options.append((scalar, (action, query)))
            return min(options, key=lambda row: (row[0], row[1]))

        # Fill all states through memoized backward recursion from the root.
        root_value, _root_choice = value(root)
        state_policy = {state: value(state)[1] for state in visited}
        behavior = {}
        for state, paths in histories_by_state.items():
            selected = state_policy[state]
            for history, visible in paths:
                key = (history, visible)
                previous = behavior.setdefault(key, selected)
                if previous != selected:
                    raise AssertionError("belief merge assigns inconsistent actions")

        def policy(history, outcomes, behavior=behavior):
            if any(action for action, _query in history):
                time_index = len(history) + 1
                remaining = config.budget - sum(query for _action, query in history)
                belief = game._belief_from_history(history, outcomes)
                key = (time_index, history[-1][0], remaining, belief)
                if key not in game._continuation_actions:
                    game._decision_value(time_index, history[-1][0], remaining, belief)
                selected = game._continuation_actions[key]
                return one_hot(game.choices(history), selected)
            visible = game.information(history, outcomes)[1]
            selected = behavior[(history, visible)]
            return one_hot(game.choices(history), selected)

        metrics = game.expected_metrics(policy)
        cost = sum(metrics[:3], F(0))
        iid_risk, iid_states = exact_risk(game, policy, iid=True)
        robust_risk, robust_states = exact_risk(game, policy, iid=False)
        framework_risk = game.null_risk(policy)
        if robust_risk != framework_risk:
            raise AssertionError("independent and framework null risk disagree")
        scalarized = cost + multiplier * iid_risk
        dual_bound = scalarized - multiplier * config.alpha
        rows.append(
            {
                "lambda": str(multiplier),
                "scalarized_bellman_value": str(root_value),
                "independent_scalarized_value": str(scalarized),
                "alternative_cost": str(cost),
                "iid_risk": str(iid_risk),
                "causal_null_risk": str(robust_risk),
                "dual_lower_bound": str(dual_bound),
                "iid_verifier_states": iid_states,
                "causal_null_verifier_states": robust_states,
                "decision_states_evaluated": value.cache_info().currsize,
            }
        )
        policies.append(policy)
        value.cache_clear()

    # Build safety-repaired policies and adjacent robust-risk bracket mixtures.
    from shiftlab.dive.eprocess_gated_planner import mix_with_never_promote

    def safe(history, outcomes):
        return one_hot(game.choices(history), (0, 0))

    candidates = []
    for index, (row, policy) in enumerate(zip(rows, policies, strict=True)):
        risk = F(row["causal_null_risk"])
        if risk <= config.alpha:
            candidates.append((f"lambda_{row['lambda']}", policy))
        else:
            activation = config.alpha / risk
            candidates.append(
                (
                    f"lambda_{row['lambda']}_safe_repair",
                    mix_with_never_promote(game, policy, activation),
                )
            )
    for index in range(len(rows) - 1):
        risk_a = F(rows[index]["causal_null_risk"])
        risk_b = F(rows[index + 1]["causal_null_risk"])
        if (risk_a - config.alpha) * (risk_b - config.alpha) < 0:
            weight_a = (config.alpha - risk_b) / (risk_a - risk_b)
            candidates.append(
                (
                    f"root_mix_lambda_{rows[index]['lambda']}_{rows[index + 1]['lambda']}",
                    root_mixture(game, policies[index], policies[index + 1], weight_a),
                )
            )

    candidates.append(("never_promote", safe))
    finalist_rows = []
    for name, candidate_policy in candidates:
        metrics = game.expected_metrics(candidate_policy)
        cost = sum(metrics[:3], F(0))
        iid_risk, _ = exact_risk(game, candidate_policy, iid=True)
        robust_risk, _ = exact_risk(game, candidate_policy, iid=False)
        framework_risk = game.null_risk(candidate_policy)
        if robust_risk != framework_risk:
            raise AssertionError(f"risk mismatch for {name}")
        if robust_risk <= config.alpha:
            finalist_rows.append(
                {
                    "name": name,
                    "cost": str(cost),
                    "iid_risk": str(iid_risk),
                    "risk": str(robust_risk),
                }
            )
    best = min(finalist_rows, key=lambda row: F(row["cost"]))
    best_cost = F(best["cost"])

    max_queries = max(max_path_queries(game, policy) for policy in policies)
    max_queries = max(max_queries, max_path_queries(game, safe))
    calendar = min(baseline["calendar_search"]["rows"], key=lambda row: F(row["calibrated_cost"]))
    calendar_cost = F(calendar["calibrated_cost"])
    lower_bound = max(F(row["dual_lower_bound"]) for row in rows)
    if lower_bound > best_cost:
        raise AssertionError("IID-relaxation lower bound exceeds robust-feasible upper cost")
    elapsed = time.perf_counter() - start
    pass_runtime = elapsed <= baseline["reference"]["elapsed_seconds"] / 2
    pass_utility = best_cost < calendar_cost
    pass_budget = max_queries <= config.budget
    pass_risk = F(best["risk"]) <= config.alpha
    passed = (
        len(visited) == expected_states
        and pass_budget
        and pass_risk
        and pass_runtime
        and pass_utility
        and lower_bound <= best_cost
    )
    rss_sampler.__exit__(None, None, None)
    payload = {
        "status": "completed",
        "decision": "continue_screen_pass" if passed else "close_scalarized_dp_route",
        "protocol": PROTOCOL.name,
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "baseline_sha256": baseline_sha,
        "belief_screen_sha256": belief_sha,
        "source_hashes": {
            "belief_graph_runner": sha(
                ROOT / "scripts/research_risk_approx/screen_candidate_g_iid_beliefs.py"
            ),
            "iid_pipeline": sha(
                ROOT / "scripts/research_risk_approx/iid_relaxation_certified_pipeline.py"
            ),
            "first_promotion_decomposition": sha(
                ROOT / "src/shiftlab/dive/first_promotion_decomposition.py"
            ),
            "causal_switching_game": sha(ROOT / "src/shiftlab/dive/causal_switching_game.py"),
        },
        "config": cfg,
        "multipliers": [str(value) for value in MULTIPLIERS],
        "belief_graph_states": len(visited),
        "belief_graph_transitions": sum(
            len(branches) for query_map in transitions.values() for branches in query_map.values()
        ),
        "decision_results": rows,
        "robust_feasible_candidates": finalist_rows,
        "selected": best,
        "max_queries_on_deterministic_paths": max_queries,
        "calendar_cost": str(calendar_cost),
        "calendar_schedule": calendar["schedule"],
        "dual_lower_bound": str(lower_bound),
        "certified_gap_upper": str(best_cost - lower_bound),
        "end_to_end_seconds": elapsed,
        "runtime_threshold_seconds": baseline["reference"]["elapsed_seconds"] / 2,
        "rss_delta_bytes": process.memory_info().rss - rss_start,
        "peak_rss_bytes": rss_sampler.peak,
        "baseline_reference_seconds": baseline["reference"]["elapsed_seconds"],
        "baseline_candidate_seconds": baseline["candidate"]["candidate_elapsed_seconds"],
        "pass_utility": pass_utility,
        "pass_runtime": pass_runtime,
        "pass_budget": pass_budget,
        "pass_risk": pass_risk,
        "pass": passed,
        "claim_scope": "one-cell implementation comparison; established CPOMDP reduction; no novelty claim",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
