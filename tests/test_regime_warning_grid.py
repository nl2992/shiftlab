import numpy as np

from shiftlab.dive.regime_warning_grid import run_grid, warning_active_probability


def test_standard_normal_warning_threshold_has_registered_false_warning_rate():
    assert np.isclose(warning_active_probability(0.05, 0.0), 0.95)
    assert warning_active_probability(0.05, 0.5) < warning_active_probability(0.05, 0.0)
    assert warning_active_probability(0.05, 1.0) < warning_active_probability(0.05, 0.5)


def test_regime_warning_grid_cpu_smoke(tmp_path):
    metrics, contrasts, manifest = run_grid(
        tmp_path,
        seeds=2,
        horizon=100,
        signal_strengths=(0.0, 1.0),
        warning_false_positive_rates=(0.05,),
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["status"] == "development_only_no_independent_selection_or_confirmation"
    assert manifest["warning_feature_visible_at_prediction"]
    assert not manifest["oracle_truth_used_by_policy"]
    assert manifest["all_label_caps_respected"]
    assert {"promotion_rollback", "warning_gate_fpr_0.05", "static_coverage_0.50"} <= set(
        metrics.policy
    )
    assert not contrasts.empty
    assert (tmp_path / "metrics.parquet").is_file()
    assert (tmp_path / "manifest.json").is_file()
