"""Run a bounded, explicitly retrospective smoke analysis on the CRSP panel."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from shiftlab.data.provenance import sha256, write_json


def find_panel(root: Path, version: str | None) -> Path:
    base = root / "processed" / "crsp_ciz_next_day"
    if version:
        path = base / version
        if not path.is_dir():
            raise FileNotFoundError(path)
        return path
    candidates = (
        sorted(
            (
                path
                for path in base.iterdir()
                if path.is_dir() and (path / "dataset_manifest.json").is_file()
            ),
            key=lambda path: path.stat().st_mtime,
        )
        if base.exists()
        else []
    )
    if not candidates:
        raise FileNotFoundError("No CRSP panel found; run scripts/build_crsp_study_panel.py first")
    return candidates[-1]


def collect_cohort(path: Path, securities: int, seed: int, batch_size: int):
    dataset = ds.dataset(path / "observations.parquet", format="parquet")
    split_entities: dict[str, set[int]] = defaultdict(set)
    scanner = dataset.scanner(columns=["permno", "split"], batch_size=batch_size)
    for batch in scanner.to_batches():
        frame = batch.to_pandas()
        for name, group in frame.groupby("split", sort=False):
            if name in {"train", "validation", "calibration", "test"}:
                split_entities[name].update(group.permno.astype("int64").unique().tolist())
    common = set.intersection(
        *(split_entities[name] for name in ["train", "validation", "calibration", "test"])
    )
    if len(common) < 10:
        raise ValueError(
            f"Only {len(common)} securities occur in every split; smoke cohort is too small"
        )
    ordered = np.array(sorted(common), dtype=np.int64)
    rng = np.random.default_rng(seed)
    chosen = np.sort(rng.choice(ordered, size=min(securities, len(ordered)), replace=False))
    filter_expr = ds.field("permno").isin(chosen.tolist()) & ds.field("split").isin(
        ["train", "validation", "calibration", "test"]
    )
    columns = ["permno", "split", "features", "target", "dlycaldt"]
    batches = dataset.scanner(
        columns=columns, filter=filter_expr, batch_size=batch_size
    ).to_batches()
    frames = [batch.to_pandas() for batch in batches]
    if not frames:
        raise ValueError("No rows selected for smoke analysis")
    return pd.concat(frames, ignore_index=True), chosen, len(common)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--version")
    parser.add_argument("--securities", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--batch-size", type=int, default=200_000)
    parser.add_argument("--output", type=Path, default=Path("data/reports/crsp_study_smoke.json"))
    args = parser.parse_args()
    if args.securities < 10 or args.batch_size < 1:
        parser.error("--securities must be at least 10 and --batch-size must be positive")

    path = find_panel(args.root, args.version)
    manifest_path = path / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observations_path = path / "observations.parquet"
    expected_sha = manifest["files"]["observations.parquet"]
    if sha256(observations_path) != expected_sha:
        raise ValueError("Panel checksum does not match its manifest")

    frame, chosen, eligible_security_count = collect_cohort(
        path, args.securities, args.seed, args.batch_size
    )
    frame["features"] = frame.features.map(lambda value: np.asarray(value, dtype=np.float64))
    X = np.stack(frame.features.to_numpy())
    y = pd.to_numeric(frame.target, errors="raise").to_numpy(dtype=np.float64)
    train = frame.split.eq("train").to_numpy()
    validation = frame.split.eq("validation").to_numpy()
    calibration = frame.split.eq("calibration").to_numpy()
    test = frame.split.eq("test").to_numpy()
    if min(train.sum(), validation.sum(), calibration.sum(), test.sum()) < 100:
        raise ValueError("Smoke cohort has fewer than 100 rows in at least one split")

    model = make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        Ridge(alpha=1.0),
    )
    model.fit(X[train], y[train])
    pred_cal = model.predict(X[calibration])
    abs_cal = np.abs(y[calibration] - pred_cal)
    rank = min(len(abs_cal), math.ceil((len(abs_cal) + 1) * 0.90))
    radius = float(np.partition(abs_cal, rank - 1)[rank - 1])

    mean_prediction = float(np.mean(y[train]))
    ridge_prediction = model.predict(X[test])
    baseline_prediction = np.full(test.sum(), mean_prediction)
    baseline_error = y[test] - baseline_prediction
    ridge_error = y[test] - ridge_prediction
    coverage = float(np.mean(np.abs(ridge_error) <= radius))
    test_frame = frame.loc[test, ["dlycaldt"]].copy()
    test_frame["baseline_squared_error"] = baseline_error**2
    test_frame["ridge_squared_error"] = ridge_error**2
    by_year = {}
    test_years = pd.to_datetime(test_frame.dlycaldt).dt.year
    for year in sorted(test_years.unique()):
        selected = test_years.eq(year).to_numpy()
        by_year[str(int(year))] = {
            "n": int(selected.sum()),
            "mean_baseline_rmse": float(
                np.sqrt(test_frame.loc[selected, "baseline_squared_error"].mean())
            ),
            "ridge_rmse": float(np.sqrt(test_frame.loc[selected, "ridge_squared_error"].mean())),
        }

    report = {
        "analysis": "CRSP CIZ next-observed-return pipeline smoke test",
        "panel_dataset": manifest["dataset"],
        "panel_version": manifest["version"],
        "panel_manifest_sha256": sha256(manifest_path),
        "observations_parquet_sha256": expected_sha,
        "seed": args.seed,
        "eligible_security_count": eligible_security_count,
        "sampled_security_count": len(chosen),
        "cohort_rule": (
            "Uniform fixed-seed sample from PERMNOs represented in train, validation, calibration, "
            "and test; this survivor cohort is for pipeline testing only."
        ),
        "row_counts": {
            "train": int(train.sum()),
            "validation": int(validation.sum()),
            "calibration": int(calibration.sum()),
            "test": int(test.sum()),
        },
        "model": "training-only median imputation, training-only standardization, Ridge(alpha=1)",
        "calibration": {
            "nominal_coverage": 0.90,
            "n": int(calibration.sum()),
            "absolute_residual_radius": radius,
            "test_empirical_coverage": coverage,
            "mean_interval_width": 2 * radius,
        },
        "test_metrics": {
            "n": int(test.sum()),
            "mean_baseline_rmse": float(np.sqrt(np.mean(baseline_error**2))),
            "ridge_rmse": float(np.sqrt(np.mean(ridge_error**2))),
            "mean_baseline_mae": float(np.mean(np.abs(baseline_error))),
            "ridge_mae": float(np.mean(np.abs(ridge_error))),
        },
        "test_rmse_by_year": by_year,
        "limitations": [
            "A deterministic sampled cohort selected for presence in all four splits; survivorship selection makes this unsuitable for inference.",
            "Calibration/test coverage is descriptive for this smoke sample, not a conditional or online guarantee.",
            "CRSP dates provide retrospective ordering, not verified historical release times.",
            "No application-grounded utility, trading strategy, or causal shift attribution is evaluated.",
        ],
    }
    write_json(args.output, report)
    print(json.dumps(report, indent=2))
    print(f"Smoke report saved to {args.output}")


if __name__ == "__main__":
    main()
