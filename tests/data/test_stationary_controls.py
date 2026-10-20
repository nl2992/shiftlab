from scripts.validate_stationary_controls import validate_stationary_controls


def test_stationary_control_suite_matches_independent_distribution_checks():
    report = validate_stationary_controls()

    assert report["checks_pass"]
    assert len(report["replicates"]) == 20
    assert all(summary["replicates"] == 5 for summary in report["summary"].values())
    assert report["summary"]["nonlinear_classification"]["checks"]["conditional_probability_pass"]
    assert report["summary"]["heteroskedastic"]["checks"]["conditional_scale_pass"]
    assert report["summary"]["heavy_tailed"]["checks"]["central_oracle_90_coverage_pass"]
