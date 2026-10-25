"""Compare repeated-candidate promotion under a shared hard label budget."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import matplotlib
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.stats import norm, sem, t
from sklearn.linear_model import LogisticRegression

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate
from .eprocess import bounded_betting_factors
from .experiment import _binary_cost, finalize_manifest
from .promotion_grid import (
    PromotionGridConfig,
    _candidate_alpha_allocations,
    _candidate_models,
    _time_splits,
)
from .query import AdaptiveQueryPolicy

QUERY_POLICIES = ("uniform", "variance", "decision_value")
BASE_ALPHA_ALLOCATIONS = ("rank", "equal", "validation_power")
CONTEXT_ALPHA_ALLOCATIONS = ("rank_context_equal", "rank_context_volume")
ALPHA_ALLOCATIONS = BASE_ALPHA_ALLOCATIONS + CONTEXT_ALPHA_ALLOCATIONS
ESTIMATORS = ("prediction_powered", "direct_ipw")
BOUND_MODES = ("global", "decision_local")
MONITORING_RULES = (
    "fixed_mixture",
    "fixed_mixture_half_alpha",
    "predictable_kelly",
    "pm_eb",
    "positive_betting",
    "hedged_positive",
)
BETTING_STAKES = np.asarray((0.05, 0.1, 0.2, 0.4, 0.8), dtype=float)
BETTING_LOG_WEIGHTS = np.full(len(BETTING_STAKES), -np.log(len(BETTING_STAKES)))


@dataclass(frozen=True)
class BudgetedPromotionConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 60
    seed_offset: int = 24102026
    alpha: float = 0.05
    switching_cost: float = 0.05
    budget_rates: tuple[float, ...] = (0.10, 0.20)
    query_policies: tuple[str, ...] = QUERY_POLICIES
    alpha_allocations: tuple[str, ...] = BASE_ALPHA_ALLOCATIONS
    estimators: tuple[str, ...] = ESTIMATORS
    monitoring_rules: tuple[str, ...] = ("fixed_mixture",)
    bound_mode: str = "global"
    context_feature_index: int = 0
    context_threshold: float = 0.0
    context_target_prevalence: float = 0.5
    context_signal_strength: float = 0.0
    context_proxy_error: float = 0.0
    include_validation_context_policy: bool = False
    include_scout_context_policy: bool = False
    scenario_subset: tuple[str, ...] = ()
    create_plot: bool = True
    device: str = "cuda"

    def validate(self) -> BudgetedPromotionConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds must be positive")
        if not np.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        if not np.isfinite(self.switching_cost) or self.switching_cost < 0:
            raise ValueError("switching_cost must be finite and nonnegative")
        if not self.budget_rates or tuple(sorted(set(self.budget_rates))) != self.budget_rates:
            raise ValueError("budget_rates must be strictly increasing and nonempty")
        if any(not np.isfinite(r) or not 0 < r < 1 for r in self.budget_rates):
            raise ValueError("budget rates must lie strictly between zero and one")
        if not self.query_policies or len(set(self.query_policies)) != len(self.query_policies):
            raise ValueError("query_policies must be nonempty and unique")
        if any(name not in QUERY_POLICIES for name in self.query_policies):
            raise ValueError(f"query_policies must be drawn from {QUERY_POLICIES}")
        if not self.alpha_allocations or len(set(self.alpha_allocations)) != len(
            self.alpha_allocations
        ):
            raise ValueError("alpha_allocations must be nonempty and unique")
        if any(name not in ALPHA_ALLOCATIONS for name in self.alpha_allocations):
            raise ValueError(f"alpha_allocations must be drawn from {ALPHA_ALLOCATIONS}")
        if any(name in CONTEXT_ALPHA_ALLOCATIONS for name in self.alpha_allocations):
            if "rank" not in self.alpha_allocations:
                raise ValueError("context alpha comparisons require the pooled rank comparator")
            if self.monitoring_rules != ("fixed_mixture",):
                raise ValueError("context alpha currently requires the fixed_mixture monitor")
            if self.bound_mode != "global":
                raise ValueError("context alpha requires the common global support bound")
        if not self.estimators or len(set(self.estimators)) != len(self.estimators):
            raise ValueError("estimators must be nonempty and unique")
        if any(name not in ESTIMATORS for name in self.estimators):
            raise ValueError(f"estimators must be drawn from {ESTIMATORS}")
        if not self.monitoring_rules or len(set(self.monitoring_rules)) != len(
            self.monitoring_rules
        ):
            raise ValueError("monitoring_rules must be nonempty and unique")
        if any(name not in MONITORING_RULES for name in self.monitoring_rules):
            raise ValueError(f"monitoring_rules must be drawn from {MONITORING_RULES}")
        if self.bound_mode not in BOUND_MODES:
            raise ValueError(f"bound_mode must be one of {BOUND_MODES}")
        if self.context_feature_index < 0 or self.context_feature_index >= self.d:
            raise ValueError("context_feature_index must identify a configured feature")
        if not np.isfinite(self.context_threshold):
            raise ValueError("context_threshold must be finite")
        if not np.isfinite(self.context_target_prevalence) or not (
            0 < self.context_target_prevalence < 1
        ):
            raise ValueError("context_target_prevalence must lie strictly between zero and one")
        if not np.isfinite(self.context_signal_strength) or not (
            0 <= self.context_signal_strength < 1 / 6
        ):
            raise ValueError("context_signal_strength must lie in [0, 1/6) for FN=5, FP=1")
        if not np.isfinite(self.context_proxy_error) or not (0 <= self.context_proxy_error < 0.5):
            raise ValueError("context_proxy_error must lie in [0, 0.5)")
        known_scenarios = {scenario.name for scenario in SCENARIOS} | {
            "candidate_family_null",
            "candidate_context_zero_mean",
            "candidate_context_heterogeneity",
        }
        if len(set(self.scenario_subset)) != len(self.scenario_subset) or any(
            name not in known_scenarios for name in self.scenario_subset
        ):
            raise ValueError("scenario_subset must contain unique registered scenarios")
        if (
            "candidate_context_heterogeneity" in self.scenario_subset
            and self.context_feature_index < 2
        ):
            raise ValueError("context heterogeneity requires a proxy feature outside signal x[0:2]")
        if self.include_validation_context_policy and self.include_scout_context_policy:
            raise ValueError("choose at most one single-policy context selection rule")
        if self.include_validation_context_policy or self.include_scout_context_policy:
            if "candidate_context_heterogeneity" not in self.scenario_subset:
                raise ValueError("single-policy context rule requires the registered context DGP")
            if self.context_feature_index < 2 or self.bound_mode != "global":
                raise ValueError(
                    "single-policy context rule requires a proxy feature and global bound"
                )
            if self.monitoring_rules != ("fixed_mixture",) or self.estimators != ("direct_ipw",):
                raise ValueError("single-policy context rule requires fixed-mixture direct IPW")
        if self.device not in {"cpu", "cuda", "auto"}:
            raise ValueError("device must be cpu, cuda, or auto")
        return self


def _binary_costs(actions: np.ndarray, labels: np.ndarray, *, fn: float, fp: float) -> np.ndarray:
    actions = np.asarray(actions, dtype=int)
    labels = np.asarray(labels, dtype=int)
    return np.where(actions == labels, 0.0, np.where(actions == 1, fp, fn))


def _candidate_outcome_contrasts(
    incumbent: np.ndarray, candidates: np.ndarray, *, fn: float, fp: float
) -> tuple[np.ndarray, np.ndarray]:
    zero = _binary_costs(incumbent, np.zeros(len(incumbent), dtype=int), fn=fn, fp=fp)[None, :]
    one = _binary_costs(incumbent, np.ones(len(incumbent), dtype=int), fn=fn, fp=fp)[None, :]
    candidate_zero = _binary_costs(candidates, np.zeros_like(candidates), fn=fn, fp=fp)
    candidate_one = _binary_costs(candidates, np.ones_like(candidates), fn=fn, fp=fp)
    return zero - candidate_zero, one - candidate_one


def _entropy(probability: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(probability, dtype=float), 1e-12, 1 - 1e-12)
    return -(p * np.log(p) + (1 - p) * np.log1p(-p))


def _decision_local_bounds(
    *,
    family: dict[str, Any],
    event_index: int,
    propensity: float,
    estimator: str,
    switch_rate: float,
) -> np.ndarray:
    """Predictable candidate-wise bounds for each event's net-gain increment.

    This normalization supports a conditional-on-current-covariates null. Under
    that stronger null, dividing each event by its pre-outcome bound preserves the
    nonpositive conditional mean. It need not be valid for a history-only null.
    """
    h = family["h_proxy"][:, event_index]
    z0 = family["z0"][:, event_index]
    z1 = family["z1"][:, event_index]
    if estimator == "prediction_powered":
        possible = np.stack((h, h + (z0 - h) / propensity, h + (z1 - h) / propensity))
    else:
        possible = np.stack((np.zeros_like(z0), z0 / propensity, z1 / propensity))
    return np.max(np.abs(possible - switch_rate), axis=0)


def _fit_candidate_family(
    *,
    x: np.ndarray,
    y: np.ndarray,
    probability_true: np.ndarray,
    scenario,
    config: BudgetedPromotionConfig,
) -> dict[str, Any]:
    train_end, validation_end, monitor_end = _time_splits(config.n)
    deployment_length = config.n - monitor_end
    incumbent = (x[:, 0] - 0.9 * x[:, 1] >= 0).astype(int)
    if scenario.harmful_adaptation:
        incumbent[config.n // 2 :] = 1

    source = LogisticRegression(C=1.0, max_iter=500)
    source.fit(x[:train_end], y[:train_end])
    probability_hat = source.predict_proba(x)[:, 1]

    grid_config = PromotionGridConfig(
        n=config.n,
        d=config.d,
        seeds=1,
        seed_offset=config.seed_offset,
        alpha=config.alpha,
        switching_cost=config.switching_cost,
        device=config.device,
    )
    candidates = _candidate_models(
        x=x,
        y=y,
        train_end=train_end,
        validation_end=validation_end,
        incumbent=incumbent,
        fn=scenario.fn_cost,
        fp=scenario.fp_cost,
        deployment_horizon=deployment_length,
        config=grid_config,
    )
    action_matrix = np.stack([np.asarray(c["actions"], dtype=int) for c in candidates])
    identifiers = [str(c["candidate_id"]) for c in candidates]

    probability_for_proxy = probability_hat.copy()
    # Exact policy copies provide a global-null familywise diagnostic. All members
    # are copies so every hypothesis in this synthetic family is truly null.
    if scenario.name == "candidate_family_null":
        action_matrix[:] = incumbent[None, :]
        for candidate in candidates:
            candidate["validation_gain"] = 0.0
            candidate["validation_gain_se"] = 0.0

    alpha_by_candidate = _candidate_alpha_allocations(candidates, alpha=config.alpha)
    for allocation in alpha_by_candidate.values():
        allocation["rank_context_equal"] = allocation["rank"]
        allocation["rank_context_volume"] = allocation["rank"]
    alpha_matrix = np.asarray(
        [
            [alpha_by_candidate[name][allocation] for allocation in config.alpha_allocations]
            for name in identifiers
        ],
        dtype=float,
    )
    if np.any(alpha_matrix <= 0) or np.any(alpha_matrix.sum(axis=0) > config.alpha + 1e-12):
        raise RuntimeError("candidate alpha allocation exceeds its familywise error budget")

    z0, z1 = _candidate_outcome_contrasts(
        incumbent, action_matrix, fn=scenario.fn_cost, fp=scenario.fp_cost
    )
    h_proxy = (1 - probability_for_proxy[None, :]) * z0 + probability_for_proxy[None, :] * z1
    h_truth = (1 - probability_true[None, :]) * z0 + probability_true[None, :] * z1
    validation = slice(train_end, validation_end)
    monitor = slice(validation_end, monitor_end)
    contexts = (x[:, config.context_feature_index] >= config.context_threshold).astype(int)
    validation_context_counts = np.bincount(contexts[validation], minlength=2).astype(int)
    context_volume_weights = (validation_context_counts + 0.5) / (
        validation_context_counts.sum() + 1.0
    )
    top = 0  # candidates are validation-ranked before any monitor feedback
    residual_variance = (
        probability_for_proxy * (1 - probability_for_proxy) * (z1[top] - z0[top]) ** 2
    )
    q_policy_paths: dict[tuple[str, float], np.ndarray] = {}
    min_propensities: dict[float, float] = {}
    for budget_rate in config.budget_rates:
        q_min = budget_rate / 2
        min_propensities[budget_rate] = q_min
        for query_name in config.query_policies:
            policy = AdaptiveQueryPolicy(
                query_name,
                target_rate=budget_rate,
                q_min=q_min,
                q_max=max(0.5, budget_rate),
            ).fit_multiplier(
                proxy=h_proxy[top, validation],
                residual_second_moment=residual_variance[validation],
                uncertainty=_entropy(probability_for_proxy[validation]),
                label_costs=np.ones(validation.stop - validation.start),
            )
            q_policy_paths[(query_name, budget_rate)] = policy.probabilities(
                proxy=h_proxy[top, monitor],
                residual_second_moment=residual_variance[monitor],
                uncertainty=_entropy(probability_for_proxy[monitor]),
                label_costs=np.ones(monitor.stop - monitor.start),
            )

    return {
        "candidate_ids": identifiers,
        "actions": action_matrix,
        "incumbent": incumbent,
        "z0": z0,
        "z1": z1,
        "h_proxy": h_proxy,
        "h_truth": h_truth,
        "alpha_matrix": alpha_matrix,
        "contexts": contexts,
        "validation_context_counts": validation_context_counts,
        "context_volume_weights": context_volume_weights,
        "q_paths": q_policy_paths,
        "q_min": min_propensities,
        "train_end": train_end,
        "validation_end": validation_end,
        "monitor_end": monitor_end,
        "monitor_length": monitor.stop - monitor.start,
        "deployment_length": deployment_length,
        "top_validation_gain": float(cast(float, candidates[0]["validation_gain"])),
        "probability_hat": probability_hat,
    }


def _monitor_family(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    scenario,
    config: BudgetedPromotionConfig,
    query_name: str,
    budget_rate: float,
    estimator: str,
    query_uniforms: np.ndarray,
    bound_mode: str = "global",
    monitoring_rule: str = "fixed_mixture",
) -> list[dict[str, Any]]:
    start = family["validation_end"]
    end = family["monitor_end"]
    length = family["monitor_length"]
    budget = int(np.floor(budget_rate * length))
    if budget < 1:
        raise ValueError("configured budget leaves no label for the monitor")
    q_path = family["q_paths"][(query_name, budget_rate)]
    q_min = family["q_min"][budget_rate]
    candidates = family["actions"].shape[0]
    switch_rate = config.switching_cost / family["deployment_length"]
    outcome_bound = float(max(scenario.fn_cost, scenario.fp_cost))
    process_bound = (
        outcome_bound * (2 / q_min - 1)
        if estimator == "prediction_powered"
        else outcome_bound / q_min
    ) + switch_rate
    if bound_mode not in BOUND_MODES:
        raise ValueError(f"bound_mode must be one of {BOUND_MODES}")
    if monitoring_rule not in MONITORING_RULES:
        raise ValueError(f"monitoring_rule must be one of {MONITORING_RULES}")
    log_wealth = np.zeros((candidates, len(BETTING_STAKES)), dtype=float)
    contextual_log_wealth = np.zeros((candidates, 2, len(BETTING_STAKES)), dtype=float)
    kelly_log_wealth = np.zeros(candidates, dtype=float)
    kelly_sum = np.zeros(candidates, dtype=float)
    kelly_sum_squares = np.zeros(candidates, dtype=float)
    pm_log_wealth = np.zeros((candidates, len(config.alpha_allocations)), dtype=float)
    positive_log_wealth = np.zeros_like(pm_log_wealth)
    pm_sum_observations = np.zeros(candidates, dtype=float)
    pm_sum_predictive_squared_deviations = np.zeros(candidates, dtype=float)
    pm_predictive_mean = np.full(candidates, 0.5, dtype=float)
    pm_predictive_variance = np.full(candidates, 0.25, dtype=float)
    certified = np.zeros((candidates, len(config.alpha_allocations)), dtype=bool)
    contextual_certified = np.zeros((candidates, 2, len(config.alpha_allocations)), dtype=bool)
    context_allocation_weights = {
        "rank_context_equal": np.asarray([0.5, 0.5]),
        "rank_context_volume": np.asarray(family.get("context_volume_weights", [0.5, 0.5])),
    }
    has_context_alpha = any(name in CONTEXT_ALPHA_ALLOCATIONS for name in config.alpha_allocations)
    if has_context_alpha and "contexts" not in family:
        raise ValueError("context alpha requires learner-visible context assignments")
    labels_used = 0
    expected_labels = 0.0
    processed = 0
    bound_total = 0.0
    max_event_bound = 0.0
    stop_reason = "monitor_horizon"

    for relative, event_index in enumerate(range(start, end)):
        # Unit-cost labels make the pre-event reserve check a pathwise hard cap.
        if budget - labels_used < 1:
            stop_reason = "label_budget_exhausted"
            break
        propensity = float(q_path[relative])
        if propensity + 1e-12 < q_min or propensity > max(0.5, budget_rate) + 1e-12:
            raise RuntimeError("query policy violated its registered propensity range")
        queried = bool(query_uniforms[relative] < propensity)
        expected_labels += propensity
        if queried:
            labels_used += 1
            observed_contrast = (
                family["z1"][:, event_index] if y[event_index] else family["z0"][:, event_index]
            )
            estimates = (
                family["h_proxy"][:, event_index]
                + (observed_contrast - family["h_proxy"][:, event_index]) / propensity
                if estimator == "prediction_powered"
                else observed_contrast / propensity
            )
        else:
            estimates = (
                family["h_proxy"][:, event_index]
                if estimator == "prediction_powered"
                else np.zeros(candidates, dtype=float)
            )
        net_estimates = estimates - switch_rate
        event_bounds = (
            _decision_local_bounds(
                family=family,
                event_index=event_index,
                propensity=propensity,
                estimator=estimator,
                switch_rate=switch_rate,
            )
            if bound_mode == "decision_local"
            else np.full(candidates, process_bound)
        )
        if np.any(event_bounds <= 0):
            event_bounds = np.maximum(event_bounds, 1e-12)
        if np.any(np.abs(net_estimates) > event_bounds + 1e-10):
            raise RuntimeError("prediction-powered contrast exceeded its declared bound")
        thresholds = -np.log(family["alpha_matrix"])
        normalized = net_estimates / event_bounds
        if np.any(np.abs(normalized) > 1 + 1e-10):
            raise RuntimeError("normalized increment escaped its declared support")

        if monitoring_rule in {"fixed_mixture", "fixed_mixture_half_alpha"}:
            factors = bounded_betting_factors(net_estimates, event_bounds, BETTING_STAKES)
            if np.any(factors <= 0):
                raise RuntimeError("nonpositive fixed-mixture betting factor")
            log_wealth += np.log(factors)
            log_e = logsumexp(log_wealth + BETTING_LOG_WEIGHTS[None, :], axis=1)
            level = thresholds if monitoring_rule == "fixed_mixture" else thresholds + np.log(2.0)
            certified |= log_e[:, None] >= level
            if has_context_alpha and monitoring_rule == "fixed_mixture":
                group = int(family["contexts"][event_index])
                contextual_log_wealth[:, group, :] += np.log(factors)
                context_log_e = logsumexp(
                    contextual_log_wealth[:, group, :] + BETTING_LOG_WEIGHTS[None, :],
                    axis=1,
                )
                for allocation in CONTEXT_ALPHA_ALLOCATIONS:
                    if allocation not in config.alpha_allocations:
                        continue
                    column = config.alpha_allocations.index(allocation)
                    cell_alpha = (
                        family["alpha_matrix"][:, column]
                        * context_allocation_weights[allocation][group]
                    )
                    contextual_certified[:, group, column] |= context_log_e >= -np.log(cell_alpha)
        elif monitoring_rule == "predictable_kelly":
            denominator = 4.0 + processed
            mean_hat = (4.0 * 0.05 + kelly_sum) / denominator
            second_hat = (4.0 * 0.25 + kelly_sum_squares) / denominator
            stake = np.clip(np.maximum(mean_hat, 0.0) / second_hat, 0.0, 0.5)
            factors = 1.0 + stake * normalized
            if np.any(factors <= 0):
                raise RuntimeError("predictable Kelly betting factor was nonpositive")
            kelly_log_wealth += np.log(factors)
            certified |= kelly_log_wealth[:, None] >= thresholds
            kelly_sum += normalized
            kelly_sum_squares += normalized**2
        elif monitoring_rule in {"pm_eb", "positive_betting", "hedged_positive"}:
            time = processed + 1
            alpha_levels = family["alpha_matrix"]
            log_stake_level = np.log(2.0 / alpha_levels)
            variance_denominator = pm_predictive_variance[:, None] * time * np.log1p(time)
            variance_stake = np.sqrt(2.0 * log_stake_level / variance_denominator)
            observation = 0.5 * (normalized + 1.0)
            residual = observation - pm_predictive_mean

            if monitoring_rule == "pm_eb":
                stake = np.minimum(0.5, variance_stake)
                psi = (-np.log1p(-stake) - stake) / 4.0
                increment = (
                    stake * (observation[:, None] - 0.5) - 4.0 * residual[:, None] ** 2 * psi
                )
                pm_log_wealth += increment
                certified |= pm_log_wealth >= thresholds
            else:
                stake = np.minimum(1.0, variance_stake)
                factors = 1.0 + stake * (observation[:, None] - 0.5)
                if np.any(factors <= 0):
                    raise RuntimeError("predictable positive betting factor was nonpositive")
                positive_log_wealth += np.log(factors)
                level = (
                    thresholds
                    if monitoring_rule == "positive_betting"
                    else thresholds + np.log(2.0)
                )
                certified |= positive_log_wealth >= level

            pm_sum_observations += observation
            updated_mean = (0.5 + pm_sum_observations) / (time + 1)
            post_update_residual = observation - updated_mean
            pm_sum_predictive_squared_deviations += post_update_residual**2
            pm_predictive_mean = updated_mean
            pm_predictive_variance = (0.25 + pm_sum_predictive_squared_deviations) / (time + 1)
        else:
            raise RuntimeError("unreachable monitoring rule")
        bound_total += float(event_bounds.mean())
        max_event_bound = max(max_event_bound, float(event_bounds.max()))
        processed += 1

    if labels_used > budget:
        raise RuntimeError("hard label budget was exceeded")
    stop_index = start + processed
    truth = family["h_truth"]
    monitor_truth = truth[:, start:end].mean(axis=1) - switch_rate
    pointwise_null_candidates = np.all(
        truth[:, start:stop_index] - switch_rate <= 1e-12,
        axis=1,
    )
    context_null_candidates: dict[int, np.ndarray] = {}
    if has_context_alpha:
        monitor_contexts = np.asarray(family["contexts"][start:stop_index], dtype=int)
        monitor_truth_by_candidate = truth[:, start:stop_index] - switch_rate
        for group in range(2):
            selected_events = monitor_contexts == group
            context_null_candidates[group] = (
                np.all(monitor_truth_by_candidate[:, selected_events] <= 1e-12, axis=1)
                if selected_events.any()
                else np.ones(candidates, dtype=bool)
            )
    output: list[dict[str, Any]] = []
    allocation_index = {name: i for i, name in enumerate(config.alpha_allocations)}
    for allocation in config.alpha_allocations:
        a = allocation_index[allocation]
        if allocation in CONTEXT_ALPHA_ALLOCATIONS:
            deploy_indices = np.arange(stop_index, config.n)
            deployment_contexts = np.asarray(family["contexts"][deploy_indices], dtype=int)
            selected_by_context = {
                group: next(
                    (
                        candidate
                        for candidate in range(candidates)
                        if contextual_certified[candidate, group, a]
                    ),
                    None,
                )
                for group in range(2)
            }
            expected_net = 0.0
            realized_net = 0.0
            selected_count = 0
            selected_monitor_sum = 0.0
            selected_monitor_events = 0
            null_certificates = 0
            null_candidate_cells = 0
            selected_is_null = False
            for group, selected in selected_by_context.items():
                null_candidate_cells += int(context_null_candidates[group].sum())
                null_certificates += int(
                    np.sum(contextual_certified[:, group, a] & context_null_candidates[group])
                )
                if selected is None:
                    continue
                use_deployment = deployment_contexts == group
                event_count = int(use_deployment.sum())
                selected_count += event_count
                expected_net += float(
                    np.sum(truth[selected, deploy_indices[use_deployment]] - switch_rate)
                )
                observed = np.where(
                    y[deploy_indices[use_deployment]] == 1,
                    family["z1"][selected, deploy_indices[use_deployment]],
                    family["z0"][selected, deploy_indices[use_deployment]],
                )
                realized_net += float(np.sum(observed - switch_rate))
                use_monitor = monitor_contexts == group
                if use_monitor.any():
                    selected_monitor_sum += float(
                        np.sum(truth[selected, start:stop_index][use_monitor] - switch_rate)
                    )
                    selected_monitor_events += int(use_monitor.sum())
                selected_is_null = selected_is_null or bool(
                    context_null_candidates[group][selected]
                )
            exposure_switching_cost = switch_rate * selected_count
            selected_any = any(value is not None for value in selected_by_context.values())
            selected_ids = {
                str(group): None if value is None else family["candidate_ids"][value]
                for group, value in selected_by_context.items()
            }
            selected_ranks = {
                str(group): None if value is None else value + 1
                for group, value in selected_by_context.items()
            }
            context_weights = context_allocation_weights[allocation]
            output.append(
                {
                    "scenario": scenario.name,
                    "seed": None,
                    "query_policy": query_name,
                    "estimator": estimator,
                    "monitoring_rule": monitoring_rule,
                    "budget_rate": budget_rate,
                    "label_budget": budget,
                    "alpha_allocation": allocation,
                    "alpha_total": config.alpha,
                    "candidate_count": candidates,
                    "candidate_id": json.dumps(selected_ids, sort_keys=True),
                    # Keep the pooled scalar rank column type-stable for Parquet.
                    # Context ranks have a separate JSON field because two ranks may be selected.
                    "candidate_validation_rank": None,
                    "candidate_validation_ranks_by_context": json.dumps(
                        selected_ranks, sort_keys=True
                    ),
                    "selected_candidates_by_context": json.dumps(selected_ids, sort_keys=True),
                    "context_weights": json.dumps(context_weights.tolist()),
                    "validation_context_counts": json.dumps(
                        np.asarray(family["validation_context_counts"], dtype=int).tolist()
                    ),
                    "candidate_is_monitor_null": selected_is_null if selected_any else None,
                    "promoted": selected_any,
                    "pointwise_null_candidate_certified": bool(null_certificates),
                    "pointwise_null_candidate_certificate_count": null_certificates,
                    "selected_candidate_monitor_expected_net_gain": (
                        selected_monitor_sum / selected_monitor_events
                        if selected_monitor_events
                        else None
                    ),
                    "expected_postpromotion_net_gain": expected_net,
                    "realized_postpromotion_net_gain": realized_net,
                    "harmful_postpromotion_promotion": bool(selected_any and expected_net <= 0),
                    "future_mean_net_gain_per_event": expected_net / max(1, config.n - stop_index),
                    "labels_queried": labels_used,
                    "expected_labels_queried": expected_labels,
                    "budget_utilization": labels_used / budget,
                    "monitor_events_processed": processed,
                    "monitor_fraction_processed": processed / length,
                    "process_bound": bound_total / max(1, processed),
                    "global_process_bound": process_bound,
                    "mean_event_process_bound": bound_total / max(1, processed),
                    "max_event_process_bound": max_event_bound,
                    "bound_mode": bound_mode,
                    "stop_reason": stop_reason,
                    "q_min": q_min,
                    "propensity_min": float(q_path[:processed].min()) if processed else None,
                    "propensity_max": float(q_path[:processed].max()) if processed else None,
                    "switching_cost": exposure_switching_cost,
                    "evaluation_start_index": stop_index,
                    "training_end_index": family["train_end"],
                    "validation_end_index": family["validation_end"],
                    "shadow_end_index": end,
                    "deployment_end_index": config.n,
                    "familywise_alpha_sum": float(
                        np.sum(family["alpha_matrix"][:, a]) * context_weights.sum()
                    ),
                    "pointwise_null_candidate_count": null_candidate_cells,
                    "context_policy_events": selected_count,
                    "context_feature_index": config.context_feature_index,
                    "context_threshold": config.context_threshold,
                }
            )
            continue
        selected = next((i for i in range(candidates) if certified[i, a]), None)
        pointwise_null_certificates = certified[:, a] & pointwise_null_candidates
        if selected is None:
            expected_net = realized_net = 0.0
            future_mean = 0.0
            selected_id = None
            selected_rank = None
            selected_null = None
        else:
            selected_future = truth[selected, stop_index:]
            expected_net = float(selected_future.sum() - config.switching_cost)
            realized_contrast = _binary_cost(
                family["incumbent"][stop_index:],
                y[stop_index:],
                scenario.fn_cost,
                scenario.fp_cost,
            ) - _binary_cost(
                family["actions"][selected, stop_index:],
                y[stop_index:],
                scenario.fn_cost,
                scenario.fp_cost,
            )
            realized_net = float(realized_contrast.sum() - config.switching_cost)
            future_mean = float(expected_net / max(1, config.n - stop_index))
            selected_id = family["candidate_ids"][selected]
            selected_rank = selected + 1
            selected_null = bool(pointwise_null_candidates[selected])
        output.append(
            {
                "scenario": scenario.name,
                "seed": None,
                "query_policy": query_name,
                "estimator": estimator,
                "monitoring_rule": monitoring_rule,
                "budget_rate": budget_rate,
                "label_budget": budget,
                "alpha_allocation": allocation,
                "alpha_total": config.alpha,
                "candidate_count": candidates,
                "candidate_id": selected_id,
                "candidate_validation_rank": selected_rank,
                "candidate_is_monitor_null": selected_null,
                "promoted": selected is not None,
                "pointwise_null_candidate_certified": bool(pointwise_null_certificates.any()),
                "pointwise_null_candidate_certificate_count": int(
                    pointwise_null_certificates.sum()
                ),
                "selected_candidate_monitor_expected_net_gain": (
                    float(monitor_truth[selected]) if selected is not None else None
                ),
                "expected_postpromotion_net_gain": expected_net,
                "realized_postpromotion_net_gain": realized_net,
                "harmful_postpromotion_promotion": bool(selected is not None and expected_net <= 0),
                "future_mean_net_gain_per_event": future_mean,
                "labels_queried": labels_used,
                "expected_labels_queried": expected_labels,
                "budget_utilization": labels_used / budget,
                "monitor_events_processed": processed,
                "monitor_fraction_processed": processed / length,
                "process_bound": bound_total / max(1, processed),
                "global_process_bound": process_bound,
                "mean_event_process_bound": bound_total / max(1, processed),
                "max_event_process_bound": max_event_bound,
                "bound_mode": bound_mode,
                "stop_reason": stop_reason,
                "q_min": q_min,
                "propensity_min": float(q_path[:processed].min()) if processed else None,
                "propensity_max": float(q_path[:processed].max()) if processed else None,
                "switching_cost": config.switching_cost if selected is not None else 0.0,
                "evaluation_start_index": stop_index,
                "training_end_index": family["train_end"],
                "validation_end_index": family["validation_end"],
                "shadow_end_index": end,
                "deployment_end_index": config.n,
                "familywise_alpha_sum": float(family["alpha_matrix"][:, a].sum()),
                "pointwise_null_candidate_count": int(pointwise_null_candidates.sum()),
            }
        )
    return output


def _monitor_validation_context_policy(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    scenario,
    config: BudgetedPromotionConfig,
    query_name: str,
    budget_rate: float,
    query_uniforms: np.ndarray,
) -> dict[str, Any]:
    """Select one contextual policy on validation and test it once on the monitor.

    The candidate tuple is fixed before the monitor. Its one global e-process
    tests the overall history-conditional mean net gain, so no alpha is split
    across the tuple's context-specific components.
    """
    if not config.include_validation_context_policy:
        raise ValueError("enable include_validation_context_policy to run this monitor")
    start = family["validation_end"]
    end = family["monitor_end"]
    length = family["monitor_length"]
    budget = int(np.floor(budget_rate * length))
    if budget < 1:
        raise ValueError("configured budget leaves no label for the monitor")
    q_path = family["q_paths"][(query_name, budget_rate)]
    q_min = family["q_min"][budget_rate]
    switch_rate = config.switching_cost / family["deployment_length"]
    outcome_bound = float(max(scenario.fn_cost, scenario.fp_cost))
    process_bound = outcome_bound / q_min + switch_rate

    validation_start = family["train_end"]
    validation_contexts = np.asarray(family["contexts"][validation_start:start], dtype=int)
    selected_by_context: dict[int, int | None] = {}
    validation_counts: dict[int, int] = {}
    for group in (0, 1):
        group_indices = np.arange(validation_start, start)[validation_contexts == group]
        validation_counts[group] = len(group_indices)
        if not len(group_indices):
            selected_by_context[group] = None
            continue
        observed = np.where(
            y[group_indices][None, :] == 1,
            family["z1"][:, group_indices],
            family["z0"][:, group_indices],
        )
        validation_net_means = observed.mean(axis=1) - switch_rate
        best = int(np.argmax(validation_net_means))
        selected_by_context[group] = best if validation_net_means[best] > 0 else None

    labels_used = 0
    expected_labels = 0.0
    processed = 0
    log_wealth = np.zeros(len(BETTING_STAKES), dtype=float)
    log_e_value = 0.0
    certified = False
    bound_total = 0.0
    stop_reason = "monitor_horizon"
    for relative, event_index in enumerate(range(start, end)):
        if budget - labels_used < 1:
            stop_reason = "label_budget_exhausted"
            break
        propensity = float(q_path[relative])
        if propensity + 1e-12 < q_min or propensity > max(0.5, budget_rate) + 1e-12:
            raise RuntimeError("query policy violated its registered propensity range")
        group = int(family["contexts"][event_index])
        selected = selected_by_context[group]
        active = selected is not None
        queried = bool(query_uniforms[relative] < propensity)
        expected_labels += propensity
        if queried:
            labels_used += 1
            if active:
                observed_gain = (
                    family["z1"][selected, event_index]
                    if y[event_index]
                    else family["z0"][selected, event_index]
                )
                estimate = observed_gain / propensity
            else:
                estimate = 0.0
        else:
            estimate = 0.0
        net_estimate = estimate - switch_rate if active else 0.0
        if abs(net_estimate) > process_bound + 1e-10:
            raise RuntimeError("composite policy increment exceeded its registered support bound")
        factors = bounded_betting_factors(
            np.asarray([net_estimate]),
            np.asarray([process_bound]),
            BETTING_STAKES,
        )[0]
        if np.any(factors <= 0):
            raise RuntimeError("nonpositive composite-policy betting factor")
        log_wealth += np.log(factors)
        log_e_value = float(logsumexp(log_wealth + BETTING_LOG_WEIGHTS))
        certified |= log_e_value >= -np.log(config.alpha)
        bound_total += process_bound
        processed += 1

    if labels_used > budget:
        raise RuntimeError("hard label budget was exceeded")
    stop_index = start + processed
    monitor_contexts = np.asarray(family["contexts"][start:stop_index], dtype=int)
    monitor_expected = np.zeros(processed, dtype=float)
    for group, selected in selected_by_context.items():
        if selected is None:
            continue
        selected_events = monitor_contexts == group
        event_indices = np.arange(start, stop_index)[selected_events]
        monitor_expected[selected_events] = family["h_truth"][selected, event_indices] - switch_rate
    monitor_policy_mean = float(monitor_expected.mean()) if processed else 0.0
    monitor_null = monitor_policy_mean <= 1e-12
    deploy_indices = np.arange(stop_index, config.n)
    deploy_contexts = np.asarray(family["contexts"][deploy_indices], dtype=int)
    expected_net = 0.0
    realized_net = 0.0
    selected_monitor_count = 0
    selected_count = 0
    for group, selected in selected_by_context.items():
        if selected is None:
            continue
        use_monitor = monitor_contexts == group
        selected_monitor_count += int(use_monitor.sum())
        use_deployment = deploy_contexts == group
        future_indices = deploy_indices[use_deployment]
        selected_count += len(future_indices)
        expected_net += float(np.sum(family["h_truth"][selected, future_indices] - switch_rate))
        observed_future_gain = np.where(
            y[future_indices] == 1,
            family["z1"][selected, future_indices],
            family["z0"][selected, future_indices],
        )
        realized_net += float(np.sum(observed_future_gain - switch_rate))
    promoted = bool(certified and any(value is not None for value in selected_by_context.values()))
    if not promoted:
        expected_net = realized_net = 0.0
        selected_count = 0
    selected_ids = {
        str(group): None if selected is None else family["candidate_ids"][selected]
        for group, selected in selected_by_context.items()
    }
    selected_ranks = {
        str(group): None if selected is None else selected + 1
        for group, selected in selected_by_context.items()
    }
    return {
        "scenario": scenario.name,
        "seed": None,
        "query_policy": query_name,
        "estimator": "direct_ipw",
        "monitoring_rule": "fixed_mixture",
        "budget_rate": budget_rate,
        "label_budget": budget,
        "alpha_allocation": "validation_context_policy",
        "alpha_total": config.alpha,
        "candidate_count": 1,
        "candidate_id": json.dumps(selected_ids, sort_keys=True),
        "candidate_validation_rank": None,
        "candidate_validation_ranks_by_context": json.dumps(selected_ranks, sort_keys=True),
        "selected_candidates_by_context": json.dumps(selected_ids, sort_keys=True),
        "context_weights": None,
        "validation_context_counts": json.dumps([validation_counts[group] for group in (0, 1)]),
        "candidate_is_monitor_null": monitor_null,
        "promoted": promoted,
        "pointwise_null_candidate_certified": bool(certified and monitor_null),
        "pointwise_null_candidate_certificate_count": int(certified and monitor_null),
        "selected_candidate_monitor_expected_net_gain": (
            monitor_policy_mean if selected_monitor_count else None
        ),
        "expected_postpromotion_net_gain": expected_net,
        "realized_postpromotion_net_gain": realized_net,
        "harmful_postpromotion_promotion": bool(promoted and expected_net <= 0),
        "future_mean_net_gain_per_event": expected_net / max(1, config.n - stop_index),
        "labels_queried": labels_used,
        "expected_labels_queried": expected_labels,
        "budget_utilization": labels_used / budget,
        "monitor_events_processed": processed,
        "monitor_fraction_processed": processed / length,
        "process_bound": bound_total / max(1, processed),
        "global_process_bound": process_bound,
        "mean_event_process_bound": bound_total / max(1, processed),
        "max_event_process_bound": process_bound if processed else 0.0,
        "bound_mode": "global",
        "stop_reason": stop_reason,
        "q_min": q_min,
        "propensity_min": float(q_path[:processed].min()) if processed else None,
        "propensity_max": float(q_path[:processed].max()) if processed else None,
        "switching_cost": switch_rate * selected_count,
        "evaluation_start_index": stop_index,
        "training_end_index": family["train_end"],
        "validation_end_index": family["validation_end"],
        "shadow_end_index": end,
        "deployment_end_index": config.n,
        "familywise_alpha_sum": config.alpha,
        "pointwise_null_candidate_count": int(monitor_null),
        "context_policy_events": selected_count,
        "context_feature_index": config.context_feature_index,
        "context_threshold": config.context_threshold,
    }


def _monitor_scout_context_policy(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    scenario,
    config: BudgetedPromotionConfig,
    query_name: str,
    budget_rate: float,
    query_uniforms: np.ndarray,
) -> dict[str, Any]:
    """Use an early target slice to select one policy, then certify it on fresh events."""
    if not config.include_scout_context_policy:
        raise ValueError("enable include_scout_context_policy to run this monitor")
    start = family["validation_end"]
    end = family["monitor_end"]
    length = family["monitor_length"]
    scout_length = length // 2
    certification_start = start + scout_length
    budget = int(np.floor(budget_rate * length))
    if budget < 1 or scout_length < 1 or scout_length >= length:
        raise ValueError("configured budget or monitor horizon is too small for two stages")
    q_path = family["q_paths"][(query_name, budget_rate)]
    q_min = family["q_min"][budget_rate]
    switch_rate = config.switching_cost / family["deployment_length"]
    outcome_bound = float(max(scenario.fn_cost, scenario.fp_cost))
    process_bound = outcome_bound / q_min + switch_rate
    candidates = family["actions"].shape[0]

    scout_sums = np.zeros((candidates, 2), dtype=float)
    scout_counts = np.zeros(2, dtype=int)
    labels_used = 0
    scout_labels = 0
    expected_labels = 0.0
    scout_processed = 0
    stop_reason = "monitor_horizon"
    for relative in range(scout_length):
        if budget - labels_used < 1:
            stop_reason = "label_budget_exhausted_during_scout"
            break
        event_index = start + relative
        group = int(family["contexts"][event_index])
        propensity = float(q_path[relative])
        if propensity + 1e-12 < q_min:
            raise RuntimeError("query policy violated its registered propensity floor")
        scout_counts[group] += 1
        scout_processed += 1
        expected_labels += propensity
        queried = bool(query_uniforms[relative] < propensity)
        if queried:
            labels_used += 1
            scout_labels += 1
            observed = (
                family["z1"][:, event_index] if y[event_index] else family["z0"][:, event_index]
            )
            scout_sums[:, group] += observed / propensity

    selected_by_context: dict[int, int | None] = {}
    selection_gain_by_context: dict[int, float | None] = {}
    for group in (0, 1):
        if scout_counts[group] == 0:
            selected_by_context[group] = None
            selection_gain_by_context[group] = None
            continue
        estimated_gain = scout_sums[:, group] / scout_counts[group]
        net_gain = estimated_gain - switch_rate
        best = int(np.argmax(net_gain))
        selection_gain_by_context[group] = float(net_gain[best])
        selected_by_context[group] = best if net_gain[best] > 0 else None

    log_wealth = np.zeros(len(BETTING_STAKES), dtype=float)
    log_e_value = 0.0
    certified = False
    processed = 0
    bound_total = 0.0
    for relative in range(scout_length, length):
        if budget - labels_used < 1:
            stop_reason = "label_budget_exhausted_during_certification"
            break
        event_index = start + relative
        propensity = float(q_path[relative])
        if propensity + 1e-12 < q_min:
            raise RuntimeError("query policy violated its registered propensity floor")
        group = int(family["contexts"][event_index])
        selected = selected_by_context[group]
        expected_labels += propensity
        queried = bool(query_uniforms[relative] < propensity)
        if queried:
            labels_used += 1
            if selected is None:
                estimate = 0.0
            else:
                observed_gain = (
                    family["z1"][selected, event_index]
                    if y[event_index]
                    else family["z0"][selected, event_index]
                )
                estimate = observed_gain / propensity
        else:
            estimate = 0.0
        increment = estimate - switch_rate if selected is not None else 0.0
        if abs(increment) > process_bound + 1e-10:
            raise RuntimeError("scout-policy increment exceeded its registered support bound")
        factors = bounded_betting_factors(
            np.asarray([increment]), np.asarray([process_bound]), BETTING_STAKES
        )[0]
        if np.any(factors <= 0):
            raise RuntimeError("nonpositive scout-policy betting factor")
        log_wealth += np.log(factors)
        log_e_value = float(logsumexp(log_wealth + BETTING_LOG_WEIGHTS))
        certified |= log_e_value >= -np.log(config.alpha)
        bound_total += process_bound
        processed += 1

    if labels_used > budget:
        raise RuntimeError("hard label budget was exceeded")
    stop_index = start + scout_length + processed
    cert_indices = np.arange(certification_start, stop_index)
    cert_contexts = np.asarray(family["contexts"][cert_indices], dtype=int)
    monitor_expected = np.zeros(processed, dtype=float)
    for group, selected in selected_by_context.items():
        if selected is not None:
            use_group = cert_contexts == group
            monitor_expected[use_group] = (
                family["h_truth"][selected, cert_indices[use_group]] - switch_rate
            )
    monitor_policy_mean = float(monitor_expected.mean()) if processed else 0.0
    monitor_null = monitor_policy_mean <= 1e-12

    deploy_indices = np.arange(stop_index, config.n)
    deployment_contexts = np.asarray(family["contexts"][deploy_indices], dtype=int)
    expected_net = 0.0
    realized_net = 0.0
    selected_count = 0
    for group, selected in selected_by_context.items():
        if selected is None:
            continue
        use_group = deployment_contexts == group
        future_indices = deploy_indices[use_group]
        selected_count += len(future_indices)
        expected_net += float(np.sum(family["h_truth"][selected, future_indices] - switch_rate))
        observed_future = np.where(
            y[future_indices] == 1,
            family["z1"][selected, future_indices],
            family["z0"][selected, future_indices],
        )
        realized_net += float(np.sum(observed_future - switch_rate))
    promoted = bool(certified and any(value is not None for value in selected_by_context.values()))
    if not promoted:
        expected_net = realized_net = 0.0
        selected_count = 0

    selected_ids = {
        str(group): None if selected is None else family["candidate_ids"][selected]
        for group, selected in selected_by_context.items()
    }
    selected_ranks = {
        str(group): None if selected is None else selected + 1
        for group, selected in selected_by_context.items()
    }
    return {
        "scenario": scenario.name,
        "seed": None,
        "query_policy": query_name,
        "estimator": "direct_ipw",
        "monitoring_rule": "fixed_mixture",
        "budget_rate": budget_rate,
        "label_budget": budget,
        "alpha_allocation": "scout_context_policy",
        "alpha_total": config.alpha,
        "candidate_count": 1,
        "candidate_id": json.dumps(selected_ids, sort_keys=True),
        "candidate_validation_rank": None,
        "candidate_validation_ranks_by_context": json.dumps(selected_ranks, sort_keys=True),
        "selected_candidates_by_context": json.dumps(selected_ids, sort_keys=True),
        "context_weights": None,
        "validation_context_counts": json.dumps(scout_counts.tolist()),
        "scout_selection_gain_by_context": json.dumps(selection_gain_by_context, sort_keys=True),
        "candidate_is_monitor_null": monitor_null,
        "promoted": promoted,
        "pointwise_null_candidate_certified": bool(certified and monitor_null),
        "pointwise_null_candidate_certificate_count": int(certified and monitor_null),
        "selected_candidate_monitor_expected_net_gain": (
            monitor_policy_mean if processed else None
        ),
        "expected_postpromotion_net_gain": expected_net,
        "realized_postpromotion_net_gain": realized_net,
        "harmful_postpromotion_promotion": bool(promoted and expected_net <= 0),
        "future_mean_net_gain_per_event": expected_net / max(1, config.n - stop_index),
        "labels_queried": labels_used,
        "scout_labels_queried": scout_labels,
        "expected_labels_queried": expected_labels,
        "budget_utilization": labels_used / budget,
        "monitor_events_processed": processed,
        "scout_events_processed": scout_processed,
        "monitor_fraction_processed": processed / length,
        "certification_fraction_processed": processed / max(1, length - scout_length),
        "process_bound": bound_total / max(1, processed),
        "global_process_bound": process_bound,
        "mean_event_process_bound": bound_total / max(1, processed),
        "max_event_process_bound": process_bound if processed else 0.0,
        "bound_mode": "global",
        "stop_reason": stop_reason,
        "q_min": q_min,
        "propensity_min": float(q_path[scout_length : scout_length + processed].min())
        if processed
        else None,
        "propensity_max": float(q_path[scout_length : scout_length + processed].max())
        if processed
        else None,
        "switching_cost": switch_rate * selected_count,
        "evaluation_start_index": stop_index,
        "training_end_index": family["train_end"],
        "validation_end_index": family["validation_end"],
        "shadow_end_index": end,
        "deployment_end_index": config.n,
        "familywise_alpha_sum": config.alpha,
        "pointwise_null_candidate_count": int(monitor_null),
        "context_policy_events": selected_count,
        "context_feature_index": config.context_feature_index,
        "context_threshold": config.context_threshold,
        "selection_start_index": start,
        "selection_end_index": certification_start,
        "certification_start_index": certification_start,
        "scout_fraction": 0.5,
    }


def _run_seed(
    *,
    scenario,
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    scout_only: bool = False,
    scout_switching_costs: tuple[float, ...] | None = None,
) -> list[dict[str, Any]]:
    source_config = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        window=64,
        stride=32,
        alpha=config.alpha,
        eprocess_epsilon=0.1,
        seed_offset=seed,
        device=device,
    )
    generation_scenario = (
        SCENARIOS[0]
        if scenario.name
        in {
            "candidate_family_null",
            "candidate_context_zero_mean",
            "candidate_context_heterogeneity",
        }
        else scenario
    )
    _, frame, oracle, _ = _generate(generation_scenario, seed, source_config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = (frame.target.to_numpy(dtype=float) > 0).astype(int)
    probability_true = oracle.probability_positive.to_numpy(dtype=float)
    if scenario.name == "candidate_context_zero_mean":
        import torch

        torch_generator = torch.Generator(device=device).manual_seed(seed + 8_271_019)
        event_probability = scenario.fp_cost / (scenario.fn_cost + scenario.fp_cost)
        y = (
            (torch.rand(config.n, generator=torch_generator, device=device) < event_probability)
            .cpu()
            .numpy()
            .astype(int)
        )
        probability_true = np.full(config.n, event_probability, dtype=float)
    elif scenario.name == "candidate_context_heterogeneity":
        x, y, probability_true = _inject_context_heterogeneity(
            x=x,
            y=y,
            probability_true=probability_true,
            seed=seed,
            config=config,
            device=device,
            fn_cost=scenario.fn_cost,
            fp_cost=scenario.fp_cost,
        )
    family = _fit_candidate_family(
        x=x,
        y=y,
        probability_true=probability_true,
        scenario=scenario,
        config=config,
    )

    import torch

    generator = torch.Generator(device=device).manual_seed(seed + 700_001)
    uniforms = (
        torch.rand(
            (len(config.query_policies), family["monitor_length"]),
            generator=generator,
            device=device,
        )
        .cpu()
        .numpy()
    )
    output = []
    if scout_switching_costs is not None and not scout_only:
        raise ValueError("multiple scout switching charges require a scout-only run")
    if scout_switching_costs is not None and not config.include_scout_context_policy:
        raise ValueError("multiple scout switching charges require the scout policy")
    if scout_switching_costs is not None and (
        not scout_switching_costs
        or len(set(scout_switching_costs)) != len(scout_switching_costs)
        or any(not np.isfinite(cost) or cost < 0 for cost in scout_switching_costs)
    ):
        raise ValueError("scout switching charges must be finite, nonnegative, and unique")
    scout_configs = (
        tuple(replace(config, switching_cost=cost) for cost in scout_switching_costs)
        if scout_switching_costs is not None
        else (config,)
    )
    for query_index, query_name in enumerate(config.query_policies):
        for budget_rate in config.budget_rates:
            if not scout_only:
                for estimator in config.estimators:
                    for monitoring_rule in config.monitoring_rules:
                        estimator_rows = _monitor_family(
                            family=family,
                            y=y,
                            scenario=scenario,
                            config=config,
                            query_name=query_name,
                            budget_rate=budget_rate,
                            estimator=estimator,
                            query_uniforms=uniforms[query_index],
                            bound_mode=config.bound_mode,
                            monitoring_rule=monitoring_rule,
                        )
                        for row in estimator_rows:
                            row["seed"] = seed
                            row["query_rng_stream"] = query_index
                            row["top_validation_gain"] = family["top_validation_gain"]
                        output.extend(estimator_rows)
            if config.include_validation_context_policy:
                row = _monitor_validation_context_policy(
                    family=family,
                    y=y,
                    scenario=scenario,
                    config=config,
                    query_name=query_name,
                    budget_rate=budget_rate,
                    query_uniforms=uniforms[query_index],
                )
                row["seed"] = seed
                row["query_rng_stream"] = query_index
                row["top_validation_gain"] = family["top_validation_gain"]
                output.append(row)
            elif config.include_scout_context_policy:
                for scout_config in scout_configs:
                    row = _monitor_scout_context_policy(
                        family=family,
                        y=y,
                        scenario=scenario,
                        config=scout_config,
                        query_name=query_name,
                        budget_rate=budget_rate,
                        query_uniforms=uniforms[query_index],
                    )
                    row["seed"] = seed
                    row["query_rng_stream"] = query_index
                    row["top_validation_gain"] = family["top_validation_gain"]
                    row["registered_switching_cost"] = scout_config.switching_cost
                    output.append(row)
    if scenario.name == "candidate_context_heterogeneity":
        observed_prevalence = float(
            family["validation_context_counts"][1] / family["validation_context_counts"].sum()
        )
        for row in output:
            row["context_target_prevalence"] = config.context_target_prevalence
            row["context_signal_strength"] = config.context_signal_strength
            row["context_proxy_error"] = config.context_proxy_error
            row["context_observed_prevalence"] = observed_prevalence
    return output


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return float("nan"), float("nan")
    z = float(norm.ppf(0.975))
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _inject_context_heterogeneity(
    *,
    x: np.ndarray,
    y: np.ndarray,
    probability_true: np.ndarray,
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    fn_cost: float = 5.0,
    fp_cost: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Add a frozen noisy context feature and a target-only context signal.

    Latent group membership is used only to generate evaluator probabilities and
    outcomes. The learner receives its independently corrupted binary proxy as a
    feature, before any monitor outcome is revealed.
    """
    import torch

    if config.context_feature_index < 2:
        raise ValueError("context heterogeneity needs a proxy feature outside signal x[0:2]")
    if fn_cost != 5.0 or fp_cost != 1.0:
        raise ValueError("registered context heterogeneity DGP assumes FN=5 and FP=1")
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=int).copy()
    probability_true = np.asarray(probability_true, dtype=float).copy()
    latent_threshold = norm.ppf(1 - config.context_target_prevalence)
    latent_context = x[:, 0] >= latent_threshold

    context_generator = torch.Generator(device=device).manual_seed(seed + 9_733_101)
    proxy_flips = (
        torch.rand(len(x), generator=context_generator, device=device).cpu().numpy()
        < config.context_proxy_error
    )
    observed_context = np.logical_xor(latent_context, proxy_flips)
    x[:, config.context_feature_index] = np.where(observed_context, 1.0, -1.0)

    # Begin the target law at the monitor boundary. At delta=0 both actions have
    # equal expected cost; positive delta moves groups to opposite sides of the
    # FN=5, FP=1 Bayes threshold and creates heterogeneous candidate value.
    _, validation_end, _ = _time_splits(len(y))
    decision_threshold = fp_cost / (fn_cost + fp_cost)
    target_probability = np.where(
        latent_context,
        decision_threshold + config.context_signal_strength,
        decision_threshold - config.context_signal_strength,
    )
    outcome_generator = torch.Generator(device=device).manual_seed(seed + 9_733_102)
    outcome_uniforms = (
        torch.rand(
            len(y) - validation_end,
            generator=outcome_generator,
            device=device,
        )
        .cpu()
        .numpy()
    )
    y[validation_end:] = (outcome_uniforms < target_probability[validation_end:]).astype(int)
    probability_true[validation_end:] = target_probability[validation_end:]
    return x, y, probability_true


def _summarize(detail: pd.DataFrame) -> pd.DataFrame:
    group_fields = [
        "scenario",
        "budget_rate",
        "query_policy",
        "estimator",
        "monitoring_rule",
        "alpha_allocation",
    ]
    rows = []
    for key, group in detail.groupby(group_fields, sort=False):
        scenario, budget_rate, query_policy, estimator, monitoring_rule, allocation = key
        promotion = int(group.promoted.sum())
        promotion_ci = _wilson(promotion, len(group))
        pointwise_null_count = int(group.pointwise_null_candidate_certified.sum())
        pointwise_null_ci = _wilson(pointwise_null_count, len(group))
        future_harm_count = int(group.harmful_postpromotion_promotion.sum())
        harm_ci = _wilson(future_harm_count, len(group))
        gains = group.expected_postpromotion_net_gain.to_numpy(dtype=float)
        realized = group.realized_postpromotion_net_gain.to_numpy(dtype=float)

        def interval(values: np.ndarray) -> tuple[float, float]:
            if len(values) < 2:
                return float("nan"), float("nan")
            radius = float(t.ppf(0.975, len(values) - 1) * sem(values))
            return float(values.mean() - radius), float(values.mean() + radius)

        gain_ci = interval(gains)
        realized_ci = interval(realized)
        rows.append(
            {
                "scenario": scenario,
                "budget_rate": budget_rate,
                "query_policy": query_policy,
                "estimator": estimator,
                "monitoring_rule": monitoring_rule,
                "alpha_allocation": allocation,
                "n_seeds": len(group),
                "candidate_count": int(group.candidate_count.iloc[0]),
                "promotion_rate": float(group.promoted.mean()),
                "promotion_ci_low": promotion_ci[0],
                "promotion_ci_high": promotion_ci[1],
                "pointwise_null_certificate_rate": float(
                    group.pointwise_null_candidate_certified.mean()
                ),
                "pointwise_null_ci_low": pointwise_null_ci[0],
                "pointwise_null_ci_high": pointwise_null_ci[1],
                "mean_expected_postpromotion_net_gain": float(gains.mean()),
                "expected_gain_ci_low": gain_ci[0],
                "expected_gain_ci_high": gain_ci[1],
                "mean_realized_postpromotion_net_gain": float(realized.mean()),
                "realized_gain_ci_low": realized_ci[0],
                "realized_gain_ci_high": realized_ci[1],
                "future_harmful_promotion_rate": float(
                    group.harmful_postpromotion_promotion.mean()
                ),
                "future_harm_ci_low": harm_ci[0],
                "future_harm_ci_high": harm_ci[1],
                "mean_labels_queried": float(group.labels_queried.mean()),
                "mean_label_budget": float(group.label_budget.mean()),
                "mean_budget_utilization": float(group.budget_utilization.mean()),
                "mean_monitor_fraction_processed": float(group.monitor_fraction_processed.mean()),
                "mean_expected_labels_queried": float(group.expected_labels_queried.mean()),
                "mean_process_bound": float(group.process_bound.mean()),
                "mean_familywise_alpha_sum": float(group.familywise_alpha_sum.mean()),
            }
        )
    return pd.DataFrame(rows)


def _paired_bootstrap_contrasts(
    detail: pd.DataFrame, *, seed: int = 23102026, draws: int = 10_000
) -> pd.DataFrame:
    """Matched-seed secondary contrasts at the predeclared 20% label cap."""
    if draws < 1000:
        raise ValueError("paired bootstrap requires at least 1000 draws")
    result_columns = [
        "scenario",
        "budget_rate",
        "contrast",
        "query_policy",
        "monitoring_rule",
        "metric",
        "n_seed_pairs",
        "mean_paired_difference",
        "bootstrap_ci_low",
        "bootstrap_ci_high",
        "bootstrap_draws",
        "bootstrap_seed",
    ]
    if "monitoring_rule" not in detail:
        detail = detail.copy()
        detail["monitoring_rule"] = "fixed_mixture"
    if detail.seed.nunique() < 2:
        return pd.DataFrame(columns=result_columns)
    rng = np.random.default_rng(seed)
    primary = detail[detail.budget_rate.eq(0.20)]
    contrasts: list[tuple[str, pd.DataFrame, pd.DataFrame, str, str, str]] = []

    # Estimator comparison uses the established rank-spending candidate alpha rule.
    keys = ["scenario", "query_policy", "monitoring_rule"]
    for key, group in primary[primary.alpha_allocation.eq("rank")].groupby(keys, sort=False):
        ppi = group[group.estimator.eq("prediction_powered")].sort_values("seed")
        ipw = group[group.estimator.eq("direct_ipw")].sort_values("seed")
        if ppi.empty or ipw.empty:
            continue
        if len(ppi) != len(ipw) or not np.array_equal(ppi.seed.to_numpy(), ipw.seed.to_numpy()):
            raise ValueError("estimators are not paired on identical seed sets")
        contrasts.append(("direct_ipw_minus_prediction_powered", ipw, ppi, key[0], key[1], key[2]))

    # Candidate-alpha allocation comparison fixes query draws and estimator.
    for (scenario, query, monitoring_rule), group in primary[
        primary.estimator.eq("direct_ipw")
    ].groupby(keys, sort=False):
        rank = group[group.alpha_allocation.eq("rank")].sort_values("seed")
        for allocation in ("equal", "validation_power", *CONTEXT_ALPHA_ALLOCATIONS):
            comparator = group[group.alpha_allocation.eq(allocation)].sort_values("seed")
            if rank.empty or comparator.empty:
                continue
            if len(rank) != len(comparator) or not np.array_equal(
                rank.seed.to_numpy(), comparator.seed.to_numpy()
            ):
                raise ValueError("alpha allocations are not paired on identical seed sets")
            contrasts.append(
                (f"rank_minus_{allocation}", rank, comparator, scenario, query, monitoring_rule)
            )

    # Acquisition comparison fixes direct IPW and rank spending.
    query_group = primary[primary.estimator.eq("direct_ipw") & primary.alpha_allocation.eq("rank")]
    for (scenario, monitoring_rule), group in query_group.groupby(
        ["scenario", "monitoring_rule"], sort=False
    ):
        uniform = group[group.query_policy.eq("uniform")].sort_values("seed")
        for query in ("variance", "decision_value"):
            adaptive = group[group.query_policy.eq(query)].sort_values("seed")
            if uniform.empty or adaptive.empty:
                continue
            if len(uniform) != len(adaptive) or not np.array_equal(
                uniform.seed.to_numpy(), adaptive.seed.to_numpy()
            ):
                raise ValueError("query policies are not paired on identical seed sets")
            contrasts.append(
                (f"{query}_minus_uniform", adaptive, uniform, scenario, query, monitoring_rule)
            )

    # Monitoring-rule comparisons fix the seed, estimator, query path, budget,
    # and candidate alpha allocation; only the e-process construction changes.
    rule_keys = ["scenario", "query_policy", "estimator", "alpha_allocation"]
    for key, group in primary.groupby(rule_keys, sort=False):
        fixed = group[group.monitoring_rule.eq("fixed_mixture")].sort_values("seed")
        for monitoring_rule in MONITORING_RULES:
            if monitoring_rule == "fixed_mixture" or monitoring_rule not in set(
                group.monitoring_rule
            ):
                continue
            method = group[group.monitoring_rule.eq(monitoring_rule)].sort_values("seed")
            if fixed.empty or method.empty:
                continue
            if len(fixed) != len(method) or not np.array_equal(
                fixed.seed.to_numpy(), method.seed.to_numpy()
            ):
                raise ValueError("monitoring rules are not paired on identical seed sets")
            contrasts.append(
                (
                    f"{monitoring_rule}_minus_fixed_mixture",
                    method,
                    fixed,
                    key[0],
                    key[1],
                    monitoring_rule,
                )
            )

    rows: list[dict[str, Any]] = []
    metrics = {
        "expected_postpromotion_net_gain": "expected_net_gain",
        "promoted": "promotion",
        "labels_queried": "labels_queried",
        "monitor_fraction_processed": "monitor_fraction_processed",
    }
    for contrast_name, treatment, comparator, scenario, query, monitoring_rule in contrasts:
        n = len(treatment)
        if n < 2:
            raise ValueError("paired comparison cells require identical multi-seed samples")
        indices = rng.integers(0, n, size=(draws, n))
        for source, label in metrics.items():
            left = treatment[source].to_numpy(dtype=float)
            right = comparator[source].to_numpy(dtype=float)
            differences = left - right
            bootstrap = differences[indices].mean(axis=1)
            rows.append(
                {
                    "scenario": scenario,
                    "budget_rate": 0.20,
                    "contrast": contrast_name,
                    "query_policy": query,
                    "monitoring_rule": monitoring_rule,
                    "metric": label,
                    "n_seed_pairs": n,
                    "mean_paired_difference": float(differences.mean()),
                    "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                    "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                    "bootstrap_draws": draws,
                    "bootstrap_seed": seed,
                }
            )
    return pd.DataFrame(rows, columns=result_columns)


def _append_paired_report(report_path: Path, paired: pd.DataFrame) -> None:
    selected = paired[
        paired.scenario.isin(["boundary_local_harm", "recurring_regimes", "harmful_adaptation"])
        & paired.metric.eq("expected_net_gain")
    ]
    lines = [
        "",
        "## Paired analysis at the 20% cap",
        "",
        "The secondary contrasts resample matched seed pairs within the predeclared design cells. They include estimator, alpha-allocation, query-policy, and monitoring-rule comparisons when those dimensions vary. The 95% percentile intervals are descriptive and unadjusted across contrasts; the full table is in `metrics/budgeted_promotion_paired_contrasts.parquet`.",
        "",
        "| Scenario | Contrast | Query | Monitoring rule | Mean paired net-gain difference (95% bootstrap CI) |",
        "|---|---|---|---|---:|",
    ]
    for row in selected.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.contrast} | {row.query_policy} | {row.monitoring_rule} | {row.mean_paired_difference:.3f} [{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}] |"
        )
    with report_path.open("a", encoding="utf-8") as report:
        report.write("\n".join(lines) + "\n")


def _plot(summary: pd.DataFrame, path: Path) -> None:
    scenarios = list(summary.scenario.drop_duplicates())
    budget_rate = float(summary.budget_rate.max())
    estimator = next(name for name in ESTIMATORS if name in set(summary.estimator))
    monitoring_values = [name for name in MONITORING_RULES if name in set(summary.monitoring_rule)]
    query = next(name for name in QUERY_POLICIES if name in set(summary.query_policy))
    allocation = next(name for name in ALPHA_ALLOCATIONS if name in set(summary.alpha_allocation))
    cell = summary[
        summary.budget_rate.eq(budget_rate)
        & summary.estimator.eq(estimator)
        & summary.query_policy.eq(query)
        & summary.alpha_allocation.eq(allocation)
    ].set_index(["scenario", "monitoring_rule"])
    cell = cell.reindex(
        pd.MultiIndex.from_product(
            [scenarios, monitoring_values], names=["scenario", "monitoring_rule"]
        )
    )
    fig, axes = plt.subplots(1, 2, figsize=(18, 7), sharex=True)
    positions = np.arange(len(scenarios))
    width = 0.82 / len(monitoring_values)
    for index, rule in enumerate(monitoring_values):
        rows = cell.xs(rule, level="monitoring_rule").reindex(scenarios)
        offset = (index - (len(monitoring_values) - 1) / 2) * width
        axes[0].bar(positions + offset, rows.promotion_rate, width, label=rule)
        gain = rows.mean_expected_postpromotion_net_gain.to_numpy()
        low = rows.expected_gain_ci_low.to_numpy()
        high = rows.expected_gain_ci_high.to_numpy()
        axes[1].bar(
            positions + offset,
            gain,
            width,
            label=rule,
            yerr=np.vstack((gain - low, high - gain)),
            capsize=2,
        )
    axes[0].set_ylabel("Promotion rate")
    axes[0].set_ylim(bottom=0)
    axes[0].set_title("Promotion probability")
    axes[1].set_ylabel("Mean expected future net gain")
    axes[1].set_title("Post-promotion value (95% t intervals)")
    for axis in axes:
        axis.axhline(0, color="black", linewidth=0.8)
        axis.grid(axis="y", alpha=0.25)
        axis.set_xticks(positions, scenarios, rotation=35, ha="right", fontsize=9)
    axes[1].legend(fontsize=8, title="Monitoring rule", loc="best")
    fig.suptitle(
        f"Repeated-candidate promotion · {budget_rate:.0%} cap · {estimator} · {query} · {allocation} spending"
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def run_budgeted_promotion(
    config: BudgetedPromotionConfig, output: Path, *, reuse_detail: bool = False
) -> Path:
    config.validate()
    device = resolve_device(config.device, n=config.n, d=config.d, chunk_size=2048)
    config = BudgetedPromotionConfig(**{**asdict(config), "device": device})
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metrics_dir / "budgeted_promotion_streams.parquet"
    summary_path = metrics_dir / "budgeted_promotion_summary.parquet"
    paired_path = metrics_dir / "budgeted_promotion_paired_contrasts.parquet"
    if (detail_path.exists() or summary_path.exists()) and not reuse_detail:
        raise FileExistsError(f"refusing to overwrite existing budgeted promotion run: {output}")
    scenarios = (
        *SCENARIOS,
        type(SCENARIOS[0])(
            name="candidate_family_null",
            dgp=SCENARIOS[0].dgp,
            description="All frozen candidates are exact copies of the incumbent policy.",
        ),
        type(SCENARIOS[0])(
            name="candidate_context_zero_mean",
            dgp=SCENARIOS[0].dgp,
            description=(
                "Outcomes are independent of features with P(Y=1)=FP/(FN+FP), so every "
                "frozen action has equal conditional expected cost in both feature contexts."
            ),
        ),
    )
    if config.scenario_subset:
        scenarios = tuple(
            scenario for scenario in scenarios if scenario.name in config.scenario_subset
        )
    if reuse_detail:
        if not detail_path.exists():
            raise FileNotFoundError(f"cannot reuse missing seed-level metrics: {detail_path}")
        detail = pd.read_parquet(detail_path)
        expected_scenarios = {scenario.name for scenario in scenarios}
        expected_seeds = set(range(config.seed_offset, config.seed_offset + config.seeds))
        if (
            set(detail.scenario.unique()) != expected_scenarios
            or set(detail.seed.unique()) != expected_seeds
            or set(detail.monitoring_rule.unique()) != set(config.monitoring_rules)
            or set(detail.query_policy.unique()) != set(config.query_policies)
            or set(detail.estimator.unique()) != set(config.estimators)
            or set(detail.alpha_allocation.unique()) != set(config.alpha_allocations)
            or set(detail.budget_rate.unique()) != set(config.budget_rates)
        ):
            raise ValueError(
                "saved seed-level metrics do not match the requested experiment config"
            )
    else:
        records: list[dict[str, Any]] = []
        for scenario in scenarios:
            print(
                f"budgeted-promotion scenario={scenario.name} seeds={config.seeds} device={device}",
                flush=True,
            )
            for replicate in range(config.seeds):
                seed = config.seed_offset + replicate
                records.extend(
                    _run_seed(scenario=scenario, seed=seed, config=config, device=device)
                )
        detail = pd.DataFrame(records)
    summary = _summarize(detail)
    detail.to_parquet(detail_path, index=False)
    summary.to_parquet(summary_path, index=False)
    paired = _paired_bootstrap_contrasts(detail)
    paired.to_parquet(paired_path, index=False)
    figure_path = output / "figures/budgeted_promotion_grid.png"
    if config.create_plot:
        _plot(summary, figure_path)

    if config.bound_mode == "global":
        bound_description = (
            "The fixed global bounds support the history-conditional mean-gain null."
        )
    else:
        bound_description = (
            "Decision-local bounds are predictable from current covariates and support only the "
            "pointwise conditional null given those covariates. Rejecting that null does not "
            "certify positive average net gain, so a crossing in this mode is a conditional-null "
            "diagnostic and is not a promotion authorization."
        )
    scenario_clause = (
        f" --scenario-subset {' '.join(config.scenario_subset)}" if config.scenario_subset else ""
    )

    lines = [
        "# Repeated-candidate promotion under a hard label budget",
        "",
        f"This benchmark evaluates {len(scenarios)} scenarios with {config.seeds} independent seeds each on `{device}`. It crosses {len(config.query_policies)} predeclared query designs, {len(config.estimators)} estimators, {len(config.monitoring_rules)} monitoring rules, {len(config.alpha_allocations)} candidate-level alpha allocations, and hard label caps {config.budget_rates}. Every query design and candidate gate sees the same seed-specific DGP; all candidate tests within one stream share queried labels. Each stream has {len(_candidate_alpha_allocations([{'candidate_id': str(i), 'validation_gain': 0.0, 'validation_gain_se': 0.0} for i in range(13)], alpha=config.alpha))} frozen candidates.",
        "",
        f"Candidates are trained on the training slice and ordered using the fully labeled validation slice. Validation also fixes candidate alpha weights and the acquisition score model. Monitor labels are revealed only when queried. This run uses query design(s) {', '.join(config.query_policies)}; propensities are predictable from current covariates and pre-monitor fits, with a positive floor. For each budget level the same maximum number of labels is available to every configured method. The monitor stops before the next event when no label remains affordable, so actual label counts never exceed the hard cap; realized counts and processed horizons are reported because policies need not spend the entire cap.",
        "",
        f"The implementation supports prediction-powered `h_tk + I_t/q_t (Z_tk-h_tk)` and direct inverse-propensity `I_t Z_tk/q_t` estimates; this run uses {', '.join(config.estimators)}. Both estimates are shifted by the amortized switching charge. Configured monitors are {', '.join(config.monitoring_rules)}. The fixed-mixture half-alpha reference matches the half-weighted hedge branch's threshold. They use the same candidate-level alpha spending rule(s) {', '.join(config.alpha_allocations)} and global bound. Here `Z` is incumbent cost minus candidate cost, `h` is a pre-monitor fitted expected-cost contrast, and the deployment horizon is `H`. With `|Z|,|h| <= M=max(FN,FP)`, the global-mode bounds are `M(2/q_min-1)+k_switch/H` and `M/q_min+k_switch/H`; local-mode bounds are computed per candidate and event from estimator support. Candidate alpha weights are fixed before monitor outcomes and sum to at most alpha. {bound_description} The global-null control replaces all candidates with incumbent copies; its zero-crossing result is a degenerate implementation diagnostic, not evidence of calibration.",
        f"Context alpha methods define a learner-visible group by `x[{config.context_feature_index}] >= {config.context_threshold:g}`. The context weights use only validation covariate counts; candidate rank weights use validation outcomes; their products sum to at most alpha. They are currently restricted to the fixed-mixture monitor and common global support bound. Context-specific switching cost is prorated by the number of deployment events using that context's candidate (`k_switch/H` per such event); the pooled rank comparator pays the full charge when deployed on every event. This models exposure-scaled update/deployment cost and requires that interpretation for utility comparisons.",
        "",
        "The synthetic evaluator alone accesses true outcome probabilities and unqueried future labels. It scores expected and realized post-promotion value on the untouched remainder of the stream, subtracting the switching charge once. This assumes policy actions do not alter outcomes; the result does not identify policy value under performative feedback. The repeated query/alpha/scenario grid is descriptive: cellwise intervals are not adjusted for choosing a method, and no winner is selected from the evaluation results.",
        "",
        "## Results",
        "",
        "| Scenario | Label cap | Query policy | Estimator | Monitoring rule | Alpha allocation | Promotion rate (95% CI) | Pointwise-null crossing (95% CI) | Mean oracle future net gain (95% t CI) | Mean labels / cap |",
        "|---|---:|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.budget_rate:.0%} | {row.query_policy} | {row.estimator} | {row.monitoring_rule} | {row.alpha_allocation} | {row.promotion_rate:.3f} [{row.promotion_ci_low:.3f}, {row.promotion_ci_high:.3f}] | {row.pointwise_null_certificate_rate:.3f} [{row.pointwise_null_ci_low:.3f}, {row.pointwise_null_ci_high:.3f}] | {row.mean_expected_postpromotion_net_gain:.3f} [{row.expected_gain_ci_low:.3f}, {row.expected_gain_ci_high:.3f}] | {row.mean_labels_queried:.1f} / {row.mean_label_budget:.0f} |"
        )
    lines.extend(
        [
            "",
            "The `candidate_family_null` scenario makes every candidate an exact copy; a familywise certificate there is a direct implementation diagnostic. In other scenarios, the pointwise-null diagnostic counts any crossing for a candidate whose evaluator-known conditional mean net gain is nonpositive at every realized monitor covariate. Future harmful promotion is a separate metric: a candidate can pass its shadow test and later lose value after a regime change.",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-budgeted-promotion --seeds {config.seeds} --seed-offset {config.seed_offset} --n {config.n} --device {device} --bound-mode {config.bound_mode} --context-feature-index {config.context_feature_index} --context-threshold {config.context_threshold:g} --monitoring-rules {' '.join(config.monitoring_rules)} --query-policies {' '.join(config.query_policies)} --estimators {' '.join(config.estimators)} --alpha-allocations {' '.join(config.alpha_allocations)} --budget-rates {' '.join(str(rate) for rate in config.budget_rates)}{scenario_clause} --output {output.as_posix()}`",
            "",
            "Detailed seed-level rows, aggregate metrics, configuration, environment, and hashes are stored with this report.",
        ]
    )
    report_path = reports_dir / "budgeted_promotion_grid.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _append_paired_report(report_path, paired)
    manifest = {
        "experiment": "repeated_candidate_promotion_under_hard_label_budget",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "environment": environment(),
        "scenarios": [scenario.name for scenario in scenarios],
        "query_policies": list(config.query_policies),
        "estimators": list(config.estimators),
        "monitoring_rules": list(config.monitoring_rules),
        "bound_mode": config.bound_mode,
        "alpha_allocations": list(config.alpha_allocations),
        "information_protocol": [
            "candidate models, rankings, query score models, and alpha weights are fixed before the monitor",
            "the current event label is read by the learner only when the query Bernoulli succeeds",
            "all candidate tests within a stream share the same queried labels",
            "a common pathwise cap is enforced before accessing each next event",
            "the oracle probability and unqueried outcomes are evaluator-only",
            "the global-null candidate family contains only exact copies of the incumbent",
            "context assignments are a fixed learner-visible feature threshold; validation context weights use features only",
            "context-specific policy activation incurs switching cost prorated by its exposure share",
            "decision-local crossings reject a pointwise conditional null and do not certify positive average net benefit",
            "the future-value evaluator assumes no action-dependent outcome process",
        ],
        "artifacts": [
            "metrics/budgeted_promotion_streams.parquet",
            "metrics/budgeted_promotion_summary.parquet",
            "metrics/budgeted_promotion_paired_contrasts.parquet",
            "reports/budgeted_promotion_grid.md",
        ],
    }
    if config.create_plot:
        manifest["artifacts"].append("figures/budgeted_promotion_grid.png")
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/budgeted_promotion_grid_ipw"))
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=24102026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cuda")
    parser.add_argument("--bound-mode", choices=BOUND_MODES, default="global")
    parser.add_argument("--context-feature-index", type=int, default=0)
    parser.add_argument("--context-threshold", type=float, default=0.0)
    parser.add_argument("--scenario-subset", nargs="+", default=[])
    parser.add_argument("--skip-figure", action="store_true")
    parser.add_argument(
        "--monitoring-rules", nargs="+", choices=MONITORING_RULES, default=["fixed_mixture"]
    )
    parser.add_argument(
        "--query-policies", nargs="+", choices=QUERY_POLICIES, default=list(QUERY_POLICIES)
    )
    parser.add_argument("--estimators", nargs="+", choices=ESTIMATORS, default=list(ESTIMATORS))
    parser.add_argument(
        "--alpha-allocations",
        nargs="+",
        choices=ALPHA_ALLOCATIONS,
        default=list(BASE_ALPHA_ALLOCATIONS),
    )
    parser.add_argument("--budget-rates", nargs="+", type=float, default=[0.10, 0.20])
    parser.add_argument(
        "--reuse-detail",
        action="store_true",
        help="rebuild report artifacts from matching existing seed-level Parquet metrics",
    )
    args = parser.parse_args(argv)
    config = BudgetedPromotionConfig(
        n=args.n,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        bound_mode=args.bound_mode,
        monitoring_rules=tuple(args.monitoring_rules),
        query_policies=tuple(args.query_policies),
        estimators=tuple(args.estimators),
        alpha_allocations=tuple(args.alpha_allocations),
        budget_rates=tuple(args.budget_rates),
        context_feature_index=args.context_feature_index,
        context_threshold=args.context_threshold,
        scenario_subset=tuple(args.scenario_subset),
        create_plot=not args.skip_figure,
    )
    print(run_budgeted_promotion(config, args.output, reuse_detail=args.reuse_detail), flush=True)


if __name__ == "__main__":
    main()
