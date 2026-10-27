"""Evaluate a paper-rule CARA adaptation on the matched EIA retraining frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from pathlib import Path
from typing import Any

import evaluate_upf_eia_frontier as upf
import numpy as np
import pandas as pd
import torch

from shiftlab.data.provenance import commit, sha256, utc_now
from shiftlab.data.validation import validate_dataset
from shiftlab.dive.cara_retraining import (
    periodic_schedule,
    threshold_schedule,
    tune_periodic,
    tune_threshold,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/cara_eia_development_protocol_v1.md"
BASELINE_OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/rccda_eia_frontier_v2"
OFFICIAL_REPO = ROOT / "tmp/cara-official"
OFFICIAL_COMMIT = "ac2a600a3bbc5729087318087c9def96104c9023"
MAX_SAMPLE = 256
OFFLINE_TUNE_PERIODS = range(1, 6)
CARA_METHODS = ("cara_threshold", "cara_cumulative_threshold", "cara_periodic")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample(array: np.ndarray, limit: int = MAX_SAMPLE) -> np.ndarray:
    if len(array) <= limit:
        return array
    return array[np.linspace(0, len(array) - 1, num=limit, dtype=np.int64)]


def _standardize_features(x: np.ndarray, scaler: dict[str, Any]) -> np.ndarray:
    imputed = np.where(np.isnan(x), scaler["median"], x)
    return (imputed - scaler["mean"]) / scaler["scale"]


def _qdm(
    model: dict[str, Any],
    x: np.ndarray,
    y: np.ndarray,
    query: np.ndarray,
    *,
    scale: float,
    scaler: dict[str, Any],
    device: torch.device,
) -> float:
    if len(x) < 20 or len(query) == 0:
        return float("nan")
    x_sample = _sample(x)
    y_sample = _sample(y)
    query_sample = _sample(query)
    residual = np.minimum(np.abs(y_sample - upf._predict(model, x_sample)) / scale, 1.0)
    x_standard = torch.as_tensor(
        _standardize_features(x_sample, scaler), dtype=torch.float64, device=device
    )
    q_standard = torch.as_tensor(
        _standardize_features(query_sample, scaler), dtype=torch.float64, device=device
    )
    losses = torch.as_tensor(residual, dtype=torch.float64, device=device)
    squared = (
        q_standard.square().sum(dim=1, keepdim=True)
        + x_standard.square().sum(dim=1).unsqueeze(0)
        - 2.0 * q_standard @ x_standard.T
    ).clamp_min_(0.0)
    # Gaussian RBF with gamma=1/d, as in sklearn's default RBF scale.
    weights = torch.exp(-squared / x_standard.shape[1])
    return float(((weights @ losses) / len(losses)).mean().item())


def _maturity_indices(data: dict[str, Any], period: int, delay_hours: int) -> np.ndarray:
    prefix = data["prefixes"][period]
    cutoff = float(data["event"][data["evaluations"][period][0]])
    eligible = (
        (data["event"][prefix] < cutoff)
        & (data["label_event"][prefix] + delay_hours * 3600 <= cutoff)
        & np.isfinite(data["y"][prefix])
    )
    return prefix[eligible]


def _training_indices(data: dict[str, Any], period: int, delay_hours: int) -> np.ndarray:
    cutoff = float(data["event"][data["evaluations"][period][0]])
    prefix_pool = np.arange(data["evaluations"][period][0], dtype=np.int64)
    eligible = (
        (data["event"][prefix_pool] < cutoff)
        & (data["label_event"][prefix_pool] + delay_hours * 3600 <= cutoff)
        & np.isfinite(data["y"][prefix_pool])
    )
    return prefix_pool[eligible]


def _staleness_matrix(
    data: dict[str, Any], prepared: dict[str, Any], *, delay_hours: int, device: torch.device
) -> tuple[np.ndarray, list[int]]:
    n_periods = upf.N_PERIODS
    scores = np.full((n_periods, n_periods), np.nan, dtype=np.float64)
    scale = float(prepared["loss_scale"])
    scaler = prepared["models"][0]
    train_rows = [_training_indices(data, i, delay_hours) for i in range(n_periods)]
    mature_rows = [_maturity_indices(data, t, delay_hours) for t in range(n_periods)]
    for t in range(1, n_periods):
        current = mature_rows[t]
        query = data["x"][data["prefixes"][t]]
        if len(current) < 20:
            continue
        current_x = data["x"][current]
        current_y = data["y"][current]
        for model_period in range(t):
            reference = train_rows[model_period]
            model = prepared["models"][model_period]
            current_qdm = _qdm(
                model, current_x, current_y, query, scale=scale, scaler=scaler, device=device
            )
            reference_qdm = _qdm(
                model,
                data["x"][reference],
                data["y"][reference],
                query,
                scale=scale,
                scaler=scaler,
                device=device,
            )
            scores[model_period, t] = current_qdm - reference_qdm
    return scores, [len(rows) for rows in mature_rows]


def _policy_rows(
    *,
    method: str,
    model_schedule: list[int],
    decision_scores: list[float],
    parameters: dict[str, Any],
    alpha: float,
    domain: str,
    delay_hours: int,
    data: dict[str, Any],
    prepared: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period, model_index, decision_score in zip(
        range(upf.ONLINE_START, upf.N_PERIODS), model_schedule, decision_scores, strict=True
    ):
        metrics = prepared["raw_metrics"][(model_index, period)]
        rows.append(
            {
                "domain_id": domain,
                "delay_hours": delay_hours,
                "method": method,
                "alpha": alpha,
                "period": period,
                "retrained": model_index == period,
                "active_model_period": model_index,
                "bounded_loss": float(metrics["bounded_loss"]),
                "mae": float(metrics["mae"]),
                "rmse": float(metrics["rmse"]),
                "clipped_fraction": float(metrics["clipped_fraction"]),
                "evaluation_rows": int(metrics["n"]),
                "label_scale": prepared["loss_scale"],
                "training_rows": prepared["training_counts"][period],
                "cara_staleness_score": float(decision_score),
                "cara_parameters": json.dumps(parameters, sort_keys=True, allow_nan=True),
                "information_cutoff_seconds": float(data["event"][data["evaluations"][period][0]]),
                "mature_current_prefix_rows": int(
                    _maturity_indices(data, period, delay_hours).size
                ),
            }
        )
    return rows


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    dataset_path = dataset_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing CARA run: {output_dir}")
    baseline_metrics_path = BASELINE_OUTPUT / "matched_period_metrics.parquet"
    baseline_manifest_path = BASELINE_OUTPUT / "manifest.json"
    if not baseline_metrics_path.is_file() or not baseline_manifest_path.is_file():
        raise FileNotFoundError("The verified matched UPF/RCCDA frontier is required")
    if not PROTOCOL.is_file():
        raise FileNotFoundError(f"Frozen protocol is missing: {PROTOCOL}")
    if not OFFICIAL_REPO.is_dir():
        raise FileNotFoundError("Official CARA source snapshot is missing")
    import subprocess

    actual_commit = subprocess.check_output(
        ["git", "-C", str(OFFICIAL_REPO), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit != OFFICIAL_COMMIT:
        raise ValueError(f"Unexpected official CARA source revision: {actual_commit}")

    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        source_manifest.get("dataset") != "eia"
        or source_manifest.get("version") != upf.DATASET_VERSION
    ):
        raise ValueError("This protocol requires the versioned EIA EBA panel")
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    if baseline_manifest.get("dataset_manifest_sha256") != sha256(manifest_path):
        raise ValueError("The baseline and CARA run use different dataset manifests")
    if baseline_manifest.get("observations_sha256") != sha256(observations_path):
        raise ValueError("The baseline and CARA run use different EIA observations")

    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    frame = pd.read_parquet(observations_path)
    cara_rows: list[dict[str, Any]] = []
    alpha_records: dict[str, dict[str, list[float]]] = {}
    parameter_records: dict[str, dict[str, list[dict[str, Any]]]] = {}
    mature_counts: dict[str, dict[str, list[int]]] = {}
    for domain, group in frame.groupby("domain_id", sort=True):
        data = upf._period_data(group)
        prepared_by_delay: dict[int, dict[str, Any]] = {}
        alpha_records[str(domain)] = {}
        parameter_records[str(domain)] = {}
        mature_counts[str(domain)] = {}
        for delay_hours in upf.LABEL_DELAYS_HOURS:
            prepared = upf._prepare_domain(data, delay_hours=delay_hours, device=device)
            prepared_by_delay[delay_hours] = prepared
            scores, counts = _staleness_matrix(
                data, prepared, delay_hours=delay_hours, device=device
            )
            mature_counts[str(domain)][str(delay_hours)] = counts
            _, alpha_values = upf._alpha_frontier(prepared["performance"])
            recorded = baseline_manifest["alpha_grid_and_domain_records"][str(domain)][
                str(delay_hours)
            ]
            if not np.array_equal(np.asarray(recorded, dtype=np.float64), alpha_values):
                raise ValueError(f"alpha grid mismatch for {domain=} {delay_hours=}")
            alpha_records[str(domain)][str(delay_hours)] = alpha_values.tolist()
            parameter_records[str(domain)][str(delay_hours)] = []
            for alpha in alpha_values:
                threshold, offline_objective, offline_updates = tune_threshold(
                    scores,
                    prepared["performance"],
                    alpha=float(alpha),
                    offline_periods=OFFLINE_TUNE_PERIODS,
                    cumulative=False,
                )
                cumulative_threshold, cumulative_objective, cumulative_updates = tune_threshold(
                    scores,
                    prepared["performance"],
                    alpha=float(alpha),
                    offline_periods=OFFLINE_TUNE_PERIODS,
                    cumulative=True,
                )
                periodic, periodic_offset, periodic_objective, periodic_updates = tune_periodic(
                    prepared["performance"],
                    alpha=float(alpha),
                    offline_periods=OFFLINE_TUNE_PERIODS,
                )
                online_periods = range(upf.ONLINE_START, upf.N_PERIODS)
                threshold_models, threshold_scores = threshold_schedule(
                    scores,
                    initial_model=upf.ONLINE_START - 1,
                    periods=online_periods,
                    threshold=threshold,
                )
                cumulative_models, cumulative_scores = threshold_schedule(
                    scores,
                    initial_model=upf.ONLINE_START - 1,
                    periods=online_periods,
                    threshold=cumulative_threshold,
                    cumulative=True,
                )
                periodic_models = periodic_schedule(
                    initial_model=upf.ONLINE_START - 1,
                    periods=online_periods,
                    period=periodic,
                    offset=periodic_offset,
                )
                params = [
                    {
                        "method": "cara_threshold",
                        "threshold": threshold,
                        "offline_objective": offline_objective,
                        "offline_updates": offline_updates,
                    },
                    {
                        "method": "cara_cumulative_threshold",
                        "threshold": cumulative_threshold,
                        "offline_objective": cumulative_objective,
                        "offline_updates": cumulative_updates,
                    },
                    {
                        "method": "cara_periodic",
                        "period": periodic,
                        "offset": periodic_offset,
                        "offline_objective": periodic_objective,
                        "offline_updates": periodic_updates,
                    },
                ]
                parameter_records[str(domain)][str(delay_hours)].append(
                    {"alpha": float(alpha), "parameters": params}
                )
                schedules = (
                    (threshold_models, threshold_scores),
                    (cumulative_models, cumulative_scores),
                    (periodic_models, [float("nan")] * len(online_periods)),
                )
                for method, (schedule, decision_scores), method_params in zip(
                    CARA_METHODS, schedules, params, strict=True
                ):
                    cara_rows.extend(
                        _policy_rows(
                            method=method,
                            model_schedule=schedule,
                            decision_scores=decision_scores,
                            parameters=method_params,
                            alpha=float(alpha),
                            domain=str(domain),
                            delay_hours=delay_hours,
                            data=data,
                            prepared=prepared,
                        )
                    )

    baseline = pd.read_parquet(baseline_metrics_path)
    selected_methods = (
        "never",
        "always",
        "periodic_2",
        "periodic_4",
        "error_threshold",
        "upf",
        "rccda_paper_rule",
        "oracle",
    )
    selected = baseline.loc[baseline.method.isin(selected_methods)].copy()
    cara = pd.DataFrame(cara_rows)
    combined = pd.concat([selected, cara], ignore_index=True, sort=False)
    key_cols = ["domain_id", "delay_hours", "method", "alpha", "period"]
    if combined.duplicated(key_cols).any():
        raise ValueError("duplicate method-period keys in the matched CARA frontier")
    expected = (
        2
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * (len(selected_methods) + len(CARA_METHODS))
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    if len(combined) != expected:
        raise ValueError(f"incomplete combined frontier: {len(combined)} != {expected}")
    summary = upf._summarize(combined)

    output_dir.mkdir(parents=True, exist_ok=False)
    snapshot = output_dir / "protocol_snapshot.md"
    snapshot.write_bytes(PROTOCOL.read_bytes())
    sources_dir = output_dir / "execution_sources"
    sources_dir.mkdir()
    source_paths = (
        Path(__file__),
        ROOT / "scripts/evaluate_upf_eia_frontier.py",
        ROOT / "scripts/evaluate_rccda_eia_frontier.py",
        ROOT / "src/shiftlab/dive/cara_retraining.py",
    )
    source_hashes: dict[str, str] = {}
    for source in source_paths:
        shutil.copy2(source, sources_dir / source.name)
        source_hashes[source.relative_to(ROOT).as_posix()] = _hash(source)

    cara_path = output_dir / "cara_period_metrics.parquet"
    matched_path = output_dir / "matched_period_metrics.parquet"
    summary_path = output_dir / "summary.csv"
    cara.to_parquet(cara_path, index=False)
    combined.to_parquet(matched_path, index=False)
    summary.to_csv(summary_path, index=False)
    result_manifest: dict[str, Any] = {
        "study": "cara_eia_matched_retraining_frontier_v1",
        "status": "exploratory_retrospective_development_only",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": source_manifest["version"],
        "dataset_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "baseline_manifest_sha256": sha256(baseline_manifest_path),
        "baseline_metrics_sha256": sha256(baseline_metrics_path),
        "protocol_sha256": _hash(PROTOCOL),
        "protocol_snapshot_sha256": _hash(snapshot),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "online_periods": list(range(upf.ONLINE_START, upf.N_PERIODS)),
        "offline_tuning_periods": list(OFFLINE_TUNE_PERIODS),
        "label_delays_hours": list(upf.LABEL_DELAYS_HOURS),
        "methods": list(selected_methods + CARA_METHODS),
        "max_qdm_sample_rows": MAX_SAMPLE,
        "alpha_grids": alpha_records,
        "tuned_parameters": parameter_records,
        "mature_current_prefix_rows": mature_counts,
        "query_proxy": "observed current-period prefix covariates; evaluation-tail covariates excluded",
        "cara_original_source_url": "https://version.helsinki.fi/ads/cost-aware-retraining-algorithms",
        "cara_official_source_revision": OFFICIAL_COMMIT,
        "cara_adaptation": "bounded normalized absolute regression loss and current-prefix query proxy; not a reproduction of published classification experiments",
        "execution_source_hashes": source_hashes,
        "artifacts": {},
    }
    for path in (snapshot, cara_path, matched_path, summary_path):
        result_manifest["artifacts"][path.name] = _hash(path)
    report_path = output_dir / "results.md"
    lines = [
        "# CARA on EIA: matched retrospective development results",
        "",
        "This is a task-specific regression adaptation of CARA, not a reproduction of its published classification experiments. It uses the official threshold, cumulative-threshold, and periodic schedule rules from the pinned source revision. The QDM score is estimated from mature current-prefix labels and current-prefix covariates; evaluation-tail covariates and outcomes are excluded from decisions.",
        "",
        f"Execution device: `{device}`; GPU: `{result_manifest['gpu_name']}`. Parameters are fit on offline periods {list(OFFLINE_TUNE_PERIODS)} for each update-cost setting, then frozen over online periods {list(range(upf.ONLINE_START, upf.N_PERIODS))}.",
        "",
        "These are two retrospective EIA series with assumed feature availability at event time and 0/168-hour additional label delays. Costs are normalized frontier scenarios, and the two authorities are not independent replications. No real-time or utility guarantee follows.",
        "",
        "| Domain | Delay (h) | Method | Alpha | Cumulative bounded loss | Updates | Cumulative objective |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    cara_summary = summary.loc[summary.method.isin(CARA_METHODS)]
    for row in cara_summary.itertuples(index=False):
        lines.append(
            f"| {row.domain_id} | {row.delay_hours} | {row.method} | {row.alpha:.6g} | {row.cumulative_bounded_loss:.5f} | {row.total_retrains:.3f} | {row.total_cost:.5f} |"
        )
    lines.extend(
        [
            "",
            "The same matched output includes never/always, periodic-2/4, error-threshold, UPF, RCCDA, and the evaluator-only oracle arms. The oracle is only a lower-bound reference and is not available to learners.",
            "",
            "## Provenance",
            "",
            f"- Official CARA code revision: `{OFFICIAL_COMMIT}`",
            f"- Protocol SHA-256: `{result_manifest['protocol_sha256']}`",
            f"- Baseline manifest SHA-256: `{result_manifest['baseline_manifest_sha256']}`",
            "- Run manifest: `manifest.json`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    result_manifest["artifacts"][report_path.name] = _hash(report_path)
    result_manifest["manifest_path"] = str((output_dir / "manifest.json").relative_to(ROOT))
    (output_dir / "manifest.json").write_text(
        json.dumps(result_manifest, indent=2), encoding="utf-8"
    )
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path", type=Path, default=Path("data/processed/eia/e47bdef8b208f8e7d788")
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/cara_eia_frontier_v1"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even when CUDA is available")
    args = parser.parse_args()
    report = run(args.dataset_path, args.output_dir, force_cpu=args.cpu)
    print(report.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
