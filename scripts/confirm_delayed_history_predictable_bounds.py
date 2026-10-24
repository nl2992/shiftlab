"""Independently confirm the selected delayed history-predictable monitor."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        HARM_SCENARIOS,
        generate_common_random_numbers,
    )
    from scripts.validate_delayed_history_predictable_bounds import simulate_delayed_arm
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        HARM_SCENARIOS,
        generate_common_random_numbers,
    )
    from validate_delayed_history_predictable_bounds import simulate_delayed_arm

SEED_ROOT = 27604027
HORIZON = 2400
DELAY = 12
Q_MIN = 0.05
ALPHA = 0.05
BOOTSTRAP_REPS = 10_000
CALIBRATION_PATH = Path("outputs/delayed_history_predictable_selected_calibration_2000")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paired_bootstrap_interval(values: np.ndarray, *, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_REPS, dtype=np.float64)
    batch_size = 128
    for start in range(0, BOOTSTRAP_REPS, batch_size):
        stop = min(start + batch_size, BOOTSTRAP_REPS)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        draws[start:stop] = values[indices].mean(axis=1)
    return tuple(float(value) for value in np.quantile(draws, [0.025, 0.975]))


def verify_calibration() -> tuple[pd.DataFrame, dict[str, object]]:
    manifest_path = CALIBRATION_PATH / "reports/manifest.json"
    summary_path = CALIBRATION_PATH / "metrics/calibration_summary.csv"
    metrics_path = CALIBRATION_PATH / "metrics/stream_metrics.parquet"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hash = manifest["sha256"]["metrics/calibration_summary.csv"]
    if sha256(summary_path) != expected_hash:
        raise ValueError("selected calibration summary checksum mismatch")
    raw_hash = manifest["sha256"]["metrics/stream_metrics.parquet"]
    if sha256(metrics_path) != raw_hash:
        raise ValueError("selected calibration stream metrics checksum mismatch")
    config = manifest["configuration"]
    if (
        config["calibration_gate_passed"] is not True
        or config["delay"] != DELAY
        or config["q_min"] != Q_MIN
        or config["generation_device"] != "cuda"
    ):
        raise ValueError("selected configuration lacks the required passing calibration")
    return pd.read_csv(summary_path), manifest


def reanalyze_existing(output: Path) -> Path:
    """Add operational latency and false-alarm summaries without rerunning streams."""
    reports = output / "reports"
    metrics_path = output / "metrics/stream_metrics.parquet"
    manifest_path = reports / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(metrics_path) != manifest["sha256"]["metrics/stream_metrics.parquet"]:
        raise ValueError("confirmation metrics checksum differs from its manifest")
    metrics = pd.read_parquet(metrics_path)
    rows = []
    for (scenario, bound_mode), group in metrics.groupby(["scenario", "bound_mode"], sort=True):
        detected = group[group["post_onset_detection"]]
        rows.append(
            {
                "scenario": scenario,
                "bound_mode": bound_mode,
                "streams": len(group),
                "false_escalations_before_onset": int(group["false_escalation"].sum()),
                "onset_reach_rate": float(group["onset_reached"].mean()),
                "detection_rate": float(group["post_onset_detection"].mean()),
                "mean_labels": float(group["labels_queried"].mean()),
                "mean_events_processed": float(group["events_processed"].mean()),
                "mean_event_delay_given_detection": float(
                    detected["detection_delay_event_time"].mean()
                ),
                "mean_wall_delay_given_detection": float(
                    detected["detection_delay_wall_time"].mean()
                ),
            }
        )
    operational = pd.DataFrame(rows)
    operational_path = output / "metrics/operational_characteristics.csv"
    operational.to_csv(operational_path, index=False)
    report_path = reports / "confirmation_results.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "## Primary result\n"
    if "## Operational characteristics\n" not in report:
        section = (
            "## Operational characteristics\n\n"
            + operational.to_markdown(index=False, floatfmt=".4f")
            + "\n\n"
        )
        report = report.replace(marker, section + marker, 1)
    report_path.write_text(report, encoding="utf-8")
    manifest["sha256"]["runner"] = sha256(Path(__file__).resolve())
    manifest["sha256"]["metrics/operational_characteristics.csv"] = sha256(operational_path)
    manifest["sha256"]["reports/confirmation_results.md"] = sha256(report_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def run(*, streams: int, seed: int, device_name: str, output: Path) -> Path:
    if streams < 1000:
        raise ValueError("independent confirmation requires at least 1,000 streams per dose")
    if seed != SEED_ROOT:
        raise ValueError(f"the frozen confirmation seed is {SEED_ROOT}")
    if device_name not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    calibration, calibration_manifest = verify_calibration()
    device = torch.device(device_name)
    rows: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(HARM_SCENARIOS):
        scenario_seed = seed + scenario_index * streams
        common = generate_common_random_numbers(
            streams=streams, horizon=HORIZON, seed=scenario_seed, device=device
        )
        for bound_mode in ("fixed", "predictable"):
            arm_rows = simulate_delayed_arm(
                scenario=scenario,
                streams=streams,
                horizon=HORIZON,
                seed=scenario_seed,
                data=common,
                device=device,
                delay=DELAY,
                bound_mode=bound_mode,
                q_min=Q_MIN,
            )
            rows.extend(arm_rows)
            print(
                f"completed scenario={scenario} arm={bound_mode} streams={len(arm_rows)}",
                flush=True,
            )

    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(HARM_SCENARIOS) * 2
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, got {len(metrics)}")
    if metrics.duplicated(["scenario", "bound_mode", "stream_id"]).any():
        raise RuntimeError("duplicate confirmation stream rows")
    if not metrics["budget_respected"].all():
        raise RuntimeError("a confirmation stream violated the hard request cap")

    paired = metrics.pivot(
        index="stream_id",
        columns=["scenario", "bound_mode"],
        values=[
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    detection_diffs, label_diffs, exposure_diffs = [], [], []
    dose_rows = []
    for dose_index, scenario in enumerate(HARM_SCENARIOS):
        dynamic_detection = paired[("post_onset_detection", scenario, "predictable")].to_numpy(
            dtype=float
        )
        fixed_detection = paired[("post_onset_detection", scenario, "fixed")].to_numpy(dtype=float)
        dynamic_labels = paired[("labels_queried", scenario, "predictable")].to_numpy(dtype=float)
        fixed_labels = paired[("labels_queried", scenario, "fixed")].to_numpy(dtype=float)
        dynamic_exposure = paired[
            ("evaluator_cumulative_expected_harm_cost", scenario, "predictable")
        ].to_numpy(dtype=float)
        fixed_exposure = paired[
            ("evaluator_cumulative_expected_harm_cost", scenario, "fixed")
        ].to_numpy(dtype=float)
        detection_diff = dynamic_detection - fixed_detection
        label_diff = dynamic_labels - fixed_labels
        exposure_diff = dynamic_exposure - fixed_exposure
        detection_diffs.append(detection_diff)
        label_diffs.append(label_diff)
        exposure_diffs.append(exposure_diff)
        dose_rows.append(
            {
                "scenario": scenario,
                "fixed_detection_rate": float(fixed_detection.mean()),
                "predictable_detection_rate": float(dynamic_detection.mean()),
                "paired_detection_difference": float(detection_diff.mean()),
                "paired_detection_ci95": paired_bootstrap_interval(
                    detection_diff, seed=seed + 81_000 + dose_index
                ),
                "fixed_onset_reach_rate": float(
                    metrics[(metrics.scenario == scenario) & (metrics.bound_mode == "fixed")][
                        "onset_reached"
                    ].mean()
                ),
                "predictable_onset_reach_rate": float(
                    metrics[(metrics.scenario == scenario) & (metrics.bound_mode == "predictable")][
                        "onset_reached"
                    ].mean()
                ),
                "paired_label_difference": float(label_diff.mean()),
                "paired_label_ci95": paired_bootstrap_interval(
                    label_diff, seed=seed + 82_000 + dose_index
                ),
                "paired_exposure_difference": float(exposure_diff.mean()),
            }
        )

    macro_detection = np.mean(np.stack(detection_diffs, axis=1), axis=1)
    macro_labels = np.mean(np.stack(label_diffs, axis=1), axis=1)
    macro_exposure = np.mean(np.stack(exposure_diffs, axis=1), axis=1)
    detection_ci = paired_bootstrap_interval(macro_detection, seed=seed + 83_001)
    labels_ci = paired_bootstrap_interval(macro_labels, seed=seed + 83_002)
    exposure_ci = paired_bootstrap_interval(macro_exposure, seed=seed + 83_003)
    primary = {
        "estimand": "equal-weight detection difference across four harm doses; predictable minus fixed bound; paired by stream id",
        "paired_mean_detection_difference": float(macro_detection.mean()),
        "paired_bootstrap_95_ci": detection_ci,
        "passes_detection_gate": bool(detection_ci[0] > 0.02),
        "paired_mean_label_difference": float(macro_labels.mean()),
        "paired_bootstrap_95_ci_labels": labels_ci,
        "passes_no_extra_labels_gate": bool(labels_ci[1] <= 0),
        "paired_mean_evaluator_exposure_difference": float(macro_exposure.mean()),
        "paired_bootstrap_95_ci_evaluator_exposure": exposure_ci,
        "passes_independent_null_calibration": bool(
            calibration["passes_5pct_calibration_gate"].all()
        ),
        "overall_retention_rule_passes": bool(
            detection_ci[0] > 0.02
            and labels_ci[1] <= 0
            and calibration["passes_5pct_calibration_gate"].all()
        ),
    }

    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics").mkdir()
    (output / "reports").mkdir()
    metrics_path = output / "metrics/stream_metrics.parquet"
    dose_path = output / "metrics/harm_dose_results.csv"
    primary_path = output / "reports/primary_result.json"
    report_path = output / "reports/confirmation_results.md"
    metrics.to_parquet(metrics_path, index=False)
    pd.DataFrame(dose_rows).to_csv(dose_path, index=False)
    primary_path.write_text(json.dumps(primary, indent=2, sort_keys=True), encoding="utf-8")
    calibration_path = CALIBRATION_PATH / "metrics/calibration_summary.csv"
    report = [
        "# Delayed history-predictable bound: independent harm confirmation",
        "",
        f"- Streams per harm dose and arm: {streams}; total rows: {len(metrics)}.",
        f"- Horizon: {HORIZON}; delay: {DELAY}; q_min/q_max: {Q_MIN}/0.80; hard label cap: 480.",
        f"- Stream generation device: {device}; sequential monitor replay: CPU NumPy.",
        f"- Fresh confirmation seed root: {seed}; calibration seed root: {calibration_manifest['configuration']['seed_root']}.",
        "- Detection retention rule: lower 95% paired-bootstrap limit for the equal-weight macro gain must exceed +2 percentage points; paired label-difference upper limit must be at most zero; separate null calibration upper limits must all be at most 5%.",
        "- No further tuning was performed on confirmation seeds. The test covers only iid events and deterministic outcome-independent feedback delay.",
        "- No figure was generated because PaperBanana is unavailable in the active environment.",
        "",
        "## Independent calibration",
        "",
        calibration.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Harm dose response",
        "",
        pd.DataFrame(dose_rows).to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Primary result",
        "",
        f"- Paired mean detection difference: {primary['paired_mean_detection_difference']:.4f} (95% CI {detection_ci}).",
        f"- Paired mean label difference: {primary['paired_mean_label_difference']:.2f} (95% CI {labels_ci}).",
        f"- Paired evaluator exposure-cost difference: {primary['paired_mean_evaluator_exposure_difference']:.2f} (95% CI {exposure_ci}).",
        f"- Overall retention rule: {primary['overall_retention_rule_passes']}.",
        "",
        "The evaluator exposure assumes immediate mitigation at the first alarm; it is a synthetic expected-cost accounting metric, not observed harm prevented. A pass supports only this frozen synthetic design and does not establish novelty or general superiority.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "delayed_history_predictable_bound_independent_harm_confirmation",
        "classification": "independent_confirmation",
        "complete": True,
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "configuration": {
            "streams_per_dose_per_arm": streams,
            "horizon": HORIZON,
            "seed_root": seed,
            "scenario_seed_ranges": {
                scenario: [seed + i * streams, seed + (i + 1) * streams - 1]
                for i, scenario in enumerate(HARM_SCENARIOS)
            },
            "delay": DELAY,
            "q_min": Q_MIN,
            "q_max": 0.80,
            "label_budget_rate": 0.20,
            "generation_device": str(device),
            "monitor_backend": "numpy_cpu_event_order",
            "calibration_gate_passed": bool(calibration["passes_5pct_calibration_gate"].all()),
            "overall_retention_rule_passed": primary["overall_retention_rule_passes"],
        },
        "calibration_artifact": {
            "path": str(calibration_path),
            "sha256": sha256(calibration_path),
            "manifest_sha256": sha256(CALIBRATION_PATH / "reports/manifest.json"),
        },
        "rows": len(metrics),
        "sha256": {
            "runner": sha256(Path(__file__).resolve()),
            "simulator": sha256(Path("scripts/validate_delayed_history_predictable_bounds.py")),
            "shared_dgp": sha256(Path("scripts/calibrate_history_predictable_query_bounds.py")),
            "protocol": sha256(Path("docs/delayed_history_predictable_confirmation_protocol.md")),
            "metrics/stream_metrics.parquet": sha256(metrics_path),
            "metrics/harm_dose_results.csv": sha256(dose_path),
            "reports/primary_result.json": sha256(primary_path),
            "reports/confirmation_results.md": sha256(report_path),
        },
        "limitations": [
            "iid event stream",
            "deterministic outcome-independent delay only",
            "fixed action pair and complete queried labels",
            "no serial-dependence or informative-delay claim",
            "no method novelty or general superiority claim",
        ],
    }
    (output / "reports/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=SEED_ROOT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/delayed_history_predictable_confirmation_2000")
    )
    parser.add_argument("--reanalyze", action="store_true")
    args = parser.parse_args()
    if args.reanalyze:
        print(reanalyze_existing(args.output), flush=True)
        return
    print(
        run(
            streams=args.streams,
            seed=args.seed,
            device_name=args.device,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
