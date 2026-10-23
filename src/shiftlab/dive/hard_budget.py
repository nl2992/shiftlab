"""Forward-time comparison of query policies under a common hard label-dollar cap."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import norm, sem
from scipy.stats import t as student_t
from sklearn.linear_model import LogisticRegression

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .eprocess import BoundedMeanEProcess
from .estimators import prediction_powered_bound, prediction_powered_estimate
from .experiment import (
    _binary_cost,
    _entropy,
    _material_harm_onset,
    _synthetic_label_costs,
    finalize_manifest,
)
from .proxy import DecisionLossProxy
from .query import (
    AdaptiveQueryPolicy,
    cost_mixture_weight_for_tolerance,
    mix_with_cost_neutral,
)

HARD_BUDGET_METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
MULTISCALE_STAKES = tuple(float(value) for value in np.geomspace(1 / 1024, 0.99, 13))
PROTECTED_EXPLORATION_STAKES = tuple(float(value) for value in np.geomspace(1 / 1024, 0.04, 8))
PROTECTED_STAKES = (0.05, 0.10, 0.20, 0.40, 0.80, *PROTECTED_EXPLORATION_STAKES)
PROTECTED_WEIGHTS = (0.18,) * 5 + (0.10 / len(PROTECTED_EXPLORATION_STAKES),) * len(
    PROTECTED_EXPLORATION_STAKES
)


@dataclass(frozen=True)
class HardBudgetConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 30
    seed_offset: int = 20361022
    alpha: float = 0.05
    harm_margin: float = 0.10
    budget_rate: float = 0.10
    q_min: float = 0.05
    q_max: float = 0.50
    cost_stability_tolerance: float = 0.05
    max_label_cost: float = 2.5
    common_eprocess_bound: bool = False
    device: str = "auto"
    scenario_subset: tuple[str, ...] = (
        "stationary",
        "benign_nuisance",
        "boundary_local_harm",
    )
    method_subset: tuple[str, ...] = HARD_BUDGET_METHODS

    def validate(self) -> HardBudgetConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if not 0 < self.alpha < 1 or self.harm_margin < 0:
            raise ValueError("alpha must lie in (0,1) and harm_margin must be nonnegative")
        if not 0 < self.q_min <= self.budget_rate <= self.q_max <= 1:
            raise ValueError("require 0 < q_min <= budget_rate <= q_max <= 1")
        if self.max_label_cost <= 0 or not np.isfinite(self.max_label_cost):
            raise ValueError("max_label_cost must be finite and positive")
        if not isinstance(self.common_eprocess_bound, bool):
            raise TypeError("common_eprocess_bound must be boolean")
        if self.cost_stability_tolerance < 0 or not np.isfinite(self.cost_stability_tolerance):
            raise ValueError("cost_stability_tolerance must be finite and nonnegative")
        scenarios = {scenario.name for scenario in SCENARIOS}
        if not self.scenario_subset or not set(self.scenario_subset) <= scenarios:
            raise ValueError("scenario_subset must contain registered scenario names")
        if not self.method_subset or not set(self.method_subset) <= set(HARD_BUDGET_METHODS):
            raise ValueError("method_subset must contain registered hard-budget methods")
        return self


def _one_method(
    *,
    method: str,
    seed: int,
    scenario,
    config: HardBudgetConfig,
    x: np.ndarray,
    centered_cost_difference: np.ndarray,
    expected_cost_difference: np.ndarray,
    label_costs: np.ndarray,
    classifier: LogisticRegression,
    proxy_template: DecisionLossProxy,
    train_end: int,
    monitor_start: int,
    harm_onset: int | None,
    common_uniforms: np.ndarray,
) -> dict[str, object]:
    validation_end = monitor_start
    validation_x = x[train_end:validation_end]
    validation_costs = label_costs[train_end:validation_end]
    validation_probability = classifier.predict_proba(validation_x)[:, 1]
    validation_uncertainty = _entropy(validation_probability)
    proxy = copy.deepcopy(proxy_template)

    query_kind = {
        "uniform_proxy": "uniform",
        "variance_proxy": "variance",
        "decision_value_proxy": "decision_value",
        "cost_variance_proxy": "cost_variance",
        "cost_stabilized_proxy": "cost_variance",
    }[method]
    policy = AdaptiveQueryPolicy(
        query_kind,
        target_rate=config.budget_rate,
        q_min=config.q_min,
        q_max=config.q_max,
    ).fit_multiplier(
        proxy=proxy.predict(validation_x),
        residual_second_moment=proxy.predict_residual_second_moment(validation_x),
        uncertainty=validation_uncertainty,
        label_costs=validation_costs,
    )

    budget_per_event = config.budget_rate * float(validation_costs.mean())
    budget = budget_per_event * (len(x) - monitor_start)
    mixture_weight = None
    if method == "cost_stabilized_proxy":
        mixture_weight = cost_mixture_weight_for_tolerance(
            budget_per_event=budget_per_event,
            drift_tolerance=config.cost_stability_tolerance,
            cost_min=0.5,
            cost_max=config.max_label_cost,
            q_min=config.q_min,
            q_max=config.q_max,
        )

    minimum_propensity = (
        config.q_min
        if config.common_eprocess_bound or query_kind != "uniform"
        else config.budget_rate
    )
    process = BoundedMeanEProcess(
        bound=prediction_powered_bound(proxy.clip, minimum_propensity), alpha=config.alpha
    )
    multiscale_process = BoundedMeanEProcess(
        bound=prediction_powered_bound(proxy.clip, minimum_propensity),
        alpha=config.alpha,
        stakes=MULTISCALE_STAKES,
    )
    protected_process = BoundedMeanEProcess(
        bound=prediction_powered_bound(proxy.clip, minimum_propensity),
        alpha=config.alpha,
        stakes=PROTECTED_STAKES,
        weights=PROTECTED_WEIGHTS,
    )
    monitor_x = x[monitor_start:]
    proxy_values = proxy.predict(monitor_x)
    residual_second_moments = proxy.predict_residual_second_moment(monitor_x)
    uncertainty_values = _entropy(classifier.predict_proba(monitor_x)[:, 1])
    threshold = -np.log(config.alpha)
    remaining = budget
    spent = 0.0
    expected_spend = 0.0
    queried_count = 0
    processed = 0
    estimates: list[float] = []
    truths: list[float] = []
    first_alarm = None
    first_multiscale_alarm = None
    first_protected_alarm = None
    stop_reason = "end_of_stream"
    for offset, index in enumerate(range(monitor_start, len(x))):
        # Stop before accessing the next event when even the maximum tariff is unaffordable.
        # This is a stopping time based only on past query outcomes and spend.
        if remaining + 1e-12 < config.max_label_cost:
            stop_reason = "budget_reserve"
            break

        x_now = x[index : index + 1]
        cost_now = float(label_costs[index])
        if not 0.5 <= cost_now <= config.max_label_cost:
            raise ValueError("synthetic tariff fell outside the prespecified support")
        h_now = float(proxy_values[offset])
        v_now = residual_second_moments[offset : offset + 1]
        u_now = uncertainty_values[offset : offset + 1]
        q_adaptive = float(
            policy.probabilities(
                proxy=np.asarray([h_now]),
                residual_second_moment=v_now,
                uncertainty=u_now,
                label_costs=np.asarray([cost_now]),
            )[0]
        )
        propensity = q_adaptive
        if method == "cost_stabilized_proxy":
            assert mixture_weight is not None
            propensity = float(
                mix_with_cost_neutral(
                    np.asarray([q_adaptive]),
                    np.asarray([cost_now]),
                    budget_per_event=budget_per_event,
                    mixture_weight=mixture_weight,
                    q_min=config.q_min,
                    q_max=config.q_max,
                )[0]
            )
        if not config.q_min - 1e-12 <= propensity <= config.q_max + 1e-12:
            raise RuntimeError("query propensity violated its registered bounds")

        expected_spend += propensity * cost_now
        queried = bool(common_uniforms[offset] < propensity)
        observed = float(centered_cost_difference[index]) if queried else None
        if queried:
            if cost_now > remaining + 1e-12:
                raise RuntimeError("hard label-dollar budget would be exceeded")
            queried_count += 1
            spent += cost_now
            remaining -= cost_now
        estimate = prediction_powered_estimate(h_now, queried, observed, propensity)
        estimates.append(estimate)
        truths.append(float(centered_cost_difference[index]))
        processed += 1
        process_value = process.update(estimate)
        if first_alarm is None and process_value >= threshold:
            first_alarm = offset
        multiscale_value = multiscale_process.update(estimate)
        if first_multiscale_alarm is None and multiscale_value >= threshold:
            first_multiscale_alarm = offset
        protected_value = protected_process.update(estimate)
        if first_protected_alarm is None and protected_value >= threshold:
            first_protected_alarm = offset
        if queried:
            assert observed is not None
            did_refit = proxy.observe(x_now[0], observed)
            if did_refit and offset + 1 < len(proxy_values):
                proxy_values[offset + 1 :] = proxy.predict(monitor_x[offset + 1 :])

    harm_reached = harm_onset is not None and harm_onset < processed
    detected = first_alarm is not None and harm_onset is not None and first_alarm >= harm_onset
    false_escalation = first_alarm is not None and (harm_onset is None or first_alarm < harm_onset)
    multiscale_detected = (
        first_multiscale_alarm is not None
        and harm_onset is not None
        and first_multiscale_alarm >= harm_onset
    )
    multiscale_false_escalation = first_multiscale_alarm is not None and (
        harm_onset is None or first_multiscale_alarm < harm_onset
    )
    protected_detected = (
        first_protected_alarm is not None
        and harm_onset is not None
        and first_protected_alarm >= harm_onset
    )
    protected_false_escalation = first_protected_alarm is not None and (
        harm_onset is None or first_protected_alarm < harm_onset
    )
    errors = np.asarray(estimates) - np.asarray(truths)
    delay = (
        int(first_alarm - harm_onset)
        if detected and harm_onset is not None and first_alarm is not None
        else None
    )
    return {
        "scenario": scenario.name,
        "seed": seed,
        "method": method,
        "hard_budget": budget,
        "realized_label_spend": spent,
        "budget_remaining": remaining,
        "budget_utilization": spent / budget,
        "budget_respected": spent <= budget + 1e-9,
        # This is the predictable spend compensator on a realized stopping path; unlike
        # actual spend, its pathwise sum is not constrained by the hard cap.
        "predictable_spend_compensator_until_stop": expected_spend,
        "eprocess_minimum_propensity": minimum_propensity,
        "labels_queried": queried_count,
        "processed_events": processed,
        "monitor_fraction_processed": processed / (len(x) - monitor_start),
        "stop_reason": stop_reason,
        "cost_stability_mix": mixture_weight,
        "material_harm": harm_onset is not None,
        "harm_onset_relative": harm_onset,
        "harm_reached_before_budget_stop": harm_reached,
        "single_e_detected": bool(detected),
        "single_e_false_escalation": bool(false_escalation),
        "single_e_alarm_time": first_alarm,
        "single_e_delay": delay,
        "multiscale_e_detected": bool(multiscale_detected),
        "multiscale_e_false_escalation": bool(multiscale_false_escalation),
        "multiscale_e_alarm_time": first_multiscale_alarm,
        "multiscale_e_delay": (
            int(first_multiscale_alarm - harm_onset)
            if multiscale_detected and harm_onset is not None and first_multiscale_alarm is not None
            else None
        ),
        "protected_e_detected": bool(protected_detected),
        "protected_e_false_escalation": bool(protected_false_escalation),
        "protected_e_alarm_time": first_protected_alarm,
        "protected_e_delay": (
            int(first_protected_alarm - harm_onset)
            if protected_detected and harm_onset is not None and first_protected_alarm is not None
            else None
        ),
        "stream_mean_estimation_error": (
            float(np.mean(estimates) - np.mean(truths)) if estimates else float("nan")
        ),
        "stream_mean_estimation_rmse": float(np.sqrt(np.mean(errors**2)))
        if len(errors)
        else float("nan"),
        "mean_expected_decision_harm": (
            float(np.mean(expected_cost_difference[monitor_start : monitor_start + processed]))
            if processed
            else float("nan")
        ),
    }


def _generate_stream_rows(
    scenario, seed: int, config: HardBudgetConfig, common_uniforms: np.ndarray
) -> list[dict[str, object]]:
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
    label_costs = _synthetic_label_costs(x)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    paired_difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered_difference = paired_difference - config.harm_margin
    probability = oracle.probability_positive.to_numpy(dtype=float)
    current_expected = np.where(deployed == 1, fp * (1 - probability), fn * probability)
    reference_expected = np.where(reference == 1, fp * (1 - probability), fn * probability)
    expected_difference = current_expected - reference_expected

    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    if train_end >= monitor_start - 50:
        raise ValueError("n is too small for disjoint train, validation, and monitor slices")
    validation_end = monitor_start
    proxy_template = DecisionLossProxy(
        clip=max(fn, fp) + config.harm_margin,
        seed=seed,
        update_every=20,
    )
    proxy_template.fit(
        x[:train_end],
        centered_difference[:train_end],
        x[train_end:validation_end],
        centered_difference[train_end:validation_end],
    )
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(
        x[:train_end], y[:train_end]
    )
    onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    rows = []
    for method in config.method_subset:
        rows.append(
            _one_method(
                method=method,
                seed=seed,
                scenario=scenario,
                config=config,
                x=x,
                centered_cost_difference=centered_difference,
                expected_cost_difference=expected_difference,
                label_costs=label_costs,
                classifier=classifier,
                proxy_template=proxy_template,
                train_end=train_end,
                monitor_start=monitor_start,
                harm_onset=onset,
                common_uniforms=common_uniforms,
            )
        )
    return rows


def _summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        harm = group[group.material_harm]
        reached = harm[harm.harm_reached_before_budget_stop]
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "mean_budget": group.hard_budget.mean(),
                "mean_spend": group.realized_label_spend.mean(),
                "budget_utilization": group.budget_utilization.mean(),
                "mean_labels": group.labels_queried.mean(),
                "mean_monitor_fraction": group.monitor_fraction_processed.mean(),
                "stream_mean_rmse": np.sqrt(
                    np.mean(group.stream_mean_estimation_error.to_numpy() ** 2)
                ),
                "harm_reachable_streams": len(reached),
                "harmful_streams": len(harm),
                "detection_rate_all_harm": harm.single_e_detected.mean() if len(harm) else np.nan,
                "detection_rate_reached_harm": reached.single_e_detected.mean()
                if len(reached)
                else np.nan,
                "false_escalation_rate": group.single_e_false_escalation.mean(),
                "multiscale_detection_rate_all_harm": (
                    harm.multiscale_e_detected.mean() if len(harm) else np.nan
                ),
                "multiscale_detection_rate_reached_harm": (
                    reached.multiscale_e_detected.mean() if len(reached) else np.nan
                ),
                "multiscale_false_escalation_rate": group.multiscale_e_false_escalation.mean(),
                "protected_detection_rate_all_harm": (
                    harm.protected_e_detected.mean() if len(harm) else np.nan
                ),
                "protected_detection_rate_reached_harm": (
                    reached.protected_e_detected.mean() if len(reached) else np.nan
                ),
                "protected_false_escalation_rate": group.protected_e_false_escalation.mean(),
            }
        )
    return pd.DataFrame(rows)


def _paired_effects(metrics: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Compare each policy with uniform using paired stream-seed intervals."""
    rng = np.random.default_rng(seed)
    rows = []
    for scenario in sorted(metrics.scenario.unique()):
        baseline = metrics.loc[
            metrics.scenario.eq(scenario) & metrics.method.eq("uniform_proxy")
        ].sort_values("seed")
        methods = sorted(set(metrics.method) - {"uniform_proxy"})
        for method in methods:
            candidate = metrics.loc[
                metrics.scenario.eq(scenario) & metrics.method.eq(method)
            ].sort_values("seed")
            paired = baseline.merge(
                candidate, on=["scenario", "seed"], suffixes=("_uniform", "_method")
            )
            if len(paired) != len(baseline) or len(paired) != len(candidate):
                raise ValueError("paired hard-budget methods have mismatched seed sets")
            n = len(paired)
            indices = rng.integers(0, n, size=(20_000, n))
            err_uniform = paired.stream_mean_estimation_error_uniform.to_numpy()
            err_method = paired.stream_mean_estimation_error_method.to_numpy()
            rmse_draw = np.sqrt(np.mean(err_method[indices] ** 2, axis=1)) - np.sqrt(
                np.mean(err_uniform[indices] ** 2, axis=1)
            )

            def t_interval(values: np.ndarray) -> tuple[float, float, float]:
                mean = float(np.mean(values))
                if len(values) < 2:
                    return mean, float("nan"), float("nan")
                radius = float(student_t.ppf(0.975, len(values) - 1) * sem(values))
                return mean, mean - radius, mean + radius

            spend = t_interval(
                paired.realized_label_spend_method.to_numpy()
                - paired.realized_label_spend_uniform.to_numpy()
            )
            labels = t_interval(
                paired.labels_queried_method.to_numpy() - paired.labels_queried_uniform.to_numpy()
            )
            horizon = t_interval(
                paired.monitor_fraction_processed_method.to_numpy()
                - paired.monitor_fraction_processed_uniform.to_numpy()
            )
            harmful = paired.loc[paired.material_harm_method.astype(bool)]
            reached = harmful.loc[harmful.harm_reached_before_budget_stop_method.astype(bool)]
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "n_seeds": n,
                    "rmse_difference": float(
                        np.sqrt(np.mean(err_method**2)) - np.sqrt(np.mean(err_uniform**2))
                    ),
                    "rmse_ci_low": float(np.quantile(rmse_draw, 0.025)),
                    "rmse_ci_high": float(np.quantile(rmse_draw, 0.975)),
                    "spend_difference": spend[0],
                    "spend_ci_low": spend[1],
                    "spend_ci_high": spend[2],
                    "label_difference": labels[0],
                    "label_ci_low": labels[1],
                    "label_ci_high": labels[2],
                    "monitor_fraction_difference": horizon[0],
                    "monitor_ci_low": horizon[1],
                    "monitor_ci_high": horizon[2],
                    "harm_detected": int(reached.single_e_detected_method.sum()),
                    "harm_reached": len(reached),
                    "harmful_streams": len(harmful),
                    "false_escalations": int(paired.single_e_false_escalation_method.sum()),
                    "multiscale_detection_method": int(reached.multiscale_e_detected_method.sum()),
                    "multiscale_detection_uniform": int(
                        reached.multiscale_e_detected_uniform.sum()
                    ),
                    "multiscale_only": int(
                        (
                            reached.multiscale_e_detected_method & ~reached.single_e_detected_method
                        ).sum()
                    ),
                    "fixed_only": int(
                        (
                            reached.single_e_detected_method & ~reached.multiscale_e_detected_method
                        ).sum()
                    ),
                    "multiscale_false_escalations": int(
                        paired.multiscale_e_false_escalation_method.sum()
                    ),
                    "protected_detection_method": int(reached.protected_e_detected_method.sum()),
                    "protected_detection_uniform": int(reached.protected_e_detected_uniform.sum()),
                    "protected_only": int(
                        (
                            reached.protected_e_detected_method & ~reached.single_e_detected_method
                        ).sum()
                    ),
                    "fixed_only_vs_protected": int(
                        (
                            reached.single_e_detected_method & ~reached.protected_e_detected_method
                        ).sum()
                    ),
                    "protected_false_escalations": int(
                        paired.protected_e_false_escalation_method.sum()
                    ),
                }
            )
    return pd.DataFrame(rows)


def _append_paired_comparisons(output: Path, metrics: pd.DataFrame, seed: int) -> None:
    effects = _paired_effects(metrics, seed)
    effects.to_csv(output / "metrics" / "paired_effects_vs_uniform.csv", index=False)
    report_path = output / "reports" / "hard_budget_comparison.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "\n## Paired comparison against uniform sampling\n"
    if marker in report:
        report = report.split(marker)[0]
    lines = [
        marker,
        "RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.",
        "",
        "|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in effects.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['rmse_difference']:.4f} [{row['rmse_ci_low']:.4f}, {row['rmse_ci_high']:.4f}]|{row['spend_difference']:.2f} [{row['spend_ci_low']:.2f}, {row['spend_ci_high']:.2f}]|{row['label_difference']:.1f} [{row['label_ci_low']:.1f}, {row['label_ci_high']:.1f}]|{row['monitor_fraction_difference']:.3f} [{row['monitor_ci_low']:.3f}, {row['monitor_ci_high']:.3f}]|{row['harm_detected']} / {row['multiscale_detection_method']} / {row['protected_detection_method']} / {row['harm_reached']}|{row['multiscale_only']} / {row['fixed_only']}|{row['protected_only']} / {row['fixed_only_vs_protected']}|{row['protected_false_escalations']} / {row['n_seeds']}|"
        )
    report_path.write_text(report + "\n".join(lines) + "\n", encoding="utf-8")


def _wilson_bounds(successes: np.ndarray, totals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return numerically ordered Wilson bounds for nonempty binomial groups."""
    successes = np.asarray(successes, dtype=float)
    totals = np.asarray(totals, dtype=float)
    if successes.shape != totals.shape or np.any(totals <= 0):
        raise ValueError("successes and positive totals must have matching shapes")
    rate = successes / totals
    z = float(norm.ppf(0.975))
    denom = 1 + z**2 / totals
    center = (rate + z**2 / (2 * totals)) / denom
    radius = z * np.sqrt(rate * (1 - rate) / totals + z**2 / (4 * totals**2)) / denom
    lower = np.minimum(rate, np.maximum(0.0, center - radius))
    upper = np.maximum(rate, np.minimum(1.0, center + radius))
    return lower, upper


def _plot_hard_budget(metrics: pd.DataFrame, figure_path: Path) -> None:
    methods = [method for method in HARD_BUDGET_METHODS if method in set(metrics.method)]
    scenarios = sorted(metrics.scenario.unique())
    x = np.arange(len(methods))
    width = 0.78 / len(scenarios)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), constrained_layout=True)
    summary = _summarize(metrics)
    for index, scenario in enumerate(scenarios):
        group = summary.loc[summary.scenario.eq(scenario)].set_index("method").reindex(methods)
        offset = (index - (len(scenarios) - 1) / 2) * width
        axes[0].bar(x + offset, group.stream_mean_rmse, width, label=scenario)
    axes[0].set_xticks(x, methods, rotation=28, ha="right")
    axes[0].set_ylabel("RMSE of stream-mean excess cost")
    axes[0].set_title("Estimation error under the common dollar cap")
    axes[0].legend(fontsize=8)
    axes[0].grid(axis="y", alpha=0.25)

    harmful_scenarios = [
        scenario
        for scenario in scenarios
        if metrics.loc[metrics.scenario.eq(scenario), "material_harm"].any()
    ]
    if not harmful_scenarios:
        axes[1].text(
            0.5,
            0.5,
            "No evaluator-labeled harmful streams\n(detection rate is not applicable)",
            ha="center",
            va="center",
            transform=axes[1].transAxes,
        )
        axes[1].set_title("Null-control false escalations")
        axes[1].set_axis_off()
    else:
        detection_scenario = (
            "boundary_local_harm"
            if "boundary_local_harm" in harmful_scenarios
            else harmful_scenarios[0]
        )
        harmful = metrics.loc[metrics.scenario.eq(detection_scenario) & metrics.material_harm]
        monitor_columns = (
            ("single_e_detected", "Fixed mixture", "tab:blue"),
            ("multiscale_e_detected", "Broad multiscale", "tab:orange"),
            ("protected_e_detected", "Protected multiscale", "tab:green"),
        )
        bar_width = 0.72 / len(monitor_columns)
        max_upper = 0.0
        sample_count = 0
        for monitor_index, (column, label, color) in enumerate(monitor_columns):
            detection = harmful.groupby("method")[column].agg(["sum", "count"]).reindex(methods)
            rate = detection["sum"] / detection["count"]
            lower, upper = _wilson_bounds(
                detection["sum"].to_numpy(), detection["count"].to_numpy()
            )
            offset = (monitor_index - (len(monitor_columns) - 1) / 2) * bar_width
            axes[1].bar(x + offset, rate, color=color, width=bar_width, label=label)
            axes[1].errorbar(
                x + offset,
                rate,
                yerr=np.maximum(0.0, np.vstack((rate - lower, upper - rate))),
                fmt="none",
                ecolor="black",
                capsize=2,
            )
            max_upper = max(max_upper, float(upper.max()))
            sample_count = max(sample_count, int(detection["count"].max()))
        axes[1].set_xticks(x, methods, rotation=28, ha="right")
        axes[1].set_ylim(0, max(0.35, max_upper + 0.03))
        axes[1].set_ylabel(f"Detection rate among {sample_count} streams")
        axes[1].set_title(f"Detection: {detection_scenario}")
        axes[1].legend(fontsize=8)
        axes[1].grid(axis="y", alpha=0.25)
    fig.suptitle("Query allocation under a common hard label-dollar budget")
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def run_hard_budget(config: HardBudgetConfig, output: Path) -> Path:
    config.validate()
    requested_device = config.device
    config = HardBudgetConfig(
        **{
            **asdict(config),
            "device": resolve_device(config.device, n=config.n, d=config.d, chunk_size=2048),
        }
    )
    metrics_dir, reports_dir, figures_dir = (
        output / "metrics",
        output / "reports",
        output / "figures",
    )
    for folder in (metrics_dir, reports_dir, figures_dir):
        folder.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "hard_budget_comparison.parquet"
    if metrics_path.exists():
        raise FileExistsError(f"refusing to overwrite existing hard-budget run: {metrics_path}")

    scenario_set = set(config.scenario_subset)
    selected_scenarios = [scenario for scenario in SCENARIOS if scenario.name in scenario_set]
    rows = []
    for scenario in selected_scenarios:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            # Match the main DIVE benchmark's query RNG stream for paired comparison.
            common_uniforms = np.random.default_rng(seed + 9_173).random(config.n)
            print(
                f"hard-budget scenario={scenario.name} replicate={replicate + 1}/{config.seeds} device={config.device}",
                flush=True,
            )
            rows.extend(_generate_stream_rows(scenario, seed, config, common_uniforms))
    metrics = pd.DataFrame(rows)
    if not metrics.budget_respected.all():
        raise RuntimeError("a run exceeded its hard label-dollar budget")
    metrics.to_parquet(metrics_path, index=False)
    summary = _summarize(metrics)
    summary.to_csv(metrics_dir / "hard_budget_summary.csv", index=False)

    _plot_hard_budget(metrics, figures_dir / "hard_budget_tradeoff.png")

    lines = [
        "# Common hard label-dollar budget comparison",
        "",
        f"Evaluated {config.seeds} seeds per scenario on `{config.device}`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at {config.max_label_cost:g}; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.",
        (
            "All methods use the common configured propensity floor for their e-process bound."
            if config.common_eprocess_bound
            else "The primary comparison uses each method's actual minimum propensity in its e-process bound: uniform queries at 0.10 use a tighter bound than adaptive policies that can query at 0.05. The common-bound sensitivity at reports/eprocess_bound_sensitivity.md found 0/30 detections for every method under q_min=0.05; do not attribute the primary 4-versus-0 difference solely to allocation."
        ),
        "",
        "The e-process is evaluated only through its budget stopping time. Harm detection is reported both over all evaluator-labeled harmful streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.",
        "",
        "|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        all_detection = row["detection_rate_all_harm"]
        reached_detection = row["detection_rate_reached_harm"]
        all_detection_text = "n/a" if pd.isna(all_detection) else f"{all_detection:.3f}"
        reached_detection_text = "n/a" if pd.isna(reached_detection) else f"{reached_detection:.3f}"
        multiscale_all = row["multiscale_detection_rate_all_harm"]
        multiscale_reached = row["multiscale_detection_rate_reached_harm"]
        multiscale_all_text = "n/a" if pd.isna(multiscale_all) else f"{multiscale_all:.3f}"
        multiscale_reached_text = (
            "n/a" if pd.isna(multiscale_reached) else f"{multiscale_reached:.3f}"
        )
        protected_all = row["protected_detection_rate_all_harm"]
        protected_reached = row["protected_detection_rate_reached_harm"]
        protected_all_text = "n/a" if pd.isna(protected_all) else f"{protected_all:.3f}"
        protected_reached_text = "n/a" if pd.isna(protected_reached) else f"{protected_reached:.3f}"
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['mean_budget']:.2f}|{row['mean_spend']:.2f}|{row['budget_utilization']:.3f}|{row['mean_labels']:.1f}|{row['mean_monitor_fraction']:.3f}|{row['stream_mean_rmse']:.4f}|{row['harm_reachable_streams']}/{row['harmful_streams']}|{all_detection_text} / {reached_detection_text}|{multiscale_all_text} / {multiscale_reached_text}|{protected_all_text} / {protected_reached_text}|{row['false_escalation_rate']:.3f} / {row['multiscale_false_escalation_rate']:.3f} / {row['protected_false_escalation_rate']:.3f}|"
        )
    lines.extend(
        [
            "",
            "## Full-horizon consistency check",
            "",
            "This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.",
            "",
            "The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.",
            "The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.",
            "",
            "## Interpretation limits",
            "",
            "This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.",
            "",
            (
                "Reproduce with `uv run shiftlab-dive-hard-budget "
                f"--seeds {config.seeds} --seed-offset {config.seed_offset} "
                f"--n {config.n} --d {config.d} --budget-rate {config.budget_rate} "
                f"--q-min {config.q_min} --q-max {config.q_max} --device {config.device} "
                f"--scenarios {' '.join(config.scenario_subset)} "
                f"--methods {' '.join(config.method_subset)} "
                f"{'--common-eprocess-bound ' if config.common_eprocess_bound else ''}"
                f"--output {output.as_posix()}`."
            ),
            "",
            "![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)",
            "",
        ]
    )
    (reports_dir / "hard_budget_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    _append_paired_comparisons(output, metrics, seed=config.seed_offset + 443)
    manifest = {
        "experiment": "hard_label_dollar_budget_query_policy_comparison",
        "configuration": asdict(config),
        "requested_device": requested_device,
        "resolved_device": config.device,
        "environment": environment(),
        "assumptions": [
            "Immediate paired labels; no delayed-feedback behavior tested.",
            "Known query-time tariff support [0.5, max_label_cost].",
            "Hard-budget stopping checks only remaining spend before the next event.",
            "Both policy costs are observable from the same outcome.",
            "E-process validity requires the conditional-mean null and bounded corrected increments.",
            "The sum of q_t * tariff_t along the realized stopping path is a compensator, not pathwise-capped actual spend.",
            "E-process minimum propensities are recorded per method; common_eprocess_bound can enforce a shared q_min bound for sensitivity runs.",
        ],
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return output


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/hard_budget"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--budget-rate", type=float, default=0.10)
    parser.add_argument("--q-min", type=float, default=0.05)
    parser.add_argument("--seed-offset", type=int, default=20361022)
    parser.add_argument("--q-max", type=float, default=0.50)
    parser.add_argument("--cost-stability-tolerance", type=float, default=0.05)
    parser.add_argument(
        "--common-eprocess-bound",
        action="store_true",
        help="use q_min for all method bounds to isolate query allocation from threshold width",
    )
    parser.add_argument("--scenarios", nargs="+", choices=[scenario.name for scenario in SCENARIOS])
    parser.add_argument("--methods", nargs="+", choices=HARD_BUDGET_METHODS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    config = HardBudgetConfig(
        n=args.n,
        d=args.d,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        budget_rate=args.budget_rate,
        q_min=args.q_min,
        q_max=args.q_max,
        cost_stability_tolerance=args.cost_stability_tolerance,
        common_eprocess_bound=args.common_eprocess_bound,
        device=args.device,
        scenario_subset=tuple(args.scenarios or HardBudgetConfig.scenario_subset),
        method_subset=tuple(args.methods or HARD_BUDGET_METHODS),
    )
    print(run_hard_budget(config, args.output), flush=True)


if __name__ == "__main__":
    main()
