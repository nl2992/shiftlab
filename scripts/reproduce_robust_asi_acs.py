"""Reproduce the Robust ASI California ACS income-regression task."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
from sklearn.preprocessing import OneHotEncoder

from shiftlab.dive.robust_asi_fixed_horizon import (
    budgeted_probabilities,
    choose_robust_geometric_path,
)

if TYPE_CHECKING:
    from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/raw/folktables/2019/1-Year/csv_pca.zip"
DEFAULT_PROTOCOL = ROOT / "papers/shiftguard_unified/robust_asi_acs_reproduction_protocol.md"
FEATURES = [
    "AGEP",
    "SCHL",
    "MAR",
    "DIS",
    "ESP",
    "CIT",
    "MIG",
    "MIL",
    "ANC1P",
    "NATIVITY",
    "DEAR",
    "DEYE",
    "DREM",
    "SEX",
    "RAC1P",
    "SOCP",
    "COW",
]
NUMERIC_FEATURES = ("AGEP", "SCHL")
TARGET = "PINCP"
EXPECTED_RECEIPT_URL = (
    "https://www2.census.gov/programs-surveys/acs/data/pums/2019/1-Year/csv_pca.zip"
)
DEFAULT_C_VALUES = (0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0)
CONFIDENCE_ALPHA = 0.10


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_sample(
    data_path: Path, n_sample: int, seed: int
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    required = [*FEATURES, TARGET]
    with zipfile.ZipFile(data_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"expected one PUMS CSV member, found {members}")
        with archive.open(members[0]) as stream:
            frame = pd.read_csv(stream, usecols=required)
    if len(frame) < n_sample:
        raise ValueError(f"requested {n_sample} rows but source has {len(frame)}")
    rng = np.random.default_rng(seed)
    selected = rng.permutation(len(frame))[:n_sample]
    sample = frame.iloc[selected].reset_index(drop=True)
    feature_frame = sample.loc[:, FEATURES].fillna(-1)
    outcome = sample[TARGET].fillna(-1).to_numpy(dtype=np.float64)
    design = sample.loc[:, ["AGEP", "SEX"]].fillna(-1).to_numpy(dtype=np.float64)
    return feature_frame, outcome, design


def _encode_features(frame: pd.DataFrame) -> sp.csr_matrix:
    numeric = sp.csr_matrix(frame.loc[:, NUMERIC_FEATURES].to_numpy(dtype=np.float32))
    categorical_fields = [field for field in FEATURES if field not in NUMERIC_FEATURES]
    categorical = frame.loc[:, categorical_fields].astype(str)
    encoder = OneHotEncoder(handle_unknown="ignore", drop="if_binary", sparse_output=True)
    encoded = encoder.fit_transform(categorical)
    return sp.hstack((numeric, encoded), format="csr", dtype=np.float32)


def _make_model(
    *,
    device: str,
    seed: int,
    trees: int,
    depth: int,
    learning_rate: float,
    objective: str,
) -> XGBRegressor:
    from xgboost import XGBRegressor

    return cast(
        "XGBRegressor",
        XGBRegressor(
            objective=objective,
            n_estimators=trees,
            max_depth=depth,
            learning_rate=learning_rate,
            tree_method="hist",
            device=device,
            random_state=seed,
            n_jobs=1,
            verbosity=0,
        ),
    )


def _fit_residual_scale(
    *,
    x_error: np.ndarray,
    residuals: np.ndarray,
    x_predict: np.ndarray,
    device: str,
    seed: int,
    error_trees: int,
) -> np.ndarray:
    model = _make_model(
        device=device,
        seed=seed,
        trees=error_trees,
        depth=20,
        learning_rate=0.1,
        objective="reg:squarederror",
    )
    model.fit(x_error, residuals)
    return np.maximum(model.predict(x_predict), 0.0)


def _influence_scale(
    predicted_absolute_error: np.ndarray, design: np.ndarray, h: np.ndarray
) -> np.ndarray:
    # Preserve the target-coordinate score used by Robust ASI. Its scale is
    # arbitrary after propensity normalization; clipping at one can collapse
    # heterogeneous scores to a constant and silently make active sampling
    # identical to uniform sampling.
    scale = np.abs(design @ h) * np.abs(predicted_absolute_error)
    if not np.isfinite(scale).all():
        raise ValueError("influence scale must be finite")
    return scale


def _evaluate_trials(
    *,
    design: np.ndarray,
    known_burnin_design: np.ndarray,
    known_burnin_y: np.ndarray,
    predicted_y: np.ndarray,
    hidden_y: np.ndarray,
    probabilities: np.ndarray,
    uniforms: torch.Tensor,
    true_theta: float,
    alpha: float,
    device: str,
) -> dict[str, np.ndarray]:
    design_t = torch.as_tensor(design, dtype=torch.float64, device=device)
    burnin_t = torch.as_tensor(known_burnin_y, dtype=torch.float64, device=device)
    prediction_t = torch.as_tensor(predicted_y, dtype=torch.float64, device=device)
    hidden_t = torch.as_tensor(hidden_y, dtype=torch.float64, device=device)
    q_t = torch.as_tensor(probabilities, dtype=torch.float64, device=device)
    query_t = uniforms < q_t.unsqueeze(0)
    pseudo_t = prediction_t.unsqueeze(0) + query_t * (
        hidden_t.unsqueeze(0) - prediction_t.unsqueeze(0)
    ) / q_t.unsqueeze(0)
    n_pool = design_t.shape[0]
    n_burn = burnin_t.numel()
    n_total = n_pool + n_burn
    estimator_y = torch.cat(
        (
            pseudo_t,
            burnin_t.unsqueeze(0).expand(pseudo_t.shape[0], -1),
        ),
        dim=1,
    )
    burn_design = torch.as_tensor(known_burnin_design, dtype=torch.float64, device=device)
    if burn_design.shape != (n_burn, design_t.shape[1]):
        raise ValueError("known burn-in design and labels must align")
    full_design = torch.cat((design_t, burn_design), dim=0)
    gram_inverse = torch.linalg.inv(full_design.T @ full_design)
    hessian_inverse = gram_inverse * n_total
    beta = gram_inverse @ (full_design.T @ estimator_y.T)
    residual = full_design @ beta - estimator_y.T
    gradients = residual.unsqueeze(-1) * full_design.unsqueeze(1)
    centered = gradients - gradients.mean(dim=0, keepdim=True)
    covariance = torch.einsum("nbp,nbq->bpq", centered, centered) / (n_total - 1)
    sandwich = torch.einsum("ij,bjk,kl->bil", hessian_inverse, covariance, hessian_inverse)
    standard_error = torch.sqrt(torch.clamp(sandwich[:, 0, 0] / n_total, min=0.0))
    point = beta[0]
    critical = float(torch.distributions.Normal(0.0, 1.0).icdf(torch.tensor(1.0 - alpha / 2.0)))
    radius = critical * standard_error
    queries = query_t.sum(dim=1)
    return {
        "estimate": point.cpu().numpy(),
        "standard_error": standard_error.cpu().numpy(),
        "lower": (point - radius).cpu().numpy(),
        "upper": (point + radius).cpu().numpy(),
        "covered": ((point - radius <= true_theta) & (true_theta <= point + radius)).cpu().numpy(),
        "labels_queried": queries.cpu().numpy(),
    }


def _trial_stderrs(
    *,
    design: np.ndarray,
    known_y: np.ndarray,
    predicted_y: np.ndarray,
    hidden_y: np.ndarray,
    q: np.ndarray,
    uniforms: torch.Tensor,
    device: str,
) -> np.ndarray:
    dummy = _evaluate_trials(
        design=design,
        known_burnin_design=np.empty((0, design.shape[1]), dtype=np.float64),
        known_burnin_y=known_y,
        predicted_y=predicted_y,
        hidden_y=hidden_y,
        probabilities=q,
        uniforms=uniforms,
        true_theta=0.0,
        alpha=CONFIDENCE_ALPHA,
        device=device,
    )
    return dummy["standard_error"]


def _cross_validate_radius(
    *,
    burn_design: np.ndarray,
    burn_y: np.ndarray,
    burn_predicted_y: np.ndarray,
    h: np.ndarray,
    budget_rates: list[float],
    c_values: tuple[float, ...],
    folds: int,
    trials: int,
    error_trees: int,
    seed: int,
    device: str,
) -> list[dict[str, object]]:
    fold_ids = np.array_split(np.arange(len(burn_y)), folds)
    selections: list[dict[str, object]] = []
    for budget_index, budget_rate in enumerate(budget_rates):
        fold_errors_by_c: dict[float, list[float]] = {c_value: [] for c_value in c_values}
        for fold_index, test_indices in enumerate(fold_ids):
            train_indices = np.setdiff1d(np.arange(len(burn_y)), test_indices, assume_unique=True)
            residual_train = np.abs(burn_y[train_indices] - burn_predicted_y[train_indices])
            predicted_error = _fit_residual_scale(
                x_error=burn_design[train_indices],
                residuals=residual_train,
                x_predict=burn_design[test_indices],
                device=device,
                seed=seed + 10_000 + budget_index * 100 + fold_index,
                error_trees=error_trees,
            )
            fold_design = burn_design[test_indices]
            scale = _influence_scale(predicted_error, fold_design, h)
            fold_budget = max(1e-6, budget_rate * len(test_indices))
            # Each fold-level residual fit and query stream is shared across
            # candidate radii; neither depends on the radius value.
            generator = torch.Generator(device=device).manual_seed(
                seed + 20_000 + budget_index * 100 + fold_index
            )
            uniforms = torch.rand((trials, len(test_indices)), generator=generator, device=device)
            for c_value in c_values:
                q, _, _ = choose_robust_geometric_path(
                    scale,
                    budget=fold_budget,
                    l2_radius=c_value * np.sqrt(len(test_indices)),
                    path_grid=tuple(np.linspace(0.0, 1.0, 101)),
                )
                stderrs = _trial_stderrs(
                    design=fold_design,
                    known_y=np.empty(0, dtype=np.float64),
                    predicted_y=burn_predicted_y[test_indices],
                    hidden_y=burn_y[test_indices],
                    q=q,
                    uniforms=uniforms,
                    device=device,
                )
                fold_errors_by_c[c_value].append(float(stderrs.mean()))
        candidates = [
            (float(np.mean(fold_errors)), c_value)
            for c_value, fold_errors in fold_errors_by_c.items()
        ]
        cv_score, selected_c = min(candidates)
        selections.append(
            {
                "budget_rate": budget_rate,
                "selected_c": selected_c,
                "cross_validated_mean_standard_error": cv_score,
                "candidate_scores": [
                    {"c": value, "mean_standard_error": score}
                    for score, value in sorted(candidates, key=lambda item: item[1])
                ],
            }
        )
    return selections


def run(args: argparse.Namespace) -> Path:
    data_path = args.data.resolve()
    output = args.output.resolve()
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = data_path.with_suffix(data_path.suffix + ".receipt.json")
    if not receipt_path.is_file():
        raise FileNotFoundError(f"missing source receipt: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("url") != EXPECTED_RECEIPT_URL:
        raise ValueError("ACS source receipt URL does not match the frozen California 2019 source")
    if receipt.get("sha256") != _sha256(data_path):
        raise ValueError("ACS source receipt SHA-256 does not match the local archive")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = args.device

    features, outcome, regression_design = _load_sample(data_path, args.n_sample, args.seed)
    encoded_features = _encode_features(features)
    permutation = np.random.default_rng(args.seed + 1).permutation(args.n_sample)
    n_train = int(args.train_fraction * args.n_sample)
    train_indices = permutation[:n_train]
    inference_indices = permutation[n_train:]
    n_burn = int(args.burnin_fraction * len(inference_indices))
    inference_permutation = np.random.default_rng(args.seed + 2).permutation(len(inference_indices))
    burn_indices = inference_indices[inference_permutation[:n_burn]]
    pool_indices = inference_indices[inference_permutation[n_burn:]]

    target_regression_design = regression_design
    true_theta = float(np.linalg.lstsq(target_regression_design, outcome, rcond=None)[0][0])
    base_model = _make_model(
        device=device,
        seed=args.seed,
        trees=args.base_trees,
        depth=7,
        learning_rate=0.3,
        objective="reg:absoluteerror",
    )
    base_model.fit(encoded_features[train_indices], outcome[train_indices], verbose=False)
    pred_burn = np.asarray(base_model.predict(encoded_features[burn_indices]), dtype=np.float64)
    pred_pool = np.asarray(base_model.predict(encoded_features[pool_indices]), dtype=np.float64)
    burn_design = regression_design[burn_indices]
    pool_design = regression_design[pool_indices]
    full_inference_design = np.vstack((pool_design, burn_design))
    n_inference = len(full_inference_design)
    hessian_inverse = np.linalg.inv(full_inference_design.T @ full_inference_design / n_inference)
    h = hessian_inverse[:, 0]
    burn_residual = np.abs(outcome[burn_indices] - pred_burn)

    n_pool = len(pool_indices)
    budget_rates = np.linspace(args.min_budget_rate, args.max_budget_rate, args.budget_count)
    budgets = [max(1, round(rate * n_pool)) for rate in budget_rates]
    c_values = tuple(args.c_values)
    radius_selections = _cross_validate_radius(
        burn_design=burn_design,
        burn_y=outcome[burn_indices],
        burn_predicted_y=pred_burn,
        h=h,
        budget_rates=[float(rate) for rate in budget_rates],
        c_values=c_values,
        folds=args.cv_folds,
        trials=args.cv_trials,
        error_trees=args.error_trees,
        seed=args.seed,
        device=device,
    )
    predicted_error = _fit_residual_scale(
        x_error=burn_design,
        residuals=burn_residual,
        x_predict=pool_design,
        device=device,
        seed=args.seed + 30_000,
        error_trees=args.error_trees,
    )
    scale = _influence_scale(predicted_error, pool_design, h)
    pool_y = outcome[pool_indices]
    burn_y = outcome[burn_indices]
    methods: list[dict[str, object]] = []
    for budget_index, budget in enumerate(budgets):
        budget = min(max(1, budget), n_pool)
        c_value = float(cast(float, radius_selections[budget_index]["selected_c"]))
        uniform_q = np.full(n_pool, budget / n_pool)
        active_q = budgeted_probabilities(scale, budget=float(budget))
        robust_q, selected_rho, robust_objective = choose_robust_geometric_path(
            scale,
            budget=float(budget),
            l2_radius=c_value * np.sqrt(n_pool),
            path_grid=tuple(np.linspace(0.0, 1.0, 101)),
        )
        generator = torch.Generator(device=device).manual_seed(args.seed + 40_000 + budget_index)
        uniforms = torch.rand((args.trials, n_pool), generator=generator, device=device)
        for method, propensities in (
            ("uniform", uniform_q),
            ("active", active_q),
            ("robust_active", robust_q),
        ):
            result = _evaluate_trials(
                design=pool_design,
                known_burnin_design=burn_design,
                known_burnin_y=burn_y,
                predicted_y=pred_pool,
                hidden_y=pool_y,
                probabilities=propensities,
                uniforms=uniforms,
                true_theta=true_theta,
                alpha=CONFIDENCE_ALPHA,
                device=device,
            )
            for trial in range(args.trials):
                methods.append(
                    {
                        "seed": args.seed,
                        "budget_rate": budget / n_pool,
                        "budget_requested": budget,
                        "budget_index": budget_index,
                        "method": method,
                        "trial": trial,
                        "true_theta": true_theta,
                        "estimate": float(result["estimate"][trial]),
                        "standard_error": float(result["standard_error"][trial]),
                        "ci_lower": float(result["lower"][trial]),
                        "ci_upper": float(result["upper"][trial]),
                        "covered": bool(result["covered"][trial]),
                        "labels_queried": int(result["labels_queried"][trial]),
                        "expected_pool_labels": float(propensities.sum()),
                        "expected_total_labeled_including_training_burnin": float(
                            n_train + n_burn + propensities.sum()
                        ),
                        "selected_c": c_value,
                        "selected_rho": selected_rho if method == "robust_active" else np.nan,
                        "robust_objective": robust_objective
                        if method == "robust_active"
                        else np.nan,
                        "min_propensity": float(propensities.min()),
                        "max_propensity": float(propensities.max()),
                    }
                )
    detail = pd.DataFrame(methods)
    output_parquet = output / "robust_asi_acs_trials.parquet"
    detail.to_parquet(output_parquet, index=False)
    detail["error"] = detail["estimate"] - detail["true_theta"]
    summary = detail.groupby(["budget_index", "budget_rate", "method"], as_index=False).agg(
        trials=("trial", "count"),
        bias=("error", "mean"),
        rmse=("error", lambda values: float(np.sqrt(np.mean(np.square(values))))),
        mean_interval_width=("ci_lower", lambda lower: float("nan")),
        empirical_90_coverage=("covered", "mean"),
        mean_expected_pool_labels=("expected_pool_labels", "mean"),
        mean_realized_pool_labels=("labels_queried", "mean"),
        selected_c=("selected_c", "first"),
        selected_rho=("selected_rho", "first"),
    )
    widths = (
        detail.assign(interval_width=detail.ci_upper - detail.ci_lower)
        .groupby(["budget_index", "budget_rate", "method"], as_index=False)["interval_width"]
        .mean()
    )
    summary = summary.drop(columns="mean_interval_width").merge(
        widths.rename(columns={"interval_width": "mean_interval_width"}),
        on=["budget_index", "budget_rate", "method"],
        validate="one_to_one",
    )
    summary_path = output / "robust_asi_acs_summary.csv"
    summary.to_csv(summary_path, index=False)
    protocol_snapshot = output / "protocol_snapshot.md"
    protocol_snapshot.write_bytes(DEFAULT_PROTOCOL.read_bytes())
    source_paths = [
        Path(__file__).resolve(),
        ROOT / "src/shiftlab/dive/robust_asi_fixed_horizon.py",
        DEFAULT_PROTOCOL,
    ]
    source_hashes = {str(path.relative_to(ROOT)): _sha256(path) for path in source_paths}
    manifest = {
        "experiment": "robust_asi_acs_income_regression_reproduction",
        "status": "reproduction_run_single_sample_monte_carlo",
        "created_utc": datetime.now(UTC).isoformat(),
        "data": {
            "path": str(data_path.relative_to(ROOT)),
            "source_url": receipt["url"],
            "bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
            "receipt_sha256": receipt["sha256"],
            "sample_rows": args.n_sample,
            "base_model_training_rows": n_train,
            "burnin_rows": n_burn,
            "inference_pool_rows": n_pool,
            "feature_names": FEATURES,
            "target": TARGET,
            "regression_design": ["AGEP", "SEX"],
            "survey_weights_used": False,
            "true_theta_evaluator_only": true_theta,
        },
        "configuration": {
            "seed": args.seed,
            "device": device,
            "base_model_trees": args.base_trees,
            "base_model_depth": 7,
            "base_model_learning_rate": 0.3,
            "base_model_objective": "reg:absoluteerror",
            "error_model_trees": args.error_trees,
            "error_model_depth": 20,
            "error_model_learning_rate": 0.1,
            "budget_rates": budget_rates.tolist(),
            "rounded_pool_budgets": budgets,
            "c_values": c_values,
            "cv_folds": args.cv_folds,
            "cv_trials": args.cv_trials,
            "evaluation_trials": args.trials,
            "confidence_level": 1.0 - CONFIDENCE_ALPHA,
            "propensity_floor": 1e-8,
            "query_uniforms_shared_across_methods": True,
            "xgboost_version": __import__("xgboost").__version__,
            "torch_version": torch.__version__,
            "cuda_name": torch.cuda.get_device_name(0) if device == "cuda" else None,
        },
        "radius_selection": radius_selections,
        "source_sha256": source_hashes,
        "artifacts_sha256": {
            output_parquet.name: _sha256(output_parquet),
            summary_path.name: _sha256(summary_path),
            "protocol_snapshot.md": _sha256(protocol_snapshot),
        },
        "deviations": [
            "Seeded data subset and splits are frozen here; the authors' notebook leaves its random split unseeded.",
            "Active and geometric-path propensities are exactly normalized to the requested expected budget, with a 1e-8 positive support floor.",
            "Robust-radius candidate values follow the authors' code convention: the Euclidean L2 radius is c * sqrt(n).",
            "This is one sampled ACS task instance with repeated query trials, not independent source-sample replications.",
        ],
        "limits": [
            "Survey weights are not applied; this reproduces the notebook's unweighted OLS task, not population-level ACS inference.",
            "Sandwich intervals are asymptotic and empirically evaluated at 90% coverage; no finite-sample coverage guarantee is claimed.",
            "The method is fixed-horizon and does not provide sequential monitoring, decision-harm, or intervention guarantees.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {output_parquet.relative_to(ROOT).as_posix()}")
    return output_parquet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--n-sample", type=int, default=20_000)
    parser.add_argument("--train-fraction", type=float, default=0.30)
    parser.add_argument("--burnin-fraction", type=float, default=0.03)
    parser.add_argument("--min-budget-rate", type=float, default=0.05)
    parser.add_argument("--max-budget-rate", type=float, default=0.20)
    parser.add_argument("--budget-count", type=int, default=10)
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--cv-trials", type=int, default=200)
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--base-trees", type=int, default=2000)
    parser.add_argument("--error-trees", type=int, default=200)
    parser.add_argument("--c-values", type=float, nargs="+", default=list(DEFAULT_C_VALUES))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
