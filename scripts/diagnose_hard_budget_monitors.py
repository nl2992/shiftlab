"""Compare predictable globally bounded monitor baselines on fresh hard-budget streams."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.data.gpu.environment import environment
from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.hard_budget import (
    HARD_BUDGET_METHODS,
    HARD_BUDGET_MONITOR_COMPARATORS,
    HardBudgetConfig,
    run_hard_budget,
)

DEFAULT_SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "recurring_regimes",
)
DEFAULT_METHODS = (
    "uniform_proxy",
    "cost_stabilized_proxy",
    "exact_mixture_growth_proxy",
)
MONITORS = (
    ("fixed_mixture", "single_e"),
    ("predictable_variance", "variance_adaptive"),
    ("predictable_empirical_bernstein", "pm_eb"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    rate = successes / n
    denominator = 1 + z**2 / n
    center = (rate + z**2 / (2 * n)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
    return float(center - radius), float(center + radius)


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        harmful = group.material_harm.astype(bool)
        null = group.population_null_control.astype(bool)
        for monitor, prefix in MONITORS:
            detected = group[f"{prefix}_detected"].astype(bool)
            false = group[f"{prefix}_false_escalation"].astype(bool)
            detected_harm = int((detected & harmful).sum())
            reached_harm = int((harmful & group.harm_reached_before_budget_stop.astype(bool)).sum())
            false_count = int((false & null).sum())
            harm_count = int(harmful.sum())
            null_count = int(null.sum())
            delays = pd.to_numeric(
                group.loc[detected & harmful, f"{prefix}_delay"], errors="coerce"
            )

            wins = losses = 0
            paired_p = float("nan")
            if monitor != "fixed_mixture" and harm_count:
                fixed = group.loc[harmful, "single_e_detected"].astype(bool)
                candidate = detected.loc[harmful]
                wins = int((candidate & ~fixed).sum())
                losses = int((~candidate & fixed).sum())
                if wins + losses:
                    paired_p = float(binomtest(wins, wins + losses, p=0.5).pvalue)
                else:
                    paired_p = 1.0

            det_low, det_high = _wilson(detected_harm, harm_count)
            false_low, false_high = _wilson(false_count, null_count)
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "monitor": monitor,
                    "streams": len(group),
                    "harmful_streams": harm_count,
                    "harm_reached": reached_harm,
                    "detections": detected_harm,
                    "detection_rate": detected_harm / harm_count if harm_count else np.nan,
                    "detection_wilson_low": det_low,
                    "detection_wilson_high": det_high,
                    "false_escalations": false_count,
                    "null_streams": null_count,
                    "false_escalation_rate": false_count / null_count if null_count else np.nan,
                    "false_wilson_low": false_low,
                    "false_wilson_high": false_high,
                    "median_delay_given_detection": float(delays.median())
                    if len(delays)
                    else np.nan,
                    "mean_spend": float(group.realized_label_spend.mean()),
                    "mean_labels": float(group.labels_queried.mean()),
                    "mean_processed_fraction": float(group.monitor_fraction_processed.mean()),
                    "discordant_wins_vs_fixed": wins,
                    "discordant_losses_vs_fixed": losses,
                    "mcnemar_p_vs_fixed": paired_p,
                }
            )
    return pd.DataFrame(rows)


def write_figure(summary: pd.DataFrame, output: Path) -> Path:
    scenarios = [scenario for scenario in DEFAULT_SCENARIOS if scenario in set(summary.scenario)]
    methods = [method for method in DEFAULT_METHODS if method in set(summary.method)]
    fig, axes = plt.subplots(len(scenarios), 1, figsize=(11, 3.1 * len(scenarios)), squeeze=False)
    colors = {
        "fixed_mixture": "#2878b5",
        "predictable_variance": "#e87500",
        "predictable_empirical_bernstein": "#3a923a",
    }
    for i, scenario in enumerate(scenarios):
        rows = summary.loc[summary.scenario.eq(scenario)]
        is_null = bool(rows.null_streams.max() > 0)
        outcome = "false_escalation_rate" if is_null else "detection_rate"
        lo = "false_wilson_low" if is_null else "detection_wilson_low"
        hi = "false_wilson_high" if is_null else "detection_wilson_high"
        ax = axes[i, 0]
        positions = np.arange(len(methods))
        width = 0.23
        for j, monitor in enumerate(name for name, _ in MONITORS):
            values = []
            lower = []
            upper = []
            for method in methods:
                row = rows.loc[rows.method.eq(method) & rows.monitor.eq(monitor)]
                if row.empty:
                    values.append(np.nan)
                    lower.append(0.0)
                    upper.append(0.0)
                else:
                    value = float(row.iloc[0][outcome])
                    values.append(value)
                    lower.append(value - float(row.iloc[0][lo]))
                    upper.append(float(row.iloc[0][hi]) - value)
            ax.bar(
                positions + (j - 1) * width,
                values,
                width,
                yerr=np.vstack((lower, upper)),
                capsize=3,
                label=monitor,
                color=colors[monitor],
            )
        ax.set_xticks(positions, methods, rotation=20, ha="right")
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("False escalation" if is_null else "Harm detection")
        ax.set_title(f"{scenario}: {outcome.replace('_', ' ')} (Wilson 95% intervals)")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(ncol=3, fontsize=8)
    fig.suptitle("Fresh-seed monitor comparison under a common hard label-dollar budget")
    fig.tight_layout()
    path = output / "figures" / "monitor_power_comparison.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def run_diagnostic(
    output: Path,
    *,
    seeds: int = 30,
    seed_offset: int = 39102026,
    n: int = 3200,
    d: int = 16,
    budget_rate: float = 0.20,
    q_min: float = 0.05,
    scenarios: tuple[str, ...] = DEFAULT_SCENARIOS,
    methods: tuple[str, ...] = DEFAULT_METHODS,
    device: str = "cuda",
) -> Path:
    if (output / "reports" / "monitor_power_diagnostic.md").exists():
        raise FileExistsError(f"refusing to overwrite completed monitor diagnostic: {output}")
    if set(methods) - set(HARD_BUDGET_METHODS) or not methods:
        raise ValueError("methods must be registered hard-budget query policies")
    config = HardBudgetConfig(
        n=n,
        d=d,
        seeds=seeds,
        seed_offset=seed_offset,
        budget_rate=budget_rate,
        q_min=q_min,
        q_max=0.80,
        common_eprocess_bound=True,
        robust_growth_probability_radius=0.20,
        monitor_comparators=HARD_BUDGET_MONITOR_COMPARATORS,
        device=device,
        scenario_subset=scenarios,
        method_subset=methods,
    )
    config.validate()
    scenario_cost_max = max(
        max(scenario.fn_cost, scenario.fp_cost)
        for scenario in SCENARIOS
        if scenario.name in scenarios
    )
    increment_bound = (scenario_cost_max + config.harm_margin) * (2 / config.q_min - 1)
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("metrics", "reports", "figures"):
        (output / folder).mkdir(exist_ok=True)
    run_hard_budget(config, output)
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    if not metrics.budget_respected.astype(bool).all():
        raise RuntimeError("monitor comparison exceeded the common hard dollar cap")
    summary = summarize(metrics)
    summary.to_csv(output / "metrics" / "monitor_comparison.csv", index=False)
    write_figure(summary, output)
    lines = [
        "# Fresh-seed hard-budget monitor diagnostic",
        "",
        "This is a development diagnostic following the completed budget frontier. It compares a fixed bounded-mean stake mixture with two existing predictable global-bound betting baselines: a smoothed variance-adaptive stake and predictable plug-in empirical Bernstein (PM-EB). Both comparator processes use the same prediction-powered estimate, global bound, query policy, labels, stopping rule, and alpha as the fixed mixture. Their stakes use only past evidence. These are established comparator algorithms, not novel contributions.",
        "",
        f"The run used {seeds} independent streams per scenario (seeds {seed_offset}–{seed_offset + seeds - 1}), n={n}, d={d}, a {budget_rate:.0%} hard dollar cap, q_min={config.q_min:.2f}, q_max={config.q_max:.2f}, alpha={config.alpha:.2f}, and the common global bound. For the selected registered scenarios, M=max(FN cost, FP cost)+margin={scenario_cost_max + config.harm_margin:.2f}, so the prediction-powered increment bound is M(2/q_min-1)={increment_bound:.2f}. Requested device: `{device}`; resolved device: `{environment().get('gpu_name') if device == 'cuda' else device}`.",
        "",
        "The primary outcomes are false escalation on stationary and benign-nuisance controls, harm detection and delay on boundary-local and recurring alternatives, onset reachability, and label spend/horizon. Report Wilson intervals and paired exact McNemar comparisons against the fixed mixture. This development grid is not a confirmation, and its small null cells cannot establish 5% calibration.",
        "",
        "|Scenario|Query policy|Monitor|Detections / harmful|Reached / harmful|False escalations / null|Median delay given detection|Mean spend|Mean labels|Mean horizon|Paired discordants vs fixed (wins/losses)|McNemar p|",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        detections = (
            "n/a" if not row["harmful_streams"] else f"{row['detections']}/{row['harmful_streams']}"
        )
        false = (
            "n/a"
            if not row["null_streams"]
            else f"{row['false_escalations']}/{row['null_streams']}"
        )
        delay = (
            "n/a"
            if pd.isna(row["median_delay_given_detection"])
            else f"{row['median_delay_given_detection']:.1f}"
        )
        pvalue = "n/a" if pd.isna(row["mcnemar_p_vs_fixed"]) else f"{row['mcnemar_p_vs_fixed']:.3f}"
        reached = (
            "n/a"
            if not row["harmful_streams"]
            else f"{row['harm_reached']}/{row['harmful_streams']}"
        )
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['monitor']}|{detections}|{reached}|{false}|{delay}|"
            f"{row['mean_spend']:.2f}|{row['mean_labels']:.1f}|{row['mean_processed_fraction']:.3f}|"
            f"{row['discordant_wins_vs_fixed']}/{row['discordant_losses_vs_fixed']}|{pvalue}|"
        )
    lines.extend(
        [
            "",
            "Detection and false-escalation confidence intervals are in `metrics/monitor_comparison.csv`. The event-level method metrics are in `metrics/hard_budget_comparison.parquet`.",
            "",
            "Interpret the comparison under the history-conditional mean null and the globally bounded prediction-powered increments. Do not use current-covariate-specific normalization to claim aggregate-null validity. Any monitor that looks promising requires a separate 2,000-stream null calibration and an independently seeded confirmation with a nonzero expected detection rate.",
            "",
            "![Monitor power comparison](../figures/monitor_power_comparison.png)",
            "",
            f"Reproduce with `uv run python scripts/diagnose_hard_budget_monitors.py --output {output.as_posix()} --seeds {seeds} --seed-offset {seed_offset} --n {n} --d {d} --budget-rate {budget_rate} --q-min {q_min} --device {device}`.",
        ]
    )
    report_path = output / "reports" / "monitor_power_diagnostic.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    finalize_manifest(output)
    manifest_path = output / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["diagnostic_script_sha256"] = _sha256(Path(__file__))
    manifest["monitor_comparators"] = list(HARD_BUDGET_MONITOR_COMPARATORS)
    manifest["source_git_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    manifest["source_worktree_clean"] = not subprocess.check_output(
        ["git", "status", "--porcelain"], text=True
    ).strip()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/monitor_power_diagnostic_30"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=39102026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--budget-rate", type=float, default=0.20)
    parser.add_argument("--q-min", type=float, default=0.05)
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    args = parser.parse_args(argv)
    print(
        run_diagnostic(
            args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            budget_rate=args.budget_rate,
            q_min=args.q_min,
            scenarios=tuple(args.scenarios),
            methods=tuple(args.methods),
            device=args.device,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
