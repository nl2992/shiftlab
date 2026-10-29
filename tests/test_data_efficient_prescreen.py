import inspect
import math

import numpy as np
import pytest
from scipy.special import logsumexp

from shiftlab.dive.comparison_betting_engines import replay_engine
from shiftlab.dive.data_efficient_prescreen import (
    ALPHA,
    BOUND,
    ENGINES,
    HORIZON,
    STAKES,
    STARTS,
    evidence_replays,
    optional_policy_replay,
)


def _policy_inputs(n=8, *, budget=100.0):
    x = np.zeros((n, 2), dtype=float)
    active = np.ones(n, dtype=bool)
    tariffs = np.full(n, 1.0)
    centered = np.linspace(-0.1, 0.4, n)
    uniforms = np.zeros(n)
    validation_active = np.ones(200, dtype=bool)
    validation_tariffs = np.ones(200)
    return {
        "x": x,
        "active": active,
        "tariffs": tariffs,
        "centered_cost": centered,
        "uniforms": uniforms,
        "validation_active": validation_active,
        "validation_tariffs": validation_tariffs,
        "budget": budget,
    }


def test_cap_reservation_stops_before_event_and_emits_only_neutral_scores():
    args = _policy_inputs(n=5, budget=4.0)
    args["tariffs"][:] = 2.5
    result = optional_policy_replay(**args, policy="uniform")

    assert result["labels"] == 1
    assert result["dollars"] == pytest.approx(2.5)
    assert result["budget_respected"]
    assert result["cap_stop_index"] == 1
    assert result["selected"].tolist() == [True, False, False, False, False]
    assert result["scores"][0] == pytest.approx(args["centered_cost"][0])
    np.testing.assert_array_equal(result["scores"][1:], 0.0)
    assert result["theta"][1] == 0.0


def test_controller_does_not_use_current_event_to_choose_current_theta():
    first = _policy_inputs(n=5)
    second = _policy_inputs(n=5)
    first["centered_cost"][:2] = 4.9
    second["centered_cost"][:2] = 4.9
    second["centered_cost"][1] = -5.1

    left = optional_policy_replay(**first, policy="candidate")
    right = optional_policy_replay(**second, policy="candidate")

    assert left["theta"][0] == right["theta"][0]
    assert left["controller_log"][0]["log_R_previous"] is None
    assert left["theta"][2] != right["theta"][2]


def test_unqueried_outcomes_do_not_affect_scores_and_api_has_no_oracle_input():
    assert "oracle" not in inspect.signature(optional_policy_replay).parameters
    first = _policy_inputs(n=6)
    second = _policy_inputs(n=6)
    first["uniforms"][:] = 0.999
    second["uniforms"][:] = 0.999
    second["centered_cost"][:] = 4.9

    left = optional_policy_replay(**first, policy="paced")
    right = optional_policy_replay(**second, policy="paced")

    np.testing.assert_array_equal(left["selected"], False)
    np.testing.assert_array_equal(left["scores"], 0.0)
    np.testing.assert_array_equal(left["scores"], right["scores"])
    np.testing.assert_array_equal(left["theta"], right["theta"])


def test_fixed_stake_sr_skip_factor_one_retains_new_calendar_start():
    values = np.zeros(HORIZON)
    values[:3] = [1.0, 0.0, 1.0]
    result = evidence_replays(values[:3], 1.0, skipmask=[False, True, False])

    expected_components = []
    for stake in STAKES:
        r = 1.0 + stake
        r = 1.0 + r  # skipped factor one: R <- 1 + R
        r = (1.0 + stake) * (1.0 + r)
        expected_components.append(r)
    expected = math.log(np.mean(expected_components))

    assert result["sr_log_statistics"]["fixed1"][2] == pytest.approx(expected)
    assert result["sr_log_statistics"]["fixed1"][1] > result["sr_log_statistics"]["fixed1"][0]
    assert result["horizon_threshold"] == pytest.approx(48_000)
    assert result["actual_length"] == 3
    assert len(result["sr_log_statistics"]["fixed1"]) == HORIZON


def test_every_engine_has_restarted_fixed_and_started_paths_with_factor_one_padding():
    values = np.array([0.2, -0.1, 0.5, 0.0])
    skipped = np.array([False, False, True, False])
    result = evidence_replays(values, BOUND, skipmask=skipped)

    assert tuple(result["engines"]) == ENGINES
    for engine in ENGINES:
        assert result["engine_log_wealth"][engine].shape == (HORIZON,)
        assert result["fixed_start_log_wealth"][engine].shape == (HORIZON,)
        assert result["started_mixture_log_wealth"][engine].shape == (HORIZON,)
        assert set(result["started_log_wealth"][engine]) == set(STARTS)
        # The padded tail carries factor one, so the fixed-start wealth is flat.
        np.testing.assert_allclose(
            result["fixed_start_log_wealth"][engine][3:],
            result["fixed_start_log_wealth"][engine][3],
        )


def test_started_mixture_is_equal_weight_of_restarted_engines_and_uses_alpha_threshold():
    values = np.zeros(HORIZON)
    values[600] = BOUND
    result = evidence_replays(values, BOUND)

    for engine in ENGINES:
        component_paths = np.stack(
            [result["started_log_wealth"][engine][start] for start in STARTS]
        )
        np.testing.assert_allclose(
            result["started_mixture_log_wealth"][engine],
            logsumexp(component_paths, axis=0) - math.log(len(STARTS)),
        )
        expected_first_factor = replay_engine(np.array([BOUND]), BOUND, engine)[0]
        assert result["started_log_wealth"][engine][600][600] == pytest.approx(
            expected_first_factor
        )
        assert result["started_log_wealth"][engine][600][599] == 0.0

    assert result["started_mixture_threshold"] == pytest.approx(1 / ALPHA)
    assert result["horizon_threshold"] == pytest.approx(HORIZON / ALPHA)


@pytest.mark.parametrize("policy", ["uniform", "paced", "temporal", "candidate"])
def test_all_observation_policies_respect_hard_cap(policy):
    args = _policy_inputs(n=50, budget=20.0)
    args["tariffs"][:] = np.linspace(0.5, 2.5, 50)
    result = optional_policy_replay(**args, policy=policy)
    assert result["budget_respected"]
    assert result["dollars"] <= result["budget"]
    assert result["labels"] == int(result["labels_mask"].sum())
    np.testing.assert_array_equal(result["scores"][~result["selected"]], 0.0)
