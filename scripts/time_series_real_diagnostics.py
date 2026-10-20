"""Run retrospective, chronological regression and interval diagnostics on stored tasks."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset


def _conformal_radius(residuals: np.ndarray, alpha: float = 0.2) -> float:
    ordered = np.sort(np.abs(residuals))
    rank = min(len(ordered), int(np.ceil((len(ordered) + 1) * (1 - alpha))))
    return float(ordered[rank - 1])


def _bootstrap_mean_interval(values: np.ndarray, seed: int, block_length: int) -> list[float]:
    """Circular moving-block percentile interval for a time-ordered mean."""
    rng = np.random.default_rng(seed)
    n = len(values)
    blocks = int(np.ceil(n / block_length))
    estimates = np.empty(1000)
    offsets = np.arange(block_length)
    for index in range(len(estimates)):
        starts = rng.integers(0, n, size=blocks)
        sample = np.concatenate([(start + offsets) % n for start in starts])[:n]
        estimates[index] = values[sample].mean()
    return [float(v) for v in np.quantile(estimates, [0.025, 0.975])]


def _block_length_sensitivity(n: int) -> list[int]:
    """Use half, baseline and double sqrt(n) block lengths, clipped to sample size."""
    if n < 4:
        raise ValueError("At least four observations are required for block sensitivity")
    baseline = max(2, int(np.sqrt(n)))
    return sorted({max(2, baseline // 2), baseline, min(n, 2 * baseline)})


def _diagnostic_partitions(
    group: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Select train/calibration/test rows without crossing known availability times.

    If required availability clocks are incomplete, retain event-time partitions only as
    retrospective diagnostics and make that limitation explicit in the returned protocol.
    """
    finite_target = np.isfinite(group.target.to_numpy(dtype=float))
    train_mask = group.split.eq("train").to_numpy() & finite_target
    calibration_mask = group.split.eq("calibration").to_numpy() & finite_target
    test_mask = group.split.eq("test").to_numpy() & finite_target
    train = group.loc[train_mask]
    calibration = group.loc[calibration_mask]
    test = group.loc[test_mask]
    timing_columns = ["feature_available_time", "prediction_time"]
    complete = bool(len(train) and len(calibration) and len(test))
    for part in (train, calibration, test):
        for column in timing_columns:
            if column not in part or part[column].isna().any():
                complete = False
    for part in (train, calibration):
        if "label_available_time" not in part or part.label_available_time.isna().any():
            complete = False

    if not complete:
        return (
            train,
            calibration,
            test,
            {
                "mode": "retrospective_event_time_splits",
                "strict_label_availability_filter": False,
                "reason": "required feature, prediction, or train/calibration label-availability times are unknown",
                "train_split_rows": int(train_mask.sum()),
                "train_eligible_rows": int(train_mask.sum()),
                "calibration_split_rows": int(calibration_mask.sum()),
                "calibration_eligible_rows": int(calibration_mask.sum()),
                "test_split_rows": int(test_mask.sum()),
                "test_eligible_rows": int(test_mask.sum()),
            },
        )

    first_calibration_prediction = float(calibration.prediction_time.min())
    first_test_prediction = float(test.prediction_time.min())
    train_feature = train.feature_available_time.to_numpy(dtype=float)
    train_labels = train.label_available_time.to_numpy(dtype=float)
    train_eligible = (train_feature < first_calibration_prediction) & (
        train_labels < first_calibration_prediction
    )
    cal_feature = calibration.feature_available_time.to_numpy(dtype=float)
    cal_prediction = calibration.prediction_time.to_numpy(dtype=float)
    cal_labels = calibration.label_available_time.to_numpy(dtype=float)
    cal_eligible = (
        (cal_feature <= cal_prediction)
        & (cal_prediction < first_test_prediction)
        & (cal_labels < first_test_prediction)
    )
    test_feature = test.feature_available_time.to_numpy(dtype=float)
    test_prediction = test.prediction_time.to_numpy(dtype=float)
    test_eligible = test_feature <= test_prediction
    protocol = {
        "mode": "strict_known_availability",
        "strict_label_availability_filter": True,
        "train_fit_cutoff": first_calibration_prediction,
        "test_prediction_cutoff": first_test_prediction,
        "train_split_rows": int(train_mask.sum()),
        "train_eligible_rows": int(train_eligible.sum()),
        "calibration_split_rows": int(calibration_mask.sum()),
        "calibration_eligible_rows": int(cal_eligible.sum()),
        "test_split_rows": int(test_mask.sum()),
        "test_eligible_rows": int(test_eligible.sum()),
    }
    return (
        train.loc[train_eligible],
        calibration.loc[cal_eligible],
        test.loc[test_eligible],
        protocol,
    )


def diagnose(path: Path) -> dict:
    manifest_path = path / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(path / "observations.parquet")
    quality = validate_dataset(path)
    features = manifest["feature_names"]
    rows = []
    for domain, group in frame.groupby("domain_id", sort=False):
        train, calibration, test, availability_protocol = _diagnostic_partitions(group)
        if min(len(train), len(calibration), len(test)) < 20:
            continue
        train = train.sort_values("event_time", kind="stable")
        calibration = calibration.sort_values("event_time", kind="stable")
        test = test.sort_values("event_time", kind="stable")
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
        model.fit(np.stack(train.features.to_numpy()), train.target.to_numpy(dtype=float))
        cal_prediction = model.predict(np.stack(calibration.features.to_numpy()))
        cal_residual = calibration.target.to_numpy(dtype=float) - cal_prediction
        radius = _conformal_radius(cal_residual)
        prediction = model.predict(np.stack(test.features.to_numpy()))
        target = test.target.to_numpy(dtype=float)
        error = target - prediction
        baseline = target - float(train.target.mean())
        covered = np.abs(error) <= radius
        loss_difference = error**2 - baseline**2
        block_lengths = _block_length_sensitivity(len(test))
        block = max(2, int(np.sqrt(len(test))))
        rolling_window = max(10, min(100, len(test) // 4))
        rolling_mse = pd.Series(error**2).rolling(rolling_window, min_periods=rolling_window).mean()
        rows.append(
            {
                "domain_id": str(domain),
                "train_n": len(train),
                "calibration_n": len(calibration),
                "test_n": len(test),
                "availability_protocol": availability_protocol,
                "model": "train-only median imputation, standardization, Ridge(alpha=1)",
                "baseline": "training-mean predictor",
                "calibration_interval": "symmetric split residual interval; calibration labels are used retrospectively",
                "calibration_abs_error_radius_80": radius,
                "test_rmse": float(np.sqrt(np.mean(error**2))),
                "test_baseline_rmse": float(np.sqrt(np.mean(baseline**2))),
                "test_mae": float(np.mean(np.abs(error))),
                "test_interval_coverage": float(covered.mean()),
                "test_interval_width": float(2 * radius),
                "rolling_window_rows": rolling_window,
                "rolling_test_mse_first": float(rolling_mse.dropna().iloc[0]),
                "rolling_test_mse_last": float(rolling_mse.dropna().iloc[-1]),
                "test_mse_difference_vs_train_mean": float(loss_difference.mean()),
                "moving_block_length_rows": block,
                "moving_block_95pct_interval_mse_difference": _bootstrap_mean_interval(
                    loss_difference, seed=20261019, block_length=block
                ),
                "moving_block_sensitivity": [
                    {
                        "block_length_rows": length,
                        "mse_difference_interval_95pct": _bootstrap_mean_interval(
                            loss_difference,
                            seed=20261019,
                            block_length=length,
                        ),
                    }
                    for length in block_lengths
                ],
                "event_time_start": float(test.event_time.min()),
                "event_time_end": float(test.event_time.max()),
            }
        )
    if not rows:
        raise ValueError(f"No domain has at least 20 labeled rows in each split: {path}")
    return {
        "dataset": manifest["dataset"],
        "version": manifest["version"],
        "manifest_sha256": sha256(manifest_path),
        "feature_names": features,
        "manifest_label_availability_known": bool(frame.label_available_time.notna().any()),
        "source_availability": "unknown; this report is retrospective and makes no real-time availability claim",
        "quality": quality,
        "domains": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", nargs="+", required=True)
    parser.add_argument("--output", default="data/reports/time_series_real_diagnostics.json")
    args = parser.parse_args()
    datasets = [diagnose(Path(value)) for value in args.dataset_path]
    report = {
        "description": "Chronological retrospective prediction, interval, rolling-loss, and moving-block diagnostics.",
        "datasets": datasets,
        "protocol": {
            "fit": "train split only, independently within each domain",
            "calibration": "Known timing uses only calibration features available by their prediction times and labels strictly available before the first test prediction; incomplete clocks fall back to clearly marked retrospective event-time splits.",
            "evaluation": "test split only; chronological ordering preserved",
            "uncertainty": "1,000-replicate circular moving-block percentile intervals on paired squared-loss differences; report baseline floor(sqrt(test_n)) and sensitivity at half and twice baseline block length (clipped to test_n); descriptive, not causal or availability guarantees",
            "decision_loss": "not reported: these are continuous forecasting tasks without a sourced, application-grounded utility",
        },
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "OPSD, NOAA and historical EIA availability clocks are unknown; those reports use retrospective event-time partitions and do not make online calibration claims.",
            "The simple Ridge model is a diagnostic baseline, not a tuned or production forecasting system.",
            "Moving-block intervals depend on the selected block length and do not address model-selection uncertainty.",
            "Intervals are evaluated empirically; finite-sample time-series coverage is not guaranteed.",
            "No application-based decision costs are available, so decision loss is intentionally omitted.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    for dataset in datasets:
        print(dataset["dataset"], dataset["version"])
        for row in dataset["domains"]:
            print(
                f"  {row['domain_id']}: RMSE={row['test_rmse']:.4f} "
                f"baseline={row['test_baseline_rmse']:.4f} "
                f"coverage={row['test_interval_coverage']:.3f} "
                f"MSE-diff CI={row['moving_block_95pct_interval_mse_difference']}"
            )
    print(output)


if __name__ == "__main__":
    main()
