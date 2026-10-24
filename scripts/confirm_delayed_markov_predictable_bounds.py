"""Run the frozen delayed Markov calibration or disjoint harm confirmation."""

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
    from scripts.calibrate_history_predictable_query_bounds import HARM_ONSET_FRACTION
    from scripts.confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from scripts.validate_delayed_history_predictable_bounds import simulate_delayed_arm
    from scripts.validate_markov_predictable_query_bounds import (
        HARM_EFFECTS,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from calibrate_history_predictable_query_bounds import HARM_ONSET_FRACTION
    from confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from validate_delayed_history_predictable_bounds import simulate_delayed_arm
    from validate_markov_predictable_query_bounds import (
        HARM_EFFECTS,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

DELAY = 12
Q_MIN = 0.05
BUDGET_RATE = 0.20
CALIBRATION_SEED = 28204027
CONFIRMATION_SEED = 28304027
NULL_SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO)
STAGES = {
    "calibration": (NULL_SCENARIOS, CALIBRATION_SEED),
    "confirmation": (MARKOV_HARM_SCENARIOS, CONFIRMATION_SEED),
}
PRIMARY_ARMS = ("delay_12_fixed", "delay_12_predictable")
BOOTSTRAP_REPS = 10_000


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


def _correct_expected_exposure(
    rows: list[dict[str, object]], states: np.ndarray, horizon: int
) -> None:
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    state_coefficient = np.where(states == 0, 4 / 3, 2 / 3)
    for row in rows:
        effect = next(
            (
                float(delta)
                for scenario, delta in zip(MARKOV_HARM_SCENARIOS, HARM_EFFECTS, strict=True)
                if row["scenario"] == scenario
            ),
            None,
        )
        if effect is None:
            row["evaluator_cumulative_expected_harm_cost"] = 0.0
            continue
        alarm = row["first_alarm_event"]
        end = int(alarm) if alarm is not None else int(row["events_processed"]) - 1
        stream = int(row["stream_id"])
        if end < onset:
            exposure = 0.0
        else:
            exposure = effect * state_coefficient[onset : end + 1, stream].sum()
        row["evaluator_cumulative_expected_harm_cost"] = float(exposure)


def _run_cells(
    *, stage: str, streams: int, seed: int, device: torch.device, horizon: int
) -> list[dict[str, object]]:
    scenarios, _ = STAGES[stage]
    data = generate_markov_dependent_data(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    states = data["regime_state"].detach().cpu().numpy()
    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        for bound_mode in ("fixed", "predictable"):
            arm_rows = simulate_delayed_arm(
                scenario=scenario,
                streams=streams,
                horizon=horizon,
                seed=seed,
                data=data,
                device=device,
                delay=DELAY,
                bound_mode=bound_mode,
                delay_profile="fixed",
                q_min=Q_MIN,
            )
            for row in arm_rows:
                row["scenario"] = scenario
                row["regime"] = "markov_volatility"
                row["arm"] = f"delay_12_{bound_mode}"
                row["bound_mode"] = bound_mode
                row["feedback_delay"] = DELAY
                row["stream_seed_id"] = seed + int(row["stream_id"])
                row["device_generation"] = str(device)
            rows.extend(arm_rows)
    _correct_expected_exposure(rows, states=states, horizon=horizon)
    return rows


def _calibration_table(metrics: pd.DataFrame) -> pd.DataFrame:
    family_size = len(NULL_SCENARIOS) * len(PRIMARY_ARMS)
    per_cell_alpha = 0.05 / family_size
    rows: list[dict[str, object]] = []
    for scenario in NULL_SCENARIOS:
        for arm in PRIMARY_ARMS:
            group = metrics[(metrics["scenario"] == scenario) & (metrics["arm"] == arm)]
            if group.empty:
                raise RuntimeError(f"missing calibration cell: {scenario} / {arm}")
            false_count = int(group["false_escalation"].sum())
            upper = exact_one_sided_upper(false_count, len(group), per_cell_alpha)
            rows.append(
                {
                    "scenario": scenario,
                    "arm": arm,
                    "streams": len(group),
                    "false_escalations": false_count,
                    "false_escalation_rate": false_count / len(group),
                    "simultaneous_one_sided_95_upper": upper,
                    "passes_5pct_gate": upper <= 0.05,
                    "mean_labels": float(group["labels_queried"].mean()),
                    "mean_processed_events": float(group["events_processed"].mean()),
                }
            )
    return pd.DataFrame(rows)


def _confirmation_result(metrics: pd.DataFrame, *, seed: int) -> dict[str, object]:
    metrics = metrics[metrics["arm"].isin(PRIMARY_ARMS)]
    paired_values: dict[str, list[np.ndarray]] = {
        "detection": [],
        "labels": [],
        "exposure": [],
    }
    dose_results: list[dict[str, object]] = []
    for dose_index, scenario in enumerate(MARKOV_HARM_SCENARIOS):
        group = metrics[metrics["scenario"] == scenario].pivot(index="stream_id", columns="arm")
        detection = group[("post_onset_detection", "delay_12_predictable")].to_numpy(
            dtype=float
        ) - group[("post_onset_detection", "delay_12_fixed")].to_numpy(dtype=float)
        labels = group[("labels_queried", "delay_12_predictable")].to_numpy(dtype=float) - group[
            ("labels_queried", "delay_12_fixed")
        ].to_numpy(dtype=float)
        exposure = group[
            ("evaluator_cumulative_expected_harm_cost", "delay_12_predictable")
        ].to_numpy(dtype=float) - group[
            ("evaluator_cumulative_expected_harm_cost", "delay_12_fixed")
        ].to_numpy(dtype=float)
        paired_values["detection"].append(detection)
        paired_values["labels"].append(labels)
        paired_values["exposure"].append(exposure)
        dose_results.append(
            {
                "scenario": scenario,
                "effect": float(HARM_EFFECTS[dose_index]),
                "fixed_detection": float(group[("post_onset_detection", "delay_12_fixed")].mean()),
                "predictable_detection": float(
                    group[("post_onset_detection", "delay_12_predictable")].mean()
                ),
                "paired_detection_difference": float(detection.mean()),
                "fixed_mean_labels": float(group[("labels_queried", "delay_12_fixed")].mean()),
                "predictable_mean_labels": float(
                    group[("labels_queried", "delay_12_predictable")].mean()
                ),
                "paired_label_difference": float(labels.mean()),
                "fixed_mean_expected_exposure": float(
                    group[("evaluator_cumulative_expected_harm_cost", "delay_12_fixed")].mean()
                ),
                "predictable_mean_expected_exposure": float(
                    group[
                        ("evaluator_cumulative_expected_harm_cost", "delay_12_predictable")
                    ].mean()
                ),
                "paired_expected_exposure_difference": float(exposure.mean()),
                "predictable_pre_onset_alarms": int(
                    metrics.loc[
                        (metrics["scenario"] == scenario)
                        & (metrics["arm"] == "delay_12_predictable"),
                        "false_escalation",
                    ].sum()
                ),
            }
        )

    macro = {key: np.stack(value, axis=1).mean(axis=1) for key, value in paired_values.items()}
    detection_ci = paired_bootstrap_interval(macro["detection"], seed=seed + 81001)
    label_ci = paired_bootstrap_interval(macro["labels"], seed=seed + 81002)
    exposure_ci = paired_bootstrap_interval(macro["exposure"], seed=seed + 81003)
    return {
        "primary_estimand": "equal-weight mean over four Markov harm doses of paired post-onset detection difference, predictable minus fixed, 12-event delay",
        "paired_mean_detection_difference": float(macro["detection"].mean()),
        "paired_bootstrap_95_ci_detection": list(detection_ci),
        "detection_gate_lower_bound": 0.02,
        "passes_detection_gate": bool(detection_ci[0] > 0.02),
        "paired_mean_label_difference": float(macro["labels"].mean()),
        "paired_bootstrap_95_ci_labels": list(label_ci),
        "passes_no_extra_labels_gate": bool(label_ci[1] <= 0),
        "paired_mean_expected_exposure_difference": float(macro["exposure"].mean()),
        "paired_bootstrap_95_ci_expected_exposure": list(exposure_ci),
        "dose_results": dose_results,
        "bootstrap_replicates": BOOTSTRAP_REPS,
        "bootstrap_seed_root": seed + 81001,
    }


def run_stage(
    *,
    stage: str,
    streams: int,
    seed: int,
    device_name: str,
    output: Path,
    calibration_summary: Path | None = None,
    horizon: int = 2400,
) -> Path:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage}")
    if streams < 30 or horizon < 100:
        raise ValueError("stage requires at least 30 streams and horizon 100")
    expected_seed = STAGES[stage][1]
    if seed != expected_seed:
        raise ValueError(f"{stage} seed root is frozen at {expected_seed}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if stage == "confirmation":
        if calibration_summary is None or not calibration_summary.is_file():
            raise ValueError("confirmation requires the Stage 1 calibration CSV")
        calibration = pd.read_csv(calibration_summary)
        if len(calibration) != 4 or not calibration["passes_5pct_gate"].all():
            raise RuntimeError("fresh Stage 1 null calibration did not pass all four cells")

    verify_dgp_algebra()
    device = torch.device(device_name)
    started = time.monotonic()
    rows = _run_cells(stage=stage, streams=streams, seed=seed, device=device, horizon=horizon)
    metrics = pd.DataFrame(rows)
    scenarios, _ = STAGES[stage]
    expected_rows = streams * len(scenarios) * len(PRIMARY_ARMS)
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("incomplete or duplicated scenario/arm/stream rows")
    if not metrics["budget_respected"].all():
        raise RuntimeError("hard label cap was violated")
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    parquet_path = metrics_dir / "stream_metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    summary = (
        metrics.groupby(["scenario", "arm"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            false_escalation_rate=("false_escalation", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            post_onset_detection=("post_onset_detection", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events_processed=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    summary_path = metrics_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)
    result_path: Path
    if stage == "calibration":
        result = _calibration_table(metrics)
        result_path = metrics_dir / "calibration.csv"
        result.to_csv(result_path, index=False)
        passed = bool(result["passes_5pct_gate"].all())
        report_text = [
            "# Delayed Markov null calibration",
            "",
            f"- Streams per cell: {streams}; delay: {DELAY}; horizon: {horizon}; labels capped at {math.floor(BUDGET_RATE * horizon)}.",
            f"- Device: {device}; generation uses PyTorch; event-prefix monitor replay uses CPU NumPy.",
            "- Family: two nonpositive-mean controls crossed with two monitor systems (four cells); exact one-sided Clopper-Pearson bounds use Bonferroni per-cell alpha 0.0125.",
            f"- Calibration gate: {'PASS' if passed else 'FAIL'}; all simultaneous upper limits must be at most 5%.",
            "- Monte Carlo calibration is specific to the registered two-state Markov DGP and implementation; the supermartingale argument supplies the stated mathematical guarantee under its assumptions.",
            "- No figure was generated; this calibration is reported as a numeric table and Parquet stream file.",
            "",
            result.to_markdown(index=False, floatfmt=".5f"),
        ]
    else:
        result = _confirmation_result(metrics, seed=seed)
        calibration = pd.read_csv(calibration_summary)  # type: ignore[arg-type]
        result["passes_calibration_gate"] = bool(calibration["passes_5pct_gate"].all())
        result["retention_rule_passes"] = bool(
            result["passes_detection_gate"]
            and result["passes_no_extra_labels_gate"]
            and result["passes_calibration_gate"]
        )
        result["independent_calibration_summary"] = str(calibration_summary)
        result["independent_calibration_sha256"] = sha256(calibration_summary)  # type: ignore[arg-type]
        result_path = reports_dir / "primary_result.json"
        report_text = [
            "# Delayed Markov harm confirmation",
            "",
            f"- Streams per harm dose and arm: {streams}; delay: {DELAY}; horizon: {horizon}; device: {device}.",
            f"- Independent null calibration gate: {'PASS' if result['passes_calibration_gate'] else 'FAIL'}.",
            f"- Frozen retention rule: {'PASS' if result['retention_rule_passes'] else 'FAIL'}.",
            "- This is confirmation only for the frozen Markov-volatility process and deterministic outcome-independent 12-event feedback delay.",
            "- Evaluator expected exposure conditions on latent state and assumes mitigation at escalation; it is not observed prevented loss.",
            "- No figure was generated; this confirmation is reported as a numeric table and Parquet stream file.",
            "",
            "## Primary result",
            "",
            "```json",
            json.dumps(
                {key: value for key, value in result.items() if key != "dose_results"}, indent=2
            ),
            "```",
            "",
            "## Dose results",
            "",
            pd.DataFrame(result["dose_results"]).to_markdown(index=False, floatfmt=".5f"),
            "",
        ]
    if stage == "calibration":
        report_path = reports_dir / "calibration_results.md"
        report_path.write_text("\n".join(report_text) + "\n", encoding="utf-8")
    else:
        report_path = reports_dir / "confirmation_results.md"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        report_path.write_text("\n".join(report_text) + "\n", encoding="utf-8")

    source_paths = [
        Path(__file__),
        Path("scripts/validate_delayed_history_predictable_bounds.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("docs/delayed_markov_bound_development_protocol.md"),
        Path("docs/delayed_markov_bound_confirmation_protocol.md"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    artifacts = [parquet_path, summary_path, result_path, report_path]
    if stage == "confirmation" and calibration_summary is not None:
        artifacts.append(calibration_summary)
    manifest = {
        "experiment": f"delayed_markov_predictable_{stage}",
        "status": "frozen_calibration" if stage == "calibration" else "disjoint_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "seed_root": seed,
        "streams_per_scenario_arm": streams,
        "horizon": horizon,
        "delay": DELAY,
        "q_min": Q_MIN,
        "budget_rate": BUDGET_RATE,
        "scenarios": list(STAGES[stage][0]),
        "arms": list(PRIMARY_ARMS),
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "runtime_seconds": time.monotonic() - started,
        "rows": len(metrics),
        "source_sha256": {str(path): sha256(path) for path in source_paths},
        "artifact_sha256": {
            str(path.relative_to(output)) if path.is_relative_to(output) else str(path): sha256(
                path
            )
            for path in artifacts
        },
        "limitations": [
            "two-state Markov-volatility process only",
            "event-time full-history conditional-mean null required",
            "fixed 12-event outcome-independent complete label delay",
            "frozen action pair and independent source proxy",
            "event-order prefix alarms; delay is not evidence",
            "standard predictable bounded-factor method; no novelty claim",
        ],
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=tuple(STAGES), required=True)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--horizon", type=int, default=2400)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--calibration-summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else STAGES[args.stage][1]
    print(
        run_stage(
            stage=args.stage,
            streams=args.streams,
            seed=seed,
            device_name=args.device,
            output=args.output,
            calibration_summary=args.calibration_summary,
            horizon=args.horizon,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
