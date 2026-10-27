"""Add mature-feedback ADWIN/DDM retraining adaptations to the EIA frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import evaluate_cara_eia_frontier as cara
import evaluate_upf_eia_frontier as upf
import numpy as np
import pandas as pd
import torch
from river import __version__ as river_version
from river import drift
from river.drift import binary

from shiftlab.data.provenance import commit, sha256, utc_now
from shiftlab.data.validation import validate_dataset
from shiftlab.dive.drift_retraining import replay_drift_schedule

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/eia_adwin_ddm_development_protocol_v1.md"
CARA_OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/cara_eia_frontier_v1"
MAX_ADWIN_DELTA = 0.002
METHODS = ("adwin_bounded_loss", "ddm_tail_error")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _loss_streams(
    data: dict[str, Any], prepared: dict[str, Any], *, delay_hours: int
) -> tuple[dict[tuple[int, int], list[float]], float, dict[str, int]]:
    streams: dict[tuple[int, int], list[float]] = {}
    counts: dict[str, int] = {}
    scale = float(prepared["loss_scale"])
    for period in range(1, upf.N_PERIODS):
        indices = cara._maturity_indices(data, period, delay_hours)
        counts[str(period)] = len(indices)
        if len(indices) < 20:
            for model_index in range(period):
                streams[(model_index, period)] = []
            continue
        x = data["x"][indices]
        y = data["y"][indices]
        for model_index in range(period):
            residual = np.minimum(
                np.abs(y - upf._predict(prepared["models"][model_index], x)) / scale,
                1.0,
            )
            streams[(model_index, period)] = residual.astype(np.float64).tolist()

    initial_training = cara._training_indices(data, 0, delay_hours)
    initial_residual = np.minimum(
        np.abs(
            data["y"][initial_training]
            - upf._predict(prepared["models"][0], data["x"][initial_training])
        )
        / scale,
        1.0,
    )
    cutoff = float(np.quantile(initial_residual, 0.95))
    return streams, cutoff, counts


def _new_detector(method: str) -> tuple[Any, Callable[[float], float | int], dict[str, Any]]:
    if method == "adwin_bounded_loss":
        return drift.ADWIN(delta=MAX_ADWIN_DELTA), float, {"delta": MAX_ADWIN_DELTA}
    if method == "ddm_tail_error":
        return (
            binary.DDM(),
            lambda value: int(value > 0.0),
            {
                "loss_threshold": "period-0 in-sample 95th percentile",
                "river_defaults": {
                    "warm_start": 30,
                    "warning_threshold": 2.0,
                    "drift_threshold": 3.0,
                },
            },
        )
    raise ValueError(f"unknown detector: {method}")


def _run_detector(
    method: str,
    streams: dict[tuple[int, int], list[float]],
    *,
    initial_model: int,
) -> tuple[list[int], list[bool], list[int], dict[str, Any]]:
    detector, transform, params = _new_detector(method)
    if method == "ddm_tail_error":
        raise ValueError("DDM threshold must be bound before replay")
    schedule, alarms, counts = replay_drift_schedule(
        detector,
        streams,
        input_transform=transform,
        initial_model_period=initial_model,
        online_start_period=upf.ONLINE_START,
    )
    return schedule, alarms, counts, params


def _run_ddm(
    streams: dict[tuple[int, int], list[float]],
    *,
    initial_model: int,
    cutoff: float,
) -> tuple[list[int], list[bool], list[int], dict[str, Any]]:
    detector = binary.DDM()
    binary_streams = {
        key: [float(value > cutoff) for value in values] for key, values in streams.items()
    }
    schedule, alarms, counts = replay_drift_schedule(
        detector,
        binary_streams,
        input_transform=lambda value: int(value),
        initial_model_period=initial_model,
        online_start_period=upf.ONLINE_START,
    )
    params = {
        "loss_threshold": cutoff,
        "threshold_source": "period-0 training residuals, 95th percentile",
        "river_defaults": {"warm_start": 30, "warning_threshold": 2.0, "drift_threshold": 3.0},
    }
    return schedule, alarms, counts, params


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    dataset_path = dataset_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing detector run: {output_dir}")
    if not PROTOCOL.is_file() or not (CARA_OUTPUT / "manifest.json").is_file():
        raise FileNotFoundError("The frozen protocol and verified CARA v1 run are required")
    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        source_manifest.get("dataset") != "eia"
        or source_manifest.get("version") != upf.DATASET_VERSION
    ):
        raise ValueError("This protocol requires the versioned EIA EBA panel")
    cara_manifest_path = CARA_OUTPUT / "manifest.json"
    cara_manifest = json.loads(cara_manifest_path.read_text(encoding="utf-8"))
    if cara_manifest.get("dataset_manifest_sha256") != sha256(manifest_path):
        raise ValueError("CARA run uses a different dataset manifest")
    if cara_manifest.get("observations_sha256") != sha256(observations_path):
        raise ValueError("CARA run uses different EIA observations")
    cara_metrics_path = CARA_OUTPUT / "matched_period_metrics.parquet"
    if cara_manifest["artifacts"]["matched_period_metrics.parquet"] != _hash(cara_metrics_path):
        raise ValueError("CARA matched metrics do not match their manifest")

    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    frame = pd.read_parquet(observations_path)
    detector_rows: list[dict[str, Any]] = []
    input_counts: dict[str, dict[str, dict[str, int]]] = {}
    thresholds: dict[str, dict[str, float]] = {}
    for domain, group in frame.groupby("domain_id", sort=True):
        data = upf._period_data(group)
        input_counts[str(domain)] = {}
        thresholds[str(domain)] = {}
        for delay in upf.LABEL_DELAYS_HOURS:
            prepared = upf._prepare_domain(data, delay_hours=delay, device=device)
            streams, ddm_cutoff, counts = _loss_streams(data, prepared, delay_hours=delay)
            input_counts[str(domain)][str(delay)] = counts
            thresholds[str(domain)][str(delay)] = ddm_cutoff
            for method in METHODS:
                if method == "adwin_bounded_loss":
                    schedule, alarms, processed, params = _run_detector(
                        method, streams, initial_model=upf.ONLINE_START - 1
                    )
                else:
                    schedule, alarms, processed, params = _run_ddm(
                        streams,
                        initial_model=upf.ONLINE_START - 1,
                        cutoff=ddm_cutoff,
                    )
                for offset, period in enumerate(range(upf.ONLINE_START, upf.N_PERIODS)):
                    model_index = schedule[offset]
                    metrics = prepared["raw_metrics"][(model_index, period)]
                    detector_rows.append(
                        {
                            "domain_id": str(domain),
                            "delay_hours": delay,
                            "method": method,
                            "alpha": 0.0,
                            "period": period,
                            "retrained": model_index == period,
                            "active_model_period": model_index,
                            "bounded_loss": float(metrics["bounded_loss"]),
                            "mae": float(metrics["mae"]),
                            "rmse": float(metrics["rmse"]),
                            "clipped_fraction": float(metrics["clipped_fraction"]),
                            "evaluation_rows": int(metrics["n"]),
                            "training_rows": int(prepared["training_counts"][period]),
                            "label_scale": prepared["loss_scale"],
                            "detector_alarm": bool(alarms[offset]),
                            "detector_feedback_rows": int(processed[offset]),
                            "ddm_loss_threshold": ddm_cutoff
                            if method == "ddm_tail_error"
                            else float("nan"),
                            "detector_parameters": json.dumps(params, sort_keys=True),
                            "information_cutoff_seconds": float(
                                data["event"][data["evaluations"][period][0]]
                            ),
                            "mature_current_prefix_rows": int(counts[str(period)]),
                        }
                    )

    detector_metrics = pd.DataFrame(detector_rows)
    # Detector schedules do not depend on alpha; repeat the same path over the
    # established frontier so all methods share the identical report schema.
    base_alpha_values = pd.read_parquet(cara_metrics_path).query("method == 'never'")
    alpha_grids = base_alpha_values.groupby(["domain_id", "delay_hours"]).alpha.unique().to_dict()
    repeated: list[pd.DataFrame] = []
    for (domain, delay), alphas in alpha_grids.items():
        subset = detector_metrics.loc[
            (detector_metrics.domain_id == domain) & (detector_metrics.delay_hours == delay)
        ]
        for alpha in sorted(alphas):
            repeated_subset = subset.copy()
            repeated_subset["alpha"] = float(alpha)
            repeated.append(repeated_subset)
    detector_metrics = pd.concat(repeated, ignore_index=True)
    existing = pd.read_parquet(cara_metrics_path)
    matched = pd.concat([existing, detector_metrics], ignore_index=True, sort=False)
    methods = sorted(matched.method.unique().tolist())
    key_cols = ["domain_id", "delay_hours", "method", "alpha", "period"]
    if matched.duplicated(key_cols).any():
        raise ValueError("duplicate method-period keys in the matched detector frontier")
    expected = (
        2
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * 13
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    if len(matched) != expected:
        raise ValueError(f"incomplete detector frontier: {len(matched)} != {expected}")
    summary = upf._summarize(matched)

    output_dir.mkdir(parents=True, exist_ok=False)
    snapshot = output_dir / "protocol_snapshot.md"
    snapshot.write_bytes(PROTOCOL.read_bytes())
    source_dir = output_dir / "execution_sources"
    source_dir.mkdir()
    sources = (
        Path(__file__),
        ROOT / "scripts/evaluate_cara_eia_frontier.py",
        ROOT / "scripts/evaluate_upf_eia_frontier.py",
        ROOT / "src/shiftlab/dive/drift_retraining.py",
    )
    source_hashes: dict[str, str] = {}
    for source in sources:
        shutil.copy2(source, source_dir / source.name)
        source_hashes[source.relative_to(ROOT).as_posix()] = _hash(source)

    detector_path = output_dir / "detector_period_metrics.parquet"
    matched_path = output_dir / "matched_period_metrics.parquet"
    summary_path = output_dir / "summary.csv"
    detector_metrics.to_parquet(detector_path, index=False)
    matched.to_parquet(matched_path, index=False)
    summary.to_csv(summary_path, index=False)
    result_manifest: dict[str, Any] = {
        "study": "eia_mature_feedback_adwin_ddm_retraining_v1",
        "status": "exploratory_retrospective_development_only",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": source_manifest["version"],
        "dataset_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "cara_manifest_sha256": sha256(cara_manifest_path),
        "cara_matched_metrics_sha256": _hash(cara_metrics_path),
        "protocol_sha256": _hash(PROTOCOL),
        "protocol_snapshot_sha256": _hash(snapshot),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "river_version": river_version,
        "online_periods": list(range(upf.ONLINE_START, upf.N_PERIODS)),
        "warmup_periods": list(range(1, upf.ONLINE_START)),
        "label_delays_hours": list(upf.LABEL_DELAYS_HOURS),
        "methods": methods,
        "alpha_grids": {
            f"{key[0]}:{key[1]}": [float(a) for a in sorted(value)]
            for key, value in alpha_grids.items()
        },
        "adwin_parameters": {"delta": MAX_ADWIN_DELTA, "river_default_parameters": True},
        "ddm_loss_thresholds": thresholds,
        "mature_current_prefix_rows": input_counts,
        "warmup_rule": "process periods 1-6 using the active prior candidate; install model 6 at the online boundary, preserving detector state",
        "execution_source_hashes": source_hashes,
        "artifacts": {},
    }
    for path in (snapshot, detector_path, matched_path, summary_path):
        result_manifest["artifacts"][path.name] = _hash(path)
    report_path = output_dir / "results.md"
    lines = [
        "# ADWIN and DDM on EIA: matched retrospective development results",
        "",
        "This study adds maintained River implementations of the ADWIN and DDM detectors used as retraining baselines in the official CARA repository. Their regression inputs are explicit adaptations: ADWIN sees bounded normalized absolute error; DDM sees whether error exceeds the period-0 training 95th percentile. Neither is an anytime-valid decision-harm monitor.",
        "",
        f"Device: `{device}`; GPU: `{result_manifest['gpu_name']}`; River: `{river_version}`. The detector paths use only feedback mature at each period-tail decision under assumed delays 0/168 hours.",
        "",
        "| Domain | Delay (h) | Method | Alpha | Cumulative bounded loss | Updates | Cumulative objective |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    detector_summary = summary.loc[summary.method.isin(METHODS)]
    for row in detector_summary.itertuples(index=False):
        lines.append(
            f"| {row.domain_id} | {row.delay_hours} | {row.method} | {row.alpha:.6g} | {row.cumulative_bounded_loss:.5f} | {row.total_retrains:.3f} | {row.total_cost:.5f} |"
        )
    lines.extend(
        [
            "",
            "CISO and ERCO are separate historical case studies; the costs are imposed normalized research scenarios. CARA, UPF, RCCDA, operational controls, and the evaluator-only oracle remain in the matched output. The oracle is never available to learner policies.",
            "",
            "## Provenance",
            "",
            f"- Protocol SHA-256: `{result_manifest['protocol_sha256']}`",
            f"- CARA manifest SHA-256: `{result_manifest['cara_manifest_sha256']}`",
            "- Source and output hashes: `manifest.json`",
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
        default=Path("outputs/shiftguard_unified/real_data_development/eia_drift_detectors_v1"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even when CUDA is available")
    args = parser.parse_args()
    print(run(args.dataset_path, args.output_dir, force_cpu=args.cpu).relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
