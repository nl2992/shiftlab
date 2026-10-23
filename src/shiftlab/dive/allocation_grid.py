"""Nested, forward-time grid search for budgeted prediction-powered sampling."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import ndtr
from scipy.stats import norm
from scipy.stats import t as student_t

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import (
    POPULATION_NULL_CONTROLS,
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from .eprocess import BoundedMeanEProcess
from .estimators import prediction_powered_bound, prediction_powered_estimate
from .evaluation import apply_population_null_classification
from .experiment import (
    _binary_cost,
    _material_harm_onset,
    finalize_manifest,
)
from .proxy import DecisionLossProxy
from .query import AdaptiveQueryPolicy, expected_rate_drift_bound, mix_with_uniform


@dataclass(frozen=True)
class AllocationGridConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 30
    seed_offset: int = 20361022
    alpha: float = 0.05
    harm_margin: float = 0.10
    label_budgets: tuple[float, ...] = (0.05, 0.10, 0.20)
    variance_powers: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
    rate_drift_tolerances: tuple[float, ...] = (0.0, 0.01, 0.025, 0.05, 0.10)
    label_cost: float = 0.01
    device: str = "auto"

    def validate(self) -> AllocationGridConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if not 0 < self.alpha < 1 or self.harm_margin < 0 or self.label_cost < 0:
            raise ValueError("alpha, harm_margin, and label_cost are invalid")
        if not self.label_budgets or any(not 0 < rate < 1 for rate in self.label_budgets):
            raise ValueError("label_budgets must be nonempty rates in (0, 1)")
        if not self.variance_powers or any(not 0 <= power <= 1 for power in self.variance_powers):
            raise ValueError("variance_powers must be nonempty values in [0, 1]")
        if len(set(self.label_budgets)) != len(self.label_budgets):
            raise ValueError("label_budgets must be unique")
        if len(set(self.variance_powers)) != len(self.variance_powers):
            raise ValueError("variance_powers must be unique")
        if not self.rate_drift_tolerances or any(
            not 0 <= delta <= 1 for delta in self.rate_drift_tolerances
        ):
            raise ValueError("rate_drift_tolerances must be nonempty values in [0, 1]")
        if len(set(self.rate_drift_tolerances)) != len(self.rate_drift_tolerances):
            raise ValueError("rate_drift_tolerances must be unique")
        return self


def _fit_allocation(
    power: float,
    rate: float,
    q_min: float,
    q_max: float,
    proxy: np.ndarray,
    residual_second_moment: np.ndarray,
) -> AdaptiveQueryPolicy:
    policy = AdaptiveQueryPolicy(
        "variance",
        target_rate=rate,
        q_min=q_min,
        q_max=q_max,
        variance_power=power,
    )
    policy.fit_multiplier(
        proxy=proxy,
        residual_second_moment=residual_second_moment,
        uncertainty=np.zeros_like(proxy),
    )
    return policy


def _one_stream(
    scenario,
    seed: int,
    config: AllocationGridConfig,
    *,
    include_power_grid: bool = True,
) -> list[dict]:
    powers = config.variance_powers if include_power_grid else (0.5,)
    base = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        window=64,
        stride=32,
        alpha=config.alpha,
        eprocess_epsilon=config.harm_margin,
        seed_offset=seed,
        device=config.device,
    )
    _, frame, oracle, timing = _generate(scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    fn, fp = scenario.fn_cost, scenario.fp_cost
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    observed_cost_difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(
        reference, y, fn, fp
    )
    centered_difference = observed_cost_difference - config.harm_margin
    p = oracle.probability_positive.to_numpy(dtype=float)
    current_expected = np.where(deployed == 1, fp * (1 - p), fn * p)
    reference_expected = np.where(reference == 1, fp * (1 - p), fn * p)
    expected_difference = current_expected - reference_expected

    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    validation_end = monitor_start
    if train_end >= validation_end - 50:
        raise ValueError("n is too small for disjoint training, validation, and monitor data")
    cost_bound = max(fn, fp) + config.harm_margin
    proxy = DecisionLossProxy(clip=cost_bound, seed=seed)
    proxy.fit(
        x[:train_end],
        centered_difference[:train_end],
        x[train_end:validation_end],
        centered_difference[train_end:validation_end],
    )
    validation_x = x[train_end:validation_end]
    validation_proxy = proxy.predict(validation_x)
    validation_v = proxy.predict_residual_second_moment(validation_x)
    validation_residual = centered_difference[train_end:validation_end] - validation_proxy
    selected: dict[float, tuple[float, float]] = {}
    policies: dict[tuple[float, float], AdaptiveQueryPolicy] = {}
    propensities: dict[tuple[float, float], np.ndarray] = {}
    q_min_by_rate: dict[float, float] = {}
    monitor_x = x[monitor_start:]
    monitor_proxy = proxy.predict(monitor_x)
    monitor_v = proxy.predict_residual_second_moment(monitor_x)
    n_monitor = len(monitor_x)

    for rate in config.label_budgets:
        q_min = rate / 4
        q_max = min(1.0, rate * 5)
        q_min_by_rate[rate] = q_min
        validation_objectives = []
        for power in powers:
            policy = _fit_allocation(power, rate, q_min, q_max, validation_proxy, validation_v)
            q_validation = policy.probabilities(
                proxy=validation_proxy,
                residual_second_moment=validation_v,
                uncertainty=np.zeros_like(validation_proxy),
            )
            # Conditional query-randomization variance on the fully labeled calibration slice.
            objective = float(np.mean(validation_residual**2 * (1 / q_validation - 1)))
            validation_objectives.append((objective, power))
            policies[(rate, power)] = policy
            propensities[(rate, power)] = policy.probabilities(
                proxy=monitor_proxy,
                residual_second_moment=monitor_v,
                uncertainty=np.zeros_like(monitor_proxy),
            )
        best_objective, best_power = min(validation_objectives, key=lambda item: (item[0], item[1]))
        selected[rate] = (best_power, best_objective)

    sample_path_onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    onset = statistical_harm_onset(scenario.name, sample_path_onset)
    rng = np.random.default_rng(seed + 112_733)
    common_uniforms = {rate: rng.random(n_monitor) for rate in config.label_budgets}
    rows: list[dict] = []
    for rate in config.label_budgets:
        best_power, best_objective = selected[rate]
        q_min = q_min_by_rate[rate]
        for power in powers:
            q = propensities[(rate, power)]
            queried = common_uniforms[rate] < q
            estimates = np.fromiter(
                (
                    prediction_powered_estimate(
                        float(h), bool(i), float(z) if i else None, float(propensity)
                    )
                    for h, i, z, propensity in zip(
                        monitor_proxy,
                        queried,
                        centered_difference[monitor_start:],
                        q,
                        strict=True,
                    )
                ),
                dtype=float,
                count=n_monitor,
            )
            eprocess = BoundedMeanEProcess(
                bound=prediction_powered_bound(cost_bound, q_min), alpha=config.alpha
            )
            first_alarm = None
            for event_index, estimate in enumerate(estimates):
                if eprocess.update(float(estimate)) >= -np.log(config.alpha):
                    first_alarm = event_index
                    break
            detected = first_alarm is not None and onset is not None and first_alarm >= onset
            false_alarm = first_alarm is not None and (onset is None or first_alarm < onset)
            n_labels = int(queried.sum())
            truth = centered_difference[monitor_start:]
            residual = estimates - truth
            rows.append(
                {
                    "scenario": scenario.name,
                    "seed": seed,
                    "budget_rate": rate,
                    "variance_power": power,
                    "allocation": (
                        "uniform_ppi"
                        if power == 0
                        else ("neyman_ppi" if power == 0.5 else "power_ppi")
                    ),
                    "is_validation_selected": power == best_power,
                    "selected_power": best_power,
                    "selected_validation_variance": best_objective,
                    "validation_objective": float(
                        np.mean(
                            validation_residual**2
                            * (
                                1
                                / policies[(rate, power)].probabilities(
                                    proxy=validation_proxy,
                                    residual_second_moment=validation_v,
                                    uncertainty=np.zeros_like(validation_proxy),
                                )
                                - 1
                            )
                        )
                    ),
                    "expected_query_rate_validation": rate,
                    "realized_query_rate_monitor": n_labels / n_monitor,
                    "labels_queried": n_labels,
                    "propensity_min": float(q.min()),
                    "propensity_max": float(q.max()),
                    "mean_estimation_error": float(estimates.mean() - truth.mean()),
                    "estimation_rmse": float(np.sqrt(np.mean(residual**2))),
                    "single_e_false_escalation": bool(false_alarm),
                    "single_e_detected": bool(detected),
                    "single_e_alarm_time": first_alarm,
                    "single_e_delay": (
                        float(first_alarm - onset)
                        if detected and first_alarm is not None and onset is not None
                        else np.nan
                    ),
                    "harm_onset_relative": onset,
                    "material_harm": onset is not None,
                    "population_null_control": scenario.name in POPULATION_NULL_CONTROLS,
                    "sample_path_material_harm": sample_path_onset is not None,
                    "sample_path_harm_onset_relative": sample_path_onset,
                    "mean_expected_decision_harm": float(
                        expected_difference[monitor_start:].mean()
                    ),
                    "label_adjusted_excess_cost": float(
                        expected_difference[monitor_start:].sum() + config.label_cost * n_labels
                    ),
                }
            )
    if not include_power_grid:
        for rate in config.label_budgets:
            q_min = rate / 4
            q_max = min(1.0, rate * 5)
            base_q_validation = policies[(rate, 0.5)].probabilities(
                proxy=validation_proxy,
                residual_second_moment=validation_v,
                uncertainty=np.zeros_like(validation_proxy),
            )
            base_q_monitor = propensities[(rate, 0.5)]
            drift_range = max(rate - q_min, q_max - rate)
            validation_candidates = []
            for tolerance in config.rate_drift_tolerances:
                rho = min(1.0, tolerance / drift_range) if drift_range > 0 else 0.0
                q_validation = mix_with_uniform(
                    base_q_validation, target_rate=rate, mixture_weight=rho
                )
                objective = float(np.mean(validation_residual**2 * (1 / q_validation - 1)))
                validation_candidates.append((objective, tolerance, rho))
            best_objective, best_tolerance, _ = min(
                validation_candidates, key=lambda item: (item[0], item[1])
            )
            for objective, tolerance, rho in validation_candidates:
                q = mix_with_uniform(base_q_monitor, target_rate=rate, mixture_weight=rho)
                queried = common_uniforms[rate] < q
                estimates = np.fromiter(
                    (
                        prediction_powered_estimate(
                            float(h), bool(i), float(z) if i else None, float(propensity)
                        )
                        for h, i, z, propensity in zip(
                            monitor_proxy,
                            queried,
                            centered_difference[monitor_start:],
                            q,
                            strict=True,
                        )
                    ),
                    dtype=float,
                    count=n_monitor,
                )
                robust_q_min = (1 - rho) * rate + rho * q_min
                eprocess = BoundedMeanEProcess(
                    bound=prediction_powered_bound(cost_bound, robust_q_min),
                    alpha=config.alpha,
                )
                first_alarm = None
                for event_index, estimate in enumerate(estimates):
                    if eprocess.update(float(estimate)) >= -np.log(config.alpha):
                        first_alarm = event_index
                        break
                detected = first_alarm is not None and onset is not None and first_alarm >= onset
                false_alarm = first_alarm is not None and (onset is None or first_alarm < onset)
                n_labels = int(queried.sum())
                truth = centered_difference[monitor_start:]
                rows.append(
                    {
                        "scenario": scenario.name,
                        "seed": seed,
                        "budget_rate": rate,
                        "variance_power": 0.5,
                        "allocation": "rate_stabilized_neyman",
                        "is_validation_selected": tolerance == best_tolerance,
                        "selected_power": 0.5,
                        "selected_validation_variance": best_objective,
                        "validation_objective": objective,
                        "expected_query_rate_validation": rate,
                        "realized_query_rate_monitor": n_labels / n_monitor,
                        "labels_queried": n_labels,
                        "propensity_min": float(q.min()),
                        "propensity_max": float(q.max()),
                        "mean_estimation_error": float(estimates.mean() - truth.mean()),
                        "estimation_rmse": float(np.sqrt(np.mean((estimates - truth) ** 2))),
                        "single_e_false_escalation": bool(false_alarm),
                        "single_e_detected": bool(detected),
                        "single_e_alarm_time": first_alarm,
                        "single_e_delay": (
                            float(first_alarm - onset)
                            if detected and first_alarm is not None and onset is not None
                            else np.nan
                        ),
                        "harm_onset_relative": onset,
                        "material_harm": onset is not None,
                        "population_null_control": scenario.name in POPULATION_NULL_CONTROLS,
                        "sample_path_material_harm": sample_path_onset is not None,
                        "sample_path_harm_onset_relative": sample_path_onset,
                        "mean_expected_decision_harm": float(
                            expected_difference[monitor_start:].mean()
                        ),
                        "label_adjusted_excess_cost": float(
                            expected_difference[monitor_start:].sum() + config.label_cost * n_labels
                        ),
                        "rate_drift_tolerance": tolerance,
                        "uniform_mixture_weight": rho,
                        "worst_case_expected_rate_drift_bound": expected_rate_drift_bound(
                            target_rate=rate,
                            mixture_weight=rho,
                            q_min=q_min,
                            q_max=q_max,
                        ),
                        "selected_rate_drift_tolerance": best_tolerance,
                    }
                )
    return rows


def _plot_allocation_summary(
    summary: pd.DataFrame, config: AllocationGridConfig, figure_path: Path
) -> None:
    scenario_order = [scenario.name for scenario in SCENARIOS]
    columns = [(rate, power) for rate in config.label_budgets for power in config.variance_powers]
    detection = np.full((len(scenario_order), len(columns)), np.nan)
    rmse = np.full_like(detection, np.nan)
    for row_index, scenario_name in enumerate(scenario_order):
        for column_index, (rate, power) in enumerate(columns):
            match = summary[
                (summary.scenario == scenario_name)
                & (summary.budget_rate == rate)
                & (summary.variance_power == power)
            ]
            if len(match):
                detection[row_index, column_index] = match.detection_rate.iloc[0]
                rmse[row_index, column_index] = match.estimation_rmse.iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    detection_image = axes[0].imshow(detection, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    rmse_image = axes[1].imshow(rmse, aspect="auto", cmap="magma")
    labels = [f"{rate:.0%} / {power:g}" for rate, power in columns]
    for axis in axes:
        axis.set_xticks(np.arange(len(columns)), labels, fontsize=7)
        axis.set_yticks(np.arange(len(scenario_order)), scenario_order)
        axis.tick_params(axis="x", labelrotation=45)
        for label in axis.get_xticklabels():
            label.set_horizontalalignment("right")
        axis.set_xlabel("Expected label budget / variance-score power")
    axes[0].set_title("Detection on material-harm streams")
    axes[0].set_ylabel("Synthetic scenario")
    axes[1].set_title("Mean forward-test stream RMSE")
    fig.colorbar(detection_image, ax=axes[0], label="Detection rate")
    fig.colorbar(rmse_image, ax=axes[1], label="RMSE")
    fig.suptitle("Validation-selected sampling allocation; untouched forward monitoring period")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)


def _plot_rate_stabilized_summary(
    summary: pd.DataFrame, config: AllocationGridConfig, figure_path: Path
) -> None:
    scenarios = [scenario.name for scenario in SCENARIOS]
    columns = [
        (rate, tolerance)
        for rate in config.label_budgets
        for tolerance in config.rate_drift_tolerances
    ]
    detection = np.full((len(scenarios), len(columns)), np.nan)
    drift = np.full_like(detection, np.nan)
    for i, scenario_name in enumerate(scenarios):
        for j, (rate, tolerance) in enumerate(columns):
            match = summary[
                (summary.scenario == scenario_name)
                & (summary.budget_rate == rate)
                & (summary.rate_drift_tolerance == tolerance)
            ]
            if len(match):
                detection[i, j] = match.detection.iloc[0]
                drift[i, j] = match.mean_absolute_rate_drift.iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    detection_image = axes[0].imshow(detection, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    drift_image = axes[1].imshow(drift, aspect="auto", cmap="magma")
    labels = [f"{rate:.0%} / {delta:g}" for rate, delta in columns]
    for axis in axes:
        axis.set_xticks(np.arange(len(columns)), labels, fontsize=7)
        axis.set_yticks(np.arange(len(scenarios)), scenarios)
        axis.tick_params(axis="x", labelrotation=45)
        for label in axis.get_xticklabels():
            label.set_horizontalalignment("right")
        axis.set_xlabel("Expected label rate / allowed expected-rate drift")
    axes[0].set_title("Detection on material-harm streams")
    axes[0].set_ylabel("Synthetic scenario")
    axes[1].set_title("Absolute realized-rate deviation (includes sampling noise)")
    fig.colorbar(detection_image, ax=axes[0], label="Detection rate")
    fig.colorbar(drift_image, ax=axes[1], label="Mean absolute rate deviation")
    fig.suptitle("Uniform-stabilized Neyman sampling under covariate shift")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)


def run_allocation_grid(config: AllocationGridConfig, output: Path) -> Path:
    config.validate()
    requested_device = config.device
    config = AllocationGridConfig(
        **{
            **asdict(config),
            "device": resolve_device(config.device, n=config.n, d=config.d, chunk_size=2048),
        }
    )
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for folder in (metrics_dir, reports_dir, figures_dir):
        folder.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "allocation_grid.parquet"
    if metrics_path.exists():
        raise FileExistsError(f"refusing to overwrite existing allocation grid: {metrics_path}")
    rows = []
    for scenario in SCENARIOS:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            print(
                f"allocation scenario={scenario.name} replicate={replicate + 1}/{config.seeds} device={config.device}",
                flush=True,
            )
            rows.extend(_one_stream(scenario, seed, config))
    metrics = pd.DataFrame(rows)
    metrics = apply_population_null_classification(metrics)
    metrics.to_parquet(metrics_path, index=False)
    summary_rows = []
    for (scenario_name, rate, power), group in metrics.groupby(
        ["scenario", "budget_rate", "variance_power"], sort=True
    ):
        harmful = group[group.material_harm]
        summary_rows.append(
            {
                "scenario": scenario_name,
                "budget_rate": rate,
                "variance_power": power,
                "selected_rate": float(group.is_validation_selected.mean()),
                "validation_variance": float(group.validation_objective.mean()),
                "labels": float(group.labels_queried.mean()),
                "estimation_rmse": float(group.estimation_rmse.mean()),
                "detection_rate": float(harmful.single_e_detected.mean())
                if len(harmful)
                else np.nan,
                "false_escalation_rate": float(group.single_e_false_escalation.mean()),
            }
        )
    summary = pd.DataFrame(summary_rows)

    def wilson_interval(successes: int, n: int) -> tuple[float, float]:
        if n == 0:
            return float("nan"), float("nan")
        z = float(norm.ppf(0.975))
        rate = successes / n
        denominator = 1 + z**2 / n
        center = (rate + z**2 / (2 * n)) / denominator
        radius = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
        return max(0.0, center - radius), min(1.0, center + radius)

    def mean_interval(values: np.ndarray) -> tuple[float, float]:
        values = np.asarray(values, dtype=float)
        if len(values) < 2:
            return float("nan"), float("nan")
        half = float(student_t.ppf(0.975, len(values) - 1)) * float(
            values.std(ddof=1) / np.sqrt(len(values))
        )
        return float(values.mean() - half), float(values.mean() + half)

    report = [
        "# Nested allocation grid search",
        "",
        f"{config.seeds} independent seeds were evaluated in each of {len(SCENARIOS)} scenarios on `{config.device}`. On each stream, the residual-variance score power was selected using only fully labeled pre-monitor validation residuals; the monitor period is an untouched forward test. Every grid point is also reported, with `is_validation_selected` marking the validation-selected member. Query budgets are expected calibration rates, not hard realized label caps.",
        "",
        "For an unbiased prediction-powered estimator `h(X)+I/q(X)(H-h(X))`, the conditional query-randomization variance is `(1/q(X)-1) v(X)`, where `v(X)=E[(H-h(X))^2|X]`. Under a fixed expected label budget and no propensity bounds, minimizing the integrated variance gives `q(X) proportional to sqrt(v(X))`; with lower and upper bounds, the solution is clipped at those bounds. Thus power 0.5 is the classical Neyman allocation baseline. Other powers are tuning candidates, not novel theory. The grid chooses the power minimizing the empirical validation estimate of this variance and measures its out-of-time performance without using monitor outcomes for selection.",
        "",
        "This is a finite hyperparameter search over budget fractions 0.05, 0.10, 0.20 and residual-second-moment powers 0, 0.25, 0.5, 0.75, 1.0. The propensity floors and caps are fixed at one quarter and five times the target rate (capped at one). The sequential e-process retains a fixed worst-case bound based on the floor, so low budgets yield conservative tests. No claim of an optimal detector or new Neyman allocation is made.",
        "",
        "| Scenario | Budget | Power | Selected rate | Labels (95% t CI) | Mean stream RMSE (95% t CI) | Detection on material streams (95% Wilson) | False escalation (95% Wilson) | Median detection delay |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        group = metrics[
            (metrics.scenario == row.scenario)
            & (metrics.budget_rate == row.budget_rate)
            & (metrics.variance_power == row.variance_power)
        ]
        harmful = group[group.material_harm]
        detections = int(harmful.single_e_detected.sum())
        detection_low, detection_high = wilson_interval(detections, len(harmful))
        false_count = int(group.single_e_false_escalation.sum())
        false_low, false_high = wilson_interval(false_count, len(group))
        labels_low, labels_high = mean_interval(group.labels_queried.to_numpy())
        rmse_low, rmse_high = mean_interval(group.estimation_rmse.to_numpy())
        delay_values = group.loc[group.single_e_detected, "single_e_delay"]
        delay = "—" if delay_values.empty else f"{delay_values.median():.0f}"
        detection_text = (
            "—"
            if len(harmful) == 0
            else f"{row.detection_rate:.2f} [{detection_low:.2f},{detection_high:.2f}]"
        )
        report.append(
            f"| {row.scenario} | {row.budget_rate:.2f} | {row.variance_power:.2f} | "
            f"{row.selected_rate:.2f} | {row.labels:.1f} [{labels_low:.1f},{labels_high:.1f}] | "
            f"{row.estimation_rmse:.4f} [{rmse_low:.4f},{rmse_high:.4f}] | "
            f"{detection_text} | {row.false_escalation_rate:.2f} "
            f"[{false_low:.2f},{false_high:.2f}] | {delay} |"
        )
    keys = ["scenario", "seed", "budget_rate"]
    selected = metrics[metrics.is_validation_selected].set_index(keys).sort_index()
    neyman = metrics[metrics.variance_power == 0.5].set_index(keys).sort_index()
    common = selected.index.intersection(neyman.index)
    selected = selected.loc[common]
    neyman = neyman.loc[common]
    rmse_difference = selected.estimation_rmse.to_numpy() - neyman.estimation_rmse.to_numpy()
    label_difference = selected.labels_queried.to_numpy() - neyman.labels_queried.to_numpy()
    rmse_low, rmse_high = mean_interval(rmse_difference)
    label_low, label_high = mean_interval(label_difference)
    material = selected.material_harm.to_numpy(dtype=bool)
    selected_detection = float(selected.single_e_detected.to_numpy()[material].mean())
    neyman_detection = float(neyman.single_e_detected.to_numpy()[material].mean())
    selected_power_counts = selected.variance_power.value_counts(normalize=True).sort_index()
    selected_power_text = ", ".join(
        f"{power:g}: {frequency:.3f}" for power, frequency in selected_power_counts.items()
    )
    report.extend(
        [
            "",
            "## Outer-test comparison against fixed Neyman power 0.5",
            "",
            f"The validation search selected power frequencies `{selected_power_text}`. On {len(common)} paired scenario-seed-budget streams, selected minus fixed Neyman had mean stream-RMSE difference {rmse_difference.mean():.4f} [{rmse_low:.4f},{rmse_high:.4f}] and label-count difference {label_difference.mean():.1f} [{label_low:.1f},{label_high:.1f}]. Detection on material-harm streams was {selected_detection:.3f} for the validation-selected configuration versus {neyman_detection:.3f} for fixed Neyman. Hyperparameters were selected before monitoring; these outer-test metrics do not feed back into selection.",
        ]
    )
    report_path = reports_dir / "allocation_grid.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    figure_path = figures_dir / "allocation_grid.png"
    _plot_allocation_summary(summary, config, figure_path)

    manifest_path = reports_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    )
    manifest["allocation_grid_search"] = {
        "configuration": asdict(config),
        "requested_device": requested_device,
        "environment": environment(),
        "metric_path": str(metrics_path),
        "report_path": str(report_path),
        "figure_path": str(figure_path),
        "selection": "minimize estimated validation query-randomization variance",
        "allocation_theory": "clipped q proportional to sqrt(conditional residual second moment)",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return metrics_path


def run_rate_stabilized_grid(config: AllocationGridConfig, output: Path) -> Path:
    """Test Neyman sampling shrunk toward uniform under a rate-drift constraint."""
    config.validate()
    requested_device = config.device
    config = AllocationGridConfig(
        **{
            **asdict(config),
            "device": resolve_device(config.device, n=config.n, d=config.d, chunk_size=2048),
        }
    )
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir, figures_dir = (
        output / "metrics",
        output / "reports",
        output / "figures",
    )
    for folder in (metrics_dir, reports_dir, figures_dir):
        folder.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "rate_stabilized_grid.parquet"
    if metrics_path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing rate-stabilized grid: {metrics_path}"
        )
    rows: list[dict] = []
    for scenario in SCENARIOS:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            print(
                f"robust allocation scenario={scenario.name} replicate={replicate + 1}/{config.seeds} device={config.device}",
                flush=True,
            )
            rows.extend(
                row
                for row in _one_stream(scenario, seed, config, include_power_grid=False)
                if row["allocation"] == "rate_stabilized_neyman"
            )
    metrics = pd.DataFrame(rows)
    metrics = apply_population_null_classification(metrics)
    metrics.to_parquet(metrics_path, index=False)

    def wilson(successes: int, n: int) -> tuple[float, float]:
        if n == 0:
            return float("nan"), float("nan")
        z = float(norm.ppf(0.975))
        rate = successes / n
        denominator = 1 + z**2 / n
        center = (rate + z**2 / (2 * n)) / denominator
        radius = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
        return max(0.0, center - radius), min(1.0, center + radius)

    def t_interval(values: np.ndarray) -> tuple[float, float]:
        values = np.asarray(values, dtype=float)
        if len(values) < 2:
            return float("nan"), float("nan")
        half = float(student_t.ppf(0.975, len(values) - 1)) * float(
            values.std(ddof=1) / np.sqrt(len(values))
        )
        return float(values.mean() - half), float(values.mean() + half)

    summary_rows = []
    for (scenario_name, rate, tolerance), group in metrics.groupby(
        ["scenario", "budget_rate", "rate_drift_tolerance"], sort=True
    ):
        harmful = group[group.material_harm]
        summary_rows.append(
            {
                "scenario": scenario_name,
                "budget_rate": rate,
                "rate_drift_tolerance": tolerance,
                "selected_rate": float(group.is_validation_selected.mean()),
                "mixture_weight": float(group.uniform_mixture_weight.mean()),
                "bound": float(group.worst_case_expected_rate_drift_bound.mean()),
                "labels": float(group.labels_queried.mean()),
                "mean_absolute_rate_drift": float(
                    np.mean(np.abs(group.realized_query_rate_monitor - rate))
                ),
                "rmse": float(group.estimation_rmse.mean()),
                "detection": float(harmful.single_e_detected.mean()) if len(harmful) else np.nan,
                "false": float(group.single_e_false_escalation.mean()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    report = [
        "# Rate-stabilized Neyman allocation grid",
        "",
        f"Evaluated {config.seeds} independent streams per scenario on `{config.device}`. The base allocation is the validation-calibrated Neyman score `q_N(x) ∝ sqrt(vhat(x))`. Each candidate uses `q_rho(x)=(1-rho)r+rho*q_N(x)`, with `rho=min(1, delta / max(r-q_min, q_max-r))`. Candidates are selected by validation query-variance objective and tested only on the forward monitor period.",
        "",
        "For any deployment feature distribution, `q_N(x)` remains in `[q_min,q_max]`, so `|E_deploy[q_rho(X)]-r| <= rho*max(r-q_min,q_max-r) <= delta`. This gives a worst-case bound on expected query-rate drift under arbitrary covariate shift while preserving predictable positive propensities. It is not a hard realized label cap; actual counts remain random. At `delta=0` the design is uniform; larger `delta` permits more Neyman adaptation and potentially more variance reduction.",
        "",
        "| Scenario | Target rate | Drift tolerance | Selected frequency | Mean mix weight | Proven rate-drift bound | Labels (95% t CI) | Mean absolute realized rate drift | RMSE (95% t CI) | Detection (95% Wilson) | False escalation (95% Wilson) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        group = metrics[
            (metrics.scenario == row.scenario)
            & (metrics.budget_rate == row.budget_rate)
            & (metrics.rate_drift_tolerance == row.rate_drift_tolerance)
        ]
        harmful = group[group.material_harm]
        detected = int(harmful.single_e_detected.sum())
        dlow, dhigh = wilson(detected, len(harmful))
        false = int(group.single_e_false_escalation.sum())
        flow, fhigh = wilson(false, len(group))
        llow, lhigh = t_interval(group.labels_queried.to_numpy())
        rlow, rhigh = t_interval(group.estimation_rmse.to_numpy())
        detection = "—" if len(harmful) == 0 else f"{row.detection:.2f} [{dlow:.2f},{dhigh:.2f}]"
        report.append(
            f"| {row.scenario} | {row.budget_rate:.2f} | {row.rate_drift_tolerance:.3f} | "
            f"{row.selected_rate:.2f} | {row.mixture_weight:.3f} | {row.bound:.3f} | "
            f"{row.labels:.1f} [{llow:.1f},{lhigh:.1f}] | {row.mean_absolute_rate_drift:.3f} | "
            f"{row.rmse:.4f} [{rlow:.4f},{rhigh:.4f}] | {detection} | "
            f"{row.false:.2f} [{flow:.2f},{fhigh:.2f}] |"
        )
    baseline_path = metrics_dir / "allocation_grid.parquet"
    if baseline_path.is_file():
        keys = ["scenario", "seed", "budget_rate"]
        selected = metrics[metrics.is_validation_selected].set_index(keys).sort_index()
        uniform = metrics[metrics.rate_drift_tolerance == 0].set_index(keys).sort_index()
        neyman = pd.read_parquet(baseline_path)
        neyman = neyman[neyman.variance_power == 0.5].set_index(keys).sort_index()
        report.extend(["", "## Paired forward comparison", ""])
        for name, baseline in (("uniform", uniform), ("unmixed Neyman", neyman)):
            common = selected.index.intersection(baseline.index)
            paired_selected = selected.loc[common]
            paired_baseline = baseline.loc[common]
            rmse_difference = (
                paired_selected.estimation_rmse.to_numpy()
                - paired_baseline.estimation_rmse.to_numpy()
            )
            label_difference = (
                paired_selected.labels_queried.to_numpy()
                - paired_baseline.labels_queried.to_numpy()
            )
            rmse_low, rmse_high = t_interval(rmse_difference)
            label_low, label_high = t_interval(label_difference)
            material = paired_selected.material_harm.to_numpy(dtype=bool)
            selected_detection = float(
                paired_selected.single_e_detected.to_numpy()[material].mean()
            )
            baseline_detection = float(
                paired_baseline.single_e_detected.to_numpy()[material].mean()
            )
            report.append(
                f"Selected robust mixture minus {name} across {len(common)} paired scenario-seed-budget streams: "
                f"RMSE difference {rmse_difference.mean():.4f} [{rmse_low:.4f},{rmse_high:.4f}], "
                f"label-count difference {label_difference.mean():.1f} [{label_low:.1f},{label_high:.1f}], "
                f"detection on material streams {selected_detection:.3f} vs {baseline_detection:.3f}."
            )
        report.append(
            "The selected tolerance is chosen from validation residuals only. These paired test comparisons are descriptive and do not tune the tolerance on monitor outcomes."
        )
    report_path = reports_dir / "rate_stabilized_grid.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    figure_path = figures_dir / "rate_stabilized_grid.png"
    _plot_rate_stabilized_summary(summary, config, figure_path)

    manifest_path = reports_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    )
    manifest["rate_stabilized_grid"] = {
        "configuration": asdict(config),
        "requested_device": requested_device,
        "environment": environment(),
        "metric_path": str(metrics_path),
        "report_path": str(report_path),
        "figure_path": str(figure_path),
        "method": "uniform mixture of fixed-rate sampling and Neyman allocation",
        "guarantee": "worst-case expected query-rate drift <= configured tolerance",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return metrics_path


def main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    config = AllocationGridConfig(seeds=args.seeds, n=args.n, d=args.d, device=args.device)
    print(run_allocation_grid(config, args.output), flush=True)


def robust_main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Search rate-stabilized Neyman allocations")
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    config = AllocationGridConfig(seeds=args.seeds, n=args.n, d=args.d, device=args.device)
    print(run_rate_stabilized_grid(config, args.output), flush=True)


if __name__ == "__main__":
    main()
