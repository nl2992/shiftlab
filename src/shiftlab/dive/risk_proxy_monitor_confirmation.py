"""Independent confirmation of fixed-mixture versus predictable-Kelly monitoring."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from ..data.gpu.environment import environment
from ..decision_harm_experiment import SCENARIOS
from .risk_proxy_monitor_grid import (
    NULL_SCENARIOS,
    RiskProxyMonitorGridConfig,
    _run_stream,
)

METHODS = ("fixed_mixture", "predictable_kelly")
ALTERNATIVES = ("boundary_local_harm", "harmful_adaptation")
QUERY_RATE = 0.20
FAMILYWISE_ALPHA = 0.05
NULL_CELL_COUNT = len(NULL_SCENARIOS) * len(METHODS)
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20405024


def _cluster_bootstrap(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
    return [float(value) for value in np.quantile(values[indices].mean(axis=1), [0.025, 0.975])]


def _summarize(metrics: pd.DataFrame, null_seeds: int):
    null_rows = []
    alpha_cell = FAMILYWISE_ALPHA / NULL_CELL_COUNT
    null_data = metrics[metrics.is_population_null]
    for (scenario, method), group in null_data.groupby(["scenario", "method"], sort=True):
        count, n = int(group.false_alarm.sum()), len(group)
        upper = 1.0 if count == n else float(beta.ppf(1 - alpha_cell, count + 1, n - count))
        null_rows.append(
            {
                "scenario": scenario,
                "method": method,
                "false_alarms": count,
                "streams": n,
                "false_alarm_rate": count / n,
                "bonferroni_one_sided_cp95_upper": upper,
                "familywise_alpha": FAMILYWISE_ALPHA,
                "family_cells": NULL_CELL_COUNT,
                "calibration_pass": upper <= 0.05,
            }
        )

    alternatives = metrics[metrics.material_harm]
    summaries = (
        alternatives.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            false_alarms=("false_alarm", "sum"),
            mean_detection_delay=("detection_delay", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_events_processed=("events_processed", "mean"),
        )
        .reset_index()
    )
    alt_wide = alternatives.pivot(index=["seed", "scenario"], columns="method", values="detected")
    seed_difference = (
        (alt_wide["fixed_mixture"].astype(float) - alt_wide["predictable_kelly"].astype(float))
        .groupby(level="seed")
        .mean()
    )
    macro = seed_difference.to_numpy()
    macro_ci = _cluster_bootstrap(macro)
    contrasts = [
        {
            "scenario": "macro_two_alternatives",
            "fixed_detection_rate": float(alt_wide["fixed_mixture"].mean()),
            "kelly_detection_rate": float(alt_wide["predictable_kelly"].mean()),
            "fixed_minus_kelly": float(macro.mean()),
            "seed_cluster_ci95_low": macro_ci[0],
            "seed_cluster_ci95_high": macro_ci[1],
            "seed_clusters": len(macro),
            "primary": True,
        }
    ]
    for scenario in ALTERNATIVES:
        cell = alternatives[alternatives.scenario == scenario].pivot(
            index="seed", columns="method", values="detected"
        )
        values = (
            cell["fixed_mixture"].astype(float) - cell["predictable_kelly"].astype(float)
        ).to_numpy()
        ci = _cluster_bootstrap(values)
        contrasts.append(
            {
                "scenario": scenario,
                "fixed_detection_rate": float(cell["fixed_mixture"].mean()),
                "kelly_detection_rate": float(cell["predictable_kelly"].mean()),
                "fixed_minus_kelly": float(values.mean()),
                "seed_cluster_ci95_low": ci[0],
                "seed_cluster_ci95_high": ci[1],
                "seed_clusters": len(values),
                "primary": False,
            }
        )
    contrast_frame = pd.DataFrame(contrasts)
    calibration = pd.DataFrame(null_rows)
    retained = bool(
        calibration.calibration_pass.all()
        and macro_ci[0] > 0
        and all(
            contrast_frame.loc[contrast_frame.scenario == scenario, "fixed_minus_kelly"].iloc[0]
            >= 0
            for scenario in ALTERNATIVES
        )
    )
    decision = {
        "null_calibration_pass": bool(calibration.calibration_pass.all()),
        "primary_macro_interval_above_zero": bool(macro_ci[0] > 0),
        "no_registered_scenario_point_loss": bool(
            all(
                contrast_frame.loc[contrast_frame.scenario == scenario, "fixed_minus_kelly"].iloc[0]
                >= 0
                for scenario in ALTERNATIVES
            )
        ),
        "advance_fixed_mixture": retained,
    }
    return summaries, calibration, contrast_frame, decision


def run_risk_proxy_monitor_confirmation(
    output_dir: str | Path,
    *,
    null_seeds: int = 2000,
    alternative_seeds: int = 1000,
    seed_offset: int = 20405024,
    n: int = 2400,
    device: str = "cuda",
) -> tuple[pd.DataFrame, dict]:
    config = RiskProxyMonitorGridConfig(
        n=n,
        null_seeds=null_seeds,
        alternative_seeds=alternative_seeds,
        seed_offset=seed_offset,
        device=device,
    ).validate()
    scenario_map = {scenario.name: scenario for scenario in SCENARIOS}
    rows = []
    seed_ranges = {}
    for scenario_name in NULL_SCENARIOS + ALTERNATIVES:
        is_null = scenario_name in NULL_SCENARIOS
        count = null_seeds if is_null else alternative_seeds
        start = seed_offset if is_null else seed_offset + null_seeds
        seed_ranges[scenario_name] = [start, start + count - 1]
        for seed in range(start, start + count):
            stream_rows = _run_stream(scenario_map[scenario_name], seed, QUERY_RATE, config)
            rows.extend(row for row in stream_rows if row["method"] in METHODS)
    metrics = pd.DataFrame(rows)
    summary, calibration, contrasts, decision = _summarize(metrics, null_seeds)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "scenario_summary.csv", index=False)
    calibration.to_csv(output / "null_calibration.csv", index=False)
    contrasts.to_csv(output / "paired_contrasts.csv", index=False)
    runner = Path(__file__)
    monitor_runner = runner.with_name("risk_proxy_monitor_grid.py")
    eprocess = runner.with_name("eprocess.py")
    experiment = runner.parent.parent / "decision_harm_experiment.py"
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "design": {
            "n": n,
            "null_seeds": null_seeds,
            "alternative_seeds": alternative_seeds,
            "seed_offset": seed_offset,
            "seed_ranges": seed_ranges,
            "query_rate": QUERY_RATE,
            "alpha": config.alpha,
            "harm_margin": config.harm_margin,
            "null_scenarios": list(NULL_SCENARIOS),
            "alternative_scenarios": list(ALTERNATIVES),
            "methods": list(METHODS),
            "familywise_null_cells": NULL_CELL_COUNT,
        },
        "metric_rows": len(metrics),
        "independent_of_development_seed_blocks": True,
        "decision": decision,
        "primary_macro_difference": {
            "fixed_minus_kelly": float(contrasts.iloc[0].fixed_minus_kelly),
            "seed_cluster_ci95_low": float(contrasts.iloc[0].seed_cluster_ci95_low),
            "seed_cluster_ci95_high": float(contrasts.iloc[0].seed_cluster_ci95_high),
            "seed_clusters": int(contrasts.iloc[0].seed_clusters),
        },
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            "risk_proxy_monitor_confirmation.py": hashlib.sha256(runner.read_bytes()).hexdigest(),
            "risk_proxy_monitor_grid.py": hashlib.sha256(monitor_runner.read_bytes()).hexdigest(),
            "eprocess.py": hashlib.sha256(eprocess.read_bytes()).hexdigest(),
            "decision_harm_experiment.py": hashlib.sha256(experiment.read_bytes()).hexdigest(),
        },
        "environment": environment(),
        "interpretation": "Independent-seed confirmation with a frozen 20% query rate and primary paired detection contrast; finite Monte Carlo calibration does not replace the process validity proof.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Independent fixed-mixture monitor confirmation",
        "",
        f"Independent seed blocks: {seed_ranges}. Query rate: {QUERY_RATE:.0%}. Streams: {len(metrics):,} monitor-stream rows.",
        "",
        "## Frozen decision rule",
        "",
        "Advance the fixed-mixture monitor only if all four Bonferroni null cells pass the 5% upper-bound screen, the paired macro detection interval across boundary harm and harmful adaptation is entirely above zero, and neither scenario's point estimate favors Kelly.",
        "",
        f"Decision: `{decision}`",
        "",
        "## Alternative results",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired primary and scenario contrasts",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Independent null calibration",
        "",
        calibration.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The monitors share the same frozen logistic proxy, Bernoulli queries, labels, spend, and stopping horizon. This is a baseline confirmation, not a novel method. Its e-process claims still require the stated history-conditional null, known support bounds, and outcome-independent query randomization.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return metrics, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/risk_proxy_monitor_confirmation")
    parser.add_argument("--null-seeds", type=int, default=2000)
    parser.add_argument("--alternative-seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20405024)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, manifest = run_risk_proxy_monitor_confirmation(
        args.output_dir,
        null_seeds=args.null_seeds,
        alternative_seeds=args.alternative_seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
    )
    print(f"decision={manifest['decision']}")
    print(f"primary={manifest['primary_macro_difference']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
