import pandas as pd
import pytest

from shiftlab.dive.evaluation import apply_population_null_classification
from shiftlab.dive.oracle_diagnostics import gaussian_threshold_excess_risk


def test_stationary_and_nuisance_population_risks_are_true_nulls():
    stationary = gaussian_threshold_excess_risk("stationary")
    benign = gaussian_threshold_excess_risk("benign_nuisance")
    assert stationary == pytest.approx(0.0792951293, abs=1e-9)
    assert benign == pytest.approx(stationary, abs=1e-12)
    assert stationary < 0.10


@pytest.mark.parametrize(
    ("scenario", "severity", "expected"),
    [
        ("boundary_local_harm", 1.5, 0.3782744943),
        ("residual_variance", 1.5, 0.1318815253),
    ],
)
def test_shifted_regimes_are_population_alternatives(scenario, severity, expected):
    excess = gaussian_threshold_excess_risk(scenario, severity=severity)
    assert excess == pytest.approx(expected, abs=1e-9)
    assert excess > 0.10


def test_oracle_integrator_rejects_unregistered_scenario():
    with pytest.raises(ValueError, match="scenario must be"):
        gaussian_threshold_excess_risk("unregistered")


def test_population_null_reclassification_preserves_path_flags_and_counts_alarms():
    raw = pd.DataFrame(
        {
            "scenario": ["stationary", "boundary_local_harm"],
            "material_harm": [True, True],
            "harm_onset_relative": [10, 10],
            "single_e_alarm": [True, True],
            "single_e_false_escalation": [False, False],
            "single_e_detected": [True, True],
            "single_e_delay": [0, 0],
        }
    )
    clean = apply_population_null_classification(raw)
    null, alternative = clean.iloc[0], clean.iloc[1]
    assert bool(null.population_null_control)
    assert bool(null.sample_path_material_harm)
    assert not bool(null.material_harm)
    assert pd.isna(null.harm_onset_relative)
    assert bool(null.single_e_false_escalation)
    assert not bool(null.single_e_detected)
    assert pd.isna(null.single_e_delay)
    assert not bool(alternative.population_null_control)
    assert bool(alternative.material_harm)
    assert bool(alternative.single_e_detected)
    assert not bool(alternative.single_e_false_escalation)
