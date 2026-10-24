import pandas as pd

from scripts.analyze_fixed_dollar_horizon_grid import (
    _monitor_rows,
    _paired_detection_contrasts,
    _wilson,
)


def test_wilson_zero_event_interval_is_non_degenerate():
    low, high = _wilson(0, 30)
    assert low == 0
    assert 0 < high < 0.2


def test_monitor_rows_maps_eventwise_and_block_monitors_to_same_seed():
    common = {
        "scenario": "boundary_local_harm",
        "cell": "boundary_late",
        "horizon": 2600,
        "seed": 10,
        "population_null_control": False,
        "material_harm": True,
        "harm_onset_relative": 1600,
        "harm_reached_before_budget_stop": True,
        "processed_events": 2400,
        "labels_queried": 480,
        "realized_label_spend": 700.0,
        "hard_budget": 720.0,
        "mean_expected_decision_harm": 0.2,
        "stream_mean_estimation_rmse": 0.1,
    }
    eventwise = {
        **common,
        "method": "uniform_proxy",
        "single_e_detected": True,
        "single_e_false_escalation": False,
        "single_e_alarm_time": 1700,
        "variance_adaptive_detected": False,
        "variance_adaptive_false_escalation": False,
        "variance_adaptive_alarm_time": None,
        "pm_eb_detected": False,
        "pm_eb_false_escalation": False,
        "pm_eb_alarm_time": None,
    }
    block = {
        **common,
        "method": "pprm_block_adaptive",
        "pprm_mix_w0p1_detected": False,
        "pprm_mix_w0p1_false_escalation": False,
        "pprm_mix_w0p1_alarm_time": None,
    }
    normalized = _monitor_rows(pd.DataFrame([eventwise, block]))
    assert set(normalized.monitor) == {
        "fixed_mixture",
        "predictable_variance",
        "pm_eb",
        "pprm_mix_w0p1",
    }
    assert normalized.seed.nunique() == 1
    assert normalized.loc[normalized.monitor.eq("fixed_mixture"), "delay"].item() == 100


def test_paired_detection_contrasts_use_seed_pairing_and_holm_adjustment():
    rows = []
    for seed, fixed, variance, pm_eb, pprm in (
        (1, True, False, False, False),
        (2, True, True, False, False),
        (3, False, False, False, False),
        (4, False, False, False, False),
    ):
        for monitor, detected in (
            ("fixed_mixture", fixed),
            ("predictable_variance", variance),
            ("pm_eb", pm_eb),
            ("pprm_mix_w0p1", pprm),
        ):
            rows.append(
                {
                    "cell": "boundary_early",
                    "horizon": 1800,
                    "seed": seed,
                    "material_harm": True,
                    "monitor": monitor,
                    "detected": detected,
                }
            )
    contrasts = _paired_detection_contrasts(pd.DataFrame(rows))
    variance = contrasts.loc[contrasts.comparator.eq("predictable_variance")].iloc[0]
    assert variance.fixed_only == 1
    assert variance.comparator_only == 0
    assert variance.rate_difference == 0.25
    assert variance.holm_adjusted_p == 1.0
