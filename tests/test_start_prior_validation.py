import numpy as np

from shiftlab.dive.start_prior_validation import (
    StartPriorValidationConfig,
    _holm_log_p,
    _mcnemar_log_p,
    run_start_prior_validation,
)


def test_mcnemar_and_holm_log_adjustment_are_ordered_and_bounded():
    values = [_mcnemar_log_p(20, 1), _mcnemar_log_p(10, 2), _mcnemar_log_p(0, 0)]
    adjusted = _holm_log_p(values)
    assert all(p <= 0 for p in adjusted)
    assert adjusted[0] <= adjusted[1] <= 0
    assert adjusted[2] == 0


def test_validation_rejects_overlapping_seed_blocks():
    config = StartPriorValidationConfig(
        null_streams=3,
        alternative_seeds_per_cell=3,
        null_seed_offset=100,
        alternative_seed_offset=102,
        device="cpu",
    )
    try:
        config.validate()
    except ValueError as error:
        assert "disjoint" in str(error)
    else:
        raise AssertionError("overlapping seed blocks should be rejected")


def test_small_fresh_validation_writes_calibration_and_paired_artifacts(tmp_path):
    config = StartPriorValidationConfig(
        null_streams=3,
        alternative_seeds_per_cell=3,
        null_seed_offset=1000,
        alternative_seed_offset=2000,
        n_events=120,
        query_rates=(0.5,),
        harm_onsets=(0.5,),
        harm_increases=(0.12,),
        device="cpu",
    )
    frame, summary, manifest = run_start_prior_validation(tmp_path, config)
    assert len(frame) == 6
    assert len(summary) == 1
    assert np.isfinite(summary.rate_difference.iloc[0])
    assert manifest["resolved_devices"] == ["cpu"]
    assert manifest["null_metric_rows"] == 2 * 1 * 3 * 2
    assert (tmp_path / "null_metrics.parquet").is_file()
    assert (tmp_path / "alternative_metrics.parquet").is_file()
    assert (tmp_path / "results.md").is_file()
