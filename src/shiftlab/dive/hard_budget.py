"""Forward-time comparison of query policies under a common hard label-dollar cap."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, replace
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
    PPIBlockConfidenceSequence,
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
)
from .estimators import (
    pprm_adaptive_reliance,
    pprm_block_estimate,
    prediction_powered_bound,
    prediction_powered_estimate,
)
from .evaluation import apply_population_null_classification
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
    ExactMixtureGrowthQueryPolicy,
    RobustMixtureGrowthQueryPolicy,
    cost_mixture_weight_for_tolerance,
    expected_cost_drift_bound,
    mix_with_cost_neutral,
)

HARD_BUDGET_METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
    "exact_mixture_growth_proxy",
    "robust_mixture_growth_proxy",
    "pprm_block_adaptive",
    "uniform_proxy_frozen",
)
DEFAULT_HARD_BUDGET_METHODS = HARD_BUDGET_METHODS[:-2]
PPRM_BLOCK_SIZE = 20
PPRM_LABELS_PER_BLOCK = 4
PPRM_MAX_RELIANCE = 1.0
PPRM_INITIAL_RELIANCE = 1.0
MULTISCALE_STAKES = tuple(float(value) for value in np.geomspace(1 / 1024, 0.99, 13))
PROTECTED_EXPLORATION_STAKES = tuple(float(value) for value in np.geomspace(1 / 1024, 0.04, 8))
PROTECTED_STAKES = (0.05, 0.10, 0.20, 0.40, 0.80, *PROTECTED_EXPLORATION_STAKES)
PROTECTED_WEIGHTS = (0.18,) * 5 + (0.10 / len(PROTECTED_EXPLORATION_STAKES),) * len(
    PROTECTED_EXPLORATION_STAKES
)
HARD_BUDGET_MONITOR_COMPARATORS = ("variance_adaptive", "pm_eb")


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
    exact_growth_adaptive_weight: float = 1.0
    robust_growth_probability_radius: float = 0.0
    monitor_comparators: tuple[str, ...] = ()
    max_label_cost: float = 2.5
    common_eprocess_bound: bool = False
    scenario_severity: float | None = None
    change_fraction: float = 0.5
    device: str = "auto"
    scenario_subset: tuple[str, ...] = (
        "stationary",
        "benign_nuisance",
        "boundary_local_harm",
    )
    method_subset: tuple[str, ...] = DEFAULT_HARD_BUDGET_METHODS

    def validate(self) -> HardBudgetConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if not 0 < self.alpha < 1 or self.harm_margin < 0:
            raise ValueError("alpha must lie in (0,1) and harm_margin must be nonnegative")
        if not 0 < self.q_min <= self.budget_rate <= self.q_max <= 1:
            raise ValueError("require 0 < q_min <= budget_rate <= q_max <= 1")
        if self.max_label_cost <= 0 or not np.isfinite(self.max_label_cost):
            raise ValueError("max_label_cost must be finite and positive")
        if self.scenario_severity is not None and (
            not np.isfinite(self.scenario_severity) or not 0 <= self.scenario_severity <= 5
        ):
            raise ValueError("scenario_severity must lie in [0, 5]")
        if not np.isfinite(self.change_fraction) or not 0 < self.change_fraction < 1:
            raise ValueError("change_fraction must lie in (0, 1)")
        if not isinstance(self.common_eprocess_bound, bool):
            raise TypeError("common_eprocess_bound must be boolean")
        if self.cost_stability_tolerance < 0 or not np.isfinite(self.cost_stability_tolerance):
            raise ValueError("cost_stability_tolerance must be finite and nonnegative")
        if (
            not np.isfinite(self.exact_growth_adaptive_weight)
            or not 0 <= self.exact_growth_adaptive_weight <= 1
        ):
            raise ValueError("exact_growth_adaptive_weight must lie in [0, 1]")
        if (
            not np.isfinite(self.robust_growth_probability_radius)
            or not 0 <= self.robust_growth_probability_radius <= 1
        ):
            raise ValueError("robust_growth_probability_radius must lie in [0, 1]")
        if len(set(self.monitor_comparators)) != len(self.monitor_comparators) or not set(
            self.monitor_comparators
        ) <= set(HARD_BUDGET_MONITOR_COMPARATORS):
            raise ValueError("monitor_comparators must contain unique registered comparator names")
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
    sample_path_material_harm: bool,
    sample_path_harm_onset: int | None,
    common_uniforms: np.ndarray,
    contrast_zero: np.ndarray,
    contrast_one: np.ndarray,
) -> dict[str, object]:
    validation_end = monitor_start
    validation_x = x[train_end:validation_end]
    validation_costs = label_costs[train_end:validation_end]
    validation_probability = classifier.predict_proba(validation_x)[:, 1]
    validation_uncertainty = _entropy(validation_probability)
    proxy = copy.deepcopy(proxy_template)
    proxy_updates_enabled = method != "uniform_proxy_frozen"

    query_kind = {
        "uniform_proxy": "uniform",
        "uniform_proxy_frozen": "uniform",
        "variance_proxy": "variance",
        "decision_value_proxy": "decision_value",
        "cost_variance_proxy": "cost_variance",
        "cost_stabilized_proxy": "cost_variance",
        "exact_mixture_growth_proxy": "exact_mixture_growth",
        "robust_mixture_growth_proxy": "robust_mixture_growth",
    }[method]
    if query_kind in {"exact_mixture_growth", "robust_mixture_growth"}:
        process_bound = prediction_powered_bound(proxy.clip, config.q_min)
        policy_class = (
            RobustMixtureGrowthQueryPolicy
            if query_kind == "robust_mixture_growth"
            else ExactMixtureGrowthQueryPolicy
        )
        policy_kwargs = {
            "target_rate": config.budget_rate,
            "q_min": config.q_min,
            "q_max": config.q_max,
            "bound": process_bound,
            "initial_stake": BoundedMeanEProcess(bound=process_bound).predictable_stake,
        }
        if query_kind == "robust_mixture_growth":
            policy_kwargs["probability_radius"] = config.robust_growth_probability_radius
        policy = policy_class(**policy_kwargs).fit_multiplier(
            proxy=proxy.predict(validation_x),
            probability_positive=validation_probability,
            contrast_zero=contrast_zero[train_end:validation_end],
            contrast_one=contrast_one[train_end:validation_end],
            label_costs=validation_costs,
        )
    else:
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
    exact_growth_spend_drift_bound = None
    if method == "exact_mixture_growth_proxy" and config.exact_growth_adaptive_weight < 1.0:
        exact_growth_spend_drift_bound = expected_cost_drift_bound(
            budget_per_event=budget_per_event,
            mixture_weight=config.exact_growth_adaptive_weight,
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
    comparator_processes = {}
    for comparator in config.monitor_comparators:
        process_class = {
            "variance_adaptive": PredictableVarianceAdaptiveEProcess,
            "pm_eb": PredictablePlugInEmpiricalBernsteinEProcess,
        }[comparator]
        comparator_processes[comparator] = {
            "process": process_class(
                bound=prediction_powered_bound(proxy.clip, minimum_propensity),
                alpha=config.alpha,
            ),
            "first_alarm": None,
        }
    monitor_x = x[monitor_start:]
    proxy_values = proxy.predict(monitor_x)
    residual_second_moments = proxy.predict_residual_second_moment(monitor_x)
    uncertainty_values = _entropy(classifier.predict_proba(monitor_x)[:, 1])
    positive_probability_values = classifier.predict_proba(x)[:, 1]
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
        if method in {"exact_mixture_growth_proxy", "robust_mixture_growth_proxy"}:
            q_adaptive = float(
                policy.probabilities(
                    proxy=np.asarray([h_now]),
                    probability_positive=np.asarray([positive_probability_values[index]]),
                    contrast_zero=np.asarray([contrast_zero[index]]),
                    contrast_one=np.asarray([contrast_one[index]]),
                    effective_stake=process.predictable_stake,
                    label_costs=np.asarray([cost_now]),
                )[0]
            )
        else:
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
        elif method == "exact_mixture_growth_proxy" and config.exact_growth_adaptive_weight < 1.0:
            propensity = float(
                mix_with_cost_neutral(
                    np.asarray([q_adaptive]),
                    np.asarray([cost_now]),
                    budget_per_event=budget_per_event,
                    mixture_weight=config.exact_growth_adaptive_weight,
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
        for state in comparator_processes.values():
            comparator_value = state["process"].update(estimate)
            if state["first_alarm"] is None and comparator_value >= threshold:
                state["first_alarm"] = offset
        if queried and proxy_updates_enabled:
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
    row = {
        "scenario": scenario.name,
        "scenario_severity": scenario.severity,
        "change_fraction": config.change_fraction,
        "seed": seed,
        "method": method,
        "proxy_updates_enabled": proxy_updates_enabled,
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
        "exact_growth_adaptive_weight": (
            config.exact_growth_adaptive_weight if method == "exact_mixture_growth_proxy" else None
        ),
        "exact_growth_expected_spend_drift_bound": exact_growth_spend_drift_bound,
        "robust_growth_probability_radius": (
            config.robust_growth_probability_radius
            if method == "robust_mixture_growth_proxy"
            else None
        ),
        "material_harm": harm_onset is not None,
        "population_null_control": scenario.name in POPULATION_NULL_CONTROLS,
        "sample_path_material_harm": sample_path_material_harm,
        "sample_path_harm_onset_relative": sample_path_harm_onset,
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
    for comparator, state in comparator_processes.items():
        alarm_time = state["first_alarm"]
        comparator_detected = (
            alarm_time is not None and harm_onset is not None and alarm_time >= harm_onset
        )
        comparator_false = alarm_time is not None and (
            harm_onset is None or alarm_time < harm_onset
        )
        row.update(
            {
                f"{comparator}_detected": bool(comparator_detected),
                f"{comparator}_false_escalation": bool(comparator_false),
                f"{comparator}_alarm_time": alarm_time,
                f"{comparator}_delay": (
                    int(alarm_time - harm_onset)
                    if comparator_detected and alarm_time is not None and harm_onset is not None
                    else None
                ),
            }
        )
    return row


def _one_pprm_block_method(
    *,
    seed: int,
    scenario,
    config: HardBudgetConfig,
    x: np.ndarray,
    centered_cost_difference: np.ndarray,
    expected_cost_difference: np.ndarray,
    label_costs: np.ndarray,
    proxy_template: DecisionLossProxy,
    monitor_start: int,
    harm_onset: int | None,
    sample_path_material_harm: bool,
    sample_path_harm_onset: int | None,
    common_uniforms: np.ndarray,
) -> dict[str, object]:
    """Compare a predictable plug-in-reliance PPI sequence at a 20% label rate."""
    if PPRM_BLOCK_SIZE % PPRM_LABELS_PER_BLOCK:
        raise RuntimeError("PPRM block must contain an integer labeled fraction")
    event_count = len(x) - monitor_start
    if event_count < PPRM_BLOCK_SIZE:
        raise ValueError("monitor stream must contain at least one complete PPI block")
    cost_bound = max(scenario.fn_cost, scenario.fp_cost)
    if cost_bound <= 0:
        raise ValueError("paired decision-cost bound must be positive")
    eta = PPRM_INITIAL_RELIANCE
    threshold = (config.harm_margin + cost_bound) / (2 * cost_bound)
    monitor = PPIBlockConfidenceSequence(
        max_reliance=PPRM_MAX_RELIANCE,
        threshold=threshold,
        alpha=config.alpha,
    )
    proxy = copy.deepcopy(proxy_template)  # frozen before the first monitor block
    predicted_centered = proxy.predict(x[monitor_start:])
    proxy_raw = np.clip(predicted_centered + config.harm_margin, -cost_bound, cost_bound)
    proxy_normalized = (proxy_raw + cost_bound) / (2 * cost_bound)
    true_normalized = (
        centered_cost_difference[monitor_start:] + config.harm_margin + cost_bound
    ) / (2 * cost_bound)
    validation_start = max(100, int(config.n * 0.125))
    validation_end = monitor_start
    budget_per_event = config.budget_rate * float(
        label_costs[validation_start:validation_end].mean()
    )
    budget = budget_per_event * event_count
    remaining = budget
    spent = 0.0
    expected_spend = 0.0
    queried_count = 0
    processed = 0
    estimates: list[float] = []
    block_truths: list[float] = []
    block_expected: list[float] = []
    block_reliances: list[float] = []
    historical_labeled: list[float] = []
    historical_labeled_proxy: list[float] = []
    historical_unlabeled_proxy: list[float] = []
    alarm_time: int | None = None
    stop_reason = "end_of_stream"

    for relative_start in range(0, event_count - PPRM_BLOCK_SIZE + 1, PPRM_BLOCK_SIZE):
        if remaining + 1e-12 < PPRM_LABELS_PER_BLOCK * config.max_label_cost:
            stop_reason = "budget_reserve"
            break
        relative_end = relative_start + PPRM_BLOCK_SIZE
        absolute_start = monitor_start + relative_start
        absolute_end = monitor_start + relative_end
        block_costs = label_costs[absolute_start:absolute_end]
        block_uniforms = common_uniforms[absolute_start:absolute_end]
        labeled_local = np.argpartition(block_uniforms, PPRM_LABELS_PER_BLOCK - 1)[
            :PPRM_LABELS_PER_BLOCK
        ]
        unlabeled_local = np.ones(PPRM_BLOCK_SIZE, dtype=bool)
        unlabeled_local[labeled_local] = False
        labeled_indices = absolute_start + labeled_local
        labeled_spend = float(label_costs[labeled_indices].sum())
        if labeled_spend > remaining + 1e-12:
            # The reserve check covers the maximum tariff; reaching this branch is an invariant failure.
            raise RuntimeError("PPRM block selection exceeded its reserved label-dollar budget")
        labeled_z = true_normalized[labeled_local]
        labeled_proxy = proxy_normalized[relative_start:relative_end][labeled_local]
        unlabeled_proxy = proxy_normalized[relative_start:relative_end][unlabeled_local]
        estimate = pprm_block_estimate(
            labeled_z,
            labeled_proxy,
            unlabeled_proxy,
            reliance=eta,
        )
        block_reliances.append(eta)
        crossed = monitor.update(estimate)
        estimates.append(-cost_bound + 2 * cost_bound * estimate - config.harm_margin)
        block_truths.append(float(centered_cost_difference[absolute_start:absolute_end].mean()))
        block_expected.append(float(expected_cost_difference[absolute_start:absolute_end].mean()))
        spent += labeled_spend
        remaining -= labeled_spend
        queried_count += PPRM_LABELS_PER_BLOCK
        historical_labeled.extend(labeled_z.tolist())
        historical_labeled_proxy.extend(labeled_proxy.tolist())
        historical_unlabeled_proxy.extend(unlabeled_proxy.tolist())
        eta = pprm_adaptive_reliance(
            np.asarray(historical_labeled),
            np.asarray(historical_labeled_proxy),
            np.asarray(historical_unlabeled_proxy),
            max_reliance=PPRM_MAX_RELIANCE,
            fallback_reliance=PPRM_INITIAL_RELIANCE,
        )
        expected_spend += (PPRM_LABELS_PER_BLOCK / PPRM_BLOCK_SIZE) * float(block_costs.sum())
        processed += PPRM_BLOCK_SIZE
        if crossed and alarm_time is None:
            alarm_time = relative_end - 1

    if processed < event_count and stop_reason == "end_of_stream":
        stop_reason = "incomplete_block"
    harm_reached = harm_onset is not None and harm_onset < processed
    detected = alarm_time is not None and harm_onset is not None and alarm_time >= harm_onset
    false_escalation = alarm_time is not None and (harm_onset is None or alarm_time < harm_onset)
    errors = np.asarray(estimates) - np.asarray(block_truths)
    return {
        "scenario": scenario.name,
        "scenario_severity": scenario.severity,
        "change_fraction": config.change_fraction,
        "seed": seed,
        "method": "pprm_block_adaptive",
        "proxy_updates_enabled": False,
        "hard_budget": budget,
        "realized_label_spend": spent,
        "budget_remaining": remaining,
        "budget_utilization": spent / budget,
        "budget_respected": spent <= budget + 1e-9,
        "predictable_spend_compensator_until_stop": expected_spend,
        "eprocess_minimum_propensity": PPRM_LABELS_PER_BLOCK / PPRM_BLOCK_SIZE,
        "labels_queried": queried_count,
        "processed_events": processed,
        "monitor_fraction_processed": processed / event_count,
        "stop_reason": stop_reason,
        "cost_stability_mix": None,
        "exact_growth_adaptive_weight": None,
        "exact_growth_expected_spend_drift_bound": None,
        "robust_growth_probability_radius": None,
        "material_harm": harm_onset is not None,
        "population_null_control": scenario.name in POPULATION_NULL_CONTROLS,
        "sample_path_material_harm": sample_path_material_harm,
        "sample_path_harm_onset_relative": sample_path_harm_onset,
        "harm_onset_relative": harm_onset,
        "harm_reached_before_budget_stop": harm_reached,
        # The legacy single_e fields are the primary monitor outcome in the common result schema.
        "single_e_detected": bool(detected),
        "single_e_false_escalation": bool(false_escalation),
        "single_e_alarm_time": alarm_time,
        "single_e_delay": (
            int(alarm_time - harm_onset)
            if detected and alarm_time is not None and harm_onset is not None
            else None
        ),
        "multiscale_e_detected": np.nan,
        "multiscale_e_false_escalation": np.nan,
        "multiscale_e_alarm_time": None,
        "multiscale_e_delay": None,
        "protected_e_detected": np.nan,
        "protected_e_false_escalation": np.nan,
        "protected_e_alarm_time": None,
        "protected_e_delay": None,
        "stream_mean_estimation_error": float(np.mean(errors)) if len(errors) else float("nan"),
        "stream_mean_estimation_rmse": float(np.sqrt(np.mean(errors**2)))
        if len(errors)
        else float("nan"),
        "mean_expected_decision_harm": float(np.mean(block_expected))
        if block_expected
        else float("nan"),
        "pprm_confidence_lower_bound": monitor.lower_bound,
        "pprm_block_size": PPRM_BLOCK_SIZE,
        "pprm_labels_per_block": PPRM_LABELS_PER_BLOCK,
        "pprm_reliance_mean": float(np.mean(block_reliances)) if block_reliances else eta,
        "pprm_reliance_last": block_reliances[-1] if block_reliances else eta,
        "pprm_max_reliance": PPRM_MAX_RELIANCE,
    }


def _generate_stream_rows(
    scenario, seed: int, config: HardBudgetConfig, common_uniforms: np.ndarray
) -> list[dict[str, object]]:
    if config.scenario_severity is not None:
        scenario = replace(scenario, severity=config.scenario_severity)
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
        change_fraction=config.change_fraction,
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
    sample_path_onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    onset = statistical_harm_onset(scenario.name, sample_path_onset)
    rows = []
    for method in config.method_subset:
        if method == "pprm_block_adaptive":
            rows.append(
                _one_pprm_block_method(
                    seed=seed,
                    scenario=scenario,
                    config=config,
                    x=x,
                    centered_cost_difference=centered_difference,
                    expected_cost_difference=expected_difference,
                    label_costs=label_costs,
                    proxy_template=proxy_template,
                    monitor_start=monitor_start,
                    harm_onset=onset,
                    sample_path_material_harm=sample_path_onset is not None,
                    sample_path_harm_onset=sample_path_onset,
                    common_uniforms=common_uniforms,
                )
            )
        else:
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
                    sample_path_material_harm=sample_path_onset is not None,
                    sample_path_harm_onset=sample_path_onset,
                    common_uniforms=common_uniforms,
                    contrast_zero=contrast_zero,
                    contrast_one=contrast_one,
                )
            )
    if "robust_mixture_growth_proxy" in config.method_subset:
        source_probability = classifier.predict_proba(x[monitor_start:])[:, 1]
        true_probability = oracle.probability_positive.to_numpy(dtype=float)[monitor_start:]
        coverage = float(
            np.mean(
                np.abs(source_probability - true_probability)
                <= config.robust_growth_probability_radius
            )
        )
        for row in rows:
            if row["method"] == "robust_mixture_growth_proxy":
                # Evaluator-only calibration diagnostic; never supplied to query selection.
                row["robust_probability_interval_coverage"] = coverage
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
                "sample_path_materiality_flags": int(group.sample_path_material_harm.sum()),
                "detection_rate_all_harm": harm.single_e_detected.mean() if len(harm) else np.nan,
                "detection_rate_reached_harm": reached.single_e_detected.mean()
                if len(reached)
                else np.nan,
                "false_escalation_rate": group.single_e_false_escalation.mean(),
                "multiscale_detection_rate_all_harm": (
                    harm.multiscale_e_detected.mean()
                    if len(harm) and "multiscale_e_detected" in metrics
                    else np.nan
                ),
                "multiscale_detection_rate_reached_harm": (
                    reached.multiscale_e_detected.mean()
                    if len(reached) and "multiscale_e_detected" in metrics
                    else np.nan
                ),
                "multiscale_false_escalation_rate": (
                    group.multiscale_e_false_escalation.mean()
                    if "multiscale_e_false_escalation" in metrics
                    else np.nan
                ),
                "protected_detection_rate_all_harm": (
                    harm.protected_e_detected.mean()
                    if len(harm) and "protected_e_detected" in metrics
                    else np.nan
                ),
                "protected_detection_rate_reached_harm": (
                    reached.protected_e_detected.mean()
                    if len(reached) and "protected_e_detected" in metrics
                    else np.nan
                ),
                "protected_false_escalation_rate": (
                    group.protected_e_false_escalation.mean()
                    if "protected_e_false_escalation" in metrics
                    else np.nan
                ),
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
            secondary_available = method != "pprm_block_adaptive"
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
                    "multiscale_detection_method": (
                        int(reached.multiscale_e_detected_method.sum())
                        if secondary_available
                        else np.nan
                    ),
                    "multiscale_detection_uniform": (
                        int(reached.multiscale_e_detected_uniform.sum())
                        if secondary_available
                        else np.nan
                    ),
                    "multiscale_only": int(
                        (
                            reached.multiscale_e_detected_method
                            & np.logical_not(reached.single_e_detected_method)
                        ).sum()
                    )
                    if secondary_available
                    else np.nan,
                    "fixed_only": int(
                        (
                            reached.single_e_detected_method
                            & np.logical_not(reached.multiscale_e_detected_method)
                        ).sum()
                    )
                    if secondary_available
                    else np.nan,
                    "multiscale_false_escalations": int(
                        paired.multiscale_e_false_escalation_method.sum()
                    )
                    if secondary_available
                    else np.nan,
                    "protected_detection_method": int(reached.protected_e_detected_method.sum())
                    if secondary_available
                    else np.nan,
                    "protected_detection_uniform": int(reached.protected_e_detected_uniform.sum())
                    if secondary_available
                    else np.nan,
                    "protected_only": int(
                        (
                            reached.protected_e_detected_method
                            & np.logical_not(reached.single_e_detected_method)
                        ).sum()
                    )
                    if secondary_available
                    else np.nan,
                    "fixed_only_vs_protected": int(
                        (
                            reached.single_e_detected_method
                            & np.logical_not(reached.protected_e_detected_method)
                        ).sum()
                    )
                    if secondary_available
                    else np.nan,
                    "protected_false_escalations": int(
                        paired.protected_e_false_escalation_method.sum()
                    )
                    if secondary_available
                    else np.nan,
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
        "|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in effects.to_dict("records"):

        def count_text(value: object) -> str:
            return "n/a" if pd.isna(value) else str(int(value))

        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['rmse_difference']:.4f} [{row['rmse_ci_low']:.4f}, {row['rmse_ci_high']:.4f}]|{row['spend_difference']:.2f} [{row['spend_ci_low']:.2f}, {row['spend_ci_high']:.2f}]|{row['label_difference']:.1f} [{row['label_ci_low']:.1f}, {row['label_ci_high']:.1f}]|{row['monitor_fraction_difference']:.3f} [{row['monitor_ci_low']:.3f}, {row['monitor_ci_high']:.3f}]|{count_text(row['harm_detected'])} / {count_text(row['multiscale_detection_method'])} / {count_text(row['protected_detection_method'])} / {count_text(row['harm_reached'])}|{count_text(row['multiscale_only'])} / {count_text(row['fixed_only'])}|{count_text(row['protected_only'])} / {count_text(row['fixed_only_vs_protected'])}|{count_text(row['protected_false_escalations'])} / {row['n_seeds']}|"
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
        monitor_columns = tuple(
            item
            for item in (
                ("single_e_detected", "Primary monitor", "tab:blue"),
                ("multiscale_e_detected", "Broad multiscale", "tab:orange"),
                ("protected_e_detected", "Protected multiscale", "tab:green"),
            )
            if item[0] in metrics
        )
        bar_width = 0.72 / len(monitor_columns)
        max_upper = 0.0
        sample_count = 0
        for monitor_index, (column, label, color) in enumerate(monitor_columns):
            detection = harmful.groupby("method")[column].agg(["sum", "count"]).reindex(methods)
            valid = detection["count"] > 0
            rate = detection["sum"] / detection["count"].replace(0, np.nan)
            totals = detection["count"].where(valid, 1).to_numpy()
            successes = detection["sum"].where(valid, 0).to_numpy()
            lower, upper = _wilson_bounds(successes, totals)
            lower[~valid.to_numpy()] = np.nan
            upper[~valid.to_numpy()] = np.nan
            rate_values = rate.fillna(0.0).to_numpy()
            lower_values = np.nan_to_num(lower, nan=0.0)
            upper_values = np.nan_to_num(upper, nan=0.0)
            offset = (monitor_index - (len(monitor_columns) - 1) / 2) * bar_width
            axes[1].bar(x + offset, rate, color=color, width=bar_width, label=label)
            axes[1].errorbar(
                x + offset,
                rate,
                yerr=np.maximum(
                    0.0,
                    np.vstack((rate_values - lower_values, upper_values - rate_values)),
                ),
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
    metrics = apply_population_null_classification(metrics)
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
            f"Exact mixture-growth acquisition uses adaptive weight {config.exact_growth_adaptive_weight:.3f} toward the per-event cost-neutral propensity. Its worst-case expected-spend drift bound is computed over tariff support [0.5, {config.max_label_cost:g}]."
            if "exact_mixture_growth_proxy" in config.method_subset
            and config.exact_growth_adaptive_weight < 1.0
            else ""
        ),
        (
            "The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support."
            if config.common_eprocess_bound
            else "The primary comparison uses each method's actual minimum propensity in its e-process bound: uniform queries at 0.10 use a tighter bound than adaptive policies that can query at 0.05. The common-bound sensitivity at reports/eprocess_bound_sensitivity.md found 0/30 detections for every method under q_min=0.05; do not attribute the primary 4-versus-0 difference solely to allocation."
        ),
        "",
        "Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.",
        "",
        "|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|",
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
        multiscale_false_text = (
            "n/a"
            if pd.isna(row["multiscale_false_escalation_rate"])
            else f"{row['multiscale_false_escalation_rate']:.3f}"
        )
        protected_false_text = (
            "n/a"
            if pd.isna(row["protected_false_escalation_rate"])
            else f"{row['protected_false_escalation_rate']:.3f}"
        )
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['mean_budget']:.2f}|{row['mean_spend']:.2f}|{row['budget_utilization']:.3f}|{row['mean_labels']:.1f}|{row['mean_monitor_fraction']:.3f}|{row['stream_mean_rmse']:.4f}|{row['harm_reachable_streams']}/{row['harmful_streams']}|{row['sample_path_materiality_flags']}|{all_detection_text} / {reached_detection_text}|{multiscale_all_text} / {multiscale_reached_text}|{protected_all_text} / {protected_reached_text}|{row['false_escalation_rate']:.3f} / {multiscale_false_text} / {protected_false_text}|"
        )
    lines.extend(
        [
            "",
            "## Full-horizon consistency check",
            "",
            "Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.",
            "",
            "The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.",
            "The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.",
            "",
            "## Interpretation limits",
            "",
            "This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.",
            "",
            (
                "Reproduce with `uv run shiftlab-dive-hard-budget "
                f"--seeds {config.seeds} --seed-offset {config.seed_offset} "
                f"--n {config.n} --d {config.d} --budget-rate {config.budget_rate} "
                f"--q-min {config.q_min} --q-max {config.q_max} --device {config.device} "
                f"--exact-growth-adaptive-weight {config.exact_growth_adaptive_weight} "
                f"--robust-growth-probability-radius {config.robust_growth_probability_radius} "
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
    if "uniform_proxy" in set(metrics.method) and {
        "multiscale_e_detected",
        "protected_e_detected",
    } <= set(metrics.columns):
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
    parser.add_argument("--exact-growth-adaptive-weight", type=float, default=1.0)
    parser.add_argument("--robust-growth-probability-radius", type=float, default=0.0)
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
        exact_growth_adaptive_weight=args.exact_growth_adaptive_weight,
        robust_growth_probability_radius=args.robust_growth_probability_radius,
        common_eprocess_bound=args.common_eprocess_bound,
        device=args.device,
        scenario_subset=tuple(args.scenarios or HardBudgetConfig.scenario_subset),
        method_subset=tuple(args.methods or DEFAULT_HARD_BUDGET_METHODS),
    )
    print(run_hard_budget(config, args.output), flush=True)


if __name__ == "__main__":
    main()
