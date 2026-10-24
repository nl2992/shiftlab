"""Fresh null calibration and paired confirmation for a frozen start-time prior."""

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
import torch
from scipy.special import gammaln
from scipy.stats import beta

from ..data.gpu.environment import environment
from .delayed_benchmark import DelayedBenchmarkConfig, _generate_stream
from .delayed_calibration import (
    NULL_SCENARIOS,
    DelayedCalibrationConfig,
    _first_crossing,
    _generate_null_stream,
    _restart_log_e_values,
    calibration_alarm_indices,
)
from .start_prior_sweep import PRIOR_SHAPES, beta_start_weights

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60)
HARM_INCREASES = (0.12, 0.24)
UNIFORM = beta_start_weights(*PRIOR_SHAPES["uniform_beta_1_1"])
CENTER = beta_start_weights(*PRIOR_SHAPES["center_beta_2_2"])


@dataclass(frozen=True)
class StartPriorValidationConfig:
    null_streams: int = 2000
    alternative_seeds_per_cell: int = 2000
    null_seed_offset: int = 20274000
    alternative_seed_offset: int = 20276000
    n_events: int = 3000
    query_rates: tuple[float, ...] = QUERY_RATES
    harm_onsets: tuple[float, ...] = ONSETS
    harm_increases: tuple[float, ...] = HARM_INCREASES
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    delay_scheme: str = "uniform_0_6"
    device: str = "cuda"

    def validate(self) -> StartPriorValidationConfig:
        if min(self.null_streams, self.alternative_seeds_per_cell) < 1:
            raise ValueError("both seed counts must be positive")
        if self.n_events < 100 or not self.query_rates:
            raise ValueError("n_events must be at least 100 and query_rates nonempty")
        if any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query rates must lie in (0, 1]")
        if any(not 0 < onset < 1 for onset in self.harm_onsets):
            raise ValueError("harm onset fractions must lie in (0, 1)")
        if any(not 0 < effect <= 0.98 * self.amplitude for effect in self.harm_increases):
            raise ValueError("harm increases must produce valid sign probabilities")
        if self.delay_scheme not in {"fixed_3", "uniform_0_6"}:
            raise ValueError("unsupported delay scheme")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        null_end = self.null_seed_offset + self.null_streams
        alt_end = self.alternative_seed_offset + self.alternative_seeds_per_cell
        if max(self.null_seed_offset, self.alternative_seed_offset) < min(null_end, alt_end):
            raise ValueError("null and alternative seed blocks must be disjoint")
        return self


def _holm_log_p(log_ps: list[float]) -> list[float]:
    order = np.argsort(log_ps)
    adjusted_sorted = np.maximum.accumulate(
        [log_ps[index] + math.log(len(log_ps) - rank) for rank, index in enumerate(order)]
    )
    result = np.empty(len(log_ps), dtype=float)
    result[order] = np.minimum(0.0, adjusted_sorted)
    return result.tolist()


def _mcnemar_log_p(candidate_only: int, uniform_only: int) -> float:
    discordant = candidate_only + uniform_only
    tail = min(candidate_only, uniform_only)
    if discordant == 0 or 2 * tail >= discordant:
        return 0.0
    support = np.arange(tail + 1, dtype=float)
    log_terms = (
        gammaln(discordant + 1)
        - gammaln(support + 1)
        - gammaln(discordant - support + 1)
        - discordant * math.log(2)
    )
    return min(0.0, math.log(2) + float(np.logaddexp.reduce(log_terms)))


def _format_log_p(log_p: float) -> str:
    log10 = log_p / math.log(10)
    return f"<1e-300 (log10={log10:.1f})" if log10 < -300 else f"{math.exp(log_p):.4g}"


def run_start_prior_validation(
    output_dir: str | Path, config: StartPriorValidationConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Calibrate both frozen priors and compare them on fresh paired alternatives."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    null_rows: list[dict[str, object]] = []
    alternative_rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()
    for scenario in NULL_SCENARIOS:
        for seed in range(config.null_seed_offset, config.null_seed_offset + config.null_streams):
            null_config = DelayedCalibrationConfig(
                streams_per_cell=config.null_streams,
                seed_offset=config.null_seed_offset,
                n_events=config.n_events,
                query_rates=config.query_rates,
                alpha=config.alpha,
                margin=config.margin,
                amplitude=config.amplitude,
                benign_amplitude=config.benign_amplitude,
                delay_scheme=config.delay_scheme,
                device=config.device,
            )
            device = torch.device(
                "cuda"
                if config.device == "auto" and torch.cuda.is_available()
                else "cpu"
                if config.device == "auto"
                else config.device
            )
            contrasts, query_uniforms, delays = _generate_null_stream(
                null_config, seed=seed, scenario=scenario, device=device
            )
            resolved_devices.add(str(device))
            for query_rate in config.query_rates:
                events = np.flatnonzero(query_uniforms < query_rate)
                values = contrasts[events]
                for method, weights in (
                    ("uniform_restart_8", UNIFORM),
                    ("center_restart_beta22", CENTER),
                ):
                    alarms = calibration_alarm_indices(
                        values,
                        events,
                        events + delays[events],
                        query_rate=query_rate,
                        n_events=config.n_events,
                        margin=config.margin,
                        alpha=config.alpha,
                        amplitude=config.amplitude,
                        restart_weights=weights,
                    )
                    alarm_event = alarms["restart_mixture_8"][0]
                    null_rows.append(
                        {
                            "scenario": scenario,
                            "query_rate": query_rate,
                            "seed": seed,
                            "method": method,
                            "false_escalation": alarm_event is not None,
                            "alarm_event": alarm_event,
                        }
                    )

    cells = list(itertools.product(config.query_rates, config.harm_onsets, config.harm_increases))
    for query_rate, onset_fraction, harm_increase in cells:
        benchmark_config = DelayedBenchmarkConfig(
            seeds=config.alternative_seeds_per_cell,
            seed_offset=config.alternative_seed_offset,
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
        for seed in range(
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.alternative_seeds_per_cell,
        ):
            _source, contrast, queried, delays, onset, resolved_device = _generate_stream(
                benchmark_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved_device)
            events = np.flatnonzero(queried)
            values = contrast[events]
            alarms = calibration_alarm_indices(
                values,
                events,
                events + delays[events],
                query_rate=query_rate,
                n_events=config.n_events,
                margin=config.margin,
                alpha=config.alpha,
                amplitude=config.amplitude,
                restart_weights=UNIFORM,
            )
            uniform_alarm = alarms["restart_mixture_8"][0]
            horizon = max(1, round(query_rate * config.n_events))
            starts = tuple(sorted({round(horizon * i / 8) for i in range(8)}))
            centered = values - config.margin
            candidate_log_e = _restart_log_e_values(
                centered,
                bound=config.amplitude + config.margin + 1e-6,
                starts=starts,
                start_weights=CENTER,
            )
            crossing = _first_crossing(candidate_log_e, math.log(1 / config.alpha))
            center_alarm = int(events[crossing]) if crossing is not None else None
            for method, alarm_event in (
                ("uniform_restart_8", uniform_alarm),
                ("center_restart_beta22", center_alarm),
            ):
                detected = alarm_event is not None and alarm_event >= onset
                processed = (
                    int(np.searchsorted(events, alarm_event, side="right"))
                    if alarm_event is not None
                    else len(events)
                )
                wall = (
                    int(np.maximum.accumulate(events + delays[events])[processed - 1])
                    if alarm_event is not None
                    else None
                )
                alternative_rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset_fraction,
                        "harm_contrast_increase": harm_increase,
                        "method": method,
                        "device": resolved_device,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": wall,
                        "detected": bool(detected),
                        "false_escalation_before_onset": bool(
                            alarm_event is not None and alarm_event < onset
                        ),
                        "event_detection_delay": alarm_event - onset if detected else None,
                        "wall_detection_delay": wall - onset if detected else None,
                        "labels_queried": len(events),
                    }
                )

    null_frame = pd.DataFrame(null_rows)
    alt_frame = pd.DataFrame(alternative_rows)
    null_summaries = []
    n_null_cells = len(NULL_SCENARIOS) * len(config.query_rates)
    for (scenario, query_rate, method), group in null_frame.groupby(
        ["scenario", "query_rate", "method"], sort=True
    ):
        false_count, trials = int(group.false_escalation.sum()), len(group)
        # One-sided exact bounds with Bonferroni control over both methods and all null cells.
        upper = (
            1.0
            if false_count == trials
            else float(
                beta.ppf(1 - 0.05 / (2 * n_null_cells), false_count + 1, trials - false_count)
            )
        )
        null_summaries.append(
            {
                "scenario": scenario,
                "query_rate": query_rate,
                "method": method,
                "false_escalations": false_count,
                "streams": trials,
                "false_escalation_rate": false_count / trials,
                "simultaneous_cp95_upper": upper,
            }
        )
    null_summary = pd.DataFrame(null_summaries)

    cell_rows = []
    log_ps = []
    for cell, group in alt_frame.groupby(
        ["query_rate", "harm_onset_fraction", "harm_contrast_increase"], sort=True
    ):
        wide = group.pivot(index="seed", columns="method", values="detected")
        center = int(wide.center_restart_beta22.sum())
        uniform = int(wide.uniform_restart_8.sum())
        candidate_only = int((wide.center_restart_beta22 & ~wide.uniform_restart_8).sum())
        uniform_only = int((~wide.center_restart_beta22 & wide.uniform_restart_8).sum())
        log_p = _mcnemar_log_p(candidate_only, uniform_only)
        log_ps.append(log_p)
        cell_rows.append(
            {
                "query_rate": cell[0],
                "harm_onset_fraction": cell[1],
                "harm_contrast_increase": cell[2],
                "center_detected": center,
                "uniform_detected": uniform,
                "streams": len(wide),
                "center_rate": center / len(wide),
                "uniform_rate": uniform / len(wide),
                "rate_difference": (center - uniform) / len(wide),
                "center_only": candidate_only,
                "uniform_only": uniform_only,
                "mcnemar_p": _format_log_p(log_p),
            }
        )
    cell_summary = pd.DataFrame(cell_rows)
    adjusted = _holm_log_p(log_ps)
    cell_summary["holm_adjusted_p"] = [_format_log_p(value) for value in adjusted]
    ranking = (
        alt_frame.groupby("method", sort=True)
        .agg(
            macro_cell_detection=("detected", "mean"),
            false_pre_onset=("false_escalation_before_onset", "sum"),
            detected=("detected", "sum"),
        )
        .reset_index()
    )

    null_path = output / "null_metrics.parquet"
    alt_path = output / "alternative_metrics.parquet"
    null_frame.to_parquet(null_path, index=False)
    alt_frame.to_parquet(alt_path, index=False)
    null_frame.to_csv(output / "null_metrics.csv", index=False)
    alt_frame.to_csv(output / "alternative_metrics.csv", index=False)
    null_summary.to_csv(output / "null_calibration_summary.csv", index=False)
    cell_summary.to_csv(output / "alternative_cell_summary.csv", index=False)
    ranking.to_csv(output / "overall_summary.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "selected_candidate_frozen_before_validation": "center_beta_2_2",
        "candidate_weights": list(CENTER),
        "reference_weights": list(UNIFORM),
        "null_seed_interval": [
            config.null_seed_offset,
            config.null_seed_offset + config.null_streams - 1,
        ],
        "alternative_seed_interval_per_cell": [
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.alternative_seeds_per_cell - 1,
        ],
        "factorial_cells": len(cells),
        "null_metric_rows": len(null_frame),
        "alternative_metric_rows": len(alt_frame),
        "resolved_devices": sorted(resolved_devices),
        "environment": environment(),
        "null_metrics_sha256": hashlib.sha256(null_path.read_bytes()).hexdigest(),
        "alternative_metrics_sha256": hashlib.sha256(alt_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "start_prior_validation.py",
                "start_prior_sweep.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference": "Fresh per-cell paired exact two-sided McNemar tests compare frozen center prior against uniform; Holm adjusts across 12 cells. Null upper bounds are one-sided exact Clopper-Pearson with Bonferroni simultaneous 95% coverage across 12 scenario/query/method cells. This is conditional on registered synthetic assumptions.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Fresh validation of the frozen center start-time prior",
        "",
        "The center Beta(2,2) prior was chosen using the disjoint development block and frozen before these runs. It is compared with the uniform eight-start mixture on independent null and paired alternative seed blocks.",
        "",
        f"- Null seeds: {manifest['null_seed_interval'][0]}–{manifest['null_seed_interval'][1]} per scenario.",
        f"- Alternative seeds: {manifest['alternative_seed_interval_per_cell'][0]}–{manifest['alternative_seed_interval_per_cell'][1]} per cell.",
        f"- Generator device(s): {', '.join(sorted(resolved_devices))}.",
        "- Alternative inference: exact paired two-sided McNemar tests with Holm adjustment across 12 cells.",
        "- Null bounds: one-sided exact Clopper–Pearson, simultaneous 95% Bonferroni coverage over 12 cells.",
        "",
        "## Null calibration",
        "",
        null_summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "## Paired alternative confirmation",
        "",
        cell_summary.to_markdown(index=False),
        "",
        "This validates finite-sample behavior only for the registered synthetic generator, bounded contrasts, predictable label query masks and outcome-independent delays. It does not cover serial dependence, informative query/delay mechanisms, or deployment-induced outcomes. A non-significant or mixed comparison retains the uniform mixture. No figure is generated; future visuals must use PaperBanana.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return alt_frame, cell_summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/start_prior_validation")
    parser.add_argument("--null-streams", type=int, default=2000)
    parser.add_argument("--alternative-seeds-per-cell", type=int, default=2000)
    parser.add_argument("--null-seed-offset", type=int, default=20274000)
    parser.add_argument("--alternative-seed-offset", type=int, default=20276000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = StartPriorValidationConfig(
        null_streams=args.null_streams,
        alternative_seeds_per_cell=args.alternative_seeds_per_cell,
        null_seed_offset=args.null_seed_offset,
        alternative_seed_offset=args.alternative_seed_offset,
        device=args.device,
    )
    _frame, summary, manifest = run_start_prior_validation(args.output_dir, config)
    print(summary.to_string(index=False))
    print(f"alternative_metrics_sha256={manifest['alternative_metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
