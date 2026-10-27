"""Run the frozen EIA retraining policies on the reserved 2026 event period."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

try:
    from scripts.audit_eia_2026_holdout_readiness import (
        ARCHIVE,
        REPORT,
        RESPONDENTS,
        TYPES,
        _eligible_rows,
        _read_selected_series,
    )
    from scripts.evaluate_eia_retraining_frontier import (
        DELAY_HOURS,
        _score_summary,
        _simulate_policy,
    )
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root, to sys.path.
    from audit_eia_2026_holdout_readiness import (
        ARCHIVE,
        REPORT,
        RESPONDENTS,
        TYPES,
        _eligible_rows,
        _read_selected_series,
    )
    from evaluate_eia_retraining_frontier import DELAY_HOURS, _score_summary, _simulate_policy
from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json

PROTOCOL = Path(__file__).resolve().parents[1] / (
    "papers/shiftguard_unified/eia_2026_out_of_time_confirmation_protocol_v1.md"
)
POLICIES = ("frozen", "weekly", "monthly", "error_trigger")
TEST_START = pd.Timestamp("2026-01-01T00:00:00Z").timestamp()
BLOCK_SECONDS = 168 * 3600
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20261026
REPORT_VERSION = "eia_2026_out_of_time_holdout_readiness"


def _split_arrays(series: dict, respondent: str) -> dict[str, tuple[np.ndarray, ...]]:
    rows = _eligible_rows(series, respondent)
    by_type = {kind: series[f"EBA.{respondent}-ALL.{kind}.H"] for kind in TYPES}
    output = {}
    for split in ("train", "calibration", "test"):
        eligible = [row for row in rows if row["split"] == split and row["complete_features"]]
        event_time = np.asarray([row["event_time"] for row in eligible], dtype=np.float64)
        target_time = np.asarray([row["target_time"] for row in eligible], dtype=np.float64)
        x = np.asarray(
            [[by_type[kind][int(event)] for kind in TYPES] for event in event_time],
            dtype=np.float64,
        )
        y = np.asarray([by_type["D"][int(target)] for target in target_time], dtype=np.float64)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError(f"{respondent}/{split} contains nonfinite complete-feature rows")
        if len(event_time) > 1 and np.any(np.diff(event_time) <= 0):
            raise ValueError(f"{respondent}/{split} event times are not strictly increasing")
        if np.any(target_time != event_time + 3600):
            raise ValueError(f"{respondent}/{split} target is not exactly one hour after event")
        output[split] = (x, y, event_time, target_time)
    if (
        not len(output["train"][1])
        or not len(output["calibration"][1])
        or not len(output["test"][1])
    ):
        raise ValueError(f"{respondent} lacks a required chronological split")
    if output["test"][2][0] < TEST_START:
        raise ValueError(f"{respondent} test includes an event before the frozen 2026 boundary")
    return output


def _block_bootstrap_intervals(
    *,
    times: np.ndarray,
    y: np.ndarray,
    predictions: dict[str, np.ndarray],
    domain: str,
    delay: int,
) -> list[dict]:
    block_id = np.floor((times - TEST_START) / BLOCK_SECONDS).astype(np.int64)
    unique_blocks = np.unique(block_id)
    if len(unique_blocks) < 20:
        raise ValueError(f"{domain} has fewer than 20 populated seven-day test blocks")
    block_metrics: dict[str, dict[str, np.ndarray]] = {}
    for policy, prediction in predictions.items():
        error = y - prediction
        mse_sum = np.asarray([np.square(error[block_id == block]).sum() for block in unique_blocks])
        mae_sum = np.asarray([np.abs(error[block_id == block]).sum() for block in unique_blocks])
        count = np.asarray([(block_id == block).sum() for block in unique_blocks], dtype=np.int64)
        block_metrics[policy] = {"mse_sum": mse_sum, "mae_sum": mae_sum, "count": count}

    rng = np.random.default_rng(BOOTSTRAP_SEED + delay + (0 if domain == "CISO" else 10_000))
    selections = rng.integers(0, len(unique_blocks), size=(BOOTSTRAP_DRAWS, len(unique_blocks)))
    result = []
    reference = block_metrics["frozen"]
    for policy in POLICIES:
        if policy == "frozen":
            continue
        candidate = block_metrics[policy]
        denominator = reference["count"][selections].sum(axis=1)
        ref_rmse = np.sqrt(reference["mse_sum"][selections].sum(axis=1) / denominator)
        cand_rmse = np.sqrt(candidate["mse_sum"][selections].sum(axis=1) / denominator)
        ref_mae = reference["mae_sum"][selections].sum(axis=1) / denominator
        cand_mae = candidate["mae_sum"][selections].sum(axis=1) / denominator
        ref_mse = reference["mse_sum"][selections].sum(axis=1) / denominator
        cand_mse = candidate["mse_sum"][selections].sum(axis=1) / denominator
        paired = {
            "delta_rmse": cand_rmse - ref_rmse,
            "delta_mae": cand_mae - ref_mae,
            "delta_mse": cand_mse - ref_mse,
        }
        point = _score_summary(y, predictions[policy])
        reference_point = _score_summary(y, predictions["frozen"])
        for metric, draws in paired.items():
            metric_name = metric.removeprefix("delta_")
            result.append(
                {
                    "domain_id": domain,
                    "delay_hours": delay,
                    "policy": policy,
                    "contrast": f"{policy}-frozen",
                    "metric": metric_name,
                    "point_difference": point[metric_name] - reference_point[metric_name],
                    "ci_2_5": float(np.quantile(draws, 0.025)),
                    "ci_97_5": float(np.quantile(draws, 0.975)),
                    "bootstrap_draws": BOOTSTRAP_DRAWS,
                    "bootstrap_seed": BOOTSTRAP_SEED + delay + (0 if domain == "CISO" else 10_000),
                    "block_hours": 168,
                    "n_populated_blocks": len(unique_blocks),
                    "ci_scope": "descriptive, paired resampling of fixed 168-hour blocks; not multiplicity-adjusted",
                }
            )
    return result


def _monthly_metrics(
    domain: str,
    delay: int,
    times: np.ndarray,
    y: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> list[dict]:
    months = pd.to_datetime(times, unit="s", utc=True).strftime("%Y-%m")
    output = []
    for policy, prediction in predictions.items():
        for month in sorted(set(months)):
            mask = months == month
            output.append(
                {
                    "domain_id": domain,
                    "delay_hours": delay,
                    "policy": policy,
                    "month": month,
                    **_score_summary(y[mask], prediction[mask]),
                }
            )
    return output


def run(output_dir: Path, *, force_cpu: bool = False) -> Path:
    readiness = json.loads(REPORT.read_text(encoding="utf-8"))
    if readiness.get("audit") != REPORT_VERSION:
        raise ValueError("Run the EIA 2026 holdout readiness audit first")
    if readiness.get("raw_rows_or_policy_metrics_persisted") is not False:
        raise ValueError("Readiness audit indicates raw data or scores were persisted")
    if readiness.get("prior_shiftlab_exposure_audit", {}).get(
        "explicit_2026_event_date_matches_in_prior_eia_result_text"
    ):
        raise ValueError("Prior EIA artifacts contain explicit dates in the reserved test period")
    if sha256(ARCHIVE) != readiness.get("source_sha256"):
        raise ValueError("EIA archive changed after the readiness audit")

    series = _read_selected_series(ARCHIVE)
    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    summary: list[dict] = []
    monthly: list[dict] = []
    intervals: list[dict] = []
    split_counts: dict[str, dict[str, int]] = {}
    for domain in RESPONDENTS:
        split = _split_arrays(series, domain)
        train_x, train_y, _, train_target_time = split["train"]
        cal_x, cal_y, cal_event_time, _ = split["calibration"]
        test_x, test_y, test_event_time, test_target_time = split["test"]
        if len(test_event_time) > 1 and np.any(np.diff(test_event_time) <= 0):
            raise ValueError(f"{domain} test chronology contains duplicates or reversals")
        if np.any(test_target_time != test_event_time + 3600):
            raise ValueError(f"{domain} test labels are not next-hour targets")
        split_counts[domain] = {name: len(values[1]) for name, values in split.items()}
        for delay in DELAY_HOURS:
            predictions: dict[str, np.ndarray] = {}
            for policy in POLICIES:
                prediction, details = _simulate_policy(
                    policy=policy,
                    delay_hours=delay,
                    x=test_x,
                    y=test_y,
                    event_time=test_event_time,
                    label_event_time=test_target_time,
                    train_x=train_x,
                    train_y=train_y,
                    train_label_event_time=train_target_time,
                    calibration_x=cal_x,
                    calibration_y=cal_y,
                    calibration_time=cal_event_time,
                    device=device,
                )
                predictions[policy] = prediction
                summary.append(
                    {
                        "domain_id": domain,
                        **details,
                        **_score_summary(test_y, prediction),
                        "test_event_start_utc": pd.to_datetime(
                            test_event_time[0], unit="s", utc=True
                        ).isoformat(),
                        "test_event_end_utc": pd.to_datetime(
                            test_event_time[-1], unit="s", utc=True
                        ).isoformat(),
                        "event_gaps_gt_one_hour": int(np.sum(np.diff(test_event_time) > 3600)),
                        "max_event_gap_hours": float(np.max(np.diff(test_event_time)) / 3600)
                        if len(test_event_time) > 1
                        else None,
                    }
                )
                monthly.extend(
                    _monthly_metrics(domain, delay, test_event_time, test_y, {policy: prediction})
                )
            intervals.extend(
                _block_bootstrap_intervals(
                    times=test_event_time,
                    y=test_y,
                    predictions=predictions,
                    domain=domain,
                    delay=delay,
                )
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.csv"
    monthly_path = output_dir / "monthly_metrics.csv"
    intervals_path = output_dir / "paired_block_intervals.csv"
    pd.DataFrame(summary).to_csv(summary_path, index=False)
    pd.DataFrame(monthly).to_csv(monthly_path, index=False)
    pd.DataFrame(intervals).to_csv(intervals_path, index=False)
    manifest = {
        "study": "eia_2026_out_of_time_confirmation_v1",
        "status": "retrospective event-time confirmation; source availability unknown",
        "executed_at_utc": utc_now(),
        "git_head": commit(),
        "source_archive_sha256": sha256(ARCHIVE),
        "readiness_report_sha256": sha256(REPORT),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "readiness_audit_script_sha256": sha256(
            Path(__file__).with_name("audit_eia_2026_holdout_readiness.py")
        ),
        "data_source_code_hash": source_hash(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "source_series": [
            f"EBA.{respondent}-ALL.{kind}.H" for respondent in RESPONDENTS for kind in TYPES
        ],
        "splits": split_counts,
        "policies": list(POLICIES),
        "delay_hours": list(DELAY_HOURS),
        "model_and_policy_constants": {
            "ridge_alpha": 1.0,
            "trigger_window_hours": 24,
            "trigger_quantile": 0.95,
            "trigger_cooldown_hours": 168,
            "weekly_update_hours": 168,
            "monthly_update_hours": 720,
        },
        "feedback_contract": "Complete labels mature at target event time plus imposed 0/24/168-hour delay; all policies share feedback; source release times are unknown.",
        "gap_handling": "No imputation across event-time gaps. Only rows with finite target and all four finite predictors are scored. Policy cadence and feedback maturity use elapsed UTC time.",
        "metric_scope": "Forecasting risk and refit resources. No downstream electricity decision utility or prospective guarantee.",
        "uncertainty": "Paired bootstrap of aligned fixed 168-hour blocks; 10000 draws, deterministic seed by authority and delay; descriptive and not multiplicity-adjusted.",
        "elapsed_seconds": time.perf_counter() - started,
        "raw_rows_or_predictions_persisted": False,
        "outputs_sha256": {},
    }
    for path in (summary_path, monthly_path, intervals_path):
        manifest["outputs_sha256"][path.name] = sha256(path)
    write_json(output_dir / "manifest.json", manifest)
    _write_report(output_dir / "results.md", summary, intervals, manifest)
    manifest["outputs_sha256"]["results.md"] = sha256(output_dir / "results.md")
    write_json(output_dir / "manifest.json", manifest)
    return output_dir


def _write_report(path: Path, summary: list[dict], intervals: list[dict], manifest: dict) -> None:
    lines = [
        "# EIA 2026 out-of-time retraining comparison",
        "",
        "**Status:** retrospective event-time confirmation on a new-to-ShiftLab period. EIA release times are unknown, and no downstream decision utility is observed.",
        "",
        f"Device: `{manifest['device']}` ({manifest['gpu_name']}); source SHA-256 `{manifest['source_archive_sha256']}`.",
        "",
        "## RMSE and refit resources",
        "",
        "| Authority | Delay (h) | Policy | RMSE | MAE | Updates | Fit rows | Mature labels |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['domain_id']} | {row['delay_hours']} | {row['policy']} | {row['rmse']:.4f} | "
            f"{row['mae']:.4f} | {row['updates_after_test_start']} | {row['cumulative_fit_rows']} | "
            f"{row['matured_test_feedback_by_test_end']} |"
        )
    lines.extend(
        [
            "",
            "## Paired differences from frozen",
            "",
            "Intervals resample fixed 168-hour blocks; they are descriptive and not multiplicity-adjusted.",
            "",
            "| Authority | Delay (h) | Policy | Metric | Difference | 95% block interval | Blocks |",
            "|---|---:|---|---|---:|---:|---:|",
        ]
    )
    for row in intervals:
        lines.append(
            f"| {row['domain_id']} | {row['delay_hours']} | {row['policy']} | {row['metric']} | "
            f"{row['point_difference']:.6g} | [{row['ci_2_5']:.6g}, {row['ci_97_5']:.6g}] | "
            f"{row['n_populated_blocks']} |"
        )
    lines.extend(
        [
            "",
            "CISO and ERCO are reported separately and are not counted as independent deployment replications. Delay settings are assumptions, not EIA release-time measurements. Error-triggered retraining is a heuristic, not a sequential guarantee. Fit rows and update counts are resource proxies; no electrical-system cost or utility conversion is made.",
            "",
            "See `summary.csv`, `monthly_metrics.csv`, `paired_block_intervals.csv`, and `manifest.json` for aggregate metrics and provenance.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/independent_real_data/eia_2026_v1"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU instead of CUDA")
    args = parser.parse_args()
    print(run(args.output_dir, force_cpu=args.cpu).as_posix())


if __name__ == "__main__":
    main()
