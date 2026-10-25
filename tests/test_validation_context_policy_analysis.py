import json

import pandas as pd

from scripts.analyze_validation_context_policy import analyze


def test_context_policy_diagnostic_separates_monitor_value_from_promotion(tmp_path):
    run_root = tmp_path / "run"
    metrics = run_root / "metrics"
    reports = run_root / "reports"
    metrics.mkdir(parents=True)
    reports.mkdir()
    rows = [
        {
            "alpha_allocation": "validation_context_policy",
            "budget_rate": 0.4,
            "context_target_prevalence": 0.5,
            "context_signal_strength": 0.1,
            "context_proxy_error": 0.1,
            "selected_candidate_monitor_expected_net_gain": 0.1,
            "expected_postpromotion_net_gain": 3.0,
            "promoted": True,
            "selected_candidates_by_context": '{"0":"candidate","1":null}',
        },
        {
            "alpha_allocation": "validation_context_policy",
            "budget_rate": 0.4,
            "context_target_prevalence": 0.5,
            "context_signal_strength": 0.1,
            "context_proxy_error": 0.1,
            "selected_candidate_monitor_expected_net_gain": -0.1,
            "expected_postpromotion_net_gain": 0.0,
            "promoted": False,
            "selected_candidates_by_context": '{"0":null,"1":null}',
        },
    ]
    pd.DataFrame(rows).to_parquet(
        metrics / "context_budgeted_promotion_streams.parquet", index=False
    )
    (reports / "manifest.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")

    report_path = analyze(run_root)
    result = pd.read_parquet(metrics / "context_policy_selection_diagnostic.parquet").iloc[0]
    manifest = json.loads((reports / "manifest.json").read_text(encoding="utf-8"))
    assert result.mean_true_monitor_net_gain_per_event == 0.0
    assert result.promotion_rate == 0.5
    assert result.mean_future_gain_when_promoted == 3.0
    assert result.mean_active_contexts == 0.5
    assert "must not be treated as a registered endpoint" in report_path.read_text(encoding="utf-8")
    assert "reports/context_policy_selection_diagnostic.md" in manifest["artifacts"]
