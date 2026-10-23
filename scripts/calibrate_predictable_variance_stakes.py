"""Compare fixed-mixture and predictable variance-adaptive betting under a label cap."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import torch
from scipy.stats import norm
from scipy.stats import t as student_t

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALPHA = 0.05
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
SCENARIOS = (
    "aggregate_zero",
    "aggregate_negative",
    "broad_positive",
    "high_cost_only_positive",
)


def _probabilities(scenario: str, high_cost: float) -> tuple[float, float]:
    if scenario == "aggregate_zero":
        return 0.56, 0.5 - 0.06 / high_cost
    if scenario == "aggregate_negative":
        return 0.44, 0.44
    if scenario == "broad_positive":
        return 0.56, 0.56
    if scenario == "high_cost_only_positive":
        return 0.50, 0.56
    raise ValueError(f"unknown scenario: {scenario}")


def _wilson(successes: int, total: int) -> tuple[float, float]:
    z = float(norm.ppf(0.975))
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def _plot_summary(summary: pd.DataFrame, path: Path) -> None:
    costs = (1.0, 2.0, 5.0)
    colors = {1.0: "#2878B5", 2.0: "#F28E2B", 5.0: "#3A923A"}
    fig, axes = plt.subplots(4, 3, figsize=(13, 13), sharex=True)
    for row, scenario in enumerate(SCENARIOS):
        for col, high_cost in enumerate(costs):
            axis = axes[row, col]
            cell = summary[summary.scenario.eq(scenario) & summary.high_cost.eq(high_cost)]
            for rule, marker, label in (
                ("fixed_mixture", "o", "Fixed mixture"),
                ("fixed_mixture_half_alpha", "x", "Fixed mixture (half alpha)"),
                ("predictable_variance_adaptive", "s", "Adaptive stake"),
                ("predictable_plug_in_eb", "^", "PM-EB"),
                ("predictable_positive_betting", "P", "Positive betting"),
                ("hedged_positive_branch", "D", "Hedged branch (half alpha)"),
            ):
                series = cell[cell.betting_rule.eq(rule)].sort_values("query_rate")
                axis.plot(
                    series.query_rate * 100,
                    series.crossing_rate * 100,
                    marker=marker,
                    color=colors[high_cost],
                    linestyle={
                        "fixed_mixture": "-",
                        "fixed_mixture_half_alpha": "--",
                        "predictable_variance_adaptive": "--",
                        "predictable_plug_in_eb": ":",
                        "predictable_positive_betting": "-.",
                        "hedged_positive_branch": "-.",
                    }[rule],
                    label=label if row == 0 and col == 0 else None,
                )
            if scenario in {"aggregate_zero", "aggregate_negative"}:
                axis.axhline(ALPHA * 100, color="black", linewidth=0.8, alpha=0.65)
                axis.set_ylim(0, 6)
            else:
                axis.set_ylim(0, 25)
            axis.set_title(f"{scenario.replace('_', ' ')} · high cost {high_cost:g}")
            axis.set_xticks([10, 20, 30])
            axis.grid(alpha=0.25)
            if col == 0:
                axis.set_ylabel("E-process crossings (%)")
            if row == len(SCENARIOS) - 1:
                axis.set_xlabel("Label cap (%)")
    handles = [
        plt.Line2D([0], [0], color="black", marker="o", label="Fixed mixture"),
        plt.Line2D(
            [0], [0], color="black", marker="x", linestyle="--", label="Fixed mixture, half alpha"
        ),
        plt.Line2D([0], [0], color="black", marker="s", linestyle="--", label="Adaptive stake"),
        plt.Line2D([0], [0], color="black", marker="^", linestyle=":", label="PM-EB"),
        plt.Line2D(
            [0],
            [0],
            color="black",
            marker="P",
            linestyle="-.",
            label="Positive betting, full alpha",
        ),
        plt.Line2D(
            [0], [0], color="black", marker="D", linestyle="--", label="Hedged branch, half alpha"
        ),
        *[plt.Line2D([0], [0], color=colors[cost], label=f"High cost {cost:g}") for cost in costs],
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.965),
        ncol=6,
        frameon=False,
    )
    fig.suptitle("Fixed betting, plug-in Kelly, PM-EB, and positive-direction bets", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.925))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def _simulate_cell(
    *,
    streams: int,
    horizon: int,
    high_cost: float,
    query_rate: float,
    scenario: str,
    seed: int,
    device: torch.device,
) -> list[dict[str, float | int | bool | str]]:
    p_low, p_high = _probabilities(scenario, high_cost)
    aggregate_gain = 0.5 * (2 * p_low - 1) + 0.5 * high_cost * (2 * p_high - 1)
    if abs(aggregate_gain) < 1e-12:
        aggregate_gain = 0.0
    generator = torch.Generator(device=device).manual_seed(seed)
    stratum = torch.randint(0, 2, (horizon, streams), generator=generator, device=device)
    query_uniform = torch.rand((horizon, streams), generator=generator, device=device)
    outcome_uniform = torch.rand((horizon, streams), generator=generator, device=device)
    cost = torch.where(stratum == 0, 1.0, high_cost).to(torch.float64)
    probability = torch.where(stratum == 0, p_low, p_high)
    outcomes = outcome_uniform < probability

    cap = int(np.floor(query_rate * horizon))
    labels = torch.zeros(streams, dtype=torch.int32, device=device)
    active_events = torch.zeros_like(labels)
    bound = high_cost / query_rate
    fixed_stakes = torch.tensor(STAKES, dtype=torch.float64, device=device)
    fixed_log_wealth = torch.zeros((streams, len(STAKES)), dtype=torch.float64, device=device)
    adaptive_log_wealth = torch.zeros(streams, dtype=torch.float64, device=device)
    normalized_sum = torch.zeros(streams, dtype=torch.float64, device=device)
    normalized_squares = torch.zeros_like(normalized_sum)
    observed_events = torch.zeros_like(labels)
    pm_log_wealth = torch.zeros(streams, dtype=torch.float64, device=device)
    pm_sum_observations = torch.zeros_like(normalized_sum)
    pm_sum_predictive_squared_deviations = torch.zeros_like(normalized_sum)
    pm_predictive_mean = torch.full_like(normalized_sum, 0.5)
    pm_predictive_variance = torch.full_like(normalized_sum, 0.25)
    hedged_log_wealth = torch.zeros(streams, dtype=torch.float64, device=device)
    crossed = {
        "fixed_mixture": torch.zeros(streams, dtype=torch.bool, device=device),
        "fixed_mixture_half_alpha": torch.zeros(streams, dtype=torch.bool, device=device),
        "predictable_variance_adaptive": torch.zeros(streams, dtype=torch.bool, device=device),
        "predictable_plug_in_eb": torch.zeros(streams, dtype=torch.bool, device=device),
        "predictable_positive_betting": torch.zeros(streams, dtype=torch.bool, device=device),
        "hedged_positive_branch": torch.zeros(streams, dtype=torch.bool, device=device),
    }
    fixed_log_weights = torch.full(
        (len(STAKES),), -np.log(len(STAKES)), dtype=torch.float64, device=device
    )
    for event in range(horizon):
        active = labels < cap
        if not bool(active.any()):
            break
        queried = active & (query_uniform[event] < query_rate)
        labels += queried.to(torch.int32)
        active_events += active.to(torch.int32)
        gain = torch.where(outcomes[event], cost[event], -cost[event])
        estimate = torch.where(queried, gain / query_rate, 0.0)
        normalized = estimate / bound

        fixed_log_wealth += torch.log1p(normalized[:, None] * fixed_stakes[None, :])
        fixed_log_e = torch.logsumexp(fixed_log_wealth + fixed_log_weights[None, :], dim=1)
        crossed["fixed_mixture"] |= active & (fixed_log_e >= -np.log(ALPHA))
        crossed["fixed_mixture_half_alpha"] |= active & (fixed_log_e >= -np.log(ALPHA / 2))

        # Plug-in Kelly maximizes the quadratic approximation to expected log
        # wealth. It is predictable because only prior rewards enter its stake.
        denom = 4.0 + observed_events.to(torch.float64)
        mean_hat = (4.0 * 0.05 + normalized_sum) / denom
        second_hat = (4.0 * 0.25 + normalized_squares) / denom
        stake = torch.clamp(torch.clamp(mean_hat, min=0.0) / second_hat, max=0.5)
        factor = 1 + stake * normalized
        adaptive_log_wealth += torch.where(active, torch.log(factor), 0.0)
        crossed["predictable_variance_adaptive"] |= active & (adaptive_log_wealth >= -np.log(ALPHA))

        # Published predictably mixed empirical-Bernstein process on [0, 1].
        pm_time = observed_events.to(torch.float64) + 1
        pm_stake = torch.clamp(
            torch.sqrt(
                2 * np.log(2 / ALPHA) / (pm_predictive_variance * pm_time * torch.log1p(pm_time))
            ),
            max=0.5,
        )
        pm_observation = 0.5 * (normalized + 1)
        pm_residual = pm_observation - pm_predictive_mean
        pm_psi = (-torch.log1p(-pm_stake) - pm_stake) / 4
        pm_increment = pm_stake * (pm_observation - 0.5) - 4 * pm_residual.square() * pm_psi
        pm_log_wealth += torch.where(active, pm_increment, 0.0)
        crossed["predictable_plug_in_eb"] |= active & (pm_log_wealth >= -np.log(ALPHA))
        # Positive-direction branch of the published hedged-capital CS. At
        # candidate mean 1/2, its stake cap is c/m=1 for c=1/2. This one-sided
        # branch remains valid for the composite upper-mean null; the complete
        # two-sided hedge does not.
        hedged_stake = torch.clamp(
            torch.sqrt(
                2 * np.log(2 / ALPHA) / (pm_predictive_variance * pm_time * torch.log1p(pm_time))
            ),
            max=1.0,
        )
        hedged_factor = 1 + hedged_stake * (pm_observation - 0.5)
        hedged_log_wealth += torch.where(active, torch.log(hedged_factor), 0.0)
        crossed["predictable_positive_betting"] |= active & (hedged_log_wealth >= -np.log(ALPHA))
        # The canonical two-sided construction allocates theta=1/2 to this
        # direction, so its directional crossing spends alpha/2.
        crossed["hedged_positive_branch"] |= active & (hedged_log_wealth >= -np.log(ALPHA / 2))
        pm_sum_observations += torch.where(active, pm_observation, 0.0)
        updated_pm_mean = (0.5 + pm_sum_observations) / (pm_time + 1)
        pm_post_update_residual = pm_observation - updated_pm_mean
        pm_sum_predictive_squared_deviations += torch.where(
            active, pm_post_update_residual.square(), 0.0
        )
        updated_pm_variance = (0.25 + pm_sum_predictive_squared_deviations) / (pm_time + 1)
        pm_predictive_mean = torch.where(active, updated_pm_mean, pm_predictive_mean)
        pm_predictive_variance = torch.where(active, updated_pm_variance, pm_predictive_variance)
        normalized_sum += torch.where(active, normalized, 0.0)
        normalized_squares += torch.where(active, normalized.square(), 0.0)
        observed_events += active.to(torch.int32)

    rows: list[dict[str, float | int | bool | str]] = []
    for rule, flags in crossed.items():
        for stream in range(streams):
            rows.append(
                {
                    "scenario": scenario,
                    "betting_rule": rule,
                    "stream": stream,
                    "high_cost": high_cost,
                    "query_rate": query_rate,
                    "horizon": horizon,
                    "label_cap": cap,
                    "labels_queried": int(labels[stream].item()),
                    "events_processed": int(active_events[stream].item()),
                    "p_low_cost": p_low,
                    "p_high_cost": p_high,
                    "aggregate_expected_gain": aggregate_gain,
                    "crossed": bool(flags[stream].item()),
                }
            )
    return rows


def run(
    *,
    output: Path,
    streams: int = 2000,
    horizon: int = 600,
    seed: int = 28102026,
    device_name: str = "cuda",
) -> None:
    if streams < 100 or horizon < 100:
        raise ValueError("streams and horizon must each be at least 100")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    device = torch.device(device_name)
    metric_dir, report_dir = output / "metrics", output / "reports"
    metric_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metric_dir / "predictable_stake_streams.parquet"
    summary_path = metric_dir / "predictable_stake_summary.parquet"
    paired_path = metric_dir / "predictable_stake_paired.parquet"
    if any(path.exists() for path in (detail_path, summary_path, paired_path)):
        raise FileExistsError(f"refusing to overwrite existing output: {output}")

    records = []
    for scenario_idx, scenario in enumerate(SCENARIOS):
        for cost_idx, high_cost in enumerate((1.0, 2.0, 5.0)):
            for query_idx, query_rate in enumerate((0.10, 0.20, 0.30)):
                cell_seed = seed + scenario_idx * 100_000 + cost_idx * 1_000 + query_idx * 10
                records.extend(
                    _simulate_cell(
                        streams=streams,
                        horizon=horizon,
                        high_cost=high_cost,
                        query_rate=query_rate,
                        scenario=scenario,
                        seed=cell_seed,
                        device=device,
                    )
                )
    detail = pd.DataFrame(records)
    detail.to_parquet(detail_path, index=False)

    summary_rows = []
    cell_keys = ["scenario", "high_cost", "query_rate", "betting_rule"]
    for key, group in detail.groupby(cell_keys, sort=False):
        row = dict(zip(cell_keys, key, strict=True))
        low, high = _wilson(int(group.crossed.sum()), len(group))
        row.update(
            streams=len(group),
            crossings=int(group.crossed.sum()),
            crossing_rate=float(group.crossed.mean()),
            wilson_ci_low=low,
            wilson_ci_high=high,
            mean_labels=float(group.labels_queried.mean()),
            label_cap=int(group.label_cap.iloc[0]),
            expected_gain=float(group.aggregate_expected_gain.iloc[0]),
        )
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_parquet(summary_path, index=False)
    figure_path = output / "figures/predictable_stake_calibration.png"
    _plot_summary(summary, figure_path)

    paired_rows = []
    pair_keys = ["scenario", "high_cost", "query_rate"]
    for key, group in detail.groupby(pair_keys, sort=False):
        paired = group.pivot(index="stream", columns="betting_rule", values="crossed")
        fixed = paired["fixed_mixture"].to_numpy(dtype=float)
        fixed_half = paired["fixed_mixture_half_alpha"].to_numpy(dtype=float)
        difference = paired["predictable_variance_adaptive"].to_numpy(dtype=float) - fixed
        pm_difference = paired["predictable_plug_in_eb"].to_numpy(dtype=float) - fixed
        positive_betting_difference = (
            paired["predictable_positive_betting"].to_numpy(dtype=float) - fixed
        )
        hedged_difference = paired["hedged_positive_branch"].to_numpy(dtype=float) - fixed_half
        radius = float(
            student_t.ppf(0.975, len(difference) - 1)
            * difference.std(ddof=1)
            / np.sqrt(len(difference))
        )
        paired_rows.append(
            {
                **dict(zip(pair_keys, key, strict=True)),
                "streams": len(difference),
                "fixed_crossings": int(paired["fixed_mixture"].sum()),
                "fixed_half_alpha_crossings": int(paired["fixed_mixture_half_alpha"].sum()),
                "adaptive_crossings": int(paired["predictable_variance_adaptive"].sum()),
                "adaptive_minus_fixed": float(difference.mean()),
                "paired_ci_low": float(difference.mean() - radius),
                "paired_ci_high": float(difference.mean() + radius),
                "pm_eb_crossings": int(paired["predictable_plug_in_eb"].sum()),
                "pm_eb_minus_fixed": float(pm_difference.mean()),
                "pm_eb_paired_ci_low": float(
                    pm_difference.mean()
                    - student_t.ppf(0.975, len(pm_difference) - 1)
                    * pm_difference.std(ddof=1)
                    / np.sqrt(len(pm_difference))
                ),
                "pm_eb_paired_ci_high": float(
                    pm_difference.mean()
                    + student_t.ppf(0.975, len(pm_difference) - 1)
                    * pm_difference.std(ddof=1)
                    / np.sqrt(len(pm_difference))
                ),
                "positive_betting_crossings": int(paired["predictable_positive_betting"].sum()),
                "positive_betting_minus_fixed": float(positive_betting_difference.mean()),
                "positive_betting_paired_ci_low": float(
                    positive_betting_difference.mean()
                    - student_t.ppf(0.975, len(positive_betting_difference) - 1)
                    * positive_betting_difference.std(ddof=1)
                    / np.sqrt(len(positive_betting_difference))
                ),
                "positive_betting_paired_ci_high": float(
                    positive_betting_difference.mean()
                    + student_t.ppf(0.975, len(positive_betting_difference) - 1)
                    * positive_betting_difference.std(ddof=1)
                    / np.sqrt(len(positive_betting_difference))
                ),
                "hedged_crossings": int(paired["hedged_positive_branch"].sum()),
                "hedged_minus_fixed_half_alpha": float(hedged_difference.mean()),
                "hedged_paired_ci_low": float(
                    hedged_difference.mean()
                    - student_t.ppf(0.975, len(hedged_difference) - 1)
                    * hedged_difference.std(ddof=1)
                    / np.sqrt(len(hedged_difference))
                ),
                "hedged_paired_ci_high": float(
                    hedged_difference.mean()
                    + student_t.ppf(0.975, len(hedged_difference) - 1)
                    * hedged_difference.std(ddof=1)
                    / np.sqrt(len(hedged_difference))
                ),
            }
        )
    pd.DataFrame(paired_rows).to_parquet(paired_path, index=False)

    lines = [
        "# Matched comparison of predictable betting rules",
        "",
        f"This CUDA/CPU calibration compares fixed five-stake bounded e-processes at alpha and alpha/2, a predictable plug-in Kelly stake, the published predictable plug-in empirical-Bernstein (PM-EB) process, a one-sided positive betting process using the full alpha level, and the canonical positive branch of the theta=1/2 hedged-capital process using half the alpha level, over {streams} paired streams per cell, a {horizon}-event horizon, and pathwise caps of 10%, 20%, and 30%.",
        "",
        "The adaptive rule normalizes every observed inverse-propensity gain by the same global support bound, then chooses the next stake as `clip(max(0, smoothed_mean) / smoothed_second_moment, 0, 0.5)`. Its smoothed prior has strength 4, normalized mean 0.05, and second moment 0.25. This is a plug-in approximation to the Kelly fraction from a quadratic expansion of expected log wealth. The stake depends only on prior observations. Under the history-conditional null `E[X_t | F_(t-1)] <= 0`, each factor `1 + lambda_t X_t / B` is nonnegative and has conditional expectation at most one for any predictable `lambda_t` in `[0,1]`; Ville's inequality therefore controls crossings. Variance adaptation is a power strategy within a standard valid betting construction, not a new validity theorem.",
        "",
        "PM-EB maps normalized gains `R_t=X_t/B` to `Z_t=(R_t+1)/2` and tests `E[Z_t | F_(t-1)] <= 1/2`. Its log increment is `lambda_t(Z_t-1/2) - 4(Z_t-mu_hat_(t-1))^2 psi_E(lambda_t)`, where `psi_E(lambda)=(-log(1-lambda)-lambda)/4`. The predictable stake is `min(1/2, sqrt(2 log(2/alpha)/(sigma_hat^2_(t-1) t log(1+t))))`; smoothed mean and variance estimates update after each observation. This published construction is included as an established baseline, not a novelty claim.",
        "",
        "Both positive-direction rules use the same log increment `log(1 + lambda_t (Z_t-1/2))` and the paper's predictable plug-in variance stake, capped at `c/m=1` for `c=1/2`. `predictable_positive_betting` tests the one-sided null at alpha=0.05. `hedged_positive_branch` applies the canonical theta=1/2 capital weight and therefore uses the alpha/2 directional threshold from the paper's two-sided confidence sequence. `fixed_mixture_half_alpha` is the matched reference at that same stricter threshold. The complete two-sided hedge is not used as a decision-harm gate: its negative-direction branch can cross when the true gain is negative, which is inside the no-harm null. The positive branch alone remains valid for the one-sided upper-mean null.",
        "",
        "`aggregate_zero` has equally likely strata with expected gains +0.12 and -0.12, respectively. `aggregate_negative` has outcome probability 0.44 in both strata and is a strict negative-mean control inside the composite no-harm null. `broad_positive` has outcome probability 0.56 in both strata. `high_cost_only_positive` has neutral low-cost and +0.12 high-cost conditional gain. Query randomization is independent with the stated propensity until the pathwise cap is reached. All six rules receive identical query draws and outcomes. The low/high cost and propensity grid varies estimator variance while preserving the global bound for each cell.",
        "",
        "| Scenario | High cost | Query cap | Betting rule | Crossings / streams (95% Wilson CI) | Mean labels / cap |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.high_cost:.0f} | {row.query_rate:.0%} | {row.betting_rule} | {row.crossings}/{row.streams} ({row.wilson_ci_low:.3f}, {row.wilson_ci_high:.3f}) | {row.mean_labels:.1f}/{row.label_cap} |"
        )
    lines.extend(
        [
            "",
            "Paired Kelly-minus-fixed, PM-EB-minus-fixed, full-alpha positive-betting-minus-fixed, and half-alpha hedged-positive-minus-half-alpha-fixed crossing-rate differences are stored with paired 95% t intervals, unadjusted across cells. The exact aggregate-zero and strict aggregate-negative cells diagnose one-sided type-I behavior. Positive alternatives compare power at the same label cap; the half-alpha hedge is also compared with the fixed mixture at half alpha. This finite experiment does not establish uniform dominance and is not preregistered; the hedged comparator was added after inspection of the earlier grid.",
            "",
            f"Figure: `figures/{figure_path.name}`. Paired contrasts and the run manifest are in the adjacent metrics and report folders.",
            "",
            f"Reproduce with `uv run python scripts/calibrate_predictable_variance_stakes.py --streams {streams} --horizon {horizon} --seed {seed} --device {device_name} --output outputs/{output.name}_reproduction`.",
        ]
    )
    report_path = report_dir / "predictable_stake_calibration.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    artifacts = (detail_path, summary_path, paired_path, figure_path, report_path)
    manifest = {
        "experiment": "predictable_betting_rules_under_hard_query_caps",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": {
            "streams_per_cell": streams,
            "horizon": horizon,
            "seed": seed,
            "device": str(device),
            "alpha": ALPHA,
            "scenarios": list(SCENARIOS),
            "high_costs": [1.0, 2.0, 5.0],
            "query_rates": [0.1, 0.2, 0.3],
            "fixed_stakes": list(STAKES),
            "adaptive_prior_strength": 4.0,
            "adaptive_prior_mean": 0.05,
            "adaptive_prior_second_moment": 0.25,
            "adaptive_max_stake": 0.5,
            "pm_eb_max_stake": 0.5,
            "pm_eb_alpha_for_stake_schedule": ALPHA,
            "hedged_positive_max_stake": 1.0,
            "hedged_truncation_c": 0.5,
            "hedged_direction_weight": 0.5,
            "hedged_directional_alpha": ALPHA / 2,
            "replication_status": "separate-seed exploratory comparison; not preregistered",
        },
        "environment": {
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "cuda_runtime": torch.version.cuda,
        },
        "information_protocol": [
            "all methods receive identical query randomization and outcomes",
            "querying stops before the next event when the hard label cap is exhausted",
            "the global support bound is fixed before monitoring and common across methods",
            "the evaluator-only scenario probabilities are not supplied to any betting rule",
            "one candidate is tested per stream at alpha=0.05",
        ],
        "reproduction_script": "scripts/calibrate_predictable_variance_stakes.py",
        "reproduction_script_sha256": hashlib.sha256(
            Path("scripts/calibrate_predictable_variance_stakes.py").read_bytes()
        ).hexdigest(),
        "artifacts": [path.relative_to(output).as_posix() for path in artifacts],
        "sha256": {
            "artifacts": {
                path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in artifacts
            }
        },
    }
    (report_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=600)
    parser.add_argument("--seed", type=int, default=28102026)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/predictable_betting_comparison")
    )
    args = parser.parse_args()
    run(
        output=args.output,
        streams=args.streams,
        horizon=args.horizon,
        seed=args.seed,
        device_name=args.device,
    )


if __name__ == "__main__":
    main()
