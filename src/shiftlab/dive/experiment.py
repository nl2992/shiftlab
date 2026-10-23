"""Paired-seed benchmark for full, uniform, proxy-corrected and adaptive-query monitors."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import norm
from scipy.stats import t as student_t
from sklearn.linear_model import LogisticRegression

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import (
    POPULATION_NULL_CONTROLS,
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from ..monitoring import rbf_gamma, rbf_mmd_squared
from .eprocess import BoundedMeanEProcess, StartedMixtureEProcess
from .estimators import AdaptiveReliance, prediction_powered_bound, prediction_powered_estimate
from .evaluation import apply_population_null_classification
from .proxy import DecisionLossProxy
from .query import (
    AdaptiveQueryPolicy,
    EvidenceGrowthQueryPolicy,
    cost_mixture_weight_for_tolerance,
    expected_cost_drift_bound,
    mix_with_cost_neutral,
    mix_with_uniform,
)

METHODS = (
    "full_feedback",
    "uniform_direct",
    "uniform_proxy",
    "pprm_reliance_analogue",
    "uncertainty_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "evidence_growth_proxy",
    "evidence_growth_stabilized_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)


@dataclass(frozen=True)
class DiveExperimentConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 30
    seed_offset: int = 20261022
    alpha: float = 0.05
    harm_margin: float = 0.10
    query_rate: float = 0.10
    query_min: float = 0.05
    query_max: float = 0.50
    label_cost: float = 0.01
    proxy_update_every: int = 20
    variance_power: float = 0.5
    heterogeneous_label_costs: bool = False
    cost_stability_tolerance: float = 0.05
    evidence_rate_stability_tolerance: float = 0.01
    scenario_subset: tuple[str, ...] = ()
    method_subset: tuple[str, ...] = ()
    device: str = "auto"

    def validate(self) -> DiveExperimentConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if not 0 < self.alpha < 1 or self.harm_margin < 0:
            raise ValueError("alpha must lie in (0,1) and harm_margin must be nonnegative")
        if not 0 < self.query_min <= self.query_rate <= self.query_max <= 1:
            raise ValueError("require 0 < query_min <= query_rate <= query_max <= 1")
        if self.label_cost < 0 or not np.isfinite(self.label_cost):
            raise ValueError("label_cost must be finite and nonnegative")
        if not np.isfinite(self.variance_power) or not 0 <= self.variance_power <= 1:
            raise ValueError("variance_power must lie in [0, 1]")
        if not np.isfinite(self.cost_stability_tolerance) or self.cost_stability_tolerance < 0:
            raise ValueError("cost_stability_tolerance must be finite and nonnegative")
        if (
            not np.isfinite(self.evidence_rate_stability_tolerance)
            or self.evidence_rate_stability_tolerance < 0
        ):
            raise ValueError("evidence_rate_stability_tolerance must be finite and nonnegative")
        scenario_names = {scenario.name for scenario in SCENARIOS}
        if len(set(self.scenario_subset)) != len(self.scenario_subset) or any(
            name not in scenario_names for name in self.scenario_subset
        ):
            raise ValueError("scenario_subset must contain unique registered scenario names")
        available_methods = set(METHODS if self.heterogeneous_label_costs else METHODS[:-2])
        if len(set(self.method_subset)) != len(self.method_subset) or any(
            name not in available_methods for name in self.method_subset
        ):
            raise ValueError("method_subset must contain unique methods enabled by this config")
        if isinstance(self.proxy_update_every, bool) or self.proxy_update_every < 1:
            raise ValueError("proxy_update_every must be a positive integer")
        return self


def _binary_cost(actions: np.ndarray, labels: np.ndarray, fn: float, fp: float) -> np.ndarray:
    actions = np.asarray(actions, dtype=int).reshape(-1)
    labels = np.asarray(labels, dtype=bool).reshape(-1)
    if len(actions) != len(labels) or not np.isin(actions, [0, 1]).all():
        raise ValueError("actions and labels must be compatible binary vectors")
    return np.where(actions == 1, fp * ~labels, fn * labels).astype(float)


def _entropy(probability: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(probability, dtype=float), 1e-6, 1 - 1e-6)
    return -(p * np.log(p) + (1 - p) * np.log1p(-p))


def _synthetic_label_costs(x: np.ndarray) -> np.ndarray:
    """Known query-time label tariff in [0.5, 2.5], based on an observed covariate."""
    score = np.clip(np.asarray(x, dtype=float)[:, -1], -30, 30)
    return 0.5 + 2.0 / (1.0 + np.exp(-score))


def _evidence_uniform_mix_weight(config: DiveExperimentConfig) -> float:
    deviation = max(
        config.query_rate - config.query_min,
        config.query_max - config.query_rate,
    )
    if deviation == 0:
        return 0.0
    return min(1.0, config.evidence_rate_stability_tolerance / deviation)


def _material_harm_onset(
    expected_difference: np.ndarray,
    margin: float,
    *,
    change_times: list[int],
    monitor_start: int,
) -> int | None:
    """Find the first evaluator-known regime whose mean expected harm exceeds margin."""
    n = len(expected_difference)
    boundaries = sorted({0, n, *(int(value) for value in change_times)})
    for start, end in pairwise(boundaries):
        start = max(start, monitor_start)
        if start < end and float(np.mean(expected_difference[start:end])) > margin:
            return start - monitor_start
    return None


def _mmd_summary(reference: np.ndarray, evaluation: np.ndarray, seed: int) -> float:
    rng = np.random.default_rng(seed)
    count = min(128, len(reference), len(evaluation) // 3)
    if count < 2:
        return 0.0
    ref = reference[rng.choice(len(reference), count, replace=False)]
    gamma = rbf_gamma(ref)
    scores = []
    for start in np.linspace(0, max(0, len(evaluation) - count), 3, dtype=int):
        current = evaluation[start : start + count]
        if len(current) == count:
            scores.append(rbf_mmd_squared(ref, current, gamma))
    return float(np.mean(scores))


def _fit_query_policy(
    method: str,
    *,
    proxy: DecisionLossProxy,
    x_validation: np.ndarray,
    validation_uncertainty: np.ndarray,
    query_rate: float,
    query_min: float,
    query_max: float,
    variance_power: float = 0.5,
    validation_label_costs: np.ndarray | None = None,
) -> AdaptiveQueryPolicy:
    policy = AdaptiveQueryPolicy(
        method,
        target_rate=query_rate,
        q_min=query_min,
        q_max=query_max,
        variance_power=variance_power,
    )
    policy.fit_multiplier(
        proxy=proxy.predict(x_validation),
        residual_second_moment=proxy.predict_residual_second_moment(x_validation),
        uncertainty=validation_uncertainty,
        label_costs=validation_label_costs,
    )
    return policy


def _monitor_method(
    *,
    method: str,
    seed: int,
    config: DiveExperimentConfig,
    scenario,
    x: np.ndarray,
    z_centered: np.ndarray,
    expected_difference: np.ndarray,
    proxy_template: DecisionLossProxy,
    classifier: LogisticRegression,
    train_end: int,
    validation_end: int,
    monitor_start: int,
    harm_onset: int | None,
    sample_path_material_harm: bool,
    sample_path_harm_onset: int | None,
    label_costs: np.ndarray | None = None,
    contrast_zero: np.ndarray | None = None,
    contrast_one: np.ndarray | None = None,
) -> dict:
    n_evaluation = len(x) - monitor_start
    x_validation = x[train_end:validation_end]
    p_validation = classifier.predict_proba(x_validation)[:, 1]
    validation_uncertainty = _entropy(p_validation)
    # Every method starts from the same pre-monitor fit; deepcopy isolates online updates.
    proxy = copy.deepcopy(proxy_template)
    proxy.update_every = config.proxy_update_every
    reliance = None
    if method == "pprm_reliance_analogue":
        reliance = AdaptiveReliance(query_fraction=config.query_rate).fit(
            proxy.predict(x_validation), z_centered[train_end:validation_end]
        )

    if method == "full_feedback":
        query_policy = None
        evidence_policy = None
        minimum_propensity = 1.0
        bound = proxy.clip
    else:
        evidence_policy = None
        query_kind = {
            "uniform_direct": "uniform",
            "uniform_proxy": "uniform",
            "pprm_reliance_analogue": "uniform",
            "uncertainty_proxy": "uncertainty",
            "variance_proxy": "variance",
            "decision_value_proxy": "decision_value",
            "evidence_growth_proxy": "evidence_growth",
            "evidence_growth_stabilized_proxy": "evidence_growth",
            "cost_variance_proxy": "cost_variance",
            "cost_stabilized_proxy": "cost_variance",
        }[method]
        validation_costs = None if label_costs is None else label_costs[train_end:validation_end]
        if query_kind == "evidence_growth":
            if contrast_zero is None or contrast_one is None:
                raise ValueError("evidence-growth sampling requires outcome-specific contrasts")
            evidence_policy = EvidenceGrowthQueryPolicy(
                target_rate=config.query_rate,
                q_min=config.query_min,
                q_max=config.query_max,
                bound=prediction_powered_bound(proxy.clip, config.query_min),
            ).fit_multiplier(
                proxy=proxy.predict(x_validation),
                probability_positive=classifier.predict_proba(x_validation)[:, 1],
                contrast_zero=contrast_zero[train_end:validation_end],
                contrast_one=contrast_one[train_end:validation_end],
                label_costs=validation_costs,
            )
            query_policy = None
        else:
            query_policy = _fit_query_policy(
                query_kind,
                proxy=proxy,
                x_validation=x_validation,
                validation_uncertainty=validation_uncertainty,
                query_rate=config.query_rate,
                query_min=config.query_min,
                query_max=config.query_max,
                variance_power=config.variance_power,
                validation_label_costs=validation_costs,
            )
        minimum_propensity = config.query_rate if query_kind == "uniform" else config.query_min
        if method == "uniform_direct":
            bound = proxy.clip / minimum_propensity
        else:
            bound = prediction_powered_bound(proxy.clip, minimum_propensity)

    monitor = BoundedMeanEProcess(bound=bound, alpha=config.alpha)
    mixture_starts = tuple(sorted({0, n_evaluation // 4, n_evaluation // 2, 3 * n_evaluation // 4}))
    mixture = StartedMixtureEProcess(bound=bound, alpha=config.alpha, starts=mixture_starts)
    monitor_x = x[monitor_start:]
    monitor_positive_probabilities = classifier.predict_proba(monitor_x)[:, 1]
    uncertainty_values = _entropy(monitor_positive_probabilities)
    residual_second_moments = proxy.predict_residual_second_moment(monitor_x)
    proxy_values = proxy.predict(monitor_x)
    if method == "uniform_direct":
        proxy_values.fill(0.0)
    rng = np.random.default_rng(seed + 9173)
    labels_queried = 0
    expected_labels = 0.0
    expected_label_spend = 0.0
    realized_label_spend = 0.0
    estimates = np.empty(n_evaluation)
    proxy_predictions = np.empty(n_evaluation)
    propensities = np.empty(n_evaluation)
    validation_expected_query_rate = (
        config.query_rate if query_policy is not None or evidence_policy is not None else 1.0
    )
    if evidence_policy is not None:
        if contrast_zero is None or contrast_one is None:
            raise RuntimeError("outcome-specific contrasts were not supplied")
        validation_expected_query_rate = float(
            evidence_policy.probabilities(
                proxy=proxy.predict(x_validation),
                probability_positive=classifier.predict_proba(x_validation)[:, 1],
                contrast_zero=contrast_zero[train_end:validation_end],
                contrast_one=contrast_one[train_end:validation_end],
                label_costs=(
                    None if label_costs is None else label_costs[train_end:validation_end]
                ),
            ).mean()
        )
    evidence_mixture_weight = None
    if method == "evidence_growth_stabilized_proxy":
        evidence_mixture_weight = _evidence_uniform_mix_weight(config)
    first_alarm = None
    first_mixture_alarm = None
    refits = 0
    budget_per_event = None
    spend_drift_bound = None
    mixture_weight = None
    if method == "cost_stabilized_proxy":
        if label_costs is None:
            raise ValueError("cost_stabilized_proxy requires heterogeneous label costs")
        validation_costs = label_costs[train_end:validation_end]
        budget_per_event = config.query_rate * float(validation_costs.mean())
        mixture_weight = cost_mixture_weight_for_tolerance(
            budget_per_event=budget_per_event,
            drift_tolerance=config.cost_stability_tolerance,
            cost_min=0.5,
            cost_max=2.5,
            q_min=config.query_min,
            q_max=config.query_max,
        )
        spend_drift_bound = expected_cost_drift_bound(
            budget_per_event=budget_per_event,
            mixture_weight=mixture_weight,
            cost_min=0.5,
            cost_max=2.5,
            q_min=config.query_min,
            q_max=config.query_max,
        )

    for offset, index in enumerate(range(monitor_start, len(x))):
        x_now = x[index : index + 1]
        label_cost_now = 1.0 if label_costs is None else float(label_costs[index])
        raw_proxy_now = float(proxy_values[offset])
        h_now = raw_proxy_now
        if reliance is not None:
            h_now = float(np.clip(reliance.reliance * raw_proxy_now, -proxy.clip, proxy.clip))
        proxy_predictions[offset] = h_now
        if query_policy is None and evidence_policy is None:
            propensity = 1.0
        else:
            uncertainty_now = np.asarray([uncertainty_values[offset]])
            variance_now = np.asarray([residual_second_moments[offset]])
            if evidence_policy is not None:
                if contrast_zero is None or contrast_one is None:
                    raise RuntimeError("outcome-specific contrasts were not supplied")
                adaptive_propensity = evidence_policy.probabilities(
                    proxy=np.asarray([h_now]),
                    probability_positive=np.asarray([monitor_positive_probabilities[offset]]),
                    contrast_zero=np.asarray([contrast_zero[index]]),
                    contrast_one=np.asarray([contrast_one[index]]),
                    label_costs=np.asarray([label_cost_now]),
                )
                if evidence_mixture_weight is not None:
                    adaptive_propensity = mix_with_uniform(
                        adaptive_propensity,
                        target_rate=config.query_rate,
                        mixture_weight=evidence_mixture_weight,
                    )
            else:
                if query_policy is None:
                    raise RuntimeError("query policy was not initialized")
                adaptive_propensity = query_policy.probabilities(
                    proxy=np.asarray([h_now]),
                    residual_second_moment=variance_now,
                    uncertainty=uncertainty_now,
                    label_costs=np.asarray([label_cost_now]),
                )
            if method == "cost_stabilized_proxy":
                if budget_per_event is None or mixture_weight is None:
                    raise RuntimeError("cost-stability calibration was not initialized")
                propensity = float(
                    mix_with_cost_neutral(
                        adaptive_propensity,
                        np.asarray([label_cost_now]),
                        budget_per_event=float(budget_per_event),
                        mixture_weight=float(mixture_weight),
                        q_min=config.query_min,
                        q_max=config.query_max,
                    )[0]
                )
            else:
                propensity = float(adaptive_propensity[0])
        propensities[offset] = propensity
        expected_labels += propensity
        expected_label_spend += propensity * label_cost_now
        queried = bool(rng.random() < propensity)
        observed = float(z_centered[index]) if queried else None
        if queried:
            labels_queried += 1
            realized_label_spend += label_cost_now
            if observed is None:
                raise RuntimeError("queried event did not produce an observed outcome")
        if method in {"full_feedback", "uniform_direct"}:
            estimate = prediction_powered_estimate(0.0, queried, observed, propensity)
        else:
            estimate = prediction_powered_estimate(h_now, queried, observed, propensity)
            if queried:
                assert observed is not None
                if reliance is not None:
                    reliance.observe(raw_proxy_now, float(observed))
                # Keep the expected-evidence policy's fitted contrast proxy fixed;
                # its validation-calibrated dual objective assumes this prediction
                # rule. Other methods retain their prequential proxy updates.
                did_refit = (
                    False
                    if method
                    in {
                        "evidence_growth_proxy",
                        "evidence_growth_stabilized_proxy",
                    }
                    else proxy.observe(x_now[0], float(observed))
                )
                refits += int(did_refit)
                if did_refit and offset + 1 < n_evaluation:
                    proxy_values[offset + 1 :] = proxy.predict(monitor_x[offset + 1 :])
        estimates[offset] = estimate
        monitor_value = monitor.update(estimate)
        mixture_value = mixture.update(estimate)
        if first_alarm is None and monitor_value >= -np.log(config.alpha):
            first_alarm = offset
        if first_mixture_alarm is None and mixture_value >= -np.log(config.alpha):
            first_mixture_alarm = offset

    truth = z_centered[monitor_start:]
    proxy_error = proxy_predictions - truth
    material = harm_onset is not None
    false_alarm = first_alarm is not None and (harm_onset is None or first_alarm < harm_onset)
    mixture_false_alarm = first_mixture_alarm is not None and (
        harm_onset is None or first_mixture_alarm < harm_onset
    )
    detected = first_alarm is not None and harm_onset is not None and first_alarm >= harm_onset
    mixture_detected = (
        first_mixture_alarm is not None
        and harm_onset is not None
        and first_mixture_alarm >= harm_onset
    )
    single_delay = (
        first_alarm - harm_onset
        if first_alarm is not None and harm_onset is not None and first_alarm >= harm_onset
        else None
    )
    mixture_delay = (
        first_mixture_alarm - harm_onset
        if first_mixture_alarm is not None
        and harm_onset is not None
        and first_mixture_alarm >= harm_onset
        else None
    )
    return {
        "scenario": scenario.name,
        "seed": seed,
        "method": method,
        "n_stream": len(x),
        "monitor_start": monitor_start,
        "harm_onset_relative": harm_onset,
        "material_harm": material,
        "population_null_control": scenario.name in POPULATION_NULL_CONTROLS,
        "sample_path_material_harm": sample_path_material_harm,
        "sample_path_harm_onset_relative": sample_path_harm_onset,
        "query_rate_target": (
            config.query_rate if query_policy is not None or evidence_policy is not None else 1.0
        ),
        "validation_expected_query_rate": validation_expected_query_rate,
        "evidence_growth_uniform_mix": evidence_mixture_weight,
        "expected_query_count": expected_labels,
        "labels_queried": labels_queried,
        "expected_label_spend": expected_label_spend,
        "realized_label_spend": realized_label_spend,
        "cost_stability_tolerance": (
            config.cost_stability_tolerance if method == "cost_stabilized_proxy" else None
        ),
        "cost_stability_mix": (mixture_weight if method == "cost_stabilized_proxy" else None),
        "cost_budget_per_event": budget_per_event,
        "expected_spend_drift_bound": spend_drift_bound,
        "observed_query_rate": labels_queried / n_evaluation,
        "propensity_mean": float(propensities.mean()),
        "propensity_min": float(propensities.min()),
        "propensity_max": float(propensities.max()),
        "proxy_validation_rmse": proxy_template.diagnostics["validation_rmse"],
        "proxy_prequential_rmse": float(np.sqrt(np.mean(proxy_error**2))),
        "stream_mean_estimate": float(estimates.mean()),
        "stream_mean_truth": float(truth.mean()),
        "stream_mean_estimation_error": float(estimates.mean() - truth.mean()),
        "cumulative_estimation_error": float(estimates.sum() - truth.sum()),
        "estimated_z_variance": float(estimates.var(ddof=1)),
        "mean_expected_decision_harm": float(expected_difference[monitor_start:].mean()),
        "cumulative_expected_decision_harm": float(expected_difference[monitor_start:].sum()),
        "cumulative_net_cost_vs_reference": float(
            expected_difference[monitor_start:].sum()
            + config.label_cost
            * (realized_label_spend if label_costs is not None else labels_queried)
        ),
        "single_e_alarm": first_alarm is not None,
        "single_e_alarm_time": first_alarm,
        "single_e_false_escalation": bool(false_alarm),
        "single_e_detected": bool(detected),
        "single_e_delay": single_delay,
        "mixture_e_alarm": first_mixture_alarm is not None,
        "mixture_e_alarm_time": first_mixture_alarm,
        "mixture_e_false_escalation": bool(mixture_false_alarm),
        "mixture_e_detected": bool(mixture_detected),
        "mixture_e_delay": mixture_delay,
        "proxy_online_refits": refits,
        "adaptive_proxy_reliance": None if reliance is None else reliance.reliance,
        "feature_mmd_mean": _mmd_summary(x[:train_end], x[monitor_start:], seed=seed + 811),
        "decision_margin": config.harm_margin,
        "fn_cost": scenario.fn_cost,
        "fp_cost": scenario.fp_cost,
        "label_cost": config.label_cost,
    }


def _one_stream(scenario, seed: int, config: DiveExperimentConfig) -> list[dict]:
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
    label_costs = _synthetic_label_costs(x) if config.heterogeneous_label_costs else None
    y_continuous = frame.target.to_numpy(dtype=float)
    y = y_continuous > 0
    fn, fp = scenario.fn_cost, scenario.fp_cost
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    observed_difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    z_centered = observed_difference - config.harm_margin
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
    p = oracle.probability_positive.to_numpy(dtype=float)
    current_expected = np.where(deployed == 1, fp * (1 - p), fn * p)
    reference_expected = np.where(reference == 1, fp * (1 - p), fn * p)
    expected_difference = current_expected - reference_expected

    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    if train_end >= monitor_start - 50:
        raise ValueError(
            "n is too small to form disjoint proxy train, validation and monitor slices"
        )
    validation_end = monitor_start
    proxy = DecisionLossProxy(
        clip=max(fn, fp) + config.harm_margin,
        seed=seed,
        update_every=config.proxy_update_every,
    )
    proxy.fit(
        x[:train_end],
        z_centered[:train_end],
        x[train_end:validation_end],
        z_centered[train_end:validation_end],
    )
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(
        x[:train_end], y[:train_end]
    )
    # Calibrate the harm onset from evaluator-known expected losses, never learner inputs.
    sample_path_onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    # Population-null controls remain null even when a finite covariate path has an
    # oracle-average excess above epsilon. Keep that pathwise event as a diagnostic.
    onset = statistical_harm_onset(scenario.name, sample_path_onset)
    rows = []
    methods = config.method_subset or (
        METHODS if config.heterogeneous_label_costs else METHODS[:-2]
    )
    for method in methods:
        rows.append(
            _monitor_method(
                method=method,
                seed=seed,
                config=config,
                scenario=scenario,
                x=x,
                z_centered=z_centered,
                expected_difference=expected_difference,
                proxy_template=proxy,
                classifier=classifier,
                train_end=train_end,
                validation_end=validation_end,
                monitor_start=monitor_start,
                harm_onset=onset,
                sample_path_material_harm=sample_path_onset is not None,
                sample_path_harm_onset=sample_path_onset,
                label_costs=label_costs,
                contrast_zero=contrast_zero,
                contrast_one=contrast_one,
            )
        )
    oracle_expected = np.minimum(fp * (1 - p), fn * p)
    predictive_probability = classifier.predict_proba(x[monitor_start:])[:, 1]
    predictive_brier = float(np.mean((predictive_probability - y[monitor_start:]) ** 2))
    mean_oracle_regret = float(
        np.mean(current_expected[monitor_start:] - oracle_expected[monitor_start:])
    )
    for row in rows:
        row["known_change_times"] = timing["change_times"]
        row["mean_predictive_brier"] = predictive_brier
        row["mean_current_expected_cost"] = float(current_expected[monitor_start:].mean())
        row["mean_reference_expected_cost"] = float(reference_expected[monitor_start:].mean())
        row["mean_oracle_expected_cost"] = float(oracle_expected[monitor_start:].mean())
        row["mean_synthetic_oracle_regret"] = mean_oracle_regret
    return rows


def _plots(metrics: pd.DataFrame, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    aggregate = metrics.groupby(["scenario", "method"], as_index=False).agg(
        mmd=("feature_mmd_mean", "mean"),
        harm=("mean_expected_decision_harm", "mean"),
        false_rate=("single_e_false_escalation", "mean"),
        detection=("single_e_detected", "mean"),
        delay=("single_e_delay", "median"),
        labels=("labels_queried", "mean"),
        estimation_error=("stream_mean_estimation_error", lambda x: np.sqrt(np.mean(x**2))),
        net_cost=("cumulative_net_cost_vs_reference", "mean"),
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    label_offsets = {
        "benign_nuisance": (-112, 9),
        "boundary_local_harm": (30, 20),
        "harmful_adaptation": (30, -24),
        "recurring_regimes": (30, -2),
        "residual_variance": (9, 7),
        "stationary": (9, 5),
    }
    for scenario, group in aggregate.groupby("scenario"):
        row = group.iloc[0]
        ax.scatter(row.mmd, row.harm, label=scenario, s=65)
        ax.annotate(
            scenario.replace("_", " "),
            (row.mmd, row.harm),
            xytext=label_offsets[scenario],
            textcoords="offset points",
            fontsize=7,
            arrowprops={"arrowstyle": "-", "color": "0.45", "lw": 0.6},
        )
    ax.axhline(0.1, color="black", linestyle="--", linewidth=0.8, label="harm margin")
    ax.set(xlabel="Unbiased RBF MMD² estimate", ylabel="Expected deployed − reference cost")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(output / "shift_vs_harm.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for method, group in aggregate.groupby("method"):
        axes[0].plot(group.scenario, group.false_rate, marker="o", label=method)
        axes[1].plot(group.scenario, group.delay, marker="o", label=method)
    axes[0].set_ylabel("Observed false escalation rate")
    axes[1].set_ylabel("Median delay among detected streams")
    for ax in axes:
        ax.tick_params(axis="x", rotation=40)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(output / "false_alarm_delay.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for method, group in aggregate.groupby("method"):
        ax.scatter(group.labels, group.estimation_error, label=method, s=45)
    ax.set(
        xlabel="Mean labels queried per stream", ylabel="RMSE of estimated stream-mean excess cost"
    )
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / "label_efficiency.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    pivot = aggregate.pivot(index="scenario", columns="method", values="net_cost")
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("Expected excess decision cost + imposed label cost")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "cumulative_net_regret.png", dpi=170)
    plt.close(fig)

    cost_summary = metrics.groupby("method", as_index=False).agg(
        mean_labels=("labels_queried", "mean"),
        estimation_rmse=("stream_mean_estimation_error", lambda x: np.sqrt(np.mean(x**2))),
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    for row in cost_summary.itertuples(index=False):
        label_spend = row.mean_labels * metrics.label_cost.mean()
        ax.scatter(label_spend, row.estimation_rmse, s=60)
        ax.annotate(row.method, (label_spend, row.estimation_rmse), fontsize=7)
    ax.set(
        xlabel="Mean label spend per stream",
        ylabel="RMSE of stream-mean paired-cost estimate",
        title="Evidence efficiency under the configured label price",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "cost_pareto.png", dpi=170)
    plt.close(fig)


def run_experiment(config: DiveExperimentConfig, output: Path) -> Path:
    config.validate()
    requested_device = config.device
    resolved = resolve_device(config.device, n=config.n, d=config.d, chunk_size=5000)
    config = DiveExperimentConfig(**{**asdict(config), "device": resolved})
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    if (metrics_dir / "method_comparison.parquet").exists():
        raise FileExistsError(f"refusing to overwrite existing benchmark: {metrics_dir}")
    for directory in (metrics_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)
    rows = []
    scenarios = tuple(
        scenario
        for scenario in SCENARIOS
        if not config.scenario_subset or scenario.name in config.scenario_subset
    )
    methods = config.method_subset or (
        METHODS if config.heterogeneous_label_costs else METHODS[:-2]
    )
    for scenario in scenarios:
        for replicate in range(config.seeds):
            seed = config.seed_offset + 100_000 + replicate
            print(
                f"scenario={scenario.name} replicate={replicate + 1}/{config.seeds} "
                f"seed={seed} device={config.device}",
                flush=True,
            )
            rows.extend(_one_stream(scenario, seed, config))
    metrics = pd.DataFrame(rows)
    metrics = apply_population_null_classification(metrics)
    metrics.to_parquet(metrics_dir / "method_comparison.parquet", index=False)
    _plots(metrics, figures_dir)
    summary = metrics.groupby(["scenario", "method"], as_index=False).agg(
        streams=("seed", "count"),
        false_escalation_rate=("single_e_false_escalation", "mean"),
        detection_rate=("single_e_detected", "mean"),
        median_delay=("single_e_delay", "median"),
        mean_query_rate=("observed_query_rate", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_label_spend=("realized_label_spend", "mean"),
        mean_estimation_error=("stream_mean_estimation_error", "mean"),
        rmse_stream_mean=("stream_mean_estimation_error", lambda x: np.sqrt(np.mean(x**2))),
        mean_proxy_rmse=("proxy_prequential_rmse", "mean"),
        mean_expected_harm=("mean_expected_decision_harm", "mean"),
        mean_predictive_brier=("mean_predictive_brier", "mean"),
        mean_oracle_regret=("mean_synthetic_oracle_regret", "mean"),
        mean_net_cost=("cumulative_net_cost_vs_reference", "mean"),
    )
    lines = [
        "# DIVE initial evidence-acquisition comparison",
        "",
        f"Generated from {config.seeds} paired evaluation seeds for each of {len(scenarios)} scenarios. Resolved device: `{config.device}`.",
        "",
        "## Implemented variants",
        "",
        "- `full_feedback`: all monitor-period labels; direct paired-cost e-process.",
        "- `uniform_direct`: uniform Bernoulli queries and direct inverse-propensity paired-cost estimates.",
        "- `uniform_proxy`: uniform queries with prediction-powered correction.",
        "- `pprm_reliance_analogue`: uniform queries with a predictable historical plug-in scalar for proxy reliance. This is not the full PPRM algorithm or its confidence-sequence construction.",
        "- `uncertainty_proxy`: entropy-based query propensities calibrated on the pre-monitor validation slice.",
        "- `variance_proxy`: query scores proportional to the square root of a held-out model for proxy residual second moments.",
        "- `decision_value_proxy`: a heuristic that increases sampling near the harm margin when proxy residual uncertainty is high.",
        "- `evidence_growth_proxy`: selects the predictable query propensity by maximizing a pre-monitor outcome model's stake-weighted expected log-wealth increment under the same expected label budget. The per-event objective is concave and solved through a dual budget multiplier. This is a model-based allocation rule, not an e-process validity result or a power-optimality claim.",
        f"- `evidence_growth_stabilized_proxy`: mixes evidence-growth propensities with uniform sampling at weight `{_evidence_uniform_mix_weight(config):.3f}`. The expected query-rate drift under arbitrary feature shift is bounded by the configured tolerance `{config.evidence_rate_stability_tolerance:g}`; this robustification may also remove most allocation adaptivity.",
        *(
            [
                "- `cost_variance_proxy`: the clipped allocation proportional to `sqrt(vhat(X)/k_label(X))`, calibrated to the same expected validation label spend as uniform sampling. This is the classical cost-constrained variance optimum, not a new theorem. The synthetic label tariff is known from a learner-visible covariate and may shift out of time.",
                f"- `cost_stabilized_proxy`: the largest cost-aware Neyman mixture weight satisfying a per-event expected-spend drift tolerance of {config.cost_stability_tolerance:g}, combined with a spend-neutral propensity. The mixture bound is elementary, not a novelty claim.",
            ]
            if config.heterogeneous_label_costs
            else []
        ),
        "",
        "All fitted proxies and query multipliers use only the pre-monitor training/validation rows. Proxy refits for updating policies use queried outcomes only after they arrive; the expected-evidence policy freezes its decision-loss proxy over the monitor interval so the validation-calibrated objective does not change. Query outcomes are immediate in this first experiment. This monitor benchmark takes no action after alarms; candidate promotion is evaluated in a separate forward-time experiment.",
        "",
        "## Preliminary results",
        "",
        f"These are descriptive paired-stream Monte Carlo results, not confirmatory inference. `rmse_stream_mean` is computed across independent seeds. False-escalation proportions have only {config.seeds} stream replicates per cell. The change-aware mixture is reported in the Parquet artifact; this report's table summarizes the single-start process.",
        "",
        "| Scenario | Method | False escalation | Detection | Median delay | Labels/stream | Realized label spend/stream | Stream-mean RMSE | Proxy RMSE | Predictive Brier | Expected harm | Oracle regret |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        delay = "—" if pd.isna(row.median_delay) else f"{row.median_delay:.0f}"
        lines.append(
            f"| {row.scenario} | {row.method} | {row.false_escalation_rate:.3f} | {row.detection_rate:.3f} | {delay} | {row.mean_labels:.1f} | {row.mean_label_spend:.1f} | {row.rmse_stream_mean:.4f} | {row.mean_proxy_rmse:.4f} | {row.mean_predictive_brier:.4f} | {row.mean_expected_harm:.4f} | {row.mean_oracle_regret:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Assumptions and limits",
            "",
            f"The proposed conditional null is that the mean of paired deployed-minus-reference cost, centered by epsilon={config.harm_margin:g}, is nonpositive given prior information. Query indicators are Bernoulli with recorded predictable propensities; labels are immediate; costs are bounded; query probabilities are bounded below by the configured floor for proxy-corrected methods. The proxy is outcome-free at prediction time, and every online refit occurs only after queried feedback.",
            "When heterogeneous label costs are enabled, the tariff is a known function of the last learner-visible feature and lies in [0.5, 2.5]. Sparse-query methods are matched to expected validation spend, while monitor-period realized spend can change under covariate shift. This is neither a fixed label-count budget nor a guaranteed spend cap. Cost-variance allocation is the classical clipped Neyman solution for estimator variance under known costs; its improvement in detection delay or decision utility is not established here.",
            "",
            "The estimator correction is unbiased under conditional Bernoulli sampling and positive known propensities, even when the proxy is misspecified. The e-process uses a fixed worst-case bound for each query design, preserving the stated unconditional conditional-mean null when query probabilities depend on current features. Empirical null crossing rates are diagnostics, not the validity proof. The variance and decision-value acquisition policies are heuristics; no optimality or novelty claim is made.",
            "Stationary and benign-nuisance streams are population-null controls, independently verified below epsilon. Their finite-stream oracle averages can cross epsilon by chance; those pathwise flags are retained as `sample_path_material_harm` and are not counted as true alternatives. Every monitor alarm on these population-null controls counts as a false escalation. For shifted alternatives, evaluator-known finite-regime oracle averages continue to define the sample-specific harm onset.",
            "",
            f"`cumulative_net_cost_vs_reference` adds an imposed label price of {config.label_cost:g} per acquired label to evaluator-known expected excess decision cost. This is sensitivity-analysis bookkeeping, not a validated real-world label price. This monitoring experiment takes no action after an alarm, so it cannot establish controller value or reduced harm. Candidate certification is evaluated separately in `promotion_comparison.md`; the one-step controller is not yet integrated into a closed-loop intervention benchmark.",
            "",
            "## Artifacts",
            "",
            "`metrics/method_comparison.parquet` contains one row per seed, scenario, and method, including query propensities, e-process alarms, delay, proxy diagnostics, estimator error, MMD, predictive Brier loss, paired expected harm, synthetic oracle regret, and label-adjusted cost. Figures are generated from these rows.",
            "",
        ]
    )
    (reports_dir / "method_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "experiment": "dive_initial_evidence_acquisition",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "requested_device": requested_device,
        "resolved_device": config.device,
        "environment": environment(),
        "methods": list(methods),
        "scenario_names": [scenario.name for scenario in scenarios],
        "assumption_summary": [
            "Immediate labels in this first simulation; delayed-label support is not evaluated.",
            "Query propensity is chosen from current features and pre-monitor fitted models before the outcome.",
            "Paired decision costs are observed for both policies on the same outcome; this does not cover action-dependent outcomes.",
            "E-process validity requires the stated conditional-mean null, bounded corrected increments, and predictable stakes.",
        ],
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    refresh_report_with_uncertainty(output)
    finalize_manifest(output)
    return output


def _wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    if trials <= 0:
        return float("nan"), float("nan")
    z = float(norm.ppf(0.5 + confidence / 2))
    rate = successes / trials
    denominator = 1 + z**2 / trials
    center = (rate + z**2 / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z**2 / (4 * trials**2)) / denominator
    return float(max(0.0, center - radius)), float(min(1.0, center + radius))


def _mean_interval(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return float("nan"), float("nan")
    margin = float(student_t.ppf(0.5 + confidence / 2, len(values) - 1)) * float(
        values.std(ddof=1) / np.sqrt(len(values))
    )
    mean = float(values.mean())
    return mean - margin, mean + margin


def _rmse_bootstrap_interval(values: np.ndarray, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(2500, len(values)))
    rmses = np.sqrt(np.mean(np.square(values[draws]), axis=1))
    low, high = np.quantile(rmses, [0.025, 0.975])
    return float(low), float(high)


def refresh_report_with_uncertainty(output: Path) -> None:
    """Add independent-stream uncertainty intervals to the generated report."""
    metrics = pd.read_parquet(output / "metrics" / "method_comparison.parquet")
    lines = [
        "| Scenario | Method | False escalation (95% Wilson) | Detection on harmful streams (95% Wilson) | Delay among detected | Labels/stream (95% t CI) | Realized label spend/stream (95% t CI) | Stream-mean RMSE (95% bootstrap) | Proxy RMSE | Predictive Brier | Expected harm (95% t CI) | Oracle regret | Net cost vs ref (95% t CI) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (scenario_name, method), group in metrics.groupby(["scenario", "method"], sort=True):
        false_count = int(group["single_e_false_escalation"].sum())
        false_low, false_high = _wilson_interval(false_count, len(group))
        harmful = group[group["material_harm"]]
        detected_count = int(harmful["single_e_detected"].sum())
        detect_low, detect_high = _wilson_interval(detected_count, len(harmful))
        label_mean = float(group["labels_queried"].mean())
        label_low, label_high = _mean_interval(group["labels_queried"].to_numpy())
        if "realized_label_spend" in group:
            spend_values = group["realized_label_spend"].to_numpy(dtype=float)
        elif "expected_label_spend" in group:
            spend_values = group["expected_label_spend"].to_numpy(dtype=float)
        else:
            spend_values = group["labels_queried"].to_numpy(dtype=float) * group[
                "label_cost"
            ].to_numpy(dtype=float)
        spend_mean = float(spend_values.mean())
        spend_low, spend_high = _mean_interval(spend_values)
        error = group["stream_mean_estimation_error"].to_numpy()
        rmse = float(np.sqrt(np.mean(error**2)))
        interval_seed = sum(ord(char) for char in f"{scenario_name}:{method}")
        rmse_low, rmse_high = _rmse_bootstrap_interval(error, interval_seed)
        harm = group["mean_expected_decision_harm"].to_numpy()
        harm_mean = float(np.mean(harm))
        harm_low, harm_high = _mean_interval(harm)
        net_cost = group["cumulative_net_cost_vs_reference"].to_numpy()
        net_cost_mean = float(np.mean(net_cost))
        net_cost_low, net_cost_high = _mean_interval(net_cost)
        delay = harmful.loc[harmful["single_e_detected"], "single_e_delay"].median()
        delay_text = "—" if pd.isna(delay) else f"{delay:.0f}"
        false_text = (
            "—"
            if not np.isfinite(false_low)
            else f"{false_count / len(group):.2f} [{false_low:.2f},{false_high:.2f}]"
        )
        detect_text = (
            "—"
            if len(harmful) == 0
            else f"{detected_count / len(harmful):.2f} [{detect_low:.2f},{detect_high:.2f}]"
        )
        lines.append(
            f"| {scenario_name} | {method} | {false_text} | {detect_text} | {delay_text} | "
            f"{label_mean:.1f} [{label_low:.1f},{label_high:.1f}] | "
            f"{spend_mean:.1f} [{spend_low:.1f},{spend_high:.1f}] | "
            f"{rmse:.4f} [{rmse_low:.4f},{rmse_high:.4f}] | "
            f"{group['proxy_prequential_rmse'].mean():.4f} | "
            f"{group['mean_predictive_brier'].mean():.4f} | "
            f"{harm_mean:.4f} [{harm_low:.4f},{harm_high:.4f}] | "
            f"{group['mean_synthetic_oracle_regret'].mean():.4f} | "
            f"{net_cost_mean:.2f} [{net_cost_low:.2f},{net_cost_high:.2f}] |"
        )
    report_path = output / "reports" / "method_comparison.md"
    report = report_path.read_text(encoding="utf-8")
    interval_note = (
        "Independent seeds are the inferential units. False-escalation intervals use Wilson's "
        "method over all population-null control streams and pre-onset alternative streams; "
        "detection intervals use only streams with evaluator-known harm onsets. Finite-stream "
        "oracle excursions within population-null controls are recorded separately. Labels and "
        "expected harm use t intervals across seeds; stream-mean RMSE uses a "
        "deterministic percentile bootstrap over seeds. Nondetections remain in the detection "
        "denominator and are not discarded from the Parquet data."
    )
    legacy_interval_note = (
        "Independent seeds are the inferential units. False-escalation intervals use Wilson's "
        "method over all streams; detection intervals use only evaluator-labeled material-harm "
        "streams. Labels and expected harm use t intervals across seeds; stream-mean RMSE uses a "
        "deterministic percentile bootstrap over seeds. Nondetections remain in the detection "
        "denominator and are not discarded from the Parquet data."
    )
    report = report.replace(legacy_interval_note + "\n\n", "")
    report = report.replace(interval_note + "\n\n", "")
    start = report.index("| Scenario | Method |", report.index("## Preliminary results"))
    end = report.index("\n\n## Assumptions and limits", start)
    report = report[:start] + interval_note + "\n\n" + "\n".join(lines) + report[end:]
    if "population_null_control" in metrics:
        controls = metrics.loc[metrics.population_null_control]
        audit_lines = [
            "## Population-null control audit",
            "",
            "Finite-stream oracle flags are shown separately from the population-null test result.",
            "",
            "| Scenario | Method | Population-null alarms / streams | Finite-stream oracle flags / streams |",
            "|---|---|---:|---:|",
        ]
        for (scenario_name, method), group in controls.groupby(["scenario", "method"], sort=True):
            alarms = int(group["single_e_alarm"].sum())
            path_flags = int(group["sample_path_material_harm"].sum())
            audit_lines.append(
                f"| {scenario_name} | {method} | {alarms}/{len(group)} | {path_flags}/{len(group)} |"
            )
        audit_marker = "\n\n## Population-null control audit"
        if audit_marker in report:
            audit_start = report.index(audit_marker)
            assumptions_start = report.index("\n\n## Assumptions and limits", audit_start)
            report = report[:audit_start] + report[assumptions_start:]
        marker = "\n\n## Assumptions and limits"
        if marker in report:
            report = report.replace(marker, "\n\n" + "\n".join(audit_lines) + marker, 1)
    report_path.write_text(report, encoding="utf-8")


def finalize_manifest(output: Path) -> None:
    manifest_path = output / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    def file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    artifacts = [
        path
        for folder in (output / "metrics", output / "reports", output / "figures")
        for path in folder.iterdir()
        if path.is_file() and path.name != manifest_path.name
    ]
    sources = sorted(Path("src/shiftlab/dive").glob("*.py"))
    sources.append(Path("src/shiftlab/decision_harm_experiment.py"))
    manifest["sha256"] = {
        "artifacts": {str(path.relative_to(output)): file_hash(path) for path in sorted(artifacts)},
        "source_files": {str(path): file_hash(path) for path in sources if path.exists()},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20261022)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--query-rate", type=float, default=0.10)
    parser.add_argument("--label-cost", type=float, default=0.01)
    parser.add_argument(
        "--heterogeneous-label-costs",
        action="store_true",
        help="evaluate cost-constrained query allocation using a known covariate-dependent label tariff",
    )
    parser.add_argument("--cost-stability-tolerance", type=float, default=0.05)
    parser.add_argument("--evidence-rate-stability-tolerance", type=float, default=0.01)
    parser.add_argument("--scenarios", nargs="+", choices=[scenario.name for scenario in SCENARIOS])
    parser.add_argument("--methods", nargs="+", choices=METHODS)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="auto")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(argv)
    config = DiveExperimentConfig(
        seeds=2 if args.quick else args.seeds,
        n=1600 if args.quick else args.n,
        d=args.d,
        seed_offset=args.seed_offset,
        query_rate=args.query_rate,
        label_cost=args.label_cost,
        heterogeneous_label_costs=args.heterogeneous_label_costs,
        cost_stability_tolerance=args.cost_stability_tolerance,
        evidence_rate_stability_tolerance=args.evidence_rate_stability_tolerance,
        scenario_subset=tuple(args.scenarios or ()),
        method_subset=tuple(args.methods or ()),
        device=args.device,
    )
    output = args.output or Path("outputs")
    print(run_experiment(config, output), flush=True)


if __name__ == "__main__":
    main()
