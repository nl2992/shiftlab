"""Exact compact-state risk recursion for a delayed finite-state controller."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def risk_after_first(y1: int, endpoints: tuple[F, ...]) -> F:
    """Worst conditional risk for the XOR terminal decision after observing Y1."""
    risks = []
    for p2 in endpoints:
        risks.append((1 - p2) * int(y1 != 0) + p2 * int(y1 != 1))
    return max(risks)


def main() -> None:
    endpoints = (F(0), F(1, 2))
    continuation = {y1: risk_after_first(y1, endpoints) for y1 in (0, 1)}
    compact_value = max((1 - p1) * continuation[0] + p1 * continuation[1] for p1 in endpoints)

    # Independent enumeration of every pure causal endpoint profile
    # (p1, p2|Y1=0, p2|Y1=1).
    full_history_values = []
    for p1, p20, p21 in product(endpoints, repeat=3):
        value = (1 - p1) * p20 + p1 * (1 - p21)
        full_history_values.append(((p1, p20, p21), value))
    explicit_value = max(value for _, value in full_history_values)
    argmax = [params for params, value in full_history_values if value == explicit_value]

    assert continuation == {0: F(1, 2), 1: F(1)}
    assert compact_value == explicit_value == F(3, 4)

    result = {
        "status": "finite_state_delayed_risk_recursion_matches_causal_oracle",
        "controller": "query Y1 at event 1 and Y2 at event 2; after fixed delay 2, promote iff Y1 != Y2",
        "hard_query_budget": 2,
        "release_timeline": {"Y1": "start of event 3", "Y2": "start of event 4"},
        "controller_memory": "one bit storing Y1 after its release, then compare to Y2",
        "causal_null": "P(Yt=1 | full event-time past and public choices) in [0,1/2]",
        "compact_risk_states": {
            "after_Y1_zero": str(continuation[0]),
            "after_Y1_one": str(continuation[1]),
            "initial_value": str(compact_value),
        },
        "full_history_endpoint_profiles_checked": len(full_history_values),
        "full_history_risk": str(explicit_value),
        "worst_endpoint_profiles": [[str(value) for value in profile] for profile in argmax],
        "state_compression": "risk recursion merges histories with the same finite controller state, queue, budget and time; rectangular [0,1/2] conditional set makes the Bellman recursion exact",
        "scope": "Fixed finite-state controller verifier only; no controller-optimization, regret or novelty claim.",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_fsc_delayed_risk_compression_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
