import numpy as np

from shiftlab.dive.regime_warning_grid import run_grid, warning_active_probability


def test_standard_normal_warning_threshold_has_registered_false_warning_rate():
    assert np.isclose(warning_active_probability(0.05, 0.0), 0.95)
    assert warning_active_probability(0.05, 0.5) < warning_active_probability(0.05, 0.0)
    assert warning_active_probability(0.05, 1.0) < warning_active_probability(0.05, 0.5)
    assert np.isclose(warning_active_probability(0.05, 0.0, 0.2), 0.76)


def test_regime_warning_grid_cpu_smoke(tmp_path):
    metrics, contrasts, manifest = run_grid(
        tmp_path,
        seeds=2,
        horizon=100,
        signal_strengths=(0.0, 1.0),
        warning_false_positive_rates=(0.05,),
        warning_missingness_rates=(0.0, 0.2),
        warning_event_costs=(0.0, 0.001),
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["status"] == "development_only_no_independent_selection_or_confirmation"
    assert manifest["warning_feature_visible_at_prediction"]
    assert not manifest["warning_policy_uses_evaluator_truth"]
    assert manifest["matched_coverage_is_evaluator_only_reference"]
    assert manifest["all_label_caps_respected"]
    assert "promotion_rollback" in set(metrics.policy)
    assert "static_coverage_0.50" in set(metrics.policy)
    warning = metrics.loc[metrics.policy.str.startswith("warning_gate")]
    assert "warning_gate_fpr_0.05_miss_0.20_cost_0.0010" in set(warning.policy)
    assert not warning.warning_missing_events.empty
    assert "matched_coverage_oracle" in set(metrics.policy)
    assert metrics.loc[
        metrics.policy.eq("matched_coverage_oracle")
    ].evaluator_oracle_reference_only.all()
    assert not contrasts.empty
    assert "static_coverage_0.25" in set(contrasts.reference)
    assert "matched_coverage_oracle" in set(contrasts.reference)
    assert (tmp_path / "metrics.parquet").is_file()
    assert (tmp_path / "manifest.json").is_file()
