import pandas as pd

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget


def test_hard_budget_run_respects_common_spend_cap_and_stops_predictably(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            common_eprocess_bound=True,
            q_min=0.10,
            q_max=0.80,
            budget_rate=0.20,
            device="cpu",
            scenario_subset=("boundary_local_harm",),
            method_subset=("uniform_proxy", "cost_stabilized_proxy"),
        ),
        tmp_path / "hard_budget",
    )

    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert set(metrics.method) == {"uniform_proxy", "cost_stabilized_proxy"}
    assert metrics.hard_budget.nunique() == 1
    assert metrics.budget_respected.all()
    assert (metrics.eprocess_minimum_propensity == 0.10).all()
    assert (metrics.realized_label_spend <= metrics.hard_budget + 1e-9).all()
    assert (metrics.processed_events > 0).all()
    assert (metrics.processed_events <= 800).all()
    for row in metrics.loc[metrics.stop_reason.eq("budget_reserve")].itertuples():
        assert row.budget_remaining < 2.5 + 1e-9
    assert "probability_positive" not in metrics.columns
