import numpy as np
import pandas as pd
import pytest

from shiftlab.dive.hard_budget import (
    PROTECTED_EXPLORATION_STAKES,
    PROTECTED_STAKES,
    PROTECTED_WEIGHTS,
    HardBudgetConfig,
    _wilson_bounds,
    run_hard_budget,
)


def test_wilson_bounds_keep_zero_and_full_detection_rates_inside_interval():
    lower, upper = _wilson_bounds(np.array([0, 6]), np.array([6, 6]))
    assert np.all(lower <= np.array([0, 1]))
    assert np.all(upper >= np.array([0, 1]))


def test_protected_stake_prior_retains_baseline_mass_and_small_bets():
    assert len(PROTECTED_STAKES) == 5 + len(PROTECTED_EXPLORATION_STAKES)
    assert sum(PROTECTED_WEIGHTS[:5]) == pytest.approx(0.90)
    assert sum(PROTECTED_WEIGHTS[5:]) == pytest.approx(0.10)
    assert sum(PROTECTED_WEIGHTS) == pytest.approx(1.0)
    assert min(PROTECTED_EXPLORATION_STAKES) < 0.01
    assert max(PROTECTED_EXPLORATION_STAKES) <= 0.04


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
            method_subset=("uniform_proxy", "cost_stabilized_proxy", "exact_mixture_growth_proxy"),
        ),
        tmp_path / "hard_budget",
    )

    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert set(metrics.method) == {
        "uniform_proxy",
        "cost_stabilized_proxy",
        "exact_mixture_growth_proxy",
    }
    assert metrics.hard_budget.nunique() == 1
    assert metrics.budget_respected.all()
    assert (metrics.eprocess_minimum_propensity == 0.10).all()
    assert (metrics.realized_label_spend <= metrics.hard_budget + 1e-9).all()
    assert (metrics.processed_events > 0).all()
    assert {
        "single_e_detected",
        "multiscale_e_detected",
        "protected_e_detected",
    } <= set(metrics.columns)
    assert metrics["multiscale_e_false_escalation"].notna().all()
    assert (metrics.processed_events <= 800).all()
    for row in metrics.loc[metrics.stop_reason.eq("budget_reserve")].itertuples():
        assert row.budget_remaining < 2.5 + 1e-9
    assert "probability_positive" not in metrics.columns


def test_hard_budget_null_control_generates_report_without_harm_scenario(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            common_eprocess_bound=True,
            q_min=0.10,
            q_max=0.80,
            budget_rate=0.20,
            device="cpu",
            scenario_subset=("stationary",),
            method_subset=("uniform_proxy",),
        ),
        tmp_path / "null_control",
    )

    report = (output / "reports" / "hard_budget_comparison.md").read_text()
    assert "n/a / n/a" in report
    assert (output / "figures" / "hard_budget_tradeoff.png").is_file()


def test_exact_growth_cost_neutral_branch_has_target_spend_compensator(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            common_eprocess_bound=True,
            q_min=0.10,
            q_max=0.80,
            budget_rate=0.20,
            exact_growth_adaptive_weight=0.0,
            device="cpu",
            scenario_subset=("stationary",),
            method_subset=("exact_mixture_growth_proxy",),
        ),
        tmp_path / "exact_growth_cost_neutral",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    row = metrics.iloc[0]
    expected_per_event = row.hard_budget / (1600 - 800)
    assert row.exact_growth_adaptive_weight == 0.0
    assert row.predictable_spend_compensator_until_stop == pytest.approx(
        expected_per_event * row.processed_events
    )
    assert row.budget_respected


@pytest.mark.parametrize("weight", [-0.01, 1.01, float("nan")])
def test_exact_growth_weight_must_lie_in_unit_interval(weight):
    with pytest.raises(ValueError, match="exact_growth_adaptive_weight"):
        HardBudgetConfig(exact_growth_adaptive_weight=weight).validate()
