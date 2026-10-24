"""Run the independent confirmation of history-predictable query bounds."""

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
from scipy.stats import beta

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        HARM_EFFECTS,
        HARM_SCENARIOS,
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
        simulate_arm,
    )
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        HARM_EFFECTS,
        HARM_SCENARIOS,
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
        simulate_arm,
    )

DEFAULT_SEED = 27104027
DEFAULT_STREAMS = 4000
HORIZON = 2400
Q_MIN = 0.05
ARMS = (
    ("uniform", 0.20, "fixed"),
    ("evidence_directed", Q_MIN, "fixed"),
    ("evidence_directed", Q_MIN, "predictable"),
)
NULLS = (NULL_SCENARIO, STRICT_NEGATIVE_SCENARIO)
SCENARIOS = (*NULLS, *HARM_SCENARIOS)
BOOTSTRAP_REPS = 10_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_one_sided_upper(successes: int, total: int, alpha: float) -> float:
    """Clopper-Pearson upper limit for a Bernoulli rate."""
    if total <= 0:
        raise ValueError("total must be positive")
    if successes == total:
        return 1.0
    return float(beta.ppf(1 - alpha, successes + 1, total - successes))


def paired_bootstrap_interval(
    values: np.ndarray, *, seed: int, confidence: float = 0.95
) -> tuple[float, float]:
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(
            "paired bootstrap requires a one-dimensional sample of at least two streams"
        )
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_REPS, dtype=np.float64)
    batch_size = 128
    for start in range(0, BOOTSTRAP_REPS, batch_size):
        stop = min(start + batch_size, BOOTSTRAP_REPS)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        draws[start:stop] = values[indices].mean(axis=1)
    tail = (1 - confidence) / 2
    low, high = np.quantile(draws, [tail, 1 - tail])
    return float(low), float(high)


def build_dose_results(metrics: pd.DataFrame, *, seed: int) -> pd.DataFrame:
    evidence = metrics[
        metrics["arm"].isin(["evidence_qmin_0.05_fixed", "evidence_qmin_0.05_predictable"])
        & metrics["scenario"].isin(HARM_SCENARIOS)
    ]
    dose_rows = []
    for index, (effect, scenario) in enumerate(zip(HARM_EFFECTS, HARM_SCENARIOS, strict=True)):
        group = evidence[evidence["scenario"] == scenario]
        by_arm = group.groupby("arm")[
            [
                "post_onset_detection",
                "false_escalation",
                "labels_queried",
                "events_processed",
                "evaluator_cumulative_expected_harm_cost",
            ]
        ].mean()
        fixed = group[group["arm"] == "evidence_qmin_0.05_fixed"].set_index("stream_id")
        dynamic = group[group["arm"] == "evidence_qmin_0.05_predictable"].set_index("stream_id")
        detection_diff = (
            dynamic["post_onset_detection"].astype(float).to_numpy()
            - fixed["post_onset_detection"].astype(float).to_numpy()
        )
        label_diff = dynamic["labels_queried"].to_numpy(dtype=float) - fixed[
            "labels_queried"
        ].to_numpy(dtype=float)
        exposure_diff = dynamic["evaluator_cumulative_expected_harm_cost"].to_numpy(
            dtype=float
        ) - fixed["evaluator_cumulative_expected_harm_cost"].to_numpy(dtype=float)
        bootstrap_seed = seed + 71_100 + index
        detection_ci = paired_bootstrap_interval(detection_diff, seed=bootstrap_seed)
        label_ci = paired_bootstrap_interval(label_diff, seed=bootstrap_seed)
        exposure_ci = paired_bootstrap_interval(exposure_diff, seed=bootstrap_seed)
        dose_rows.append(
            {
                "scenario": scenario,
                "harm_effect": effect,
                "fixed_detection_rate": float(
                    by_arm.loc["evidence_qmin_0.05_fixed", "post_onset_detection"]
                ),
                "predictable_detection_rate": float(
                    by_arm.loc["evidence_qmin_0.05_predictable", "post_onset_detection"]
                ),
                "paired_detection_difference": float(detection_diff.mean()),
                "paired_detection_ci95_low": detection_ci[0],
                "paired_detection_ci95_high": detection_ci[1],
                "fixed_pre_onset_escalation_rate": float(
                    by_arm.loc["evidence_qmin_0.05_fixed", "false_escalation"]
                ),
                "predictable_pre_onset_escalation_rate": float(
                    by_arm.loc["evidence_qmin_0.05_predictable", "false_escalation"]
                ),
                "paired_label_difference": float(label_diff.mean()),
                "paired_label_ci95_low": label_ci[0],
                "paired_label_ci95_high": label_ci[1],
                "paired_exposure_cost_difference": float(exposure_diff.mean()),
                "paired_exposure_cost_ci95_low": exposure_ci[0],
                "paired_exposure_cost_ci95_high": exposure_ci[1],
            }
        )
    return pd.DataFrame(dose_rows)


def reanalyze_existing(output: Path) -> Path:
    """Recompute dose-level bootstrap intervals from checksum-verified stream rows."""
    reports_dir = output / "reports"
    metrics_dir = output / "metrics"
    manifest_path = reports_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics_path = metrics_dir / "stream_metrics.parquet"
    expected_hash = manifest["artifact_sha256"]["metrics\\stream_metrics.parquet"]
    if sha256(metrics_path) != expected_hash:
        raise ValueError("stream metrics checksum differs from the registered manifest")
    metrics = pd.read_parquet(metrics_path)
    seed = int(manifest["configuration"]["seed_root"])
    dose = build_dose_results(metrics, seed=seed)
    dose_path = metrics_dir / "harm_dose_results.csv"
    dose.to_csv(dose_path, index=False)

    report_path = reports_dir / "confirmation_results.md"
    report = report_path.read_text(encoding="utf-8")
    begin_marker = "## Harm dose response\n\n"
    end_marker = "\n\n## Primary result"
    begin = report.index(begin_marker) + len(begin_marker)
    end = report.index(end_marker, begin)
    dose_section = (
        dose.to_markdown(index=False, floatfmt=".4f")
        + "\n\nDose-level paired 95% bootstrap intervals are descriptive secondary analyses and are not adjusted across doses."
    )
    report = report[:begin] + dose_section + report[end:]
    report_path.write_text(report, encoding="utf-8")

    source_path = Path("scripts/confirm_history_predictable_query_bounds.py")
    manifest["analysis_recomputed_without_regenerating_streams"] = True
    manifest["git_commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    manifest["source_sha256"][str(source_path)] = sha256(source_path)
    manifest["artifact_sha256"]["metrics\\harm_dose_results.csv"] = sha256(dose_path)
    manifest["artifact_sha256"]["reports\\confirmation_results.md"] = sha256(report_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def run_confirmation(*, streams: int, seed: int, device_name: str, output: Path) -> Path:
    if streams < 100:
        raise ValueError("confirmation requires at least 100 paired streams")
    if seed < DEFAULT_SEED:
        raise ValueError(f"confirmation seeds must start at {DEFAULT_SEED} or later")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")

    device = torch.device(device_name)
    data = generate_common_random_numbers(
        streams=streams, horizon=HORIZON, seed=seed, device=device
    )
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for query_policy, q_min, bound_mode in ARMS:
            rows.extend(
                simulate_arm(
                    scenario=scenario,
                    streams=streams,
                    horizon=HORIZON,
                    seed=seed,
                    data=data,
                    device=device,
                    query_policy=query_policy,
                    q_min=q_min,
                    bound_mode=bound_mode,
                )
            )

    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(SCENARIOS) * len(ARMS)
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} stream-arm rows, got {len(metrics)}")
    if metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("duplicate scenario-arm-stream rows")
    if not metrics["budget_respected"].all():
        raise RuntimeError("hard label budget violated")

    alpha_family = 0.05
    calibration_cells = len(NULLS) * len(ARMS)
    alpha_cell = alpha_family / calibration_cells
    calibration_rows = []
    for scenario in NULLS:
        for arm, group in metrics[metrics["scenario"] == scenario].groupby("arm", sort=True):
            count = int(group["false_escalation"].sum())
            calibration_rows.append(
                {
                    "scenario": scenario,
                    "arm": arm,
                    "streams": len(group),
                    "false_escalations": count,
                    "false_rate": count / len(group),
                    "simultaneous_one_sided_95_upper": exact_one_sided_upper(
                        count, len(group), alpha_cell
                    ),
                    "per_cell_alpha": alpha_cell,
                    "passes_5pct_upper_limit": exact_one_sided_upper(count, len(group), alpha_cell)
                    <= 0.05,
                    "mean_labels": float(group["labels_queried"].mean()),
                    "mean_events_processed": float(group["events_processed"].mean()),
                }
            )
    calibration = pd.DataFrame(calibration_rows)

    evidence = metrics[
        metrics["arm"].isin(["evidence_qmin_0.05_fixed", "evidence_qmin_0.05_predictable"])
        & metrics["scenario"].isin(HARM_SCENARIOS)
    ]
    dose = build_dose_results(metrics, seed=seed)
    per_stream = evidence.pivot(
        index="stream_id",
        columns=["scenario", "arm"],
        values=[
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    detection_diffs = []
    label_diffs = []
    exposure_diffs = []
    for scenario in HARM_SCENARIOS:
        detection_diffs.append(
            per_stream[
                ("post_onset_detection", scenario, "evidence_qmin_0.05_predictable")
            ].to_numpy(dtype=float)
            - per_stream[("post_onset_detection", scenario, "evidence_qmin_0.05_fixed")].to_numpy(
                dtype=float
            )
        )
        label_diffs.append(
            per_stream[("labels_queried", scenario, "evidence_qmin_0.05_predictable")].to_numpy(
                dtype=float
            )
            - per_stream[("labels_queried", scenario, "evidence_qmin_0.05_fixed")].to_numpy(
                dtype=float
            )
        )
        exposure_diffs.append(
            per_stream[
                (
                    "evaluator_cumulative_expected_harm_cost",
                    scenario,
                    "evidence_qmin_0.05_predictable",
                )
            ].to_numpy(dtype=float)
            - per_stream[
                ("evaluator_cumulative_expected_harm_cost", scenario, "evidence_qmin_0.05_fixed")
            ].to_numpy(dtype=float)
        )
    macro_detection = np.mean(np.stack(detection_diffs, axis=1), axis=1)
    macro_labels = np.mean(np.stack(label_diffs, axis=1), axis=1)
    macro_exposure = np.mean(np.stack(exposure_diffs, axis=1), axis=1)
    detection_ci = paired_bootstrap_interval(macro_detection, seed=seed + 70001)
    label_ci = paired_bootstrap_interval(macro_labels, seed=seed + 70002)
    exposure_ci = paired_bootstrap_interval(macro_exposure, seed=seed + 70003)
    primary = {
        "estimand": "equal-weight mean post-onset detection difference across delta=0.04,0.20,0.40,0.60; predictable minus fixed bound; paired by stream ID",
        "paired_mean_detection_difference": float(macro_detection.mean()),
        "paired_bootstrap_95_ci": list(detection_ci),
        "retention_practical_margin": 0.02,
        "passes_primary_detection_rule": bool(detection_ci[0] > 0.02),
        "paired_mean_label_difference": float(macro_labels.mean()),
        "paired_bootstrap_95_ci_labels": list(label_ci),
        "passes_no_extra_labels_rule": bool(label_ci[1] <= 0),
        "paired_mean_evaluator_exposure_cost_difference": float(macro_exposure.mean()),
        "paired_bootstrap_95_ci_evaluator_exposure_cost": list(exposure_ci),
        "passes_all_calibration_cells": bool(calibration["passes_5pct_upper_limit"].all()),
        "overall_retention_rule_passes": bool(
            detection_ci[0] > 0.02
            and label_ci[1] <= 0
            and calibration["passes_5pct_upper_limit"].all()
        ),
    }

    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    metrics_path = metrics_dir / "stream_metrics.parquet"
    calibration_path = metrics_dir / "null_calibration.csv"
    dose_path = metrics_dir / "harm_dose_results.csv"
    primary_path = reports_dir / "primary_result.json"
    report_path = reports_dir / "confirmation_results.md"
    metrics.to_parquet(metrics_path, index=False)
    calibration.to_csv(calibration_path, index=False)
    dose.to_csv(dose_path, index=False)
    primary_path.write_text(json.dumps(primary, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Independent confirmation: history-predictable query bound",
        "",
        f"This registered CUDA/CPU confirmation used {streams:,} paired streams per scenario, a {HORIZON}-event horizon, alpha 0.05, and a 20% hard label cap. The seed block begins at {seed} and is disjoint from the development block ending at 27104026.",
        "",
        "The sole primary harm estimand is the stream-paired, equal-weight mean detection-rate difference for the four registered doses (delta 0.04, 0.20, 0.40, 0.60), comparing q_min=0.05 history-predictable against q_min=0.05 fixed-bound evidence-directed querying. Retention requires the two-sided 95% paired-bootstrap lower limit to exceed +2 percentage points, the two-sided 95% upper limit for the label-count difference to be no greater than zero, and every simultaneous calibration upper limit below 5%.",
        "",
        f"The exact one-sided null limits use Bonferroni alpha 0.05/{calibration_cells} across the two nonpositive-mean controls and three arms. A strict negative control has an expected paired-cost contrast of -0.20 starting at zero-based event index 1200. These Monte Carlo limits check this simulator and implementation; the mathematical guarantee still depends on the stated conditional-mean null and predictable q.",
        "",
        "## Calibration",
        "",
        calibration.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Harm dose response",
        "",
        dose.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Dose-level paired 95% bootstrap intervals are descriptive secondary analyses and are not adjusted across doses.",
        "",
        "## Primary result",
        "",
        f"- Equal-weight paired detection difference: {primary['paired_mean_detection_difference']:.4f} (95% paired-bootstrap CI {detection_ci}).",
        f"- Paired label difference: {primary['paired_mean_label_difference']:.2f} (95% paired-bootstrap CI {label_ci}).",
        f"- Paired evaluator exposure-cost difference: {primary['paired_mean_evaluator_exposure_cost_difference']:.2f} (95% paired-bootstrap CI {exposure_ci}).",
        f"- Calibration gate: {primary['passes_all_calibration_cells']}; overall retention rule: {primary['overall_retention_rule_passes']}.",
        "",
        "Evaluator exposure assumes the system mitigates immediately after escalation. It is a synthetic expected-cost accounting quantity, not observed real-world harm prevented. Dose-specific comparisons are secondary and should not be used to override a failed primary result.",
        "",
        "This confirmation tests only independent synthetic events, immediate randomized label feedback, a frozen current/reference action pair, and a history-only propensity. It does not validate serial dependence, delayed or informative feedback, policy adaptation, repeated-candidate selection, or interventions that alter outcomes. A passing result would support this registered benchmark only and would not establish novelty or universal superiority.",
        "",
        "No figure was generated: PaperBanana was unavailable in this environment, and project guidance requires it for research visuals.",
        "",
        "Reproduce with:",
        "",
        "```powershell",
        f"uv run python scripts/confirm_history_predictable_query_bounds.py --streams {streams} --seed {seed} --device {device_name} --output {output.as_posix()}",
        "```",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    source_paths = [
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("src/shiftlab/dive/eprocess.py"),
        Path("src/shiftlab/dive/estimators.py"),
        Path("docs/history_predictable_bound_confirmation_protocol.md"),
    ]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    artifacts = [metrics_path, calibration_path, dose_path, primary_path, report_path]
    manifest = {
        "experiment": "independent_history_predictable_query_bound_confirmation",
        "classification": "independent_confirmation",
        "complete": True,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "configuration": {
            "streams_per_scenario": streams,
            "horizon": HORIZON,
            "seed_root": seed,
            "seed_range_inclusive": [seed, seed + streams - 1],
            "device_requested": device_name,
            "device_resolved": str(device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "scenarios": list(SCENARIOS),
            "arms": [f"{policy}:{floor:.2f}:{bound}" for policy, floor, bound in ARMS],
            "primary_harm_effects": list(HARM_EFFECTS),
            "primary_detection_margin": 0.02,
            "calibration_family_cells": calibration_cells,
            "calibration_family_alpha": alpha_family,
            "calibration_per_cell_alpha": alpha_cell,
            "bootstrap_replicates": BOOTSTRAP_REPS,
            "hard_label_budget": int(metrics["hard_label_budget"].max()),
            "oracle_boundary": "truth used only to generate DGP and evaluator-known expected harm; learner receives sampled training data and current context",
        },
        "primary_result": primary,
        "source_sha256": {str(path): sha256(path) for path in source_paths},
        "artifact_sha256": {str(path.relative_to(output)): sha256(path) for path in artifacts},
        "rows": len(metrics),
        "visuals_generated": False,
    }
    (reports_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=DEFAULT_STREAMS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/history_predictable_bound_confirmation")
    )
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        help="recompute dose-level intervals from checksum-verified stream rows without resimulation",
    )
    args = parser.parse_args()
    if args.reanalyze:
        path = reanalyze_existing(args.output)
        print(f"Reanalyzed checksum-verified confirmation metrics without resimulation: {path}")
        return
    path = run_confirmation(
        streams=args.streams, seed=args.seed, device_name=args.device, output=args.output
    )
    print(f"Completed independent confirmation on {args.device}: {path}")


if __name__ == "__main__":
    main()
