"""Independently verify the saved T=8, B=4 policy's pre-promotion risk."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from functools import cache
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/risk_preserving_approx/t8_b4_policy_shape_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/t8_b4_policy_shape_verification_v1.json"
HORIZON = 8
BUDGET = 4
DELAY = 2


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    saved = json.loads(SOURCE.read_text(encoding="utf-8"))
    behavior = {}
    for row in saved["behavior_records"]:
        history = tuple(tuple(choice) for choice in row["history"])
        released = tuple(tuple(item) for item in row["released"])
        choices = tuple(tuple(choice) for choice in row["choices"])
        probabilities = tuple(F(value) for value in row["probabilities"])
        if sum(probabilities, F(0)) != 1 or any(value < 0 for value in probabilities):
            raise AssertionError("invalid behavioral probabilities")
        key = (history, released)
        if key in behavior:
            raise AssertionError("duplicate saved information key")
        behavior[key] = dict(zip(choices, probabilities, strict=True))

    def information(history, outcomes):
        now = len(history) + 1
        released = tuple((event, label) for event, label in outcomes if event + DELAY <= now)
        return history, released

    def policy(history, outcomes):
        return behavior[information(history, outcomes)]

    def choices(history):
        remaining = BUDGET - sum(query for _action, query in history)
        if remaining < 0:
            raise AssertionError("saved policy exceeds its pathwise query budget")
        return tuple(product((0, 1), (0, 1) if remaining else (0,)))

    @cache
    def robust_risk(history, outcomes):
        time = len(history) + 1
        if time > HORIZON:
            return F(0)
        total = F(0)
        probabilities = policy(history, outcomes)
        for action_query in choices(history):
            action, query = action_query
            action_mass = probabilities.get(action_query, F(0))
            if not action_mass:
                continue
            if action:
                continuation = F(1)
            elif query:
                following = history + ((action, query),)
                zero = robust_risk(following, outcomes + ((time, 0),))
                one = robust_risk(following, outcomes + ((time, 1),))
                continuation = max(zero, (zero + one) / 2)
            else:
                continuation = robust_risk(history + ((action, query),), outcomes)
            total += action_mass * continuation
        return total

    @cache
    def iid_risk(history, outcomes):
        time = len(history) + 1
        if time > HORIZON:
            return F(0)
        total = F(0)
        probabilities = policy(history, outcomes)
        for action_query in choices(history):
            action, query = action_query
            action_mass = probabilities.get(action_query, F(0))
            if not action_mass:
                continue
            if action:
                continuation = F(1)
            elif query:
                following = history + ((action, query),)
                continuation = (
                    iid_risk(following, outcomes + ((time, 0),))
                    + iid_risk(following, outcomes + ((time, 1),))
                ) / 2
            else:
                continuation = iid_risk(history + ((action, query),), outcomes)
            total += action_mass * continuation
        return total

    @cache
    def iid_promotion_by_time(history, outcomes):
        time = len(history) + 1
        if time > HORIZON:
            return (F(0),) * HORIZON
        total = [F(0)] * HORIZON
        probabilities = policy(history, outcomes)
        for action_query in choices(history):
            action, query = action_query
            action_mass = probabilities.get(action_query, F(0))
            if not action_mass:
                continue
            if action:
                future = [F(0)] * HORIZON
                future[time - 1] = 1
            elif query:
                following = history + ((action, query),)
                zero = iid_promotion_by_time(following, outcomes + ((time, 0),))
                one = iid_promotion_by_time(following, outcomes + ((time, 1),))
                future = [(a + b) / 2 for a, b in zip(zero, one, strict=True)]
            else:
                future = list(iid_promotion_by_time(history + ((action, query),), outcomes))
            total = [a + action_mass * b for a, b in zip(total, future, strict=True)]
        return tuple(total)

    promotion_support = []
    for (history, released), probabilities in behavior.items():
        time = len(history) + 1
        for (action, query), probability in probabilities.items():
            if action and probability:
                promotion_support.append(
                    {
                        "time": time,
                        "history": [list(choice) for choice in history],
                        "released": [list(item) for item in released],
                        "action_query": [action, query],
                        "probability": str(probability),
                    }
                )

    branch_info = (
        tuple(((0, 1),) * 3),
        ((1, 1), (2, 1)),
    )
    split = behavior[(branch_info[0], branch_info[1])]
    split_summary = {
        "time": 4,
        "history": [list(choice) for choice in branch_info[0]],
        "released": [list(item) for item in branch_info[1]],
        "wait_probability": str(split.get((0, 0), F(0))),
        "query_fourth_probability": str(split.get((0, 1), F(0))),
    }

    robust = robust_risk((), ())
    iid = iid_risk((), ())
    promotion_timing = iid_promotion_by_time((), ())
    if robust != F(1, 10) or iid != F(1, 10):
        raise AssertionError(f"unexpected exact risk: robust={robust}, iid={iid}")
    if len(promotion_support) != 2:
        raise AssertionError(
            f"expected two promoting information states, got {len(promotion_support)}"
        )
    if (
        split_summary["wait_probability"] != "3/5"
        or split_summary["query_fourth_probability"] != "2/5"
    ):
        raise AssertionError(f"unexpected adaptive query split: {split_summary}")
    if promotion_timing[4] != F(3, 40) or promotion_timing[5] != F(1, 40):
        raise AssertionError(f"unexpected IID branch risks: {promotion_timing}")
    if any(promotion_timing[index] for index in range(HORIZON) if index not in (4, 5)):
        raise AssertionError("promotion occurred at an unexpected event")

    payload = {
        "input_sha256": sha(SOURCE),
        "verifier_sha256": sha(Path(__file__)),
        "scope": "optimizer-free exact behavioral verification of pre-promotion risk and policy support",
        "behavior_information_states": len(behavior),
        "robust_null_risk": str(robust),
        "iid_boundary_risk": str(iid),
        "iid_promotion_probability_by_event": [str(value) for value in promotion_timing],
        "adaptive_split_after_two_positive_releases": split_summary,
        "promotion_support": promotion_support,
        "saved_solver_cost_not_recomputed": saved["exact_cost"],
        "status": "PASS",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "behavior_information_states",
                    "robust_null_risk",
                    "iid_boundary_risk",
                    "iid_promotion_probability_by_event",
                    "adaptive_split_after_two_positive_releases",
                    "status",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
