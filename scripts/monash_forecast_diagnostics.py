"""Retrospective diagnostics on local Monash/M4 official fixed-origin holdouts."""

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


def diagnose_entity(frame: pd.DataFrame) -> dict:
    """Compare train-only Ridge with simple baselines for one official TSF origin."""
    train = frame.loc[frame.split == "train"].copy()
    test_all = frame.loc[frame.split == "test"].copy()
    train = train[np.isfinite(train.target.to_numpy(dtype=float))]
    if len(train) < 20 or not len(test_all):
        raise ValueError("Need at least 20 finite training targets and official test rows")
    metadata = test_all.metadata.map(json.loads).tolist()
    origins = {int(row["origin_index"]) for row in metadata}
    horizons = {int(row["official_horizon"]) for row in metadata}
    steps = [int(row["forecast_step"]) for row in metadata]
    if len(origins) != 1 or len(horizons) != 1:
        raise ValueError("Test rows must share one official origin and horizon")
    origin, horizon = origins.pop(), horizons.pop()
    if sorted(steps) != list(range(1, horizon + 1)):
        raise ValueError("Test rows must contain every official horizon step exactly once")
    if int(train.sequence_index.max()) > origin:
        raise ValueError("Training targets must not exceed the official forecast origin")
    X_train = np.stack(train.features.to_numpy()).astype(float)
    finite_test = np.isfinite(test_all.target.to_numpy(dtype=float))
    test = test_all.loc[finite_test].copy()
    steps = np.asarray(steps)[finite_test].tolist()
    if not len(test):
        raise ValueError("Official horizon has no finite scoring targets")
    X_test = np.stack(test.features.to_numpy()).astype(float)
    if not np.allclose(X_test, X_test[0], equal_nan=True):
        raise ValueError(
            "Official fixed-origin holdout features must be identical across forecast steps"
        )
    y_train = train.target.to_numpy(dtype=float)
    y_test = test.target.to_numpy(dtype=float)
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
    model.fit(X_train, y_train)
    predictions = {
        "ridge": model.predict(X_test),
        "last_value": np.full(len(test), X_test[0, -1]),
        "training_mean": np.full(len(test), y_train.mean()),
    }
    scale = float(np.mean(np.abs(np.diff(y_train))))
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    target = y_test
    metrics = {}
    for name, prediction in predictions.items():
        error = target - prediction
        metrics[name] = {
            "rmse": float(np.sqrt(np.mean(error**2))),
            "mae": float(np.mean(np.abs(error))),
            "mase": float(np.mean(np.abs(error)) / scale),
        }
    by_step = []
    for i, step in enumerate(steps):
        by_step.append(
            {
                "forecast_step": step,
                "target": float(target[i]),
                "predictions": {
                    name: float(prediction[i]) for name, prediction in predictions.items()
                },
                "absolute_errors": {
                    name: float(abs(target[i] - prediction[i]))
                    for name, prediction in predictions.items()
                },
            }
        )
    return {
        "entity_id": str(frame.entity_id.iloc[0]),
        "n_train": len(train),
        "n_test": len(test),
        "origin_index": origin,
        "official_horizon": horizon,
        "train_only_naive_scale": scale,
        "metrics": metrics,
        "by_step": by_step,
    }


def diagnose_dataset(path: Path) -> dict:
    manifest_path = path / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["dataset"] != "monash":
        raise ValueError(f"Expected Monash version, got {manifest['dataset']}")
    frame = pd.read_parquet(path / "observations.parquet")
    entities = [diagnose_entity(group) for _, group in frame.groupby("entity_id", sort=True)]
    if not entities:
        raise ValueError(f"No series in {path}")
    horizons = sorted({row["official_horizon"] for row in entities})
    return {
        "dataset": manifest.get("retrieval_parameters", {}).get("dataset", "unknown"),
        "version": manifest["version"],
        "manifest_sha256": sha256(manifest_path),
        "entities": len(entities),
        "official_horizons": horizons,
        "series_metrics": entities,
        "mean_series_mase": {
            model: float(np.mean([row["metrics"][model]["mase"] for row in entities]))
            for model in ["ridge", "last_value", "training_mean"]
        },
        "entities_beaten_by_ridge": {
            model: int(
                sum(
                    row["metrics"]["ridge"]["mase"] < row["metrics"][model]["mase"]
                    for row in entities
                )
            )
            for model in ["last_value", "training_mean"]
        },
    }


def build_report(paths: list[Path]) -> dict:
    datasets = [diagnose_dataset(path) for path in paths]
    return {
        "description": "Retrospective per-series Ridge and naive-baseline metrics on publisher-declared Monash/M4 fixed-origin holdouts.",
        "protocol": {
            "fit": "Ridge uses only finite rows marked train within each series; imputation and scaling are fit on training features only.",
            "baselines": "Last observed value at the official origin and the training-target mean; MASE denominator is mean absolute one-step change in training targets (fallback 1 only for a constant series).",
            "holdout": "Publisher-declared forecast steps are scored individually and aggregated per series; no random split or horizon substitution is used.",
            "time": "TSF sequence indices are ordinal within-series positions, not verified event, publication, or label-availability times.",
            "uncertainty": "Per-series descriptive results only. The deterministic first-series subset is not treated as an IID sample of the full competition.",
        },
        "datasets": datasets,
        "limitations": [
            "This diagnostic is retrospective and does not claim real-time label availability.",
            "The direct Ridge model receives the same origin covariates at every horizon step; it is a baseline, not a tuned multi-step forecaster.",
            "Only locally acquired deterministic subsets are evaluated; results are not full-dataset competition estimates.",
        ],
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", nargs="+", required=True)
    parser.add_argument("--output", default="data/reports/monash_forecast_diagnostics.json")
    args = parser.parse_args()
    report = build_report([Path(value) for value in args.dataset_path])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    for dataset in report["datasets"]:
        print(
            f"{dataset['dataset']}: entities={dataset['entities']} "
            f"horizons={dataset['official_horizons']} MASE={dataset['mean_series_mase']}"
        )
    print(output)


if __name__ == "__main__":
    main()
