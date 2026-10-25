import numpy as np

from shiftlab.dive.delayed_adaptive_query import Config, simulate


def test_delayed_adaptive_query_is_paired_bounded_and_finishes_prefix():
    config = Config(
        seeds=2,
        n_source=100,
        n_target=120,
        delay_max=5,
        variance_window=16,
        device="cpu",
    )
    arms = simulate(config, seed=17, scenario="boundary_harm")
    assert {row["query_policy"] for row in arms} == {"uniform", "variance_adaptive"}
    for row in arms:
        assert row["processed_events"] == config.n_target
        assert row["pending_at_end"] == 0
        assert row["propensities_in_range"]
        assert row["min_propensity"] >= config.q_min
        assert row["max_propensity"] <= config.q_max


def test_history_adaptive_query_uses_only_prior_feedback_and_has_variable_rate():
    config = Config(
        n_source=300,
        n_target=600,
        delay_max=0,
        variance_window=24,
        device="cpu",
    )
    uniform, adaptive = simulate(config, seed=121, scenario="benign_variance_shift")
    assert uniform["mean_propensity"] == config.base_query_rate
    assert np.isfinite(adaptive["mean_propensity"])
    assert config.q_min <= adaptive["mean_propensity"] <= config.q_max
    assert adaptive["mean_propensity"] < uniform["mean_propensity"]
    assert adaptive["processed_events"] == config.n_target


def test_second_moment_policy_does_not_react_to_sign_only_harm():
    config = Config(
        n_source=300,
        n_target=600,
        delay_max=3,
        variance_window=24,
        device="cpu",
    )
    uniform, adaptive = simulate(config, seed=211, scenario="boundary_harm")
    assert np.isclose(adaptive["mean_propensity"], uniform["mean_propensity"])
    assert adaptive["labels_queried"] == uniform["labels_queried"]
