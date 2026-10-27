"""Run a fresh, calibration-gated alternative confirmation for Comparecast."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

reproduction = importlib.import_module("reproduce_comparecast_paired_cost")

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/comparecast_paired_cost_confirmation_protocol.md"
EXPECTED_COMMIT = "52748c86e0429a9612dc79892c3be6156a524132"
EXPECTED_EPROCESS = "f07eb4496b61e89e03be22fa2f3554ea3ed25b045e0ff4c796d6a6dba4e30307"
SEEDS = 300
SEED_OFFSET = 99_100_000
FAMILY_ALPHA = 0.05
PRIMARY_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
METHODS = ("comparecast_weak_running_score", "shiftlab_conditional_bounded_mean")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cp_interval(
    events: int, trials: int, *, family_alpha: float, family_cells: int = 8
) -> tuple[float, float]:
    if trials < 1 or not 0 <= events <= trials or family_cells < 1 or not 0 < family_alpha < 1:
        raise ValueError("invalid interval inputs")
    tail = family_alpha / (2 * family_cells)
    lower = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    upper = 1.0 if events == trials else float(beta.ppf(1 - tail, events + 1, trials - events))
    return lower, upper


def _verify_calibration(path: Path) -> tuple[dict, str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("experiment") != "comparecast_weak_running_average_null_calibration":
        raise ValueError("calibration manifest is not the registered weak-null calibration")
    if manifest.get("status") != "diagnostic_pass":
        raise RuntimeError("Comparecast weak-null calibration did not pass")
    if not manifest.get("population_null_audit_pass") or not manifest.get(
        "simultaneous_exact_binomial_calibration_pass"
    ):
        raise RuntimeError("Comparecast calibration audit or exact-binomial gate failed")
    source = manifest.get("source", {})
    if (
        source.get("commit") != EXPECTED_COMMIT
        or source.get("eprocess_sha256") != EXPECTED_EPROCESS
    ):
        raise RuntimeError("calibration used a different upstream Comparecast version")
    for name, expected in manifest.get("artifact_sha256", {}).items():
        artifact = path.parent / name
        if not artifact.is_file() or sha256(artifact) != expected:
            raise RuntimeError(f"calibration artifact hash mismatch: {name}")
    return manifest, sha256(path)


def run(*, source_dir: Path, calibration_manifest: Path, output_dir: Path) -> dict:
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    calibration, calibration_hash = _verify_calibration(calibration_manifest)
    commit = subprocess.check_output(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != EXPECTED_COMMIT:
        raise RuntimeError(f"expected Comparecast commit {EXPECTED_COMMIT}, found {commit}")
    eprocess_path = source_dir / "comparecast/eprocess.py"
    if sha256(eprocess_path) != EXPECTED_EPROCESS:
        raise RuntimeError("upstream Comparecast e-process hash differs from calibrated source")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")

    # Reuse the already audited reproduction code unchanged and bind its run to
    # this frozen confirmation protocol and fresh seed block.
    reproduction.PROTOCOL = PROTOCOL  # type: ignore[attr-defined]
    reproduction.run(
        source_dir=source_dir,
        output_dir=output_dir,
        seeds=SEEDS,
        seed_offset=SEED_OFFSET,
        n=2400,
        d=16,
        device="cuda",
    )
    metrics_path = output_dir / "metrics.parquet"
    metrics = pd.read_parquet(metrics_path)
    if len(metrics) != 6 * SEEDS * len(METHODS):
        raise RuntimeError("confirmation row count is incomplete")
    if not metrics["events_processed"].eq(1600).all():
        raise RuntimeError("a stream did not process all 1,600 registered monitor events")
    if not set(metrics["scenario"].unique()) == {
        "stationary",
        "benign_nuisance",
        *PRIMARY_SCENARIOS,
    }:
        raise RuntimeError("scenario set differs from the frozen protocol")
    if set(metrics["method"].unique()) != set(METHODS):
        raise RuntimeError("method set differs from the frozen comparison")
    if not np.isfinite(metrics.loc[metrics["method"].eq(METHODS[0]), "max_e_value"]).all():
        raise RuntimeError("Comparecast returned a nonfinite e-value")
    if (metrics["events_processed"] != 1600).any():
        raise RuntimeError("monitor event horizon mismatch")

    summary_rows: list[dict[str, object]] = []
    for scenario in (*PRIMARY_SCENARIOS, "stationary", "benign_nuisance"):
        for method in METHODS:
            group = metrics.loc[metrics["scenario"].eq(scenario) & metrics["method"].eq(method)]
            if len(group) != SEEDS:
                raise RuntimeError(f"incomplete cell: {scenario}/{method}")
            if scenario in PRIMARY_SCENARIOS:
                successes = int(group["post_onset_detection"].astype(bool).sum())
                lower, upper = cp_interval(successes, len(group), family_alpha=FAMILY_ALPHA)
                delays = group.loc[
                    group["post_onset_detection"].astype(bool), "first_crossing_relative"
                ].astype(float) - group.loc[
                    group["post_onset_detection"].astype(bool), "harm_onset_relative"
                ].astype(float)
                lower_ci, upper_ci = lower, upper
            else:
                successes = int(group["alarm"].astype(bool).sum())
                lower_ci = upper_ci = float("nan")
                delays = pd.Series(dtype=float)
            summary_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "streams": len(group),
                    "post_onset_detections_or_alarms": successes,
                    "rate": successes / len(group),
                    "simultaneous_cp_lower": lower_ci,
                    "simultaneous_cp_upper": upper_ci,
                    "pre_onset_alarms": int(group["pre_onset_alarm"].astype(bool).sum()),
                    "mean_delay_among_post_onset_detections": float(delays.mean())
                    if len(delays)
                    else None,
                    "mean_expected_margin_excess": float(
                        group["mean_expected_margin_excess"].mean()
                    ),
                    "upstream_warning_count": int(group["upstream_warning_count"].sum()),
                }
            )
    confirmation_summary = pd.DataFrame(summary_rows)
    summary_csv = output_dir / "confirmation_summary.csv"
    summary_parquet = output_dir / "confirmation_summary.parquet"
    confirmation_summary.to_csv(summary_csv, index=False)
    confirmation_summary.to_parquet(summary_parquet, index=False)

    report_lines = [
        "# Independent Comparecast paired-cost alternative confirmation",
        "",
        f"**Status:** complete; {SEEDS} fresh seeds per scenario; device `cuda`; upstream commit `{EXPECTED_COMMIT}`.",
        "",
        "Comparecast's weak running-average null and ShiftLab's eventwise conditional-mean null differ. Alarm rates below are descriptive matched outcomes; they are not a calibrated head-to-head superiority comparison.",
        "",
        "| Alternative | Method | Post-onset detections / 300 | Rate | Simultaneous exact 95% interval | Pre-onset alarms | Mean delay among detections | Mean expected margin excess |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        if row["scenario"] not in PRIMARY_SCENARIOS:
            continue
        report_lines.append(
            f"| {row['scenario']} | {row['method']} | {row['post_onset_detections_or_alarms']} / 300 | "
            f"{row['rate']:.4f} | [{row['simultaneous_cp_lower']:.4f}, {row['simultaneous_cp_upper']:.4f}] | "
            f"{row['pre_onset_alarms']} | {row['mean_delay_among_post_onset_detections'] if row['mean_delay_among_post_onset_detections'] is not None else 'n/a'} | "
            f"{row['mean_expected_margin_excess']:.4f} |"
        )
    report_lines.extend(
        [
            "",
            "The stationary and benign-nuisance counts are reported as replication diagnostics only; weak-null error control is supported by the separately registered 2,000-stream calibration. The confidence intervals are Bonferroni-adjusted over the eight method-by-alternative cells. No inference comparing one method's rate to the other's is planned.",
        ]
    )
    report_path = output_dir / "results.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "independent_alternative_confirmation"
    manifest["confirmation"] = {
        "protocol_sha256": sha256(PROTOCOL),
        "orchestrator": "scripts/confirm_comparecast_paired_cost.py",
        "orchestrator_sha256": sha256(Path(__file__).resolve()),
        "calibration_manifest": str(calibration_manifest),
        "calibration_manifest_sha256": calibration_hash,
        "calibration_source_commit": calibration["source"]["commit"],
        "calibration_eprocess_sha256": calibration["source"]["eprocess_sha256"],
        "seed_range": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "primary_scenarios": list(PRIMARY_SCENARIOS),
        "simultaneous_interval_cells": 8,
        "familywise_alpha": FAMILY_ALPHA,
        "matched_alarm_rates_are_descriptive_only": True,
    }
    manifest["confirmation_summary"] = (
        confirmation_summary.astype(object)
        .where(pd.notna(confirmation_summary), None)
        .to_dict(orient="records")
    )
    for name in ("confirmation_summary.csv", "confirmation_summary.parquet", "results.md"):
        manifest.setdefault("artifact_sha256", {})[name] = sha256(output_dir / name)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        confirmation_summary.loc[confirmation_summary.scenario.isin(PRIMARY_SCENARIOS)].to_string(
            index=False
        )
    )
    print(f"output={output_dir}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparecast-source", type=Path, required=True)
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=ROOT
        / "outputs/shiftguard_unified/sota_reproductions/comparecast_weak_null_calibration_v2/manifest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT
        / "outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1",
    )
    args = parser.parse_args()
    run(
        source_dir=args.comparecast_source,
        calibration_manifest=args.calibration_manifest,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
