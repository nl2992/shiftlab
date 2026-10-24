import pytest
import torch

from scripts.calibrate_history_predictable_query_bounds import (
    MARKOV_NEGATIVE_SCENARIO,
    scenario_harm_effect,
    simulate_arm,
)
from scripts.validate_markov_predictable_query_bounds import (
    DEFAULT_SEED,
    EFFECT_PROBABILITY_SHIFT_PER_UNIT,
    HARM_EFFECTS,
    HIGH_CONTEXT_PROBABILITY,
    HIGH_PROBABILITY,
    LOW_PROBABILITY,
    MARKOV_FLIP_PROBABILITY,
    ORACLE_HARM_MEAN_PER_UNIT,
    generate_markov_dependent_data,
    sample_markov_states,
    verify_dgp_algebra,
)


def test_regime_null_has_zero_conditional_mean_in_each_state():
    verify_dgp_algebra()
    means = []
    for state in (0, 1):
        p_high_context = HIGH_CONTEXT_PROBABILITY[state]
        low_mean = 1 * (1 - 2 * LOW_PROBABILITY[state])
        high_mean = 5 * (1 - 2 * HIGH_PROBABILITY[state])
        means.append((1 - p_high_context) * low_mean + p_high_context * high_mean)
    assert means == pytest.approx([0.0, 0.0], abs=1e-12)


def test_harm_doses_and_negative_control_have_registered_statewise_means():
    assert scenario_harm_effect(MARKOV_NEGATIVE_SCENARIO) == pytest.approx(-0.20)
    assert (
        0.5 * ORACLE_HARM_MEAN_PER_UNIT[0] + 0.5 * ORACLE_HARM_MEAN_PER_UNIT[1]
    ) == pytest.approx(1.0)
    assert EFFECT_PROBABILITY_SHIFT_PER_UNIT == pytest.approx(1 / 3.75)
    for effect in HARM_EFFECTS:
        assert min(HIGH_PROBABILITY.values()) - effect * EFFECT_PROBABILITY_SHIFT_PER_UNIT > 0
        state_means = [effect * ORACLE_HARM_MEAN_PER_UNIT[state] for state in (0, 1)]
        assert min(state_means) > 0
        assert sum(state_means) / 2 == pytest.approx(effect)
    negative_state_means = [-0.20 * ORACLE_HARM_MEAN_PER_UNIT[state] for state in (0, 1)]
    assert max(negative_state_means) <= 0


def test_markov_state_and_context_dependence_match_registered_transition_rates():
    streams, horizon = 64, 1000
    data = generate_markov_dependent_data(
        streams=streams,
        horizon=horizon,
        seed=DEFAULT_SEED,
        device=torch.device("cpu"),
    )
    state = data["regime_state"]
    context = data["context"]
    assert state.shape == (horizon, streams)
    assert context.shape == (horizon, streams)
    transition_rate = (state[1:] != state[:-1]).float().mean().item()
    assert transition_rate == pytest.approx(MARKOV_FLIP_PROBABILITY, abs=0.006)
    assert (context[state == 0] == 1).float().mean().item() == pytest.approx(0.5, abs=0.02)
    assert (context[state == 1] == 1).float().mean().item() == pytest.approx(0.25, abs=0.02)
    assert data["h_low"].shape == (streams,)
    assert data["h_high"].shape == (streams,)


def test_dependent_negative_null_counts_every_alarm_as_false():
    streams, horizon = 24, 40
    device = torch.device("cpu")
    data = generate_markov_dependent_data(
        streams=streams,
        horizon=horizon,
        seed=DEFAULT_SEED + 10,
        device=device,
    )
    rows = simulate_arm(
        scenario=MARKOV_NEGATIVE_SCENARIO,
        streams=streams,
        horizon=horizon,
        seed=DEFAULT_SEED + 10,
        data=data,
        device=device,
        query_policy="evidence_directed",
        q_min=0.05,
        bound_mode="predictable",
    )
    assert all(row["false_escalation"] == (row["first_alarm_event"] is not None) for row in rows)
    assert all(not row["post_onset_detection"] for row in rows)
    assert all(row["budget_respected"] for row in rows)


def test_markov_state_generator_rejects_empty_dimensions():
    with pytest.raises(ValueError, match="positive"):
        sample_markov_states(streams=0, steps=10, seed=1, device=torch.device("cpu"))
