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


def diagnose(path: Path) -> dict:
    manifest_path = path / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(path / "observations.parquet")
    quality = validate_dataset(path)
    features = manifest["feature_names"]
    rows = []
    for domain, group in frame.groupby("domain_id", sort=False):
        train = group[group.split == "train"].copy()
        calibration = group[group.split == "calibration"].copy()
        test = group[group.split == "test"].copy()
        train = train[np.isfinite(train.target.to_numpy(dtype=float))]
        calibration = calibration[np.isfinite(calibration.target.to_numpy(dtype=float))]
        test = test[np.isfinite(test.target.to_numpy(dtype=float))]
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
        block = max(2, int(np.sqrt(len(test))))
        rolling_window = max(10, min(100, len(test) // 4))
        rolling_mse = pd.Series(error**2).rolling(rolling_window, min_periods=rolling_window).mean()
        rows.append(
            {
                "domain_id": str(domain),
                "train_n": len(train),
                "calibration_n": len(calibration),
                "test_n": len(test),
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
            "calibration": "calibration split only; symmetric absolute-residual interval with finite-sample rank",
            "evaluation": "test split only; chronological ordering preserved",
            "uncertainty": "circular moving-block percentile interval on paired squared-loss differences, block length floor(sqrt(test_n)); descriptive, not a causal or availability guarantee",
            "decision_loss": "not reported: these are continuous forecasting tasks without a sourced, application-grounded utility",
        },
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "OPSD and NOAA label availability is unknown; train/calibration/test refer to retrospective event-time partitions.",
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
