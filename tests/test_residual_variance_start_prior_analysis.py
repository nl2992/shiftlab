import pandas as pd

from shiftlab.dive.analyze_residual_variance_start_prior import analyze


def test_analysis_clusters_resampling_by_seed_and_audits_rows(tmp_path):
    rows = []
    detections = {
        "fixed_mixture": [False, False],
        "uniform_start_mixture": [True, False],
        "late_start_mixture": [False, True],
    }
    for seed in (10, 11):
        for severity in (1.5, 4.5):
            for query_rate in (0.2, 1.0):
                cell = int(severity == 4.5) + int(query_rate == 1.0)
                for method, outcomes in detections.items():
                    rows.append(
                        {
                            "seed": seed,
                            "severity": severity,
                            "query_rate": query_rate,
                            "method": method,
                            "detected": outcomes[cell % 2],
                            "material_harm": True,
                            "harm_onset_relative": 20,
                            "events_processed": 100,
                            "budget_respected": True,
                            "false_alarm": False,
                        }
                    )
    metrics_path = tmp_path / "metrics.parquet"
    pd.DataFrame(rows).to_parquet(metrics_path, index=False)
    contrasts, audit = analyze(
        metrics_path,
        tmp_path,
        bootstrap_replicates=100,
        bootstrap_seed=7,
    )
    assert len(contrasts) == 3
    assert contrasts.seed_clusters.eq(2).all()
    assert contrasts.cells_per_seed.eq(4).all()
    assert audit["metric_rows"] == 24
    assert audit["harm_onsets_reached"] == 24
    assert audit["budget_violations"] == 0
    assert (tmp_path / "analysis_manifest.json").is_file()
