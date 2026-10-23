"""Calibrate repeated-candidate e-process gates on nondegenerate mean-null streams.

The synthetic candidate policies differ from an incumbent on balanced contexts.
Their paired costs vary from event to event, while the history-conditional
aggregate gain is exactly zero in the null scenario. Covariates are not used by
the gate, query propensities are fixed, and all candidates share each queried
label. This isolates familywise betting behavior from model fitting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import torch
from scipy.stats import norm, t

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.experiment import finalize_manifest

ALPHA = 0.05
FN_COST = 5.0
FP_COST = 1.0
RULES = (
    "fixed_mixture",
    "fixed_mixture_half_alpha",
    "predictable_kelly",
    "pm_eb",
    "positive_betting",
    "hedged_positive",
)
STAKES = torch.tensor((0.05, 0.1, 0.2, 0.4, 0.8), dtype=torch.float64)
QUERY_RATES = (0.10, 0.20, 0.40)
BOUND_MULTIPLIERS = (1.0, 1.5, 2.0)
CANDIDATE_COUNTS = (1, 5, 13)
SCENARIOS = {
    # Each candidate has 50% no action change, 25% +0.4 mean gain, and
    # 25% -0.4 mean gain. Thus its average gain is exactly zero, with
    # nonzero eventwise variance.
    "aggregate_zero": (0.10, 0.10, 0.0),
    # Positive and negative candidates change only the outcome rate by stratum;
    # the resulting average candidate gain is exactly +/-0.12 cost units/event.
    "aggregate_positive": (0.06, 0.14, 0.12),
    "aggregate_negative": (0.14, 0.06, -0.12),
}


@dataclass(frozen=True)
class CalibrationConfig:
    streams: int = 2000
    horizon: int = 1000
    seed: int = 26102026
    alpha: float = ALPHA
    device: str = "cuda"

    def validate(self) -> None:
        if self.streams < 100 or self.horizon < 100:
            raise ValueError("streams and horizon must both be at least 100")
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total < 1:
        return float("nan"), float("nan")
    z = float(norm.ppf(0.5 + confidence / 2))
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _context_flip_lookup(device: torch.device) -> torch.Tensor:
    """Thirteen distinct candidate action rules, independent of incumbent action."""
    contexts = torch.arange(32, device=device, dtype=torch.int64)
    masks = torch.arange(1, 14, device=device, dtype=torch.int64) << 1
    intersections = contexts[:, None] & masks[None, :]
    parity = torch.zeros_like(intersections)
    for bit in range(1, 5):
        parity ^= (intersections >> bit) & 1
    return parity.bool()


def _simulate_scenario(
    *,
    scenario: str,
    p_incumbent_one: float,
    p_incumbent_zero: float,
    true_mean_gain: float,
    contexts: torch.Tensor,
    outcome_uniforms: torch.Tensor,
    query_uniforms: torch.Tensor,
    config: CalibrationConfig,
    device: torch.device,
) -> list[dict[str, Any]]:
    horizon, streams = contexts.shape
    query_rates = torch.tensor(QUERY_RATES, dtype=torch.float64, device=device)
    bound_multipliers = torch.tensor(BOUND_MULTIPLIERS, dtype=torch.float64, device=device)
    caps = torch.floor(query_rates * horizon).to(torch.int64)[None, :]
    flip_lookup = _context_flip_lookup(device)
    stakes = STAKES.to(device)
    log_weights = torch.full_like(stakes, -np.log(len(STAKES)))
    rows: list[dict[str, Any]] = []

    for candidate_count in CANDIDATE_COUNTS:
        candidate_alpha = config.alpha / candidate_count
        threshold = -np.log(candidate_alpha)
        family_thresholds = torch.tensor(
            (
                threshold,
                threshold + np.log(2),
                threshold,
                threshold,
                threshold,
                threshold + np.log(2),
            ),
            dtype=torch.float64,
            device=device,
        )
        shape = (streams, candidate_count, len(QUERY_RATES), len(BOUND_MULTIPLIERS))
        fixed_log_wealth = torch.zeros((*shape, len(STAKES)), dtype=torch.float64, device=device)
        kelly_log_wealth = torch.zeros(shape, dtype=torch.float64, device=device)
        kelly_sum = torch.zeros_like(kelly_log_wealth)
        kelly_squares = torch.zeros_like(kelly_log_wealth)
        pm_log_wealth = torch.zeros_like(kelly_log_wealth)
        positive_log_wealth = torch.zeros_like(kelly_log_wealth)
        pm_sum_observations = torch.zeros_like(kelly_log_wealth)
        pm_sum_squared_deviations = torch.zeros_like(kelly_log_wealth)
        pm_predictive_mean = torch.full_like(kelly_log_wealth, 0.5)
        pm_predictive_variance = torch.full_like(kelly_log_wealth, 0.25)
        crossed = torch.zeros((*shape, len(RULES)), dtype=torch.bool, device=device)
        first_crossing = torch.zeros(
            (streams, len(QUERY_RATES), len(BOUND_MULTIPLIERS), len(RULES)),
            dtype=torch.int32,
            device=device,
        )
        labels_used = torch.zeros((streams, len(QUERY_RATES)), dtype=torch.int64, device=device)
        events_processed = torch.zeros_like(labels_used)

        for event in range(horizon):
            active = labels_used < caps
            context = contexts[event]
            incumbent_one = (context & 1).bool()
            flips = flip_lookup[context, :candidate_count]
            label_probability = torch.where(
                incumbent_one,
                torch.full((streams,), p_incumbent_one, dtype=torch.float64, device=device),
                torch.full((streams,), p_incumbent_zero, dtype=torch.float64, device=device),
            )
            label_one = outcome_uniforms[event] < label_probability
            gain_if_flipped = torch.where(
                incumbent_one[:, None],
                torch.where(
                    label_one[:, None],
                    torch.full(
                        (streams, candidate_count), -FN_COST, dtype=torch.float64, device=device
                    ),
                    torch.full(
                        (streams, candidate_count), FP_COST, dtype=torch.float64, device=device
                    ),
                ),
                torch.where(
                    label_one[:, None],
                    torch.full(
                        (streams, candidate_count), FN_COST, dtype=torch.float64, device=device
                    ),
                    torch.full(
                        (streams, candidate_count), -FP_COST, dtype=torch.float64, device=device
                    ),
                ),
            )
            gain = torch.where(flips, gain_if_flipped, 0.0)
            queried = (query_uniforms[event, :, None] < query_rates[None, :]) & active
            # Direct-IPW gain divided by its declared bound M/q is I_t Z_t/M.
            normalized = (
                gain[:, :, None, None]
                * queried[:, None, :, None]
                / (FN_COST * bound_multipliers[None, None, None, :])
            )
            active_mask = active[:, None, :, None]
            active_float = active_mask.to(torch.float64)

            fixed_log_wealth += torch.log1p(
                normalized.unsqueeze(-1) * stakes
            ) * active_float.unsqueeze(-1)
            fixed_log_e = torch.logsumexp(fixed_log_wealth + log_weights, dim=-1)

            denominator = 4.0 + events_processed[:, None, :, None]
            mean_hat = (4.0 * 0.05 + kelly_sum) / denominator
            second_hat = (4.0 * 0.25 + kelly_squares) / denominator
            kelly_stake = torch.clamp(torch.clamp(mean_hat, min=0.0) / second_hat, 0.0, 0.5)
            kelly_log_wealth += torch.log1p(kelly_stake * normalized) * active_float

            time_index = 1.0 + events_processed[:, None, :, None]
            variance_denominator = pm_predictive_variance * time_index * torch.log1p(time_index)
            stake_level = torch.sqrt(2 * np.log(2 / candidate_alpha) / variance_denominator)
            pm_stake = torch.clamp(stake_level, max=0.5)
            positive_stake = torch.clamp(stake_level, max=1.0)
            observation = 0.5 * (normalized + 1.0)
            residual = observation - pm_predictive_mean
            psi = (-torch.log1p(-pm_stake) - pm_stake) / 4.0
            pm_increment = pm_stake * (observation - 0.5) - 4.0 * residual.square() * psi
            pm_log_wealth += pm_increment * active_float
            positive_log_wealth += torch.log1p(positive_stake * (observation - 0.5)) * active_float

            kelly_sum += normalized * active_float
            kelly_squares += normalized.square() * active_float
            pm_sum_observations += observation * active_float
            updated_mean = (0.5 + pm_sum_observations) / (time_index + 1)
            post_update_residual = observation - updated_mean
            pm_sum_squared_deviations += post_update_residual.square() * active_float
            pm_predictive_mean = torch.where(active_mask, updated_mean, pm_predictive_mean)
            updated_variance = (0.25 + pm_sum_squared_deviations) / (time_index + 1)
            pm_predictive_variance = torch.where(
                active_mask, updated_variance, pm_predictive_variance
            )

            alarm_stack = torch.stack(
                (
                    fixed_log_e >= family_thresholds[0],
                    fixed_log_e >= family_thresholds[1],
                    kelly_log_wealth >= family_thresholds[2],
                    pm_log_wealth >= family_thresholds[3],
                    positive_log_wealth >= family_thresholds[4],
                    positive_log_wealth >= family_thresholds[5],
                ),
                dim=-1,
            )
            crossed |= alarm_stack & active_mask.unsqueeze(-1)
            family_alarm = crossed.any(dim=1)
            first_crossing = torch.where(
                (first_crossing == 0) & family_alarm,
                (events_processed[:, :, None, None] + 1).to(torch.int32),
                first_crossing,
            )
            events_processed += active.to(torch.int64)
            labels_used += queried.to(torch.int64)

        family_crossed = crossed.any(dim=1).cpu().numpy()
        candidate_crossing_count = crossed.sum(dim=1).cpu().numpy()
        first = first_crossing.cpu().numpy()
        labels_np = labels_used.cpu().numpy()
        events_np = events_processed.cpu().numpy()
        for stream in range(streams):
            for query_index, query_rate in enumerate(QUERY_RATES):
                for bound_index, bound_multiplier in enumerate(BOUND_MULTIPLIERS):
                    for rule_index, rule in enumerate(RULES):
                        crossed_family = bool(
                            family_crossed[stream, query_index, bound_index, rule_index]
                        )
                        rows.append(
                            {
                                "scenario": scenario,
                                "stream": stream,
                                "candidate_count": candidate_count,
                                "query_rate": query_rate,
                                "label_cap": int(caps[0, query_index].item()),
                                "bound_multiplier": bound_multiplier,
                                "rule": rule,
                                "candidate_alpha": candidate_alpha,
                                "true_mean_gain": true_mean_gain,
                                "familywise_crossed": crossed_family,
                                "false_promotion": crossed_family and true_mean_gain <= 0,
                                "detection": crossed_family and true_mean_gain > 0,
                                "candidates_crossed": int(
                                    candidate_crossing_count[
                                        stream, query_index, bound_index, rule_index
                                    ]
                                ),
                                "first_crossing_event": int(
                                    first[stream, query_index, bound_index, rule_index]
                                ),
                                "labels_used": int(labels_np[stream, query_index]),
                                "events_processed": int(events_np[stream, query_index]),
                            }
                        )
    return rows


def _summarize(detail: pd.DataFrame) -> pd.DataFrame:
    keys = ["scenario", "candidate_count", "query_rate", "bound_multiplier", "rule"]
    records = []
    for key, group in detail.groupby(keys, sort=False):
        scenario, candidate_count, query_rate, bound_multiplier, rule = key
        crossings = int(group.familywise_crossed.sum())
        low, high = _wilson(crossings, len(group))
        detected = group.loc[group.detection, "first_crossing_event"]
        records.append(
            {
                "scenario": scenario,
                "candidate_count": candidate_count,
                "query_rate": query_rate,
                "bound_multiplier": bound_multiplier,
                "rule": rule,
                "n_streams": len(group),
                "familywise_crossings": crossings,
                "familywise_crossing_rate": crossings / len(group),
                "crossing_ci_low": low,
                "crossing_ci_high": high,
                "false_promotions": int(group.false_promotion.sum()),
                "detection_rate": float(group.detection.mean()),
                "mean_candidates_crossed": float(group.candidates_crossed.mean()),
                "mean_labels_used": float(group.labels_used.mean()),
                "mean_events_processed": float(group.events_processed.mean()),
                "mean_crossing_event_given_crossing": float(detected.mean())
                if len(detected)
                else np.nan,
                "true_mean_gain": float(group.true_mean_gain.iloc[0]),
            }
        )
    return pd.DataFrame(records)


def _paired_contrasts(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_keys = ["scenario", "candidate_count", "query_rate", "bound_multiplier"]
    for key, group in detail.groupby(group_keys, sort=False):
        baseline = group[group.rule.eq("fixed_mixture")].set_index("stream")
        for rule in RULES:
            if rule == "fixed_mixture":
                continue
            comparison = group[group.rule.eq(rule)].set_index("stream")
            if not baseline.index.equals(comparison.index):
                raise ValueError("monitor rules are not paired on identical streams")
            for metric in ("familywise_crossed", "candidates_crossed"):
                difference = comparison[metric].to_numpy(dtype=float) - baseline[metric].to_numpy(
                    dtype=float
                )
                n = len(difference)
                standard_error = float(difference.std(ddof=1) / np.sqrt(n))
                critical = float(t.ppf(0.975, n - 1))
                rows.append(
                    {
                        **dict(zip(group_keys, key, strict=True)),
                        "rule": rule,
                        "contrast": f"{rule}_minus_fixed_mixture",
                        "metric": metric,
                        "n_paired_streams": n,
                        "mean_paired_difference": float(difference.mean()),
                        "ci_low": float(difference.mean() - critical * standard_error),
                        "ci_high": float(difference.mean() + critical * standard_error),
                    }
                )
    return pd.DataFrame(rows)


def _plot(summary: pd.DataFrame, path: Path) -> None:
    colors = dict(zip(RULES, plt.get_cmap("tab10").colors, strict=False))
    styles = {1.0: "-", 1.5: "--", 2.0: ":"}
    fig, axes = plt.subplots(2, len(CANDIDATE_COUNTS), figsize=(18, 9), sharex=True)
    for column, candidate_count in enumerate(CANDIDATE_COUNTS):
        for row, (scenario, metric, title) in enumerate(
            (
                ("aggregate_zero", "familywise_crossing_rate", "Null false-promotion rate"),
                ("aggregate_positive", "detection_rate", "Positive-gain detection power"),
            )
        ):
            axis = axes[row, column]
            cell = summary[
                summary.scenario.eq(scenario) & summary.candidate_count.eq(candidate_count)
            ]
            for rule in RULES:
                for bound_multiplier in BOUND_MULTIPLIERS:
                    series = cell[
                        cell.rule.eq(rule) & cell.bound_multiplier.eq(bound_multiplier)
                    ].sort_values("query_rate")
                    axis.plot(
                        series.query_rate * 100,
                        series[metric] * 100,
                        color=colors[rule],
                        linestyle=styles[bound_multiplier],
                        marker="o",
                        label=(
                            f"{rule}, bound×{bound_multiplier:g}"
                            if column == 0 and row == 0
                            else None
                        ),
                    )
            if row == 0:
                axis.axhline(ALPHA * 100, color="black", linewidth=0.8, alpha=0.7)
                axis.set_title(f"{candidate_count} candidates")
            if column == 0:
                axis.set_ylabel(f"{title} (%)")
            if row == 1:
                axis.set_xlabel("Hard label cap (%)")
            axis.set_xticks([10, 20, 40])
            axis.grid(alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=4, fontsize=8)
    fig.suptitle("Repeated-candidate anytime-gate calibration and power")
    fig.tight_layout(rect=(0, 0.12, 1, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def run(config: CalibrationConfig, output: Path) -> Path:
    config.validate()
    device = torch.device(config.device)
    generator = torch.Generator(device=device).manual_seed(config.seed)
    shape = (config.horizon, config.streams)
    contexts = torch.randint(0, 32, shape, generator=generator, device=device)
    outcome_uniforms = torch.rand(shape, generator=generator, device=device, dtype=torch.float64)
    query_uniforms = torch.rand(shape, generator=generator, device=device, dtype=torch.float64)
    rows: list[dict[str, Any]] = []
    for scenario, (p_one, p_zero, mean_gain) in SCENARIOS.items():
        print(
            f"repeated-null scenario={scenario} streams={config.streams} device={device}",
            flush=True,
        )
        rows.extend(
            _simulate_scenario(
                scenario=scenario,
                p_incumbent_one=p_one,
                p_incumbent_zero=p_zero,
                true_mean_gain=mean_gain,
                contexts=contexts,
                outcome_uniforms=outcome_uniforms,
                query_uniforms=query_uniforms,
                config=config,
                device=device,
            )
        )
    detail = pd.DataFrame(rows)
    summary = _summarize(detail)
    paired = _paired_contrasts(detail)
    output.mkdir(parents=True, exist_ok=False)
    for folder in ("metrics", "reports", "figures"):
        (output / folder).mkdir()
    detail.to_parquet(output / "metrics/repeated_candidate_null_streams.parquet", index=False)
    summary.to_parquet(output / "metrics/repeated_candidate_null_summary.parquet", index=False)
    paired.to_parquet(output / "metrics/repeated_candidate_null_paired.parquet", index=False)
    _plot(summary, output / "figures/repeated_candidate_null_calibration.png")

    primary = summary[summary.candidate_count.eq(13) & summary.bound_multiplier.isin((1.0, 2.0))]
    lines = [
        "# Repeated-candidate nondegenerate null calibration",
        "",
        f"This frozen benchmark used {config.streams} independent streams, horizon {config.horizon}, seed {config.seed}, and `{device}`. It tests 1, 5, and 13 distinct fixed candidate policies; 10%, 20%, and 40% hard query caps; and globally valid support bounds multiplied by 1, 1.5, and 2. Six sequential monitors share each queried outcome path. Candidate hypotheses receive equal Bonferroni alpha `0.05 / C`.",
        "",
        "The null is nondegenerate: each candidate changes its action on half the contexts, with conditional mean gains balanced at +0.4 and −0.4 cost units on the changed contexts, yielding exactly zero history-conditional average gain and nonzero paired-cost variance. The positive and negative alternatives have exact mean gains +0.12 and −0.12 per event. Query propensities are fixed and independent of the visible context. The gate uses one global support bound and does not condition its stake or stopping rule on the current context. These results address the history-conditional average-gain null; they do not establish conditional-on-current-context validity.",
        "",
        "## Nondegenerate null: 13 candidates",
        "",
        "| Query cap | Bound multiplier | Monitor | Familywise false promotion (95% Wilson CI) | Mean labels |",
        "|---:|---:|---|---:|---:|",
    ]
    null = primary[primary.scenario.eq("aggregate_zero")]
    for row in null.sort_values(["query_rate", "bound_multiplier", "rule"]).itertuples(index=False):
        lines.append(
            f"| {row.query_rate:.0%} | {row.bound_multiplier:g}× | {row.rule} | {row.familywise_crossings}/{row.n_streams} ({row.familywise_crossing_rate:.3f}; {row.crossing_ci_low:.3f}–{row.crossing_ci_high:.3f}) | {row.mean_labels_used:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Positive alternative: 13 candidates",
            "",
            "| Query cap | Bound multiplier | Monitor | Detection power (95% Wilson CI) | Mean first crossing event among detections |",
            "|---:|---:|---|---:|---:|",
        ]
    )
    positive = primary[primary.scenario.eq("aggregate_positive")]
    for row in positive.sort_values(["query_rate", "bound_multiplier", "rule"]).itertuples(
        index=False
    ):
        lines.append(
            f"| {row.query_rate:.0%} | {row.bound_multiplier:g}× | {row.rule} | {row.familywise_crossings}/{row.n_streams} ({row.detection_rate:.3f}; {row.crossing_ci_low:.3f}–{row.crossing_ci_high:.3f}) | {row.mean_crossing_event_given_crossing:.1f} |"
        )
    lines.extend(
        [
            "",
            "The complete 1/5/13-candidate grid, strict negative control, all bound scales, and paired comparisons are in the Parquet files. Confidence intervals are pointwise; no monitor is selected from this grid. The exact mathematical validity still follows from each process's one-step supermartingale argument, predictable stakes, globally correct support bounds, randomized query design, and the union bound over frozen candidates. Monte Carlo rates are diagnostics, not the proof. This synthetic setup assumes immediate labels, i.i.d. contexts/outcomes, fixed policies, and no action-dependent outcomes.",
            "",
            "## Reproduction",
            "",
            f"`uv run python scripts/calibrate_repeated_candidate_nulls.py --streams {config.streams} --horizon {config.horizon} --seed {config.seed} --device {device} --output {output.as_posix()}`",
        ]
    )
    report_path = output / "reports/repeated_candidate_null_calibration.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "repeated_candidate_non_degenerate_mean_null_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "environment": environment(),
        "scenarios": {
            name: {"p_incumbent_one": p[0], "p_incumbent_zero": p[1], "true_mean_gain": p[2]}
            for name, p in SCENARIOS.items()
        },
        "candidate_counts": list(CANDIDATE_COUNTS),
        "query_rates": list(QUERY_RATES),
        "bound_multipliers": list(BOUND_MULTIPLIERS),
        "rules": list(RULES),
        "familywise_allocation": "equal Bonferroni alpha / candidate_count",
        "information_protocol": [
            "candidate policies are fixed before stream generation",
            "all candidate tests share the same queried labels",
            "query propensities are fixed and independent of current context",
            "current event labels affect the gate only when queried",
            "the monitor stops before an event when its hard label cap is exhausted",
            "the gate uses a fixed global support bound and does not normalize by current context",
        ],
        "artifacts": [
            "metrics/repeated_candidate_null_streams.parquet",
            "metrics/repeated_candidate_null_summary.parquet",
            "metrics/repeated_candidate_null_paired.parquet",
            "figures/repeated_candidate_null_calibration.png",
            "reports/repeated_candidate_null_calibration.md",
        ],
    }
    (output / "reports/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = Path("scripts/calibrate_repeated_candidate_nulls.py")
    protocol_path = Path("docs/repeated_candidate_null_calibration_protocol.md")
    for path in (source_path, protocol_path):
        if path.exists():
            manifest["sha256"]["source_files"][str(path)] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=26102026)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args(argv)
    config = CalibrationConfig(
        streams=args.streams,
        horizon=args.horizon,
        seed=args.seed,
        device=args.device,
    )
    print(run(config, args.output), flush=True)


if __name__ == "__main__":
    main()
