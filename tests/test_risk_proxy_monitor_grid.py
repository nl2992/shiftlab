import numpy as np
import pandas as pd

from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.eprocess import (
    BoundedMeanEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
)
from shiftlab.dive.risk_proxy_monitor_grid import (
    PROCESS_NAMES,
    RiskProxyMonitorGridConfig,
    _paired_power_contrasts,
    _process,
    _run_stream,
    _summarize,
)


def test_monitor_grid_cpu_smoke_has_matched_paths_and_valid_processes():
    config = RiskProxyMonitorGridConfig(
        n=1200,
        d=4,
        null_seeds=2,
        alternative_seeds=2,
        seed_offset=20403024,
        device="cpu",
    ).validate()
    scenario = next(item for item in SCENARIOS if item.name == "stationary")
    methods = (
        *PROCESS_NAMES,
        "uniform_start_mixture",
        "early_start_mixture",
        "late_start_mixture",
        "center_start_mixture",
        "quarter_start_beta_4_12",
    )
    rows = _run_stream(scenario, config.seed_offset, 0.4, config, methods=methods)
    assert {row["method"] for row in rows} == set(methods)
    assert len({row["labels_queried"] for row in rows}) == 1
    assert len({row["events_processed"] for row in rows}) == 1
    assert len({row["realized_label_spend"] for row in rows}) == 1
    assert all(row["budget_respected"] for row in rows)
    assert all(row["is_population_null"] for row in rows)
    assert not any(row["material_harm"] for row in rows)
    assert all(row["offline_proxy_residual_mse"] >= 0 for row in rows)
    assert all(row["offline_ppi_variance_approx"] >= 0 for row in rows)
    assert all(np.isfinite(row["offline_mean_margin_excess"]) for row in rows)


def test_monitor_factory_returns_registered_anytime_processes():
    assert isinstance(_process("fixed_mixture", 3.0, 0.05), BoundedMeanEProcess)
    assert isinstance(_process("predictable_kelly", 3.0, 0.05), PredictableVarianceAdaptiveEProcess)
    assert isinstance(
        _process("plug_in_empirical_bernstein", 3.0, 0.05),
        PredictablePlugInEmpiricalBernsteinEProcess,
    )


def test_null_calibration_uses_familywise_one_sided_exact_bound():
    records = []
    for method in PROCESS_NAMES:
        for seed in range(1000):
            records.append(
                {
                    "scenario": "stationary",
                    "query_rate": 0.2,
                    "method": method,
                    "seed": seed,
                    "is_population_null": True,
                    "material_harm": False,
                    "detected": False,
                    "false_alarm": False,
                    "detection_delay": np.nan,
                    "labels_queried": 10,
                    "realized_label_spend": 20.0,
                    "events_processed": 100,
                    "estimator_rmse": 1.0,
                    "centered_paired_cost_variance": 1.0,
                    "expected_excess_cost_mean": -0.1,
                }
            )
    _summary, calibration = _summarize(pd.DataFrame(records), 1000)
    assert len(calibration) == 3
    assert calibration.bonferroni_one_sided_cp95_upper.max() < 0.05
    assert calibration.calibration_pass.all()


def test_paired_power_contrasts_preserve_stream_matching():
    import pandas as pd

    rows = []
    outcomes = {
        "fixed_mixture": [True, False, True],
        "predictable_kelly": [False, False, True],
        "plug_in_empirical_bernstein": [True, True, False],
    }
    for method, values in outcomes.items():
        for seed, detected in enumerate(values):
            rows.append(
                {
                    "scenario": "boundary_local_harm",
                    "query_rate": 0.4,
                    "method": method,
                    "seed": seed,
                    "material_harm": True,
                    "detected": detected,
                }
            )
    contrasts = _paired_power_contrasts(pd.DataFrame(rows))
    assert len(contrasts) == 3
    baseline = contrasts[contrasts.second_method == "predictable_kelly"].iloc[0]
    assert baseline.first_only == 1
    assert baseline.second_only == 0
