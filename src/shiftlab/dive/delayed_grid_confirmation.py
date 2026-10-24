"""Multiplicity-adjusted factorial confirmation for delayed harm monitoring."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaln, logsumexp

from ..data.gpu.environment import environment
from .delayed_benchmark import DelayedBenchmarkConfig, _generate_stream
from .delayed_calibration import CALIBRATION_METHODS, _exact_interval, calibration_alarm_indices

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60)
HARM_INCREASES = (0.12, 0.24)


@dataclass(frozen=True)
class DelayedGridConfirmationConfig:
    """Frozen alternative factorial with common seeds and paired monitors."""

    seeds_per_cell: int = 2000
    seed_offset: int = 20270000
    n_events: int = 3000
    query_rates: tuple[float, ...] = QUERY_RATES
    harm_onsets: tuple[float, ...] = ONSETS
    harm_increases: tuple[float, ...] = HARM_INCREASES
    delay_scheme: str = "uniform_0_6"
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    device: str = "cuda"

    def validate(self) -> DelayedGridConfirmationConfig:
        if self.seeds_per_cell < 1 or self.n_events < 100:
            raise ValueError("seeds_per_cell must be positive and n_events at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query_rates must be nonempty and in (0, 1]")
        if not self.harm_onsets or any(not 0 < x < 1 for x in self.harm_onsets):
            raise ValueError("harm_onsets must be nonempty and in (0, 1)")
        if not self.harm_increases or any(
            not 0 < x <= 0.98 * self.amplitude for x in self.harm_increases
        ):
            raise ValueError("harm_increases must be positive and yield sign probabilities <= 0.99")
        if len(set(self.query_rates)) != len(self.query_rates):
            raise ValueError("query_rates must be unique")
        if self.delay_scheme not in {"fixed_3", "uniform_0_6"}:
            raise ValueError("delay_scheme must be fixed_3 or uniform_0_6")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu or cuda")
        return self


def holm_adjust(p_values: list[float]) -> list[float]:
    """Return Holm adjusted p-values in original order."""
    if any(not np.isfinite(p) or not 0 <= p <= 1 for p in p_values):
        raise ValueError("p-values must be finite and in [0, 1]")
    order = np.argsort(p_values)
    adjusted_sorted = np.maximum.accumulate(
        [(len(p_values) - rank) * p_values[index] for rank, index in enumerate(order)]
    )
    adjusted = np.empty(len(p_values), dtype=float)
    adjusted[order] = np.minimum(1.0, adjusted_sorted)
    return adjusted.tolist()


def exact_mcnemar_log_p(restart_only: int, betting_only: int) -> float:
    """Compute the exact two-sided McNemar p-value on the log scale."""
    if restart_only < 0 or betting_only < 0:
        raise ValueError("discordant-pair counts must be nonnegative")
    discordant = restart_only + betting_only
    if discordant == 0:
        return 0.0
    tail_count = min(restart_only, betting_only)
    if 2 * tail_count >= discordant:
        return 0.0
    support = np.arange(tail_count + 1, dtype=float)
    log_probabilities = (
        gammaln(discordant + 1)
        - gammaln(support + 1)
        - gammaln(discordant - support + 1)
        - discordant * math.log(2)
    )
    return min(0.0, math.log(2) + float(logsumexp(log_probabilities)))


def holm_adjust_log_p(log_p_values: list[float]) -> list[float]:
    """Holm adjustment that retains very small p-values below float underflow."""
    if any(not np.isfinite(p) or p > 0 for p in log_p_values):
        raise ValueError("log p-values must be finite and nonpositive")
    order = np.argsort(log_p_values)
    adjusted_sorted = np.maximum.accumulate(
        [
            log_p_values[index] + math.log(len(log_p_values) - rank)
            for rank, index in enumerate(order)
        ]
    )
    adjusted = np.empty(len(log_p_values), dtype=float)
    adjusted[order] = np.minimum(0.0, adjusted_sorted)
    return adjusted.tolist()


def _display_p(log_p_value: float) -> str:
    log10_p = log_p_value / math.log(10)
    if log10_p < -300:
        return f"<1e-300 (log10={log10_p:.1f})"
    return f"{math.exp(log_p_value):.4g}"


def run_grid_confirmation(
    output_dir: str | Path, config: DelayedGridConfirmationConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Evaluate the fixed 12-cell alternative grid with paired exact comparisons."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()
    cells = list(itertools.product(config.query_rates, config.harm_onsets, config.harm_increases))
    for query_rate, onset_fraction, harm_increase in cells:
        benchmark_config = DelayedBenchmarkConfig(
            seeds=config.seeds_per_cell,
            seed_offset=config.seed_offset,
            n_source=3000,
            n_target=config.n_events,
            query_rate=query_rate,
            alpha=config.alpha,
            materiality_margin=config.margin,
            harm_onset_fraction=onset_fraction,
            harm_contrast_increase=harm_increase,
            amplitude=config.amplitude,
            delay_schemes=(config.delay_scheme,),
            scenarios=("boundary_harm",),
            device=config.device,
        ).validate()
        for seed in range(config.seed_offset, config.seed_offset + config.seeds_per_cell):
            _source, contrast, queried, delays, onset, resolved_device = _generate_stream(
                benchmark_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved_device)
            event_indices = np.flatnonzero(queried)
            alarms = calibration_alarm_indices(
                contrast[event_indices],
                event_indices,
                event_indices + delays[event_indices],
                query_rate=query_rate,
                n_events=config.n_events,
                margin=config.margin,
                alpha=config.alpha,
                amplitude=config.amplitude,
            )
            for method, (alarm_event, alarm_wall) in alarms.items():
                detected = alarm_event is not None and alarm_event >= onset
                rows.append(
                    {
                        "seed": seed,
                        "scenario": "boundary_harm",
                        "delay_scheme": config.delay_scheme,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset_fraction,
                        "harm_contrast_increase": harm_increase,
                        "method": method,
                        "device": resolved_device,
                        "n_events": config.n_events,
                        "labels_queried": len(event_indices),
                        "labels_processed_at_alarm_or_end": (
                            int(event_indices.searchsorted(alarm_event, side="right"))
                            if alarm_event is not None
                            else len(event_indices)
                        ),
                        "harm_onset_event": onset,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": alarm_wall,
                        "event_detection_delay": alarm_event - onset if detected else None,
                        "wall_detection_delay": alarm_wall - onset if detected else None,
                        "detected": detected,
                        "false_escalation": alarm_event is not None and alarm_event < onset,
                        "mean_realized_feedback_delay": float(delays[event_indices].mean()),
                        "materiality_margin": config.margin,
                        "alpha": config.alpha,
                    }
                )

    frame = pd.DataFrame(rows)
    group_cols = ["query_rate", "harm_onset_fraction", "harm_contrast_increase"]
    summary_rows = []
    paired_rows = []
    for cell_key, cell_frame in frame.groupby(group_cols, sort=True):
        cell_values = dict(zip(group_cols, cell_key, strict=True))
        wide = cell_frame.pivot(index="seed", columns="method", values="detected")
        for method in CALIBRATION_METHODS:
            successes = int(wide[method].sum())
            lower, upper = _exact_interval(successes, len(wide))
            method_frame = cell_frame[cell_frame.method == method]
            detected_frame = method_frame[method_frame.detected]
            summary_rows.append(
                {
                    **cell_values,
                    "method": method,
                    "detected": successes,
                    "streams": len(wide),
                    "detection_rate": successes / len(wide),
                    "cp95_lower": lower,
                    "cp95_upper": upper,
                    "mean_event_delay_given_detection": float(
                        detected_frame.event_detection_delay.mean()
                    ),
                    "mean_wall_delay_given_detection": float(
                        detected_frame.wall_detection_delay.mean()
                    ),
                }
            )
        restart_only = int((wide.restart_mixture_8 & ~wide.paired_cost_betting).sum())
        betting_only = int((~wide.restart_mixture_8 & wide.paired_cost_betting).sum())
        discordant = restart_only + betting_only
        log_p_value = exact_mcnemar_log_p(restart_only, betting_only)
        paired_rows.append(
            {
                **cell_values,
                "restart_only": restart_only,
                "betting_only": betting_only,
                "discordant_pairs": discordant,
                "mcnemar_exact_two_sided_p": _display_p(log_p_value),
                "mcnemar_log10_p": log_p_value / math.log(10),
            }
        )
    summary = pd.DataFrame(summary_rows)
    paired = pd.DataFrame(paired_rows)
    adjusted_log_p = holm_adjust_log_p([value * math.log(10) for value in paired.mcnemar_log10_p])
    paired["holm_adjusted_log10_p"] = np.asarray(adjusted_log_p) / math.log(10)
    paired["holm_adjusted_p"] = [_display_p(value) for value in adjusted_log_p]
    metrics_path = output / "grid_confirmation_metrics.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "grid_confirmation_metrics.csv", index=False)
    summary.to_csv(output / "grid_confirmation_summary.csv", index=False)
    paired.to_csv(output / "paired_tests.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "environment": environment(),
        "resolved_devices": sorted(resolved_devices),
        "seed_interval_per_cell": [
            config.seed_offset,
            config.seed_offset + config.seeds_per_cell - 1,
        ],
        "factorial_cells": len(cells),
        "streams_per_cell": config.seeds_per_cell,
        "metric_rows": len(frame),
        "primary_method_contrast": "restart_mixture_8 versus paired_cost_betting",
        "paired_test_family": "12 cellwise exact two-sided McNemar tests with Holm adjustment",
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "delayed_grid_confirmation.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference_scope": (
            "Alternative-only factorial confirmation. Paired seeds are reused across cells to reduce "
            "Monte Carlo noise; each cell retains its own independent-stream estimate. The 12 paired "
            "restart-versus-full-stream tests use Holm adjustment. Null calibration is in the separate "
            "registered null study."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = [
        "# Delayed decision-harm factorial confirmation",
        "",
        f"This alternative-only grid contains {len(cells)} cells and {config.seeds_per_cell} paired seeds per cell.",
        "It varies query rate, harm onset and expected paired-cost increase, with CUDA stream generation",
        "and independent uniform label delays from zero through six. Seeds are reused across cells as",
        "common random numbers; they are paired within cell across the three registered e-processes.",
        "",
        f"- Seed interval per cell: {config.seed_offset}–{config.seed_offset + config.seeds_per_cell - 1}.",
        f"- Resolved generation device: {', '.join(sorted(resolved_devices))}.",
        "- Primary cellwise contrast: restart mixture versus full-stream betting.",
        "- Cellwise paired p-values: exact two-sided McNemar; familywise adjustment: Holm across 12 cells.",
        "- Tiny p-values and Holm values are computed on the log scale to avoid numerical underflow.",
        "- Marginal detection intervals: exact two-sided 95% Clopper–Pearson, reported per cell.",
        "",
        "## Detection rates and censored-delay summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired restart-mixture contrasts",
        "",
        paired.to_markdown(index=False, floatfmt=".5g"),
        "",
        "This factorial confirmation supports comparisons only over the registered synthetic conditions.",
        "The e-process guarantees still require the stated eventwise conditional-mean null, bounded",
        "contrasts, predictable queries, and outcome-independent delays. Delay means are conditional on",
        "detection and nondetections remain censored. No new algorithm or universal superiority claim is",
        "made. No figure is included because project guidance requires PaperBanana for visuals and that",
        "tool is unavailable in this session.",
        "",
    ]
    (output / "results.md").write_text("\n".join(lines), encoding="utf-8")
    return frame, paired, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/delayed_feedback_grid_confirmation_2000")
    parser.add_argument("--seeds-per-cell", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=20270000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = DelayedGridConfirmationConfig(
        seeds_per_cell=args.seeds_per_cell,
        seed_offset=args.seed_offset,
        device=args.device,
    )
    _frame, paired, manifest = run_grid_confirmation(args.output_dir, config)
    print(paired.to_string(index=False))
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
