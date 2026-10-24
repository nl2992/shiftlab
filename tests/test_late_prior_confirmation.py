import pandas as pd

from shiftlab.dive.late_prior_confirmation import (
    LatePriorConfirmationConfig,
    _cluster_bootstrap,
    run_late_prior_confirmation,
)


def test_seed_cluster_bootstrap_is_reproducible_and_contains_mean():
    differences = pd.Series([0.1, 0.2, 0.3, 0.4])
    first = _cluster_bootstrap(differences, replicates=1000, seed=71)
    second = _cluster_bootstrap(differences, replicates=1000, seed=71)
    assert first == second
    assert first[0] == 0.25
    assert first[1] <= first[0] <= first[2]


def test_small_late_prior_confirmation_writes_paired_artifacts(tmp_path):
    config = LatePriorConfirmationConfig(
        streams_per_cell=2,
        null_streams=2,
        alternative_seed_offset=1000,
        null_seed_offset=2000,
        n_events=120,
        device="cpu",
    )
    alternative, cells, manifest = run_late_prior_confirmation(tmp_path, config)
    assert len(alternative) == 18 * 2 * 2
    assert len(cells) == 18 * 2
    assert manifest["resolved_devices"] == ["cpu"]
    assert manifest["alternative_metric_rows"] == 72
    assert manifest["null_metric_rows"] == 2 * 2 * 3 * 2
    assert (tmp_path / "alternative_metrics.parquet").is_file()
    assert (tmp_path / "null_metrics.parquet").is_file()
    assert (tmp_path / "results.md").is_file()
