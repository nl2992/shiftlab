"""Count exact reachable beliefs for the IID-relaxed hidden-root POMDP."""

from __future__ import annotations

import hashlib
import json
import time as timer
from collections import defaultdict, deque
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.delayed_regime_information import RegimeModel

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/CANDIDATE_G_IID_BELIEF_COMPRESSION_PROTOCOL_V1.md"
REFERENCE_PROTOCOL = ROOT / "docs/risk_preserving_approx/IID_RELAXATION_T10_STRESS_PROTOCOL_V1.md"
REFERENCE_COUNTS = ROOT / "docs/risk_preserving_approx/candidate_e_pruning_feasibility_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/candidate_g_iid_belief_screen_v1.json"

# A state entry is (root_mode, regime_state, pending (release_time, y), mass).
Belief = tuple[tuple[int, int, tuple[tuple[int, int], ...], F], ...]
DecisionState = tuple[int, int, Belief]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(entries) -> Belief:
    masses: dict[tuple[int, int, tuple[tuple[int, int], ...]], F] = defaultdict(F)
    for mode, state, pending, mass in entries:
        if mass:
            masses[mode, state, tuple(sorted(pending))] += mass
    total = sum(masses.values(), F(0))
    if not total:
        raise ValueError("cannot normalize a zero-mass belief")
    return tuple(
        (mode, state, pending, mass / total)
        for (mode, state, pending), mass in sorted(masses.items())
        if mass
    )


def release_after_event(entries, next_time: int):
    grouped: dict[tuple[tuple[int, int], ...], list] = defaultdict(list)
    for mode, state, pending, mass in entries:
        due = tuple(sorted((release, y) for release, y in pending if release <= next_time))
        remaining = tuple((release, y) for release, y in pending if release > next_time)
        grouped[due].append((mode, state, remaining, mass))
    result = []
    for observations, branch in sorted(grouped.items()):
        probability = sum((row[3] for row in branch), F(0))
        result.append((probability, observations, canonical(branch)))
    return tuple(result)


def continue_after_action(belief: Belief, time: int, query: int, delay: int, model: RegimeModel):
    """Apply hidden emissions, regime transitions, then release due labels."""
    generated = []
    for mode, state, pending, mass in belief:
        if mode == 0:
            positive = model.emission1 if state else model.emission0
            emission = ((0, 1 - positive), (1, positive))
        else:
            emission = ((0, F(1, 2)), (1, F(1, 2)))
        outcomes = emission if query else ((0, F(1)),)
        for outcome, outcome_mass in outcomes:
            next_pending = tuple(sorted((*pending, (time + delay, outcome)))) if query else pending
            if mode == 0:
                if state == 0:
                    transitions = ((0, 1 - model.transition01), (1, model.transition01))
                else:
                    transitions = ((0, model.transition10), (1, 1 - model.transition10))
            else:
                transitions = ((-1, F(1)),)
            for next_state, transition_mass in transitions:
                joint = mass * outcome_mass * transition_mass
                if joint:
                    generated.append((mode, next_state, next_pending, joint))
    return release_after_event(generated, time + 1)


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    horizon, budget, delay = 10, 4, 2
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    state0 = model.propagate(model.prior1, 1)
    initial = canonical(
        (
            (0, 0, (), F(1, 2) * (1 - state0)),
            (0, 1, (), F(1, 2) * state0),
            (1, -1, (), F(1, 2)),
        )
    )
    root: DecisionState = (1, budget, initial)
    queue = deque([root])
    visited = {root}
    edge_count = 0
    terminal_promote_actions = 0
    started = timer.perf_counter()
    status = "completed"
    error = None

    while queue:
        event, remaining, belief = queue.popleft()
        if event >= horizon:
            terminal_promote_actions += 1
            continue
        query_choices = (0, 1) if remaining else (0,)
        # Keep incumbent and continue. Promotion actions are counted but terminal
        # for the first-promotion relaxation and do not add a pre-promotion state.
        terminal_promote_actions += len(query_choices)
        for query in query_choices:
            next_remaining = remaining - query
            for probability, _observations, following in continue_after_action(
                belief, event, query, delay, model
            ):
                if not probability:
                    continue
                child = (event + 1, next_remaining, following)
                edge_count += 1
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
                    if len(visited) > 200_000:
                        status = "state_cap_exceeded"
                        queue.clear()
                        break
            if status != "completed":
                break

    elapsed = timer.perf_counter() - started
    if elapsed > 60 and status == "completed":
        status = "elapsed_limit_exceeded"
    reference_counts = json.loads(REFERENCE_COUNTS.read_text(encoding="utf-8"))
    payload = {
        "status": status,
        "error": error,
        "protocol": PROTOCOL.name,
        "protocol_sha256": digest(PROTOCOL),
        "reference_protocol_sha256": digest(REFERENCE_PROTOCOL),
        "runner_sha256": digest(Path(__file__)),
        "model_source_sha256": digest(ROOT / "src/shiftlab/dive/delayed_regime_information.py"),
        "reference_counts_sha256": digest(REFERENCE_COUNTS),
        "config": {
            "horizon": horizon,
            "budget": budget,
            "delay": delay,
            "transition": "1/10",
            "emissions": ["1/50", "49/50"],
            "prior1": "1/2",
            "root_mode_priors": ["1/2", "1/2"],
        },
        "exact_reachable_belief_decision_states": len(visited),
        "public_history_decision_states": reference_counts["exact_pre_promotion_public_histories"],
        "prepromotion_realization_columns": reference_counts["pre_promotion_realization_columns"],
        "state_ratio_to_public_histories": str(
            F(len(visited), reference_counts["exact_pre_promotion_public_histories"])
        ),
        "transition_edges": edge_count,
        "terminal_promotion_actions_counted": terminal_promote_actions,
        "build_seconds": elapsed,
        "all_beliefs_exact_rational": True,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
