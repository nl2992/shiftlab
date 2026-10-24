import json

import pandas as pd

from shiftlab.dive.residual_variance_discounted_betting import (
    _aggregate_contrasts,
    _paired_contrasts,
    run_grid,
)


def test_discounted_betting_contrasts_cluster_shared_seed_cells():
    rows = []
    methods = (
        "fixed_mixture",
        "predictable_kelly",
        "uniform_start_mixture",
        "discounted_start_mixture",
    )
    for seed in (1, 2, 3):
        for severity in (1.5, 3.0, 4.5):
            for query_rate in (0.8, 1.0):
                for method in methods:
                    detected = method == "discounted_start_mixture" and seed == 1
                    rows.append(
                        {
                            "seed": seed,
                            "severity": severity,
                            "query_rate": query_rate,
                            "method": method,
                            "detected": detected,
                        }
                    )
    metrics = pd.DataFrame(rows)
    aggregate = _aggregate_contrasts(metrics, bootstrap_replicates=200)
    cells = _paired_contrasts(metrics, bootstrap_replicates=200)
    assert len(aggregate) == 3
    assert aggregate.seed_clusters.eq(3).all()
    assert aggregate.paired_macro_detection_difference.eq(1 / 3).all()
    assert aggregate.positive_seed_clusters.eq(1).all()
    assert len(cells) == 18
    assert cells.seed_clusters.eq(3).all()


def test_discounted_betting_grid_cpu_smoke_writes_complete_manifest(tmp_path):
    metrics, summary, aggregate, manifest = run_grid(
        tmp_path,
        seeds=2,
        n=1200,
        device="cpu",
        bootstrap_replicates=100,
    )
    assert len(metrics) == 3 * 2 * 2 * 4
    assert len(summary) == 3 * 2 * 4
    assert len(aggregate) == 3
    assert metrics.groupby(["seed", "severity", "query_rate"]).method.nunique().eq(4).all()
    assert metrics.budget_respected.all()
    assert manifest["metric_rows"] == len(metrics)
    assert (
        json.loads((tmp_path / "manifest.json").read_text())["metrics_sha256"]
        == manifest["metrics_sha256"]
    )
    assert (tmp_path / "metrics.parquet").is_file()
