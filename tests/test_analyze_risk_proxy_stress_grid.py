import hashlib
import json

import pandas as pd

from shiftlab.dive import analyze_risk_proxy_stress_grid as analysis


def test_analysis_checks_manifest_and_emits_paired_contrasts(tmp_path, monkeypatch):
    rows = []
    methods = ("risk_model", "ridge", "validation_best", "prequential_hedge")
    for seed in (10, 11):
        for method_index, method in enumerate(methods):
            rows.append(
                {
                    "cell_id": 1,
                    "scenario": "boundary_local_harm",
                    "severity": 1.5,
                    "query_rate": 0.2,
                    "train_fraction": 0.125,
                    "cost_ratio_fn_fp": 5.0,
                    "seed": seed,
                    "method": method,
                    "detected": method == "risk_model",
                    "material_harm": True,
                    "estimator_rmse": 1.0 + method_index,
                    "false_escalation": False,
                    "labels_queried": 20,
                    "realized_label_spend": 30.0,
                    "events_processed": 100,
                    "budget_respected": True,
                    "selected_validation_expert": "risk_model",
                }
            )
    metrics = pd.DataFrame(rows)
    path = tmp_path / "metrics.parquet"
    metrics.to_parquet(path, index=False)
    manifest = {
        "metrics_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "metric_rows": len(metrics),
        "design": {"seeds_per_cell": 2, "cell_count": 1, "device_requested": "cpu"},
        "environment": {"gpu_name": "test-device"},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(analysis, "BOOTSTRAP_REPLICATES", 50)

    contrasts, summary = analysis.analyze_risk_proxy_stress_grid(tmp_path)

    assert len(contrasts) == (1 + 5) * len(analysis.METRICS) * len(analysis.COMPARATORS)
    assert set(summary.method) == set(methods)
    overall = contrasts[contrasts.factor == "all"]
    detection = overall[overall.metric == "detected"]
    assert (detection.risk_model_minus_comparator > 0).all()
    assert json.loads((tmp_path / "manifest.json").read_text())["analysis"]["validation"][
        "matched_resources"
    ]


def test_analysis_rejects_corrupted_metrics_checksum(tmp_path):
    (tmp_path / "metrics.parquet").write_bytes(b"bad")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"metrics_sha256": "wrong"}), encoding="utf-8"
    )
    try:
        analysis.analyze_risk_proxy_stress_grid(tmp_path)
    except ValueError as exc:
        assert "checksum" in str(exc)
    else:
        raise AssertionError("corrupt metrics passed integrity checking")
