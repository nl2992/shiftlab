"""Exploratory EIA cost-frontier evaluation of an independent UPF implementation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset
from shiftlab.dive.upf_retraining import (
    PerformanceObservation,
    fit_available_performance_forecaster,
    upf_retraining_schedule,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/upf_eia_development_protocol_v2.md"
DATASET_VERSION = "e47bdef8b208f8e7d788"
N_PERIODS = 15
N_OFFLINE = 7
ONLINE_START = N_OFFLINE
N_ALPHA_POINTS = 10
LABEL_DELAYS_HOURS = (0, 168)
RIDGE_ALPHA = 1.0
UPF_QUANTILE = 0.95
MONTE_CARLO_DRAWS = 10_000
SEED = 2026102701
METHODS = ("never", "always", "periodic_2", "periodic_4", "error_threshold", "upf", "oracle")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fit_ridge(x: np.ndarray, y: np.ndarray, device: torch.device) -> dict[str, Any]:
    if x.ndim != 2 or x.shape[1] != 4 or len(x) != len(y) or len(y) < 20:
        raise ValueError("EIA Ridge fit requires at least 20 matching four-feature rows")
    if np.isinf(x).any() or not np.isfinite(y).all():
        raise ValueError("Ridge training features cannot be infinite; targets must be finite")
    if np.any(np.isfinite(x).sum(axis=0) == 0):
        raise ValueError("Each EIA feature requires at least one observed training value")
    median = np.nanmedian(x, axis=0)
    imputed = np.where(np.isnan(x), median, x)
    mean = imputed.mean(axis=0, dtype=np.float64)
    scale = imputed.std(axis=0, dtype=np.float64)
    scale[scale < 1e-12] = 1.0
    standardized = (imputed - mean) / scale
    target_mean = float(y.mean())
    tx = torch.as_tensor(standardized, dtype=torch.float64, device=device)
    ty = torch.as_tensor(y - target_mean, dtype=torch.float64, device=device)
    coefficient = torch.linalg.solve(
        tx.T @ tx + RIDGE_ALPHA * torch.eye(4, dtype=torch.float64, device=device),
        tx.T @ ty,
    )
    if not torch.isfinite(coefficient).all():
        raise FloatingPointError("Ridge solve returned nonfinite coefficients")
    return {
        "mean": mean,
        "scale": scale,
        "median": median,
        "coefficient": coefficient.detach().cpu().numpy(),
        "intercept": target_mean,
    }


def _predict(model: dict[str, Any], x: np.ndarray) -> np.ndarray:
    if np.isinf(x).any():
        raise ValueError("prediction features cannot contain infinity")
    imputed = np.where(np.isnan(x), model["median"], x)
    standardized = (imputed - model["mean"]) / model["scale"]
    prediction = standardized @ model["coefficient"] + model["intercept"]
    if not np.isfinite(prediction).all():
        raise FloatingPointError("Ridge prediction returned nonfinite values")
    return prediction


def _score(
    y: np.ndarray,
    prediction: np.ndarray,
    *,
    scale: float,
) -> dict[str, float | int]:
    error = np.abs(y - prediction)
    bounded = np.minimum(error / scale, 1.0)
    return {
        "n": len(y),
        "bounded_loss": float(bounded.mean()),
        "mae": float(error.mean()),
        "rmse": float(np.sqrt(np.square(y - prediction).mean())),
        "clipped_fraction": float(np.mean(error >= scale)),
    }


def _exact_oracle(
    performance: np.ndarray,
    *,
    alpha: float,
    initial_model: int,
) -> tuple[tuple[bool, ...], float]:
    """Enumerate online updates after the initial model's training period."""
    first_decision_period = initial_model + 1
    horizon = performance.shape[0] - first_decision_period
    best_cost = math.inf
    best_schedule: tuple[bool, ...] = ()
    for mask in range(1 << horizon):
        schedule = tuple(bool(mask & (1 << index)) for index in range(horizon))
        model_index = initial_model
        total = 0.0
        for offset, retrain in enumerate(schedule):
            period = first_decision_period + offset
            if retrain:
                model_index = period
                total += alpha
            total += performance[model_index, period]
        if total < best_cost:
            best_cost = total
            best_schedule = schedule
    return best_schedule, best_cost


def _alpha_frontier(performance: np.ndarray) -> tuple[float, np.ndarray]:
    initial_model = ONLINE_START - 1
    base_loss = float(
        sum(performance[initial_model, period] for period in range(ONLINE_START, N_PERIODS))
    )
    break_even: list[float] = []
    horizon = N_PERIODS - ONLINE_START
    for mask in range(1, 1 << horizon):
        schedule = tuple(bool(mask & (1 << index)) for index in range(horizon))
        model_index = initial_model
        loss = 0.0
        count = 0
        for offset, retrain in enumerate(schedule):
            period = ONLINE_START + offset
            if retrain:
                model_index = period
                count += 1
            loss += performance[model_index, period]
        if count:
            break_even.append((base_loss - loss) / count)
    alpha_max = max(0.0, max(break_even, default=0.0))
    return alpha_max, np.linspace(0.0, alpha_max, N_ALPHA_POINTS, dtype=np.float64)


def _period_data(group: pd.DataFrame) -> dict[str, Any]:
    frame = group.sort_values("event_time", kind="stable").reset_index(drop=True)
    event = frame.event_time.to_numpy(dtype=np.float64)
    label_event = frame.label_event_time.to_numpy(dtype=np.float64)
    x = np.stack(frame.features.to_numpy()).astype(np.float64, copy=False)
    y = frame.target.to_numpy(dtype=np.float64)
    if not np.isfinite(event).all() or np.isinf(x).any():
        raise ValueError("EIA event times must be finite and features cannot be infinite")
    if len(event) < N_PERIODS * 100 or np.any(np.diff(event) <= 0):
        raise ValueError("Each domain needs enough unique, strictly ordered EIA events")
    indices = np.array_split(np.arange(len(event), dtype=np.int64), N_PERIODS)
    prefixes: list[np.ndarray] = []
    evaluations: list[np.ndarray] = []
    for period_indices in indices:
        prefix_end = math.floor(0.8 * len(period_indices))
        if prefix_end < 20 or len(period_indices) - prefix_end < 20:
            raise ValueError("A period lacks enough prefix or held-out evaluation rows")
        prefixes.append(period_indices[:prefix_end])
        evaluations.append(period_indices[prefix_end:])

    shifts: list[float] = []
    previous_mean: np.ndarray | None = None
    for prefix in prefixes:
        current_mean = np.nanmean(x[prefix], axis=0, dtype=np.float64)
        if not np.isfinite(current_mean).all():
            raise ValueError("Every period prefix must have finite feature means")
        shifts.append(
            0.0 if previous_mean is None else float(np.abs(current_mean - previous_mean).sum())
        )
        previous_mean = current_mean

    return {
        "frame": frame,
        "event": event,
        "label_event": label_event,
        "x": x,
        "y": y,
        "prefixes": prefixes,
        "evaluations": evaluations,
        "shifts": np.asarray(shifts, dtype=np.float64),
    }


def _prepare_domain(
    data: dict[str, Any],
    *,
    delay_hours: int,
    device: torch.device,
) -> dict[str, Any]:
    event = data["event"]
    label_event = data["label_event"]
    x = data["x"]
    y = data["y"]
    delay_seconds = delay_hours * 3600
    model_rows: list[dict[str, Any]] = []
    models: list[dict[str, Any]] = []
    training_counts: list[int] = []
    fit_seconds: list[float] = []

    first_prefix = data["prefixes"][0]
    first_eval_time = event[data["evaluations"][0][0]]
    initial_eligible = (
        (event[first_prefix] < first_eval_time)
        & (label_event[first_prefix] + delay_seconds <= first_eval_time)
        & np.isfinite(y[first_prefix])
    )
    initial_targets = y[first_prefix][initial_eligible]
    if len(initial_targets) < 20:
        raise ValueError("Initial period has too few labels mature at evaluation start")
    target_median = float(np.median(initial_targets))
    loss_scale = float(1.4826 * np.median(np.abs(initial_targets - target_median)))
    loss_scale = max(loss_scale, 1e-6)

    for period in range(N_PERIODS):
        evaluation = data["evaluations"][period]
        evaluation_start = float(event[evaluation[0]])
        prefix_pool = np.arange(evaluation[0], dtype=np.int64)
        eligible = (
            (event[prefix_pool] < evaluation_start)
            & (label_event[prefix_pool] + delay_seconds <= evaluation_start)
            & np.isfinite(y[prefix_pool])
        )
        train_indices = prefix_pool[eligible]
        if len(train_indices) < 20:
            raise ValueError(f"Period {period} has too few mature training labels")
        started = time.perf_counter()
        model = _fit_ridge(x[train_indices], y[train_indices], device)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        fit_seconds.append(time.perf_counter() - started)
        models.append(model)
        training_counts.append(len(train_indices))
        model_rows.append(
            {
                "period": period,
                "evaluation_start_event_time": evaluation_start,
                "training_rows": len(train_indices),
                "fit_seconds": fit_seconds[-1],
                "training_target_maturity_cutoff_seconds": delay_seconds,
            }
        )

    performance = np.full((N_PERIODS, N_PERIODS), np.nan, dtype=np.float64)
    raw_metrics: dict[tuple[int, int], dict[str, float | int]] = {}
    for model_period in range(N_PERIODS):
        for evaluation_period in range(model_period, N_PERIODS):
            evaluation = data["evaluations"][evaluation_period]
            valid = np.isfinite(y[evaluation])
            evaluation_indices = evaluation[valid]
            prediction = _predict(models[model_period], x[evaluation_indices])
            score = _score(y[evaluation_indices], prediction, scale=loss_scale)
            performance[model_period, evaluation_period] = float(score["bounded_loss"])
            raw_metrics[(model_period, evaluation_period)] = score

    return {
        "models": models,
        "training_counts": training_counts,
        "fit_seconds": fit_seconds,
        "model_rows": model_rows,
        "performance": performance,
        "raw_metrics": raw_metrics,
        "loss_scale": loss_scale,
    }


def _offline_observations(
    performance: np.ndarray,
    shifts: np.ndarray,
) -> list[PerformanceObservation]:
    return [
        PerformanceObservation(
            training_period=model_period,
            evaluation_period=evaluation_period,
            feature_shift_l1=float(shifts[evaluation_period]),
            normalized_loss=float(performance[model_period, evaluation_period]),
            available_period=evaluation_period,
        )
        for model_period in range(N_OFFLINE)
        for evaluation_period in range(model_period, N_OFFLINE)
    ]


def _upf_first_action(
    observations: list[PerformanceObservation],
    *,
    incumbent_model: int,
    current_period: int,
    latest_shift: float,
    alpha: float,
    seed: int,
    device: torch.device,
) -> tuple[bool, float, int]:
    forecaster = fit_available_performance_forecaster(
        observations,
        max_available_period=current_period - 1,
        seed=seed,
    )
    horizon = N_PERIODS - current_period
    beta_alpha = np.ones((horizon + 1, horizon), dtype=np.float64)
    beta_beta = np.ones((horizon + 1, horizon), dtype=np.float64)
    feature_rows: list[list[float]] = []
    cells: list[tuple[int, int]] = []
    for local_time in range(1, horizon + 1):
        absolute_eval = current_period + local_time - 1
        for local_model in range(local_time + 1):
            absolute_model = (
                incumbent_model if local_model == 0 else current_period + local_model - 1
            )
            feature_rows.append(
                [
                    float(absolute_model),
                    float(absolute_eval),
                    float(absolute_eval - absolute_model),
                    latest_shift,
                ]
            )
            cells.append((local_model, local_time - 1))
    alpha_values, beta_values = forecaster.predict_beta_parameters(
        np.asarray(feature_rows, dtype=np.float64)
    )
    for (local_model, local_time), a_value, b_value in zip(
        cells, alpha_values, beta_values, strict=True
    ):
        beta_alpha[local_model, local_time] = a_value
        beta_beta[local_model, local_time] = b_value
    schedule, margins = upf_retraining_schedule(
        beta_alpha,
        beta_beta,
        retraining_cost=alpha,
        quantile=UPF_QUANTILE,
        monte_carlo_draws=MONTE_CARLO_DRAWS,
        seed=seed,
        device=device,
    )
    return bool(schedule[1, 0]), float(margins[1, 0]), forecaster.n_observations


def _run_policy(
    *,
    method: str,
    alpha: float,
    data: dict[str, Any],
    prepared: dict[str, Any],
    domain_index: int,
    delay_hours: int,
    device: torch.device,
) -> list[dict[str, Any]]:
    performance = prepared["performance"]
    metrics = prepared["raw_metrics"]
    shifts = data["shifts"]
    incumbent = N_OFFLINE - 1
    trained = set(range(N_OFFLINE))
    observations = _offline_observations(performance, shifts)
    offline_diagonal = np.asarray(
        [performance[index, index] for index in range(N_OFFLINE)], dtype=np.float64
    )
    error_threshold = float(np.quantile(offline_diagonal, 0.95))
    previous_active_loss: float | None = None
    rows: list[dict[str, Any]] = []

    oracle_schedule, _ = _exact_oracle(
        performance,
        alpha=alpha,
        initial_model=incumbent,
    )
    for period in range(ONLINE_START, N_PERIODS):
        retrain = False
        upf_margin = float("nan")
        forecaster_rows = 0
        if method == "always":
            retrain = True
        elif method == "periodic_2":
            retrain = (period - ONLINE_START + 1) % 2 == 0
        elif method == "periodic_4":
            retrain = (period - ONLINE_START + 1) % 4 == 0
        elif method == "error_threshold":
            retrain = previous_active_loss is not None and previous_active_loss > error_threshold
        elif method == "upf":
            retrain, upf_margin, forecaster_rows = _upf_first_action(
                observations,
                incumbent_model=incumbent,
                current_period=period,
                latest_shift=float(shifts[period]),
                alpha=alpha,
                seed=SEED
                + domain_index * 100_000
                + delay_hours * 1_000
                + int(alpha * 10**6)
                + period,
                device=device,
            )
        elif method == "oracle":
            retrain = oracle_schedule[period - ONLINE_START]
        elif method != "never":
            raise ValueError(f"unknown method {method}")

        if retrain:
            incumbent = period
            trained.add(period)
        active_score = metrics[(incumbent, period)]
        previous_active_loss = float(active_score["bounded_loss"])
        rows.append(
            {
                "domain_id": data["domain_id"],
                "delay_hours": delay_hours,
                "method": method,
                "alpha": alpha,
                "period": period,
                "retrained": retrain,
                "active_model_period": incumbent,
                "bounded_loss": float(active_score["bounded_loss"]),
                "mae": float(active_score["mae"]),
                "rmse": float(active_score["rmse"]),
                "clipped_fraction": float(active_score["clipped_fraction"]),
                "evaluation_rows": int(active_score["n"]),
                "upf_first_action_quantile_margin": upf_margin,
                "upf_forecaster_observations": forecaster_rows,
                "label_scale": prepared["loss_scale"],
                "error_trigger_threshold": error_threshold,
            }
        )
        # Feedback from this evaluation tail is available before the next period's
        # decision under both declared extra-delay assumptions.
        for model_period in sorted(trained):
            observations.append(
                PerformanceObservation(
                    training_period=model_period,
                    evaluation_period=period,
                    feature_shift_l1=float(shifts[period]),
                    normalized_loss=float(performance[model_period, period]),
                    available_period=period,
                )
            )
    return rows


def _summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    group_keys = ["domain_id", "delay_hours", "method", "alpha"]
    summary = metrics.groupby(group_keys, as_index=False).agg(
        cumulative_bounded_loss=("bounded_loss", "sum"),
        cumulative_mae=("mae", "sum"),
        cumulative_rmse=("rmse", "sum"),
        total_retrains=("retrained", "sum"),
        mean_clipped_fraction=("clipped_fraction", "mean"),
        total_evaluation_rows=("evaluation_rows", "sum"),
    )
    summary["total_cost"] = summary.cumulative_bounded_loss + summary.alpha * summary.total_retrains
    return summary


def _manifest_paths(output_dir: Path) -> dict[str, str]:
    relative = (
        "scripts/evaluate_upf_eia_frontier.py",
        "src/shiftlab/dive/upf_retraining.py",
        "scripts/evaluate_eia_retraining_frontier.py",
    )
    return {path: _hash_file(ROOT / path) for path in relative}


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing UPF development run: {output_dir}")
    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("dataset") != "eia" or source_manifest.get("version") != DATASET_VERSION:
        raise ValueError(f"This protocol accepts only EIA release {DATASET_VERSION}")
    frame = pd.read_parquet(observations_path)
    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    result_rows: list[dict[str, Any]] = []
    domain_records: dict[str, Any] = {}
    for domain_index, (domain, group) in enumerate(frame.groupby("domain_id", sort=True)):
        data = _period_data(group)
        data["domain_id"] = str(domain)
        domain_records[str(domain)] = {
            "event_ranges": [
                [float(data["event"][part[0]]), float(data["event"][part[-1]])]
                for part in data["prefixes"]
            ],
            "period_rows": [len(part) for part in data["prefixes"]],
            "evaluation_rows": [len(part) for part in data["evaluations"]],
            "feature_shift_l1": data["shifts"].tolist(),
        }
        for delay_hours in LABEL_DELAYS_HOURS:
            prepared = _prepare_domain(data, delay_hours=delay_hours, device=device)
            alpha_max, alpha_values = _alpha_frontier(prepared["performance"])
            domain_records[str(domain)].setdefault("delay_runs", {})[str(delay_hours)] = {
                "loss_scale": prepared["loss_scale"],
                "training_rows_by_period": prepared["training_counts"],
                "fit_seconds_by_period": prepared["fit_seconds"],
                "alpha_max": alpha_max,
                "alpha_values": alpha_values.tolist(),
                "offline_forecaster_entries": len(
                    _offline_observations(prepared["performance"], data["shifts"])
                ),
            }
            for alpha_index, alpha in enumerate(alpha_values):
                for method in METHODS:
                    result_rows.extend(
                        _run_policy(
                            method=method,
                            alpha=float(alpha),
                            data=data,
                            prepared=prepared,
                            domain_index=domain_index,
                            delay_hours=delay_hours,
                            device=device,
                        )
                    )

    metrics = pd.DataFrame(result_rows)
    summary = _summarize(metrics)
    output_dir.mkdir(parents=True, exist_ok=False)
    protocol_snapshot = output_dir / "protocol_snapshot.md"
    protocol_snapshot.write_bytes(PROTOCOL.read_bytes())
    metrics_path = output_dir / "period_metrics.parquet"
    summary_path = output_dir / "summary.csv"
    report_path = output_dir / "results.md"
    metrics.to_parquet(metrics_path, index=False)
    summary.to_csv(summary_path, index=False)
    run_manifest: dict[str, Any] = {
        "study": "upf_eia_bounded_retraining_cost_frontier_development_v2",
        "status": "exploratory_retrospective_development_only",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": source_manifest["version"],
        "dataset_source_url": source_manifest.get("source_url"),
        "dataset_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "protocol_sha256": _hash_file(PROTOCOL),
        "protocol_snapshot_sha256": _hash_file(protocol_snapshot),
        "runner_sha256": _hash_file(Path(__file__)),
        "method_sha256": _hash_file(ROOT / "src/shiftlab/dive/upf_retraining.py"),
        "ridge_reference_sha256": _hash_file(ROOT / "scripts/evaluate_eia_retraining_frontier.py"),
        "data_source_code_hash": source_hash(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "n_periods": N_PERIODS,
        "n_offline_periods": N_OFFLINE,
        "online_periods": list(range(ONLINE_START, N_PERIODS)),
        "label_delays_hours": list(LABEL_DELAYS_HOURS),
        "methods": list(METHODS),
        "n_alpha_points": N_ALPHA_POINTS,
        "upf_quantile": UPF_QUANTILE,
        "monte_carlo_draws": MONTE_CARLO_DRAWS,
        "alpha_grid_and_domain_records": domain_records,
        "metric_contract": "bounded clipped normalized MAE plus relative alpha per retrain; raw MAE/RMSE reported separately",
        "label_scale_contract": "1.4826*MAD of mature period-0 prefix targets; floor 1e-6; computed before evaluation tail",
        "availability_contract": "features assumed available at event timestamp; labels mature at label_event_time plus imposed delay; historical publication times unknown",
        "prior_exposure": "EIA source period and test partition were used by previous repository diagnostics; this is development only",
        "dependence_note": "Two balancing authorities are separate descriptive traces, not independent replications; no row-level inferential intervals are reported.",
        "known_comparator_gap": "CARA and published drift-detector baselines are not included; this run is not SOTA-complete.",
        "output_sha256": {},
    }
    report_path.write_text(_render_report(summary, run_manifest), encoding="utf-8")
    run_manifest["output_sha256"] = {
        path.name: sha256(path)
        for path in (metrics_path, summary_path, report_path, protocol_snapshot)
    }
    write_json(output_dir / "manifest.json", run_manifest)
    return output_dir


def _render_report(summary: pd.DataFrame, manifest: dict[str, Any]) -> str:
    lines = [
        "# UPF on EIA: bounded retraining-cost frontier",
        "",
        "**Status:** exploratory retrospective development only; not independent confirmation or a SOTA-complete comparison.",
        "",
        f"Device: `{manifest['device']}` (`{manifest['gpu_name']}`); source `{manifest['dataset_version']}`.",
        "",
        "The UPF adaptation uses a bounded clipped normalized absolute-error score. The scale is fixed per domain from the first-period training prefix. `alpha` is an imposed relative retraining cost, not an application cost.",
        "",
        "The evaluator's exact oracle uses the incumbent trained before the online horizon and enumerates decisions only for online periods 7–14. This v2 corrects a v1 off-by-one that included offline period 6 in the schedule.",
        "",
        "| Domain | Delay (h) | Method | Alpha | Total cost | Bounded loss | Retrains | MAE sum | RMSE sum |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.domain_id} | {row.delay_hours} | {row.method} | {row.alpha:.6g} | "
            f"{row.total_cost:.6f} | {row.cumulative_bounded_loss:.6f} | {row.total_retrains} | "
            f"{row.cumulative_mae:.3f} | {row.cumulative_rmse:.3f} |"
        )
    lines.extend(
        [
            "",
            "The original series is hourly, but historical feature publication and target-release times are unknown. Delay values are sensitivity assumptions. The experiment is retrospective and previously exposed; CISO and ERCO are not treated as independent replications. The output omits CARA and published drift-detector baselines and therefore does not satisfy the final comparator gate.",
            "",
            "See `period_metrics.parquet`, `summary.csv`, `protocol_snapshot.md`, and `manifest.json` for per-period results and provenance.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("data/processed/eia/e47bdef8b208f8e7d788"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/upf_eia_frontier_v2"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even when CUDA is available")
    args = parser.parse_args()
    print(run(args.dataset_path, args.output_dir, force_cpu=args.cpu))


if __name__ == "__main__":
    main()
