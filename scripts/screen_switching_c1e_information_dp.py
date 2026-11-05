"""Exact finite-cell information screen for the C1-E query-timing question."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/sota_sprint/switching_c1e_information_dp_protocol_v1.md"
OUT = ROOT / "outputs/switching_c1e_information_dp_v1/result.json"
T, B = 20, 4
ALT_A, NULL_A = Fraction(3, 10), Fraction(1, 10)
EMIT0, EMIT1 = Fraction(4, 5), Fraction(1, 5)  # P(+ | state 0/1)
ZERO = Fraction(0)


def trans(p: Fraction, a: Fraction) -> Fraction:
    return a + (1 - 2 * a) * p


def pred_plus(p: Fraction) -> Fraction:
    return EMIT0 * (1 - p) + EMIT1 * p


def update(p: Fraction, y: int, a: Fraction) -> Fraction:
    q = pred_plus(p)
    post = p * EMIT1 / q if y else p * (1 - EMIT1) / (1 - q)
    return trans(post, a)


def kl_bernoulli(p: Fraction, q: Fraction) -> float:
    ans = 0.0
    for x, z in ((p, q), (1 - p, 1 - q)):
        if x:
            ans += float(x) * math.log(float(x / z))
    return ans


def immediate(state: tuple[Fraction, Fraction]) -> float:
    return kl_bernoulli(pred_plus(state[0]), pred_plus(state[1]))


def children(state: tuple[Fraction, Fraction]):
    p1, p0 = state
    q = pred_plus(p1)
    return (
        (q, (update(p1, 1, ALT_A), update(p0, 1, NULL_A))),
        (1 - q, (update(p1, 0, ALT_A), update(p0, 0, NULL_A))),
    )


@lru_cache(None)
def value(t: int, b: int, state: tuple[Fraction, Fraction]) -> float:
    if t == T:
        return 0.0
    skip = value(t + 1, b, (trans(state[0], ALT_A), trans(state[1], NULL_A)))
    if not b:
        return skip
    query = immediate(state) + sum(w * value(t + 1, b - 1, child) for w, child in children(state))
    return max(query, skip)


@lru_cache(None)
def fixed_value(
    t: int, b: int, state: tuple[Fraction, Fraction], calendar: tuple[int, ...]
) -> float:
    q_now = t in calendar
    if t == T:
        return 0.0
    if not q_now:
        return fixed_value(t + 1, b, (trans(state[0], ALT_A), trans(state[1], NULL_A)), calendar)
    if b <= 0:
        raise ValueError("calendar exceeds pathwise budget")
    return immediate(state) + sum(
        w * fixed_value(t + 1, b - 1, child, calendar) for w, child in children(state)
    )


def main():
    init = (Fraction(1, 2), Fraction(1, 2))
    oracle = value(0, B, init)
    calendars = []
    for n in range(B + 1):
        for xs in itertools.combinations(range(T), n):
            calendars.append((fixed_value(0, B, init, xs), xs))
    best_val, best_cal = max(calendars, key=lambda z: z[0])
    burst = max(
        (
            (fixed_value(0, B, init, tuple(range(s, s + n))), tuple(range(s, s + n)))
            for n in range(1, B + 1)
            for s in range(T - n + 1)
        ),
        key=lambda z: z[0],
    )

    policy = {}

    def walk(t, b, state):
        if t == T:
            return
        skip_state = (trans(state[0], ALT_A), trans(state[1], NULL_A))
        skip = value(t + 1, b, skip_state)
        query = -1.0
        if b:
            query = immediate(state) + sum(
                w * value(t + 1, b - 1, child) for w, child in children(state)
            )
        act = int(b > 0 and query >= skip)
        key = (t, b, str(state[0]), str(state[1]))
        policy[key] = "query" if act else "skip"
        next_states = [c for _, c in children(state)] if act else [skip_state]
        for ns in next_states:
            walk(t + 1, b - act, ns)

    walk(0, B, init)

    @lru_cache(None)
    def expected_queries(t, b, state):
        if t == T:
            return 0
        skip_state = (trans(state[0], ALT_A), trans(state[1], NULL_A))
        skip = value(t + 1, b, skip_state)
        query = -1.0
        if b:
            query = immediate(state) + sum(
                w * value(t + 1, b - 1, child) for w, child in children(state)
            )
        if b and query >= skip:
            return 1 + sum(
                w * expected_queries(t + 1, b - 1, child) for w, child in children(state)
            )
        return expected_queries(t + 1, b, skip_state)

    payload = {
        "status": "exact finite-cell information diagnostic; not a method/SOTA/power/FAR/cost claim",
        "model": {
            "T": T,
            "B": B,
            "delay": 1,
            "alternative_transition": [["7/10", "3/10"], ["3/10", "7/10"]],
            "null_transition": [["9/10", "1/10"], ["1/10", "9/10"]],
            "emission_plus_by_state": ["4/5", "1/5"],
        },
        "calendar_count": len(calendars),
        "best_fixed_calendar": list(best_cal),
        "best_fixed_kl": best_val,
        "best_contiguous_burst": list(burst[1]),
        "best_contiguous_burst_kl": burst[0],
        "adaptive_oracle_kl": oracle,
        "adaptive_over_best_calendar_ratio": oracle / best_val if best_val else None,
        "adaptive_minus_best_calendar_kl": oracle - best_val,
        "oracle_gap": 0.0,
        "adaptive_expected_queries": float(expected_queries(0, B, init)),
        "reachable_policy_states": len(policy),
        "policy_decisions": [
            {"t": k[0], "remaining": k[1], "belief_alt": k[2], "belief_null": k[3], "action": a}
            for k, a in sorted(policy.items())
        ],
        "dp_state_count": value.cache_info().currsize,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "interpretation": "A finite-cell gain over calendars is standard adaptive sensing evidence only. No novelty claim follows.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: payload[k]
                for k in (
                    "calendar_count",
                    "best_fixed_calendar",
                    "best_fixed_kl",
                    "best_contiguous_burst",
                    "best_contiguous_burst_kl",
                    "adaptive_oracle_kl",
                    "adaptive_over_best_calendar_ratio",
                    "adaptive_minus_best_calendar_kl",
                    "adaptive_expected_queries",
                    "reachable_policy_states",
                    "dp_state_count",
                    "script_sha256",
                    "protocol_sha256",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
