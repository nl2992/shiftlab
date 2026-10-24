"""Run frozen null calibration and harm confirmation for the matched-path ablation."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

try:
    from scripts.confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from scripts.run_matched_path_bound_ablation import (
        BOUND_MODES,
        DELAY,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        SCHEDULES,
        build_schedule,
        simulate_arm,
    )
    from scripts.validate_markov_predictable_query_bounds import (
        HARM_EFFECTS,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from confirm_history_predictable_query_bounds import (
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
    from run_matched_path_bound_ablation import (
        BOUND_MODES,
        DELAY,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        SCHEDULES,
        build_schedule,
        simulate_arm,
    )
    from validate_markov_predictable_query_bounds import (
        HARM_EFFECTS,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

CALIBRATION_SEED = 28504027
CONFIRMATION_SEED = 28604027
STAGES = {
    "calibration": ((MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO), CALIBRATION_SEED),
    "confirmation": (MARKOV_HARM_SCENARIOS, CONFIRMATION_SEED),
}
SELECTED_SCHEDULE = SCHEDULES[-1]
BOOTSTRAP_REPLICATES = 10_000
DEFAULT_HORIZON = 2400


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


def run_cells(*, stage: str, streams: int, seed: int, horizon: int, device: torch.device):
    scenarios, _ = STAGES[stage]
    data = generate_markov_dependent_data(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    data["seed"] = seed
    schedule_name, low, high, slots = SELECTED_SCHEDULE
    propensity = build_schedule(
        name=schedule_name,
        low=low,
        high=high,
        high_slots=slots,
        horizon=horizon,
        streams=streams,
    )
    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        for bound_mode in BOUND_MODES:
            arm_rows = simulate_arm(
                scenario=scenario,
                schedule_name=schedule_name,
                propensity=propensity,
                data=data,
                bound_mode=bound_mode,
            )
            for row in arm_rows:
                row["stream_seed_id"] = seed + int(row["stream_id"])
                row["device_generation"] = str(device)
            rows.extend(arm_rows)
    return rows


def calibration_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    scenarios = STAGES["calibration"][0]
    family_size = len(scenarios) * len(BOUND_MODES)
    per_cell_alpha = 0.05 / family_size
    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        for mode in BOUND_MODES:
            group = metrics[(metrics["scenario"] == scenario) & (metrics["bound_mode"] == mode)]
            if group.empty:
                raise RuntimeError(f"missing calibration cell {scenario}/{mode}")
            alarms = int(group["false_escalation"].sum())
            upper = exact_one_sided_upper(alarms, len(group), per_cell_alpha)
            rows.append(
                {
                    "scenario": scenario,
                    "bound_mode": mode,
                    "streams": len(group),
                    "false_escalations": alarms,
                    "false_escalation_rate": alarms / len(group),
                    "simultaneous_one_sided_95_upper": upper,
                    "passes_5pct_gate": upper <= 0.05,
                    "mean_labels": float(group["labels_queried"].mean()),
                    "mean_events_processed": float(group["events_processed"].mean()),
                }
            )
    return pd.DataFrame(rows)


def confirmation_result(metrics: pd.DataFrame, *, seed: int) -> dict[str, object]:
    per_dose: list[dict[str, object]] = []
    detection_by_dose: list[np.ndarray] = []
    labels_by_dose: list[np.ndarray] = []
    exposure_by_dose: list[np.ndarray] = []
    for dose_index, scenario in enumerate(MARKOV_HARM_SCENARIOS):
        wide = metrics[metrics["scenario"] == scenario].pivot(
            index="stream_id", columns="bound_mode"
        )
        detection = wide[("post_onset_detection", "eventwise")].to_numpy(dtype=float) - wide[
            ("post_onset_detection", "fixed")
        ].to_numpy(dtype=float)
        labels = wide[("labels_queried", "eventwise")].to_numpy(dtype=float) - wide[
            ("labels_queried", "fixed")
        ].to_numpy(dtype=float)
        exposure = wide[("evaluator_cumulative_expected_harm_cost", "eventwise")].to_numpy(
            dtype=float
        ) - wide[("evaluator_cumulative_expected_harm_cost", "fixed")].to_numpy(dtype=float)
        detection_by_dose.append(detection)
        labels_by_dose.append(labels)
        exposure_by_dose.append(exposure)
        per_dose.append(
            {
                "scenario": scenario,
                "effect": float(HARM_EFFECTS[dose_index]),
                "fixed_detection": float(wide[("post_onset_detection", "fixed")].mean()),
                "eventwise_detection": float(wide[("post_onset_detection", "eventwise")].mean()),
                "paired_detection_difference": float(detection.mean()),
                "fixed_mean_labels": float(wide[("labels_queried", "fixed")].mean()),
                "eventwise_mean_labels": float(wide[("labels_queried", "eventwise")].mean()),
                "paired_label_difference": float(labels.mean()),
                "fixed_mean_expected_exposure": float(
                    wide[("evaluator_cumulative_expected_harm_cost", "fixed")].mean()
                ),
                "eventwise_mean_expected_exposure": float(
                    wide[("evaluator_cumulative_expected_harm_cost", "eventwise")].mean()
                ),
                "paired_expected_exposure_difference": float(exposure.mean()),
                "eventwise_pre_onset_alarms": int(
                    metrics.loc[
                        (metrics["scenario"] == scenario) & (metrics["bound_mode"] == "eventwise"),
                        "false_escalation",
                    ].sum()
                ),
            }
        )
    macro = {
        "detection": np.stack(detection_by_dose, axis=1).mean(axis=1),
        "labels": np.stack(labels_by_dose, axis=1).mean(axis=1),
        "exposure": np.stack(exposure_by_dose, axis=1).mean(axis=1),
    }
    detection_ci = paired_bootstrap_interval(macro["detection"], seed=seed + 99001)
    label_ci = paired_bootstrap_interval(macro["labels"], seed=seed + 99002)
    exposure_ci = paired_bootstrap_interval(macro["exposure"], seed=seed + 99003)
    return {
        "primary_estimand": "equal-weight macro over four doses of paired eventwise-minus-fixed post-onset detection under the frozen periodic q={0.05,0.80} schedule",
        "paired_mean_detection_difference": float(macro["detection"].mean()),
        "paired_bootstrap_95_ci_detection": list(detection_ci),
        "detection_gate_lower_bound": 0.02,
        "passes_detection_gate": bool(detection_ci[0] > 0.02),
        "paired_mean_label_difference": float(macro["labels"].mean()),
        "paired_bootstrap_95_ci_labels": list(label_ci),
        "passes_no_extra_labels_gate": bool(label_ci[1] <= 0),
        "paired_mean_expected_exposure_difference": float(macro["exposure"].mean()),
        "paired_bootstrap_95_ci_expected_exposure": list(exposure_ci),
        "dose_results": per_dose,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed_root": seed + 99001,
    }


def run_stage(
    *,
    stage: str,
    streams: int,
    seed: int,
    horizon: int,
    device_name: str,
    output: Path,
    calibration_path: Path | None = None,
) -> Path:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage}")
    if streams < 30 or horizon < 100:
        raise ValueError("validation stage requires at least 30 streams and horizon 100")
    if seed != STAGES[stage][1]:
        raise ValueError(f"{stage} seed root is frozen at {STAGES[stage][1]}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if stage == "confirmation":
        if calibration_path is None or not calibration_path.is_file():
            raise ValueError("confirmation requires the independent calibration CSV")
        cal = pd.read_csv(calibration_path)
        if len(cal) != 4 or not cal["passes_5pct_gate"].all():
            raise RuntimeError("calibration did not pass all four simultaneous limits")

    verify_dgp_algebra()
    device = torch.device(device_name)
    started = time.monotonic()
    rows = run_cells(stage=stage, streams=streams, seed=seed, horizon=horizon, device=device)
    metrics = pd.DataFrame(rows)
    expected = streams * len(STAGES[stage][0]) * len(BOUND_MODES)
    if (
        len(metrics) != expected
        or metrics.duplicated(["scenario", "schedule", "bound_mode", "stream_id"]).any()
    ):
        raise RuntimeError("missing or duplicated validation rows")
    if not metrics["budget_respected"].all() or metrics["bound_violations"].sum() != 0:
        raise RuntimeError("budget or support invariant failed")
    paths = metrics.pivot(
        index=["scenario", "stream_id"],
        columns="bound_mode",
        values=["labels_queried", "events_processed", "registered_events"],
    )
    for metric in ("labels_queried", "events_processed", "registered_events"):
        if not np.array_equal(paths[(metric, "fixed")], paths[(metric, "eventwise")]):
            raise RuntimeError(f"bound arms do not share identical {metric}")
    if stage == "confirmation" and not metrics["onset_reached"].fillna(False).all():
        raise RuntimeError("at least one harm stream failed to reach onset")

    output.mkdir(parents=True, exist_ok=True)
    metric_dir, report_dir = output / "metrics", output / "reports"
    metric_dir.mkdir()
    report_dir.mkdir()
    parquet_path = metric_dir / "stream_metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    summary = (
        metrics.groupby(["scenario", "bound_mode"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            false_escalation_rate=("false_escalation", "mean"),
            detection_rate=("post_onset_detection", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events_processed=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    summary_path = metric_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)

    if stage == "calibration":
        result = calibration_summary(metrics)
        result_path = metric_dir / "calibration.csv"
        result.to_csv(result_path, index=False)
        passed = bool(result["passes_5pct_gate"].all())
        report_lines = [
            "# Matched-path selected-schedule null calibration",
            "",
            f"- Streams per cell: {streams}; selected schedule: `periodic_q080`; delay: {DELAY}; horizon: {horizon}.",
            f"- Requested/resolved data-generation device: {device_name}/{device}; replay device: CPU NumPy.",
            "- Calibration family: two nonpositive-mean controls crossed with fixed/eventwise bounds; four exact one-sided limits use Bonferroni alpha 0.0125 per cell.",
            f"- Gate: {'PASS' if passed else 'FAIL'}; every simultaneous upper limit must be at most 5%.",
            "- Constant-q identity was verified in the preceding development block; this calibration tests only the selected variable-q schedule.",
            "- No figure was generated; numerical tables and Parquet metrics are the prespecified outputs.",
            "",
            result.to_markdown(index=False, floatfmt=".5f"),
        ]
        report_path = report_dir / "calibration_results.md"
        report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        result_payload: dict[str, object] = {"calibration_gate_passes": passed}
    else:
        result_payload = confirmation_result(metrics, seed=seed)
        calibration = pd.read_csv(calibration_path)  # type: ignore[arg-type]
        result_payload["passes_calibration_gate"] = bool(calibration["passes_5pct_gate"].all())
        result_payload["retention_rule_passes"] = bool(
            result_payload["passes_detection_gate"]
            and result_payload["passes_no_extra_labels_gate"]
            and result_payload["passes_calibration_gate"]
        )
        result_payload["independent_calibration_sha256"] = sha256(calibration_path)  # type: ignore[arg-type]
        result_payload["independent_calibration_path"] = str(calibration_path)
        result_path = report_dir / "primary_result.json"
        result_path.write_text(
            json.dumps(result_payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        report_lines = [
            "# Matched-path selected-schedule harm confirmation",
            "",
            f"- Streams per dose and bound: {streams}; schedule: `periodic_q080`; delay: {DELAY}; horizon: {horizon}; device: {device}.",
            f"- Independent null calibration: {'PASS' if result_payload['passes_calibration_gate'] else 'FAIL'}.",
            f"- Frozen retention rule: {'PASS' if result_payload['retention_rule_passes'] else 'FAIL'}.",
            "- Fixed/eventwise paths were verified identical for labels, registered prefix, and processed events.",
            "- No figure was generated; the prespecified numeric result and stream metrics are provided.",
            "",
            "## Primary result",
            "",
            "```json",
            json.dumps(
                {key: value for key, value in result_payload.items() if key != "dose_results"},
                indent=2,
            ),
            "```",
            "",
            "## Dose results",
            "",
            pd.DataFrame(result_payload["dose_results"]).to_markdown(index=False, floatfmt=".5f"),
        ]
        report_path = report_dir / "confirmation_results.md"
        report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    sources = [
        Path(__file__),
        Path("scripts/run_matched_path_bound_ablation.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("docs/matched_path_bound_ablation_protocol.md"),
        Path("docs/matched_path_bound_confirmation_protocol.md"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    artifacts = [parquet_path, summary_path, result_path, report_path]
    if stage == "confirmation" and calibration_path is not None:
        artifacts.append(calibration_path)
    manifest = {
        "experiment": f"matched_path_bound_{stage}",
        "status": "frozen_calibration" if stage == "calibration" else "disjoint_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "seed_root": seed,
        "streams_per_scenario_arm": streams,
        "horizon": horizon,
        "delay": DELAY,
        "schedule": {
            "name": SELECTED_SCHEDULE[0],
            "q_low": 0.05,
            "q_high": 0.80,
            "high_slots_per_10": 2,
        },
        "bound_modes": list(BOUND_MODES),
        "scenarios": list(STAGES[stage][0]),
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "runtime_seconds": time.monotonic() - started,
        "rows": len(metrics),
        "source_sha256": {str(path): sha256(path) for path in sources},
        "artifact_sha256": {
            str(path.relative_to(output)) if path.is_relative_to(output) else str(path): sha256(
                path
            )
            for path in artifacts
        },
        "path_identity": "fixed/eventwise arms share queried labels, registered events, and processed prefix",
        "limitations": [
            "two-state Markov-volatility DGP only",
            "fixed outcome-independent complete 12-event label delay",
            "event-time full-history conditional-mean null required",
            "frozen action pair and source proxy",
            "standard predictable bounded-factor e-process; no novelty claim",
        ],
    }
    (report_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=tuple(STAGES), required=True)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
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
            horizon=args.horizon,
            device_name=args.device,
            calibration_path=args.calibration_summary,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
