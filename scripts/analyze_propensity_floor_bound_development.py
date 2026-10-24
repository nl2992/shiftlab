"""Validate and summarize the paired propensity-floor development grid."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from scripts.run_propensity_floor_bound_development import (
    FLOORS,
    METHODS,
    OUTPUT,
    PROTOCOL,
    SCENARIO_NAMES,
    SEED_OFFSET,
    SEEDS,
    sha256,
)
from shiftlab.dive.estimators import prediction_powered_bound

MONITORS = {
    "registered_bound": ("registered_bound_detected", "registered_bound_false_escalation"),
    "common_q010": ("common_q010_detected", "common_q010_false_escalation"),
    "eventwise_qt_diagnostic": (
        "eventwise_qt_detected_diagnostic",
        "eventwise_qt_false_escalation_diagnostic",
    ),
}
NULL_SCENARIOS = {"stationary", "benign_nuisance"}


def verify_manifest(output: Path) -> tuple[dict, pd.DataFrame]:
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("resolved_device") != "cuda":
        raise ValueError("development grid did not resolve to CUDA")
    provenance = manifest.get("run_provenance", {})
    if provenance.get("protocol_sha256") != sha256(ROOT / PROTOCOL):
        raise ValueError("run protocol hash does not match the frozen protocol")
    source_commit = provenance.get("source_git_commit_at_run")
    if not source_commit:
        raise ValueError("run provenance is missing its source commit")
    runner_at_run = subprocess.check_output(
        ["git", "show", f"{source_commit}:scripts/run_propensity_floor_bound_development.py"],
        cwd=ROOT,
    )
    if hashlib.sha256(runner_at_run).hexdigest() != provenance.get("runner_sha256"):
        raise ValueError("recorded runner hash does not match the source commit used for the run")

    hashes = manifest.get("sha256", {})
    artifacts = {
        str(path).replace("\\", "/"): digest for path, digest in hashes.get("artifacts", {}).items()
    }
    for relative, digest in artifacts.items():
        path = output / Path(relative)
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"artifact hash mismatch: {relative}")
    source_files = {
        str(path).replace("\\", "/"): digest
        for path, digest in hashes.get("source_files", {}).items()
    }
    analysis_relative = "scripts/analyze_propensity_floor_bound_development.py"
    for relative, digest in source_files.items():
        if relative == analysis_relative:
            path = ROOT / Path(relative)
            if digest != provenance.get("analysis_script_sha256"):
                raise ValueError("analysis script hash differs from its provenance record")
            if not path.is_file() or sha256(path) != digest:
                raise ValueError(f"analysis script hash mismatch: {relative}")
            continue
        path = ROOT / Path(relative)
        if path.is_file() and sha256(path) == digest:
            continue
        source = subprocess.check_output(["git", "show", f"{source_commit}:{relative}"], cwd=ROOT)
        if hashlib.sha256(source).hexdigest() != digest:
            raise ValueError(f"source hash does not match the run commit: {relative}")
    metrics_path = output / "metrics/propensity_floor_bound_grid.parquet"
    if artifacts.get("metrics/propensity_floor_bound_grid.parquet") != sha256(metrics_path):
        raise ValueError("manifest does not hash the full development grid")
    metrics = pd.read_parquet(metrics_path)
    return manifest, metrics


def wilson_interval(events: int, trials: int) -> tuple[float, float]:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("require valid binomial counts")
    z = 1.959963984540054
    rate = events / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return max(0.0, float(center - radius)), min(1.0, float(center + radius))


def paired_bootstrap_interval(values: np.ndarray, *, seed: int, repetitions: int = 10_000):
    if values.ndim != 1 or not len(values) or repetitions < 1:
        raise ValueError("paired bootstrap requires a nonempty vector and positive repetitions")
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(values), size=(repetitions, len(values)))
    means = values[draw].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def validate_metrics(metrics: pd.DataFrame, manifest: dict) -> None:
    expected_config = manifest.get("configuration_by_q_min", {})
    if set(expected_config) != {f"{floor:.2f}" for floor in FLOORS}:
        raise ValueError("registered q_min configuration set differs from protocol")
    for floor in FLOORS:
        config = expected_config[f"{floor:.2f}"]
        if config.get("q_min") != floor or config.get("seed_offset") != SEED_OFFSET:
            raise ValueError("a propensity-floor configuration differs from protocol")
        if config.get("seeds") != SEEDS or config.get("method_subset") != list(METHODS):
            raise ValueError("seed count or policy set differs from protocol")
        if config.get("scenario_subset") != list(SCENARIO_NAMES):
            raise ValueError("scenario set differs from protocol")
        if config.get("device") != "cuda" or config.get("record_event_traces") is not True:
            raise ValueError("configuration does not match trace-audited CUDA development")

    expected_rows = len(FLOORS) * len(SCENARIO_NAMES) * SEEDS * len(METHODS)
    keys = ["q_min", "scenario", "seed", "method"]
    if len(metrics) != expected_rows or metrics.duplicated(keys).any():
        raise ValueError(f"expected {expected_rows} unique floor-scenario-seed-policy rows")
    if set(metrics.q_min) != set(FLOORS) or set(metrics.scenario) != set(SCENARIO_NAMES):
        raise ValueError("floor or scenario set differs from the protocol")
    if set(metrics.method) != set(METHODS):
        raise ValueError("query-policy set differs from the protocol")
    expected_seeds = set(range(SEED_OFFSET, SEED_OFFSET + SEEDS))
    for (floor, scenario, method), group in metrics.groupby(keys[:1] + keys[1:2] + keys[3:4]):
        del floor, scenario, method
        if set(group.seed) != expected_seeds:
            raise ValueError("a policy cell does not contain the exact paired seed block")
    if not metrics.budget_respected.astype(bool).all():
        raise ValueError("a stream violated its hard dollar budget")

    for floor in FLOORS:
        for method in METHODS:
            group = metrics.loc[metrics.q_min.eq(floor) & metrics.method.eq(method)]
            registered_floor = 0.20 if method == "uniform_proxy" else floor
            expected_bound = prediction_powered_bound(5.1, registered_floor)
            if not np.allclose(
                group.registered_minimum_propensity, registered_floor, rtol=0, atol=1e-12
            ):
                raise ValueError(f"{method} has an unexpected registered propensity floor")
            if not np.allclose(group.registered_support_bound, expected_bound, rtol=0, atol=1e-10):
                raise ValueError(f"{method} has an unexpected registered fixed support bound")
            if (group.query_propensity_min < floor - 1e-10).any():
                raise ValueError(f"{method} queried below configured q_min={floor}")
    if not metrics.groupby(["scenario", "seed", "q_min"]).material_harm.nunique().eq(1).all():
        raise ValueError("evaluator harm eligibility differs by method on a paired stream")


def summarize(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summaries = []
    for (floor, scenario, method), group in metrics.groupby(
        ["q_min", "scenario", "method"], sort=True
    ):
        harmful = group.loc[group.material_harm.astype(bool)]
        reached = harmful.loc[harmful.harm_reached_before_budget_stop.astype(bool)]
        for monitor, (detect_column, false_column) in MONITORS.items():
            detections = int(harmful[detect_column].astype(bool).sum())
            low, high = (
                wilson_interval(detections, len(harmful)) if len(harmful) else (np.nan, np.nan)
            )
            delays = []
            for alarm, onset in zip(
                harmful[f"{monitor.removesuffix('_diagnostic')}_alarm_time"]
                if monitor != "eventwise_qt_diagnostic"
                else harmful["eventwise_qt_alarm_time"],
                harmful.harm_onset_relative,
                strict=True,
            ):
                if pd.notna(alarm) and pd.notna(onset) and int(alarm) >= int(onset):
                    delays.append(int(alarm) - int(onset))
            null = group.loc[group.scenario.isin(NULL_SCENARIOS)]
            summaries.append(
                {
                    "q_min": floor,
                    "scenario": scenario,
                    "method": method,
                    "monitor": monitor,
                    "streams": len(group),
                    "material_harm_streams": len(harmful),
                    "onsets_reached": int(
                        harmful.harm_reached_before_budget_stop.astype(bool).sum()
                    ),
                    "detections": detections,
                    "detection_rate": detections / len(harmful) if len(harmful) else np.nan,
                    "wilson_95_low": low,
                    "wilson_95_high": high,
                    "detection_rate_among_reached": (
                        float(reached[detect_column].astype(bool).mean())
                        if len(reached)
                        else np.nan
                    ),
                    "mean_delay_among_detections": float(np.mean(delays)) if delays else np.nan,
                    "false_escalations": int(group[false_column].astype(bool).sum()),
                    "population_null_false_escalations": (
                        int(null[false_column].astype(bool).sum()) if len(null) else 0
                    ),
                    "population_null_streams": len(null),
                    "mean_labels": float(group.labels_queried.mean()),
                    "mean_spend": float(group.realized_label_spend.mean()),
                    "mean_budget": float(group.hard_budget.mean()),
                    "mean_processed_events": float(group.processed_events.mean()),
                    "mean_q": float(group.query_propensity_mean.mean()),
                    "mean_eventwise_bound": float(group.eventwise_bound_mean.mean()),
                    "budget_violations": int((~group.budget_respected.astype(bool)).sum()),
                }
            )
    summary = pd.DataFrame(summaries)

    monitor_deltas = []
    for (floor, scenario, method), group in metrics.groupby(
        ["q_min", "scenario", "method"], sort=True
    ):
        for monitor, column in (
            ("common_q010", "common_q010_detected"),
            ("eventwise_qt_diagnostic", "eventwise_qt_detected_diagnostic"),
        ):
            differences = (
                group[column].astype(float).to_numpy()
                - group.registered_bound_detected.astype(float).to_numpy()
            )
            low, high = paired_bootstrap_interval(
                differences,
                seed=56_100_000
                + round(floor * 100) * 1000
                + SCENARIO_NAMES.index(scenario) * 10
                + METHODS.index(method),
            )
            monitor_deltas.append(
                {
                    "q_min": floor,
                    "scenario": scenario,
                    "method": method,
                    "monitor_vs_registered": monitor,
                    "paired_rate_difference": float(differences.mean()),
                    "paired_bootstrap_95_low": low,
                    "paired_bootstrap_95_high": high,
                    "method_only": int((differences > 0).sum()),
                    "registered_only": int((differences < 0).sum()),
                    "streams": len(group),
                }
            )
    low_floor, high_floor = FLOORS
    floor_effects = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        pivot = group.pivot(index="seed", columns="q_min", values="registered_bound_detected")
        differences = (
            pivot[high_floor].astype(float).to_numpy() - pivot[low_floor].astype(float).to_numpy()
        )
        low, high = paired_bootstrap_interval(
            differences,
            seed=56_200_000 + SCENARIO_NAMES.index(scenario) * 10 + METHODS.index(method),
        )
        floor_effects.append(
            {
                "scenario": scenario,
                "method": method,
                "paired_rate_difference_high_minus_low": float(differences.mean()),
                "paired_bootstrap_95_low": low,
                "paired_bootstrap_95_high": high,
                "high_floor_only": int((differences > 0).sum()),
                "low_floor_only": int((differences < 0).sum()),
                "paired_seeds": len(pivot),
                "interpretation": "floor plus acquisition policy; not a monitor-only contrast",
            }
        )
    return summary, pd.DataFrame(monitor_deltas), pd.DataFrame(floor_effects)


def analyze(output: Path = OUTPUT) -> tuple[Path, Path]:
    manifest, metrics = verify_manifest(output)
    validate_metrics(metrics, manifest)
    summary, monitor_deltas, floor_effects = summarize(metrics)
    low_floor, high_floor = FLOORS
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    summary_path = analysis_dir / "propensity_floor_bound_summary.csv"
    monitor_path = analysis_dir / "paired_monitor_deltas.csv"
    floor_path = analysis_dir / "paired_floor_effects.csv"
    summary.to_csv(summary_path, index=False)
    monitor_deltas.to_csv(monitor_path, index=False)
    floor_effects.to_csv(floor_path, index=False)

    lines = [
        "# Propensity-floor and e-process bound development grid",
        "",
        "This is a frozen development grid. The 60-seed null cells are descriptive and do not establish a 5% false-escalation guarantee; harmful-stream comparisons do not select a confirmatory winner.",
        "",
        f"CUDA: `{manifest['environment'].get('gpu_name', 'unknown')}`; seed block `{SEED_OFFSET}–{SEED_OFFSET + SEEDS - 1}` paired across q_min values; {len(metrics)} stream-policy rows.",
        "",
        "The fixed registered bound is valid only under the registered conditional-on-past null and support assumptions. The eventwise q_t bound requires the stronger conditional null given current context and bound-selection information. Eventwise rates below are uncalibrated sensitivity diagnostics, not valid population-null rates or evidence for deployment.",
        "",
        "## Detection and false-escalation summaries",
        "",
        "|q_min|Scenario|Policy|Monitor|Harm / streams|Onsets reached|Detections|Rate (Wilson 95%)|Null false / streams|Mean q|Mean labels|Mean spend / cap|Mean events|",
        "|---:|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    execution_note = manifest.get("run_provenance", {}).get("post_run_execution_note")
    if execution_note:
        lines.extend(["## Execution note", "", execution_note, ""])
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['q_min']:.2f}|{row['scenario']}|{row['method']}|{row['monitor']}|{row['material_harm_streams']}|{row['onsets_reached']}|{row['detections']}|{row['detection_rate']:.3f} [{row['wilson_95_low']:.3f}, {row['wilson_95_high']:.3f}]|{row['population_null_false_escalations']}/{row['population_null_streams']}|{row['mean_q']:.3f}|{row['mean_labels']:.1f}|{row['mean_spend']:.2f} / {row['mean_budget']:.2f}|{row['mean_processed_events']:.1f}|"
        )
    lines.extend(
        [
            "",
            "## Paired monitor and floor effects",
            "",
            "`common_q010` is the same query path with the common 0.10 support bound. `eventwise_qt_diagnostic` uses the realized pre-outcome propensity and is conditional-null sensitive. The floor contrast changes acquisition as well as the registered support bound.",
            "",
            "### Monitor bound contrasts",
            "",
            "|q_min|Scenario|Policy|Monitor vs registered|Paired rate difference (bootstrap 95%)|Monitor-only / registered-only|",
            "|---:|---|---|---|---:|---:|",
        ]
    )
    for row in monitor_deltas.to_dict("records"):
        lines.append(
            f"|{row['q_min']:.2f}|{row['scenario']}|{row['method']}|{row['monitor_vs_registered']}|{row['paired_rate_difference']:.3f} [{row['paired_bootstrap_95_low']:.3f}, {row['paired_bootstrap_95_high']:.3f}]|{row['method_only']} / {row['registered_only']}|"
        )
    lines.extend(
        [
            "",
            "### Propensity-floor contrasts",
            "",
            f"|Scenario|Policy|q_min {high_floor:.2f} minus {low_floor:.2f} rate difference (bootstrap 95%)|high-floor-only / low-floor-only|",
            "|---|---|---:|---:|",
        ]
    )
    for row in floor_effects.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['paired_rate_difference_high_minus_low']:.3f} [{row['paired_bootstrap_95_low']:.3f}, {row['paired_bootstrap_95_high']:.3f}]|{row['high_floor_only']} / {row['low_floor_only']}|"
        )
    lines.extend(
        [
            "",
            "No confirmatory winner or novelty claim is supported. Before treating the eventwise comparator as valid for population harm, either establish a suitable conditional null or use a scale predictable before current covariates are observed. A new registered null-calibration block is required before confirmation.",
            "",
            "No figure was generated under this protocol.",
            "",
        ]
    )
    report_path = output / "reports/propensity_floor_bound_development.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    manifest_path = output / "reports/manifest.json"
    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = updated["sha256"]["artifacts"]
    for path in (summary_path, monitor_path, floor_path, report_path):
        artifacts[path.relative_to(output).as_posix()] = sha256(path)
    source_files = updated["sha256"]["source_files"]
    analyzer_path = ROOT / "scripts/analyze_propensity_floor_bound_development.py"
    source_files[analyzer_path.relative_to(ROOT).as_posix()] = sha256(analyzer_path)
    updated.setdefault("run_provenance", {})["analysis_script_sha256"] = sha256(analyzer_path)
    updated["sha256"]["source_files"][analyzer_path.relative_to(ROOT).as_posix()] = sha256(
        analyzer_path
    )
    manifest_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return summary_path, report_path


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    summary_path, report_path = analyze()
    print(report_path)
    print(
        pd.read_csv(summary_path)
        .groupby(["q_min", "scenario", "monitor"], sort=True)[
            [
                "detections",
                "material_harm_streams",
                "population_null_false_escalations",
                "population_null_streams",
            ]
        ]
        .sum()
        .to_string()
    )


if __name__ == "__main__":
    main()
