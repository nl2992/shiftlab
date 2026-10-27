"""Run a paper-rule RCCDA adaptation on the existing EIA period benchmark."""

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

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now
from shiftlab.data.validation import validate_dataset
from shiftlab.dive.rccda import RCCDAState

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/rccda_eia_development_protocol_v2.md"
BASELINE_OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/upf_eia_frontier_v2"
OFFICIAL_REPO = ROOT / "tmp/rccda-official"
OFFICIAL_POLICY = OFFICIAL_REPO / "src/execute_PACS/evaluate_policy.py"
METHODS = (*upf.METHODS, "rccda_paper_rule")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matured_bounded_loss(
    *,
    model_index: int,
    evaluation_period: int,
    decision_time: float,
    delay_hours: int,
    data: dict[str, Any],
    prepared: dict[str, Any],
) -> tuple[float, int] | None:
    indices = data["evaluations"][evaluation_period]
    available = (data["label_event"][indices] + delay_hours * 3600 <= decision_time) & np.isfinite(
        data["y"][indices]
    )
    matured_indices = indices[available]
    if len(matured_indices) < 20:
        return None
    prediction = upf._predict(prepared["models"][model_index], data["x"][matured_indices])
    score = upf._score(data["y"][matured_indices], prediction, scale=prepared["loss_scale"])
    return float(score["bounded_loss"]), int(score["n"])


def _initial_rccda_history(
    *,
    first_online_time: float,
    delay_hours: int,
    data: dict[str, Any],
    prepared: dict[str, Any],
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for period in range(upf.N_OFFLINE):
        observed = _matured_bounded_loss(
            model_index=period,
            evaluation_period=period,
            decision_time=first_online_time,
            delay_hours=delay_hours,
            data=data,
            prepared=prepared,
        )
        if observed is not None:
            loss, count = observed
            history.append(
                {
                    "evaluation_period": period,
                    "model_period": period,
                    "loss": loss,
                    "mature_rows": count,
                    "is_predeployment": True,
                }
            )
    if not history:
        raise ValueError("RCCDA has no mature predeployment losses at the first decision")
    return history


def _run_rccda_policy(
    *,
    alpha: float,
    data: dict[str, Any],
    prepared: dict[str, Any],
    delay_hours: int,
) -> list[dict[str, Any]]:
    metrics = prepared["raw_metrics"]
    incumbent = upf.N_OFFLINE - 1
    history = _initial_rccda_history(
        first_online_time=float(data["event"][data["evaluations"][upf.ONLINE_START][0]]),
        delay_hours=delay_hours,
        data=data,
        prepared=prepared,
    )
    state = RCCDAState(
        update_cost=1.0,
        average_update_budget=0.1,
        tradeoff=10.0,
        proportional_gain=1.0,
        derivative_gain=0.3,
    )
    last_active_model = incumbent
    rows: list[dict[str, Any]] = []

    for period in range(upf.ONLINE_START, upf.N_PERIODS):
        decision_time = float(data["event"][data["evaluations"][period][0]])
        if period > upf.ONLINE_START:
            observed = _matured_bounded_loss(
                model_index=last_active_model,
                evaluation_period=period - 1,
                decision_time=decision_time,
                delay_hours=delay_hours,
                data=data,
                prepared=prepared,
            )
            if observed is not None:
                loss, count = observed
                history.append(
                    {
                        "evaluation_period": period - 1,
                        "model_period": last_active_model,
                        "loss": loss,
                        "mature_rows": count,
                        "is_predeployment": False,
                    }
                )

        current_loss = float(history[-1]["loss"])
        previous_loss = float(history[-2]["loss"]) if len(history) >= 2 else current_loss
        best_loss = min(float(item["loss"]) for item in history)
        rccda_decision = state.decide(
            current_loss=current_loss,
            previous_loss=previous_loss,
            best_observed_loss=best_loss,
        )
        if rccda_decision.update:
            incumbent = period

        active_score = metrics[(incumbent, period)]
        rows.append(
            {
                "domain_id": data["domain_id"],
                "delay_hours": delay_hours,
                "method": "rccda_paper_rule",
                "alpha": alpha,
                "period": period,
                "retrained": rccda_decision.update,
                "active_model_period": incumbent,
                "bounded_loss": float(active_score["bounded_loss"]),
                "mae": float(active_score["mae"]),
                "rmse": float(active_score["rmse"]),
                "clipped_fraction": float(active_score["clipped_fraction"]),
                "evaluation_rows": int(active_score["n"]),
                "upf_first_action_quantile_margin": float("nan"),
                "upf_forecaster_observations": 0,
                "label_scale": prepared["loss_scale"],
                "error_trigger_threshold": float("nan"),
                "rccda_estimated_gain": rccda_decision.estimated_gain,
                "rccda_threshold": rccda_decision.threshold,
                "rccda_queue_before": rccda_decision.queue_before,
                "rccda_queue_after": rccda_decision.queue_after,
                "rccda_feedback_current_loss": current_loss,
                "rccda_feedback_previous_loss": previous_loss,
                "rccda_feedback_best_loss": best_loss,
                "rccda_feedback_rows": int(history[-1]["mature_rows"]),
                "rccda_feedback_period": int(history[-1]["evaluation_period"]),
                "rccda_feedback_model_period": int(history[-1]["model_period"]),
                "rccda_target_update_rate": state.average_update_budget,
                "rccda_tradeoff": state.tradeoff,
                "rccda_proportional_gain": state.proportional_gain,
                "rccda_derivative_gain": state.derivative_gain,
                "information_cutoff_seconds": decision_time,
            }
        )
        last_active_model = incumbent

    return rows


def _render_report(summary: pd.DataFrame, manifest: dict[str, Any]) -> str:
    lines = [
        "# RCCDA on EIA: matched retrospective development results",
        "",
        "This is a paper-rule RCCDA adaptation on EIA, not a reproduction of the PACS/DigitsDG experiments. Its loss-history estimate error is not covered by the ideal-estimator theorem. The fixed real-data periods are exploratory and already exposed to repository development.",
        "",
        f"Device: `{manifest['device']}`; GPU: `{manifest['gpu_name']}`. The experiment uses {manifest['n_online_periods']} online periods, delays {manifest['label_delays_hours']} hours, and a target mean update rate of {manifest['rccda_target_update_rate']:.2f}.",
        "",
        "The RCCDA update schedule is independent of the display-only `alpha` cost grid. Interpret the grid as a loss-versus-update-cost frontier; the average-resource theorem is asymptotic and assumes a perfect gain estimator, so the finite run does not inherit strict budget compliance. The evaluator-only oracle is aligned to the eight online periods in the corrected UPF v2 reference run.",
        "",
        "| Domain | Delay (h) | Method | Alpha | Cumulative bounded loss | Total updates | Cumulative objective |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.domain_id} | {row.delay_hours} | {row.method} | {row.alpha:.6g} | {row.cumulative_bounded_loss:.5f} | {row.total_retrains:.3f} | {row.total_cost:.5f} |"
        )
    lines.extend(
        [
            "",
            "The `rccda_paper_rule` arm is joined to the frozen v1 UPF/periodic/error-threshold baseline artifact only after dataset-version, observation-hash, delay, domain, and alpha-grid equality checks. Two balancing-authority time series are separate case studies, not independent replications.",
            "",
            "## Provenance",
            "",
            f"- Run manifest: `{manifest['manifest_path']}`",
            f"- Protocol SHA-256: `{manifest['protocol_sha256']}`",
            f"- Baseline manifest SHA-256: `{manifest['baseline_manifest_sha256']}`",
            f"- RCCDA source revision: `{manifest['official_repo_commit']}`",
            "",
        ]
    )
    return "\n".join(lines)


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    dataset_path = dataset_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing RCCDA run: {output_dir}")
    if not BASELINE_OUTPUT.is_dir():
        raise FileNotFoundError(f"Required matched UPF baseline is missing: {BASELINE_OUTPUT}")
    baseline_manifest_path = BASELINE_OUTPUT / "manifest.json"
    baseline_metrics_path = BASELINE_OUTPUT / "period_metrics.parquet"
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        source_manifest.get("dataset") != "eia"
        or source_manifest.get("version") != upf.DATASET_VERSION
    ):
        raise ValueError(f"This protocol accepts only EIA release {upf.DATASET_VERSION}")
    if baseline_manifest.get("dataset_manifest_sha256") != sha256(manifest_path):
        raise ValueError("UPF baseline uses a different EIA dataset manifest")
    if baseline_manifest.get("observations_sha256") != sha256(observations_path):
        raise ValueError("UPF baseline uses different EIA observations")

    frame = pd.read_parquet(observations_path)
    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    rccda_rows: list[dict[str, Any]] = []
    observed_grids: dict[str, dict[str, list[float]]] = {}
    for domain, group in frame.groupby("domain_id", sort=True):
        data = upf._period_data(group)
        data["domain_id"] = str(domain)
        observed_grids[str(domain)] = {}
        for delay_hours in upf.LABEL_DELAYS_HOURS:
            prepared = upf._prepare_domain(data, delay_hours=delay_hours, device=device)
            _, alpha_values = upf._alpha_frontier(prepared["performance"])
            key = f"{domain}:{delay_hours}"
            recorded = np.asarray(
                baseline_manifest["alpha_grid_and_domain_records"][str(domain)]["delay_runs"][
                    str(delay_hours)
                ]["alpha_values"],
                dtype=np.float64,
            )
            if not np.array_equal(recorded, alpha_values):
                raise ValueError(f"RCCDA and baseline alpha grids differ for {key}")
            observed_grids[str(domain)][str(delay_hours)] = alpha_values.tolist()
            for alpha in alpha_values:
                rccda_rows.extend(
                    _run_rccda_policy(
                        alpha=float(alpha),
                        data=data,
                        prepared=prepared,
                        delay_hours=delay_hours,
                    )
                )

    baseline = pd.read_parquet(baseline_metrics_path)
    selected = baseline.loc[
        baseline.method.isin(
            ("never", "always", "periodic_2", "periodic_4", "error_threshold", "upf", "oracle")
        )
    ].copy()
    rccda = pd.DataFrame(rccda_rows)
    combined = pd.concat([selected, rccda], ignore_index=True, sort=False)
    key_cols = ["domain_id", "delay_hours", "method", "alpha", "period"]
    if combined.duplicated(key_cols).any():
        raise ValueError("duplicate method-period rows in matched RCCDA/baseline data")
    expected_rows = (
        len(observed_grids)
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * len(METHODS)
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    if len(combined) != expected_rows:
        raise ValueError(f"incomplete matched metric table: {len(combined)} != {expected_rows}")
    summary = upf._summarize(combined)

    output_dir.mkdir(parents=True, exist_ok=False)
    snapshot = output_dir / "protocol_snapshot.md"
    snapshot.write_bytes(PROTOCOL.read_bytes())
    execution_sources = output_dir / "execution_sources"
    execution_sources.mkdir()
    source_paths = (
        Path(__file__),
        ROOT / "scripts/evaluate_upf_eia_frontier.py",
        ROOT / "scripts/evaluate_eia_retraining_frontier.py",
        ROOT / "src/shiftlab/dive/rccda.py",
    )
    source_hashes: dict[str, str] = {}
    for source in source_paths:
        destination = execution_sources / source.name
        shutil.copy2(source, destination)
        source_hashes[str(source.relative_to(ROOT))] = _sha256(source)

    rccda_path = output_dir / "rccda_period_metrics.parquet"
    combined_path = output_dir / "matched_period_metrics.parquet"
    summary_path = output_dir / "summary.csv"
    rccda.to_parquet(rccda_path, index=False)
    combined.to_parquet(combined_path, index=False)
    summary.to_csv(summary_path, index=False)
    official_repo_commit = None
    official_source_sha256 = None
    if OFFICIAL_REPO.is_dir() and OFFICIAL_POLICY.is_file():
        import subprocess

        official_repo_commit = subprocess.check_output(
            ["git", "-C", str(OFFICIAL_REPO), "rev-parse", "HEAD"], text=True
        ).strip()
        official_source_sha256 = _sha256(OFFICIAL_POLICY)

    result_manifest: dict[str, Any] = {
        "study": "rccda_eia_matched_retraining_frontier_development_v2",
        "status": "exploratory_retrospective_development_only",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": source_manifest["version"],
        "dataset_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "protocol_sha256": _sha256(PROTOCOL),
        "protocol_snapshot_sha256": _sha256(snapshot),
        "baseline_run": str(BASELINE_OUTPUT.relative_to(ROOT)),
        "baseline_manifest_sha256": sha256(baseline_manifest_path),
        "baseline_metrics_sha256": sha256(baseline_metrics_path),
        "data_source_code_hash": source_hash(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "n_periods": upf.N_PERIODS,
        "n_online_periods": upf.N_PERIODS - upf.ONLINE_START,
        "n_offline_periods": upf.N_OFFLINE,
        "online_periods": list(range(upf.ONLINE_START, upf.N_PERIODS)),
        "label_delays_hours": list(upf.LABEL_DELAYS_HOURS),
        "methods": list(METHODS),
        "rccda_target_update_rate": 0.1,
        "rccda_update_cost": 1.0,
        "rccda_tradeoff": 10.0,
        "rccda_proportional_gain": 1.0,
        "rccda_derivative_gain": 0.3,
        "alpha_grid_and_domain_records": observed_grids,
        "official_repo_url": "https://github.com/Adampi210/RCCDA_resource_constrained_concept_drift_adaptation_code",
        "official_repo_commit": official_repo_commit,
        "official_pacs_evaluator_sha256": official_source_sha256,
        "official_code_audit": "PACS evaluator appends current loss then reads loss_array[-1] as loss_prev, nulling its derivative term; ShiftLab follows the paper's lagged-loss equation and records the correction in the protocol.",
        "execution_source_hashes": source_hashes,
        "source_snapshot_hashes": {
            path.relative_to(output_dir).as_posix(): _sha256(path)
            for path in execution_sources.iterdir()
        },
        "artifacts": {
            "protocol_snapshot.md": _sha256(snapshot),
            "rccda_period_metrics.parquet": _sha256(rccda_path),
            "matched_period_metrics.parquet": _sha256(combined_path),
            "summary.csv": _sha256(summary_path),
        },
        "manifest_path": str((output_dir / "manifest.json").relative_to(ROOT)),
    }
    report_path = output_dir / "results.md"
    report_path.write_text(_render_report(summary, result_manifest), encoding="utf-8")
    result_manifest["artifacts"]["results.md"] = _sha256(report_path)
    final_manifest_path = output_dir / "manifest.json"
    final_manifest_path.write_text(json.dumps(result_manifest, indent=2), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path", type=Path, default=Path("data/processed/eia/e47bdef8b208f8e7d788")
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/rccda_eia_frontier_v2"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even when CUDA is available")
    args = parser.parse_args()
    report_path = run(args.dataset_path, args.output_dir, force_cpu=args.cpu)
    print(report_path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
