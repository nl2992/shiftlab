"""Independently calibrate and confirm predictable stake rebalancing."""

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

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        STAKES,
        M,
        scenario_harm_effect,
    )
    from scripts.confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from scripts.run_matched_path_bound_ablation import SCHEDULES, build_schedule
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
        STAKES,
        M,
        scenario_harm_effect,
    )
    from confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from run_matched_path_bound_ablation import SCHEDULES, build_schedule
    from validate_markov_predictable_query_bounds import (
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

DELAY = 12
HORIZON = 2400
CALIBRATION_SEED = 28714027
CONFIRMATION_SEED = 28724027
DEFAULT_DEVELOPMENT_MANIFEST = Path(
    "outputs/predictable_stake_portfolio_development/reports/manifest.json"
)
DEFAULT_CALIBRATION_OUTPUT = Path("outputs/predictable_stake_portfolio_calibration_2000")
DEFAULT_CONFIRMATION_OUTPUT = Path("outputs/predictable_stake_portfolio_confirmation_2000")
METHODS = ("uniform_rebalanced_eta0", "fixed_mixture_eta1")
NULL_SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO)
SCENARIOS = (*NULL_SCENARIOS, *MARKOV_HARM_SCENARIOS)
ETAS = (0.0, 1.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_development_manifest(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("selection", {}).get("selected_eta") != 0.0:
        raise ValueError("independent confirmation requires the frozen eta=0 development nominee")
    root = path.parent.parent
    for relative, expected in manifest.get("artifact_sha256", {}).items():
        artifact = root / relative
        if not artifact.is_file() or sha256(artifact) != expected:
            raise ValueError(f"development artifact failed checksum validation: {relative}")
    return manifest


def simulate_pair(
    *,
    scenario: str,
    propensity: torch.Tensor,
    data: dict[str, torch.Tensor | float],
) -> list[dict[str, object]]:
    """Replay both registered monitors on a single CUDA/CPU event and label path."""
    horizon, streams = propensity.shape
    device = propensity.device
    dtype = torch.float64
    integer = torch.int64
    row = torch.arange(streams, dtype=integer, device=device)
    stakes = torch.tensor(STAKES, dtype=dtype, device=device)
    log_prior = torch.full((len(STAKES),), -math.log(len(STAKES)), dtype=dtype, device=device)
    log_components = torch.zeros((streams, len(STAKES)), dtype=dtype, device=device)
    log_adaptive = torch.zeros(streams, dtype=dtype, device=device)
    log_eta_one = torch.zeros(streams, dtype=dtype, device=device)
    threshold = -math.log(ALPHA)
    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    effect = scenario_harm_effect(scenario)

    remaining = torch.full((streams,), budget, dtype=integer, device=device)
    labels = torch.zeros(streams, dtype=integer, device=device)
    registered = torch.zeros(streams, dtype=integer, device=device)
    cursor = torch.zeros(streams, dtype=integer, device=device)
    processed = torch.zeros(streams, dtype=integer, device=device)
    first_alarm = torch.full((streams, 2), -1, dtype=integer, device=device)
    alarm_wall = torch.full_like(first_alarm, -1)
    queried = torch.zeros((horizon, streams), dtype=torch.bool, device=device)
    known = torch.zeros_like(queried)
    included = torch.zeros_like(queried)
    estimate = torch.zeros((horizon, streams), dtype=dtype, device=device)
    proxy = torch.zeros_like(estimate)
    bound = torch.zeros_like(estimate)
    support_violations = torch.zeros(streams, dtype=torch.bool, device=device)

    def release_ready_prefix(wall_time: int) -> None:
        nonlocal \
            log_components, \
            log_adaptive, \
            log_eta_one, \
            cursor, \
            processed, \
            first_alarm, \
            alarm_wall
        while True:
            index = cursor.clamp(max=horizon - 1)
            ready = (cursor < registered) & known[index, row]
            if not bool(ready.any()):
                return
            update = ready & included[index, row]
            x = estimate[index, row]
            b = bound[index, row]
            support_violations.logical_or_(update & (torch.abs(x) > b + 1e-9))
            normalized = torch.where(b > 0, x / b, torch.zeros_like(x))
            log_factors = torch.log1p(normalized[:, None] * stakes[None, :])
            adaptive_increment = torch.logsumexp(log_factors, dim=1) - math.log(len(STAKES))
            log_adaptive = log_adaptive + torch.where(update, adaptive_increment, 0.0)
            prior_log_e = torch.logsumexp(log_components + log_prior[None, :], dim=1)
            posterior_weights = torch.exp(
                log_components + log_prior[None, :] - prior_log_e[:, None]
            )
            eta_one_increment = torch.logsumexp(torch.log(posterior_weights) + log_factors, dim=1)
            log_eta_one = log_eta_one + torch.where(update, eta_one_increment, 0.0)
            log_components = log_components + torch.where(
                update[:, None], log_factors, torch.zeros_like(log_factors)
            )
            fixed_log_e = torch.logsumexp(log_components + log_prior[None, :], dim=1)
            crossing = torch.stack((log_adaptive >= threshold, fixed_log_e >= threshold), dim=1)
            newly = update[:, None] & (first_alarm < 0) & crossing
            alarm_events = index[:, None].expand(-1, 2)
            alarm_walls = torch.full_like(alarm_events, wall_time)
            first_alarm = torch.where(newly, alarm_events, first_alarm)
            alarm_wall = torch.where(newly, alarm_walls, alarm_wall)
            processed = processed + update.to(integer)
            cursor = cursor + ready.to(integer)

    def release_label(event: int) -> None:
        if event < 0 or event >= horizon:
            return
        mask = queried[event]
        if not bool(mask.any()):
            return
        context = data["context"][event]
        high = context == 1
        p_high = data["p_high"][event].to(dtype)
        if effect is not None:
            p_high = p_high - float(data["effect_probability_shift_per_unit"]) * effect
        probability = torch.where(high, p_high, data["p_low"][event].to(dtype))
        outcome = data["outcome_uniform"][event].to(dtype) < probability
        cost = torch.where(
            high,
            torch.full_like(probability, HIGH_COST, dtype=dtype),
            torch.ones_like(probability, dtype=dtype),
        )
        contrast = cost * (1 - 2 * outcome.to(dtype))
        corrected = proxy[event] + (contrast - proxy[event]) / propensity[event]
        estimate[event] = torch.where(mask, corrected, estimate[event])
        known[event] = known[event] | mask

    for wall_time in range(horizon):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
        active = remaining > 0
        q = propensity[wall_time]
        query = active & (data["query_uniform"][wall_time].to(dtype) < q)
        context = data["context"][wall_time]
        high = context == 1
        current_proxy = torch.where(high, data["h_high"], data["h_low"]).to(dtype)
        proxy[wall_time] = torch.where(active, current_proxy, 0.0)
        estimate[wall_time] = proxy[wall_time]
        queried[wall_time] = query
        included[wall_time] = active
        known[wall_time] = ~query | ~active
        current_bound = M * (2 / q - 1)
        bound[wall_time] = torch.where(active, current_bound, 0.0)
        remaining = remaining - query.to(integer)
        labels = labels + query.to(integer)
        registered = registered + active.to(integer)

    for wall_time in range(horizon, horizon + DELAY):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
    if not torch.equal(cursor, registered):
        raise RuntimeError("not every enrolled event was committed in event order")
    if bool((labels > budget).any()):
        raise RuntimeError("hard label budget exceeded")
    if bool(support_violations.any()):
        raise RuntimeError("predictable support bound was violated")
    fixed_log_e = torch.logsumexp(log_components + log_prior[None, :], dim=1)
    if not torch.allclose(log_eta_one, fixed_log_e, rtol=0, atol=1e-12):
        raise RuntimeError("eta=1 portfolio failed fixed-mixture identity")

    labels_cpu = labels.cpu().numpy()
    processed_cpu = processed.cpu().numpy()
    registered_cpu = registered.cpu().numpy()
    alarms_cpu = first_alarm.cpu().numpy()
    walls_cpu = alarm_wall.cpu().numpy()
    support_cpu = support_violations.cpu().numpy()
    states = data["regime_state"].cpu().numpy()
    coefficient = np.where(states == 0, 4 / 3, 2 / 3)
    seed = int(data.get("seed", 0))
    rows: list[dict[str, object]] = []
    for stream in range(streams):
        for method_index, method in enumerate(METHODS):
            alarm = int(alarms_cpu[stream, method_index])
            harmful = effect is not None and effect > 0
            detected = bool(harmful and alarm >= onset)
            false = bool(alarm >= 0 and (alarm < onset if harmful else True))
            stop_at = alarm if alarm >= 0 else int(processed_cpu[stream]) - 1
            exposure = (
                float(effect * coefficient[onset : stop_at + 1, stream].sum())
                if harmful and stop_at >= onset
                else 0.0
            )
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "stream_id": stream,
                    "stream_seed_id": seed + stream,
                    "events_processed": int(processed_cpu[stream]),
                    "registered_events": int(registered_cpu[stream]),
                    "labels_queried": int(labels_cpu[stream]),
                    "hard_label_budget": budget,
                    "budget_respected": bool(labels_cpu[stream] <= budget),
                    "first_alarm_event": alarm if alarm >= 0 else None,
                    "first_alarm_wall_time": int(walls_cpu[stream, method_index])
                    if alarm >= 0
                    else None,
                    "false_escalation": false,
                    "onset_reached": bool(processed_cpu[stream] > onset) if harmful else None,
                    "post_onset_detection": detected,
                    "detection_delay_event_time": float(alarm - onset) if detected else None,
                    "detection_delay_wall_time": float(walls_cpu[stream, method_index] - onset)
                    if detected
                    else None,
                    "evaluator_cumulative_expected_harm_cost": exposure,
                    "support_violation": bool(support_cpu[stream]),
                }
            )
    return rows


def calibrate(metrics: pd.DataFrame, *, alpha: float = 0.05) -> pd.DataFrame:
    rows = []
    family_size = len(NULL_SCENARIOS) * len(METHODS)
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        false_count = int(group["false_escalation"].sum())
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "false_escalations": false_count,
                "false_escalation_rate": false_count / len(group),
                "simultaneous_one_sided_95_upper": exact_one_sided_upper(
                    false_count, len(group), alpha / family_size
                ),
                "budget_violations": int((~group["budget_respected"]).sum()),
                "support_violations": int(group["support_violation"].sum()),
            }
        )
    return pd.DataFrame(rows)


def confirm(
    metrics: pd.DataFrame, *, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    harmful = metrics[metrics["scenario"].isin(MARKOV_HARM_SCENARIOS)]
    summary = (
        harmful.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            detections=("post_onset_detection", "sum"),
            detection_rate=("post_onset_detection", "mean"),
            false_escalations=("false_escalation", "sum"),
            onset_reached=("onset_reached", "sum"),
            mean_labels=("labels_queried", "mean"),
            mean_events_processed=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    pivot = harmful.pivot(
        index=["scenario", "stream_id"],
        columns="method",
        values=[
            "post_onset_detection",
            "labels_queried",
            "events_processed",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    per_dose = []
    for scenario in MARKOV_HARM_SCENARIOS:
        part = pivot.loc[scenario]
        adaptive = part[("post_onset_detection", METHODS[0])].to_numpy(dtype=float)
        fixed = part[("post_onset_detection", METHODS[1])].to_numpy(dtype=float)
        detection_delta = adaptive - fixed
        labels_delta = part[("labels_queried", METHODS[0])].to_numpy(dtype=float) - part[
            ("labels_queried", METHODS[1])
        ].to_numpy(dtype=float)
        exposure_delta = part[("evaluator_cumulative_expected_harm_cost", METHODS[0])].to_numpy(
            dtype=float
        ) - part[("evaluator_cumulative_expected_harm_cost", METHODS[1])].to_numpy(dtype=float)
        per_dose.append(
            {
                "scenario": scenario,
                "adaptive_detection_rate": float(adaptive.mean()),
                "fixed_detection_rate": float(fixed.mean()),
                "detection_difference": float(detection_delta.mean()),
                "labels_difference": float(labels_delta.mean()),
                "expected_exposure_difference": float(exposure_delta.mean()),
                "all_onsets_reached": bool(
                    harmful.loc[harmful["scenario"] == scenario, "onset_reached"].all()
                ),
            }
        )
    seed_macro = np.stack(
        [
            (
                pivot.loc[scenario][("post_onset_detection", METHODS[0])].to_numpy(dtype=float)
                - pivot.loc[scenario][("post_onset_detection", METHODS[1])].to_numpy(dtype=float)
            )
            for scenario in MARKOV_HARM_SCENARIOS
        ],
        axis=1,
    ).mean(axis=1)
    detection_ci = paired_bootstrap_interval(seed_macro, seed=seed + 99173)
    label_delta = float(np.mean([row["labels_difference"] for row in per_dose]))
    exposure_delta = float(np.mean([row["expected_exposure_difference"] for row in per_dose]))
    primary = {
        "candidate": METHODS[0],
        "reference": METHODS[1],
        "macro_detection_difference": float(seed_macro.mean()),
        "paired_bootstrap_95_low": detection_ci[0],
        "paired_bootstrap_95_high": detection_ci[1],
        "mean_labels_difference": label_delta,
        "mean_evaluator_expected_exposure_difference": exposure_delta,
        "streams_per_dose": int(metrics["stream_id"].nunique()),
        "all_onsets_reached": bool(all(row["all_onsets_reached"] for row in per_dose)),
        "retention_gate_passed": bool(
            seed_macro.mean() >= 0.02
            and detection_ci[0] > 0
            and label_delta <= 0
            and all(row["all_onsets_reached"] for row in per_dose)
        ),
    }
    return summary, pd.DataFrame(per_dose), primary


def run_stage(
    *,
    stage: str,
    streams: int,
    seed: int,
    horizon: int,
    device_name: str,
    output: Path,
    development_manifest: Path = DEFAULT_DEVELOPMENT_MANIFEST,
    calibration_summary: Path | None = None,
) -> Path:
    if stage not in {"calibration", "confirmation"}:
        raise ValueError("stage must be calibration or confirmation")
    expected_seed = CALIBRATION_SEED if stage == "calibration" else CONFIRMATION_SEED
    if streams < 30 or horizon < 100 or seed != expected_seed:
        raise ValueError("streams, horizon, or frozen stage seed is invalid")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    validate_development_manifest(development_manifest)
    if stage == "confirmation":
        if calibration_summary is None or not calibration_summary.is_file():
            raise ValueError("confirmation requires the independent calibration summary")
        calibration = pd.read_csv(calibration_summary)
        if (
            len(calibration) != 4
            or not calibration["simultaneous_one_sided_95_upper"].le(0.05).all()
        ):
            raise ValueError("confirmation is gated on all four calibrated upper limits <= 0.05")
        if calibration["budget_violations"].sum() or calibration["support_violations"].sum():
            raise ValueError("calibration invariant violations block confirmation")

    verify_dgp_algebra()
    device = torch.device(device_name)
    started = time.monotonic()
    data = generate_markov_dependent_data(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    data["seed"] = seed
    schedule_name, low, high, high_slots = next(
        item for item in SCHEDULES if item[0] == "periodic_q080"
    )
    propensity_np = build_schedule(
        name=schedule_name,
        low=low,
        high=high,
        high_slots=high_slots,
        horizon=horizon,
        streams=streams,
    )
    propensity = torch.as_tensor(propensity_np, dtype=torch.float64, device=device)
    scenarios = NULL_SCENARIOS if stage == "calibration" else MARKOV_HARM_SCENARIOS
    metrics = pd.DataFrame(
        [
            row
            for scenario in scenarios
            for row in simulate_pair(scenario=scenario, propensity=propensity, data=data)
        ]
    )
    expected_rows = streams * len(scenarios) * len(METHODS)
    if (
        len(metrics) != expected_rows
        or metrics.duplicated(["scenario", "method", "stream_id"]).any()
    ):
        raise RuntimeError("incomplete or duplicated stream metrics")
    if not metrics["budget_respected"].all() or metrics["support_violation"].any():
        raise RuntimeError("budget or support invariant failed")
    path_fields = ["labels_queried", "events_processed", "registered_events"]
    paths = metrics.pivot(index=["scenario", "stream_id"], columns="method", values=path_fields)
    for field in path_fields:
        if not np.array_equal(paths[(field, METHODS[0])], paths[(field, METHODS[1])]):
            raise RuntimeError(f"methods did not share {field} paths")

    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    metrics_path = metrics_dir / "stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    artifacts = [metrics_path]
    summary_path: Path
    report_path = reports_dir / f"{stage}_results.md"
    if stage == "calibration":
        calibration = calibrate(metrics)
        summary_path = metrics_dir / "calibration_summary.csv"
        calibration.to_csv(summary_path, index=False)
        artifacts.append(summary_path)
        gate_passed = bool(
            len(calibration) == 4
            and calibration["simultaneous_one_sided_95_upper"].le(0.05).all()
            and calibration["budget_violations"].sum() == 0
            and calibration["support_violations"].sum() == 0
        )
        report = [
            "# Predictable stake portfolio independent null calibration",
            "",
            f"- Streams per method and null: {streams}; horizon: {horizon}; delay: {DELAY}.",
            f"- Device: {device}; generation and sequential delayed-feedback replay used the selected device.",
            "- Family: two methods × two nonpositive-mean null/control scenarios; one-sided exact limits use Bonferroni alpha 0.05/4.",
            f"- Frozen calibration gate passed: `{gate_passed}`.",
            "- Only if all four simultaneous upper limits are at most 5%, with no support/budget violations, may the disjoint confirmation run.",
            "- The eta=0 and eta=1 procedures share query, label, enrollment, and event-prefix paths by construction.",
            "- No figure was generated; PaperBanana is required for research visuals and unavailable in this session.",
            "",
            calibration.to_markdown(index=False, floatfmt=".5f"),
        ]
        if not gate_passed:
            report.append("\nCalibration failed; the alternative confirmation was not run.")
    else:
        summary, per_dose, primary = confirm(metrics, seed=seed)
        summary_path = metrics_dir / "harm_summary.csv"
        summary.to_csv(summary_path, index=False)
        per_dose_path = metrics_dir / "dose_effects.csv"
        per_dose.to_csv(per_dose_path, index=False)
        primary_path = reports_dir / "primary_result.json"
        primary_path.write_text(json.dumps(primary, indent=2, sort_keys=True), encoding="utf-8")
        artifacts.extend([summary_path, per_dose_path, primary_path])
        report = [
            "# Predictable stake portfolio disjoint harm confirmation",
            "",
            f"- Streams per dose and method: {streams}; horizon: {horizon}; delay: {DELAY}.",
            f"- Device: {device}; generation and sequential delayed-feedback replay used the selected device.",
            "- Candidate: uniform per-event rebalancing (`eta=0`); reference: fixed equal-weight mixture (`eta=1`).",
            "- Candidate was frozen after the development gate and the separate 4-cell calibration passed.",
            "- Primary retention gate passed: `{"
            + str(primary["retention_gate_passed"]).lower()
            + "}`.",
            "- Labels and processed event prefixes were identical between methods; all onsets and support/budget checks passed.",
            "- Evaluator exposure assumes immediate mitigation at first alarm and is not observed avoided harm.",
            "- No figure was generated; PaperBanana is required for research visuals and unavailable in this session.",
            "",
            summary.to_markdown(index=False, floatfmt=".5f"),
            "",
            per_dose.to_markdown(index=False, floatfmt=".5f"),
            "",
            json.dumps(primary, indent=2, sort_keys=True),
        ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    artifacts.append(report_path)
    source_paths = [
        Path(__file__),
        Path("docs/predictable_stake_portfolio_protocol.md"),
        Path("scripts/run_predictable_stake_portfolio.py"),
        Path("scripts/run_matched_path_bound_ablation.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    manifest = {
        "experiment": f"predictable_stake_portfolio_{stage}",
        "status": "independent_null_calibration"
        if stage == "calibration"
        else "disjoint_alternative_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "seed_root": seed,
        "streams_per_scenario_method": streams,
        "horizon": horizon,
        "delay": DELAY,
        "budget_rate": LABEL_BUDGET_RATE,
        "schedule": {
            "name": schedule_name,
            "low": low,
            "high": high,
            "high_slots_per_10": high_slots,
        },
        "methods": list(METHODS),
        "scenarios": list(scenarios),
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "runtime_seconds": time.monotonic() - started,
        "rows": len(metrics),
        "development_manifest": str(development_manifest),
        "calibration_summary": str(calibration_summary) if calibration_summary else None,
        "source_sha256": {str(path): sha256(path) for path in source_paths},
        "artifact_sha256": {str(path.relative_to(output)): sha256(path) for path in [*artifacts]},
        "shared_path_checks": {field: True for field in path_fields},
        "budget_and_support_checks_passed": True,
        "limitations": [
            "two-state Markov-volatility DGP only",
            "fixed complete outcome-independent delay of 12 events",
            "fixed action pair and source-trained proxy",
            "standard predictable convex betting construction; no novelty claim",
        ],
    }
    if stage == "calibration":
        manifest["calibration_gate_passed"] = gate_passed
    else:
        manifest["primary_retention_gate"] = primary
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("calibration", "confirmation"), required=True)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--development-manifest", type=Path, default=DEFAULT_DEVELOPMENT_MANIFEST)
    parser.add_argument("--calibration-summary", type=Path)
    args = parser.parse_args()
    seed = (
        args.seed
        if args.seed is not None
        else (CALIBRATION_SEED if args.stage == "calibration" else CONFIRMATION_SEED)
    )
    output = args.output or (
        DEFAULT_CALIBRATION_OUTPUT if args.stage == "calibration" else DEFAULT_CONFIRMATION_OUTPUT
    )
    print(
        run_stage(
            stage=args.stage,
            streams=args.streams,
            seed=seed,
            horizon=args.horizon,
            device_name=args.device,
            output=output,
            development_manifest=args.development_manifest,
            calibration_summary=args.calibration_summary,
        )
    )


if __name__ == "__main__":
    main()
