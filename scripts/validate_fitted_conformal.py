"""Evaluate a fitted regression predictor with chronological split/prequential conformal scores."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.replication import replicate_grid_integrity
from shiftlab.data.synthetic import conformal_stress_catalogue, generate_chunks
from shiftlab.methods import weighted_conformal_quantile


def _arrived_prior_scores(
    now: float,
    calibration_residual: np.ndarray,
    calibration_prediction_time: np.ndarray,
    calibration_available: np.ndarray,
    prior_test_residual: np.ndarray,
    prior_test_prediction_time: np.ndarray,
    prior_test_available: np.ndarray,
) -> np.ndarray:
    """Return only residuals both predicted and labeled strictly before this request."""
    calibration_known = (
        (calibration_prediction_time < now)
        & np.isfinite(calibration_available)
        & (calibration_available < now)
    )
    test_known = (
        (prior_test_prediction_time < now)
        & np.isfinite(prior_test_available)
        & (prior_test_available < now)
    )
    return np.concatenate(
        (calibration_residual[calibration_known], prior_test_residual[test_known])
    )


def _block_interval(values: np.ndarray, block_length: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    n = len(values)
    block_count = int(np.ceil(n / block_length))
    offsets = np.arange(block_length)
    estimates = np.empty(500)
    for i in range(len(estimates)):
        starts = rng.integers(0, n, size=block_count)
        indices = np.concatenate([(start + offsets) % n for start in starts])[:n]
        estimates[i] = values[indices].mean()
    return [float(value) for value in np.quantile(estimates, [0.025, 0.975])]


def _adaptive_test_predictions(
    X: np.ndarray,
    y: np.ndarray,
    prediction_time: np.ndarray,
    label_available_time: np.ndarray,
    split: np.ndarray,
    test_indices: np.ndarray,
    *,
    update_period: int = 50,
    max_training_rows: int = 2400,
) -> tuple[np.ndarray, list[dict]]:
    """Refit at fixed batch boundaries using only labels strictly arrived by that time."""
    if update_period < 1 or max_training_rows < 20:
        raise ValueError("update_period must be positive and max_training_rows at least 20")
    ordered = test_indices[np.argsort(prediction_time[test_indices], kind="stable")]
    prediction = np.full(len(ordered), np.nan)
    audit = []
    for start in range(0, len(ordered), update_period):
        block = ordered[start : start + update_period]
        now = float(prediction_time[block[0]])
        eligible = (
            np.isin(split, ["train", "test"])
            & (prediction_time < now)
            & np.isfinite(label_available_time)
            & (label_available_time < now)
            & np.isfinite(y)
        )
        fit_indices = np.flatnonzero(eligible)
        if len(fit_indices) > max_training_rows:
            latest = np.argsort(prediction_time[fit_indices], kind="stable")[-max_training_rows:]
            fit_indices = fit_indices[latest]
        if len(fit_indices) < 20:
            raise ValueError(f"Too few strictly arrived labels before adaptive fit at {now}")
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
        model.fit(X[fit_indices], y[fit_indices])
        prediction[start : start + len(block)] = model.predict(X[block])
        audit.append(
            {
                "fit_time": now,
                "n_fit_rows": len(fit_indices),
                "max_label_available_time": float(np.max(label_available_time[fit_indices])),
                "fit_row_indices": fit_indices.tolist(),
            }
        )
    return prediction, audit


def evaluate() -> dict:
    seeds = (42, 43, 44, 45, 46)
    replicates = []
    presets = conformal_stress_catalogue(n=12000)
    for preset in presets:
        for seed in seeds:
            config = preset.config.model_copy(update={"seed": seed})
            generated = list(generate_chunks(config))
            frame = pd.concat([part[0] for part in generated], ignore_index=True)
            y = frame.target.to_numpy(dtype=float)
            X = np.stack(frame.features.to_numpy())
            prediction_time = frame.prediction_time.to_numpy(dtype=float)
            available = frame.label_available_time.to_numpy(dtype=float)
            split = frame.split.to_numpy()
            calibration_indices = np.flatnonzero(split == "calibration")
            test_indices = np.flatnonzero(split == "test")
            missing_test_labels = int(np.count_nonzero(~np.isfinite(y[test_indices])))
            if len(calibration_indices) == 0 or len(test_indices) == 0:
                raise ValueError(f"Missing calibration/test split for {preset.name}")
            first_test_time = float(np.min(prediction_time[test_indices]))
            first_calibration_time = float(np.min(prediction_time[calibration_indices]))
            train_indices = np.flatnonzero(
                (split == "train")
                & np.isfinite(y)
                & np.isfinite(available)
                & (available < first_calibration_time)
            )
            calibration_indices = calibration_indices[
                np.isfinite(y[calibration_indices]) & np.isfinite(available[calibration_indices])
            ]
            test_indices = test_indices[np.isfinite(y[test_indices])]
            if len(train_indices) < 20 or len(calibration_indices) < 20 or len(test_indices) < 20:
                raise ValueError(
                    f"Insufficient available labeled rows for {preset.name}, seed {seed}"
                )
            model = make_pipeline(
                SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0)
            )
            model.fit(X[train_indices], y[train_indices])
            calibration_prediction = model.predict(X[calibration_indices])
            calibration_residual = np.abs(y[calibration_indices] - calibration_prediction)
            calibration_prediction_time = prediction_time[calibration_indices]
            calibration_available = available[calibration_indices]
            initially_available = np.isfinite(calibration_available) & (
                calibration_available < first_test_time
            )
            if initially_available.sum() < 20:
                raise ValueError(
                    f"Too few arrived calibration scores for {preset.name}, seed {seed}"
                )
            fixed_radius = weighted_conformal_quantile(calibration_residual[initially_available])

            test_indices = test_indices[np.argsort(prediction_time[test_indices], kind="stable")]
            test_prediction = model.predict(X[test_indices])
            test_residual = np.abs(y[test_indices] - test_prediction)
            test_prediction_time = prediction_time[test_indices]
            test_available = available[test_indices]
            online_radius = np.full(len(test_indices), np.nan)
            score_counts = np.zeros(len(test_indices), dtype=int)
            for i, now in enumerate(test_prediction_time):
                scores = _arrived_prior_scores(
                    now,
                    calibration_residual,
                    calibration_prediction_time,
                    calibration_available,
                    test_residual[:i],
                    test_prediction_time[:i],
                    test_available[:i],
                )
                score_counts[i] = len(scores)
                if len(scores) >= 20:
                    online_radius[i] = weighted_conformal_quantile(scores)

            adaptive_prediction, adaptive_fit_audit = _adaptive_test_predictions(
                X,
                y,
                prediction_time,
                available,
                split,
                test_indices,
                update_period=50,
                max_training_rows=2400,
            )
            adaptive_residual = np.abs(y[test_indices] - adaptive_prediction)
            adaptive_radius = np.full(len(test_indices), np.nan)
            for i, now in enumerate(test_prediction_time):
                scores = _arrived_prior_scores(
                    now,
                    calibration_residual,
                    calibration_prediction_time,
                    calibration_available,
                    adaptive_residual[:i],
                    test_prediction_time[:i],
                    test_available[:i],
                )
                if len(scores) >= 20:
                    adaptive_radius[i] = weighted_conformal_quantile(scores)

            finite = np.isfinite(online_radius)
            adaptive_finite = np.isfinite(adaptive_radius)
            fixed_covered = test_residual <= fixed_radius
            online_covered = test_residual[finite] <= online_radius[finite]
            adaptive_covered = (
                adaptive_residual[adaptive_finite] <= adaptive_radius[adaptive_finite]
            )
            if finite.sum() < 20:
                raise ValueError(
                    f"Too few online-scored predictions for {preset.name}, seed {seed}"
                )
            block = max(2, int(np.sqrt(finite.sum())))
            block_2 = 2 * block
            replicates.append(
                {
                    "preset": preset.name,
                    "scenario": config.scenario,
                    "seed": seed,
                    "calibration_target_scope": preset.calibration_target_scope,
                    "n_train_available": len(train_indices),
                    "n_calibration_arrived_before_test": int(initially_available.sum()),
                    "n_test_labeled": len(test_indices),
                    "n_online_scored": int(finite.sum()),
                    "fixed_split_radius": float(fixed_radius),
                    "fixed_split_test_coverage": float(fixed_covered.mean()),
                    "prequential_test_coverage": float(online_covered.mean()),
                    "adaptive_predictor_prequential_test_coverage": float(adaptive_covered.mean()),
                    "frozen_predictor_prequential_mse": float(
                        np.mean(test_residual[adaptive_finite] ** 2)
                    ),
                    "adaptive_predictor_prequential_mse": float(
                        np.mean(adaptive_residual[adaptive_finite] ** 2)
                    ),
                    "adaptive_predictor_update_period": 50,
                    "adaptive_predictor_max_training_rows": 2400,
                    "adaptive_predictor_refit_count": len(adaptive_fit_audit),
                    "adaptive_predictor_min_fit_rows": min(
                        row["n_fit_rows"] for row in adaptive_fit_audit
                    ),
                    "adaptive_predictor_min_availability_margin": float(
                        min(
                            row["fit_time"] - row["max_label_available_time"]
                            for row in adaptive_fit_audit
                        )
                    ),
                    "adaptive_predictor_coverage_block_length": block,
                    "adaptive_predictor_coverage_moving_block_95pct_interval": _block_interval(
                        adaptive_covered.astype(float), block, seed + 1700
                    ),
                    "adaptive_predictor_coverage_2x_block_moving_block_95pct_interval": _block_interval(
                        adaptive_covered.astype(float), block_2, seed + 1900
                    ),
                    "prequential_median_radius": float(np.median(online_radius[finite])),
                    "prequential_mean_radius": float(np.mean(online_radius[finite])),
                    "mean_online_score_count": float(score_counts[finite].mean()),
                    "prequential_coverage_block_length": block,
                    "prequential_coverage_moving_block_95pct_interval": _block_interval(
                        online_covered.astype(float), block, seed + 700
                    ),
                    "prequential_coverage_2x_block_moving_block_95pct_interval": _block_interval(
                        online_covered.astype(float), block_2, seed + 900
                    ),
                    "predictor": "baseline: frozen train-only Ridge; adaptive arm: refit every 50 test requests on at most the latest 2400 train/prior-test rows whose labels strictly arrived before each batch",
                    "radius_update": "after each prediction, its absolute residual joins the score pool only when label_available_time is strictly before a later prediction_time",
                    "missing_test_labels": missing_test_labels,
                }
            )
    replication_check = replicate_grid_integrity(
        replicates, [preset.name for preset in presets], seeds
    )
    coverage_fields = [
        "fixed_split_test_coverage",
        "prequential_test_coverage",
        "adaptive_predictor_prequential_test_coverage",
    ]
    metric_rows_valid = all(
        row["n_test_labeled"] >= 20
        and row["n_online_scored"] >= 20
        and all(np.isfinite(row[field]) and 0 <= row[field] <= 1 for field in coverage_fields)
        and np.isfinite(row["frozen_predictor_prequential_mse"])
        and row["frozen_predictor_prequential_mse"] >= 0
        and np.isfinite(row["adaptive_predictor_prequential_mse"])
        and row["adaptive_predictor_prequential_mse"] >= 0
        and np.isfinite(row["prequential_mean_radius"])
        and row["prequential_mean_radius"] >= 0
        for row in replicates
    )
    leakage_rows_valid = all(
        row["n_train_available"] >= 20
        and row["n_calibration_arrived_before_test"] >= 20
        and row["adaptive_predictor_refit_count"] > 0
        and row["adaptive_predictor_min_fit_rows"] >= 20
        and row["adaptive_predictor_min_availability_margin"] > 0
        for row in replicates
    )
    return {
        "protocol": "Five-seed comparison of a frozen fitted Ridge predictor and a Ridge predictor refit every 50 test requests on a rolling window capped at the latest 2400 eligible rows. At each refit, only train and earlier test labels whose availability precedes the block's first request are eligible. Calibration labels are held out from refitting; the prequential radius uses calibration and prior test scores that arrived before each request.",
        "alpha": 0.1,
        "coverage_target": 0.9,
        "replication_check": replication_check,
        "metric_rows_valid": metric_rows_valid,
        "leakage_rows_valid": leakage_rows_valid,
        "checks_pass": replication_check["passes"] and metric_rows_valid and leakage_rows_valid,
        "replicates": replicates,
        "by_preset": [
            {
                "preset": name,
                "replicates": len(rows),
                "mean_fixed_split_test_coverage": float(
                    np.mean([row["fixed_split_test_coverage"] for row in rows])
                ),
                "mean_prequential_test_coverage": float(
                    np.mean([row["prequential_test_coverage"] for row in rows])
                ),
                "mean_adaptive_predictor_prequential_test_coverage": float(
                    np.mean([row["adaptive_predictor_prequential_test_coverage"] for row in rows])
                ),
                "mean_adaptive_predictor_prequential_mse": float(
                    np.mean([row["adaptive_predictor_prequential_mse"] for row in rows])
                ),
                "mean_frozen_predictor_prequential_mse": float(
                    np.mean([row["frozen_predictor_prequential_mse"] for row in rows])
                ),
                "mean_prequential_radius": float(
                    np.mean([row["prequential_mean_radius"] for row in rows])
                ),
            }
            for name in sorted({row["preset"] for row in replicates})
            for rows in [[row for row in replicates if row["preset"] == name]]
        ],
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "The frozen baseline adapts only its residual quantile; the adaptive arm refits Ridge every 50 test requests on at most 2400 recent arrived train/test labels.",
            "The adaptive arm uses past test labels only after strict availability; calibration rows remain held out from model fitting.",
            "Adaptive prequential residuals come from a sequence of batch-frozen predictors; coverage is empirical and no finite-sample guarantee is claimed.",
            "Prequential residual quantiles under serial dependence or changing distributions do not have a finite-sample coverage guarantee.",
            "Moving-block intervals use sqrt(n) and 2*sqrt(n) row blocks; these are sensitivity diagnostics, not guaranteed confidence intervals under arbitrary drift.",
            "Five-seed averages are descriptive and are not pooled as IID observations.",
            "Rows with missing outcomes do not enter coverage; calibration residuals must have arrived before they are used.",
        ],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = evaluate()
    output = root / "data/reports/fitted_conformal_validation.json"
    write_json(output, result)
    for row in result["by_preset"]:
        print(
            f"{row['preset']}: split={row['mean_fixed_split_test_coverage']:.3f} "
            f"frozen={row['mean_prequential_test_coverage']:.3f} "
            f"adaptive={row['mean_adaptive_predictor_prequential_test_coverage']:.3f} "
            f"mse={row['mean_frozen_predictor_prequential_mse']:.3f}->"
            f"{row['mean_adaptive_predictor_prequential_mse']:.3f} "
            f"radius={row['mean_prequential_radius']:.3f}"
        )
    print("data/reports/fitted_conformal_validation.json")
    if not result["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
