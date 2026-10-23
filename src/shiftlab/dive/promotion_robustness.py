"""Evaluate promotion rules over switching costs and benefit reversals.

This is a controlled synthetic benchmark. The candidate is frozen before the
shadow interval, all gates receive the same paired bounded cost outcomes, and
the simulator's benefit schedule is evaluator-only.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment
from .experiment import finalize_manifest
from .persistence_promotion import _two_phase_decisions
from .promotion_grid import (
    _fixed_horizon_empirical_bernstein_gate,
    _fixed_horizon_gate,
    _time_splits,
)
from .promotion_timing import (
    _generate_costs,
    _summarize,
    _vectorized_crossing_times,
)


@dataclass(frozen=True)
class PromotionRobustnessConfig:
    n: int = 3200
    seeds: int = 1000
    seed_offset: int = 23102026
    alpha: float = 0.05
    switching_costs: tuple[float, ...] = (0.0, 10.0, 30.0, 60.0)
    discovery_fractions: tuple[float, ...] = (0.25, 0.5, 0.75)
    device: str = "cuda"

    def validate(self) -> PromotionRobustnessConfig:
        if self.n < 1000 or self.seeds < 1:
            raise ValueError("n must be >=1000 and seeds must be positive")
        if not np.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        if (
            not self.switching_costs
            or tuple(sorted(set(self.switching_costs))) != self.switching_costs
        ):
            raise ValueError("switching_costs must be strictly increasing and nonempty")
        if any(not np.isfinite(x) or x < 0 for x in self.switching_costs):
            raise ValueError("switching costs must be finite and nonnegative")
        if (
            not self.discovery_fractions
            or tuple(sorted(set(self.discovery_fractions))) != self.discovery_fractions
        ):
            raise ValueError("discovery fractions must be strictly increasing and nonempty")
        if any(not np.isfinite(x) or not 0 < x < 1 for x in self.discovery_fractions):
            raise ValueError("discovery fractions must lie in (0,1)")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")
        return self


def _schedule(scenario: str, n: int, monitor_start: int, monitor_end: int) -> np.ndarray:
    """Return evaluator-only expected cost reductions for one regime schedule."""
    benefit = np.zeros(n, dtype=np.float64)
    length = monitor_end - monitor_start
    if scenario == "no_benefit":
        return benefit
    if scenario == "persistent_benefit":
        benefit[monitor_start:] = 0.12
        return benefit
    if scenario.startswith("reversal_"):
        _, onset_label, duration_label = scenario.split("_")
        onset_fraction = {"early": 0.20, "middle": 0.50, "late": 0.70}[onset_label]
        duration_fraction = {"short": 0.20, "long": 0.55}[duration_label]
        reversal_start = monitor_start + round(onset_fraction * length)
        recovery = min(n, reversal_start + round(duration_fraction * n))
        benefit[monitor_start:reversal_start] = 0.22
        benefit[reversal_start:recovery] = -0.04
        return benefit
    raise ValueError(f"unknown robustness scenario: {scenario}")


def _rows_for_scenario(
    scenario: str,
    *,
    config: PromotionRobustnessConfig,
    scenario_index: int,
) -> list[dict[str, Any]]:
    train_end, validation_end, monitor_end = _time_splits(config.n)
    monitor_start = validation_end
    monitor_length = monitor_end - monitor_start
    deployment_start = monitor_end
    benefit = _schedule(scenario, config.n, monitor_start, monitor_end)
    seed = config.seed_offset + scenario_index * 100_003
    incumbent, candidate = _generate_costs(
        benefit, seeds=config.seeds, seed=seed, device=config.device
    )
    records: list[dict[str, Any]] = []

    # Each cost value uses identical potential outcomes. The charge is
    # amortized over the untouched deployment horizon for the testing bound.
    for switching_cost in config.switching_costs:
        per_event_charge = switching_cost / (config.n - deployment_start)
        gains = (
            incumbent[:, monitor_start:monitor_end].astype(float)
            - candidate[:, monitor_start:monitor_end].astype(float)
            - per_event_charge
        )
        bound = 1.0 + per_event_charge
        full = _vectorized_crossing_times(gains, bound=bound, alpha=config.alpha, starts=(0,))
        multi = _vectorized_crossing_times(
            gains,
            bound=bound,
            alpha=config.alpha,
            starts=(0, monitor_length // 3, (2 * monitor_length) // 3),
        )
        eb = np.asarray(
            [
                _fixed_horizon_empirical_bernstein_gate(row, bound=bound, alpha=config.alpha)[0]
                for row in gains
            ],
            dtype=bool,
        )
        hoeffding = np.asarray(
            [_fixed_horizon_gate(row, bound=bound, alpha=config.alpha) for row in gains],
            dtype=bool,
        )
        method_decisions: dict[str, tuple[np.ndarray, np.ndarray]] = {
            "sequential_full_start": (full >= 0, full),
            "sequential_multi_start_3": (multi >= 0, multi),
            "empirical_bernstein_fixed_horizon": (eb, np.where(eb, monitor_length - 1, -1)),
            "hoeffding_fixed_horizon": (hoeffding, np.where(hoeffding, monitor_length - 1, -1)),
            "never_promote": (np.zeros(config.seeds, dtype=bool), np.full(config.seeds, -1)),
        }
        for fraction in config.discovery_fractions:
            discovery_length = round(fraction * monitor_length)
            _disc, persist, promoted = _two_phase_decisions(
                gains,
                discovery_length=discovery_length,
                bound=bound,
                alpha=config.alpha,
            )
            crossing = np.where(promoted, discovery_length + persist, -1)
            method_decisions[f"persistence_intersection_d={fraction:g}"] = (promoted, crossing)

        for method, (promoted, crossings) in method_decisions.items():
            for i in range(config.seeds):
                crossed = int(crossings[i])
                is_promoted = bool(promoted[i])
                evaluation_start = (
                    monitor_start + crossed + 1
                    if is_promoted and method.startswith(("sequential_", "persistence_"))
                    else deployment_start
                    if is_promoted
                    else config.n
                )
                oracle_net = (
                    float(benefit[evaluation_start:].sum() - switching_cost) if is_promoted else 0.0
                )
                realized_net = (
                    float(
                        incumbent[i, evaluation_start:].astype(float).sum()
                        - candidate[i, evaluation_start:].astype(float).sum()
                        - switching_cost
                    )
                    if is_promoted
                    else 0.0
                )
                records.append(
                    {
                        "scenario": scenario,
                        "switching_cost": switching_cost,
                        "seed": seed + i,
                        "method": method,
                        "promoted": is_promoted,
                        "discovery_fraction": (
                            float(method.rsplit("=", 1)[1])
                            if method.startswith("persistence_")
                            else None
                        ),
                        "certificate_time_in_shadow": crossed if is_promoted else None,
                        "right_censored_at": monitor_length if not is_promoted else None,
                        "evaluation_start_index": evaluation_start,
                        "training_end_index": train_end,
                        "validation_end_index": validation_end,
                        "shadow_start_index": monitor_start,
                        "shadow_end_index": monitor_end,
                        "deployment_start_index": deployment_start,
                        "deployment_end_index": config.n,
                        "oracle_postpromotion_net_gain": oracle_net,
                        "realized_postpromotion_net_gain": realized_net,
                        "harmful_postpromotion_promotion": bool(is_promoted and oracle_net <= 0),
                        "switching_charge_paid": switching_cost if is_promoted else 0.0,
                        "oracle_benefit_schedule_id": scenario,
                        "alpha_each_phase": config.alpha
                        if method.startswith("persistence_")
                        else None,
                    }
                )
    return records


def run_promotion_robustness(config: PromotionRobustnessConfig, output: Path) -> Path:
    config.validate()
    if config.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
    metrics = output / "metrics"
    reports = output / "reports"
    figures = output / "figures"
    for directory in (metrics, reports, figures):
        directory.mkdir(parents=True, exist_ok=True)
    detail_path = metrics / "promotion_robustness_streams.parquet"
    summary_path = metrics / "promotion_robustness_summary.parquet"
    if detail_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite existing robustness grid: {output}")
    scenarios = (
        "no_benefit",
        "persistent_benefit",
        "reversal_early_short",
        "reversal_early_long",
        "reversal_middle_long",
        "reversal_late_short",
    )
    rows: list[dict[str, Any]] = []
    for index, scenario in enumerate(scenarios):
        print(f"robustness scenario={scenario} device={config.device}", flush=True)
        rows.extend(_rows_for_scenario(scenario, config=config, scenario_index=index))
    detail = pd.DataFrame(rows)
    group_fields = ["scenario", "switching_cost", "method"]
    summaries = []
    for (scenario, cost, method), group in detail.groupby(group_fields, sort=False):
        summary = _summarize(group.assign(scenario=scenario, method=method)).iloc[0].to_dict()
        summary["switching_cost"] = cost
        summaries.append(summary)
    summary_frame = pd.DataFrame(summaries)
    detail.to_parquet(detail_path, index=False)
    summary_frame.to_parquet(summary_path, index=False)

    # Full grid visualization: expected net gain and harmful promotion.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    methods = list(summary_frame.method.drop_duplicates())
    scenarios_order = list(scenarios)
    fig, axes = plt.subplots(2, 1, figsize=(16, 11), sharex=True)
    x_labels = [f"{s}\n${c:g}" for s in scenarios_order for c in config.switching_costs]
    positions = np.arange(len(x_labels))
    width = 0.82 / len(methods)
    for j, method in enumerate(methods):
        values = []
        harms = []
        for scenario in scenarios_order:
            for cost in config.switching_costs:
                row = summary_frame[
                    summary_frame.scenario.eq(scenario)
                    & summary_frame.switching_cost.eq(cost)
                    & summary_frame.method.eq(method)
                ].iloc[0]
                values.append(row.mean_oracle_postpromotion_net_gain)
                harms.append(row.harmful_promotion_rate)
        offset = (j - (len(methods) - 1) / 2) * width
        axes[0].bar(positions + offset, values, width, label=method)
        axes[1].bar(positions + offset, harms, width)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_ylabel("Mean oracle post-promotion net gain")
    axes[1].set_ylabel("Harmful promotions / all seeds")
    axes[1].set_xticks(positions, x_labels, rotation=55, ha="right", fontsize=8)
    axes[0].legend(ncol=4, fontsize=8)
    for axis in axes:
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Promotion methods across switching cost and benefit-reversal grid")
    fig.tight_layout()
    figure_path = figures / "promotion_robustness_grid.png"
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)

    report_lines = [
        "# Promotion robustness grid",
        "",
        f"This predeclared grid compares the existing sequential full-start, three-start, empirical-Bernstein, Hoeffding, never-promote, and two-phase persistence gates over {len(scenarios)} schedules and switching charges {config.switching_costs}. Each cell uses {config.seeds} independent CUDA-generated streams (device `{config.device}`), paired across methods and cost levels. The candidate is frozen before shadow outcomes; schedules are evaluator-only; future potential costs score net value after promotion.",
        "",
        "Reversal schedules first provide expected benefit +0.22, then impose -0.04 for 20% (short) or 55% (long) of the full stream, with early, middle, and late onset as specified by scenario names; benefit returns to zero after the reversal interval. The no-benefit and persistent-benefit schedules are controls. Switching cost is paid once on promotion and is amortized across the fixed deployment horizon when constructing monitor gains. Sequential rules can promote after a crossing; fixed-horizon rules act after shadow. The simulator assumes independent Bernoulli potential costs and no action-dependent outcomes.",
        "",
        "The e-processes test conditional mean net gain under their bounded-increment assumptions. The two-phase rule is a standard intersection-union construction at level alpha in each phase. Fixed-horizon gates retain their stated independent bounded-observation assumptions. Monte Carlo error bars describe seed variation; they do not establish theorem validity. The complete grid is reported without selecting a discovery fraction or cost from evaluation outcomes. No multiplicity adjustment is made across descriptive grid cells.",
        "",
        "## Results",
        "",
        "| Scenario | Switch cost | Method | Promote (95% Wilson CI) | Mean oracle net gain (95% t CI) | Harmful promotion |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in summary_frame.itertuples(index=False):
        report_lines.append(
            f"| {row.scenario} | {row.switching_cost:g} | {row.method} | {row.promotion_rate:.3f} [{row.promotion_rate_ci_low:.3f}, {row.promotion_rate_ci_high:.3f}] | {row.mean_oracle_postpromotion_net_gain:.3f} [{row.oracle_gain_ci_low:.3f}, {row.oracle_gain_ci_high:.3f}] | {row.harmful_promotion_rate:.3f} |"
        )
    report_lines.extend(
        [
            "",
            "These are controlled synthetic results. They do not estimate utility in performative settings, establish that one gate is generally preferable, or show that the cost grid was selected optimally.",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-promotion-robustness --seeds {config.seeds} --seed-offset {config.seed_offset} --n {config.n} --device {config.device} --output {output.as_posix()}`",
            "",
        ]
    )
    report_path = reports / "promotion_robustness_grid.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    manifest = {
        "experiment": "promotion_switching_cost_reversal_robustness_grid",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "environment": environment(),
        "scenarios": list(scenarios),
        "methods": methods,
        "information_protocol": [
            "candidate and schedules fixed before shadow monitoring",
            "all methods and switching costs use paired simulator streams",
            "benefit schedule is evaluator-only and never passed to gates",
            "promotion is scored on untouched future potential outcomes",
            "one-time switching charge is included in test gain and future net utility",
            "independent event noise; no action-dependent outcomes",
            "descriptive full-grid reporting; no split selected on evaluation outcomes",
        ],
        "artifacts": [
            "metrics/promotion_robustness_streams.parquet",
            "metrics/promotion_robustness_summary.parquet",
            "figures/promotion_robustness_grid.png",
            "reports/promotion_robustness_grid.md",
        ],
    }
    (reports / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/promotion_robustness_grid"))
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=23102026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--switching-costs", nargs="+", type=float, default=[0, 10, 30, 60])
    parser.add_argument("--discovery-fractions", nargs="+", type=float, default=[0.25, 0.5, 0.75])
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    args = parser.parse_args(argv)
    config = PromotionRobustnessConfig(
        n=args.n,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        switching_costs=tuple(args.switching_costs),
        discovery_fractions=tuple(args.discovery_fractions),
        device=args.device,
    )
    print(run_promotion_robustness(config, args.output), flush=True)


if __name__ == "__main__":
    main()
