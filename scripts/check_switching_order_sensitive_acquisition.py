"""Exact rational check for an order-sensitive delayed query example."""

from __future__ import annotations

import json
from fractions import Fraction as F
from itertools import product

HALF = F(1, 2)
TRANSITION = F(1, 4)  # P(S_{t+1}=1 | S_t=0)
STAY = F(3, 4)
EMIT_GOOD = F(9, 10)  # P(Y=1 | S=1)
EMIT_BAD = F(1, 10)  # P(Y=1 | S=0)
SWITCH_COST = F(13, 20)
QUERY_COST = F(1, 1000)
ALPHA = F(1, 20)
PROMOTION_LOTTERY = F(1, 5)


def predict_one_step(prob_good: F) -> F:
    return TRANSITION * (1 - prob_good) + STAY * prob_good


def update(prob_good: F, label: int) -> F:
    p_good = EMIT_GOOD if label else 1 - EMIT_GOOD
    p_bad = EMIT_BAD if label else 1 - EMIT_BAD
    return prob_good * p_good / (prob_good * p_good + (1 - prob_good) * p_bad)


def posterior(labels: tuple[int, ...]) -> F:
    prob_good = HALF
    for index, label in enumerate(labels):
        if index:
            prob_good = predict_one_step(prob_good)
        prob_good = update(prob_good, label)
    return prob_good


def no_query_switch_value(prob_good_s3: F) -> F:
    # Choose once at t=4 and hold through t=6. Include one HMM transition
    # before the first action and discount the belief at every future round.
    gross = sum(
        (
            2 * (EMIT_BAD + (EMIT_GOOD - EMIT_BAD) * predict_n(prob_good_s3, step)) - 1
            for step in (1, 2, 3)
        ),
        F(0),
    )
    return max(F(0), gross - SWITCH_COST)


def predict_n(prob_good: F, steps: int) -> F:
    for _ in range(steps):
        prob_good = predict_one_step(prob_good)
    return prob_good


def query_value_before_query_cost(prob_good_s3: F) -> F:
    # Query Y_4; it arrives at t=5. Then choose once for t=5,6.
    prior_s4 = predict_one_step(prob_good_s3)
    p_positive = EMIT_BAD + (EMIT_GOOD - EMIT_BAD) * prior_s4
    posterior_positive = update(prior_s4, 1)
    posterior_negative = update(prior_s4, 0)

    def continuation_value(prob_good_s4: F) -> F:
        # The label is for S_4. Switching begins at t=5 and is held through t=6.
        gross = sum(
            (
                2 * (EMIT_BAD + (EMIT_GOOD - EMIT_BAD) * predict_n(prob_good_s4, step)) - 1
                for step in (1, 2)
            ),
            F(0),
        )
        return max(F(0), gross - SWITCH_COST)

    return p_positive * continuation_value(posterior_positive) + (
        1 - p_positive
    ) * continuation_value(posterior_negative)


def exact_causal_null_risk() -> F:
    """Enumerate endpoint kernels on histories affecting the promotion event."""
    endpoints = (F(0), HALF)
    worst = F(0)
    for p1, p2_after_0, p2_after_1, p3_01, p3_10, p4_101 in product(endpoints, repeat=6):
        # Immediate promotion is randomized only after prefix 011.
        path_011 = (1 - p1) * p2_after_0 * p3_01
        # Delayed promotion is randomized only after prefix 101 and Y_4=1.
        path_1011 = p1 * (1 - p2_after_1) * p3_10 * p4_101
        worst = max(worst, PROMOTION_LOTTERY * (path_011 + path_1011))
    return worst


def as_pair(value: F) -> list[int]:
    return [value.numerator, value.denominator]


def main() -> None:
    histories = {
        "+-+": (1, 0, 1),
        "-++": (0, 1, 1),
    }
    rows = {}
    for name, labels in histories.items():
        belief = posterior(labels)
        query_gross = query_value_before_query_cost(belief)
        no_query = no_query_switch_value(belief)
        safe_query = PROMOTION_LOTTERY * query_gross - QUERY_COST
        safe_immediate = PROMOTION_LOTTERY * no_query
        rows[name] = {
            "belief_good_s3": as_pair(belief),
            "query_gross_value": as_pair(query_gross),
            "query_net_value_with_safe_lottery": as_pair(safe_query),
            "no_query_switch_value_before_safety_lottery": as_pair(no_query),
            "safe_immediate_switch_value": as_pair(safe_immediate),
            "query_optimal": safe_query > safe_immediate,
        }

    null_risk = exact_causal_null_risk()
    assert rows["+-+"]["belief_good_s3"] == [54, 65]
    assert rows["-++"]["belief_good_s3"] == [33, 35]
    assert rows["+-+"]["query_gross_value"] == [0, 1]
    assert rows["-++"]["query_gross_value"] == [0, 1]
    assert rows["+-+"]["query_net_value_with_safe_lottery"] == [-1, 1000]
    assert rows["-++"]["query_net_value_with_safe_lottery"] == [-1, 1000]
    assert rows["+-+"]["safe_immediate_switch_value"] == [0, 1]
    assert rows["-++"]["safe_immediate_switch_value"] == [0, 1]
    assert not rows["+-+"]["query_optimal"]
    assert not rows["-++"]["query_optimal"]
    assert null_risk == ALPHA
    assert sorted(histories["+-+"]) == sorted(histories["-++"])
    assert histories["+-+"][-1] == histories["-++"][-1] == 1

    print(
        json.dumps(
            {
                "contract": {
                    "horizon": 6,
                    "fixed_delay": 1,
                    "pathwise_query_budget": 4,
                    "switch_cost": as_pair(SWITCH_COST),
                    "query_cost": as_pair(QUERY_COST),
                    "global_causal_null_alpha": as_pair(ALPHA),
                    "promotion_randomization": as_pair(PROMOTION_LOTTERY),
                },
                "histories": rows,
                "worst_causal_null_promotion_risk": as_pair(null_risk),
                "score_multiset_and_current_score_match": True,
                "order_sensitive_query_separation_survives": False,
                "interpretation": "The histories have different posteriors, but with the registered switch cost and future belief decay, neither warrants a query or switch. The prior economic separation was caused by an overstated hand-derived payoff formula.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
