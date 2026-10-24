"""Matched comparison of established anytime monitors with a fixed risk proxy."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import ndtr
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression

from ..data.gpu.environment import environment
from ..decision_harm_experiment import (
    POPULATION_NULL_CONTROLS,
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from .eprocess import (
    BoundedMeanEProcess,
    MultiTimescaleStartedKellyEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
    VectorizedStartedMixtureEProcess,
)
from .estimators import prediction_powered_bound, prediction_powered_estimate
from .experiment import _binary_cost, _material_harm_onset, _synthetic_label_costs
from .start_prior_sweep import beta_start_weights

PROCESS_NAMES = ("fixed_mixture", "predictable_kelly", "plug_in_empirical_bernstein")
START_PRIOR_SHAPES = {
    "uniform_start_mixture": (1.0, 1.0),
    "early_start_mixture": (1.0, 2.0),
    "late_start_mixture": (2.0, 1.0),
    "center_start_mixture": (2.0, 2.0),
    "quarter_start_beta_4_12": (4.0, 12.0),
}
NULL_SCENARIOS = ("stationary", "benign_nuisance")
ALTERNATIVE_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
QUERY_RATES = (0.20, 0.40)
FAMILYWISE_NULL_CELLS = len(NULL_SCENARIOS) * len(QUERY_RATES) * len(PROCESS_NAMES)
NULL_FAMILY_ALPHA = 0.05
BOOTSTRAP_REPLICATES = 10_000


@dataclass(frozen=True)
class RiskProxyMonitorGridConfig:
    n: int = 2400
    d: int = 16
    null_seeds: int = 1000
    alternative_seeds: int = 300
    seed_offset: int = 20403024
    alpha: float = 0.05
    harm_margin: float = 0.10
    max_label_cost: float = 2.5
    device: str = "cuda"

    def validate(self) -> RiskProxyMonitorGridConfig:
        if self.n < 1000 or self.d < 2:
            raise ValueError("n must be >= 1000 and d >= 2")
        if self.null_seeds < 2 or self.alternative_seeds < 2:
            raise ValueError("each scenario family requires at least two seeds")
        if not 0 < self.alpha < 1 or self.harm_margin < 0:
            raise ValueError("alpha must be in (0,1) and harm_margin nonnegative")
        if self.max_label_cost <= 0:
            raise ValueError("max_label_cost must be positive")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        return self


def _process(name: str, bound: float, alpha: float):
    factories: dict[str, Callable[[], object]] = {
        "fixed_mixture": lambda: BoundedMeanEProcess(bound=bound, alpha=alpha),
        "predictable_kelly": lambda: PredictableVarianceAdaptiveEProcess(bound=bound, alpha=alpha),
        "plug_in_empirical_bernstein": lambda: PredictablePlugInEmpiricalBernsteinEProcess(
            bound=bound, alpha=alpha
        ),
    }
    try:
        return factories[name]()
    except KeyError as exc:
        raise ValueError(f"unknown monitor process {name!r}") from exc


@lru_cache(maxsize=1)
def _prepare_stream(scenario, seed: int, config: RiskProxyMonitorGridConfig):
    """Generate one path and fit its frozen proxy once across label-rate arms."""
    experiment_config = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        alpha=config.alpha,
        eprocess_epsilon=config.harm_margin,
        seed_offset=seed,
        device=config.device,
    )
    _, frame, oracle, timing = _generate(scenario, seed, experiment_config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    p_truth = oracle.probability_positive.to_numpy(dtype=float)
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    paired = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered = paired - config.harm_margin
    contrast_zero = (
        _binary_cost(deployed, np.zeros_like(y), fn, fp)
        - _binary_cost(reference, np.zeros_like(y), fn, fp)
        - config.harm_margin
    )
    contrast_one = (
        _binary_cost(deployed, np.ones_like(y), fn, fp)
        - _binary_cost(reference, np.ones_like(y), fn, fp)
        - config.harm_margin
    )
    expected = np.where(deployed == 1, fp * (1 - p_truth), fn * p_truth) - np.where(
        reference == 1, fp * (1 - p_truth), fn * p_truth
    )
    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    clip = float(max(fn, fp) + config.harm_margin)
    train_y = y[:train_end]
    if np.unique(train_y).size == 2:
        predictor = LogisticRegression(max_iter=500, random_state=seed).fit(x[:train_end], train_y)
        probabilities = predictor.predict_proba(x[monitor_start:])[:, 1]
    else:
        probabilities = np.full(config.n - monitor_start, float(np.mean(train_y)))
    h = (1 - probabilities) * contrast_zero[monitor_start:] + probabilities * contrast_one[
        monitor_start:
    ]
    h = np.clip(h, -clip, clip)
    harm_onset = statistical_harm_onset(
        scenario.name,
        _material_harm_onset(
            expected,
            config.harm_margin,
            change_times=timing["change_times"],
            monitor_start=monitor_start,
        ),
    )
    costs = _synthetic_label_costs(x)
    return (
        scenario,
        seed,
        experiment_config,
        centered,
        expected,
        h,
        costs,
        monitor_start,
        train_end,
        harm_onset,
        clip,
    )


def _run_stream(
    scenario,
    seed: int,
    query_rate: float,
    config: RiskProxyMonitorGridConfig,
    methods: tuple[str, ...] = PROCESS_NAMES,
):
    (
        scenario,
        seed,
        experiment_config,
        centered,
        expected,
        h,
        costs,
        monitor_start,
        train_end,
        harm_onset,
        clip,
    ) = _prepare_stream(scenario, seed, config)
    available = config.n - monitor_start
    budget = query_rate * float(costs[train_end:monitor_start].mean()) * available
    uniforms = np.random.default_rng(seed + 910_2026).random(available)
    query_mask = np.zeros(available, dtype=bool)
    selected_costs = []
    processed = 0
    remaining = budget
    for offset, index in enumerate(range(monitor_start, config.n)):
        if remaining + 1e-12 < config.max_label_cost:
            break
        processed += 1
        cost = float(costs[index])
        if uniforms[offset] < query_rate:
            if cost > remaining + 1e-12:
                raise RuntimeError("query cost exceeded the pre-event reserve")
            query_mask[offset] = True
            remaining -= cost
        selected_costs.append(cost)

    true_values = centered[monitor_start : monitor_start + processed]
    expected_values = expected[monitor_start : monitor_start + processed]
    proxy_values = h[:processed]
    # Evaluator-only diagnostics: these quantify proxy residual noise without
    # entering the learner's filtration or any monitor update.
    proxy_residual_mse = float(np.mean((true_values - proxy_values) ** 2))
    queries = query_mask[:processed]
    event_costs = np.asarray(selected_costs)
    bound = prediction_powered_bound(clip, query_rate)
    available_horizon = config.n - monitor_start
    start_positions = tuple(round(i * available_horizon / 8) for i in range(8))
    output = []
    for method in methods:
        if method in PROCESS_NAMES:
            process = _process(method, bound, config.alpha)
        elif method in START_PRIOR_SHAPES:
            beta_shape = START_PRIOR_SHAPES[method]
            process = VectorizedStartedMixtureEProcess(
                bound=bound,
                alpha=config.alpha,
                starts=start_positions,
                weights=beta_start_weights(*beta_shape),
            )
        elif method == "discounted_start_mixture":
            process = MultiTimescaleStartedKellyEProcess(
                bound=bound,
                alpha=config.alpha,
                starts=start_positions,
            )
        else:
            raise ValueError(f"unknown monitor method {method!r}")
        remaining = budget
        spend = 0.0
        labels = 0
        alarm_time = None
        labels_at_alarm = None
        estimates, truths = [], []
        for offset, (truth, proxy, queried, cost) in enumerate(
            zip(true_values, proxy_values, queries, event_costs, strict=True)
        ):
            observed = float(truth) if queried else None
            estimate = prediction_powered_estimate(proxy, bool(queried), observed, query_rate)
            log_e = process.update(estimate)
            estimates.append(estimate)
            truths.append(float(truth))
            if queried:
                labels += 1
                spend += float(cost)
                remaining -= float(cost)
            if alarm_time is None and log_e >= -np.log(config.alpha):
                alarm_time = offset
                labels_at_alarm = labels
        detected = alarm_time is not None and harm_onset is not None and alarm_time >= harm_onset
        false_alarm = alarm_time is not None and (harm_onset is None or alarm_time < harm_onset)
        error = np.asarray(estimates) - np.asarray(truths)
        output.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "query_rate": query_rate,
                "method": method,
                "is_population_null": scenario.name in POPULATION_NULL_CONTROLS,
                "material_harm": harm_onset is not None,
                "harm_onset_relative": harm_onset,
                "detected": bool(detected),
                "false_alarm": bool(false_alarm),
                "alarm_time": alarm_time,
                "detection_delay": alarm_time - harm_onset if detected else None,
                "labels_at_alarm": labels_at_alarm,
                "labels_queried": labels,
                "events_processed": processed,
                "hard_budget": budget,
                "realized_label_spend": spend,
                "budget_respected": spend <= budget + 1e-9,
                "estimator_rmse": float(np.sqrt(np.mean(error**2))),
                "centered_paired_cost_variance": float(np.var(true_values)),
                "offline_proxy_residual_mse": proxy_residual_mse,
                "offline_ppi_variance_approx": float(
                    (1 - query_rate) / query_rate * proxy_residual_mse
                ),
                "offline_mean_margin_excess": float(np.mean(expected_values) - config.harm_margin),
                "expected_excess_cost_mean": float(np.mean(expected_values)),
                "cumulative_expected_excess_cost": float(np.sum(expected_values)),
                "eprocess_bound": bound,
                "proxy_type": "frozen_train_only_logistic_decision_risk",
                "generator_device": experiment_config.device,
            }
        )
    if (
        len(
            {
                (row["labels_queried"], row["events_processed"], row["realized_label_spend"])
                for row in output
            }
        )
        != 1
    ):
        raise RuntimeError("monitor processes did not share query and cost paths")
    if not all(row["budget_respected"] for row in output):
        raise RuntimeError("a monitor exceeded the common hard label-cost cap")
    return output


def _summarize(metrics: pd.DataFrame, null_seed_count: int):
    summary = (
        metrics.groupby(["scenario", "query_rate", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            material_harm_streams=("material_harm", "sum"),
            detections=("detected", "sum"),
            false_alarms=("false_alarm", "sum"),
            false_alarm_rate=("false_alarm", "mean"),
            mean_delay_when_detected=("detection_delay", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_events_processed=("events_processed", "mean"),
            mean_rmse=("estimator_rmse", "mean"),
            mean_centered_paired_cost_variance=("centered_paired_cost_variance", "mean"),
            mean_expected_excess_cost=("expected_excess_cost_mean", "mean"),
        )
        .reset_index()
    )
    conditional_detection = (
        metrics[metrics.material_harm]
        .groupby(["scenario", "query_rate", "method"])
        .detected.mean()
        .rename("detection_rate")
        .reset_index()
    )
    summary = summary.merge(
        conditional_detection, on=["scenario", "query_rate", "method"], how="left"
    )
    null_rows = []
    alpha_cell = NULL_FAMILY_ALPHA / FAMILYWISE_NULL_CELLS
    nulls = metrics[metrics.is_population_null]
    for (scenario, query_rate, method), group in nulls.groupby(
        ["scenario", "query_rate", "method"], sort=True
    ):
        count, n = int(group.false_alarm.sum()), len(group)
        upper = 1.0 if count == n else float(beta.ppf(1 - alpha_cell, count + 1, n - count))
        null_rows.append(
            {
                "scenario": scenario,
                "query_rate": query_rate,
                "method": method,
                "false_alarms": count,
                "streams": n,
                "false_alarm_rate": count / n,
                "bonferroni_one_sided_cp95_upper": upper,
                "familywise_alpha": NULL_FAMILY_ALPHA,
                "family_cells": FAMILYWISE_NULL_CELLS,
                "target_level": 0.05,
                "calibration_pass": upper <= 0.05,
                "known_null_seed_count": null_seed_count,
            }
        )
    return summary, pd.DataFrame(null_rows)


def _paired_power_contrasts(metrics: pd.DataFrame) -> pd.DataFrame:
    alternatives = metrics[metrics.material_harm]
    rows = []
    contrasts = (
        (PROCESS_NAMES[0], PROCESS_NAMES[1]),
        (PROCESS_NAMES[0], PROCESS_NAMES[2]),
        (PROCESS_NAMES[1], PROCESS_NAMES[2]),
    )
    for (scenario, query_rate), group in alternatives.groupby(
        ["scenario", "query_rate"], sort=True
    ):
        wide = group.pivot(index="seed", columns="method", values="detected")
        for first, second in contrasts:
            paired = wide[[first, second]].dropna()
            difference = paired[first].astype(float) - paired[second].astype(float)
            values = difference.to_numpy()
            rng = np.random.default_rng(20403024 + len(rows))
            indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
            ci = np.quantile(values[indices].mean(axis=1), [0.025, 0.975])
            rows.append(
                {
                    "scenario": scenario,
                    "query_rate": query_rate,
                    "first_method": first,
                    "second_method": second,
                    "first_detection_rate": float(paired[first].mean()),
                    "second_detection_rate": float(paired[second].mean()),
                    "paired_detection_difference": float(values.mean()),
                    "seed_cluster_ci95_low": float(ci[0]),
                    "seed_cluster_ci95_high": float(ci[1]),
                    "first_only": int((paired[first] & ~paired[second]).sum()),
                    "second_only": int((~paired[first] & paired[second]).sum()),
                    "seed_clusters": len(values),
                    "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                }
            )
    return pd.DataFrame(rows)


def run_risk_proxy_monitor_grid(
    output_dir: str | Path, config: RiskProxyMonitorGridConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    config.validate()
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    rows = []
    seed_ranges = {}
    for scenario_name in NULL_SCENARIOS + ALTERNATIVE_SCENARIOS:
        count = config.null_seeds if scenario_name in NULL_SCENARIOS else config.alternative_seeds
        seed_start = config.seed_offset + (
            0 if scenario_name in NULL_SCENARIOS else config.null_seeds
        )
        seeds = range(seed_start, seed_start + count)
        seed_ranges[scenario_name] = [seed_start, seed_start + count - 1]
        scenario = scenarios[scenario_name]
        for query_rate in QUERY_RATES:
            for seed in seeds:
                rows.extend(_run_stream(scenario, seed, query_rate, config))
    metrics = pd.DataFrame(rows)
    summary, null_calibration = _summarize(metrics, config.null_seeds)
    paired_power = _paired_power_contrasts(metrics)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "scenario_summary.csv", index=False)
    null_calibration.to_csv(output / "null_calibration.csv", index=False)
    paired_power.to_csv(output / "paired_power_contrasts.csv", index=False)
    module_path = Path(__file__)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "processes": list(PROCESS_NAMES),
        "null_scenarios": list(NULL_SCENARIOS),
        "alternative_scenarios": list(ALTERNATIVE_SCENARIOS),
        "query_rates": list(QUERY_RATES),
        "seed_ranges": seed_ranges,
        "metric_rows": len(metrics),
        "null_calibration_cells": FAMILYWISE_NULL_CELLS,
        "null_familywise_alpha": NULL_FAMILY_ALPHA,
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            "risk_proxy_monitor_grid.py": hashlib.sha256(module_path.read_bytes()).hexdigest(),
            "eprocess.py": hashlib.sha256(
                module_path.with_name("eprocess.py").read_bytes()
            ).hexdigest(),
            "proxy_hedge_benchmark.py": hashlib.sha256(
                module_path.with_name("proxy_hedge_benchmark.py").read_bytes()
            ).hexdigest(),
            "decision_harm_experiment.py": hashlib.sha256(
                (module_path.parent.parent / "decision_harm_experiment.py").read_bytes()
            ).hexdigest(),
        },
        "environment": environment(),
        "interpretation": "Matched monitor comparison; finite null calibration is simulation evidence only. The conditional-mean supermartingale proof and outcome-independent query mechanism remain required.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Risk-proxy monitor comparison",
        "",
        f"The CUDA design evaluated {len(metrics):,} process-stream rows across {len(NULL_SCENARIOS)} null scenarios and {len(ALTERNATIVE_SCENARIOS)} harm scenarios at query rates {QUERY_RATES}.",
        "",
        "## Scenario results",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null calibration",
        "",
        null_calibration.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired alternative power contrasts",
        "",
        paired_power.to_markdown(index=False, floatfmt=".4f"),
        "",
        "These finite Monte Carlo intervals are diagnostics, not substitutes for the e-process validity proof. The PM-EB and plug-in Kelly processes require the eventwise history-conditional null, predictable support bound, and current-outcome-independent query randomization. The synthetic nulls are stationary or benign feature-shift controls; the two costs are observed on the same simulated outcome.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return metrics, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/risk_proxy_monitor_grid")
    parser.add_argument("--null-seeds", type=int, default=1000)
    parser.add_argument("--alternative-seeds", type=int, default=300)
    parser.add_argument("--seed-offset", type=int, default=20403024)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = RiskProxyMonitorGridConfig(
        n=args.n,
        null_seeds=args.null_seeds,
        alternative_seeds=args.alternative_seeds,
        seed_offset=args.seed_offset,
        device=args.device,
    )
    _metrics, summary, manifest = run_risk_proxy_monitor_grid(args.output_dir, config)
    print(summary.to_string(index=False))
    print(f"null_calibration_cells={manifest['null_calibration_cells']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
