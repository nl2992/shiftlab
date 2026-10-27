"""Compare frozen, periodic and threshold-triggered EIA retraining policies."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset

DELAY_HOURS = (0, 24, 168)
FEATURES = 4
RIDGE_ALPHA = 1.0
TRIGGER_WINDOW_HOURS = 24
TRIGGER_QUANTILE = 0.95
TRIGGER_COOLDOWN_HOURS = 168
WEEK_HOURS = 168
MONTH_HOURS = 720


def _fit_ridge(x: np.ndarray, y: np.ndarray, device: torch.device) -> dict:
    if x.ndim != 2 or x.shape[1] != FEATURES or len(x) != len(y) or len(y) < 20:
        raise ValueError("Ridge fit requires at least 20 matching four-feature rows")
    if np.isinf(x).any() or not np.isfinite(y).all():
        raise ValueError("Ridge fit data cannot contain infinite predictors or missing targets")
    if np.any(np.isfinite(x).sum(axis=0) == 0):
        raise ValueError("Each EIA feature needs at least one observed training value")
    median = np.nanmedian(x, axis=0)
    imputed_x = np.where(np.isnan(x), median, x)
    x_mean = imputed_x.mean(axis=0, dtype=np.float64)
    x_scale = imputed_x.std(axis=0, dtype=np.float64)
    x_scale[x_scale < 1e-12] = 1.0
    z = (imputed_x - x_mean) / x_scale
    y_mean = float(y.mean())
    dtype = torch.float64
    tx = torch.as_tensor(z, dtype=dtype, device=device)
    ty = torch.as_tensor(y - y_mean, dtype=dtype, device=device)
    gram = tx.T @ tx + RIDGE_ALPHA * torch.eye(FEATURES, dtype=dtype, device=device)
    rhs = tx.T @ ty
    coefficient = torch.linalg.solve(gram, rhs)
    if not torch.isfinite(coefficient).all():
        raise FloatingPointError("Ridge solve produced nonfinite coefficients")
    return {
        "mean": x_mean,
        "scale": x_scale,
        "median": median,
        "coefficient": coefficient.detach().cpu().numpy(),
        "intercept": y_mean,
    }


def _predict(model: dict, x: np.ndarray) -> np.ndarray:
    if np.isinf(x).any():
        raise ValueError("Predictions cannot contain infinite EIA features")
    imputed_x = np.where(np.isnan(x), model["median"], x)
    z = (imputed_x - model["mean"]) / model["scale"]
    result = z @ model["coefficient"] + model["intercept"]
    if not np.isfinite(result).all():
        raise FloatingPointError("Ridge prediction is nonfinite")
    return result


def _calibration_threshold(
    x: np.ndarray,
    y: np.ndarray,
    times: np.ndarray,
    model: dict,
) -> float:
    prediction = _predict(model, x)
    errors_squared = np.square(y - prediction)
    index = pd.to_datetime(times, unit="s", utc=True)
    rolling = (
        pd.Series(errors_squared, index=index)
        .rolling(f"{TRIGGER_WINDOW_HOURS}h", min_periods=20)
        .mean()
    )
    finite = rolling.to_numpy()[np.isfinite(rolling.to_numpy())]
    if len(finite) < 50:
        raise ValueError("Calibration split has too few complete 24-hour rolling errors")
    return float(np.quantile(finite, TRIGGER_QUANTILE))


def _score_summary(y: np.ndarray, prediction: np.ndarray) -> dict:
    error = y - prediction
    return {
        "n": len(y),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mae": float(np.mean(np.abs(error))),
        "mse": float(np.mean(np.square(error))),
    }


def _simulate_policy(
    *,
    policy: str,
    delay_hours: int,
    x: np.ndarray,
    y: np.ndarray,
    event_time: np.ndarray,
    label_event_time: np.ndarray,
    train_x: np.ndarray,
    train_y: np.ndarray,
    train_label_event_time: np.ndarray,
    calibration_x: np.ndarray,
    calibration_y: np.ndarray,
    calibration_time: np.ndarray,
    device: torch.device,
) -> tuple[np.ndarray, dict]:
    if delay_hours < 0:
        raise ValueError("Assumed label delay must be nonnegative")
    first_time = float(event_time[0])
    initial_mask = train_label_event_time + delay_hours * 3600 <= first_time
    fit_x = train_x[initial_mask].copy()
    fit_y = train_y[initial_mask].copy()
    if len(fit_y) < 20:
        raise ValueError("Fewer than 20 training labels are mature at test start")

    fit_start = time.perf_counter()
    model = _fit_ridge(fit_x, fit_y, device)
    fit_seconds = time.perf_counter() - fit_start
    initial_n = len(fit_y)
    fit_rows_total = initial_n
    update_count = 0

    calibration_mask = calibration_time + 3600 + delay_hours * 3600 <= first_time
    threshold = _calibration_threshold(
        calibration_x[calibration_mask],
        calibration_y[calibration_mask],
        calibration_time[calibration_mask],
        model,
    )

    predictions = np.full(len(y), np.nan, dtype=np.float64)
    matured_indices: list[int] = []
    arrivals: list[tuple[float, float]] = []
    arrival_cursor = 0
    last_fit_feedback_count = 0
    cadence_seconds = {"weekly": WEEK_HOURS, "monthly": MONTH_HOURS}.get(policy)
    next_update = first_time + (cadence_seconds or 0) * 3600
    last_trigger_time = -np.inf

    for index, current_time in enumerate(event_time):
        while arrival_cursor < index:
            candidate_idx = arrival_cursor
            arrival_time = label_event_time[candidate_idx] + delay_hours * 3600
            if arrival_time > current_time:
                break
            if not np.isfinite(predictions[candidate_idx]):
                raise RuntimeError("A label matured before its prediction was stored")
            arrivals.append(
                (
                    float(arrival_time),
                    float((y[candidate_idx] - predictions[candidate_idx]) ** 2),
                )
            )
            matured_indices.append(candidate_idx)
            arrival_cursor += 1

        new_feedback = len(matured_indices) > last_fit_feedback_count
        should_update = False
        if policy in {"weekly", "monthly"}:
            should_update = current_time >= next_update and new_feedback
        elif policy == "error_trigger" and new_feedback:
            cutoff = current_time - TRIGGER_WINDOW_HOURS * 3600
            recent = [value for arrival, value in arrivals if arrival > cutoff]
            cooldown_complete = current_time - last_trigger_time >= TRIGGER_COOLDOWN_HOURS * 3600
            should_update = (
                len(recent) >= 20 and float(np.mean(recent)) > threshold and cooldown_complete
            )

        if should_update:
            feedback_idx = np.asarray(matured_indices, dtype=np.int64)
            update_x = np.concatenate([fit_x, x[feedback_idx]], axis=0)
            update_y = np.concatenate([fit_y, y[feedback_idx]], axis=0)
            fit_start = time.perf_counter()
            model = _fit_ridge(update_x, update_y, device)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            fit_seconds += time.perf_counter() - fit_start
            fit_rows_total += len(update_y)
            update_count += 1
            last_fit_feedback_count = len(matured_indices)
            if policy == "error_trigger":
                last_trigger_time = current_time
            else:
                next_update = current_time + (cadence_seconds or 0) * 3600

        predictions[index] = float(_predict(model, x[index : index + 1])[0])

    matured_test_labels = int(np.sum(label_event_time + delay_hours * 3600 <= event_time[-1]))
    details = {
        "policy": policy,
        "delay_hours": delay_hours,
        "test_n": len(y),
        "initial_training_rows": initial_n,
        "updates_after_test_start": update_count,
        "cumulative_fit_rows": fit_rows_total,
        "fit_seconds": fit_seconds,
        "matured_test_feedback_by_test_end": matured_test_labels,
        "calibration_trigger_threshold_mse": threshold,
    }
    if not np.isfinite(predictions).all():
        raise FloatingPointError("Some test predictions were not produced")
    return predictions, details


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    protocol_path = (
        Path(__file__).resolve().parents[1] / "papers/shiftguard_unified/eia_retraining_protocol.md"
    )
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        source_manifest.get("dataset") != "eia"
        or source_manifest.get("version") != "e47bdef8b208f8e7d788"
    ):
        raise ValueError("This frozen run accepts only EIA release e47bdef8b208f8e7d788")
    frame = pd.read_parquet(observations_path)
    if frame.features.map(len).ne(FEATURES).any():
        raise ValueError("Expected four EIA feature values per observation")
    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    summary_rows: list[dict] = []
    monthly_rows: list[dict] = []
    delay_thresholds: dict[str, dict[str, float]] = {}
    policy_names = ("frozen", "weekly", "monthly", "error_trigger")
    for domain, group in frame.groupby("domain_id", sort=True):
        group = group.sort_values("event_time", kind="stable").reset_index(drop=True)
        x_all = np.stack(group.features.to_numpy()).astype(np.float64, copy=False)
        y_all = group.target.to_numpy(dtype=np.float64)
        event_all = group.event_time.to_numpy(dtype=np.float64)
        label_event_all = group.label_event_time.to_numpy(dtype=np.float64)
        if np.isinf(x_all).any() or not np.isfinite(event_all).all():
            raise ValueError(f"{domain} features cannot be infinite and event times must be finite")
        train_mask = (
            group.split.eq("train").to_numpy() & np.isfinite(y_all) & np.isfinite(label_event_all)
        )
        calibration_mask = (
            group.split.eq("calibration").to_numpy()
            & np.isfinite(y_all)
            & np.isfinite(label_event_all)
        )
        test_mask = (
            group.split.eq("test").to_numpy() & np.isfinite(y_all) & np.isfinite(label_event_all)
        )
        if min(train_mask.sum(), calibration_mask.sum(), test_mask.sum()) < 500:
            raise ValueError(f"{domain} lacks sufficient frozen split support")
        x_train, y_train = x_all[train_mask], y_all[train_mask]
        train_label_event = label_event_all[train_mask]
        x_cal, y_cal, time_cal = (
            x_all[calibration_mask],
            y_all[calibration_mask],
            event_all[calibration_mask],
        )
        x_test, y_test = x_all[test_mask], y_all[test_mask]
        time_test, label_test = event_all[test_mask], label_event_all[test_mask]
        if len(time_test) > 1 and not np.all(np.diff(time_test) == 3600):
            raise ValueError(f"{domain} test events are not a unique contiguous hourly sequence")
        if np.any(label_test <= time_test):
            raise ValueError(f"{domain} target events must occur after their forecast events")
        delay_thresholds[str(domain)] = {}
        for delay in DELAY_HOURS:
            for policy in policy_names:
                prediction, details = _simulate_policy(
                    policy=policy,
                    delay_hours=delay,
                    x=x_test,
                    y=y_test,
                    event_time=time_test,
                    label_event_time=label_test,
                    train_x=x_train,
                    train_y=y_train,
                    train_label_event_time=train_label_event,
                    calibration_x=x_cal,
                    calibration_y=y_cal,
                    calibration_time=time_cal,
                    device=device,
                )
                delay_thresholds[str(domain)][str(delay)] = details[
                    "calibration_trigger_threshold_mse"
                ]
                summary_rows.append(
                    {
                        "domain_id": str(domain),
                        **details,
                        **_score_summary(y_test, prediction),
                    }
                )
                dates = pd.to_datetime(time_test, unit="s", utc=True)
                monthly_frame = pd.DataFrame(
                    {"month": dates.strftime("%Y-%m"), "target": y_test, "prediction": prediction}
                )
                for month, month_group in monthly_frame.groupby("month", sort=True):
                    monthly_rows.append(
                        {
                            "domain_id": str(domain),
                            "delay_hours": delay,
                            "policy": policy,
                            "month": month,
                            **_score_summary(
                                month_group.target.to_numpy(),
                                month_group.prediction.to_numpy(),
                            ),
                        }
                    )

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(output_dir / "summary.csv", index=False)
    pd.DataFrame(monthly_rows).to_csv(output_dir / "monthly_metrics.csv", index=False)
    run_manifest = {
        "study": "eia_retraining_resource_frontier_v1",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": source_manifest["version"],
        "source_url": source_manifest.get("source_url"),
        "input_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(Path(__file__)),
        "data_source_code_hash": source_hash(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "delays_hours": list(DELAY_HOURS),
        "policies": list(policy_names),
        "model": {
            "type": "Ridge",
            "alpha": RIDGE_ALPHA,
            "feature_imputation": "training-pool median, refit after each update",
            "feature_standardization": "training pool only",
            "target": "next-period EIA type D",
        },
        "trigger": {
            "window_hours": TRIGGER_WINDOW_HOURS,
            "calibration_quantile": TRIGGER_QUANTILE,
            "cooldown_hours": TRIGGER_COOLDOWN_HOURS,
            "guarantee": "none; heuristic threshold with repeated monitoring",
        },
        "feedback_contract": "complete labels after target event time plus imposed delay; same feedback for all policies; features assumed available at event time",
        "metric_scope": "forecasting risk and retraining resources only; no application decision utility or cost conversion",
        "prior_exposure": "EIA test period was used by existing repository time-series diagnostics; exploratory only",
        "availability": "historical publication/revision times unknown; retrospective event-time replay",
        "thresholds": delay_thresholds,
        "output_sha256": {},
    }
    write_report(output_dir / "results.md", summary_rows, run_manifest)
    run_manifest["output_sha256"] = {
        name: sha256(output_dir / name)
        for name in ("summary.csv", "monthly_metrics.csv", "results.md")
    }
    write_json(output_dir / "manifest.json", run_manifest)
    return output_dir


def write_report(path: Path, summary_rows: list[dict], manifest: dict) -> None:
    lines = [
        "# EIA event-time retraining and resource frontier",
        "",
        "**Status:** exploratory retrospective development replay; publisher release times are unknown and the test period was previously inspected.",
        "",
        f"Device: `{manifest['device']}` (`{manifest['gpu_name']}`); source version `{manifest['dataset_version']}`.",
        "",
        "RMSE by balancing authority, assumed label delay, and policy:",
        "",
        "| Domain | Delay (h) | Policy | RMSE | MAE | Updates | Fit rows | Mature test labels |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['domain_id']} | {row['delay_hours']} | {row['policy']} | {row['rmse']:.3f} | "
            f"{row['mae']:.3f} | {row['updates_after_test_start']} | {row['cumulative_fit_rows']} | "
            f"{row['matured_test_feedback_by_test_end']} |"
        )
    lines.extend(
        [
            "",
            (
                "The report keeps model error and retraining resources separate; no arbitrary conversion to system utility was applied. "
                "Delay values are sensitivity assumptions, not measured EIA publication latency. The error-trigger policy is a heuristic, "
                "not an anytime-valid test, and the displayed test outcomes do not provide independent or prospective evidence."
            ),
            "",
            "See `summary.csv`, `monthly_metrics.csv`, and `manifest.json` for per-policy results and provenance.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path", type=Path, default=Path("data/processed/eia/e47bdef8b208f8e7d788")
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/eia_retraining_v1"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even if CUDA is available")
    args = parser.parse_args()
    print(run(args.dataset_path, args.output_dir, force_cpu=args.cpu))


if __name__ == "__main__":
    main()
