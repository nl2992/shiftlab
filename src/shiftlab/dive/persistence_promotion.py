"""Grid a two-phase intersection-union gate for persistent candidate gains."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..data.gpu.environment import environment
from .experiment import finalize_manifest
from .promotion_grid import _time_splits
from .promotion_timing import (
    PromotionTimingConfig,
    _benefit_schedule,
    _evaluate_scenario,
    _generate_costs,
    _summarize,
    _vectorized_crossing_times,
)


@dataclass(frozen=True)
class PersistencePromotionConfig:
    n: int = 3200
    seeds: int = 1000
    seed_offset: int = 20401023
    alpha: float = 0.05
    switching_cost: float = 0.05
    discovery_fractions: tuple[float, ...] = (0.25, 0.5, 0.75)
    device: str = "cuda"

    def validate(self) -> PersistencePromotionConfig:
        if self.n < 1000 or self.seeds < 1:
            raise ValueError("n must be >=1000 and seeds must be positive")
        if not np.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        if not np.isfinite(self.switching_cost) or self.switching_cost < 0:
            raise ValueError("switching_cost must be finite and nonnegative")
        if not self.discovery_fractions:
            raise ValueError("discovery_fractions must be nonempty")
        if tuple(sorted(set(self.discovery_fractions))) != self.discovery_fractions:
            raise ValueError("discovery_fractions must be strictly increasing")
        if any(not np.isfinite(x) or not 0 < x < 1 for x in self.discovery_fractions):
            raise ValueError("discovery_fractions must lie strictly between zero and one")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")
        return self


def _two_phase_decisions(
    gains: np.ndarray, *, discovery_length: int, bound: float, alpha: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cross one e-process in each disjoint, fixed phase; promote only on both."""
    values = np.asarray(gains, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("gains must be a finite seed-by-time matrix")
    if not 0 < discovery_length < values.shape[1]:
        raise ValueError("discovery_length must split gains into two nonempty phases")
    discovery = _vectorized_crossing_times(
        values[:, :discovery_length],
        bound=bound,
        alpha=alpha,
        starts=(0,),
    )
    persistence = _vectorized_crossing_times(
        values[:, discovery_length:],
        bound=bound,
        alpha=alpha,
        starts=(0,),
    )
    return discovery, persistence, (discovery >= 0) & (persistence >= 0)


def _persistence_rows(
    scenario: str,
    *,
    config: PersistencePromotionConfig,
    scenario_index: int,
) -> list[dict[str, Any]]:
    train_end, validation_end, monitor_end = _time_splits(config.n)
    monitor_start = validation_end
    monitor_length = monitor_end - monitor_start
    deployment_start = monitor_end
    benefit = _benefit_schedule(scenario, config.n, monitor_start, monitor_end)
    incumbent, candidate = _generate_costs(
        benefit,
        seeds=config.seeds,
        seed=config.seed_offset + scenario_index * 100_003,
        device=config.device,
    )
    per_event_switch_cost = config.switching_cost / (config.n - deployment_start)
    gains = (
        incumbent[:, monitor_start:monitor_end].astype(float)
        - candidate[:, monitor_start:monitor_end].astype(float)
        - per_event_switch_cost
    )
    bound = 1 + per_event_switch_cost
    output: list[dict[str, Any]] = []
    for fraction in config.discovery_fractions:
        discovery_length = round(fraction * monitor_length)
        if not 1 <= discovery_length < monitor_length:
            raise ValueError("grid fraction leaves an empty discovery or persistence window")
        persistence_length = monitor_length - discovery_length
        discovery_crossings, persistence_crossings, promoted = _two_phase_decisions(
            gains,
            discovery_length=discovery_length,
            bound=bound,
            alpha=config.alpha,
        )
        method = f"persistence_intersection_d={fraction:g}"
        for seed_index in range(config.seeds):
            if promoted[seed_index]:
                promote_relative = discovery_length + int(persistence_crossings[seed_index])
                promote_event = monitor_start + promote_relative
                evaluation_start = promote_event + 1
                oracle_net = float(benefit[evaluation_start:].sum() - config.switching_cost)
                realized_net = float(
                    incumbent[seed_index, evaluation_start:].astype(float).sum()
                    - candidate[seed_index, evaluation_start:].astype(float).sum()
                    - config.switching_cost
                )
            else:
                promote_relative = -1
                promote_event = -1
                evaluation_start = config.n
                oracle_net = 0.0
                realized_net = 0.0
            output.append(
                {
                    "scenario": scenario,
                    "seed": config.seed_offset + scenario_index * 100_003 + seed_index,
                    "method": method,
                    "promoted": bool(promoted[seed_index]),
                    "discovery_fraction": fraction,
                    "discovery_window_length": discovery_length,
                    "persistence_window_length": persistence_length,
                    "discovery_certificate_time": (
                        int(discovery_crossings[seed_index])
                        if discovery_crossings[seed_index] >= 0
                        else None
                    ),
                    "persistence_certificate_time": (
                        int(persistence_crossings[seed_index])
                        if persistence_crossings[seed_index] >= 0
                        else None
                    ),
                    "certificate_time_in_shadow": promote_relative
                    if promoted[seed_index]
                    else None,
                    "right_censored_at": (monitor_length if not promoted[seed_index] else None),
                    "promotion_event_index": promote_event if promoted[seed_index] else None,
                    "evaluation_start_index": evaluation_start,
                    "training_end_index": train_end,
                    "validation_end_index": validation_end,
                    "shadow_start_index": monitor_start,
                    "shadow_end_index": monitor_end,
                    "deployment_start_index": deployment_start,
                    "deployment_end_index": config.n,
                    "oracle_postpromotion_net_gain": oracle_net,
                    "realized_postpromotion_net_gain": realized_net,
                    "harmful_postpromotion_promotion": bool(
                        promoted[seed_index] and oracle_net <= 0
                    ),
                    "switching_cost": config.switching_cost if promoted[seed_index] else 0.0,
                    "monitor_expected_gain_per_event": float(
                        benefit[monitor_start:monitor_end].mean()
                    ),
                    "oracle_benefit_schedule_id": scenario,
                    "alpha_each_phase": config.alpha,
                    "promotion_null": "discovery phase nonpositive OR confirmation phase nonpositive",
                }
            )
    return output


def _plot(summary: pd.DataFrame, path: Path) -> None:
    scenarios = list(summary.scenario.drop_duplicates())
    fractions = [0.25, 0.5, 0.75]
    method_labels = {
        f"persistence_intersection_d={fraction:g}": f"Two-phase, discovery {fraction:.0%}"
        for fraction in fractions
    }
    baseline_methods = [
        "sequential_full_start",
        "sequential_multi_start_3",
        "empirical_bernstein_fixed_horizon",
        "hoeffding_fixed_horizon",
        "never_promote",
    ]
    method_labels.update(
        {
            "sequential_full_start": "Sequential, full start",
            "sequential_multi_start_3": "Sequential, three starts",
            "empirical_bernstein_fixed_horizon": "Empirical-Bernstein",
            "hoeffding_fixed_horizon": "Hoeffding",
            "never_promote": "Never",
        }
    )
    methods = baseline_methods + [
        f"persistence_intersection_d={fraction:g}" for fraction in fractions
    ]
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), sharex=True)
    x = np.arange(len(scenarios))
    width = 0.82 / len(methods)
    for index, method in enumerate(methods):
        rows = summary[summary.method.eq(method)].set_index("scenario").reindex(scenarios)
        offset = (index - (len(methods) - 1) / 2) * width
        axes[0].bar(
            x + offset,
            rows.promotion_rate,
            width,
            yerr=np.vstack(
                [
                    np.maximum(0.0, rows.promotion_rate - rows.promotion_rate_ci_low),
                    np.maximum(0.0, rows.promotion_rate_ci_high - rows.promotion_rate),
                ]
            ),
            capsize=2,
            label=method_labels[method],
        )
        axes[1].bar(
            x + offset,
            rows.mean_oracle_postpromotion_net_gain,
            width,
            yerr=np.vstack(
                [
                    np.maximum(
                        0.0,
                        rows.mean_oracle_postpromotion_net_gain - rows.oracle_gain_ci_low,
                    ),
                    np.maximum(
                        0.0,
                        rows.oracle_gain_ci_high - rows.mean_oracle_postpromotion_net_gain,
                    ),
                ]
            ),
            capsize=2,
        )
    axes[0].set_ylabel("Promotion rate")
    axes[1].set_ylabel("Mean oracle future net gain")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[0].legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.25))
    for axis in axes:
        axis.grid(axis="y", alpha=0.25)
    axes[1].set_xticks(x, scenarios, rotation=20, ha="right")
    fig.suptitle("Persistence-certified promotion: discovery-window grid")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def run_persistence_grid(config: PersistencePromotionConfig, output: Path) -> Path:
    config.validate()
    if config.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available")
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metrics_dir / "persistence_promotion_streams.parquet"
    summary_path = metrics_dir / "persistence_promotion_summary.parquet"
    if detail_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite persistence grid: {output}")
    scenarios = (
        "no_benefit",
        "early_transient",
        "benefit_reversal",
        "persistent_benefit",
        "late_persistent",
    )
    baseline_config = PromotionTimingConfig(
        n=config.n,
        seeds=config.seeds,
        seed_offset=config.seed_offset,
        alpha=config.alpha,
        switching_cost=config.switching_cost,
        device=config.device,
    )
    rows: list[dict[str, Any]] = []
    for scenario_index, scenario in enumerate(scenarios):
        print(
            f"persistence-grid scenario={scenario} seeds={config.seeds} device={config.device}",
            flush=True,
        )
        baseline = _evaluate_scenario(
            scenario,
            config=baseline_config,
            scenario_index=scenario_index,
        )
        for row in baseline:
            row["discovery_fraction"] = None
            row["discovery_window_length"] = None
            row["persistence_window_length"] = None
            row["promotion_null"] = None
        rows.extend(baseline)
        rows.extend(
            _persistence_rows(
                scenario,
                config=config,
                scenario_index=scenario_index,
            )
        )
    detail = pd.DataFrame(rows)
    summary = _summarize(detail)
    detail.to_parquet(detail_path, index=False)
    summary.to_parquet(summary_path, index=False)
    figure_path = output / "figures/persistence_promotion_grid.png"
    _plot(summary, figure_path)
    lines = [
        "# Persistence-certified promotion grid",
        "",
        f"This benchmark compares the existing sequential full-start, three-start, empirical-Bernstein and Hoeffding gates with a two-phase intersection-union gate across {len(scenarios)} fixed benefit schedules and {config.seeds} independent CUDA-generated streams per schedule. The frozen candidate is evaluated on the same paired outcomes for every method. The three discovery windows use {config.discovery_fractions} of the fixed shadow horizon; the remaining shadow events form the disjoint persistence window. Promotion may occur only after both windows' separate bounded-mean e-processes have crossed their thresholds.",
        "",
        f"Each phase process uses level alpha={config.alpha:g}. The promotion null is a union: the candidate has nonpositive eventwise conditional expected net gain throughout the discovery phase, OR throughout the confirmation phase. The alternative requires evidence against both phase nulls. This is an intersection-union test: under either part of the union null, the probability of promoting is bounded by the corresponding phase e-process's alpha level. No Bonferroni split is needed for the conjunctive decision. The argument requires a candidate frozen before both phases, predictable phase boundaries, bounded increments, and the stated conditional-mean null within whichever phase is null. It is a standard construction, not a novelty claim.",
        "",
        "The discovery cut is fixed before any monitor costs are observed. The confirmation process starts at that fixed boundary, not at the discovery crossing, so early positive samples cannot be reused as persistence evidence. A promotion begins on the event after the confirmation crossing. The final stream tail is untouched by testing and is scored with evaluator-only potential costs. This synthetic setup assumes no action-dependent outcomes and independent event noise; the e-process validity argument itself only needs its conditional supermartingale assumptions.",
        "",
        "## Performance grid",
        "",
        "Promotion rates and mean oracle post-promotion net gains use independent seeds as experimental units. The paired stream-level Parquet preserves baseline comparisons and every discovery fraction.",
        "",
        "| Scenario | Rule | Promotion rate (95% CI) | Mean oracle future net gain (95% CI) | Harmful promotion rate | Mean promotion event |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        time = (
            f"{row.mean_certificate_time_if_promoted:.1f}"
            if np.isfinite(row.mean_certificate_time_if_promoted)
            else "—"
        )
        lines.append(
            f"| {row.scenario} | {row.method} | {row.promotion_rate:.3f} [{row.promotion_rate_ci_low:.3f}, {row.promotion_rate_ci_high:.3f}] | {row.mean_oracle_postpromotion_net_gain:.3f} [{row.oracle_gain_ci_low:.3f}, {row.oracle_gain_ci_high:.3f}] | {row.harmful_promotion_rate:.3f} | {time} |"
        )
    lines.extend(
        [
            "",
            "The conclusion must be based on the complete scenario grid and confidence intervals, not the best-performing split. A persistence window can suppress a harmful reversal by withholding promotion after discovery-only benefit, but it also delays or misses benefit that begins late. No split is selected on these evaluation outcomes; any data-driven split choice needs a separate pilot/validation stream and a fresh test stream.",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-persistence-grid --seeds {config.seeds} --seed-offset {config.seed_offset} --n {config.n} --device {config.device} --output {output.as_posix()}`",
        ]
    )
    report_path = reports_dir / "persistence_promotion_grid.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "two_phase_persistence_certification_grid",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "environment": environment(),
        "scenarios": list(scenarios),
        "methods": list(detail.method.drop_duplicates()),
        "information_protocol": [
            "the single candidate is frozen before monitor outcomes",
            "the discovery fraction is fixed before any monitor outcomes",
            "the persistence phase is disjoint and starts at the fixed discovery boundary",
            "each phase tests the same bounded eventwise mean null at alpha",
            "conjunctive promotion tests a union null by an intersection-union rule; no alpha split is required",
            "promotion begins after both phase processes have crossed",
            "the final stream tail is not used for testing and is evaluator-only scoring",
            "the simulator has independent event noise and no action-dependent outcomes",
        ],
        "artifacts": [
            "metrics/persistence_promotion_streams.parquet",
            "metrics/persistence_promotion_summary.parquet",
            "figures/persistence_promotion_grid.png",
            "reports/persistence_promotion_grid.md",
        ],
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/persistence_promotion_grid"))
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20401023)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--switching-cost", type=float, default=0.05)
    parser.add_argument("--discovery-fractions", nargs="+", type=float, default=[0.25, 0.5, 0.75])
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    args = parser.parse_args(argv)
    config = PersistencePromotionConfig(
        n=args.n,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        switching_cost=args.switching_cost,
        discovery_fractions=tuple(args.discovery_fractions),
        device=args.device,
    )
    print(run_persistence_grid(config, args.output), flush=True)


if __name__ == "__main__":
    main()
