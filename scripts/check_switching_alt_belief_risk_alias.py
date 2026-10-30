"""Exact arithmetic check for a posterior-only risk-allocation counterexample."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def main() -> dict:
    alpha = F(1, 10)
    query_cost = F(1, 100)
    switch_cost = F(1, 10)
    future_rounds = 3
    budget = 2
    delay = 1

    alternative_tapes = {(1, 1): F(9, 10), (0, 1): F(1, 10)}
    assert sum(alternative_tapes.values()) == 1
    # After the transition, both tapes induce the same current hidden-state posterior.
    current_belief = {tape: F(1) for tape in alternative_tapes}
    assert len(set(current_belief.values())) == 1

    endpoint_values = []
    for p1, p2_after_zero, p2_after_one in product((F(0), F(1, 2)), repeat=3):
        event_probability = p1 * p2_after_one
        endpoint_values.append(event_probability)
    event11_risk = max(endpoint_values)
    assert event11_risk == F(1, 4)

    activation = alpha / event11_risk
    safe_alt_promotion_probability = alternative_tapes[(1, 1)] * activation
    per_promotion_value = F(future_rounds) - switch_cost
    safe_query_cost = budget * query_cost
    unrestricted_value = safe_alt_promotion_probability * per_promotion_value - safe_query_cost

    # On the alternative support, posterior-only behavior must use the same beta
    # on 11 and 01. Give it favorable off-support behavior: reject whenever Y2=0.
    # Under the causal null P(Y2=1)<=1/2, so beta can be at most 2*alpha.
    posterior_only_promotion_probability = min(F(1), alpha / F(1, 2))
    posterior_only_value = (
        posterior_only_promotion_probability * per_promotion_value - safe_query_cost
    )
    gap = unrestricted_value - posterior_only_value

    assert activation == F(2, 5)
    assert safe_alt_promotion_probability == F(9, 25)
    assert unrestricted_value == F(128, 125)
    assert posterior_only_promotion_probability == F(1, 5)
    assert posterior_only_value == F(14, 25)
    assert gap == F(58, 125)

    # Positive feasibility slack does not remove the loss from merging the two
    # alternative histories with the same current HMM posterior.
    risk_slack = F(1, 100)
    slack_activation = (alpha - risk_slack) / event11_risk
    slack_policy_risk = slack_activation * event11_risk
    slack_alt_promotion_probability = alternative_tapes[(1, 1)] * slack_activation
    slack_full_value = slack_alt_promotion_probability * per_promotion_value - safe_query_cost
    slack_gap = slack_full_value - posterior_only_value
    assert slack_activation == F(9, 25)
    assert slack_policy_risk == F(9, 100)
    assert alpha - slack_policy_risk == risk_slack
    assert slack_full_value == F(2299, 2500)
    assert slack_gap == F(899, 2500)

    alpha_sweep = []
    for level in (F(1, 20), F(1, 10), F(1, 4), F(2, 5)):
        full_activation = min(F(1), level / event11_risk)
        belief_activation = min(F(1), level / F(1, 2))
        full_value = (
            alternative_tapes[(1, 1)] * full_activation * per_promotion_value - safe_query_cost
        )
        belief_value = belief_activation * per_promotion_value - safe_query_cost
        alpha_sweep.append(
            {
                "alpha": str(level),
                "full_history_value": str(full_value),
                "posterior_only_upper_bound": str(belief_value),
                "gap": str(full_value - belief_value),
            }
        )
        assert full_value > belief_value

    payload = {
        "status": "exact_posterior_only_compression_separation_checked",
        "contract": {
            "horizon": 5,
            "hard_query_budget": budget,
            "delay": delay,
            "alpha": str(alpha),
            "query_cost": str(query_cost),
            "switch_cost": str(switch_cost),
            "promotion_opportunity": "start of event 3 after both labels arrive",
            "null": "full-history conditional success probability in [0,1/2]",
        },
        "alternative": {
            "label_tape_probabilities": {
                "".join(map(str, tape)): str(prob) for tape, prob in alternative_tapes.items()
            },
            "current_state_posterior_by_supported_tape": {
                "".join(map(str, tape)): str(belief) for tape, belief in current_belief.items()
            },
        },
        "unrestricted_safe_policy": {
            "rule": "query at events 1 and 2; after both arrive, draw a private 2/5 coin and promote only on tape 11",
            "conditional_null_event_risk": str(event11_risk),
            "promotion_risk": str(activation * event11_risk),
            "alternative_promotion_probability": str(safe_alt_promotion_probability),
            "value_before_query_cost": str(safe_alt_promotion_probability * per_promotion_value),
            "query_cost": str(safe_query_cost),
            "net_value": str(unrestricted_value),
        },
        "posterior_only_policy_class": {
            "promotion_probability_upper_bound": str(posterior_only_promotion_probability),
            "net_value_upper_bound": str(posterior_only_value),
        },
        "value_gap": str(gap),
        "positive_slack_check": {
            "target_alpha": str(alpha),
            "risk_slack": str(risk_slack),
            "full_history_activation": str(slack_activation),
            "full_history_risk": str(slack_policy_risk),
            "full_history_value": str(slack_full_value),
            "posterior_only_value_upper_bound": str(posterior_only_value),
            "gap": str(slack_gap),
        },
        "same_model_alpha_sweep": alpha_sweep,
        "interpretation": "Rejects current-alternative-posterior-only policies; does not reject controllers with extra risk-relevant memory.",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path("outputs/switching_alt_belief_risk_alias_v1/results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    main()
