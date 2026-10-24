import numpy as np
from scipy.stats import binomtest

from shiftlab.dive.delayed_grid_confirmation import (
    DelayedGridConfirmationConfig,
    exact_mcnemar_log_p,
    holm_adjust,
    holm_adjust_log_p,
    run_grid_confirmation,
)


def test_holm_adjust_preserves_original_order_and_monotonicity():
    values = holm_adjust([0.04, 0.001, 0.03, 0.8])
    assert np.allclose(values, [0.09, 0.004, 0.09, 0.8])
    ordered = np.sort(values)
    assert np.all(np.diff(ordered) >= 0)


def test_log_exact_mcnemar_matches_scipy_and_avoids_underflow():
    log_p = exact_mcnemar_log_p(30, 5)
    assert np.isclose(np.exp(log_p), binomtest(30, 35, p=0.5).pvalue)
    extreme = exact_mcnemar_log_p(1160, 7)
    assert np.isfinite(extreme)
    assert extreme < -300 * np.log(10)
    adjusted = holm_adjust_log_p([np.log(0.04), np.log(0.001), np.log(0.03)])
    assert np.allclose(np.exp(adjusted), [0.06, 0.003, 0.06])


def test_small_grid_confirmation_writes_paired_metrics_and_manifest(tmp_path):
    config = DelayedGridConfirmationConfig(
        seeds_per_cell=3,
        seed_offset=17,
        n_events=120,
        query_rates=(0.5,),
        harm_onsets=(0.5,),
        harm_increases=(0.12,),
        device="cpu",
    )
    frame, paired, manifest = run_grid_confirmation(tmp_path, config)
    assert len(frame) == 3 * 3
    assert len(paired) == 1
    assert isinstance(paired.iloc[0].holm_adjusted_p, str)
    assert np.isfinite(paired.iloc[0].holm_adjusted_log10_p)
    assert manifest["metric_rows"] == 9
    assert manifest["resolved_devices"] == ["cpu"]
    assert (tmp_path / "grid_confirmation_metrics.parquet").is_file()
    assert (tmp_path / "grid_confirmation_summary.csv").is_file()
    assert (tmp_path / "paired_tests.csv").is_file()
    assert (tmp_path / "results.md").is_file()
