"""Independently calibrate the frozen direct-IPW history-evidence query rule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import beta

from .experiment import finalize_manifest
from .hard_budget import HardBudgetConfig, run_hard_budget

FROZEN_CANDIDATE = "evidence_curve_a0_p0.5"
BASELINE = "uniform_proxy"
CALIBRATION_METHODS = (BASELINE, FROZEN_CANDIDATE)
CALIBRATION_SCENARIOS = ("stationary", "benign_nuisance")
FAMILYWISE_ALPHA = 0.05
MAX_FALSE_ESCALATION_RATE = 0.05
MINIMUM_CALIBRATION_SEEDS = 2_000


def summarize_direct_ipw_query_calibration(
    metrics: pd.DataFrame,
    *,
    expected_seeds: int,
    familywise_alpha: float = FAMILYWISE_ALPHA,
) -> pd.DataFrame:
    """Summarize exact simultaneous one-sided false-escalation limits."""
    required = {
        "scenario",
        "seed",
        "method",
        "population_null_control",
        "material_harm",
        "single_e_false_escalation",
        "budget_respected",
        "monitor_estimator",
        "query_propensity_min",
        "eprocess_support_bound",
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics are missing required columns: {sorted(missing)}")
    if expected_seeds < 1 or not 0 < familywise_alpha < 1:
        raise ValueError("expected_seeds and familywise_alpha must be positive and valid")
    if not metrics.population_null_control.astype(bool).all():
        raise ValueError("calibration input contains a non-null stream")
    if metrics.material_harm.astype(bool).any():
        raise ValueError("calibration input contains evaluator-defined material harm")
    if set(metrics.scenario) != set(CALIBRATION_SCENARIOS):
        raise ValueError("calibration must contain exactly the two frozen null scenarios")
    if set(metrics.method) != set(CALIBRATION_METHODS):
        raise ValueError("calibration must contain exactly uniform and the frozen candidate")
    if set(metrics.monitor_estimator) != {"direct_ipw"}:
        raise ValueError("calibration must use the direct-IPW monitor")
    if not metrics.budget_respected.astype(bool).all():
        raise ValueError("calibration contains a hard label-dollar cap violation")
    if metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError("calibration has duplicate scenario/seed/method keys")
    propensity_floor = metrics.groupby("scenario").query_propensity_min.min()
    if (propensity_floor < 0.05 - 1e-12).any():
        raise ValueError("a query propensity fell below the frozen 0.05 support floor")
    support_counts = metrics.groupby("scenario").eprocess_support_bound.nunique()
    if (support_counts != 1).any():
        raise ValueError("methods do not share the registered global support bound")

    cell_count = len(CALIBRATION_SCENARIOS) * len(CALIBRATION_METHODS)
    per_cell_alpha = familywise_alpha / cell_count
    rows: list[dict[str, object]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        n = len(group)
        if group.seed.nunique() != n:
            raise ValueError("a calibration cell repeats a seed")
        false_escalations = int(group.single_e_false_escalation.astype(bool).sum())
        upper = (
            1.0
            if false_escalations == n
            else float(beta.ppf(1 - per_cell_alpha, false_escalations + 1, n - false_escalations))
        )
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": n,
                "false_escalations": false_escalations,
                "false_escalation_rate": false_escalations / n,
                "simultaneous_cp95_upper": upper,
                "cell_alpha": per_cell_alpha,
                "max_false_escalation_rate": MAX_FALSE_ESCALATION_RATE,
                "cell_passes": (
                    expected_seeds >= MINIMUM_CALIBRATION_SEEDS
                    and n == expected_seeds
                    and upper <= MAX_FALSE_ESCALATION_RATE
                ),
                "mean_labels": float(group.labels_queried.mean())
                if "labels_queried" in group
                else float("nan"),
                "mean_spend": float(group.realized_label_spend.mean())
                if "realized_label_spend" in group
                else float("nan"),
                "mean_processed_events": float(group.processed_events.mean())
                if "processed_events" in group
                else float("nan"),
                "max_cap_spend_overrun": float(
                    (group.realized_label_spend - group.hard_budget).max()
                )
                if "realized_label_spend" in group and "hard_budget" in group
                else 0.0,
            }
        )
    result = pd.DataFrame(rows)
    if len(result) != cell_count:
        raise ValueError("calibration is missing one or more registered cells")
    return result


def run_direct_ipw_query_calibration(
    output: Path,
    *,
    seeds: int = MINIMUM_CALIBRATION_SEEDS,
    seed_offset: int = 32_102_026,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    workers: int = 4,
) -> Path:
    """Run fresh null streams, preserving uniform/candidate pairing by stream seed."""
    if seeds < 2:
        raise ValueError("at least two streams per cell are required")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty calibration output: {output}")
    config = HardBudgetConfig(
        n=n,
        d=d,
        seeds=seeds,
        seed_offset=seed_offset,
        alpha=0.05,
        harm_margin=0.10,
        budget_rate=0.20,
        monitor_estimator="direct_ipw",
        q_min=0.05,
        q_max=0.80,
        common_eprocess_bound=True,
        generate_figure=False,
        device=device,
        workers=workers,
        scenario_subset=CALIBRATION_SCENARIOS,
        method_subset=CALIBRATION_METHODS,
    ).validate()
    run_hard_budget(config, output)
    metrics_path = output / "metrics" / "hard_budget_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    expected_rows = seeds * len(CALIBRATION_SCENARIOS) * len(CALIBRATION_METHODS)
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} stream rows, found {len(metrics)}")
    expected_seed_ids = set(range(seed_offset, seed_offset + seeds))
    for (scenario, method), cell in metrics.groupby(["scenario", "method"]):
        if set(cell.seed.astype(int)) != expected_seed_ids:
            raise RuntimeError(f"incomplete or unexpected seed block in {scenario}/{method}")
    summary = summarize_direct_ipw_query_calibration(metrics, expected_seeds=seeds)
    summary_path = output / "metrics" / "direct_ipw_query_calibration.csv"
    summary.to_csv(summary_path, index=False)

    calibrated = seeds >= MINIMUM_CALIBRATION_SEEDS
    family_pass = calibrated and bool(summary.cell_passes.all())
    status = (
        "calibration_passed"
        if family_pass
        else ("calibration_failed" if calibrated else "smoke_or_incomplete")
    )
    lines = [
        "# Direct-IPW history-evidence query null calibration",
        "",
        f"**Status: {status}.** This fresh-seed calibration evaluates the candidate frozen after the separate development grid: `{FROZEN_CANDIDATE}` at `q_min=0.05`, against `uniform_proxy`. It is not confirmation of harm-detection power.",
        "",
        f"The run used {seeds} independent stream seeds per cell, seed IDs `{seed_offset}`–`{seed_offset + seeds - 1}`, n={n}, d={d}, a 20% realized label-dollar cap, `q_max=0.80`, alpha=0.05, and immediate randomized labels. Both methods share the scenario/seed stream and query random numbers. Requested device: `{device}`; resolved device: `{config.device}`. The candidate's query propensities use only prior monitor wealth and past realized spend.",
        "",
        "The four-cell family is the two frozen population-null controls (`stationary`, `benign_nuisance`) crossed with both query procedures. Each one-sided exact Clopper–Pearson upper limit uses Bonferroni cell alpha 0.0125, giving at least 95% simultaneous coverage. A calibration cell passes only when it has all registered seeds and its upper limit is at most 0.05; the family passes only when every cell passes and all run invariants hold.",
        "",
        "|Scenario|Query procedure|Streams|False escalations|Rate|Simultaneous CP upper|Mean labels|Mean spend|Mean events|Cell pass|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['streams']}|{row['false_escalations']}|"
            f"{row['false_escalation_rate']:.4%}|{row['simultaneous_cp95_upper']:.4%}|"
            f"{row['mean_labels']:.1f}|{row['mean_spend']:.2f}|"
            f"{row['mean_processed_events']:.1f}|{row['cell_passes']}|"
        )
    lines.extend(
        [
            "",
            "The formal guarantee is the bounded-mean e-process argument under the history-conditional null, predictable query probabilities, immediate unbiased randomized feedback, and the registered support bound. The finite simulator calibration does not prove those assumptions, extend to delayed or selectively observed labels, establish robustness to unregistered dependence, or establish a query-policy advantage. A disjoint alternative confirmation is a separate step.",
            "",
            f"Reproduce with `uv run shiftlab-dive-direct-ipw-query-calibration --output {output.as_posix()} --seeds {seeds} --seed-offset {seed_offset} --n {n} --d {d} --device {device} --workers {workers}`.",
        ]
    )
    report_path = output / "reports" / "direct_ipw_query_calibration.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_path = output / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["calibration"] = {
        "status": status,
        "candidate_frozen_after_development": FROZEN_CANDIDATE,
        "baseline": BASELINE,
        "scenarios": list(CALIBRATION_SCENARIOS),
        "seeds_per_cell": seeds,
        "seed_offset": seed_offset,
        "familywise_alpha": FAMILYWISE_ALPHA,
        "cells": len(CALIBRATION_SCENARIOS) * len(CALIBRATION_METHODS),
        "minimum_streams_for_calibration": MINIMUM_CALIBRATION_SEEDS,
        "max_false_escalation_rate": MAX_FALSE_ESCALATION_RATE,
        "family_passed": family_pass,
        "does_not_establish": [
            "harm detection power",
            "validity outside registered assumptions",
            "superiority over uniform querying",
            "algorithmic novelty",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/direct_ipw_query_calibration_2000")
    )
    parser.add_argument("--seeds", type=int, default=MINIMUM_CALIBRATION_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=32_102_026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    print(
        run_direct_ipw_query_calibration(
            args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            workers=args.workers,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
