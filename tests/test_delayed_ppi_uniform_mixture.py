import numpy as np

from shiftlab.dive.delayed_evidence_directed_ppi_mixture import (
    Config,
    _generate,
    _method_parameters,
    _simulate_method,
)


def test_uniform_mixture_weights_are_registered_and_predictable_policy_kind():
    assert _method_parameters("evidence_blend_25_a0p025_p0p5_eventwise") == (
        "eventwise",
        0.025,
        0.5,
        0.25,
    )
    assert _method_parameters("evidence_blend_50_a0p025_p0p5_eventwise")[3] == 0.5
    assert _method_parameters("evidence_blend_75_a0p025_p0p5_eventwise")[3] == 0.75


def test_uniform_mixture_replay_respects_propensity_and_label_support():
    config = Config(
        seeds=2,
        n_source=100,
        n_target=240,
        budget_rate=0.2,
        q_min=0.05,
        q_max=0.8,
        max_delay=0,
        device="cpu",
    ).validate()
    x_source, z_source, x_target, z_target, _, onset, _ = _generate(
        config, seed=2_045_001, scenario="boundary_harm"
    )
    row = _simulate_method(
        config,
        seed=2_045_001,
        scenario="boundary_harm",
        method="evidence_blend_50_a0p025_p0p5_eventwise",
        x_source=x_source,
        z_source=z_source,
        x_target=x_target,
        z_target=z_target,
        delays=np.zeros(config.n_target, dtype=np.int64),
        onset=onset,
        monitor_variant="full_stream",
        continue_after_alarm=True,
    )
    assert row["budget_respected"]
    assert row["labels_queried"] <= row["hard_label_cap"]
    assert config.q_min <= row["min_propensity"] <= row["max_propensity"] <= config.q_max
    assert row["events_registered"] == row["events_updated"]
