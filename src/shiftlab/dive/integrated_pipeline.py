"""Run the common-stream Q1 -> candidate certification -> rollback comparison.

The default is development-only. A frozen independent-efficacy protocol and
disjoint seed block are required before selecting confirmatory status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.special import ndtri

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .budgeted_promotion import (
    BudgetedPromotionConfig,
    _candidate_outcome_contrasts,
    _fit_candidate_family,
    _monitor_scout_context_policy,
)
from .controller import ActionEstimate, Intervention, InterventionController
from .eprocess import BoundedMeanEProcess
from .experiment import _binary_cost

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "papers/shiftguard_unified/integrated_benchmark_protocol.md"
STAGES = {
    "fit_end": 800,
    "monitor_end": 1600,
    "scout_cert_end": 2400,
    "stream_end": 3200,
}
MONITOR_QUERY_RATE = 0.40
QUERY_RATE = 0.20
TOTAL_LABEL_CAP = 640
MONITOR_LABEL_CAP = 320
SCOUT_CERT_LABEL_CAP = 320
ROLLBACK_LABEL_CAP = 160
SWITCH_COST = 0.05
ROLLBACK_COST = 0.05
HARM_MARGIN = 0.10
MONITOR_ALPHA = 0.02
PROMOTION_ALPHA = 0.015
ROLLBACK_ALPHA = 0.015
SEED_OFFSET = 2026102700
PIPELINE_METHODS = (
    "continue",
    "scheduled_promote",
    "two_gate",
    "two_gate_controller",
    "q1_fallback",
    "full_pipeline",
    "full_pipeline_controller",
    "fixed_candidate_certification",
    "full_pipeline_fixed_certification",
)
LEARNER_EVENT_SCHEMA = pa.schema(
    [
        ("scenario", pa.string()),
        ("seed", pa.int64()),
        ("method", pa.string()),
        ("event_index", pa.int32()),
        ("feature_available_index", pa.int32()),
        ("prediction_decision_index", pa.int32()),
        ("stage", pa.string()),
        ("policy_version", pa.string()),
        ("action", pa.int8()),
        ("query_requested", pa.bool_()),
        ("query_probability", pa.float64()),
        ("query_stage", pa.string()),
        ("candidate_selection_available", pa.bool_()),
        ("selected_candidate_id", pa.string()),
        ("label_available_index", pa.int32()),
        ("observed_label", pa.int8()),
        ("q1_log_e_value", pa.float64()),
        ("certification_log_e_value", pa.float64()),
        ("rollback_log_e_value", pa.float64()),
        ("q1_triggered_here", pa.bool_()),
        ("promotion_certified_here", pa.bool_()),
        ("rollback_triggered_here", pa.bool_()),
        ("controller_action", pa.string()),
        ("label_resource_units", pa.int8()),
        ("intervention_cost_units", pa.float64()),
    ]
)
EVALUATOR_EVENT_SCHEMA = pa.schema(
    [
        ("scenario", pa.string()),
        ("seed", pa.int64()),
        ("method", pa.string()),
        ("event_index", pa.int32()),
        ("true_label", pa.int8()),
        ("true_positive_probability", pa.float64()),
        ("incumbent_action", pa.int8()),
        ("reference_action", pa.int8()),
        ("deployed_action", pa.int8()),
        ("incumbent_cost", pa.float64()),
        ("reference_cost", pa.float64()),
        ("deployed_cost", pa.float64()),
        ("realized_incumbent_minus_deployed_gain", pa.float64()),
        ("expected_incumbent_minus_deployed_gain", pa.float64()),
        ("intervention_cost_units", pa.float64()),
        ("evaluator_only", pa.bool_()),
    ]
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cost(actions: np.ndarray, y: np.ndarray, *, fn: float, fp: float) -> np.ndarray:
    return _binary_cost(actions, y, fn, fp)


def _install_pointwise_null_candidate_family(
    *,
    x: np.ndarray,
    family: dict[str, Any],
    probability_hat: np.ndarray,
    probability_true: np.ndarray,
    fn: float,
    fp: float,
) -> None:
    """Install a non-degenerate Q2 calibration family with pointwise nonpositive gain.

    This diagnostic family is used only by the registered calibration profile. Its
    policies switch the all-positive incumbent to negative inside nested score bands
    beginning at the Bayes decision boundary. Every switched event has nonpositive
    expected incumbent-minus-candidate gain under the stationary Gaussian-label DGP.
    The scout can still select a policy due to noise, allowing the fresh certificate
    to be tested on a genuine, non-identical challenger.
    """
    score = x[:, 0] - 0.9 * x[:, 1]
    boundary = 0.3 * float(ndtri(fp / (fn + fp)))
    widths = np.linspace(0.03, 0.30, family["actions"].shape[0])
    actions = np.ones_like(family["actions"], dtype=int)
    for candidate, width in enumerate(widths):
        actions[candidate, (score >= boundary) & (score <= boundary + width)] = 0
    family["actions"] = actions
    z0, z1 = _candidate_outcome_contrasts(
        np.asarray(family["incumbent"], dtype=int), actions, fn=fn, fp=fp
    )
    family["z0"], family["z1"] = z0, z1
    family["h_proxy"] = (1 - probability_hat[None, :]) * z0 + probability_hat[None, :] * z1
    family["h_truth"] = (1 - probability_true[None, :]) * z0 + probability_true[None, :] * z1


def _candidate_active_mask(start: int, end: int, rollback_alarm_index: int | None) -> np.ndarray:
    """Candidate remains active on the rollback-alarm event itself."""
    events = np.arange(start, end, dtype=int)
    return (
        np.ones(len(events), dtype=bool)
        if rollback_alarm_index is None
        else events <= rollback_alarm_index
    )


def _paired_contrasts(detail: pd.DataFrame, *, draws: int = 10_000) -> pd.DataFrame:
    """Descriptive seed-paired bootstrap intervals; not multiplicity adjusted."""
    comparisons = (
        ("full_pipeline", "continue"),
        ("full_pipeline_fixed_certification", "continue"),
        ("two_gate", "continue"),
        ("scheduled_promote", "continue"),
        ("q1_fallback", "continue"),
        ("full_pipeline", "two_gate"),
        ("full_pipeline", "full_pipeline_fixed_certification"),
        ("full_pipeline", "q1_fallback"),
    )
    rng = np.random.default_rng(2026102701)
    rows: list[dict[str, Any]] = []
    for scenario, group in detail.groupby("scenario"):
        for metric in ("expected_incremental_utility", "realized_incremental_utility"):
            wide = group.pivot(index="seed", columns="method", values=metric).sort_index()
            if wide.isna().any().any():
                raise ValueError(f"unmatched method/seed rows in scenario {scenario}")
            for treatment, reference in comparisons:
                paired = wide[treatment].to_numpy() - wide[reference].to_numpy()
                sample_indices = rng.integers(0, len(paired), size=(draws, len(paired)))
                boot = paired[sample_indices].mean(axis=1)
                rows.append(
                    {
                        "scenario": scenario,
                        "metric": metric,
                        "treatment": treatment,
                        "reference": reference,
                        "streams": len(paired),
                        "mean_paired_difference": float(paired.mean()),
                        "bootstrap_ci_level": 0.95,
                        "bootstrap_ci_low": float(np.quantile(boot, 0.025)),
                        "bootstrap_ci_high": float(np.quantile(boot, 0.975)),
                        "bootstrap_draws": draws,
                        "bootstrap_seed": 2026102701,
                        "multiplicity_adjusted": False,
                    }
                )
    return pd.DataFrame(rows)


def _controller_decision(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    selected_by_context: dict[int, int | None],
    certification_start: int,
    certification_events: int,
    query_uniforms: np.ndarray,
    query_rate: float,
    fn_cost: float,
    fp_cost: float,
    deployment_horizon: int,
    promotion_certified: bool,
) -> tuple[Intervention, float]:
    """Gate promotion with a controller fed only queried certification outcomes.

    The empirical IPW mean estimates gross per-event cost reduction on the
    certification block and scales it to the deployment horizon. This is a
    heuristic forecast; the independent promotion e-process remains mandatory.
    Label expenditure is reported separately because no conversion to cost
    units is justified by the current benchmark contract.
    """
    if certification_events < 1 or not 0 < query_rate <= 1 or deployment_horizon < 1:
        if certification_events == 0 and 0 < query_rate <= 1 and deployment_horizon >= 1:
            return Intervention.CONTINUE, 0.0
        raise ValueError("controller requires a valid certification horizon and propensity")
    indices = np.arange(certification_start, certification_start + certification_events)
    queried = query_uniforms[indices] < query_rate
    gains = np.zeros(certification_events, dtype=np.float64)
    contexts = np.asarray(family["contexts"][indices], dtype=int)
    incumbent = np.asarray(family["incumbent"][indices], dtype=int)
    labels = np.asarray(y[indices], dtype=int)
    for relative in np.flatnonzero(queried):
        candidate = selected_by_context.get(int(contexts[relative]))
        if candidate is None:
            continue
        candidate_action = int(family["actions"][candidate, indices[relative]])
        incumbent_action = int(incumbent[relative])
        label = int(labels[relative])
        incumbent_cost = fp_cost if incumbent_action == 1 and label == 0 else 0.0
        incumbent_cost += fn_cost if incumbent_action == 0 and label == 1 else 0.0
        candidate_cost = fp_cost if candidate_action == 1 and label == 0 else 0.0
        candidate_cost += fn_cost if candidate_action == 0 and label == 1 else 0.0
        gains[relative] = (incumbent_cost - candidate_cost) / query_rate
    estimated_gross_gain = float(gains.mean() * deployment_horizon)
    estimates = {
        Intervention.CONTINUE: ActionEstimate(expected_loss_reduction=0.0),
        Intervention.PROMOTE: ActionEstimate(
            expected_loss_reduction=estimated_gross_gain,
            switching_cost=SWITCH_COST,
        ),
    }
    action = InterventionController().choose(
        estimates,
        promotion_certified=promotion_certified,
    )
    return action, estimated_gross_gain


def _fixed_candidate_certification(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    scenario: Any,
    query_uniforms: np.ndarray,
    budget: int,
    alpha: float = PROMOTION_ALPHA,
) -> dict[str, Any]:
    """Certify candidate 0, frozen by initial validation, on the fresh Q2 block.

    This is the no-scout ablation. Candidate identity is fixed before Q1/Q2; only
    queried labels in [monitor_end, scout_cert_end) enter the e-process.
    """
    start = STAGES["monitor_end"]
    end = STAGES["scout_cert_end"]
    horizon = end - start
    if budget < 1 or budget > SCOUT_CERT_LABEL_CAP:
        raise ValueError("fixed-candidate certification budget is outside protocol cap")
    rate = budget / horizon
    if not 0 < rate <= 1:
        raise ValueError("invalid fixed-candidate certification query rate")
    selected = 0
    switch_rate = SWITCH_COST / family["deployment_length"]
    outcome_bound = float(max(scenario.fn_cost, scenario.fp_cost))
    process = BoundedMeanEProcess(
        bound=outcome_bound / rate + switch_rate,
        alpha=alpha,
    )
    labels = 0
    processed = 0
    log_path: list[float] = []
    for event in range(start, end):
        queried = bool(query_uniforms[event] < rate)
        if queried and labels >= budget:
            break
        if queried:
            labels += 1
            observed_gain = (
                family["z1"][selected, event] if y[event] else family["z0"][selected, event]
            )
            increment = float(observed_gain) / rate - switch_rate
        else:
            increment = -switch_rate
        log_path.append(process.update(increment))
        processed += 1
    crossing = next(
        (start + i for i, value in enumerate(log_path) if value >= -np.log(alpha)), None
    )
    selected_ids = {
        "0": str(family["candidate_ids"][selected]),
        "1": str(family["candidate_ids"][selected]),
    }
    contexts = np.asarray(family["contexts"][start : start + processed], dtype=int)
    gains = np.asarray(family["h_truth"][selected, start : start + processed], dtype=float)
    monitor_mean = float(np.mean(gains - switch_rate)) if processed else None
    return {
        "labels_queried": labels,
        "promoted": crossing is not None,
        "selected_candidates_by_context": json.dumps(selected_ids, sort_keys=True),
        "monitor_events_processed": processed,
        "scout_events_processed": 0,
        "certification_start_index": start,
        "certification_log_e_path": log_path,
        "candidate_is_monitor_null": bool(monitor_mean is not None and monitor_mean <= 1e-12),
        "selected_candidate_monitor_expected_net_gain": monitor_mean,
        "scout_selection_gain_by_context": "{}",
        "evaluation_start_index": crossing if crossing is not None else end,
        "promotion_event": crossing,
        "candidate_index": selected,
        "candidate_context_events": int(np.sum(contexts == 0) + np.sum(contexts == 1)),
    }


def _build_event_logs(
    *,
    scenario: Any,
    scenario_label: str,
    seed: int,
    method: str,
    y: np.ndarray,
    probability_true: np.ndarray,
    incumbent: np.ndarray,
    reference: np.ndarray,
    actual_actions: np.ndarray,
    family: dict[str, Any],
    selected_by_context: dict[int, int | None],
    selected_ids: dict[str, str | None],
    promoted: bool,
    fallback_used: bool,
    trigger_index: int | None,
    rollback_index: int | None,
    rollback_enabled: bool,
    rollback_processed: int,
    q1_processed: int,
    q1_log_e_by_event: dict[int, float],
    scout_result: dict[str, Any] | None,
    scout_rate: float | None,
    query_uniforms: np.ndarray,
    controller_action: str,
    promotion_event: int | None,
    rollback_log_e_by_event: dict[int, float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Serialize learner-visible events separately from evaluator outcomes."""
    n = len(y)
    queried = np.zeros(n, dtype=bool)
    query_probability = np.zeros(n, dtype=np.float64)
    query_stage = np.full(n, "none", dtype=object)
    certification_e_by_event: dict[int, float] = {}
    if q1_processed:
        start = STAGES["fit_end"]
        stop = start + q1_processed
        events = np.arange(start, stop)
        queried[events] = query_uniforms[events] < MONITOR_QUERY_RATE
        query_probability[events] = MONITOR_QUERY_RATE
        query_stage[events] = "incumbent_monitor"
    if scout_result is not None and scout_rate is not None:
        scout_start = STAGES["monitor_end"]
        scout_stop = scout_start + int(scout_result["scout_events_processed"])
        if scout_stop > scout_start:
            events = np.arange(scout_start, scout_stop)
            queried[events] = query_uniforms[events] < scout_rate
            query_probability[events] = scout_rate
            query_stage[events] = "candidate_scout"
        certification_start = int(scout_result["certification_start_index"])
        certification_count = int(scout_result["monitor_events_processed"])
        certification_stop = certification_start + certification_count
        if certification_stop > certification_start:
            events = np.arange(certification_start, certification_stop)
            queried[events] = query_uniforms[events] < scout_rate
            query_probability[events] = scout_rate
            query_stage[events] = "candidate_certification"
        certification_e_by_event = {
            certification_start + offset: float(value)
            for offset, value in enumerate(scout_result["certification_log_e_path"])
        }
    if rollback_enabled and rollback_processed:
        start = STAGES["scout_cert_end"]
        stop = start + rollback_processed
        events = np.arange(start, stop)
        queried[events] = query_uniforms[events] < QUERY_RATE
        query_probability[events] = QUERY_RATE
        query_stage[events] = "rollback_monitor"

    if int(queried.sum()) != (
        int(queried[STAGES["fit_end"] : STAGES["monitor_end"]].sum())
        + (int(scout_result["labels_queried"]) if scout_result is not None else 0)
        + int(queried[STAGES["scout_cert_end"] :].sum())
    ):
        raise RuntimeError("event-query accounting failed across disjoint stages")

    policy_versions = np.full(n, "incumbent", dtype=object)
    if fallback_used and trigger_index is not None:
        policy_versions[trigger_index + 1 :] = "source_reference"
    if promoted:
        deployment_start = STAGES["scout_cert_end"]
        for event in range(deployment_start, n):
            if rollback_index is not None and event > rollback_index:
                break
            context = int(family["contexts"][event])
            selected = selected_by_context.get(context)
            if selected is not None:
                policy_versions[event] = f"candidate:{selected_ids.get(str(context))}"

    incumbent_cost = _cost(incumbent, y, fn=scenario.fn_cost, fp=scenario.fp_cost)
    deployed_cost = _cost(actual_actions, y, fn=scenario.fn_cost, fp=scenario.fp_cost)
    reference_cost = _cost(reference, y, fn=scenario.fn_cost, fp=scenario.fp_cost)
    expected_incumbent_cost = np.where(
        incumbent == 1,
        scenario.fp_cost * (1 - probability_true),
        scenario.fn_cost * probability_true,
    )
    expected_deployed_cost = np.where(
        actual_actions == 1,
        scenario.fp_cost * (1 - probability_true),
        scenario.fn_cost * probability_true,
    )

    learner_rows: list[dict[str, Any]] = []
    evaluator_rows: list[dict[str, Any]] = []
    for event in range(n):
        if event < STAGES["fit_end"]:
            stage = "fit_validation"
        elif event < STAGES["monitor_end"]:
            stage = "incumbent_monitor"
        elif event < STAGES["scout_cert_end"]:
            stage = (
                (
                    "candidate_scout"
                    if event < int(scout_result["certification_start_index"])
                    else "candidate_certification"
                )
                if scout_result is not None
                else "reserved_scout_certification"
            )
        else:
            stage = "deployment_rollback"
        fixed_selection = method in {
            "fixed_candidate_certification",
            "full_pipeline_fixed_certification",
        }
        selection_available_at = (
            STAGES["fit_end"]
            if fixed_selection
            else (int(scout_result["certification_start_index"]) if scout_result is not None else n)
        )
        intervention_cost = 0.0
        if promoted and event == STAGES["scout_cert_end"]:
            intervention_cost += SWITCH_COST
        if fallback_used and trigger_index is not None and event == trigger_index + 1:
            intervention_cost += SWITCH_COST
        if rollback_index is not None and event == rollback_index:
            intervention_cost += ROLLBACK_COST
        learner_rows.append(
            {
                "scenario": scenario_label,
                "seed": seed,
                "method": method,
                "event_index": event,
                "feature_available_index": event,
                "prediction_decision_index": event,
                "stage": stage,
                "policy_version": policy_versions[event],
                "action": int(actual_actions[event]),
                "query_requested": bool(queried[event]),
                "query_probability": float(query_probability[event]),
                "query_stage": str(query_stage[event]),
                "candidate_selection_available": bool(
                    event >= selection_available_at
                    and (scout_result is not None or fixed_selection)
                ),
                "selected_candidate_id": (
                    selected_ids.get(str(int(family["contexts"][event])))
                    if event >= selection_available_at
                    and (scout_result is not None or fixed_selection)
                    else None
                ),
                "label_available_index": event if queried[event] else None,
                "observed_label": int(y[event]) if queried[event] else None,
                "q1_log_e_value": q1_log_e_by_event.get(event),
                "certification_log_e_value": certification_e_by_event.get(event),
                "rollback_log_e_value": rollback_log_e_by_event.get(event),
                "q1_triggered_here": event == trigger_index,
                "promotion_certified_here": event == promotion_event,
                "rollback_triggered_here": event == rollback_index,
                "controller_action": controller_action if event == promotion_event else None,
                "label_resource_units": int(queried[event]),
                "intervention_cost_units": intervention_cost,
            }
        )
        evaluator_rows.append(
            {
                "scenario": scenario_label,
                "seed": seed,
                "method": method,
                "event_index": event,
                "true_label": int(y[event]),
                "true_positive_probability": float(probability_true[event]),
                "incumbent_action": int(incumbent[event]),
                "reference_action": int(reference[event]),
                "deployed_action": int(actual_actions[event]),
                "incumbent_cost": float(incumbent_cost[event]),
                "reference_cost": float(reference_cost[event]),
                "deployed_cost": float(deployed_cost[event]),
                "realized_incumbent_minus_deployed_gain": float(
                    incumbent_cost[event] - deployed_cost[event]
                ),
                "expected_incumbent_minus_deployed_gain": float(
                    expected_incumbent_cost[event] - expected_deployed_cost[event]
                ),
                "intervention_cost_units": intervention_cost,
                "evaluator_only": True,
            }
        )
    return learner_rows, evaluator_rows


def run_seed(
    *,
    scenario: Any,
    seed: int,
    device: str,
    method: str = "full_pipeline",
    profile: str | None = None,
) -> dict[str, Any]:
    """Run one synthetic stream with non-overlapping monitor/scout/cert/deploy blocks."""
    if method not in PIPELINE_METHODS:
        raise ValueError(f"method must be one of {PIPELINE_METHODS}")
    n = STAGES["stream_end"]
    source_config = ExperimentConfig(
        n=n,
        d=16,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=800,
        window=64,
        stride=32,
        alpha=MONITOR_ALPHA,
        eprocess_epsilon=HARM_MARGIN,
        seed_offset=seed,
        change_fraction=0.20,
        device=device,
    )
    _, frame, oracle, _timing = _generate(scenario, seed, source_config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = (frame.target.to_numpy(dtype=float) > 0).astype(int)
    probability_true = oracle.probability_positive.to_numpy(dtype=float).copy()

    promotion_config = BudgetedPromotionConfig(
        n=n,
        d=x.shape[1],
        seeds=1,
        seed_offset=seed,
        alpha=PROMOTION_ALPHA,
        switching_cost=SWITCH_COST,
        budget_rates=(QUERY_RATE,),
        query_policies=("uniform",),
        shared_query_randomness=True,
        alpha_allocations=("rank",),
        estimators=("direct_ipw",),
        monitoring_rules=("fixed_mixture",),
        context_feature_index=0,
        context_threshold=0.0,
        scout_bound_mode="eventwise_propensity",
        include_scout_context_policy=True,
        create_plot=False,
        device=device,
    )
    family = _fit_candidate_family(
        x=x,
        y=y,
        probability_true=probability_true,
        scenario=scenario,
        config=promotion_config,
    )
    if int(family["validation_end"]) != STAGES["fit_end"]:
        raise RuntimeError("candidate family training/validation split differs from protocol")
    scenario_label = profile or scenario.name
    if scenario.harmful_adaptation:
        # Retain both the source-timed late adaptation and the separately named
        # event-800 alignment used to test Q1 monitor response.
        adaptation_start = (
            STAGES["monitor_end"] if profile == "harmful_adaptation_native" else STAGES["fit_end"]
        )
        scenario_label = (
            "harmful_adaptation_native"
            if profile == "harmful_adaptation_native"
            else "harmful_adaptation_at_monitor"
        )
        incumbent = np.asarray(family["incumbent"], dtype=int).copy()
        incumbent[adaptation_start:] = 1
        family["incumbent"] = incumbent
        z0, z1 = _candidate_outcome_contrasts(
            incumbent,
            np.asarray(family["actions"], dtype=int),
            fn=scenario.fn_cost,
            fp=scenario.fp_cost,
        )
        family["z0"], family["z1"] = z0, z1
        p_hat = np.asarray(family["probability_hat"], dtype=float)
        family["h_proxy"] = (1 - p_hat[None, :]) * z0 + p_hat[None, :] * z1
        family["h_truth"] = (1 - probability_true[None, :]) * z0 + probability_true[None, :] * z1

    if profile == "calibration_candidate_null":
        if not scenario.harmful_adaptation:
            raise ValueError("calibration_candidate_null requires the staged harm scenario")
        _install_pointwise_null_candidate_family(
            x=x,
            family=family,
            probability_hat=np.asarray(family["probability_hat"], dtype=float),
            probability_true=probability_true,
            fn=scenario.fn_cost,
            fp=scenario.fp_cost,
        )
        scenario_label = profile

    if profile == "post_promotion_reversal":
        if scenario.name not in {"boundary_local_harm", "harmful_adaptation"}:
            raise ValueError("post_promotion_reversal requires a harm scenario")
        scenario_label = profile
        reversal_start = STAGES["scout_cert_end"]
        # A predeclared abrupt regime change makes the pre-change incumbent
        # action perfect after the Q2 certification block. Candidate actions
        # remain frozen, so any candidate that differs incurs observable harm.
        probability_true[reversal_start:] = family["incumbent"][reversal_start:]
        y[reversal_start:] = family["incumbent"][reversal_start:]
        family["h_truth"] = (1 - probability_true[None, :]) * family["z0"] + probability_true[
            None, :
        ] * family["z1"]

    # Candidate policies and proxy were frozen using only events before the monitor.
    # Rebind only the downstream stage boundaries; the target-scouter receives no Q1 data.
    family["validation_end"] = STAGES["monitor_end"]
    family["monitor_end"] = STAGES["scout_cert_end"]
    family["monitor_length"] = STAGES["scout_cert_end"] - STAGES["monitor_end"]
    family["deployment_length"] = STAGES["stream_end"] - STAGES["scout_cert_end"]
    family["q_min"][QUERY_RATE] = QUERY_RATE / 2
    family["q_paths"][("uniform", QUERY_RATE)] = np.full(
        family["monitor_length"], QUERY_RATE, dtype=float
    )

    query_rng = np.random.default_rng(seed + 700_001)
    query_uniforms = query_rng.random(n)

    # The Q1 contrast is incumbent cost minus the frozen source reference cost.
    incumbent = np.asarray(family["incumbent"], dtype=int)
    reference = np.asarray(_source_action(x, scenario), dtype=int)
    observed_harm = _cost(incumbent, y, fn=scenario.fn_cost, fp=scenario.fp_cost) - _cost(
        reference, y, fn=scenario.fn_cost, fp=scenario.fp_cost
    )
    cost_bound = float(max(scenario.fn_cost, scenario.fp_cost))
    monitor_process = BoundedMeanEProcess(
        bound=cost_bound / MONITOR_QUERY_RATE + HARM_MARGIN,
        alpha=MONITOR_ALPHA,
    )
    q1_start = STAGES["fit_end"]
    trigger_index: int | None = None
    q1_labels = 0
    q1_processed = 0
    q1_log_e_by_event: dict[int, float] = {}
    if method in {
        "full_pipeline",
        "full_pipeline_controller",
        "full_pipeline_fixed_certification",
        "q1_fallback",
    }:
        for event in range(q1_start, STAGES["monitor_end"]):
            if q1_labels >= MONITOR_LABEL_CAP:
                break
            queried = query_uniforms[event] < MONITOR_QUERY_RATE
            q1_processed += 1
            if queried:
                q1_labels += 1
                estimate = observed_harm[event] / MONITOR_QUERY_RATE
            else:
                estimate = 0.0
            log_e = monitor_process.update(estimate - HARM_MARGIN)
            q1_log_e_by_event[event] = log_e
            if log_e >= -np.log(MONITOR_ALPHA):
                trigger_index = event
                break

    scout_result: dict[str, Any] | None = None
    scout_budget = 0
    scout_rate: float | None = None
    should_scout = method in {"two_gate", "two_gate_controller"} or (
        method in {"full_pipeline", "full_pipeline_controller"} and trigger_index is not None
    )
    should_fixed_certify = method == "fixed_candidate_certification" or (
        method == "full_pipeline_fixed_certification" and trigger_index is not None
    )
    if should_scout or should_fixed_certify:
        scout_budget = min(
            SCOUT_CERT_LABEL_CAP,
            max(0, TOTAL_LABEL_CAP - q1_labels - ROLLBACK_LABEL_CAP),
        )
        if scout_budget < 1:
            raise RuntimeError("no label budget remains for the fresh scout/certification stage")
        scout_rate = scout_budget / family["monitor_length"]
        family["q_min"][scout_rate] = scout_rate / 2
        family["q_paths"][("uniform", scout_rate)] = np.full(
            family["monitor_length"], scout_rate, dtype=float
        )
        if should_fixed_certify:
            scout_result = _fixed_candidate_certification(
                family=family,
                y=y,
                scenario=scenario,
                query_uniforms=query_uniforms,
                budget=scout_budget,
            )
        else:
            scout_config = replace(promotion_config, budget_rates=(scout_rate,))
            # `_monitor_scout_context_policy` processes scout then fresh certification data.
            scout_result = _monitor_scout_context_policy(
                family=family,
                y=y,
                scenario=scenario,
                config=scout_config,
                query_name="uniform",
                budget_rate=scout_rate,
                query_uniforms=query_uniforms[STAGES["monitor_end"] : STAGES["scout_cert_end"]],
            )

    certified = bool(scout_result and scout_result["promoted"])
    selected_ids: dict[str, str | None] = {}
    if scout_result is not None:
        selected_ids = json.loads(str(scout_result["selected_candidates_by_context"]))
    id_to_index = {str(value): index for index, value in enumerate(family["candidate_ids"])}
    fixed_selection = method in {
        "fixed_candidate_certification",
        "full_pipeline_fixed_certification",
    }
    if fixed_selection:
        fixed_id = str(family["candidate_ids"][0])
        selected_ids = {"0": fixed_id, "1": fixed_id}
    if method == "scheduled_promote":
        top_candidate = str(family["candidate_ids"][0])
        selected_ids = {"0": top_candidate, "1": top_candidate}
    selected_by_context = {
        int(group): (None if name is None else id_to_index[str(name)])
        for group, name in selected_ids.items()
    }
    if method == "scheduled_promote":
        selected_by_context = {0: 0, 1: 0}
    controller_action = "not_run"
    controller_estimated_gross_gain: float | None = None
    if method in {"two_gate_controller", "full_pipeline_controller"}:
        if scout_result is None:
            controller_action = Intervention.CONTINUE.value
        else:
            if scout_rate is None:
                raise RuntimeError("scout returned without a registered query propensity")
            controller_action_enum, controller_estimated_gross_gain = _controller_decision(
                family=family,
                y=y,
                selected_by_context=selected_by_context,
                certification_start=int(scout_result["certification_start_index"]),
                certification_events=int(scout_result["monitor_events_processed"]),
                query_uniforms=query_uniforms,
                query_rate=scout_rate,
                fn_cost=scenario.fn_cost,
                fp_cost=scenario.fp_cost,
                deployment_horizon=STAGES["stream_end"] - STAGES["scout_cert_end"],
                promotion_certified=certified,
            )
            controller_action = controller_action_enum.value
    promoted = method == "scheduled_promote" or (
        certified
        and (
            method not in {"two_gate_controller", "full_pipeline_controller"}
            or controller_action == Intervention.PROMOTE.value
        )
    )
    rollback_enabled = promoted and method in {
        "two_gate",
        "two_gate_controller",
        "full_pipeline",
        "full_pipeline_controller",
        "full_pipeline_fixed_certification",
    }

    # Fresh forward deployment rollback process. On cap exhaustion the process stops;
    # the policy remains deployed and its remaining harm is still evaluator-scored.
    deployment_start = STAGES["scout_cert_end"]
    deployment_end = STAGES["stream_end"]
    deployment_context = np.asarray(family["contexts"][deployment_start:deployment_end], dtype=int)
    deployed_candidate = np.asarray(incumbent[deployment_start:deployment_end], dtype=int).copy()
    if promoted:
        for relative, group in enumerate(deployment_context):
            selected = selected_by_context.get(int(group))
            if selected is not None:
                deployed_candidate[relative] = family["actions"][
                    selected, deployment_start + relative
                ]

    rollback_process = BoundedMeanEProcess(
        bound=cost_bound / QUERY_RATE + ROLLBACK_COST / family["deployment_length"],
        alpha=ROLLBACK_ALPHA,
    )
    rollback_index: int | None = None
    rollback_labels = 0
    rollback_processed = 0
    rollback_cap_exhausted = False
    rollback_log_e_by_event: dict[int, float] = {}
    candidate_cost = _cost(
        deployed_candidate,
        y[deployment_start:deployment_end],
        fn=scenario.fn_cost,
        fp=scenario.fp_cost,
    )
    incumbent_cost = _cost(
        incumbent[deployment_start:deployment_end],
        y[deployment_start:deployment_end],
        fn=scenario.fn_cost,
        fp=scenario.fp_cost,
    )
    rollback_harm = candidate_cost - incumbent_cost
    if rollback_enabled:
        for relative, event in enumerate(range(deployment_start, deployment_end)):
            if rollback_labels >= ROLLBACK_LABEL_CAP:
                rollback_cap_exhausted = True
                break
            queried = query_uniforms[event] < QUERY_RATE
            rollback_processed += 1
            estimate = rollback_harm[relative] / QUERY_RATE if queried else 0.0
            rollback_labels += int(queried)
            threshold = ROLLBACK_COST / family["deployment_length"]
            log_e = rollback_process.update(estimate - threshold)
            rollback_log_e_by_event[event] = log_e
            if log_e >= -np.log(ROLLBACK_ALPHA):
                rollback_index = event
                break
    rollback_query_harm_events = int(
        np.sum((rollback_harm > 0) & (query_uniforms[deployment_start:deployment_end] < QUERY_RATE))
    )
    rollback_harm_events = int(np.sum(rollback_harm > 0))

    # Score actions against the incumbent policy; oracle probabilities remain evaluator-only.
    actual_actions = np.asarray(incumbent, dtype=int).copy()
    if promoted:
        candidate_active_mask = _candidate_active_mask(
            deployment_start, deployment_end, rollback_index
        )
        for relative, event in enumerate(range(deployment_start, deployment_end)):
            if candidate_active_mask[relative]:
                actual_actions[event] = deployed_candidate[relative]
    fallback_used = method == "q1_fallback" and trigger_index is not None
    if fallback_used and trigger_index is not None:
        actual_actions[trigger_index + 1 :] = reference[trigger_index + 1 :]
    observed_gain = _cost(incumbent, y, fn=scenario.fn_cost, fp=scenario.fp_cost) - _cost(
        actual_actions, y, fn=scenario.fn_cost, fp=scenario.fp_cost
    )
    expected_gain = np.zeros(n, dtype=float)
    if promoted:
        candidate_active_mask = _candidate_active_mask(
            deployment_start, deployment_end, rollback_index
        )
        for relative, event in enumerate(range(deployment_start, deployment_end)):
            if not candidate_active_mask[relative]:
                break
            group = int(family["contexts"][event])
            selected = selected_by_context.get(group)
            if selected is not None:
                expected_gain[event] = family["h_truth"][selected, event]
    elif fallback_used and trigger_index is not None:
        p = probability_true
        incumbent_expected = np.where(
            incumbent == 1, scenario.fp_cost * (1 - p), scenario.fn_cost * p
        )
        reference_expected = np.where(
            reference == 1, scenario.fp_cost * (1 - p), scenario.fn_cost * p
        )
        expected_gain[trigger_index + 1 :] = (
            incumbent_expected[trigger_index + 1 :] - reference_expected[trigger_index + 1 :]
        )
    intervention_cost = (SWITCH_COST if promoted or fallback_used else 0.0) + (
        ROLLBACK_COST if rollback_index is not None else 0.0
    )
    total_labels = (
        q1_labels + (int(scout_result["labels_queried"]) if scout_result else 0) + rollback_labels
    )
    if total_labels > TOTAL_LABEL_CAP:
        raise RuntimeError("integrated hard label cap exceeded")

    promotion_decision_index = (
        int(scout_result["evaluation_start_index"])
        if promoted and scout_result is not None
        else STAGES["scout_cert_end"]
        if method == "scheduled_promote"
        else None
    )
    learner_event_log, evaluator_event_log = _build_event_logs(
        scenario=scenario,
        scenario_label=scenario_label,
        seed=seed,
        method=method,
        y=y,
        probability_true=probability_true,
        incumbent=incumbent,
        reference=reference,
        actual_actions=actual_actions,
        family=family,
        selected_by_context=selected_by_context,
        selected_ids=selected_ids,
        promoted=promoted,
        fallback_used=fallback_used,
        trigger_index=trigger_index,
        rollback_index=rollback_index,
        rollback_enabled=rollback_enabled,
        rollback_processed=rollback_processed,
        q1_processed=q1_processed,
        q1_log_e_by_event=q1_log_e_by_event,
        scout_result=scout_result,
        scout_rate=scout_rate,
        query_uniforms=query_uniforms,
        controller_action=controller_action,
        promotion_event=promotion_decision_index,
        rollback_log_e_by_event=rollback_log_e_by_event,
    )

    return {
        "scenario": scenario_label,
        "method": method,
        "seed": seed,
        "device": device,
        "monitor_triggered": trigger_index is not None,
        "monitor_trigger_event": trigger_index,
        "monitor_events_processed": q1_processed,
        "monitor_labels": q1_labels,
        "monitor_log_e_final": monitor_process.log_e_value,
        "scout_cert_ran": scout_result is not None,
        "candidate_promoted": promoted,
        "promotion_certified": certified,
        "controller_action": controller_action,
        "controller_estimated_gross_gain": controller_estimated_gross_gain,
        "fallback_used": fallback_used,
        "candidate_by_context": json.dumps(selected_ids, sort_keys=True),
        "candidate_selection_source": (
            "initial_validation_fixed"
            if method in {"fixed_candidate_certification", "full_pipeline_fixed_certification"}
            else "target_scout"
            if scout_result is not None
            else "scheduled"
            if method == "scheduled_promote"
            else "none"
        ),
        "scout_cert_labels": int(scout_result["labels_queried"]) if scout_result else 0,
        "scout_cert_label_cap": scout_budget if scout_result else 0,
        "scout_cert_query_rate": (scout_budget / family["monitor_length"] if scout_result else 0.0),
        "scout_certified": bool(scout_result and scout_result["promoted"]),
        "scout_selected_candidate": bool(any(value is not None for value in selected_ids.values())),
        "scout_expected_net_gain_on_certification": (
            float(scout_result["selected_candidate_monitor_expected_net_gain"])
            if scout_result
            and scout_result["selected_candidate_monitor_expected_net_gain"] is not None
            else None
        ),
        "scout_certificate_null_by_oracle": bool(
            scout_result and scout_result["candidate_is_monitor_null"]
        ),
        "scout_selection_gain_by_context": (
            scout_result["scout_selection_gain_by_context"] if scout_result else "{}"
        ),
        "scout_events_processed": int(scout_result["scout_events_processed"])
        if scout_result
        else 0,
        "rollback_event": rollback_index if rollback_enabled else None,
        "rollback_labels": rollback_labels,
        "rollback_events_processed": rollback_processed,
        "rollback_cap_exhausted": rollback_cap_exhausted,
        "rollback_log_e_final": rollback_process.log_e_value,
        "rollback_e_threshold": -float(np.log(ROLLBACK_ALPHA)),
        "rollback_harm_events_evaluator": rollback_harm_events,
        "rollback_queried_harm_events_evaluator": rollback_query_harm_events,
        "learner_event_log": learner_event_log,
        "evaluator_event_log": evaluator_event_log,
        "total_labels": total_labels,
        "hard_label_cap": TOTAL_LABEL_CAP,
        "expected_deployment_gain": float(expected_gain.sum() - intervention_cost),
        "expected_incremental_utility": float(expected_gain.sum() - intervention_cost),
        "realized_deployment_gain": float(
            observed_gain[deployment_start:deployment_end].sum() - intervention_cost
        ),
        "realized_incremental_utility": float(observed_gain.sum() - intervention_cost),
        "intervention_cost": intervention_cost,
        "mean_incumbent_reference_harm_monitor": float(
            observed_harm[q1_start : STAGES["monitor_end"]].mean()
        ),
        "monitor_margin": HARM_MARGIN,
        "alpha_monitor": MONITOR_ALPHA,
        "alpha_promotion": PROMOTION_ALPHA,
        "alpha_rollback": ROLLBACK_ALPHA,
    }


def run(
    *,
    seeds: int,
    seed_offset: int,
    device: str,
    output: Path,
    protocol: Path = PROTOCOL,
    status: str = "exploratory_development_not_confirmation",
) -> Path:
    if seeds < 1 or seed_offset < SEED_OFFSET:
        raise ValueError("seed block must be nonempty and use the registered fresh range")
    if status not in {
        "exploratory_development_not_confirmation",
        "independent_efficacy_confirmation",
    }:
        raise ValueError("unsupported integrated run status")
    resolved = resolve_device(device, n=STAGES["stream_end"], d=16, chunk_size=2048)
    output = output.resolve()
    protocol = protocol.resolve()
    if not protocol.is_file():
        raise FileNotFoundError(protocol)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    protocol_snapshot = output / "protocol_snapshot.md"
    protocol_snapshot.write_bytes(protocol.read_bytes())
    protocol_snapshot_sha256 = _sha256(protocol_snapshot)
    source_files = [
        Path(__file__),
        ROOT / "src/shiftlab/dive/budgeted_promotion.py",
        ROOT / "src/shiftlab/dive/eprocess.py",
        ROOT / "src/shiftlab/dive/controller.py",
        ROOT / "src/shiftlab/decision_harm_experiment.py",
        protocol,
    ]
    execution_source_dir = output / "execution_sources"
    source_snapshots: dict[str, Path] = {}
    for source_path in source_files:
        relative_source = source_path.relative_to(ROOT)
        snapshot_path = execution_source_dir / relative_source
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_bytes(source_path.read_bytes())
        source_snapshots[str(relative_source)] = snapshot_path
    source_hashes = {key: _sha256(path) for key, path in source_snapshots.items()}

    rows: list[dict[str, Any]] = []
    learner_log_path = output / "learner_event_log.parquet"
    evaluator_log_path = output / "evaluator_event_log.parquet"
    learner_writer = pq.ParquetWriter(learner_log_path, LEARNER_EVENT_SCHEMA, compression="zstd")
    evaluator_writer = pq.ParquetWriter(
        evaluator_log_path, EVALUATOR_EVENT_SCHEMA, compression="zstd"
    )
    learner_event_count = 0
    evaluator_event_count = 0
    scenario_names = (
        "stationary",
        "benign_nuisance",
        "boundary_local_harm",
        "post_promotion_reversal",
        "recurring_regimes",
        "residual_variance",
        "harmful_adaptation_at_monitor",
        "harmful_adaptation_native",
    )
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    for scenario_name in scenario_names:
        source_scenario = (
            "harmful_adaptation"
            if scenario_name
            in {
                "harmful_adaptation_at_monitor",
                "harmful_adaptation_native",
                "post_promotion_reversal",
            }
            else scenario_name
        )
        scenario = scenarios[source_scenario]
        for seed in range(seed_offset, seed_offset + seeds):
            for method in PIPELINE_METHODS:
                result = run_seed(
                    scenario=scenario,
                    seed=seed,
                    device=resolved,
                    method=method,
                    profile=scenario_name,
                )
                learner_events = result.pop("learner_event_log")
                evaluator_events = result.pop("evaluator_event_log")
                learner_table = pa.Table.from_pylist(learner_events, schema=LEARNER_EVENT_SCHEMA)
                evaluator_table = pa.Table.from_pylist(
                    evaluator_events, schema=EVALUATOR_EVENT_SCHEMA
                )
                learner_writer.write_table(learner_table)
                evaluator_writer.write_table(evaluator_table)
                learner_event_count += learner_table.num_rows
                evaluator_event_count += evaluator_table.num_rows
                rows.append(result)
                print(
                    f"scenario={scenario_name} method={method} seed={seed} "
                    f"trigger={result['monitor_triggered']} "
                    f"promoted={result['candidate_promoted']} labels={result['total_labels']}",
                    flush=True,
                )
    learner_writer.close()
    evaluator_writer.close()
    detail = pd.DataFrame(rows)
    detail_path = output / "integrated_pipeline_seed_metrics.parquet"
    detail.to_parquet(detail_path, index=False)
    summary = detail.groupby(["scenario", "method"], as_index=False).agg(
        streams=("seed", "count"),
        monitor_trigger_rate=("monitor_triggered", "mean"),
        promotion_rate=("candidate_promoted", "mean"),
        rollback_rate=("rollback_event", lambda values: values.notna().mean()),
        mean_labels=("total_labels", "mean"),
        mean_expected_gain=("expected_incremental_utility", "mean"),
        mean_realized_gain=("realized_incremental_utility", "mean"),
    )
    summary_path = output / "integrated_pipeline_summary.csv"
    summary.to_csv(summary_path, index=False)
    contrasts = _paired_contrasts(detail)
    contrasts_path = output / "integrated_pipeline_paired_contrasts.csv"
    contrasts.to_csv(contrasts_path, index=False)
    manifest = {
        "experiment": "integrated_q1_target_scout_rollback_matched_comparison",
        "status": status,
        "created_utc": datetime.now(UTC).isoformat(),
        "seeds": {"offset": seed_offset, "count_per_scenario": seeds},
        "scenarios": list(scenario_names),
        "methods": list(PIPELINE_METHODS),
        "scenario_transform": {
            "harmful_adaptation_at_monitor": (
                "Stationary outcome law; the deployed policy changes to the all-positive "
                "action at event 800 after fitting, aligned with the Q1 monitor start."
            ),
            "harmful_adaptation_native": (
                "Stationary outcome law; the deployed policy changes to all-positive at event "
                "1,600, just after the Q1 monitoring block, preserving the source scenario timing."
            ),
            "post_promotion_reversal": (
                "Uses the same event-800 adaptation; from event 2,400, labels equal the frozen "
                "all-positive incumbent action, making that incumbent optimal while candidate "
                "actions remain frozen. This is a declared synthetic reversal stress profile."
            ),
        },
        "stages": STAGES,
        "monitor_query_rate": MONITOR_QUERY_RATE,
        "scout_query_rate_rule": "predictable scout label cap / 800 events; between 0.20 and 0.40",
        "scout_bound_mode": "eventwise_propensity; q is constant within each scout/certification block",
        "rollback_query_rate": QUERY_RATE,
        "label_caps": {
            "total": TOTAL_LABEL_CAP,
            "monitor": MONITOR_LABEL_CAP,
            "scout_cert": SCOUT_CERT_LABEL_CAP,
            "rollback": ROLLBACK_LABEL_CAP,
        },
        "alpha": {
            "monitor": MONITOR_ALPHA,
            "promotion": PROMOTION_ALPHA,
            "rollback": ROLLBACK_ALPHA,
            "sum": MONITOR_ALPHA + PROMOTION_ALPHA + ROLLBACK_ALPHA,
        },
        "device": resolved,
        "hardware": environment(),
        "source_sha256": source_hashes,
        "protocol_snapshot": str(protocol_snapshot.relative_to(ROOT)),
        "protocol_snapshot_sha256": protocol_snapshot_sha256,
        "metrics_sha256": _sha256(detail_path),
        "summary_sha256": _sha256(summary_path),
        "paired_contrasts_sha256": _sha256(contrasts_path),
        "learner_event_log": {
            "path": learner_log_path.name,
            "rows": learner_event_count,
            "sha256": _sha256(learner_log_path),
            "schema": str(LEARNER_EVENT_SCHEMA),
        },
        "evaluator_event_log": {
            "path": evaluator_log_path.name,
            "rows": evaluator_event_count,
            "sha256": _sha256(evaluator_log_path),
            "schema": str(EVALUATOR_EVENT_SCHEMA),
        },
        "limitations": [
            "The null calibration is limited to the separately registered synthetic controls and does not calibrate efficacy outcomes.",
            "The stagewise error allocation is supported only under the registered feedback and predictability assumptions.",
            "The synthetic workflow uses immediate labels and non-performative outcomes; no real-data transfer is established.",
            *(
                []
                if status == "independent_efficacy_confirmation"
                else ["This run is exploratory development and cannot support confirmatory claims."]
            ),
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return detail_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "outputs/shiftguard_unified/integrated_development/pipeline_controller_dev_v1",
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument(
        "--status",
        choices=(
            "exploratory_development_not_confirmation",
            "independent_efficacy_confirmation",
        ),
        default="exploratory_development_not_confirmation",
    )
    args = parser.parse_args()
    result = run(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        output=args.output,
        protocol=args.protocol,
        status=args.status,
    )
    print(f"wrote {result.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
