import pytest
import torch

from scripts.calibrate_history_predictable_query_bounds import (
    HARM_EFFECTS,
    HARM_SCENARIOS,
    NULL_SCENARIO,
    STRICT_NEGATIVE_SCENARIO,
    M,
    evidence_directed_propensity,
    expected_population_contrast,
    generate_common_random_numbers,
    high_probability_for_effect,
    scenario_harm_effect,
    simulate_arm,
    validate_configuration,
)


def test_dgp_has_exact_marginal_null_and_registered_harm_shift():
    assert abs(expected_population_contrast(high_probability=0.488)) < 1e-12
    for effect in HARM_EFFECTS:
        assert (
            abs(
                expected_population_contrast(high_probability=high_probability_for_effect(effect))
                - effect
            )
            < 1e-12
        )
    assert M == 5.0
    assert expected_population_contrast(high_probability=0.528) == pytest.approx(-0.20)


def test_strict_negative_control_is_a_valid_nonpositive_mean_scenario():
    assert STRICT_NEGATIVE_SCENARIO == "strict_negative_control"
    assert scenario_harm_effect(STRICT_NEGATIVE_SCENARIO) == pytest.approx(-0.20)


def test_strict_negative_control_counts_every_alarm_as_false_escalation():
    streams, horizon, seed = 32, 40, 991
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    rows = simulate_arm(
        scenario=STRICT_NEGATIVE_SCENARIO,
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        query_policy="uniform",
        q_min=0.20,
        bound_mode="fixed",
    )
    assert all(not row["post_onset_detection"] for row in rows)
    assert all(row["false_escalation"] == (row["first_alarm_event"] is not None) for row in rows)
    assert all(row["evaluator_cumulative_expected_harm_cost"] == 0 for row in rows)


def test_history_only_propensity_respects_floor_cap_and_spend_taper():
    threshold = torch.tensor([-10.0, -torch.log(torch.tensor(0.05)), 0.0])
    remaining = torch.tensor([1.0, 1.0, 0.5])
    propensity = evidence_directed_propensity(threshold, remaining, q_min=0.10)
    assert torch.all(propensity >= 0.10)
    assert torch.all(propensity <= 0.80)
    assert propensity[0].item() == pytest.approx(0.10)
    assert propensity[1].item() == pytest.approx(0.80)
    assert propensity[2].item() < 0.80


def test_cpu_smoke_preserves_budget_and_bound_invariants():
    streams, horizon, seed = 32, 40, 901
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    rows = simulate_arm(
        scenario=HARM_SCENARIOS[0],
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        query_policy="evidence_directed",
        q_min=0.10,
        bound_mode="predictable",
    )
    assert len(rows) == streams
    assert all(row["budget_respected"] for row in rows)
    assert all(row["labels_queried"] <= row["hard_label_budget"] for row in rows)
    assert all(row["events_processed"] <= horizon for row in rows)


def test_uniform_arm_stops_at_alarm_or_hard_budget():
    streams, horizon, seed = 16, 40, 121
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    rows = simulate_arm(
        scenario=NULL_SCENARIO,
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        query_policy="uniform",
        q_min=0.20,
        bound_mode="fixed",
    )
    assert len(rows) == streams
    assert all(row["budget_respected"] for row in rows)
    assert all(row["mean_propensity_processed"] == pytest.approx(0.20) for row in rows)


def test_configuration_rejects_too_short_horizon():
    try:
        validate_configuration(10, 10, 1, "cpu")
    except ValueError as exc:
        assert "horizon" in str(exc)
    else:
        raise AssertionError("too-short horizon should be rejected")
