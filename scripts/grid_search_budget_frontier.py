"""Run a paired hard-budget frontier for decision-harm query policies."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.hard_budget import (
    HARD_BUDGET_METHODS,
    HardBudgetConfig,
    run_hard_budget,
)

DEFAULT_BUDGETS = (0.10, 0.20, 0.30)
DEFAULT_SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "recurring_regimes",
)
METHODS = HARD_BUDGET_METHODS


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    rate = successes / n
    denom = 1 + z**2 / n
    center = (rate + z**2 / (2 * n)) / denom
    half = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denom
    return float(center - half), float(center + half)


def _paired_rmse_interval(
    errors: np.ndarray, comparator_errors: np.ndarray, *, seed: int, replicates: int = 20_000
) -> tuple[float, float, float]:
    if errors.shape != comparator_errors.shape or errors.ndim != 1 or not len(errors):
        raise ValueError("paired stream errors must have matching nonempty vectors")
    observed = float(np.sqrt(np.mean(errors**2)) - np.sqrt(np.mean(comparator_errors**2)))
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=float)
    for start in range(0, replicates, 500):
        size = min(500, replicates - start)
        indices = rng.integers(0, len(errors), size=(size, len(errors)))
        draws[start : start + size] = np.sqrt(np.mean(errors[indices] ** 2, axis=1)) - np.sqrt(
            np.mean(comparator_errors[indices] ** 2, axis=1)
        )
    low, high = np.quantile(draws, [0.025, 0.975])
    return observed, float(low), float(high)


def _summarize(metrics: pd.DataFrame, *, seed_offset: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (budget, scenario), group in metrics.groupby(["budget_rate", "scenario"], sort=True):
        wide = group.pivot(index="seed", columns="method")
        if "uniform_proxy" not in wide.columns.get_level_values(1):
            raise ValueError("uniform_proxy is required as the paired reference")
        for method in METHODS:
            if method not in wide.columns.get_level_values(1):
                continue
            current = wide.xs(method, axis=1, level=1).sort_index()
            uniform = wide.xs("uniform_proxy", axis=1, level=1).sort_index()
            if not current.index.equals(uniform.index):
                raise ValueError(
                    f"seed mismatch for {method} at budget={budget}, scenario={scenario}"
                )
            harmful = current.material_harm.astype(bool)
            reached = harmful & current.harm_reached_before_budget_stop.astype(bool)
            detections = current.single_e_detected.astype(bool)
            false = current.single_e_false_escalation.astype(bool)
            discordant_wins = int((detections & ~uniform.single_e_detected.astype(bool)).sum())
            discordant_losses = int((~detections & uniform.single_e_detected.astype(bool)).sum())
            if discordant_wins + discordant_losses:
                mcnemar = float(
                    binomtest(
                        discordant_wins,
                        discordant_wins + discordant_losses,
                        p=0.5,
                    ).pvalue
                )
            else:
                mcnemar = 1.0
            err = current.stream_mean_estimation_error.to_numpy(dtype=float)
            uniform_err = uniform.stream_mean_estimation_error.to_numpy(dtype=float)
            rmse = float(np.sqrt(np.mean(err**2)))
            uniform_rmse = float(np.sqrt(np.mean(uniform_err**2)))
            difference, ci_low, ci_high = _paired_rmse_interval(
                err,
                uniform_err,
                seed=seed_offset + round(float(budget) * 10_000) + len(scenario),
            )
            n = len(current)
            harmful_n = int(harmful.sum())
            reached_n = int(reached.sum())
            detected_harm = int((detections & harmful).sum())
            detected_reached = int((detections & reached).sum())
            false_count = int(false.sum())
            false_low, false_high = _wilson(false_count, n)
            power_low, power_high = _wilson(detected_harm, harmful_n)
            reached_low, reached_high = _wilson(detected_reached, reached_n)
            rows.append(
                {
                    "budget_rate": float(budget),
                    "scenario": scenario,
                    "method": method,
                    "streams": n,
                    "mean_cap": float(current.hard_budget.mean()),
                    "mean_spend": float(current.realized_label_spend.mean()),
                    "mean_labels": float(current.labels_queried.mean()),
                    "mean_processed_fraction": float(current.monitor_fraction_processed.mean()),
                    "cap_violations": int((~current.budget_respected.astype(bool)).sum()),
                    "harmful_streams": harmful_n,
                    "harm_reached": reached_n,
                    "detections_all_harm": detected_harm,
                    "detection_rate_all_harm": detected_harm / harmful_n if harmful_n else np.nan,
                    "detection_wilson_low": power_low,
                    "detection_wilson_high": power_high,
                    "detection_rate_reached_harm": detected_reached / reached_n
                    if reached_n
                    else np.nan,
                    "reached_detection_wilson_low": reached_low,
                    "reached_detection_wilson_high": reached_high,
                    "false_escalations": false_count,
                    "false_escalation_rate": false_count / n,
                    "false_wilson_low": false_low,
                    "false_wilson_high": false_high,
                    "stream_mean_rmse": rmse,
                    "uniform_stream_mean_rmse": uniform_rmse,
                    "rmse_difference_vs_uniform": difference,
                    "rmse_difference_ci_low": ci_low,
                    "rmse_difference_ci_high": ci_high,
                    "detection_wins_vs_uniform": discordant_wins,
                    "detection_losses_vs_uniform": discordant_losses,
                    "mcnemar_p_vs_uniform": mcnemar if harmful_n else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _write_figure(summary: pd.DataFrame, output: Path, methods: tuple[str, ...]) -> Path:
    scenarios = [scenario for scenario in DEFAULT_SCENARIOS if scenario in set(summary.scenario)]
    fig, axes = plt.subplots(len(scenarios), 2, figsize=(12, 4.1 * len(scenarios)), squeeze=False)
    colors = plt.get_cmap("tab10").colors
    for row_index, scenario in enumerate(scenarios):
        rows = summary.loc[summary.scenario.eq(scenario)]
        for index, method in enumerate(methods):
            series = rows.loc[rows.method.eq(method)].sort_values("budget_rate")
            if series.empty:
                continue
            color = colors[index % len(colors)]
            if scenario in {"stationary", "benign_nuisance"}:
                rate = series.false_escalation_rate
                low = series.false_wilson_low
                high = series.false_wilson_high
                panel_title = f"{scenario}: false escalation"
                panel_ylabel = "False escalations / 60 (Wilson 95% CI)"
            else:
                rate = series.detection_rate_all_harm
                low = series.detection_wilson_low
                high = series.detection_wilson_high
                panel_title = f"{scenario}: harm detection"
                panel_ylabel = "Detections / harmful streams (Wilson 95% CI)"
            axes[row_index, 0].errorbar(
                series.budget_rate,
                rate,
                yerr=np.vstack((rate - low, high - rate)),
                marker="o",
                capsize=3,
                label=method,
                color=color,
            )
            axes[row_index, 1].plot(
                series.budget_rate,
                series.stream_mean_rmse,
                marker="o",
                label=method,
                color=color,
            )
        axes[row_index, 0].set_title(panel_title)
        axes[row_index, 0].set_xlabel("Target label-dollar budget rate")
        axes[row_index, 0].set_ylabel(panel_ylabel)
        axes[row_index, 0].set_ylim(0, 1.02)
        axes[row_index, 1].set_title(f"{scenario}: stream-mean RMSE")
        axes[row_index, 1].set_xlabel("Target label-dollar budget rate")
        axes[row_index, 1].set_ylabel("RMSE (lower is better)")
        for axis in axes[row_index]:
            axis.grid(alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.01))
    fig.suptitle("Decision-harm acquisition frontier under a common hard dollar cap", y=1.025)
    fig.tight_layout()
    path = output / "figures" / "budget_frontier.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def run_grid(
    output: Path,
    *,
    seeds: int = 60,
    seed_offset: int = 28802026,
    n: int = 3200,
    d: int = 16,
    budgets: tuple[float, ...] = DEFAULT_BUDGETS,
    scenarios: tuple[str, ...] = DEFAULT_SCENARIOS,
    methods: tuple[str, ...] = METHODS,
    device: str = "cuda",
) -> Path:
    if (output / "reports" / "budget_frontier.md").exists():
        raise FileExistsError(f"refusing to overwrite a completed budget-grid output: {output}")
    if not budgets or len(set(budgets)) != len(budgets):
        raise ValueError("budgets must be a nonempty collection of unique rates")
    if not scenarios or len(set(scenarios)) != len(scenarios):
        raise ValueError("scenarios must be a nonempty collection of unique names")
    if set(methods) - set(METHODS) or "uniform_proxy" not in methods:
        raise ValueError("methods must be registered defaults and include uniform_proxy")
    for budget in budgets:
        HardBudgetConfig(
            n=n,
            d=d,
            seeds=seeds,
            seed_offset=seed_offset,
            budget_rate=budget,
            q_min=0.05,
            q_max=0.80,
            common_eprocess_bound=True,
            device=device,
            scenario_subset=scenarios,
            method_subset=methods,
        ).validate()

    output.mkdir(parents=True, exist_ok=True)
    for folder in ("metrics", "reports", "figures"):
        (output / folder).mkdir(exist_ok=True)
    frames = []
    run_manifests: dict[str, str] = {}
    for budget in budgets:
        rate_tag = f"{budget:.2f}".replace(".", "p")
        run_dir = output / f"budget_{rate_tag}"
        manifest_path = run_dir / "reports" / "manifest.json"
        metrics_path = run_dir / "metrics" / "hard_budget_comparison.parquet"
        if metrics_path.exists() and manifest_path.exists():
            metrics = pd.read_parquet(metrics_path)
        else:
            config = HardBudgetConfig(
                n=n,
                d=d,
                seeds=seeds,
                seed_offset=seed_offset,
                budget_rate=budget,
                q_min=0.05,
                q_max=0.80,
                robust_growth_probability_radius=0.20,
                common_eprocess_bound=True,
                device=device,
                scenario_subset=scenarios,
                method_subset=methods,
            )
            run_hard_budget(config, run_dir)
            metrics = pd.read_parquet(metrics_path)
        metrics["budget_rate"] = budget
        frames.append(metrics)
        run_manifests[str(run_dir / "reports" / "manifest.json")] = _digest(manifest_path)

    metrics_all = pd.concat(frames, ignore_index=True)
    if metrics_all.duplicated(["budget_rate", "scenario", "seed", "method"]).any():
        raise RuntimeError("budget frontier contains duplicate budget/scenario/seed/method rows")
    if not metrics_all.budget_respected.astype(bool).all():
        raise RuntimeError("budget frontier contains a hard-cap violation")
    metrics_all.to_parquet(output / "metrics" / "budget_frontier.parquet", index=False)
    summary = _summarize(metrics_all, seed_offset=seed_offset)
    summary.to_csv(output / "metrics" / "budget_frontier_summary.csv", index=False)
    _write_figure(summary, output, methods)

    lines = [
        "# Paired hard-budget acquisition frontier",
        "",
        f"This screening grid compares {len(methods)} query policies at target label-dollar rates {', '.join(f'{v:.0%}' for v in budgets)}. It uses {seeds} paired seeds per scenario, seed offset {seed_offset}, n={n}, d={d}, and resolved device `{environment().get('gpu_name') if device == 'cuda' else device}`.",
        "",
        "Within each budget level, all methods share generated streams, query uniforms, a common q_min=0.05 e-process bound, and the same pathwise dollar cap. The same stream seed is reused across budget levels to enable paired budget contrasts. The target budget changes the cap and validation-calibrated allocation; it does not change alpha or the margin. The selection grid is descriptive and does not establish a nominal false-alarm guarantee.",
        "",
        "Detection rates use Wilson 95% intervals. Paired RMSE differences versus uniform use seed bootstrap 95% intervals. The exact McNemar p-value is shown for detection versus uniform; the p-values are unadjusted across methods and budget levels. Report harm reachability separately because budget exhaustion can censor late onsets.",
        "",
        "|Budget|Scenario|Method|Detected / harmful|Reached / harmful|Detection rate [Wilson 95%]|False alarms / streams|RMSE|RMSE delta vs uniform [bootstrap 95%]|Mean spend|Mean labels|Processed fraction|Cap violations|McNemar p vs uniform|",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        rate = row["detection_rate_all_harm"]
        detection = (
            "n/a"
            if pd.isna(rate)
            else f"{row['detections_all_harm']}/{row['harmful_streams']} [{row['detection_wilson_low']:.3f}, {row['detection_wilson_high']:.3f}]"
        )
        rmse_delta = (
            "reference"
            if row["method"] == "uniform_proxy"
            else f"{row['rmse_difference_vs_uniform']:+.4f} [{row['rmse_difference_ci_low']:+.4f}, {row['rmse_difference_ci_high']:+.4f}]"
        )
        lines.append(
            f"|{row['budget_rate']:.0%}|{row['scenario']}|{row['method']}|"
            f"{row['detections_all_harm']}/{row['harmful_streams']}|"
            f"{row['harm_reached']}/{row['harmful_streams']}|{detection}|"
            f"{row['false_escalations']}/{row['streams']}|{row['stream_mean_rmse']:.4f}|"
            f"{rmse_delta}|{row['mean_spend']:.2f}|{row['mean_labels']:.1f}|"
            f"{row['mean_processed_fraction']:.3f}|{row['cap_violations']}|"
            f"{row['mcnemar_p_vs_uniform']:.3f}|"
        )
    lines.extend(
        [
            "",
            "![Acquisition power and error across hard-budget rates](../figures/budget_frontier.png)",
            "",
            "The grid is a screening study. Advance a query method only if its advantage persists in a separately seeded confirmation, improves decision-harm detection or cumulative decision loss at matched realized spend, and retains acceptable calibration on nondegenerate null streams. A 60-seed zero-alarm cell is a diagnostic, not proof of 5% error control.",
        ]
    )
    report_path = output / "reports" / "budget_frontier.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "experiment": "paired_hard_budget_acquisition_frontier",
        "configuration": {
            "seeds": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "d": d,
            "budget_rates": list(budgets),
            "scenarios": list(scenarios),
            "methods": list(methods),
            "q_min": 0.05,
            "q_max": 0.80,
            "harm_margin": 0.10,
            "alpha": 0.05,
            "common_eprocess_bound": True,
            "device": device,
            "robust_growth_probability_radius": 0.20,
        },
        "environment": environment(),
        "paired_budget_runs": run_manifests,
        "assumptions": [
            "Synthetic outcomes and query-time tariffs.",
            "Immediate paired labels; delayed feedback not studied in this grid.",
            "All query propensities are predictable and bounded below by q_min.",
            "Hard-dollar stopping uses past realized spend and the maximum tariff support.",
            "The e-process still requires its bounded conditional-mean null.",
            "Wilson intervals and paired bootstrap intervals are descriptive; method-grid contrasts are not multiplicity-adjusted.",
        ],
    }
    (output / "reports" / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    finalize_manifest(output)
    final_manifest = json.loads((output / "reports" / "manifest.json").read_text())
    final_manifest["paired_budget_run_manifests_sha256"] = run_manifests
    final_manifest["analysis_script_sha256"] = _digest(Path(__file__))
    (output / "reports" / "manifest.json").write_text(
        json.dumps(final_manifest, indent=2), encoding="utf-8"
    )
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/budget_frontier_60"))
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=28802026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--budgets", type=float, nargs="+", default=DEFAULT_BUDGETS)
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--methods", nargs="+", default=METHODS)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    args = parser.parse_args()
    print(
        run_grid(
            args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            budgets=tuple(args.budgets),
            scenarios=tuple(args.scenarios),
            methods=tuple(args.methods),
            device=args.device,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
