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


def test_hard_budget_config_validates_scenario_grid_parameters():
    config = HardBudgetConfig(
        scenario_severity=2.25,
        change_fraction=0.35,
    )
    assert config.validate().scenario_severity == 2.25
    assert config.validate().change_fraction == 0.35
    with pytest.raises(ValueError, match="scenario_severity"):
        HardBudgetConfig(scenario_severity=5.1).validate()
    with pytest.raises(ValueError, match="change_fraction"):
        HardBudgetConfig(change_fraction=1.0).validate()


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


def test_hard_budget_monitor_comparators_share_labels_and_respect_cap(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            common_eprocess_bound=True,
            q_min=0.10,
            q_max=0.80,
            budget_rate=0.20,
            monitor_comparators=("variance_adaptive", "pm_eb"),
            device="cpu",
            scenario_subset=("stationary", "boundary_local_harm"),
            method_subset=("uniform_proxy",),
        ),
        tmp_path / "monitor_comparators",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert len(metrics) == 2
    assert metrics.budget_respected.all()
    assert metrics.labels_queried.notna().all()
    for comparator in ("variance_adaptive", "pm_eb"):
        assert metrics[f"{comparator}_detected"].notna().all()
        assert metrics[f"{comparator}_false_escalation"].notna().all()
        valid_alarms = metrics[f"{comparator}_alarm_time"].dropna()
        assert (valid_alarms < metrics.loc[valid_alarms.index, "processed_events"]).all()


def test_pprm_block_comparator_respects_spend_and_updates_only_complete_blocks(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            device="cpu",
            scenario_subset=("stationary", "boundary_local_harm"),
            method_subset=("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"),
        ),
        tmp_path / "pprm_block",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    pprm = metrics.loc[metrics.method.eq("pprm_block_adaptive")]
    frozen = metrics.loc[metrics.method.eq("uniform_proxy_frozen")]
    assert len(pprm) == 2
    assert len(frozen) == 2
    assert not frozen.proxy_updates_enabled.any()
    assert not pprm.proxy_updates_enabled.any()
    assert pprm.budget_respected.all()
    assert (pprm.labels_queried % 4 == 0).all()
    assert (pprm.processed_events % 20 == 0).all()
    assert np.allclose(pprm.labels_queried / pprm.processed_events, 0.20)
    assert (pprm.pprm_block_size == 20).all()
    assert (pprm.pprm_labels_per_block == 4).all()
    assert pprm.pprm_confidence_lower_bound.between(0, 1).all()
    assert pprm.pprm_reliance_mean.between(0, 1).all()
    assert pprm.pprm_reliance_last.between(0, 1).all()
    assert "probability_positive" not in metrics.columns
    assert "expected_cost_difference" not in metrics.columns
    report = (output / "reports" / "hard_budget_comparison.md").read_text()
    assert "Primary detection all / reached" in report
    assert "pprm_block_adaptive" in report


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


def test_robust_growth_hard_budget_path_records_radius_and_respects_cap(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            common_eprocess_bound=True,
            q_min=0.10,
            q_max=0.80,
            budget_rate=0.20,
            robust_growth_probability_radius=0.15,
            device="cpu",
            scenario_subset=("stationary",),
            method_subset=("robust_mixture_growth_proxy",),
        ),
        tmp_path / "robust_growth",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert len(metrics) == 1
    row = metrics.iloc[0]
    assert row.robust_growth_probability_radius == 0.15
    assert 0 <= row.robust_probability_interval_coverage <= 1
    assert row.budget_respected
    assert row.realized_label_spend <= row.hard_budget


@pytest.mark.parametrize("comparators", [("unknown",), ("pm_eb", "pm_eb")])
def test_hard_budget_rejects_unknown_or_duplicate_monitor_comparators(comparators):
    with pytest.raises(ValueError, match="monitor_comparators"):
        HardBudgetConfig(monitor_comparators=comparators).validate()


@pytest.mark.parametrize("radius", [-0.01, 1.01, float("nan")])
def test_robust_growth_probability_radius_must_lie_in_unit_interval(radius):
    with pytest.raises(ValueError, match="robust_growth_probability_radius"):
        HardBudgetConfig(robust_growth_probability_radius=radius).validate()
