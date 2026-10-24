import numpy as np

from shiftlab.dive.start_prior_robustness import (
    METHODS,
    StartPriorRobustnessConfig,
    _adjusted_p_below_alpha,
    _delay_values,
    _start_locations,
    run_start_prior_robustness,
)


def test_delay_laws_are_reproducible_and_within_support():
    first = _delay_values(20261024, 1000, "uniform_0_12")
    second = _delay_values(20261024, 1000, "uniform_0_12")
    assert np.array_equal(first, second)
    assert set(np.unique(first)).issubset(set(range(13)))
    assert np.all(_delay_values(1, 100, "fixed_0") == 0)
    assert np.all(_delay_values(1, 100, "fixed_12") == 12)


def test_horizon_multiplier_changes_prespecified_start_locations():
    short = _start_locations(0.5, 1000, 0.5)
    nominal = _start_locations(0.5, 1000, 1.0)
    long = _start_locations(0.5, 1000, 1.5)
    assert short[0] == nominal[0] == long[0] == 0
    assert short[-1] < nominal[-1] < long[-1]


def test_adjusted_p_value_summary_uses_the_registered_alpha():
    assert _adjusted_p_below_alpha("0.0499")
    assert _adjusted_p_below_alpha("<1e-300 (log10=-312.4)")
    assert not _adjusted_p_below_alpha("0.05")
    assert not _adjusted_p_below_alpha("1")


def test_small_robustness_screen_writes_paired_and_null_artifacts(tmp_path):
    config = StartPriorRobustnessConfig(
        seeds_per_cell=2,
        null_streams=2,
        alternative_seed_offset=1000,
        null_seed_offset=2000,
        n_events=120,
        query_rates=(0.5,),
        harm_onsets=(0.5,),
        harm_increases=(0.12,),
        horizon_multipliers=(0.5, 1.0),
        delay_laws=("fixed_0", "uniform_0_6"),
        device="cpu",
    )
    frame, paired, manifest = run_start_prior_robustness(tmp_path, config)
    assert len(frame) == 2 * 2 * 2 * len(METHODS)
    assert len(paired) == 2 * 2 * 5
    assert manifest["resolved_devices"] == ["cpu"]
    assert manifest["alternative_cells"] == 4
    assert manifest["null_metric_rows"] == 2 * 2 * 1 * 2 * 2 * 6
    assert (tmp_path / "alternative_metrics.parquet").is_file()
    assert (tmp_path / "null_summary.csv").is_file()
    assert (tmp_path / "paired_tests.csv").is_file()
