"""Compare sequential and fixed-horizon candidate promotion under changing gains.

The benchmark freezes one candidate before a shadow interval, monitors paired
bounded costs, then scores each promotion decision on the remaining independent
potential-outcome stream. It is a controlled synthetic comparison, not a claim
about deployments where actions change outcomes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.stats import t

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..data.gpu.environment import environment
from .experiment import finalize_manifest
from .promotion_grid import (
    _fixed_horizon_empirical_bernstein_gate,
    _fixed_horizon_gate,
    _time_splits,
)


@dataclass(frozen=True)
class PromotionTimingConfig:
    n: int = 3200
    seeds: int = 1000
    seed_offset: int = 20401023
    alpha: float = 0.05
    switching_cost: float = 0.05
    multi_start_fractions: tuple[float, ...] = (0.0, 1 / 3, 2 / 3)
    device: str = "cuda"

    def validate(self) -> PromotionTimingConfig:
        if self.n < 1000 or self.seeds < 1:
            raise ValueError("n must be >=1000 and seeds must be positive")
        if not np.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0, 1)")
        if not np.isfinite(self.switching_cost) or self.switching_cost < 0:
            raise ValueError("switching_cost must be finite and nonnegative")
        if not self.multi_start_fractions or self.multi_start_fractions[0] != 0:
            raise ValueError("multi-start grid must begin at zero")
        if len(self.multi_start_fractions) != 3:
            raise ValueError("this benchmark labels the method as a three-start mixture")
        if tuple(sorted(set(self.multi_start_fractions))) != self.multi_start_fractions:
            raise ValueError("multi-start fractions must be strictly increasing")
        if any(not np.isfinite(x) or not 0 <= x < 1 for x in self.multi_start_fractions):
            raise ValueError("multi-start fractions must be in [0, 1)")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")
        return self


def _benefit_schedule(scenario: str, n: int, monitor_start: int, monitor_end: int) -> np.ndarray:
    """Evaluator-only expected cost reduction; never passed to gate functions."""
    benefit = np.zeros(n, dtype=np.float64)
    monitor_length = monitor_end - monitor_start
    if scenario == "no_benefit":
        return benefit
    if scenario == "early_transient":
        benefit[monitor_start : monitor_start + monitor_length // 5] = 0.22
    elif scenario == "benefit_reversal":
        benefit[monitor_start : monitor_start + monitor_length // 5] = 0.22
        benefit[monitor_start + monitor_length // 5 :] = -0.04
    elif scenario == "persistent_benefit":
        benefit[monitor_start:] = 0.12
    elif scenario == "late_persistent":
        late_start = monitor_start + (2 * monitor_length) // 3
        benefit[late_start:] = 0.18
    else:
        raise ValueError(f"unknown timing scenario: {scenario}")
    return benefit


def _generate_costs(
    benefit: np.ndarray,
    *,
    seeds: int,
    seed: int,
    device: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate independent bounded potential costs on the requested device."""
    import torch

    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but PyTorch cannot access it")
    generator = torch.Generator(device=device).manual_seed(seed)
    means = torch.as_tensor(benefit, dtype=torch.float32, device=device)
    incumbent_u = torch.rand((seeds, len(benefit)), generator=generator, device=device)
    candidate_u = torch.rand((seeds, len(benefit)), generator=generator, device=device)
    incumbent = (incumbent_u < 0.5).to(torch.uint8)
    candidate = (candidate_u < (0.5 - means).unsqueeze(0)).to(torch.uint8)
    return incumbent.cpu().numpy(), candidate.cpu().numpy()


def _vectorized_crossing_times(
    gains: np.ndarray, *, bound: float, alpha: float, starts: tuple[int, ...]
) -> np.ndarray:
    """First crossing times for the same fixed-stake mixture used by eprocess.py."""
    values = np.asarray(gains, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] == 0 or not np.isfinite(values).all():
        raise ValueError("gains must be a finite seed-by-time matrix")
    if not np.isfinite(bound) or bound <= 0 or not 0 < alpha < 1:
        raise ValueError("bound must be positive and alpha in (0,1)")
    if not starts or tuple(sorted(set(starts))) != starts or starts[0] < 0:
        raise ValueError("starts must be strictly increasing nonnegative indices")
    if starts[-1] >= values.shape[1]:
        raise ValueError("all starts must precede the final observation")
    stakes = np.asarray((0.05, 0.1, 0.2, 0.4, 0.8))
    log_weights = np.full(len(stakes), -np.log(len(stakes)))
    log_wealth = np.zeros((len(values), len(starts), len(stakes)), dtype=np.float64)
    crossings = np.full(len(values), -1, dtype=np.int64)
    threshold = -np.log(alpha)
    for time_index in range(values.shape[1]):
        active = np.asarray(starts) <= time_index
        if active.any():
            factor = 1 + values[:, time_index, None] * stakes[None, :] / bound
            if np.any(factor <= 0):
                raise ValueError("gain falls outside the e-process bound")
            log_wealth[:, active, :] += np.log(factor[:, None, :])
        component_log_e = logsumexp(log_wealth + log_weights[None, None, :], axis=2)
        component_log_e[:, ~active] = 0.0  # unborn processes contribute e-value one
        mixture_log_e = logsumexp(component_log_e, axis=1) - np.log(len(starts))
        newly_crossed = (crossings < 0) & (mixture_log_e >= threshold)
        crossings[newly_crossed] = time_index
    return crossings


def _ci(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return (float("nan"), float("nan"))
    radius = float(t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return float(values.mean() - radius), float(values.mean() + radius)


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denom
    return float(center - radius), float(center + radius)


def _evaluate_scenario(
    scenario: str, *, config: PromotionTimingConfig, scenario_index: int
) -> list[dict[str, Any]]:
    train_end, validation_end, monitor_end = _time_splits(config.n)
    monitor = slice(validation_end, monitor_end)
    deployment = slice(monitor_end, config.n)
    monitor_length = monitor.stop - monitor.start
    benefit = _benefit_schedule(scenario, config.n, monitor.start, monitor.stop)
    incumbent, candidate = _generate_costs(
        benefit,
        seeds=config.seeds,
        seed=config.seed_offset + scenario_index * 100_003,
        device=config.device,
    )
    # The monitor sees only paired observed costs. The evaluator retains benefit truth.
    switch_per_monitor_event = config.switching_cost / (deployment.stop - deployment.start)
    observed_gain = (
        incumbent[:, monitor].astype(float)
        - candidate[:, monitor].astype(float)
        - switch_per_monitor_event
    )
    bound = 1.0 + switch_per_monitor_event
    full_starts = (0,)
    relative_starts = tuple(
        min(monitor_length - 1, round(fraction * monitor_length))
        for fraction in config.multi_start_fractions
    )
    if len(set(relative_starts)) != len(relative_starts):
        raise ValueError("multi-start fractions collapse to duplicate starts at this n")
    full_crossings = _vectorized_crossing_times(
        observed_gain, bound=bound, alpha=config.alpha, starts=full_starts
    )
    multi_crossings = _vectorized_crossing_times(
        observed_gain, bound=bound, alpha=config.alpha, starts=relative_starts
    )
    eb_results = [
        _fixed_horizon_empirical_bernstein_gate(row, bound=bound, alpha=config.alpha)
        for row in observed_gain
    ]
    eb_promoted = np.asarray([result[0] for result in eb_results], dtype=bool)
    hoeffding_promoted = np.asarray(
        [_fixed_horizon_gate(row, bound=bound, alpha=config.alpha) for row in observed_gain],
        dtype=bool,
    )
    methods: dict[str, tuple[np.ndarray, np.ndarray]] = {
        "sequential_full_start": (full_crossings >= 0, full_crossings),
        "sequential_multi_start_3": (multi_crossings >= 0, multi_crossings),
        "empirical_bernstein_fixed_horizon": (
            eb_promoted,
            np.where(eb_promoted, monitor_length - 1, -1),
        ),
        "hoeffding_fixed_horizon": (
            hoeffding_promoted,
            np.where(hoeffding_promoted, monitor_length - 1, -1),
        ),
        "never_promote": (np.zeros(config.seeds, dtype=bool), np.full(config.seeds, -1)),
    }
    rows: list[dict[str, Any]] = []
    for method, (promoted, crossing_times) in methods.items():
        for seed_index in range(config.seeds):
            crossing = int(crossing_times[seed_index])
            if not promoted[seed_index]:
                evaluation_start = config.n
                oracle_net_gain = 0.0
                realized_net_gain = 0.0
            else:
                # Sequential deployment begins on the event after certification;
                # the fixed-horizon gate can act only after the shadow horizon.
                evaluation_start = (
                    monitor.start + crossing + 1
                    if method.startswith("sequential_")
                    else deployment.start
                )
                oracle_net_gain = float(benefit[evaluation_start:].sum() - config.switching_cost)
                realized_net_gain = float(
                    incumbent[seed_index, evaluation_start:].astype(float).sum()
                    - candidate[seed_index, evaluation_start:].astype(float).sum()
                    - config.switching_cost
                )
            rows.append(
                {
                    "scenario": scenario,
                    "seed": config.seed_offset + scenario_index * 100_003 + seed_index,
                    "method": method,
                    "promoted": bool(promoted[seed_index]),
                    "certificate_time_in_shadow": crossing if crossing >= 0 else None,
                    "right_censored_at": monitor_length if crossing < 0 else None,
                    "promotion_event_index": (monitor.start + crossing if crossing >= 0 else None),
                    "evaluation_start_index": evaluation_start,
                    "training_end_index": train_end,
                    "validation_end_index": validation_end,
                    "shadow_start_index": monitor.start,
                    "shadow_end_index": monitor.stop,
                    "deployment_start_index": deployment.start,
                    "deployment_end_index": deployment.stop,
                    "oracle_postpromotion_net_gain": oracle_net_gain,
                    "realized_postpromotion_net_gain": realized_net_gain,
                    "harmful_postpromotion_promotion": bool(
                        promoted[seed_index] and oracle_net_gain <= 0
                    ),
                    "switching_cost": config.switching_cost if promoted[seed_index] else 0.0,
                    "monitor_expected_gain_per_event": float(benefit[monitor].mean()),
                    "oracle_benefit_schedule_id": scenario,
                }
            )
    return rows


def _summarize(rows: pd.DataFrame) -> pd.DataFrame:
    summary = []
    for (scenario, method), group in rows.groupby(["scenario", "method"], sort=False):
        rate = float(group.promoted.mean())
        lo, hi = _wilson(int(group.promoted.sum()), len(group))
        harmful_count = int(group.harmful_postpromotion_promotion.sum())
        harmful_lo, harmful_hi = _wilson(harmful_count, len(group))
        expected = group.oracle_postpromotion_net_gain.to_numpy(dtype=float)
        realized = group.realized_postpromotion_net_gain.to_numpy(dtype=float)
        expected_ci = _ci(expected)
        realized_ci = _ci(realized)
        promoted_times = group.loc[group.promoted, "certificate_time_in_shadow"].dropna()
        summary.append(
            {
                "scenario": scenario,
                "method": method,
                "n_seeds": len(group),
                "promotion_rate": rate,
                "promotion_rate_ci_low": lo,
                "promotion_rate_ci_high": hi,
                "mean_oracle_postpromotion_net_gain": float(expected.mean()),
                "oracle_gain_ci_low": expected_ci[0],
                "oracle_gain_ci_high": expected_ci[1],
                "mean_realized_postpromotion_net_gain": float(realized.mean()),
                "realized_gain_ci_low": realized_ci[0],
                "realized_gain_ci_high": realized_ci[1],
                "harmful_promotion_rate": float(group.harmful_postpromotion_promotion.mean()),
                "harmful_promotion_ci_low": harmful_lo,
                "harmful_promotion_ci_high": harmful_hi,
                "mean_certificate_time_if_promoted": (
                    float(promoted_times.mean()) if len(promoted_times) else np.nan
                ),
                "restricted_mean_certificate_time": float(
                    group.certificate_time_in_shadow.fillna(
                        group.shadow_end_index - group.shadow_start_index
                    ).mean()
                ),
            }
        )
    return pd.DataFrame(summary)


def _write_outputs(summary: pd.DataFrame, figure_path: Path) -> None:
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    scenarios = list(summary.scenario.drop_duplicates())
    methods = list(summary.method.drop_duplicates())
    labels = {
        "sequential_full_start": "Sequential, full start",
        "sequential_multi_start_3": "Sequential, 3 starts",
        "empirical_bernstein_fixed_horizon": "Empirical-Bernstein, fixed horizon",
        "hoeffding_fixed_horizon": "Hoeffding, fixed horizon",
        "never_promote": "Never promote",
    }
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    x = np.arange(len(scenarios))
    width = 0.8 / len(methods)
    for j, method in enumerate(methods):
        g = summary[summary.method.eq(method)].set_index("scenario").reindex(scenarios)
        offset = (j - (len(methods) - 1) / 2) * width
        axes[0].bar(
            x + offset,
            g.promotion_rate,
            width,
            yerr=np.vstack(
                [
                    np.maximum(0.0, g.promotion_rate - g.promotion_rate_ci_low),
                    np.maximum(0.0, g.promotion_rate_ci_high - g.promotion_rate),
                ]
            ),
            capsize=2,
            label=labels[method],
        )
        axes[1].bar(
            x + offset,
            g.mean_oracle_postpromotion_net_gain,
            width,
            yerr=np.vstack(
                [
                    np.maximum(
                        0.0,
                        g.mean_oracle_postpromotion_net_gain - g.oracle_gain_ci_low,
                    ),
                    np.maximum(
                        0.0,
                        g.oracle_gain_ci_high - g.mean_oracle_postpromotion_net_gain,
                    ),
                ]
            ),
            capsize=2,
        )
        axes[2].bar(
            x + offset,
            g.harmful_promotion_rate,
            width,
            yerr=np.vstack(
                [
                    np.maximum(
                        0.0,
                        g.harmful_promotion_rate - g.harmful_promotion_ci_low,
                    ),
                    np.maximum(
                        0.0,
                        g.harmful_promotion_ci_high - g.harmful_promotion_rate,
                    ),
                ]
            ),
            capsize=2,
        )
    axes[0].set_ylabel("Promotion probability")
    axes[1].set_ylabel("Mean oracle net gain after promotion")
    axes[2].set_ylabel("Promotion with nonpositive future net gain")
    for axis in axes:
        axis.set_xticks(x, scenarios, rotation=25, ha="right")
        axis.grid(axis="y", alpha=0.25)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[0].legend(fontsize=8, loc="best")
    fig.suptitle("Promotion timing under transient and persistent candidate benefit")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)


def run_promotion_timing(config: PromotionTimingConfig, output: Path) -> Path:
    config.validate()
    if config.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available")
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metrics_dir / "promotion_timing_streams.parquet"
    summary_path = metrics_dir / "promotion_timing_summary.parquet"
    if detail_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite existing timing benchmark: {output}")
    scenario_names = (
        "no_benefit",
        "early_transient",
        "benefit_reversal",
        "persistent_benefit",
        "late_persistent",
    )
    records = []
    for scenario_index, scenario in enumerate(scenario_names):
        print(
            f"promotion-timing scenario={scenario} seeds={config.seeds} device={config.device}",
            flush=True,
        )
        records.extend(_evaluate_scenario(scenario, config=config, scenario_index=scenario_index))
    detail = pd.DataFrame(records)
    summary = _summarize(detail)
    detail.to_parquet(detail_path, index=False)
    summary.to_parquet(summary_path, index=False)
    figure_path = output / "figures/promotion_timing.png"
    _write_outputs(summary, figure_path)
    _, validation_end, monitor_end = _time_splits(config.n)
    lines = [
        "# Promotion timing benchmark",
        "",
        f"This generated benchmark compares two sequential e-processes, two fixed-horizon gates, and a no-promotion control over {config.seeds} independent streams in each of five predeclared scenarios. Potential costs are Bernoulli and generated on `{config.device}`; the candidate is conceptually frozen before shadow monitoring. The first {validation_end} events are a reserved pre-monitor construction prefix and are not used to fit or select a model in this focused test; shadow monitoring spans [{validation_end},{monitor_end}); the untouched final slice is [{monitor_end},{config.n}).",
        "",
        (
            "The full-start and three-start e-processes use the repository's fixed-stake bounded-mean mixture at alpha="
            f"{config.alpha:g}. The three starts are fixed at shadow fractions {config.multi_start_fractions}; their equally weighted mixture is Ville-valid under the pointwise conditional-mean null. The fixed-horizon Hoeffding gate is valid for average expected gain under independent bounded observations, including non-identically distributed streams. The empirical-Bernstein gate uses the independent, bounded, non-identically distributed version of Maurer and Pontil's bound (Theorem 11); it tests the average expected gain at this one prespecified horizon and is not anytime-valid. All methods use the same paired monitor outcomes and cost bound."
        ),
        "",
        f"Potential benefit in the shadow is 0 for `no_benefit`, 0.22 for the first fifth only in `early_transient`, 0.22 for the first fifth then -0.04 for the remaining stream in `benefit_reversal`, 0.12 throughout `persistent_benefit`, and 0.18 in the final third only in `late_persistent`. The scenario schedule is evaluator-only. For the sequential gates, promotion begins on the event after a crossing; for the fixed-horizon gate, promotion begins after the shadow window. Outcomes after promotion are scored with simulator-known potential costs, and the one-time switching charge is {config.switching_cost:g}. The synthetic setup assumes actions do not alter outcomes; results do not identify counterfactual policy values in performative settings.",
        "",
        "## Results by scenario and rule",
        "",
        "Independent seeds are the statistical units. Intervals are Wilson 95% intervals for promotion rates and t intervals over seed-level net gains. Non-crossings are right-censored at the shadow horizon in the restricted mean certificate time.",
        "",
        "| Scenario | Method | Promote (95% CI) | Mean oracle future net gain (95% CI) | Harmful promotion | Mean certificate time |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        mean_time = (
            f"{row.mean_certificate_time_if_promoted:.1f}"
            if np.isfinite(row.mean_certificate_time_if_promoted)
            else "—"
        )
        lines.append(
            f"| {row.scenario} | {row.method} | {row.promotion_rate:.3f} [{row.promotion_rate_ci_low:.3f}, {row.promotion_rate_ci_high:.3f}] | {row.mean_oracle_postpromotion_net_gain:.3f} [{row.oracle_gain_ci_low:.3f}, {row.oracle_gain_ci_high:.3f}] | {row.harmful_promotion_rate:.3f} | {mean_time} |"
        )
    lines.extend(
        [
            "",
            "A promotion on a transient shadow gain can be statistically valid for the historical shadow estimand and still have nonpositive future value. The `harmful promotion` column measures that decision mismatch; it is not a false-rejection rate for the e-process null. The no-benefit scenario is the pointwise-null calibration diagnostic. A finite Monte Carlo run is not itself the validity proof. Empirical-Bernstein bound: [Maurer and Pontil (2009), Theorem 11](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf).",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-promotion-timing --seeds {config.seeds} --seed-offset {config.seed_offset} --device {config.device} --output {output.as_posix()}`",
            "",
            "Detailed seed-level outcomes, summary metrics, the figure, and a hash manifest are stored beside this report.",
        ]
    )
    report_path = reports_dir / "promotion_timing.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "promotion_timing_under_nonstationary_benefit",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "environment": environment(),
        "scenarios": list(scenario_names),
        "methods": [
            "sequential_full_start",
            "sequential_multi_start_3",
            "empirical_bernstein_fixed_horizon",
            "hoeffding_fixed_horizon",
            "never_promote",
        ],
        "information_protocol": [
            "candidate fixed before shadow observations",
            "train and validation indices precede shadow; no model fitting uses shadow outcomes",
            "gate inputs contain paired monitor costs only; oracle schedule is evaluator-only",
            "sequential processes start at predeclared shadow indices and stop on promotion",
            "fixed-horizon Hoeffding is evaluated once and covers independent non-identical bounded costs",
            "empirical-Bernstein uses the independent bounded non-identical result; observations must be independent across events",
            "future potential costs are used only by the synthetic evaluator after promotion",
            "candidate and incumbent outcomes are generated independently; action-dependent outcomes are out of scope",
        ],
        "artifacts": [
            "metrics/promotion_timing_streams.parquet",
            "metrics/promotion_timing_summary.parquet",
            "figures/promotion_timing.png",
            "reports/promotion_timing.md",
        ],
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/promotion_timing"))
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20401023)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--switching-cost", type=float, default=0.05)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    args = parser.parse_args(argv)
    config = PromotionTimingConfig(
        n=args.n,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        switching_cost=args.switching_cost,
        device=args.device,
    )
    print(run_promotion_timing(config, args.output), flush=True)


if __name__ == "__main__":
    main()
