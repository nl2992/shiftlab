"""Summarize the paired 36-cell harm power screen without selecting a winner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from run_harm_power_grid import _plot

from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/harm_power_grid_30"
MONITORS = (
    "fixed_mixture",
    "predictable_variance",
    "predictable_empirical_bernstein",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _monotone_fraction(
    summary: pd.DataFrame,
    *,
    scenario: str,
    monitor: str,
    factor: str,
    conditioning: list[str],
    order: list[float],
    direction: str,
) -> tuple[int, int]:
    subset = summary.loc[summary.scenario.eq(scenario) & summary.monitor.eq(monitor)]
    successes = total = 0
    for _, group in subset.groupby(conditioning, sort=True):
        values = group.set_index(factor).detection_rate_all_material_harm.reindex(order)
        if values.isna().any():
            continue
        diffs = np.diff(values.to_numpy(float))
        successes += int(
            np.all(diffs >= -1e-12) if direction == "increasing" else np.all(diffs <= 1e-12)
        )
        total += 1
    return successes, total


def analyze(
    metrics: pd.DataFrame, summary: pd.DataFrame, paired: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, object]]:
    cell_keys = ["scenario", "n", "scenario_severity", "change_fraction"]
    cells = metrics[cell_keys].drop_duplicates()
    cell_sizes = metrics.groupby(cell_keys, dropna=False).size()
    if len(metrics) != 1080 or len(cells) != 36 or not cell_sizes.eq(30).all():
        raise ValueError("expected 36 grid cells with 30 paired streams each")
    if metrics.material_harm.sum() != len(metrics):
        raise ValueError("the registered grid contains a stream without material harm")
    unreached = int(
        (
            metrics.material_harm.astype(bool)
            & ~metrics.harm_reached_before_budget_stop.astype(bool)
        ).sum()
    )
    cap_violations = int((~metrics.budget_respected.astype(bool)).sum())
    if unreached or cap_violations:
        raise ValueError(f"unexpected censored onsets={unreached}, cap violations={cap_violations}")
    expected_monitors = set(MONITORS)
    if set(summary.monitor) != expected_monitors or len(summary) != 108:
        raise ValueError("summary must contain all three monitors in each of 36 cells")

    trend_rows = []
    monotonicities: dict[str, object] = {}
    for scenario in ("boundary_local_harm", "recurring_regimes"):
        for monitor in MONITORS:
            cell_rows = summary.loc[summary.scenario.eq(scenario) & summary.monitor.eq(monitor)]
            trend_rows.append(
                {
                    "scenario": scenario,
                    "monitor": monitor,
                    "mean_cell_detection_rate": float(
                        cell_rows.detection_rate_all_material_harm.mean()
                    ),
                    "median_cell_delay": float(cell_rows.median_delay_given_detection.median()),
                }
            )
            horizon = _monotone_fraction(
                summary,
                scenario=scenario,
                monitor=monitor,
                factor="n",
                conditioning=["scenario_severity", "change_fraction"],
                order=[2400, 3200, 4000],
                direction="increasing",
            )
            severity = _monotone_fraction(
                summary,
                scenario=scenario,
                monitor=monitor,
                factor="scenario_severity",
                conditioning=["n", "change_fraction"],
                order=[0.75, 1.5, 2.25],
                direction="increasing",
            )
            item: dict[str, object] = {
                "scenario": scenario,
                "monitor": monitor,
                "horizon_increasing_cells": horizon[0],
                "horizon_total_cells": horizon[1],
                "severity_increasing_cells": severity[0],
                "severity_total_cells": severity[1],
            }
            if scenario == "boundary_local_harm":
                onset = _monotone_fraction(
                    summary,
                    scenario=scenario,
                    monitor=monitor,
                    factor="change_fraction",
                    conditioning=["n", "scenario_severity"],
                    order=[0.35, 0.5, 0.65],
                    direction="decreasing",
                )
                item.update(
                    {
                        "earlier_onset_nonincreasing_cells": onset[0],
                        "onset_total_cells": onset[1],
                    }
                )
            monotonicities[f"{scenario}:{monitor}"] = item

    paired_counts = paired.groupby("comparator", sort=True)[
        ["fixed_only_detections", "comparator_only_detections", "discordant_pairs"]
    ].sum()
    for comparator in paired_counts.index:
        monotonicities[f"paired_fixed_vs_{comparator}"] = {
            field: int(paired_counts.loc[comparator, field]) for field in paired_counts.columns
        }
    monotonicities["data_integrity"] = {
        "stream_rows": len(metrics),
        "cells": len(cells),
        "streams_per_cell": 30,
        "material_harm_misses": int((~metrics.material_harm.astype(bool)).sum()),
        "unreached_harm_onsets": unreached,
        "budget_violations": cap_violations,
    }
    return pd.DataFrame(trend_rows), monotonicities


def _cell_rate(summary: pd.DataFrame, scenario: str, monitor: str, **where: float) -> pd.Series:
    mask = summary.scenario.eq(scenario) & summary.monitor.eq(monitor)
    for column, value in where.items():
        mask &= summary[column].eq(value)
    selected = summary.loc[mask]
    if len(selected) != 1:
        raise ValueError(f"expected one grid cell for {scenario}/{monitor}/{where}")
    return selected.iloc[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    metrics = pd.read_parquet(output / "metrics/harm_power_grid.parquet")
    summary = pd.read_csv(output / "metrics/harm_power_grid_summary.csv")
    paired = pd.read_csv(output / "metrics/harm_power_grid_paired_tests.csv")
    trends, facts = analyze(metrics, summary, paired)
    trends_path = output / "metrics/harm_power_grid_trends.csv"
    trends.to_csv(trends_path, index=False)
    figure_path = output / "figures/harm_power_grid.png"
    _plot(summary, figure_path)

    baseline_onsets = [
        _cell_rate(
            summary,
            "boundary_local_harm",
            "fixed_mixture",
            n=3200,
            scenario_severity=1.5,
            change_fraction=fraction,
        )
        for fraction in (0.35, 0.5, 0.65)
    ]
    baseline_severity = [
        _cell_rate(
            summary,
            "boundary_local_harm",
            "fixed_mixture",
            n=3200,
            scenario_severity=severity,
            change_fraction=0.5,
        )
        for severity in (0.75, 1.5, 2.25)
    ]
    baseline_horizon = [
        _cell_rate(
            summary,
            "boundary_local_harm",
            "fixed_mixture",
            n=n,
            scenario_severity=1.5,
            change_fraction=0.5,
        )
        for n in (2400, 3200, 4000)
    ]
    recurring_horizon = [
        _cell_rate(
            summary,
            "recurring_regimes",
            "fixed_mixture",
            n=n,
            scenario_severity=1.5,
            change_fraction=0.5,
        )
        for n in (2400, 3200, 4000)
    ]
    fixed_var = facts["paired_fixed_vs_predictable_variance"]
    fixed_pm = facts["paired_fixed_vs_predictable_empirical_bernstein"]
    boundary_monotonicity = "; ".join(
        f"{monitor}: horizon {facts[f'boundary_local_harm:{monitor}']['horizon_increasing_cells']}/"
        f"{facts[f'boundary_local_harm:{monitor}']['horizon_total_cells']}, severity "
        f"{facts[f'boundary_local_harm:{monitor}']['severity_increasing_cells']}/"
        f"{facts[f'boundary_local_harm:{monitor}']['severity_total_cells']}, earlier onset "
        f"{facts[f'boundary_local_harm:{monitor}']['earlier_onset_nonincreasing_cells']}/"
        f"{facts[f'boundary_local_harm:{monitor}']['onset_total_cells']}"
        for monitor in MONITORS
    )
    recurring_monotonicity = "; ".join(
        f"{monitor}: horizon {facts[f'recurring_regimes:{monitor}']['horizon_increasing_cells']}/"
        f"{facts[f'recurring_regimes:{monitor}']['horizon_total_cells']}, severity "
        f"{facts[f'recurring_regimes:{monitor}']['severity_increasing_cells']}/"
        f"{facts[f'recurring_regimes:{monitor}']['severity_total_cells']}"
        for monitor in MONITORS
    )
    lines = [
        "# Harm severity/onset/horizon grid: measured results",
        "",
        "This CUDA development screen completed 1,080 stream-cell observations across 36 cells (30 paired seeds per cell). All 1,080 evaluator-classified streams had material harm, all 1,080 harm onsets were reached before budget stopping, and all respected the realized dollar cap. There were no missing cells or incomplete seed blocks.",
        "",
        "## Main measured patterns",
        "",
        "|Scenario|Monitor|Mean detection rate across cells|Median cell delay among detections|",
        "|---|---|---:|---:|",
    ]
    for row in trends.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['monitor']}|{row['mean_cell_detection_rate']:.3f}|"
            f"{row['median_cell_delay']:.1f}|"
        )
    lines.extend(
        [
            "",
            f"Empirical monotonicity counts for boundary-local harm (successes/conditioning slices): {boundary_monotonicity}. Recurring-regime counts are {recurring_monotonicity}. These are observed grid patterns, not population guarantees.",
            "",
            "At the central boundary-local setting (`n=3200`, severity 1.50), fixed-mixture detection was "
            + " → ".join(f"{row.detection_rate_all_material_harm:.2f}" for row in baseline_onsets)
            + " as onset fraction moved .35 → .50 → .65; it was "
            + " → ".join(f"{row.detection_rate_all_material_harm:.2f}" for row in baseline_severity)
            + " as severity moved .75 → 1.50 → 2.25; and "
            + " → ".join(f"{row.detection_rate_all_material_harm:.2f}" for row in baseline_horizon)
            + " as n moved 2400 → 3200 → 4000. These rates use 30 streams per cell and each cell has its own Wilson interval in the main summary CSV.",
            "",
            "For recurring regimes at severity 1.50, fixed-mixture rates were "
            + " → ".join(f"{row.detection_rate_all_material_harm:.2f}" for row in recurring_horizon)
            + " across n=2400, 3200, 4000.",
            "",
            f"Across all cells, there were {fixed_var['fixed_only_detections']} fixed-only versus {fixed_var['comparator_only_detections']} variance-only detections, and {fixed_pm['fixed_only_detections']} fixed-only versus {fixed_pm['comparator_only_detections']} PM-EB-only detections. Because seed streams recur across the parameter cells, these pooled discordances are descriptive and are not treated as independent tests. Cellwise exact p-values in `harm_power_grid_paired_tests.csv` are exploratory and unadjusted.",
            "",
            "## Interpretation and limits",
            "",
            "The screen supports the earlier conclusion that fixed mixture is a strong baseline in these settings, while PM-EB is substantially more conservative. The fixed-mixture advantage over predictable variance is largest at earlier onsets and stronger harm; the two are closer in some high-severity/long-horizon cells. These patterns do not identify a new algorithm. The 20% dollar budget scales with the available horizon, so horizon trends combine more observation time with more total label dollars. They are not a fixed-total-cost causal comparison.",
            "",
            "This is a 30-seed development grid, not a final confirmatory test. No false-alarm controls were included in this alternative-only screen; the independent null calibration is reported separately. The bounded e-process result remains conditional on the history-conditional mean null and valid propensity/increment bounds, and the experiment does not cover delayed feedback, serial dependence outside the registered generator, or real-world distribution shift.",
            "",
            "## Reproduction and artifacts",
            "",
            "Rebuild the grid using `docs/harm_power_grid_protocol.md` and run `uv run python scripts/analyze_harm_power_grid.py` for this summary. See the full 108-cell monitor table in `reports/harm_power_grid.md`, stream metrics in `metrics/harm_power_grid.parquet`, cellwise paired contrasts in `metrics/harm_power_grid_paired_tests.csv`, and the figure `figures/harm_power_grid.png`.",
        ]
    )
    report_path = output / "reports/harm_power_grid_results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_path = output / "reports/manifest.json"
    manifest_before = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_script_hash = manifest_before.get("sha256", {}).get("grid_script")
    finalize_manifest(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["analysis_script_sha256"] = _sha256(Path(__file__).resolve())
    if run_script_hash:
        manifest["grid_script_sha256_at_run"] = run_script_hash
    manifest["grid_screen_interpretation"] = (
        "descriptive only; paired seed IDs recur across cells, and total dollar budget scales with horizon"
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {trends_path.relative_to(ROOT).as_posix()}")
    print(f"Wrote {report_path.relative_to(ROOT).as_posix()}")
    print(trends.to_string(index=False))


if __name__ == "__main__":
    main()
