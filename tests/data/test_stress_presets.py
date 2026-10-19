import numpy as np
import pandas as pd

from shiftlab.data.synthetic import generate_chunks
from shiftlab.data.synthetic.presets import conformal_stress_catalogue, decision_stress_catalogue


def test_decision_catalogue_binds_all_ten_named_cases_to_supported_mechanisms():
    presets = decision_stress_catalogue(n=1000)
    assert len(presets) == 10
    assert len({preset.name for preset in presets}) == 10
    assert all(preset.config.scenario for preset in presets)
    assert all(preset.policy_class and preset.loss and preset.oracle_policy for preset in presets)
    assert all(preset.learner_visible_context and preset.expected_relation for preset in presets)


def test_prediction_only_case_degrades_prediction_while_preserving_actions():
    preset = next(
        item
        for item in decision_stress_catalogue(n=20000)
        if item.name == "prediction_degradation_without_decision_degradation"
    )
    generated = list(generate_chunks(preset.config))
    frame = pd.concat([item[0] for item in generated], ignore_index=True)
    oracle = pd.concat([item[1] for item in generated], ignore_index=True)
    features = np.stack(frame.features.to_numpy())
    baseline_mean = features[:, 0] - 0.9 * features[:, 1]
    shifted = oracle.weight.to_numpy() == 1
    assert shifted.any()
    assert np.array_equal(oracle.oracle_action, (baseline_mean > 0).astype(int))
    stale_mean = baseline_mean[shifted]
    true_mean = oracle.conditional_mean.to_numpy()[shifted]
    assert np.mean((true_mean - stale_mean) ** 2) > 0
    assert np.allclose(oracle.fn_cost, 1.0)


def test_conformal_catalogue_names_both_target_and_oracle_radius_scope():
    presets = conformal_stress_catalogue(n=1000)
    assert len(presets) == 13
    assert len({preset.name for preset in presets}) == 13
    assert {preset.calibration_target_scope for preset in presets} == {"conditional", "marginal"}
    assert all(
        preset.oracle_radius_scope and preset.residual_law and preset.stress for preset in presets
    )
    assert all(preset.config.scenario for preset in presets)
