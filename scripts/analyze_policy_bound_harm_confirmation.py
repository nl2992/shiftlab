"""Analyze the frozen, paired policy-specific-bound harm confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm

from shiftlab.decision_harm_experiment import SCENARIOS as SCENARIO_DEFINITIONS
from shiftlab.dive.estimators import prediction_powered_bound
from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/policy_bound_harm_confirmation_200"
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIOS = ("boundary_local_harm", "recurring_regimes", "harmful_adaptation")
MONITORS = {
    "fixed_mixture": "single_e_detected",
    "predictable_variance": "variance_adaptive_detected",
    "pm_eb": "pm_eb_detected",
}
DELAY_COLUMNS = {
    "fixed_mixture": "single_e_delay",
    "predictable_variance": "variance_adaptive_delay",
    "pm_eb": "pm_eb_delay",
}
PRIMARY_MONITOR = "fixed_mixture"
ADAPTIVE_METHODS = METHODS[1:]


def wilson_interval(events: int, trials: int) -> tuple[float, float]:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("require 0 <= events <= positive trials")
    z = float(norm.ppf(0.975))
    rate = events / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return max(0.0, float(center - radius)), min(1.0, float(center + radius))


def holm_adjust(p_values: list[float]) -> list[float]:
    """Return Holm familywise-adjusted p-values in their original order."""
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or not len(values) or np.any(~np.isfinite(values)):
        raise ValueError("p-values must be a nonempty finite one-dimensional sequence")
    if np.any((values < 0) | (values > 1)):
        raise ValueError("p-values must lie in [0, 1]")
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    factors = len(values) - np.arange(len(values))
    adjusted_sorted = np.maximum.accumulate(factors * sorted_values).clip(max=1)
    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = adjusted_sorted
    return adjusted.tolist()


def paired_detection_pvalue(method_only: int, uniform_only: int) -> float:
    """One-sided exact McNemar/sign-test p-value for higher method detection."""
    discordant = method_only + uniform_only
    if min(method_only, uniform_only) < 0:
        raise ValueError("discordant counts must be nonnegative")
    if discordant == 0:
        return 1.0
    return float(binomtest(method_only, discordant, p=0.5, alternative="greater").pvalue)


def paired_bootstrap_interval(
    differences: np.ndarray, *, seed: int, repetitions: int = 10_000
) -> tuple[float, float]:
    if differences.ndim != 1 or not len(differences) or repetitions < 1:
        raise ValueError("paired bootstrap requires observations and positive repetitions")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(differences), size=(repetitions, len(differences)))
    means = differences[draws].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def _verify_run(output: Path) -> pd.DataFrame:
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["configuration"]
    if config["common_eprocess_bound"]:
        raise ValueError("the frozen comparison requires method-specific support bounds")
    if config["seeds"] != 200 or config["seed_offset"] != 55_000_000:
        raise ValueError("run does not match the frozen seed block and sample size")
    if (
        config["n"] != 3200
        or config["d"] != 16
        or config["budget_rate"] != 0.20
        or config["q_min"] != 0.10
        or config["q_max"] != 0.80
        or config["harm_margin"] != 0.10
        or set(config["scenario_subset"]) != set(SCENARIOS)
        or set(config["method_subset"]) != set(METHODS)
        or manifest.get("resolved_device") != "cuda"
    ):
        raise ValueError("run configuration differs from the frozen protocol")
    metrics = pd.read_parquet(output / "metrics/hard_budget_comparison.parquet")
    required = {
        "scenario",
        "seed",
        "method",
        "material_harm",
        "population_null_control",
        "budget_respected",
        "hard_budget",
        "realized_label_spend",
        "eprocess_minimum_propensity",
        "eprocess_support_bound",
        "query_propensity_min",
        "labels_queried",
        "processed_events",
        "harm_reached_before_budget_stop",
        "single_e_detected",
        "single_e_delay",
        "variance_adaptive_detected",
        "variance_adaptive_delay",
        "pm_eb_detected",
        "pm_eb_delay",
        "stream_mean_estimation_rmse",
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics are missing fields: {sorted(missing)}")
    expected_rows = len(SCENARIOS) * len(METHODS) * 200
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError(f"expected {expected_rows} unique method-stream rows")
    if set(metrics.scenario) != set(SCENARIOS) or set(metrics.method) != set(METHODS):
        raise ValueError("scenario or policy set differs from the frozen protocol")
    expected_seeds = set(range(55_000_000, 55_000_200))
    if set(metrics.seed.astype(int)) != expected_seeds:
        raise ValueError("metrics do not contain the complete frozen seed block")
    if metrics.population_null_control.astype(bool).any():
        raise ValueError("an alternative stream was classified as a population-null control")
    if not metrics.budget_respected.astype(bool).all():
        raise ValueError("a stream violated the hard label-dollar budget")
    if (metrics.realized_label_spend > metrics.hard_budget + 1e-8).any():
        raise ValueError("realized spend exceeds the saved hard budget")

    scenario_map = {scenario.name: scenario for scenario in SCENARIO_DEFINITIONS}
    for method in METHODS:
        floor = 0.20 if method == "uniform_proxy" else 0.10
        group = metrics.loc[metrics.method.eq(method)]
        if not np.allclose(group.eprocess_minimum_propensity, floor, rtol=0, atol=1e-12):
            raise ValueError(f"{method} does not use its registered floor {floor}")
        if (group.query_propensity_min < floor - 1e-10).any():
            raise ValueError(f"{method} realized a query probability below its floor")
        for scenario in SCENARIOS:
            cell = group.loc[group.scenario.eq(scenario)]
            if len(cell) != 200 or cell.seed.nunique() != 200:
                raise ValueError(f"{method}/{scenario} does not contain 200 independent seeds")
            outcome_bound = (
                max(scenario_map[scenario].fn_cost, scenario_map[scenario].fp_cost)
                + config["harm_margin"]
            )
            expected_bound = prediction_powered_bound(outcome_bound, floor)
            if not np.allclose(cell.eprocess_support_bound, expected_bound, rtol=0, atol=1e-12):
                raise ValueError(f"{method}/{scenario} uses an unexpected support bound")
    return metrics


def analyze(output: Path) -> tuple[Path, Path]:
    metrics = _verify_run(output)
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        material = group.loc[group.material_harm.astype(bool)]
        if material.empty:
            raise ValueError(f"{scenario}/{method} has no evaluator-defined material-harm streams")
        reached = material.harm_reached_before_budget_stop.astype(bool)
        for monitor, column in MONITORS.items():
            detected = material[column].astype(bool)
            low, high = wilson_interval(int(detected.sum()), len(material))
            detected_delay = material.loc[detected, DELAY_COLUMNS[monitor]].dropna()
            summary_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "monitor": monitor,
                    "material_harm_streams": len(material),
                    "harm_onsets_reached": int(reached.sum()),
                    "detections": int(detected.sum()),
                    "detection_rate": float(detected.mean()),
                    "detection_wilson_95_low": low,
                    "detection_wilson_95_high": high,
                    "detection_among_reached": (
                        float(detected.loc[reached].mean()) if reached.any() else np.nan
                    ),
                    "mean_delay_among_detections": (
                        float(detected_delay.mean()) if len(detected_delay) else np.nan
                    ),
                    "mean_labels": float(material.labels_queried.mean()),
                    "mean_realized_spend": float(material.realized_label_spend.mean()),
                    "mean_hard_budget": float(material.hard_budget.mean()),
                    "mean_processed_events": float(material.processed_events.mean()),
                    "mean_stream_rmse": float(material.stream_mean_estimation_rmse.mean()),
                    "budget_violations": int((~material.budget_respected.astype(bool)).sum()),
                }
            )
    summary = pd.DataFrame(summary_rows)
    summary_path = analysis_dir / "policy_bound_harm_confirmation.csv"
    summary.to_csv(summary_path, index=False)

    tests: list[dict[str, object]] = []
    p_values: list[float] = []
    for scenario in SCENARIOS:
        scenario_metrics = metrics.loc[metrics.scenario.eq(scenario)]
        pivot = scenario_metrics.pivot(index="seed", columns="method", values="single_e_detected")
        harm = scenario_metrics.pivot(index="seed", columns="method", values="material_harm")
        if not harm.eq(harm.iloc[:, 0], axis=0).all().all():
            raise ValueError(f"evaluator harm eligibility differs by policy in {scenario}")
        eligible = harm.iloc[:, 0].astype(bool)
        if not eligible.any():
            raise ValueError(f"{scenario} has no eligible paired seeds")
        for method in ADAPTIVE_METHODS:
            pair = pivot.loc[eligible, ["uniform_proxy", method]].astype(bool)
            method_only = int((pair[method] & ~pair.uniform_proxy).sum())
            uniform_only = int((~pair[method] & pair.uniform_proxy).sum())
            differences = (
                pair[method].astype(float).to_numpy() - pair.uniform_proxy.astype(float).to_numpy()
            )
            p_values.append(paired_detection_pvalue(method_only, uniform_only))
            low, high = paired_bootstrap_interval(
                differences,
                seed=55_100_000 + SCENARIOS.index(scenario) * 10 + ADAPTIVE_METHODS.index(method),
            )
            tests.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "reference_method": "uniform_proxy",
                    "primary_monitor": PRIMARY_MONITOR,
                    "eligible_seeds": int(eligible.sum()),
                    "method_only_detections": method_only,
                    "uniform_only_detections": uniform_only,
                    "paired_detection_rate_difference": float(differences.mean()),
                    "paired_bootstrap_95_low": low,
                    "paired_bootstrap_95_high": high,
                    "mcnemar_one_sided_p": p_values[-1],
                }
            )
    adjusted = holm_adjust(p_values)
    for row, p_adjusted in zip(tests, adjusted, strict=True):
        row["holm_adjusted_p"] = p_adjusted
        row["holm_significant_0_05"] = bool(p_adjusted < 0.05)
    tests_frame = pd.DataFrame(tests)
    tests_path = analysis_dir / "policy_bound_harm_paired_tests.csv"
    tests_frame.to_csv(tests_path, index=False)

    lines = [
        "# Policy-specific-bound harmful-stream confirmation",
        "",
        "This report compares five label-query policies at a matched 20% pathwise dollar cap, with policy-specific propensity support bounds. It is evidence only for the registered synthetic streams and does not establish a deployment guarantee or algorithmic novelty.",
        "",
        f"GPU: `{json.loads((output / 'reports/manifest.json').read_text(encoding='utf-8')).get('gpu_name', 'unknown')}`; resolved device: `cuda`; independent seeds: 200 per scenario; seed block: `55000000–55000199`.",
        "",
        "## Detection outcomes",
        "",
        "|Scenario|Policy|Monitor|Material streams|Onsets reached|Detections|Rate (Wilson 95%)|Rate among reached|Mean delay if detected|Mean labels|Mean spend / cap|Mean events|Mean RMSE|",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['monitor']}|{row['material_harm_streams']}|{row['harm_onsets_reached']}|{row['detections']}|{row['detection_rate']:.3f} [{row['detection_wilson_95_low']:.3f}, {row['detection_wilson_95_high']:.3f}]|{row['detection_among_reached']:.3f}|{row['mean_delay_among_detections']:.1f}|{row['mean_labels']:.1f}|{row['mean_realized_spend']:.2f} / {row['mean_hard_budget']:.2f}|{row['mean_processed_events']:.1f}|{row['mean_stream_rmse']:.4f}|"
        )
    lines.extend(
        [
            "",
            "## Paired primary comparisons",
            "",
            "The primary monitor is the fixed mixture. Each adaptive policy is compared with uniform by a one-sided exact McNemar test across paired seed streams; Holm adjustment covers all 12 policy-by-scenario tests.",
            "",
            "|Scenario|Policy vs uniform|Method-only / uniform-only|Paired rate difference (bootstrap 95%)|Exact p|Holm p|",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in tests:
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['method_only_detections']} / {row['uniform_only_detections']}|{row['paired_detection_rate_difference']:.3f} [{row['paired_bootstrap_95_low']:.3f}, {row['paired_bootstrap_95_high']:.3f}]|{row['mcnemar_one_sided_p']:.5g}|{row['holm_adjusted_p']:.5g}|"
        )
    lines.extend(
        [
            "",
            "A query policy shows a confirmatory detection improvement only where its adjusted p-value is below 0.05 and its paired effect is positive. All nondetections remain in the all-material-harm denominator; rates among onset-reached streams are reported separately. The event horizon can vary under the shared hard dollar cap, so these results compare resource-constrained policies rather than fixed-horizon monitors.",
            "",
            "No figure was generated; PaperBanana was unavailable in the active environment.",
            "",
        ]
    )
    report_path = output / "reports/policy_bound_harm_confirmation.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    finalize_manifest(output)
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_files = manifest["sha256"]["source_files"]
    for relative in (
        "scripts/run_policy_bound_harm_confirmation.py",
        "scripts/analyze_policy_bound_harm_confirmation.py",
        "docs/policy_bound_harm_confirmation_protocol.md",
    ):
        source_files[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    manifest.setdefault("run_provenance", {})["analysis_script_sha256"] = hashlib.sha256(
        Path(__file__).resolve().read_bytes()
    ).hexdigest()
    manifest["run_provenance"]["paired_comparison_tests"] = 12
    manifest["run_provenance"]["holm_familywise_alpha"] = 0.05
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(report_path)
    print(summary.to_string(index=False))
    print(tests_frame.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    analyze(args.output)


if __name__ == "__main__":
    main()
