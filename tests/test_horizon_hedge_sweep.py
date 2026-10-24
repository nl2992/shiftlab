from shiftlab.dive.horizon_hedge_sweep import (
    METHODS,
    HorizonHedgeSweepConfig,
    run_horizon_hedge_sweep,
)


def test_small_horizon_hedge_sweep_writes_null_and_alternative_artifacts(tmp_path):
    config = HorizonHedgeSweepConfig(
        seeds_per_cell=2,
        null_streams=2,
        alternative_seed_offset=1000,
        null_seed_offset=2000,
        n_events=120,
        query_rates=(0.5,),
        harm_onsets=(0.5,),
        harm_increases=(0.12,),
        device="cpu",
    )
    frame, paired, manifest = run_horizon_hedge_sweep(tmp_path, config)
    assert len(frame) == 2 * len(METHODS)
    assert len(paired) == len(METHODS) - 1
    assert manifest["resolved_devices"] == ["cpu"]
    assert manifest["alternative_metric_rows"] == 2 * len(METHODS)
    assert manifest["null_metric_rows"] == 2 * 2 * 1 * 5
    assert (tmp_path / "alternative_metrics.parquet").is_file()
    assert (tmp_path / "null_metrics.parquet").is_file()
    assert (tmp_path / "paired_tests.csv").is_file()
