"""Development screen for history-only PPI querying with delayed labels.

This is not a confirmation. The monitor commits eventwise PPI increments only
when the contiguous event-time prefix is observable. Query budget is reserved
when a request is made, and a queried outcome is first accessed at its arrival.
The default DGP uses iid events and an outcome-independent fixed delay. Optional
stress profiles make label latency depend on the sign of the queried cost
contrast; those profiles are evaluator-side and latency is not monitor evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HARM_SCENARIOS,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        NULL_SCENARIO,
        Q_MAX,
        STAKES,
        STRICT_NEGATIVE_SCENARIO,
        M,
        _log_e,
        evidence_directed_propensity,
        generate_common_random_numbers,
        scenario_harm_effect,
    )
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HARM_SCENARIOS,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        NULL_SCENARIO,
        Q_MAX,
        STAKES,
        STRICT_NEGATIVE_SCENARIO,
        M,
        _log_e,
        evidence_directed_propensity,
        generate_common_random_numbers,
        scenario_harm_effect,
    )

Q_MIN = 0.05
DELAY_PROFILES = ("fixed", "positive_fast", "positive_slow")


def simulate_delayed_arm_gpu_reference(
    *,
    scenario: str,
    streams: int,
    horizon: int,
    seed: int,
    data: dict[str, torch.Tensor],
    device: torch.device,
    delay: int,
    bound_mode: str,
    q_min: float = Q_MIN,
) -> list[dict[str, object]]:
    """Run one vectorized arm; only the evaluator reveals labels after ``delay``."""
    if delay < 1:
        raise ValueError("delayed screen requires delay >= 1")
    if bound_mode not in {"fixed", "predictable"}:
        raise ValueError("bound_mode must be fixed or predictable")
    if not 0 < q_min <= LABEL_BUDGET_RATE <= Q_MAX <= 1:
        raise ValueError("require q_min <= label-budget rate <= q_max")
    if data["context"].shape != (horizon, streams):
        raise ValueError("data dimensions do not match streams and horizon")

    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    harm_effect = scenario_harm_effect(scenario)
    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    stakes = torch.tensor(STAKES, dtype=torch.float64, device=device)
    log_weights = torch.full_like(stakes, -math.log(len(STAKES)))
    log_wealth = torch.zeros((streams, len(STAKES)), dtype=torch.float64, device=device)
    remaining = torch.full((streams,), budget, dtype=torch.int64, device=device)
    labels = torch.zeros_like(remaining)
    processed = torch.zeros_like(remaining)
    cursor = torch.zeros_like(remaining)
    first_alarm = torch.full((streams,), -1, dtype=torch.int64, device=device)
    alarm_wall = torch.full_like(first_alarm, -1)
    propensity_sum = torch.zeros(streams, dtype=torch.float64, device=device)
    bound_sum = torch.zeros_like(propensity_sum)

    # These arrays are learner-visible evidence state. A queried contrast is
    # not filled until its registered arrival; only proxy/propensity are stored
    # when the request is made.
    estimate = torch.zeros((horizon, streams), dtype=torch.float64, device=device)
    event_bound = torch.full_like(estimate, M * (2 / q_min - 1))
    event_known = torch.zeros((horizon, streams), dtype=torch.bool, device=device)
    event_queried = torch.zeros_like(event_known)
    event_proxy = torch.zeros_like(estimate)
    event_propensity = torch.full_like(estimate, LABEL_BUDGET_RATE)
    event_included = torch.zeros_like(event_known)
    support_violation = torch.zeros(streams, dtype=torch.bool, device=device)
    factor_violation = torch.zeros_like(support_violation)
    propensity_violation = torch.zeros_like(support_violation)
    stream_index = torch.arange(streams, device=device)
    threshold = -math.log(ALPHA)

    def release_ready_prefix(wall_time: int, registered: int) -> None:
        """Commit up to delay+1 ready items per stream in event order."""
        nonlocal log_wealth, first_alarm, alarm_wall, support_violation, factor_violation
        for _ in range(delay + 2):
            event_index = cursor.clamp(max=horizon - 1)
            ready = (cursor < registered) & event_known[event_index, stream_index]
            values = estimate[event_index, stream_index]
            bounds = event_bound[event_index, stream_index]
            factors = 1 + (values[:, None] / bounds[:, None]) * stakes[None, :]
            update = ready & event_included[event_index, stream_index]
            support_violation |= update & (torch.abs(values) > bounds + 1e-8)
            factor_violation |= update & (factors <= 0).any(dim=1)
            candidate = log_wealth + torch.log(factors)
            log_wealth = torch.where(update[:, None], candidate, log_wealth)
            crossed = update & (first_alarm < 0) & (_log_e(log_wealth, log_weights) >= threshold)
            first_alarm = torch.where(crossed, event_index, first_alarm)
            alarm_wall = torch.where(crossed, wall_time, alarm_wall)
            processed.add_(update.to(torch.int64))
            propensity_sum.add_(torch.where(update, event_propensity[event_index, stream_index], 0))
            bound_sum.add_(torch.where(update, bounds, 0))
            cursor.add_(ready.to(torch.int64))

    def reveal_due(event_index: int, wall_time: int) -> None:
        """Reveal only queried outcomes whose registered delay has elapsed."""
        if event_index < 0 or event_index >= horizon:
            return
        queried = event_queried[event_index]
        context = data["context"][event_index]
        high = context == 1
        if "p_low" in data and "p_high" in data:
            low_probability = data["p_low"][event_index]
            high_probability = data["p_high"][event_index]
            if harm_effect is not None and event_index >= onset:
                high_probability = (
                    high_probability
                    - float(data["effect_probability_shift_per_unit"]) * harm_effect
                )
            probability = torch.where(high, high_probability, low_probability)
        else:
            high_probability_value = 0.488
            if harm_effect is not None and event_index >= onset:
                high_probability_value -= harm_effect / HIGH_COST
            probability = torch.where(
                high,
                torch.full((streams,), high_probability_value, device=device),
                torch.full((streams,), 0.56, device=device),
            )
        # This is the first access to the outcome uniform for queried events.
        y = data["outcome_uniform"][event_index] < probability
        cost = torch.where(high, HIGH_COST, 1.0)
        contrast = cost * (1 - 2 * y.to(torch.float32))
        q = event_propensity[event_index]
        estimate[event_index, queried] = (
            event_proxy[event_index, queried]
            + (contrast[queried].to(torch.float64) - event_proxy[event_index, queried]) / q[queried]
        )
        event_known[event_index] |= queried

    def make_request(event_index: int) -> None:
        prior_log_e = _log_e(log_wealth, log_weights)
        active = (remaining > 0) & (first_alarm < 0)
        remaining_fraction = remaining.to(torch.float64) / max(budget, 1)
        q = evidence_directed_propensity(prior_log_e, remaining_fraction, q_min=q_min)
        q = torch.where(active, q, torch.full_like(q, q_min))
        propensity_violation.__ior__(active & ((q < q_min - 1e-12) | (q > Q_MAX + 1e-12)))
        queried = active & (data["query_uniform"][event_index] < q)
        context = data["context"][event_index]
        proxy = torch.where(context == 1, data["h_high"], data["h_low"]).to(torch.float64)
        event_proxy[event_index] = proxy
        event_propensity[event_index] = q
        if bound_mode == "predictable":
            event_bound[event_index] = M * (2 / q - 1)
        estimate[event_index] = proxy
        event_queried[event_index] = queried
        event_known[event_index] = ~queried
        event_included[event_index] = active
        labels.add_(queried.to(torch.int64))
        remaining.sub_(queried.to(torch.int64))

    for wall_time in range(horizon):
        # Fixed delay: label for event wall_time-delay becomes observable now.
        due = wall_time - delay
        reveal_due(due, wall_time)
        release_ready_prefix(wall_time, wall_time)
        make_request(wall_time)
        # Query delay is positive, so current-event labels cannot arrive now.

    # Flush all pending queried labels and the resulting contiguous prefix.
    for wall_time in range(horizon, horizon + delay):
        due = wall_time - delay
        reveal_due(due, wall_time)
        release_ready_prefix(wall_time, horizon)

    if bool((cursor != horizon).any()):
        raise RuntimeError("delayed evidence buffer did not release every event")
    if bool((labels > budget).any()):
        raise RuntimeError("query-time label reservation exceeded the hard cap")
    if bool(support_violation.any()):
        raise RuntimeError("a delayed PPI increment exceeded its registered eventwise bound")
    if bool(factor_violation.any()):
        raise RuntimeError("a delayed eventwise betting factor was nonpositive")
    if bool(propensity_violation.any()):
        raise RuntimeError("a history-based propensity escaped its registered range")

    processed_np = processed.cpu().numpy()
    labels_np = labels.cpu().numpy()
    alarms_np = first_alarm.cpu().numpy()
    alarm_wall_np = alarm_wall.cpu().numpy()
    prop_np = propensity_sum.cpu().numpy()
    bound_np = bound_sum.cpu().numpy()
    harmful = harm_effect is not None and harm_effect > 0
    reached = (processed_np > onset) if harmful else np.zeros(streams, dtype=bool)
    detected = (alarms_np >= onset) & (alarms_np >= 0) if harmful else np.zeros(streams, dtype=bool)
    false = (alarms_np >= 0) & ((alarms_np < onset) if harmful else True)
    exposure = np.zeros(streams, dtype=np.int64)
    if harmful:
        stop = np.where(alarms_np >= 0, alarms_np, horizon - 1)
        exposure = np.maximum(0, stop - onset + 1)

    return [
        {
            "scenario": scenario,
            "stream_id": stream,
            "stream_seed_id": seed + stream,
            "arm": f"evidence_qmin_{q_min:.2f}_{bound_mode}_delay_{delay}",
            "bound_mode": bound_mode,
            "feedback_delay": delay,
            "events_processed": int(processed_np[stream]),
            "labels_queried": int(labels_np[stream]),
            "hard_label_budget": budget,
            "budget_respected": bool(labels_np[stream] <= budget),
            "mean_bound_processed": float(bound_np[stream] / max(processed_np[stream], 1)),
            "mean_propensity_processed": float(prop_np[stream] / max(processed_np[stream], 1)),
            "first_alarm_event": int(alarms_np[stream]) if alarms_np[stream] >= 0 else None,
            "first_alarm_wall_time": int(alarm_wall_np[stream])
            if alarm_wall_np[stream] >= 0
            else None,
            "false_escalation": bool(false[stream]),
            "onset_reached": bool(reached[stream]),
            "post_onset_detection": bool(detected[stream]),
            "detection_delay_event_time": float(alarms_np[stream] - onset)
            if detected[stream]
            else None,
            "detection_delay_wall_time": float(alarm_wall_np[stream] - onset)
            if detected[stream]
            else None,
            "evaluator_cumulative_expected_harm_cost": float(
                max(harm_effect or 0.0, 0.0) * exposure[stream]
            ),
        }
        for stream in range(streams)
    ]


def simulate_delayed_arm(
    *,
    scenario: str,
    streams: int,
    horizon: int,
    seed: int,
    data: dict[str, torch.Tensor],
    device: torch.device,
    delay: int,
    bound_mode: str,
    delay_profile: str = "fixed",
    q_min: float = Q_MIN,
) -> list[dict[str, object]]:
    """Fast NumPy monitor replay over CUDA- or CPU-generated common streams.

    The state recursion is sequential in event and arrival time. Vectorized
    NumPy prefix updates avoid thousands of small GPU kernel launches; stream
    generation remains on the requested device.
    """
    if delay < 1 or bound_mode not in {"fixed", "predictable"}:
        raise ValueError("require delay >= 1 and a fixed or predictable bound")
    if delay_profile not in DELAY_PROFILES or (delay_profile != "fixed" and delay < 2):
        raise ValueError(
            "delay_profile must be fixed/positive_fast/positive_slow; "
            "informative profiles require delay >= 2"
        )
    arrays = {
        key: value.detach().cpu().numpy() if torch.is_tensor(value) else value
        for key, value in data.items()
    }
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    harm_effect = scenario_harm_effect(scenario)
    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    stakes = np.asarray(STAKES, dtype=np.float64)
    log_weights = np.full(len(stakes), -math.log(len(stakes)), dtype=np.float64)
    log_wealth = np.zeros((streams, len(stakes)), dtype=np.float64)
    remaining = np.full(streams, budget, dtype=np.int64)
    labels = np.zeros(streams, dtype=np.int64)
    processed = np.zeros(streams, dtype=np.int64)
    cursor = np.zeros(streams, dtype=np.int64)
    first_alarm = np.full(streams, -1, dtype=np.int64)
    alarm_wall = np.full(streams, -1, dtype=np.int64)
    propensity_sum = np.zeros(streams, dtype=np.float64)
    bound_sum = np.zeros(streams, dtype=np.float64)
    estimate = np.zeros((horizon, streams), dtype=np.float64)
    event_bound = np.full((horizon, streams), M * (2 / q_min - 1), dtype=np.float64)
    event_known = np.zeros((horizon, streams), dtype=bool)
    event_queried = np.zeros_like(event_known)
    event_proxy = np.zeros_like(estimate)
    event_propensity = np.full_like(estimate, LABEL_BUDGET_RATE)
    event_included = np.zeros_like(event_known)
    evaluator_contrast = np.zeros_like(estimate)
    requested_delay_sum = np.zeros(streams, dtype=np.float64)
    positive_delay_sum = np.zeros(streams, dtype=np.float64)
    negative_delay_sum = np.zeros(streams, dtype=np.float64)
    positive_delay_count = np.zeros(streams, dtype=np.int64)
    negative_delay_count = np.zeros(streams, dtype=np.int64)
    factor_violation = np.zeros(streams, dtype=bool)
    support_violation = np.zeros(streams, dtype=bool)
    propensity_violation = np.zeros(streams, dtype=bool)
    stream_index = np.arange(streams)
    threshold = -math.log(ALPHA)
    max_delay = delay
    arrival_queue: list[list[tuple[int, np.ndarray]]] = [[] for _ in range(horizon + max_delay)]

    def release(registered: int, wall_time: int) -> None:
        nonlocal log_wealth, factor_violation, support_violation, first_alarm, alarm_wall
        nonlocal processed, propensity_sum, bound_sum, cursor
        for _ in range(registered + 1):
            event_index = np.minimum(cursor, horizon - 1)
            ready = (cursor < registered) & event_known[event_index, stream_index]
            if not ready.any():
                break
            values = estimate[event_index, stream_index]
            bounds = event_bound[event_index, stream_index]
            update = ready & event_included[event_index, stream_index]
            support_violation |= update & (np.abs(values) > bounds + 1e-8)
            with np.errstate(divide="ignore", invalid="ignore"):
                factors = 1 + (values[:, None] / bounds[:, None]) * stakes[None, :]
                factor_violation |= update & (factors <= 0).any(axis=1)
                log_factors = np.log(factors)
            candidate = log_wealth + np.where(update[:, None], log_factors, 0.0)
            crossed_value = logsumexp(candidate + log_weights[None, :], axis=1)
            crossed = update & (first_alarm < 0) & (crossed_value >= threshold)
            first_alarm[crossed] = event_index[crossed]
            alarm_wall[crossed] = wall_time
            log_wealth = candidate
            processed += update
            propensity_sum += np.where(update, event_propensity[event_index, stream_index], 0.0)
            bound_sum += np.where(update, bounds, 0.0)
            cursor += ready

    def outcome_probability(event_index: int) -> np.ndarray:
        context = arrays["context"][event_index]
        high = context == 1
        if "p_low" in arrays and "p_high" in arrays:
            low_probability = arrays["p_low"][event_index]
            high_probability = arrays["p_high"][event_index]
            if harm_effect is not None and event_index >= onset:
                high_probability = (
                    high_probability
                    - float(arrays["effect_probability_shift_per_unit"]) * harm_effect
                )
            probability = np.where(high, high_probability, low_probability)
        else:
            high_probability_value = 0.488
            if harm_effect is not None and event_index >= onset:
                high_probability_value -= harm_effect / HIGH_COST
            probability = np.where(high, high_probability_value, 0.56)
        return probability

    def schedule_feedback(event_index: int, queried: np.ndarray, wall_time: int) -> None:
        """Evaluator schedules labels; only arrivals enter learner-visible state."""
        nonlocal requested_delay_sum, positive_delay_sum, negative_delay_sum
        nonlocal positive_delay_count, negative_delay_count
        if not queried.any():
            return
        context = arrays["context"][event_index]
        high = context == 1
        probability = outcome_probability(event_index)
        y = arrays["outcome_uniform"][event_index, queried] < probability[queried]
        contrast = np.where(high[queried], HIGH_COST, 1.0) * (1 - 2 * y.astype(np.float32))
        evaluator_contrast[event_index, queried] = contrast.astype(np.float64)
        positive = queried & (evaluator_contrast[event_index] > 0)
        negative = queried & ~positive
        if delay_profile == "fixed":
            delay_by_stream = np.full(streams, delay, dtype=np.int64)
        elif delay_profile == "positive_fast":
            delay_by_stream = np.where(positive, 1, delay)
        else:
            delay_by_stream = np.where(positive, delay, 1)
        requested_delay_sum += np.where(queried, delay_by_stream, 0)
        positive_delay_sum += np.where(positive, delay_by_stream, 0)
        negative_delay_sum += np.where(negative, delay_by_stream, 0)
        positive_delay_count += positive
        negative_delay_count += negative
        for this_delay in np.unique(delay_by_stream[queried]):
            mask = queried & (delay_by_stream == this_delay)
            arrival_queue[wall_time + int(this_delay)].append((event_index, mask))

    def release_feedback(wall_time: int) -> None:
        for event_index, queried in arrival_queue[wall_time]:
            q = event_propensity[event_index, queried]
            estimate[event_index, queried] = (
                event_proxy[event_index, queried]
                + (evaluator_contrast[event_index, queried] - event_proxy[event_index, queried]) / q
            )
            event_known[event_index, queried] = True

    for wall_time in range(horizon + max_delay):
        release_feedback(wall_time)
        release(min(wall_time, horizon), wall_time)
        if wall_time >= horizon:
            continue
        log_e = logsumexp(log_wealth + log_weights[None, :], axis=1)
        active = (remaining > 0) & (first_alarm < 0)
        remaining_fraction = remaining.astype(np.float64) / max(budget, 1)
        urgency = np.clip(log_e / threshold + 0.05, 0, 1) ** 0.5
        q = q_min + (Q_MAX - q_min) * urgency * remaining_fraction
        q = np.where(active, q, q_min)
        propensity_violation |= active & ((q < q_min - 1e-12) | (q > Q_MAX + 1e-12))
        queried = active & (arrays["query_uniform"][wall_time] < q)
        context = arrays["context"][wall_time]
        proxy = np.where(context == 1, arrays["h_high"], arrays["h_low"]).astype(np.float64)
        event_proxy[wall_time] = proxy
        event_propensity[wall_time] = q
        if bound_mode == "predictable":
            event_bound[wall_time] = M * (2 / q - 1)
        event_queried[wall_time] = queried
        event_included[wall_time] = active
        event_known[wall_time] = ~queried
        estimate[wall_time] = proxy
        labels += queried
        remaining -= queried
        schedule_feedback(wall_time, queried, wall_time)

    if not np.all(cursor == horizon):
        raise RuntimeError("delayed evidence buffer did not release every event")
    if np.any(labels > budget):
        raise RuntimeError("query-time label reservation exceeded the hard cap")
    if support_violation.any() or factor_violation.any() or propensity_violation.any():
        raise RuntimeError("support, factor, or propensity invariant failed")

    harmful = harm_effect is not None and harm_effect > 0
    reached = processed > onset if harmful else np.zeros(streams, dtype=bool)
    detected = (
        (first_alarm >= onset) & (first_alarm >= 0) if harmful else np.zeros(streams, dtype=bool)
    )
    false = (first_alarm >= 0) & ((first_alarm < onset) if harmful else True)
    stop = np.where(first_alarm >= 0, first_alarm, horizon - 1)
    exposure = np.maximum(0, stop - onset + 1) if harmful else np.zeros(streams, dtype=int)
    return [
        {
            "scenario": scenario,
            "stream_id": stream,
            "stream_seed_id": seed + stream,
            "arm": f"evidence_qmin_{q_min:.2f}_{bound_mode}_{delay_profile}_delay_{delay}",
            "bound_mode": bound_mode,
            "feedback_delay": delay,
            "delay_profile": delay_profile,
            "events_processed": int(processed[stream]),
            "labels_queried": int(labels[stream]),
            "mean_feedback_delay": float(requested_delay_sum[stream] / max(labels[stream], 1)),
            "mean_positive_contrast_delay": float(
                positive_delay_sum[stream] / max(positive_delay_count[stream], 1)
            ),
            "mean_negative_contrast_delay": float(
                negative_delay_sum[stream] / max(negative_delay_count[stream], 1)
            ),
            "hard_label_budget": budget,
            "budget_respected": bool(labels[stream] <= budget),
            "mean_bound_processed": float(bound_sum[stream] / max(processed[stream], 1)),
            "mean_propensity_processed": float(propensity_sum[stream] / max(processed[stream], 1)),
            "first_alarm_event": int(first_alarm[stream]) if first_alarm[stream] >= 0 else None,
            "first_alarm_wall_time": int(alarm_wall[stream]) if alarm_wall[stream] >= 0 else None,
            "false_escalation": bool(false[stream]),
            "onset_reached": bool(reached[stream]),
            "post_onset_detection": bool(detected[stream]),
            "detection_delay_event_time": float(first_alarm[stream] - onset)
            if detected[stream]
            else None,
            "detection_delay_wall_time": float(alarm_wall[stream] - onset)
            if detected[stream]
            else None,
            "evaluator_cumulative_expected_harm_cost": float(
                max(harm_effect or 0.0, 0.0) * exposure[stream]
            ),
        }
        for stream in range(streams)
    ]


def run(
    *,
    streams: int,
    horizon: int,
    seed: int,
    delay: int,
    device_name: str,
    output: Path,
    delay_profile: str = "fixed",
) -> Path:
    if streams < 30 or horizon < 100:
        raise ValueError("development screen requires at least 30 streams and horizon 100")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if delay_profile not in DELAY_PROFILES or (delay_profile != "fixed" and delay < 2):
        raise ValueError("informative delay profiles require delay >= 2")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(device_name)
    scenarios = (NULL_SCENARIO, STRICT_NEGATIVE_SCENARIO, *HARM_SCENARIOS)
    rows: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(scenarios):
        # Disjoint streams per scenario; arms within a scenario share all RNGs.
        scenario_seed = seed + scenario_index * streams
        data = generate_common_random_numbers(
            streams=streams, horizon=horizon, seed=scenario_seed, device=device
        )
        for bound_mode in ("fixed", "predictable"):
            rows.extend(
                simulate_delayed_arm(
                    scenario=scenario,
                    streams=streams,
                    horizon=horizon,
                    seed=scenario_seed,
                    data=data,
                    device=device,
                    delay=delay,
                    bound_mode=bound_mode,
                    delay_profile=delay_profile,
                )
            )
    metrics = pd.DataFrame(rows)
    expected = streams * len(scenarios) * 2
    if len(metrics) != expected or metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("stream metrics are incomplete or duplicated")
    if not metrics["budget_respected"].all():
        raise RuntimeError("at least one stream violated its query-time label cap")

    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics").mkdir()
    (output / "reports").mkdir()
    metrics_path = output / "metrics/stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    grouped = metrics.groupby(["scenario", "bound_mode", "delay_profile"], sort=True)
    summary = grouped.agg(
        streams=("stream_id", "size"),
        false_escalations=("false_escalation", "sum"),
        detection_rate=("post_onset_detection", "mean"),
        onset_reach_rate=("onset_reached", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_events_processed=("events_processed", "mean"),
        mean_event_delay=("detection_delay_event_time", "mean"),
        mean_wall_delay=("detection_delay_wall_time", "mean"),
    ).reset_index()
    summary_path = output / "metrics/summary.csv"
    summary.to_csv(summary_path, index=False)
    report = [
        "# Delayed history-predictable bound development screen",
        "",
        f"- Streams per scenario and arm: {streams}",
        f"- Horizon: {horizon}; onset index: {math.floor(HARM_ONSET_FRACTION * horizon)}",
        f"- Feedback delay profile: {delay_profile}; fixed/slow delay: {delay} events",
        f"- Hard query cap: {math.floor(LABEL_BUDGET_RATE * horizon)} labels per stream",
        f"- Stream generation device: {device}; sequential monitor replay: CPU NumPy.",
        "- This is a development screen; it is not confirmatory evidence or a method novelty claim.",
        "- Under the iid event DGP, each q_t and its support bound are determined by previously committed prefix evidence and query spend. The monitor commits evidence in event order; latency is never included as a model feature or evidence increment.",
        "- In positive_fast/positive_slow, the evaluator assigns 1-event versus configured-delay labels based on the sign of the queried decision-cost contrast. These are informative-delay power/latency stress conditions, not new validity calibration.",
        "- The null guarantee requires the event-time conditional-mean null and a valid predictable bound given the full history used by querying. See docs/delayed_event_prefix_validity.md; no serial-dependence or policy-adaptation claim is made.",
        "- Calibration must be evaluated on fresh independent nonpositive-mean controls before a separate harm confirmation.",
        "- No figure was generated: PaperBanana is not available in the active environment.",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
    ]
    report_path = output / "reports/development_results.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "delayed_history_predictable_bound_development",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": __import__("subprocess")
        .run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        .stdout.strip(),
        "configuration": {
            "streams_per_scenario_per_arm": streams,
            "horizon": horizon,
            "seed_root": seed,
            "delay": delay,
            "delay_profile": delay_profile,
            "device": str(device),
            "monitor_backend": "numpy_cpu_event_order",
            "scenarios": scenarios,
            "arms": ("fixed", "predictable"),
            "q_min": Q_MIN,
            "q_max": Q_MAX,
            "label_budget_rate": LABEL_BUDGET_RATE,
            "outcome_independent_fixed_delay": delay_profile == "fixed",
        },
        "rows": len(metrics),
        "sha256": {
            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "shared_dgp_source": hashlib.sha256(
                Path("scripts/calibrate_history_predictable_query_bounds.py").read_bytes()
            ).hexdigest(),
            "protocol": hashlib.sha256(
                Path("docs/delayed_history_predictable_bound_protocol.md").read_bytes()
            ).hexdigest(),
            "informative_delay_protocol": hashlib.sha256(
                Path("docs/informative_delay_stress_protocol.md").read_bytes()
            ).hexdigest(),
            "metrics/stream_metrics.parquet": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
            "metrics/summary.csv": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "reports/development_results.md": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        },
        "artifacts": {
            "metrics/stream_metrics.parquet": str(metrics_path),
            "metrics/summary.csv": str(summary_path),
            "reports/development_results.md": str(report_path),
        },
        "limitations": [
            "development screen only",
            "iid event process only",
            f"delay profile {delay_profile}; informative profiles are power/latency stress tests only",
            "event-order prefix buffer; eventwise predictable support bound",
            "no serial-dependence, policy-adaptation, or latency-as-evidence claim",
        ],
    }
    (output / "reports/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=30)
    parser.add_argument("--horizon", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=27204027)
    parser.add_argument("--delay", type=int, default=12)
    parser.add_argument("--delay-profile", choices=DELAY_PROFILES, default="fixed")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/delayed_history_predictable_development_30")
    )
    args = parser.parse_args()
    print(
        run(
            streams=args.streams,
            horizon=args.horizon,
            seed=args.seed,
            delay=args.delay,
            device_name=args.device,
            output=args.output,
            delay_profile=args.delay_profile,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
