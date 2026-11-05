"""Exact finite-cell promotion-power screen for adaptive delayed HMM queries."""

from __future__ import annotations

import hashlib
import itertools
import json
import platform
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/sota_sprint/switching_c1e_anytime_power_protocol_v1.md"
OUT = ROOT / "outputs/switching_c1e_anytime_power_v1/result.json"
T, B = 20, 4
ALT_A, NULL_A = Fraction(3, 10), Fraction(1, 10)
EMIT0, EMIT1 = Fraction(4, 5), Fraction(1, 5)
ALPHAS = (Fraction(1, 20), Fraction(1, 10), Fraction(1, 5))


def trans(p: Fraction, a: Fraction) -> Fraction:
    return a + (1 - 2 * a) * p


def pred_plus(p: Fraction) -> Fraction:
    return EMIT0 * (1 - p) + EMIT1 * p


def update_next(p: Fraction, y: int, a: Fraction) -> Fraction:
    q = pred_plus(p)
    post = p * EMIT1 / q if y else p * (1 - EMIT1) / (1 - q)
    return trans(post, a)


def children(state: tuple[Fraction, Fraction]):
    p1, p0 = state
    q1, q0 = pred_plus(p1), pred_plus(p0)
    return (
        (q1, (update_next(p1, 1, ALT_A), update_next(p0, 1, NULL_A)), q1 / q0),
        (1 - q1, (update_next(p1, 0, ALT_A), update_next(p0, 0, NULL_A)), (1 - q1) / (1 - q0)),
    )


def run_alpha(alpha: Fraction) -> dict:
    threshold = 1 / alpha
    init = (Fraction(1, 2), Fraction(1, 2))

    @lru_cache(None)
    def value(t: int, b: int, state: tuple[Fraction, Fraction], lr: Fraction) -> float:
        if lr >= threshold:
            return 1.0
        if t == T:
            return 0.0
        p1, p0 = state
        skip_state = (trans(p1, ALT_A), trans(p0, NULL_A))
        skip = value(t + 1, b, skip_state, lr)
        if b == 0:
            return skip
        query = sum(
            w * value(t + 1, b - 1, child, lr * ratio) for w, child, ratio in children(state)
        )
        return max(query, skip)

    policy: dict[tuple, str] = {}

    def choose(t: int, b: int, state: tuple[Fraction, Fraction], lr: Fraction) -> str:
        key = (t, b, str(state[0]), str(state[1]), str(lr))
        if key in policy:
            return policy[key]
        if lr >= threshold or t == T or b == 0:
            action = "stop"
        else:
            skip_state = (trans(state[0], ALT_A), trans(state[1], NULL_A))
            skip = value(t + 1, b, skip_state, lr)
            query = sum(
                w * value(t + 1, b - 1, child, lr * ratio) for w, child, ratio in children(state)
            )
            action = "query" if query >= skip else "skip"
        policy[key] = action
        return action

    def evaluate(
        t: int,
        b: int,
        state: tuple[Fraction, Fraction],
        lr: Fraction,
        law: str,
        fixed: tuple[int, ...] | None = None,
        policy_map: dict[tuple, str] | None = None,
    ) -> float:
        if lr >= threshold:
            return 1.0
        if t == T:
            return 0.0
        if fixed is not None:
            action = "query" if t in fixed else "skip"
        elif policy_map is not None:
            action = choose(t, b, state, lr)
        else:
            action = choose(t, b, state, lr)
        if action != "query" or b == 0:
            next_state = (trans(state[0], ALT_A), trans(state[1], NULL_A))
            return evaluate(t + 1, b, next_state, lr, law, fixed, policy_map)
        total = 0.0
        for w_alt, child, ratio in children(state):
            weight = w_alt if law == "alt" else w_alt / ratio
            total += float(weight) * evaluate(
                t + 1, b - 1, child, lr * ratio, law, fixed, policy_map
            )
        return total

    # Capture the exact maximizing action at each history reachable under the alternative.
    def record(t: int, b: int, state: tuple[Fraction, Fraction], lr: Fraction):
        if lr >= threshold or t == T:
            return
        action = choose(t, b, state, lr)
        if action == "query" and b:
            for _, child, ratio in children(state):
                record(t + 1, b - 1, child, lr * ratio)
        else:
            record(t + 1, b, (trans(state[0], ALT_A), trans(state[1], NULL_A)), lr)

    record(0, B, init, Fraction(1))
    adaptive_power = value(0, B, init, Fraction(1))
    adaptive_null = evaluate(0, B, init, Fraction(1), "null", policy_map=policy)

    def fixed_power(calendar: tuple[int, ...], law: str) -> float:
        return evaluate(0, B, init, Fraction(1), law, fixed=calendar)

    @lru_cache(None)
    def expected_queries(t: int, b: int, state: tuple[Fraction, Fraction], lr: Fraction) -> float:
        if lr >= threshold or t == T:
            return 0.0
        action = choose(t, b, state, lr)
        if action != "query" or b == 0:
            return expected_queries(t + 1, b, (trans(state[0], ALT_A), trans(state[1], NULL_A)), lr)
        return 1.0 + sum(
            w * expected_queries(t + 1, b - 1, child, lr * ratio)
            for w, child, ratio in children(state)
        )

    @lru_cache(None)
    def max_lr_for_calendar(
        t: int, state: tuple[Fraction, Fraction], lr: Fraction, calendar: tuple[int, ...]
    ) -> Fraction:
        if t == T:
            return lr
        if t not in calendar:
            return max_lr_for_calendar(
                t + 1, (trans(state[0], ALT_A), trans(state[1], NULL_A)), lr, calendar
            )
        return max(
            max_lr_for_calendar(t + 1, child, lr * ratio, calendar)
            for _, child, ratio in children(state)
        )

    calendars = []
    for n in range(B + 1):
        for xs in itertools.combinations(range(T), n):
            # A query at t=T-1 is observed at the horizon and can be useful.
            pa = fixed_power(xs, "alt")
            pn = fixed_power(xs, "null")
            calendars.append((pa, pn, xs))
    best_calendar = max(calendars, key=lambda z: (z[0], tuple(-i for i in z[2])))
    bursts = []
    for n in range(B + 1):
        for s in range(T - n + 1):
            xs = tuple(range(s, s + n))
            bursts.append((fixed_power(xs, "alt"), fixed_power(xs, "null"), xs))
    best_burst = max(bursts, key=lambda z: (z[0], tuple(-i for i in z[2])))
    lr_ceiling = max(
        (max_lr_for_calendar(0, init, Fraction(1), row[2]), row[2]) for row in calendars
    )

    actions = []
    for (t, b, p1, p0, lr), action in sorted(policy.items()):
        actions.append(
            {
                "t": t,
                "remaining": b,
                "belief_alt_state1": p1,
                "belief_null_state1": p0,
                "lr": lr,
                "action": action,
            }
        )
    return {
        "alpha": float(alpha),
        "threshold": float(threshold),
        "calendar_count": len(calendars),
        "adaptive_power": adaptive_power,
        "adaptive_null_crossing_probability": adaptive_null,
        "adaptive_expected_queries_alt": expected_queries(0, B, init, Fraction(1)),
        "best_fixed_calendar": list(best_calendar[2]),
        "best_fixed_calendar_power": best_calendar[0],
        "best_fixed_calendar_null_crossing_probability": best_calendar[1],
        "best_contiguous_burst": list(best_burst[2]),
        "best_contiguous_burst_power": best_burst[0],
        "best_contiguous_burst_null_crossing_probability": best_burst[1],
        "adaptive_minus_best_calendar_power": adaptive_power - best_calendar[0],
        "adaptive_over_best_calendar_power": adaptive_power / best_calendar[0]
        if best_calendar[0]
        else None,
        "max_attainable_lr_over_all_fixed_calendars": float(lr_ceiling[0]),
        "max_lr_witness_calendar": list(lr_ceiling[1]),
        "reachable_policy_states": len(policy),
        "dp_state_count": value.cache_info().currsize,
        "policy_decisions": actions,
    }


def main() -> None:
    rows = [run_alpha(a) for a in ALPHAS]
    payload = {
        "status": "exact finite-cell development screen; not a method/SOTA/novelty result",
        "model": {
            "T": T,
            "B": B,
            "delay": 1,
            "alternative_transition_switch_probability": "3/10",
            "null_transition_switch_probability": "1/10",
            "emission_plus_by_state": ["4/5", "1/5"],
            "initial_state1_probability": "1/2",
        },
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "results": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            [
                {
                    k: row[k]
                    for k in (
                        "alpha",
                        "adaptive_power",
                        "adaptive_null_crossing_probability",
                        "best_fixed_calendar",
                        "best_fixed_calendar_power",
                        "best_fixed_calendar_null_crossing_probability",
                        "best_contiguous_burst",
                        "best_contiguous_burst_power",
                        "best_contiguous_burst_null_crossing_probability",
                        "adaptive_minus_best_calendar_power",
                        "adaptive_over_best_calendar_power",
                        "reachable_policy_states",
                        "dp_state_count",
                    )
                }
                for row in rows
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
