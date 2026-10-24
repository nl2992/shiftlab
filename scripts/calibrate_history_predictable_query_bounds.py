"""Calibrate history-predictable PPI support bounds on a paired decision-cost stream."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import norm

ALPHA = 0.05
M = 5.0
LOW_COST = 1.0
HIGH_COST = 5.0
P_LOW = 0.56
P_HIGH_NULL = 0.488
HARM_EFFECTS = (0.04, 0.20, 0.40, 0.60)
HARM_ONSET_FRACTION = 0.5
LABEL_BUDGET_RATE = 0.20
TRAINING_EVENTS = 512
Q_MAX = 0.80
ACTIVATION = 0.05
URGENCY_POWER = 0.5
BUDGET_TAPER_POWER = 1.0
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
Q_FLOORS = (0.05, 0.10, 0.15)
NULL_SCENARIO = "mixed_sign_exact_marginal_null"
HARM_SCENARIOS = tuple(f"high_cost_local_harm_d{effect:.2f}" for effect in HARM_EFFECTS)
SCENARIOS = (NULL_SCENARIO, *HARM_SCENARIOS)


def scenario_harm_effect(scenario: str) -> float | None:
    if scenario == NULL_SCENARIO:
        return None
    try:
        return dict(zip(HARM_SCENARIOS, HARM_EFFECTS, strict=True))[scenario]
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {scenario}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_configuration(streams: int, horizon: int, seed: int, device_name: str) -> None:
    if streams < 1 or horizon < 20:
        raise ValueError("streams must be positive and horizon must be at least 20")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")


def expected_population_contrast(*, high_probability: float) -> float:
    """Return E[cost * (1-2Y)] for the two equally likely strata."""
    low = LOW_COST * (1 - 2 * P_LOW)
    high = HIGH_COST * (1 - 2 * high_probability)
    return 0.5 * (low + high)


def high_probability_for_effect(effect: float) -> float:
    if effect not in HARM_EFFECTS:
        raise ValueError("effect must belong to the registered harm dose grid")
    return P_HIGH_NULL - effect / HIGH_COST


def evidence_directed_propensity(
    prior_log_e: torch.Tensor, remaining_fraction: torch.Tensor, *, q_min: float
) -> torch.Tensor:
    """History-only urgency rule; neither current context nor outcome is an input."""
    threshold = -math.log(ALPHA)
    urgency = (prior_log_e / threshold + ACTIVATION).clamp(0, 1).pow(URGENCY_POWER)
    return q_min + (Q_MAX - q_min) * urgency * remaining_fraction.pow(BUDGET_TAPER_POWER)


def generate_common_random_numbers(
    *, streams: int, horizon: int, seed: int, device: torch.device
) -> dict[str, torch.Tensor]:
    """Generate independent train, context, outcome, and query random numbers."""
    generator = torch.Generator(device=device).manual_seed(seed)
    training_context = torch.randint(
        0, 2, (streams, TRAINING_EVENTS), generator=generator, device=device
    )
    training_outcome_u = torch.rand((streams, TRAINING_EVENTS), generator=generator, device=device)
    monitor_context = torch.randint(0, 2, (horizon, streams), generator=generator, device=device)
    outcome_uniform = torch.rand((horizon, streams), generator=generator, device=device)
    query_uniform = torch.rand((horizon, streams), generator=generator, device=device)

    training_probability = torch.where(
        training_context == 0,
        torch.full_like(training_outcome_u, P_LOW),
        torch.full_like(training_outcome_u, P_HIGH_NULL),
    )
    training_y = training_outcome_u < training_probability
    training_cost = torch.where(
        training_context == 0,
        torch.full_like(training_outcome_u, LOW_COST),
        torch.full_like(training_outcome_u, HIGH_COST),
    )
    training_z = training_cost * (1 - 2 * training_y.to(torch.float32))
    low_mask = training_context == 0
    high_mask = ~low_mask
    low_count = low_mask.sum(dim=1)
    high_count = high_mask.sum(dim=1)
    if torch.any(low_count == 0) or torch.any(high_count == 0):
        raise RuntimeError("training sample omitted a context stratum")
    h_low = (training_z * low_mask).sum(dim=1) / low_count
    h_high = (training_z * high_mask).sum(dim=1) / high_count

    return {
        "context": monitor_context,
        "outcome_uniform": outcome_uniform,
        "query_uniform": query_uniform,
        "h_low": h_low.clamp(-M, M),
        "h_high": h_high.clamp(-M, M),
    }


def _log_e(log_wealth: torch.Tensor, log_weights: torch.Tensor) -> torch.Tensor:
    return torch.logsumexp(log_wealth + log_weights[None, :], dim=1)


def simulate_arm(
    *,
    scenario: str,
    streams: int,
    horizon: int,
    seed: int,
    data: dict[str, torch.Tensor],
    device: torch.device,
    query_policy: str,
    q_min: float,
    bound_mode: str,
) -> list[dict[str, object]]:
    harm_effect = scenario_harm_effect(scenario)
    if query_policy not in {"uniform", "evidence_directed"}:
        raise ValueError("unknown query policy")
    if bound_mode not in {"fixed", "predictable"}:
        raise ValueError("unknown bound mode")
    if query_policy == "uniform" and bound_mode == "predictable":
        raise ValueError("uniform predictable bound duplicates its fixed bound")
    if not 0 < q_min <= LABEL_BUDGET_RATE <= Q_MAX <= 1:
        raise ValueError("require q_min <= budget rate <= q_max")

    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    threshold = -math.log(ALPHA)
    stakes = torch.tensor(STAKES, dtype=torch.float64, device=device)
    log_weights = torch.full_like(stakes, -math.log(len(STAKES)))
    log_wealth = torch.zeros((streams, len(STAKES)), dtype=torch.float64, device=device)
    remaining = torch.full((streams,), budget, dtype=torch.int64, device=device)
    labels = torch.zeros_like(remaining)
    processed = torch.zeros_like(remaining)
    first_alarm = torch.full((streams,), -1, dtype=torch.int64, device=device)
    propensity_sum = torch.zeros(streams, dtype=torch.float64, device=device)
    bound_sum = torch.zeros(streams, dtype=torch.float64, device=device)
    propensity_violation = torch.zeros(streams, dtype=torch.bool, device=device)
    support_violation = torch.zeros(streams, dtype=torch.bool, device=device)
    factor_violation = torch.zeros(streams, dtype=torch.bool, device=device)

    fixed_q = float(LABEL_BUDGET_RATE)
    for event in range(horizon):
        prior_log_e = _log_e(log_wealth, log_weights)
        active = (remaining > 0) & (first_alarm < 0)

        if query_policy == "uniform":
            propensity = torch.full((streams,), fixed_q, dtype=torch.float64, device=device)
        else:
            remaining_fraction = remaining.to(torch.float64) / max(budget, 1)
            propensity = evidence_directed_propensity(prior_log_e, remaining_fraction, q_min=q_min)
        propensity_violation |= active & (
            (propensity < q_min - 1e-12) | (propensity > Q_MAX + 1e-12)
        )

        queried = active & (data["query_uniform"][event] < propensity)
        context = data["context"][event]
        high_cost_stratum = context == 1
        high_probability = P_HIGH_NULL
        if harm_effect is not None and event >= onset:
            high_probability = high_probability_for_effect(harm_effect)
        probability = torch.where(
            high_cost_stratum,
            torch.full((streams,), high_probability, dtype=torch.float32, device=device),
            torch.full((streams,), P_LOW, dtype=torch.float32, device=device),
        )
        outcome = data["outcome_uniform"][event] < probability
        cost = torch.where(
            high_cost_stratum,
            torch.full((streams,), HIGH_COST, dtype=torch.float32, device=device),
            torch.full((streams,), LOW_COST, dtype=torch.float32, device=device),
        )
        # Current action is 1 and reference action is 0; Z is their paired cost difference.
        z = cost * (1 - 2 * outcome.to(torch.float32))
        proxy = torch.where(high_cost_stratum, data["h_high"], data["h_low"]).to(torch.float64)
        estimate = torch.where(
            queried,
            proxy + (z.to(torch.float64) - proxy) / propensity,
            proxy,
        )
        if bound_mode == "fixed":
            bound = torch.full((streams,), M * (2 / q_min - 1), dtype=torch.float64, device=device)
        else:
            # q_t depends only on prior e-wealth and label spend, never current X or Y.
            bound = M * (2 / propensity - 1)
        factors = 1 + (estimate / bound)[:, None] * stakes[None, :]
        support_violation |= active & (torch.abs(estimate) > bound + 1e-8)
        factor_violation |= active & (factors <= 0).any(dim=1)
        updated_wealth = log_wealth + torch.log(factors)
        log_wealth = torch.where(active[:, None], updated_wealth, log_wealth)
        updated_log_e = _log_e(log_wealth, log_weights)
        crossed_now = active & (first_alarm < 0) & (updated_log_e >= threshold)
        first_alarm = torch.where(crossed_now, event, first_alarm)

        processed += active.to(torch.int64)
        labels += queried.to(torch.int64)
        remaining -= queried.to(torch.int64)
        propensity_sum += torch.where(active, propensity, 0).to(torch.float64)
        bound_sum += torch.where(active, bound, 0).to(torch.float64)

    if bool(propensity_violation.any()):
        raise RuntimeError("query propensity escaped its registered range")
    if bool(support_violation.any()):
        raise RuntimeError("PPI estimate exceeded its registered support bound")
    if bool(factor_violation.any()):
        raise RuntimeError("a betting factor was not positive")

    processed_cpu = processed.cpu().numpy()
    labels_cpu = labels.cpu().numpy()
    alarms_cpu = first_alarm.cpu().numpy()
    prop_sum_cpu = propensity_sum.cpu().numpy()
    bound_sum_cpu = bound_sum.cpu().numpy()
    onset_reached = (processed_cpu > onset) if harm_effect is not None else np.zeros(streams, bool)
    detected = (
        (alarms_cpu >= onset) & (alarms_cpu >= 0)
        if harm_effect is not None
        else np.zeros(streams, bool)
    )
    early_escalation = (
        (alarms_cpu >= 0) & (alarms_cpu < onset) if harm_effect is not None else alarms_cpu >= 0
    )
    delay = np.where(detected, alarms_cpu - onset, np.nan)
    exposure_events = np.zeros(streams, dtype=np.int64)
    if harm_effect is not None:
        end_event = np.where(alarms_cpu >= 0, alarms_cpu, processed_cpu - 1)
        exposure_events = np.maximum(0, end_event - onset + 1)

    arm_name = (
        "uniform_q020" if query_policy == "uniform" else f"evidence_qmin_{q_min:.2f}_{bound_mode}"
    )
    rows = []
    for stream in range(streams):
        n_processed = int(processed_cpu[stream])
        alarm = int(alarms_cpu[stream])
        rows.append(
            {
                "scenario": scenario,
                "stream_id": stream,
                "stream_seed_id": seed + stream,
                "query_policy": query_policy,
                "q_min": q_min,
                "bound_mode": bound_mode,
                "arm": arm_name,
                "events_processed": n_processed,
                "labels_queried": int(labels_cpu[stream]),
                "hard_label_budget": budget,
                "budget_respected": bool(labels_cpu[stream] <= budget),
                "mean_propensity_processed": (
                    float(prop_sum_cpu[stream] / n_processed) if n_processed else float("nan")
                ),
                "mean_bound_processed": (
                    float(bound_sum_cpu[stream] / n_processed) if n_processed else float("nan")
                ),
                "first_alarm_event": alarm if alarm >= 0 else None,
                "false_escalation": bool(early_escalation[stream]),
                "onset_reached": bool(onset_reached[stream]),
                "post_onset_detection": bool(detected[stream]),
                "detection_delay": float(delay[stream]) if detected[stream] else None,
                "evaluator_harm_exposure_events": int(exposure_events[stream]),
                "evaluator_expected_harm_per_post_onset_event": harm_effect or 0.0,
                "evaluator_cumulative_expected_harm_cost": (
                    (harm_effect or 0.0) * int(exposure_events[stream])
                ),
            }
        )
    return rows


def wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    z = float(norm.ppf(0.5 + confidence / 2))
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def summarize(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    for keys, group in metrics.groupby(
        ["scenario", "query_policy", "q_min", "bound_mode", "arm"], sort=True
    ):
        scenario, query_policy, q_min, bound_mode, arm = keys
        false_count = int(group["false_escalation"].sum())
        detected_count = int(group["post_onset_detection"].sum())
        false_low, false_high = wilson(false_count, len(group))
        detect_low, detect_high = wilson(detected_count, len(group))
        summary_rows.append(
            {
                "scenario": scenario,
                "query_policy": query_policy,
                "q_min": q_min,
                "bound_mode": bound_mode,
                "arm": arm,
                "streams": len(group),
                "false_escalations": false_count,
                "false_rate": false_count / len(group),
                "false_wilson_95_low": false_low,
                "false_wilson_95_high": false_high,
                "onsets_reached": int(group["onset_reached"].sum()),
                "post_onset_detections": detected_count,
                "detection_rate_all": detected_count / len(group),
                "detection_wilson_95_low": detect_low,
                "detection_wilson_95_high": detect_high,
                "mean_delay_detected": group["detection_delay"].mean(),
                "mean_labels": float(group["labels_queried"].mean()),
                "mean_events_processed": float(group["events_processed"].mean()),
                "mean_harm_exposure_events": float(group["evaluator_harm_exposure_events"].mean()),
                "mean_cumulative_expected_harm_cost": float(
                    group["evaluator_cumulative_expected_harm_cost"].mean()
                ),
            }
        )
    summary = pd.DataFrame(summary_rows)

    pair_rows = []
    rng = np.random.default_rng(42102026)
    for scenario in SCENARIOS:
        for q_min in Q_FLOORS:
            selected = metrics[
                (metrics["scenario"] == scenario)
                & (metrics["query_policy"] == "evidence_directed")
                & (metrics["q_min"] == q_min)
            ]
            pivot = selected.pivot(
                index="stream_id",
                columns="bound_mode",
                values=[
                    "false_escalation",
                    "post_onset_detection",
                    "labels_queried",
                    "events_processed",
                    "evaluator_harm_exposure_events",
                    "evaluator_cumulative_expected_harm_cost",
                ],
            )
            for measure in pivot.columns.levels[0]:
                if measure not in {
                    "false_escalation",
                    "post_onset_detection",
                    "labels_queried",
                    "evaluator_harm_exposure_events",
                    "evaluator_cumulative_expected_harm_cost",
                }:
                    continue
                difference = pivot[(measure, "predictable")].to_numpy(dtype=float) - pivot[
                    (measure, "fixed")
                ].to_numpy(dtype=float)
                if measure in {
                    "false_escalation",
                    "post_onset_detection",
                    "labels_queried",
                    "evaluator_cumulative_expected_harm_cost",
                }:
                    # Paired stream bootstrap; resample streams, not events.
                    sampled = rng.integers(0, len(difference), size=(4000, len(difference)))
                    draws = difference[sampled].mean(axis=1)
                    low, high = np.quantile(draws, [0.025, 0.975])
                else:
                    low = high = float("nan")
                pair_rows.append(
                    {
                        "scenario": scenario,
                        "q_min": q_min,
                        "paired_measure": measure,
                        "streams": len(difference),
                        "predictable_minus_fixed_mean": float(difference.mean()),
                        "paired_bootstrap_95_low": float(low),
                        "paired_bootstrap_95_high": float(high),
                        "positive_discordances": int((difference > 0).sum()),
                        "negative_discordances": int((difference < 0).sum()),
                    }
                )
    return summary, pd.DataFrame(pair_rows)


def configuration(streams: int, horizon: int, seed: int, device: torch.device) -> dict[str, object]:
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    return {
        "streams_per_scenario": streams,
        "rng_root_seed": seed,
        "stream_id_range_inclusive": [0, streams - 1],
        "stream_seed_id_range_inclusive": [seed, seed + streams - 1],
        "scenarios": list(SCENARIOS),
        "horizon": horizon,
        "harm_onset_event": onset,
        "alpha": ALPHA,
        "stakes": list(STAKES),
        "outcome_support_M": M,
        "low_cost": LOW_COST,
        "high_cost": HIGH_COST,
        "p_y1_low_stratum": P_LOW,
        "p_y1_high_null": P_HIGH_NULL,
        "post_onset_aggregate_harm_effects": list(HARM_EFFECTS),
        "p_y1_high_harm_by_effect": {
            f"{effect:.2f}": high_probability_for_effect(effect) for effect in HARM_EFFECTS
        },
        "population_mean_Z_null": 0.0,
        "population_variance_Z_null": 13.0,
        "label_budget_rate": LABEL_BUDGET_RATE,
        "hard_label_budget": math.floor(LABEL_BUDGET_RATE * horizon),
        "training_events_per_stream": TRAINING_EVENTS,
        "query_floors": list(Q_FLOORS),
        "q_max": Q_MAX,
        "urgency_activation_fraction": ACTIVATION,
        "urgency_power": URGENCY_POWER,
        "budget_taper_power": BUDGET_TAPER_POWER,
        "requested_device": str(device),
        "randomness": "one shared CUDA/CPU torch generator per run; independent tensor columns are stream IDs and are reused across arms and paired scenarios",
        "primary_metrics": [
            "null false-escalation probability",
            "harm post-onset detection by horizon",
            "stream-paired dynamic-minus-fixed differences",
            "labels and events consumed",
            "evaluator-known harm exposure until alarm or censoring",
        ],
    }


def render_report(
    summary: pd.DataFrame,
    paired: pd.DataFrame,
    config: dict[str, object],
    device_name: str,
    output: Path,
) -> str:
    null = summary[summary["scenario"] == NULL_SCENARIO]
    harm = summary[summary["scenario"] != NULL_SCENARIO]
    paired_power = paired[
        (paired["scenario"] != NULL_SCENARIO)
        & paired["paired_measure"].isin(
            {
                "post_onset_detection",
                "labels_queried",
                "evaluator_cumulative_expected_harm_cost",
            }
        )
    ]
    return (
        f"""# History-predictable PPI bound calibration and localized-harm benchmark

## Locked setup

This GPU/CPU synthetic benchmark used {config["streams_per_scenario"]:,} paired streams per condition, a {config["horizon"]}-event horizon, alpha {ALPHA}, and a hard cap of {config["hard_label_budget"]} labels. The null has exactly zero aggregate expected paired cost contrast and variance 13: the low- and high-cost strata have expected contrasts -0.12 and +0.12. At event {config["harm_onset_event"]}, only the high-cost outcome law changes. The registered post-onset aggregate expected-cost effects are {HARM_EFFECTS}; the high-stratum probability is derived from each effect before outcome generation.

The learner receives an empirical two-stratum proxy fit on {TRAINING_EVENTS} independent pre-monitor examples per stream. Query probabilities use prior process wealth and prior spend only. The fixed-bound process uses `B=M(2/q_min-1)`. Its paired comparator uses `B_t=M(2/q_t-1)` with the policy's current propensity, which is predictable because it is a function of prior wealth and spend. Both use the same stakes, alpha, hard label cap, and common random numbers. No oracle truth enters the learner or query policy.

The exact mixture-bound argument is standard: under the conditional-mean null, predictable q makes B_t history-predictable; the PPI estimate has the paired-cost contrast as its conditional mean and satisfies `|H_t|≤B_t`; therefore each nonnegative betting factor has conditional expectation at most one. This experiment checks code behavior and finite Monte Carlo calibration for the registered independent-stream DGP. It does not establish validity under dependence, delayed or informative labels, policy changes, or candidate selection, and it does not support a novelty claim.

## Null calibration

|Query arm|q floor|Bound|False escalations / streams|Rate|Wilson 95% interval|Mean labels|Mean events|
|---|---:|---|---:|---:|---:|---:|---:|
"""
        + "\n".join(
            f"| {row.arm} | {row.q_min:.2f} | {row.bound_mode} | {int(row.false_escalations)}/{int(row.streams)} | {row.false_rate:.3%} | [{row.false_wilson_95_low:.3%}, {row.false_wilson_95_high:.3%}] | {row.mean_labels:.1f} | {row.mean_events_processed:.1f} |"
            for row in null.itertuples(index=False)
        )
        + """

## Localized-harm detection

|Scenario|Query arm|q floor|Bound|Detections / streams|Rate|Wilson 95% interval|Pre-onset escalations|Onsets reached|Mean delay if detected|Mean labels|Mean harm exposure events|Mean cumulative expected harm cost|
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
"""
        + "\n".join(
            f"| {row.scenario} | {row.arm} | {row.q_min:.2f} | {row.bound_mode} | {int(row.post_onset_detections)}/{int(row.streams)} | {row.detection_rate_all:.3%} | [{row.detection_wilson_95_low:.3%}, {row.detection_wilson_95_high:.3%}] | {int(row.false_escalations)} | {int(row.onsets_reached)}/{int(row.streams)} | {row.mean_delay_detected:.1f} | {row.mean_labels:.1f} | {row.mean_harm_exposure_events:.1f} | {row.mean_cumulative_expected_harm_cost:.3f} |"
            for row in harm.itertuples(index=False)
        )
        + """

## Paired predictable-bound minus fixed-bound differences

|Scenario|q floor|Measure|Dynamic minus fixed|Paired bootstrap 95% interval|Positive / negative stream differences|
|---|---:|---|---:|---:|---:|
"""
        + "\n".join(
            f"| {row.scenario} | {row.q_min:.2f} | {row.paired_measure} | {row.predictable_minus_fixed_mean:+.4f} | [{row.paired_bootstrap_95_low:+.4f}, {row.paired_bootstrap_95_high:+.4f}] | {row.positive_discordances} / {row.negative_discordances} |"
            for row in paired_power.itertuples(index=False)
        )
        + f"""

These are development-grid estimates from the locked seed block. Wilson intervals describe individual cells; the paired bootstrap resamples whole streams. They are unadjusted across floors and methods, so this block does not select a winning floor or establish a confirmatory advantage. A selected configuration needs an independent seed block and an explicit familywise error plan. Zero false escalations, if observed, are not proof of the 5% guarantee.

The study uses independent synthetic events and immediate randomized labels. It does not establish robustness to time dependence, informative label availability, delayed feedback, shifting policies, or deployment interventions. Query-policy comparisons are coupled through common random numbers but can follow different propensity and stopping paths. The harm exposure metric sums evaluator-known expected excess cost at the registered dose from onset through the alarm event, or through the last processed event if no alarm occurs; it is synthetic evaluator output only.

No figure is included because project guidance requires PaperBanana and no callable PaperBanana tool is available in this session. The validated summary tables and per-stream Parquet metrics are the reported outputs.

Reproduce with:

```powershell
uv run python scripts/calibrate_history_predictable_query_bounds.py --streams {config["streams_per_scenario"]} --horizon {config["horizon"]} --seed {config["rng_root_seed"]} --device {device_name} --output {output.as_posix()}
uv run pytest tests/test_history_predictable_query_bounds.py -q
```
"""
    )


def run(*, streams: int, horizon: int, seed: int, device_name: str, output: Path) -> Path:
    validate_configuration(streams, horizon, seed, device_name)
    device = torch.device(device_name)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    if onset <= 0 or onset >= horizon:
        raise ValueError("harm onset must lie strictly inside the monitoring horizon")
    if abs(expected_population_contrast(high_probability=P_HIGH_NULL)) > 1e-12:
        raise RuntimeError("null generator does not have exactly zero aggregate expected contrast")
    for effect in HARM_EFFECTS:
        actual = expected_population_contrast(high_probability=high_probability_for_effect(effect))
        if abs(actual - effect) > 1e-12:
            raise RuntimeError("harm generator does not have the registered aggregate effect")

    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    rows: list[dict[str, object]] = []
    config = configuration(streams, horizon, seed, device)
    arms = [("uniform", 0.20, 0.20, "fixed")]
    for q_min in Q_FLOORS:
        arms.append(("evidence_directed", q_min, q_min, "fixed"))
        arms.append(("evidence_directed", q_min, q_min, "predictable"))
    for scenario in SCENARIOS:
        for query_policy, q_min, bound_floor, bound_mode in arms:
            rows.extend(
                simulate_arm(
                    scenario=scenario,
                    streams=streams,
                    horizon=horizon,
                    seed=seed,
                    data=data,
                    device=device,
                    query_policy=query_policy,
                    q_min=bound_floor,
                    bound_mode=bound_mode,
                )
            )

    metrics = pd.DataFrame(rows)
    if len(metrics) != streams * len(SCENARIOS) * (1 + 2 * len(Q_FLOORS)):
        raise RuntimeError("unexpected number of per-stream rows")
    if metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("duplicate scenario-arm-seed metric row")
    if not metrics["budget_respected"].all():
        raise RuntimeError("hard label budget was violated")
    summary, paired = summarize(metrics)

    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    metrics_path = metrics_dir / "stream_metrics.parquet"
    summary_path = metrics_dir / "summary.csv"
    paired_path = metrics_dir / "paired_contrasts.csv"
    report_path = reports_dir / "calibration_and_harm_results.md"
    metrics.to_parquet(metrics_path, index=False)
    summary.to_csv(summary_path, index=False)
    paired.to_csv(paired_path, index=False)

    report_path.write_text(
        render_report(summary, paired, config, device_name, output), encoding="utf-8"
    )
    source_files = [
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("docs/history_predictable_bound_calibration_protocol.md"),
        Path("src/shiftlab/dive/eprocess.py"),
        Path("src/shiftlab/dive/estimators.py"),
    ]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    artifacts = [metrics_path, summary_path, paired_path, report_path]
    manifest = {
        "experiment": "history_predictable_ppi_bound_null_calibration_and_localized_harm",
        "classification": "locked_development_grid_not_confirmatory",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": config,
        "git_commit": commit,
        "environment": {
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        },
        "input_data": "synthetic only; no raw event-level export",
        "oracle_boundary": "oracle outcome probabilities and conditional means only used to generate DGP/evaluator harm; learner receives sampled pre-monitor training labels and current context",
        "visuals_generated": False,
        "reproducibility": {
            "script_sha256": sha256(source_files[0]),
            "source_file_sha256": {str(path): sha256(path) for path in source_files[1:]},
        },
        "artifact_sha256": {str(path.relative_to(output)): sha256(path) for path in artifacts},
        "complete": True,
        "rows": len(metrics),
    }
    (reports_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def reanalyze_existing(output: Path) -> Path:
    """Rebuild summaries and reports from verified saved stream metrics."""
    reports_dir = output / "reports"
    metrics_dir = output / "metrics"
    manifest_path = reports_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics_path = metrics_dir / "stream_metrics.parquet"
    recorded_metrics_hash = manifest.get("artifact_sha256", {}).get(
        str(metrics_path.relative_to(output))
    )
    if recorded_metrics_hash != sha256(metrics_path):
        raise ValueError("saved stream metrics do not match the run manifest")
    metrics = pd.read_parquet(metrics_path)
    summary, paired = summarize(metrics)
    summary_path = metrics_dir / "summary.csv"
    paired_path = metrics_dir / "paired_contrasts.csv"
    report_path = reports_dir / "calibration_and_harm_results.md"
    summary.to_csv(summary_path, index=False)
    paired.to_csv(paired_path, index=False)
    config = manifest["configuration"]
    report_path.write_text(
        render_report(summary, paired, config, str(config["requested_device"]), output),
        encoding="utf-8",
    )
    source_files = [
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("docs/history_predictable_bound_calibration_protocol.md"),
        Path("src/shiftlab/dive/eprocess.py"),
        Path("src/shiftlab/dive/estimators.py"),
    ]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    manifest["git_commit"] = commit
    manifest["analysis_recomputed_without_regenerating_streams"] = True
    manifest["reproducibility"] = {
        "script_sha256": sha256(source_files[0]),
        "source_file_sha256": {str(path): sha256(path) for path in source_files[1:]},
    }
    artifacts = [metrics_path, summary_path, paired_path, report_path]
    manifest["artifact_sha256"] = {
        str(path.relative_to(output)): sha256(path) for path in artifacts
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=27102027)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        help="rebuild summaries and report from saved, checksum-verified metrics without rerunning",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/history_predictable_bound_calibration_2000")
    )
    args = parser.parse_args()
    if args.reanalyze:
        path = reanalyze_existing(args.output)
        print(f"Reanalyzed verified stream metrics without resimulation: {path}")
        return
    path = run(
        streams=args.streams,
        horizon=args.horizon,
        seed=args.seed,
        device_name=args.device,
        output=args.output,
    )
    print(f"Completed {args.streams} streams per scenario on {args.device}: {path}")


if __name__ == "__main__":
    main()
