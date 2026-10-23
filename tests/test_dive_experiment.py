import numpy as np
import pytest

from shiftlab.dive.experiment import (
    DiveExperimentConfig,
    _material_harm_onset,
    _synthetic_label_costs,
)


def test_material_harm_onset_uses_regime_mean_not_individual_features():
    expected = np.full(1000, 0.05)
    expected[500:] = 0.2
    assert _material_harm_onset(expected, 0.1, change_times=[500], monitor_start=200) == 300


def test_stationary_high_tail_noise_does_not_define_harm_by_single_event():
    expected = np.full(1000, 0.06)
    expected[400] = 0.9
    assert _material_harm_onset(expected, 0.1, change_times=[], monitor_start=200) is None


def test_recurring_regime_onsets_are_checked_segment_by_segment():
    expected = np.array([0.05] * 250 + [0.2] * 250 + [0.03] * 250 + [0.25] * 250)
    assert _material_harm_onset(expected, 0.1, change_times=[250, 500, 750], monitor_start=250) == 0


def test_synthetic_label_tariff_is_bounded_and_uses_only_observed_features():
    x = np.zeros((3, 4))
    x[:, -1] = [-100.0, 0.0, 100.0]
    costs = _synthetic_label_costs(x)
    assert costs[0] == pytest.approx(0.5)
    assert costs[1] == pytest.approx(1.5)
    assert costs[2] == pytest.approx(2.5)


def test_experiment_subset_selectors_validate_registered_choices():
    DiveExperimentConfig(
        scenario_subset=("stationary", "boundary_local_harm"),
        method_subset=("uniform_proxy", "cost_stabilized_proxy"),
        heterogeneous_label_costs=True,
    ).validate()
    with pytest.raises(ValueError, match="registered scenario"):
        DiveExperimentConfig(scenario_subset=("made_up",)).validate()
    with pytest.raises(ValueError, match="enabled by this config"):
        DiveExperimentConfig(method_subset=("cost_stabilized_proxy",)).validate()
