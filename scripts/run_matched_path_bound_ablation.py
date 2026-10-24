"""Development grid isolating fixed versus eventwise PPI bounds on common paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import time
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
        HIGH_COST,
        LABEL_BUDGET_RATE,
        Q_MAX,
        STAKES,
        M,
        scenario_harm_effect,
    )
    from scripts.confirm_history_predictable_query_bounds import paired_bootstrap_interval
    from scripts.validate_markov_predictable_query_bounds import (
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        Q_MAX,
        STAKES,
        M,
        scenario_harm_effect,
    )
    from confirm_history_predictable_query_bounds import paired_bootstrap_interval
    from validate_markov_predictable_query_bounds import (
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

DEFAULT_SEED = 28404027
DEFAULT_OUTPUT = Path("outputs/matched_path_bound_ablation_60")
HORIZON = 2400
DELAY = 12
SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO, *MARKOV_HARM_SCENARIOS)
SCHEDULES = (
    ("constant_q20", 0.20, 0.20, 10),
    ("periodic_q035", 0.05, 0.35, 5),
    ("periodic_q055", 0.05, 0.55, 3),
    ("periodic_q080", 0.05, 0.80, 2),
)
BOUND_MODES = ("fixed", "eventwise")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_schedule(
    *, name: str, low: float, high: float, high_slots: int, horizon: int, streams: int
) -> np.ndarray:
    """Return an exogenous, phase-balanced propensity matrix, fixed pre-outcome."""
    if not 0 < low <= high <= Q_MAX or not 1 <= high_slots <= 10:
        raise ValueError("invalid propensity schedule parameters")
    if name == "constant_q20":
        return np.full((horizon, streams), 0.20, dtype=np.float64)
    if name not in {schedule[0] for schedule in SCHEDULES}:
        raise ValueError(f"unknown schedule: {name}")
    phases = np.arange(streams, dtype=np.int64) % 10
    event = np.arange(horizon, dtype=np.int64)[:, None]
    high_mask = (event + phases[None, :]) % 10 < high_slots
    return np.where(high_mask, high, low).astype(np.float64)


def simulate_arm(
    *,
    scenario: str,
    schedule_name: str,
    propensity: np.ndarray,
    data: dict[str, torch.Tensor | float],
    bound_mode: str,
) -> list[dict[str, object]]:
    """Monitor common exogenous queries with delayed labels and event-order release."""
    if bound_mode not in BOUND_MODES:
        raise ValueError(f"unknown bound mode: {bound_mode}")
    horizon, streams = propensity.shape
    if horizon < 1 or streams < 1:
        raise ValueError("propensity matrix must have positive dimensions")
    if np.any(propensity <= 0) or np.any(propensity > Q_MAX):
        raise ValueError("all propensities must be in (0, q_max]")
    q_min = float(propensity.min())
    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    effect = scenario_harm_effect(scenario)
    arrays = {
        key: value.detach().cpu().numpy() if torch.is_tensor(value) else value
        for key, value in data.items()
    }
    expected_shape = (horizon, streams)
    for key in ("context", "outcome_uniform", "query_uniform", "p_low", "p_high"):
        if np.shape(arrays[key]) != expected_shape:
            raise ValueError(f"{key} has wrong shape")

    stakes = np.asarray(STAKES, dtype=np.float64)
    log_weights = np.full(len(stakes), -math.log(len(stakes)), dtype=np.float64)
    log_wealth = np.zeros((streams, len(stakes)), dtype=np.float64)
    threshold = -math.log(ALPHA)
    fixed_bound = M * (2 / q_min - 1)
    remaining = np.full(streams, budget, dtype=np.int64)
    labels = np.zeros(streams, dtype=np.int64)
    registered = np.zeros(streams, dtype=np.int64)
    cursor = np.zeros(streams, dtype=np.int64)
    processed = np.zeros(streams, dtype=np.int64)
    first_alarm = np.full(streams, -1, dtype=np.int64)
    alarm_wall = np.full(streams, -1, dtype=np.int64)
    known = np.zeros((horizon, streams), dtype=bool)
    queried = np.zeros_like(known)
    included = np.zeros_like(known)
    proxy = np.zeros((horizon, streams), dtype=np.float64)
    estimate = np.zeros_like(proxy)
    bound = np.full_like(proxy, fixed_bound)
    queried_outcome = np.zeros_like(proxy)
    bound_violations = np.zeros(streams, dtype=bool)
    query_order_violations = np.zeros(streams, dtype=bool)

    def release_ready_prefix(wall_time: int) -> None:
        nonlocal log_wealth
        while True:
            idx = np.minimum(cursor, horizon - 1)
            ready = (cursor < registered) & known[idx, np.arange(streams)]
            if not ready.any():
                break
            update = ready & included[idx, np.arange(streams)]
            x = estimate[idx, np.arange(streams)]
            b = bound[idx, np.arange(streams)]
            bound_violations[:] |= update & (np.abs(x) > b + 1e-9)
            factors = 1 + (x[:, None] / b[:, None]) * stakes[None, :]
            if np.any(update[:, None] & (factors <= 0)):
                raise RuntimeError("nonpositive betting factor")
            log_wealth += np.where(update[:, None], np.log(factors), 0.0)
            crossed_value = logsumexp(log_wealth + log_weights[None, :], axis=1)
            crossed = update & (first_alarm < 0) & (crossed_value >= threshold)
            first_alarm[crossed] = idx[crossed]
            alarm_wall[crossed] = wall_time
            processed[:] += update
            cursor[:] += ready

    def outcome_probability(event: int) -> np.ndarray:
        context = arrays["context"][event]
        high = context == 1
        p_high = arrays["p_high"][event].astype(np.float64, copy=True)
        if effect is not None and event >= onset:
            p_high -= float(arrays["effect_probability_shift_per_unit"]) * effect
        return np.where(high, p_high, arrays["p_low"][event])

    def release_label(event: int) -> None:
        if event < 0 or event >= horizon:
            return
        mask = queried[event]
        if not mask.any():
            return
        context = arrays["context"][event]
        high = context == 1
        y = arrays["outcome_uniform"][event] < outcome_probability(event)
        cost = np.where(high, HIGH_COST, 1.0)
        contrast = cost * (1 - 2 * y.astype(np.float64))
        queried_outcome[event, mask] = contrast[mask]
        q = propensity[event, mask]
        estimate[event, mask] = proxy[event, mask] + (contrast[mask] - proxy[event, mask]) / q
        known[event, mask] = True

    for wall_time in range(horizon):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
        active = remaining > 0
        q = propensity[wall_time]
        query = active & (arrays["query_uniform"][wall_time] < q)
        context = arrays["context"][wall_time]
        h = np.where(context == 1, arrays["h_high"], arrays["h_low"]).astype(np.float64)
        proxy[wall_time, active] = h[active]
        estimate[wall_time, active] = h[active]
        queried[wall_time] = query
        included[wall_time] = active
        known[wall_time] = ~query | ~active
        if bound_mode == "eventwise":
            bound[wall_time, active] = M * (2 / q[active] - 1)
        remaining -= query.astype(np.int64)
        labels += query.astype(np.int64)
        registered += active.astype(np.int64)
        query_order_violations |= active & (q <= 0)

    for wall_time in range(horizon, horizon + DELAY):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
    if np.any(cursor != registered):
        raise RuntimeError("not every registered event was released in event order")
    if np.any(labels > budget):
        raise RuntimeError("hard query cap exceeded")
    if bound_violations.any() or query_order_violations.any():
        raise RuntimeError("support or query-order invariant failed")

    states = arrays["regime_state"]
    coefficient = np.where(states == 0, 4 / 3, 2 / 3)
    rows: list[dict[str, object]] = []
    for stream in range(streams):
        alarm = int(first_alarm[stream])
        harmful = effect is not None and effect > 0
        detected = bool(harmful and alarm >= onset)
        false = bool(alarm >= 0 and (alarm < onset if harmful else True))
        stopped_at = alarm if alarm >= 0 else int(cursor[stream]) - 1
        exposure = (
            float(effect * coefficient[onset : stopped_at + 1, stream].sum())
            if harmful and stopped_at >= onset
            else 0.0
        )
        rows.append(
            {
                "scenario": scenario,
                "schedule": schedule_name,
                "bound_mode": bound_mode,
                "stream_id": stream,
                "stream_seed_id": int(data.get("seed", 0)) + stream,
                "feedback_delay": DELAY,
                "q_min": q_min,
                "q_max": float(propensity.max()),
                "mean_target_propensity": float(propensity[:, stream].mean()),
                "hard_label_budget": budget,
                "labels_queried": int(labels[stream]),
                "events_processed": int(processed[stream]),
                "registered_events": int(registered[stream]),
                "budget_respected": bool(labels[stream] <= budget),
                "first_alarm_event": alarm if alarm >= 0 else None,
                "first_alarm_wall_time": int(alarm_wall[stream]) if alarm >= 0 else None,
                "false_escalation": false,
                "onset_reached": bool(processed[stream] > onset) if harmful else None,
                "post_onset_detection": detected,
                "detection_delay_event_time": float(alarm - onset) if detected else None,
                "detection_delay_wall_time": float(alarm_wall[stream] - onset)
                if detected
                else None,
                "evaluator_cumulative_expected_harm_cost": exposure,
                "bound_violations": int(bound_violations[stream]),
            }
        )
    return rows


def analyze(metrics: pd.DataFrame, *, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        metrics.groupby(["scenario", "schedule", "bound_mode"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            detection_rate=("post_onset_detection", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_processed_events=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    paired: list[dict[str, object]] = []
    for schedule_index, (schedule, *_rest) in enumerate(SCHEDULES):
        sub = metrics[metrics["schedule"] == schedule]
        wide = sub.pivot(index=["scenario", "stream_id"], columns="bound_mode")
        harm_arrays: dict[str, list[np.ndarray]] = {
            "detection": [],
            "labels": [],
            "exposure": [],
        }
        for scenario in MARKOV_HARM_SCENARIOS:
            part = wide.loc[scenario]
            harm_arrays["detection"].append(
                part[("post_onset_detection", "eventwise")].to_numpy(dtype=float)
                - part[("post_onset_detection", "fixed")].to_numpy(dtype=float)
            )
            harm_arrays["labels"].append(
                part[("labels_queried", "eventwise")].to_numpy(dtype=float)
                - part[("labels_queried", "fixed")].to_numpy(dtype=float)
            )
            harm_arrays["exposure"].append(
                part[("evaluator_cumulative_expected_harm_cost", "eventwise")].to_numpy(dtype=float)
                - part[("evaluator_cumulative_expected_harm_cost", "fixed")].to_numpy(dtype=float)
            )
        for name, dose_values in harm_arrays.items():
            macro = np.stack(dose_values, axis=1).mean(axis=1)
            interval = paired_bootstrap_interval(macro, seed=seed + 90000 + schedule_index)
            paired.append(
                {
                    "schedule": schedule,
                    "metric": name,
                    "contrast": "eventwise_minus_fixed",
                    "mean_difference": float(macro.mean()),
                    "bootstrap_95_low": interval[0],
                    "bootstrap_95_high": interval[1],
                    "streams": len(macro),
                }
            )
    return summary, pd.DataFrame(paired)


def run(*, streams: int, seed: int, device_name: str, output: Path, horizon: int = HORIZON) -> Path:
    if streams < 30 or horizon < 100:
        raise ValueError("development grid requires at least 30 streams and horizon 100")
    if seed != DEFAULT_SEED:
        raise ValueError(f"development seed root is frozen at {DEFAULT_SEED}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    verify_dgp_algebra()
    device = torch.device(device_name)
    started = time.monotonic()
    data = generate_markov_dependent_data(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    data["seed"] = seed
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for schedule_name, low, high, high_slots in SCHEDULES:
            propensities = build_schedule(
                name=schedule_name,
                low=low,
                high=high,
                high_slots=high_slots,
                horizon=horizon,
                streams=streams,
            )
            for bound_mode in BOUND_MODES:
                rows.extend(
                    simulate_arm(
                        scenario=scenario,
                        schedule_name=schedule_name,
                        propensity=propensities,
                        data=data,
                        bound_mode=bound_mode,
                    )
                )
    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(SCENARIOS) * len(SCHEDULES) * len(BOUND_MODES)
    if (
        len(metrics) != expected_rows
        or metrics.duplicated(["scenario", "schedule", "bound_mode", "stream_id"]).any()
    ):
        raise RuntimeError("stream grid is incomplete or duplicated")
    if not metrics["budget_respected"].all() or metrics["bound_violations"].sum() != 0:
        raise RuntimeError("budget or support invariant failed")
    # Common-path identity checks: bound choice cannot change queries/horizon.
    path_fields = ["labels_queried", "events_processed", "registered_events"]
    paired_paths = metrics.pivot(
        index=["scenario", "schedule", "stream_id"], columns="bound_mode", values=path_fields
    )
    for field in path_fields:
        if not np.array_equal(paired_paths[(field, "fixed")], paired_paths[(field, "eventwise")]):
            raise RuntimeError(f"fixed/eventwise paths differ in {field}")
    # Constant propensity makes the two support bounds identical.
    constant = metrics[metrics["schedule"] == "constant_q20"].pivot(
        index=["scenario", "stream_id"], columns="bound_mode", values="post_onset_detection"
    )
    if not np.array_equal(constant["fixed"], constant["eventwise"]):
        raise RuntimeError("constant-q identity check failed")

    summary, paired = analyze(metrics, seed=seed)
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    metrics_path = metrics_dir / "stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    summary_path = metrics_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)
    paired_path = metrics_dir / "paired_bound_effects.csv"
    paired.to_csv(paired_path, index=False)
    report_path = reports_dir / "development_results.md"
    report = [
        "# Matched-path support-bound development grid",
        "",
        f"- Streams per scenario/schedule/bound cell: {streams}",
        f"- Horizon: {horizon}; delay: {DELAY}; pathwise label cap: {math.floor(LABEL_BUDGET_RATE * horizon)}.",
        f"- Generation device: {device}; event-order sequential replay: CPU NumPy.",
        "- All query probabilities are precommitted by schedule and stream phase. Fixed/eventwise bound arms shared identical requested labels and processed event prefixes in every cell.",
        "- The constant-q identity check passed: q=0.20 has identical fixed and eventwise bounds and stream decisions.",
        "- This 60-stream development grid does not calibrate false alarms. Null counts are diagnostic only.",
        "- No figure was generated; the frozen protocol requires PaperBanana for visuals, and these results are adequately represented by tables and Parquet.",
        "",
        "## Cell summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired eventwise-minus-fixed effects, macro-averaged over four harm doses",
        "",
        paired.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Interpretation limits",
        "",
        "The bound contrast isolates bound choice under a fixed exogenous propensity path. The schedule contrast is a development screen and may change realized horizon at the hard label cap. No choice is confirmatory; any selected schedule needs fresh null calibration and a disjoint alternative block. This is a standard predictable bounded-factor construction and makes no novelty claim.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    sources = [
        Path(__file__),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("docs/matched_path_bound_ablation_protocol.md"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    manifest = {
        "experiment": "matched_path_support_bound_ablation",
        "status": "development_only_not_calibration_or_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "seed_root": seed,
        "streams_per_scenario_schedule_bound": streams,
        "horizon": horizon,
        "delay": DELAY,
        "budget_rate": LABEL_BUDGET_RATE,
        "schedules": [
            {"name": name, "q_low": low, "q_high": high, "high_slots_per_10": slots}
            for name, low, high, slots in SCHEDULES
        ],
        "bound_modes": list(BOUND_MODES),
        "scenario_names": list(SCENARIOS),
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "runtime_seconds": time.monotonic() - started,
        "rows": len(metrics),
        "source_sha256": {str(path): sha256(path) for path in sources},
        "artifact_sha256": {
            str(path.relative_to(output)): sha256(path)
            for path in (metrics_path, summary_path, paired_path, report_path)
        },
        "path_identity_checks": {
            "bound_modes_share_labels_and_processed_events": True,
            "constant_q_fixed_and_eventwise_decisions_identical": True,
        },
        "limitations": [
            "development-only; no calibration or confirmation",
            "two-state Markov volatility DGP only",
            "fixed outcome-independent delay 12 and complete labels",
            "query propensity schedule is exogenous and does not use model evidence",
            "fixed action pair and frozen proxy",
        ],
    }
    (reports_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=60)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(
        run(
            streams=args.streams,
            seed=args.seed,
            horizon=args.horizon,
            device_name=args.device,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
