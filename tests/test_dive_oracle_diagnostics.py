import pytest

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
