"""Validate and summarize frozen policy-specific-bound null calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from shiftlab.decision_harm_experiment import SCENARIOS as SCENARIO_DEFINITIONS
from shiftlab.dive.estimators import prediction_powered_bound
from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/policy_bound_null_calibration_500"
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIOS = ("stationary", "benign_nuisance")
MONITORS = {
    "fixed_mixture": "single_e_false_escalation",
    "predictable_variance": "variance_adaptive_false_escalation",
    "pm_eb": "pm_eb_false_escalation",
}
PRIMARY_ALPHA = 0.05
PROTOCOL = Path("docs/policy_bound_null_calibration_protocol.md")
EXPECTED_SEEDS = set(range(54_000_000, 54_000_500))
EXPECTED_CONFIG = {
    "n": 3200,
    "d": 16,
    "seeds": 500,
    "seed_offset": 54_000_000,
    "alpha": 0.05,
    "harm_margin": 0.10,
    "budget_rate": 0.20,
    "budget_dollars": None,
    "monitor_horizon_events": None,
    "q_min": 0.10,
    "q_max": 0.80,
    "cost_stability_tolerance": 0.05,
    "exact_growth_adaptive_weight": 1.0,
    "robust_growth_probability_radius": 0.0,
    "monitor_comparators": ["variance_adaptive", "pm_eb"],
    "pprm_block_size": 20,
    "pprm_labels_per_block": 4,
    "pprm_max_reliance": 1.0,
    "pprm_initial_reliance": 1.0,
    "max_label_cost": 2.5,
    "common_eprocess_bound": False,
    "generate_figure": False,
    "record_event_traces": False,
    "scenario_severity": None,
    "change_fraction": 0.5,
    "device": "cuda",
    "workers": 2,
    "scenario_subset": ["stationary", "benign_nuisance"],
    "method_subset": list(METHODS),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest_integrity(output: Path, manifest: dict) -> None:
    hashes = manifest.get("sha256", {})
    artifact_hashes = {
        str(path).replace("\\", "/"): digest for path, digest in hashes.get("artifacts", {}).items()
    }
    required_metrics = "metrics/hard_budget_comparison.parquet"
    if required_metrics not in artifact_hashes:
        raise ValueError("run manifest does not hash the calibration metrics")
    for relative, expected_hash in artifact_hashes.items():
        path = output / Path(relative)
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"run artifact failed its manifest hash: {relative}")

    source_hashes = {
        str(path).replace("\\", "/"): digest
        for path, digest in hashes.get("source_files", {}).items()
    }
    if not source_hashes:
        raise ValueError("run manifest does not hash its source files")
    for relative, expected_hash in source_hashes.items():
        path = ROOT / Path(relative)
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"run source failed its manifest hash: {relative}")


def verify_run_provenance(manifest: dict) -> None:
    if manifest.get("resolved_device") != "cuda":
        raise ValueError("the frozen calibration must resolve to CUDA")
    provenance = manifest.get("run_provenance", {})
    expected_hashes = {
        "protocol_sha256": ROOT / PROTOCOL,
        "run_script_sha256": ROOT / "scripts/run_policy_bound_null_calibration.py",
    }
    for key, path in expected_hashes.items():
        if provenance.get(key) != sha256(path):
            raise ValueError(f"run provenance is missing or mismatches {key}")
    if not provenance.get("source_git_commit_at_run"):
        raise ValueError("run provenance is missing the source commit")


def wilson_interval(events: int, trials: int) -> tuple[float, float]:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("require 0 <= events <= positive trials")
    z = 1.959963984540054
    rate = events / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return max(0.0, float(center - radius)), min(1.0, float(center + radius))


def clopper_pearson_upper(events: int, trials: int, confidence: float = 0.95) -> float:
    if trials <= 0 or not 0 <= events <= trials or not 0 < confidence < 1:
        raise ValueError("require valid binomial counts and confidence in (0, 1)")
    if events == trials:
        return 1.0
    return float(beta.ppf(confidence, events + 1, trials - events))


MAX_PRIMARY_FALSE_ESCALATIONS = max(
    events
    for events in range(501)
    if clopper_pearson_upper(events, 500, 1 - PRIMARY_ALPHA / 10) < PRIMARY_ALPHA
)


def validate_seed_block(seeds: pd.Series, *, method: str, scenario: str) -> None:
    if set(seeds) != EXPECTED_SEEDS:
        raise ValueError(f"{method}/{scenario} does not contain the exact registered seed block")


def analyze(output: Path) -> tuple[Path, Path]:
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["configuration"]
    if config != EXPECTED_CONFIG:
        raise ValueError("run configuration does not match the frozen calibration protocol")
    verify_run_provenance(manifest)
    verify_manifest_integrity(output, manifest)
    metrics = pd.read_parquet(output / "metrics/hard_budget_comparison.parquet")
    required = {
        "scenario",
        "seed",
        "method",
        "population_null_control",
        "budget_respected",
        "eprocess_minimum_propensity",
        "eprocess_support_bound",
        "query_propensity_min",
        *MONITORS.values(),
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics missing required fields: {sorted(missing)}")
    expected_rows = len(SCENARIOS) * len(METHODS) * 500
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError(f"expected {expected_rows} unique method-stream rows")
    if set(metrics.scenario) != set(SCENARIOS) or set(metrics.method) != set(METHODS):
        raise ValueError("scenario or method set differs from the frozen protocol")
    if not metrics.population_null_control.astype(bool).all():
        raise ValueError("a stream is not a registered population-null control")
    if not metrics.budget_respected.astype(bool).all():
        raise ValueError("a stream violated the hard label-dollar budget")
    scenario_map = {scenario.name: scenario for scenario in SCENARIO_DEFINITIONS}
    for method in METHODS:
        floor = 0.20 if method == "uniform_proxy" else 0.10
        group = metrics.loc[metrics.method.eq(method)]
        if not np.allclose(group.eprocess_minimum_propensity, floor, rtol=0, atol=1e-12):
            raise ValueError(f"{method} does not use its registered support floor {floor}")
        if (group.query_propensity_min < floor - 1e-10).any():
            raise ValueError(f"{method} realized a propensity below its declared floor")
        for scenario in SCENARIOS:
            cell = group.loc[group.scenario.eq(scenario)]
            if len(cell) != 500 or cell.seed.nunique() != 500:
                raise ValueError(f"{method}/{scenario} does not have 500 independent streams")
            outcome_bound = (
                max(scenario_map[scenario].fn_cost, scenario_map[scenario].fp_cost)
                + config["harm_margin"]
            )
            expected_bound = prediction_powered_bound(outcome_bound, floor)
            if not np.allclose(cell.eprocess_support_bound, expected_bound, rtol=0, atol=1e-12):
                raise ValueError(f"{method}/{scenario} uses an unexpected PPI support bound")
            validate_seed_block(cell.seed, method=method, scenario=scenario)

    rows: list[dict[str, object]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        for monitor, column in MONITORS.items():
            events = int(group[column].astype(bool).sum())
            trials = len(group)
            low, high = wilson_interval(events, trials)
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "monitor": monitor,
                    "support_floor": float(group.eprocess_minimum_propensity.iloc[0]),
                    "support_bound": float(
                        5.1 * (2 / group.eprocess_minimum_propensity.iloc[0] - 1)
                    ),
                    "streams": trials,
                    "false_escalations": events,
                    "false_escalation_rate": events / trials,
                    "wilson_95_low": low,
                    "wilson_95_high": high,
                    "clopper_pearson_95_upper": clopper_pearson_upper(events, trials),
                    "primary_familywise_95_upper": (
                        clopper_pearson_upper(events, trials, 1 - PRIMARY_ALPHA / 10)
                        if monitor == "fixed_mixture"
                        else np.nan
                    ),
                    "mean_labels": float(group.labels_queried.mean()),
                    "mean_spend": float(group.realized_label_spend.mean()),
                    "mean_budget": float(group.hard_budget.mean()),
                    "budget_violations": int((~group.budget_respected.astype(bool)).sum()),
                }
            )
    summary = pd.DataFrame(rows)
    primary = summary.loc[summary.monitor.eq("fixed_mixture")]
    passed = bool((primary.primary_familywise_95_upper < PRIMARY_ALPHA).all())
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analysis_dir / "policy_bound_null_calibration.csv"
    summary.to_csv(csv_path, index=False)
    report_path = output / "reports/policy_bound_null_calibration.md"
    lines = [
        "# Policy-specific-bound null calibration",
        "",
        "This is a frozen synthetic null-calibration study, not a harmful-regime power comparison or a real-world validity guarantee. Independent stream seeds are the calibration units. Each method uses its guaranteed propensity floor in the PPI support bound; the shared-bound option is disabled.",
        "",
        f"GPU: `{manifest.get('gpu_name', 'unknown')}`; resolved device: `{manifest.get('resolved_device', 'unknown')}`. Seeds: 500 per scenario, block `54000000–54000499`. The fixed-mixture primary family contains 10 policy-by-scenario cells; its simultaneous one-sided limits use Bonferroni familywise 95% coverage. The calibration criterion is **{'PASS' if passed else 'FAIL / INCONCLUSIVE'}**: every primary simultaneous upper limit must be below 0.05.",
        f"With 500 streams per primary cell, passing this criterion requires at most {MAX_PRIMARY_FALSE_ESCALATIONS} false escalations in every cell.",
        "",
        "|Scenario|Policy|Monitor|Floor|PPI bound|False escalations / streams|Rate|Wilson 95% interval|Pointwise exact upper|Primary familywise exact upper|Mean labels|Mean spend / cap|",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        family = (
            f"{row['primary_familywise_95_upper']:.5f}"
            if pd.notna(row["primary_familywise_95_upper"])
            else "—"
        )
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['monitor']}|{row['support_floor']:.2f}|{row['support_bound']:.2f}|{row['false_escalations']}/{row['streams']}|{row['false_escalation_rate']:.5f}|[{row['wilson_95_low']:.5f}, {row['wilson_95_high']:.5f}]|{row['clopper_pearson_95_upper']:.5f}|{family}|{row['mean_labels']:.1f}|{row['mean_spend']:.2f} / {row['mean_budget']:.2f}|"
        )
    lines.extend(
        [
            "",
            "The fixed-mixture primary familywise bound controls the ten registered method/scenario comparisons under arbitrary dependence between cells. PVA is a secondary existing comparator; PM-EB is exploratory. Their pointwise limits are descriptive and are not used to pass the primary calibration criterion.",
            "",
            "Calibration is limited to the registered stationary and benign-nuisance generators, immediate paired feedback, predictable query rules, the stated policy floors, the specified reference policy, and the conditional-mean assumptions. It does not establish validity with delayed, selectively sampled, serially dependent, misspecified, or post-selected feedback. A passing simulator calibration does not prove those assumptions in deployment.",
            "",
            "No visual was generated; PaperBanana was not available in the active environment.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    finalize_manifest(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_files = manifest["sha256"]["source_files"]
    for relative in (
        "scripts/run_policy_bound_null_calibration.py",
        "scripts/analyze_policy_bound_null_calibration.py",
        "docs/policy_bound_null_calibration_protocol.md",
    ):
        source_files[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    manifest.setdefault("run_provenance", {})["analysis_script_sha256"] = hashlib.sha256(
        Path(__file__).resolve().read_bytes()
    ).hexdigest()
    protocol_commit = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", PROTOCOL.as_posix()],
        cwd=ROOT,
        text=True,
    ).strip()
    manifest["run_provenance"]["protocol_commit"] = protocol_commit
    manifest["run_provenance"]["protocol_lock_commit"] = protocol_commit
    manifest["run_provenance"]["analysis_criterion"] = (
        "all 10 primary familywise upper bounds < 0.05"
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(report_path)
    print(summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    analyze(args.output)


if __name__ == "__main__":
    main()
