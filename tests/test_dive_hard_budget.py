from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from shiftlab.dive.hard_budget import (
    DEFAULT_HARD_BUDGET_METHODS,
    EVIDENCE_DIRECTED_GRID_METHODS,
    HARD_BUDGET_METHODS,
    PROTECTED_EXPLORATION_STAKES,
    PROTECTED_STAKES,
    PROTECTED_WEIGHTS,
    HardBudgetConfig,
    _one_pprm_block_method,
    _wilson_bounds,
    run_hard_budget,
)
from shiftlab.dive.proxy import DecisionLossProxy


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
    with pytest.raises(ValueError, match="PPRM blocks"):
        HardBudgetConfig(pprm_block_size=20, pprm_labels_per_block=20).validate()
    with pytest.raises(ValueError, match="pprm_initial_reliance"):
        HardBudgetConfig(pprm_max_reliance=0.5, pprm_initial_reliance=1.0).validate()
    with pytest.raises(ValueError, match="budget_dollars"):
        HardBudgetConfig(budget_dollars=0).validate()
    with pytest.raises(ValueError, match="monitor_horizon_events"):
        HardBudgetConfig(n=1600, monitor_horizon_events=801).validate()


def test_evidence_urgency_grid_has_nine_explicit_candidates_without_expanding_defaults():
    assert len(EVIDENCE_DIRECTED_GRID_METHODS) == 9
    assert set(EVIDENCE_DIRECTED_GRID_METHODS) <= set(HARD_BUDGET_METHODS)
    assert not set(EVIDENCE_DIRECTED_GRID_METHODS) & set(DEFAULT_HARD_BUDGET_METHODS)
    config = HardBudgetConfig(method_subset=tuple(EVIDENCE_DIRECTED_GRID_METHODS)).validate()
    assert set(config.method_subset) == set(EVIDENCE_DIRECTED_GRID_METHODS)


def test_fixed_dollar_cap_and_monitor_horizon_are_respected_for_eventwise_and_block_methods(
    tmp_path,
):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            budget_rate=0.20,
            budget_dollars=100.0,
            monitor_horizon_events=400,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            pprm_block_size=10,
            pprm_labels_per_block=2,
            pprm_max_reliance=0.1,
            pprm_initial_reliance=0.1,
            device="cpu",
            scenario_subset=("boundary_local_harm",),
            method_subset=("uniform_proxy", "pprm_block_adaptive"),
        ),
        tmp_path / "fixed_dollar_horizon",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert metrics.hard_budget.tolist() == pytest.approx([100.0, 100.0])
    assert metrics.budget_respected.all()
    assert (metrics.processed_events <= 400).all()
    assert metrics.monitor_fraction_processed.between(0, 1).all()
    eventwise = metrics.loc[metrics.method.eq("uniform_proxy")].iloc[0]
    assert np.array_equal(eventwise.started_mixture_e_starts, [0, 100, 200, 300])
    assert isinstance(eventwise.started_mixture_e_detected, (bool, np.bool_))
    pprm = metrics.loc[metrics.method.eq("pprm_block_adaptive")].iloc[0]
    assert pprm.processed_events % 10 == 0
    assert pprm.pprm_max_reliance == pytest.approx(0.1)


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


def test_hard_budget_records_policy_specific_propensity_support_bounds(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=False,
            generate_figure=False,
            device="cpu",
            scenario_subset=("stationary",),
            method_subset=("uniform_proxy", "variance_proxy"),
        ),
        tmp_path / "policy_specific_bounds",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    uniform = metrics.loc[metrics.method.eq("uniform_proxy")].iloc[0]
    adaptive = metrics.loc[metrics.method.eq("variance_proxy")].iloc[0]
    assert uniform.eprocess_minimum_propensity == pytest.approx(0.20)
    assert uniform.eprocess_support_bound == pytest.approx(45.9)
    assert adaptive.eprocess_minimum_propensity == pytest.approx(0.10)
    assert adaptive.eprocess_support_bound == pytest.approx(96.9)


def test_parallel_hard_budget_replicates_match_serial_seed_results(tmp_path):
    common = {
        "n": 1600,
        "seeds": 1,
        "seed_offset": 87654321,
        "budget_rate": 0.20,
        "q_min": 0.10,
        "q_max": 0.80,
        "common_eprocess_bound": False,
        "generate_figure": False,
        "device": "cpu",
        "scenario_subset": ("stationary",),
        "method_subset": ("uniform_proxy", "variance_proxy"),
    }
    serial = run_hard_budget(HardBudgetConfig(**common, workers=1), tmp_path / "serial_run")
    parallel = run_hard_budget(HardBudgetConfig(**common, workers=2), tmp_path / "parallel_run")
    serial_metrics = pd.read_parquet(serial / "metrics" / "hard_budget_comparison.parquet")
    parallel_metrics = pd.read_parquet(parallel / "metrics" / "hard_budget_comparison.parquet")
    pd.testing.assert_frame_equal(serial_metrics, parallel_metrics)


def test_evidence_directed_policy_uses_preoutcome_evidence_and_skips_unavailable_visuals(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1600,
            seeds=1,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            generate_figure=False,
            device="cpu",
            scenario_subset=("boundary_local_harm",),
            method_subset=("uniform_proxy", "evidence_curve_a0.05_p0.5"),
        ),
        tmp_path / "evidence_directed",
    )
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    assert set(metrics.method) == {"uniform_proxy", "evidence_curve_a0.05_p0.5"}
    assert metrics.budget_respected.all()
    evidence = metrics.loc[metrics.method.eq("evidence_curve_a0.05_p0.5")].iloc[0]
    assert evidence.query_propensity_min >= 0.10
    assert evidence.query_propensity_max <= 0.80
    assert evidence.eprocess_minimum_propensity == pytest.approx(0.10)
    assert evidence.query_urgency_activation_fraction == pytest.approx(0.05)
    assert evidence.query_urgency_power == pytest.approx(0.5)
    assert not list((output / "figures").glob("*.png"))
    report = (output / "reports" / "hard_budget_comparison.md").read_text()
    assert "PaperBanana is unavailable" in report


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
            pprm_block_size=10,
            pprm_labels_per_block=2,
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
    assert (pprm.labels_queried % 2 == 0).all()
    assert (pprm.processed_events % 10 == 0).all()
    assert np.allclose(pprm.labels_queried / pprm.processed_events, 0.20)
    assert (pprm.pprm_block_size == 10).all()
    assert (pprm.pprm_labels_per_block == 2).all()
    assert pprm.pprm_confidence_lower_bound.between(0, 1).all()
    assert pprm.pprm_reliance_mean.between(0, 1).all()
    assert pprm.pprm_reliance_last.between(0, 1).all()
    for weight in ("0p1", "0p25", "0p5", "0p75", "0p9"):
        assert pprm[f"pprm_mix_w{weight}_detected"].notna().all()
        assert pprm[f"pprm_mix_w{weight}_false_escalation"].notna().all()
    assert "probability_positive" not in metrics.columns
    assert "expected_cost_difference" not in metrics.columns
    report = (output / "reports" / "hard_budget_comparison.md").read_text()
    assert "Primary detection all / reached" in report
    assert "pprm_block_adaptive" in report


def test_pprm_uses_current_block_labels_not_the_first_block():
    config = HardBudgetConfig(
        n=1000,
        d=2,
        budget_rate=0.50,
        q_min=0.10,
        q_max=0.80,
        pprm_block_size=20,
        pprm_labels_per_block=4,
        pprm_max_reliance=0.1,
        pprm_initial_reliance=0.0,
        max_label_cost=2.5,
        device="cpu",
    )
    monitor_start = 200
    centered = np.zeros(config.n)
    for block in range((config.n - monitor_start) // config.pprm_block_size):
        left = monitor_start + block * config.pprm_block_size
        right = left + config.pprm_block_size
        centered[left:right] = 0.01 * block
    features = np.zeros((config.n, config.d))
    proxy = DecisionLossProxy(clip=5.1, seed=7).fit(
        features[:100],
        centered[:100],
        features[100:monitor_start],
        centered[100:monitor_start],
    )
    result = _one_pprm_block_method(
        seed=7,
        scenario=SimpleNamespace(name="block_index_test", severity=0.0, fn_cost=5.0, fp_cost=1.0),
        config=config,
        x=features,
        centered_cost_difference=centered,
        expected_cost_difference=centered,
        label_costs=np.ones(config.n),
        proxy_template=proxy,
        monitor_start=monitor_start,
        harm_onset=None,
        sample_path_material_harm=False,
        sample_path_harm_onset=None,
        common_uniforms=np.random.default_rng(11).random(config.n),
    )
    assert result["processed_events"] == config.n - monitor_start
    assert result["stream_mean_estimation_error"] == pytest.approx(0.0, abs=1e-12)
    assert result["stream_mean_estimation_rmse"] == pytest.approx(0.0, abs=1e-12)


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


def test_event_trace_separates_unobserved_labels_and_evaluator_feedback(tmp_path):
    output = run_hard_budget(
        HardBudgetConfig(
            n=1200,
            seeds=1,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            device="cpu",
            scenario_subset=("boundary_local_harm",),
            method_subset=("uniform_proxy",),
            generate_figure=False,
            record_event_traces=True,
        ),
        tmp_path / "event_trace",
    )
    trace = pd.read_parquet(output / "metrics" / "event_traces.parquet")
    assert len(trace) > 0
    assert trace.propensity.between(0.10, 0.80).all()
    assert trace.loc[~trace.queried, "learner_observed_excess_cost"].isna().all()
    assert trace.loc[trace.queried, "learner_observed_excess_cost"].notna().all()
    assert "evaluator_expected_excess_cost" in trace
    assert np.allclose(
        trace.evaluator_expected_excess_cost,
        trace.evaluator_expected_paired_cost_difference - trace.evaluator_harm_margin,
    )
    assert "evaluator_full_feedback_log_e" in trace
    assert "expected_cost_difference" not in trace
    assert not (output / "figures" / "hard_budget_tradeoff.png").exists()


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
