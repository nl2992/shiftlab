"""Fresh confirmation for the fixed nominal-horizon Beta(2,1) start prior."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

from ..data.gpu.environment import environment
from .delayed_benchmark import DelayedBenchmarkConfig, _generate_stream
from .delayed_calibration import (
    NULL_SCENARIOS,
    DelayedCalibrationConfig,
    _generate_null_stream,
    calibration_alarm_indices,
)
from .start_prior_sweep import beta_start_weights
from .start_prior_validation import _format_log_p, _holm_log_p, _mcnemar_log_p

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60, 0.80)
HARM_INCREASES = (0.12, 0.24)
CANDIDATE = "late_beta_2_1"
REFERENCE = "uniform_beta_1_1"
LATE_WEIGHTS = beta_start_weights(2.0, 1.0)
UNIFORM_WEIGHTS = beta_start_weights(1.0, 1.0)
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20261025


@dataclass(frozen=True)
class LatePriorConfirmationConfig:
    streams_per_cell: int = 2000
    null_streams: int = 2000
    alternative_seed_offset: int = 20286000
    null_seed_offset: int = 20288000
    n_events: int = 3000
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    delay_scheme: str = "uniform_0_6"
    device: str = "cuda"

    def validate(self) -> LatePriorConfirmationConfig:
        if min(self.streams_per_cell, self.null_streams) < 1 or self.n_events < 100:
            raise ValueError("stream counts must be positive and n_events at least 100")
        if not 0 < self.alpha < 1 or not 0 <= self.margin < 1:
            raise ValueError("alpha and margin are invalid")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if self.delay_scheme != "uniform_0_6":
            raise ValueError("the confirmation delay scheme is frozen at uniform_0_6")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        alt_end = self.alternative_seed_offset + self.streams_per_cell
        null_end = self.null_seed_offset + self.null_streams
        if max(self.alternative_seed_offset, self.null_seed_offset) < min(alt_end, null_end):
            raise ValueError("alternative and null seed blocks must be disjoint")
        return self


def _cluster_bootstrap(
    differences_by_seed: pd.Series,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float, float]:
    """Bootstrap the macro paired difference by independent seed cluster."""
    values = differences_by_seed.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    boot = np.empty(replicates, dtype=float)
    batch_size = 500
    for start in range(0, replicates, batch_size):
        size = min(batch_size, replicates - start)
        indices = rng.integers(0, len(values), size=(size, len(values)))
        boot[start : start + size] = values[indices].mean(axis=1)
    lower, upper = np.quantile(boot, [0.025, 0.975])
    return float(values.mean()), float(lower), float(upper)


def run_late_prior_confirmation(
    output_dir: str | Path, config: LatePriorConfirmationConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Calibrate and compare frozen late and uniform start-time mixtures."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    alternative_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()

    null_config = DelayedCalibrationConfig(
        streams_per_cell=config.null_streams,
        seed_offset=config.null_seed_offset,
        n_events=config.n_events,
        query_rates=QUERY_RATES,
        alpha=config.alpha,
        margin=config.margin,
        amplitude=config.amplitude,
        benign_amplitude=config.benign_amplitude,
        delay_scheme=config.delay_scheme,
        device=config.device,
    ).validate()
    null_device = torch.device(
        "cuda"
        if config.device == "auto" and torch.cuda.is_available()
        else "cpu"
        if config.device == "auto"
        else config.device
    )
    for scenario in NULL_SCENARIOS:
        for seed in range(config.null_seed_offset, config.null_seed_offset + config.null_streams):
            contrasts, query_uniforms, delays = _generate_null_stream(
                null_config, seed=seed, scenario=scenario, device=null_device
            )
            resolved_devices.add(str(null_device))
            for query_rate in QUERY_RATES:
                events = np.flatnonzero(query_uniforms < query_rate)
                values = contrasts[events]
                arrivals = events + delays[events]
                for method, weights in (
                    (CANDIDATE, LATE_WEIGHTS),
                    (REFERENCE, UNIFORM_WEIGHTS),
                ):
                    alarms = calibration_alarm_indices(
                        values,
                        events,
                        arrivals,
                        query_rate=query_rate,
                        n_events=config.n_events,
                        margin=config.margin,
                        alpha=config.alpha,
                        amplitude=config.amplitude,
                        restart_weights=weights,
                    )
                    alarm_event, alarm_wall = alarms["restart_mixture_8"]
                    null_rows.append(
                        {
                            "scenario": scenario,
                            "query_rate": query_rate,
                            "seed": seed,
                            "method": method,
                            "alarm_event": alarm_event,
                            "alarm_wall_time": alarm_wall,
                            "false_escalation": alarm_event is not None,
                        }
                    )

    alternative_cells = list(itertools.product(QUERY_RATES, ONSETS, HARM_INCREASES))
    for query_rate, onset, harm_increase in alternative_cells:
        stream_config = DelayedBenchmarkConfig(
            seeds=config.streams_per_cell,
            seed_offset=config.alternative_seed_offset,
            n_source=3000,
            n_target=config.n_events,
            query_rate=query_rate,
            alpha=config.alpha,
            materiality_margin=config.margin,
            harm_onset_fraction=onset,
            harm_contrast_increase=harm_increase,
            amplitude=config.amplitude,
            delay_schemes=(config.delay_scheme,),
            scenarios=("boundary_harm",),
            device=config.device,
        ).validate()
        for seed in range(
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.streams_per_cell,
        ):
            _source, contrasts, queried, delays, onset_event, resolved_device = _generate_stream(
                stream_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved_device)
            events = np.flatnonzero(queried)
            values = contrasts[events]
            arrivals = events + delays[events]
            for method, weights in (
                (CANDIDATE, LATE_WEIGHTS),
                (REFERENCE, UNIFORM_WEIGHTS),
            ):
                alarms = calibration_alarm_indices(
                    values,
                    events,
                    arrivals,
                    query_rate=query_rate,
                    n_events=config.n_events,
                    margin=config.margin,
                    alpha=config.alpha,
                    amplitude=config.amplitude,
                    restart_weights=weights,
                )
                alarm_event, alarm_wall = alarms["restart_mixture_8"]
                detected = alarm_event is not None and alarm_event >= onset_event
                processed = (
                    int(np.searchsorted(events, alarm_event, side="right"))
                    if alarm_event is not None
                    else len(events)
                )
                alternative_rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset,
                        "harm_increase": harm_increase,
                        "method": method,
                        "device": resolved_device,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": alarm_wall,
                        "detected": bool(detected),
                        "false_escalation_before_onset": bool(
                            alarm_event is not None and alarm_event < onset_event
                        ),
                        "event_detection_delay": alarm_event - onset_event if detected else None,
                        "wall_detection_delay": alarm_wall - onset_event if detected else None,
                        "labels_queried": len(events),
                        "labels_processed_at_alarm": processed,
                    }
                )

    alternative = pd.DataFrame(alternative_rows)
    null = pd.DataFrame(null_rows)
    cell_rows = []
    log_ps = []
    for keys, group in alternative.groupby(
        ["query_rate", "harm_onset_fraction", "harm_increase"], sort=True
    ):
        wide = group.pivot(index="seed", columns="method", values="detected")
        candidate_count = int(wide[CANDIDATE].sum())
        reference_count = int(wide[REFERENCE].sum())
        candidate_only = int((wide[CANDIDATE] & ~wide[REFERENCE]).sum())
        reference_only = int((~wide[CANDIDATE] & wide[REFERENCE]).sum())
        log_p = _mcnemar_log_p(candidate_only, reference_only)
        log_ps.append(log_p)
        for method, count in ((CANDIDATE, candidate_count), (REFERENCE, reference_count)):
            method_rows = group[group.method == method]
            lower = 0.0 if count == 0 else float(beta.ppf(0.025, count, len(wide) - count + 1))
            upper = (
                1.0 if count == len(wide) else float(beta.ppf(0.975, count + 1, len(wide) - count))
            )
            cell_rows.append(
                {
                    "query_rate": keys[0],
                    "harm_onset_fraction": keys[1],
                    "harm_increase": keys[2],
                    "method": method,
                    "detected": count,
                    "streams": len(wide),
                    "detection_rate": count / len(wide),
                    "cp95_lower": lower,
                    "cp95_upper": upper,
                    "pre_onset_escalations": int(method_rows.false_escalation_before_onset.sum()),
                    "mean_event_delay_given_detection": method_rows.event_detection_delay.mean(),
                    "mean_wall_delay_given_detection": method_rows.wall_detection_delay.mean(),
                    "candidate_only": candidate_only,
                    "reference_only": reference_only,
                    "mcnemar_p": _format_log_p(log_p),
                }
            )
    cell_summary = pd.DataFrame(cell_rows)
    adjusted = _holm_log_p(log_ps)
    cell_summary["holm_adjusted_p"] = np.repeat([_format_log_p(value) for value in adjusted], 2)

    paired = alternative[alternative.method == CANDIDATE].merge(
        alternative[alternative.method == REFERENCE],
        on=["seed", "query_rate", "harm_onset_fraction", "harm_increase"],
        suffixes=("_late", "_uniform"),
        validate="one_to_one",
    )
    seed_differences = (
        paired.assign(
            difference=paired.detected_late.astype(float) - paired.detected_uniform.astype(float)
        )
        .groupby("seed", sort=True)
        .difference.mean()
    )
    macro_difference, bootstrap_lower, bootstrap_upper = _cluster_bootstrap(seed_differences)
    overall = (
        alternative.groupby("method", sort=True)
        .agg(
            macro_cell_detection=("detected", "mean"),
            pre_onset_escalations=("false_escalation_before_onset", "sum"),
        )
        .reset_index()
    )
    false_family = len(NULL_SCENARIOS) * len(QUERY_RATES) * 2
    null_summary_rows = []
    for keys, group in null.groupby(["scenario", "query_rate", "method"], sort=True):
        count = int(group.false_escalation.sum())
        trials = len(group)
        upper = (
            1.0
            if count == trials
            else float(beta.ppf(1 - 0.05 / false_family, count + 1, trials - count))
        )
        null_summary_rows.append(
            {
                "scenario": keys[0],
                "query_rate": keys[1],
                "method": keys[2],
                "false_escalations": count,
                "streams": trials,
                "false_escalation_rate": count / trials,
                "simultaneous_cp95_upper": upper,
            }
        )
    null_summary = pd.DataFrame(null_summary_rows)

    alternative_path = output / "alternative_metrics.parquet"
    null_path = output / "null_metrics.parquet"
    alternative.to_parquet(alternative_path, index=False)
    null.to_parquet(null_path, index=False)
    alternative.to_csv(output / "alternative_metrics.csv", index=False)
    null.to_csv(output / "null_metrics.csv", index=False)
    cell_summary.to_csv(output / "alternative_cell_summary.csv", index=False)
    null_summary.to_csv(output / "null_calibration_summary.csv", index=False)
    overall.to_csv(output / "overall_summary.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "candidate_weights": list(LATE_WEIGHTS),
        "reference_weights": list(UNIFORM_WEIGHTS),
        "alternative_cells": len(alternative_cells),
        "alternative_seed_interval_per_cell": [
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.streams_per_cell - 1,
        ],
        "null_seed_interval_per_scenario": [
            config.null_seed_offset,
            config.null_seed_offset + config.null_streams - 1,
        ],
        "alternative_metric_rows": len(alternative),
        "null_metric_rows": len(null),
        "macro_detection_difference": macro_difference,
        "macro_cluster_bootstrap_95": [bootstrap_lower, bootstrap_upper],
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "resolved_devices": sorted(resolved_devices),
        "environment": environment(),
        "alternative_metrics_sha256": hashlib.sha256(alternative_path.read_bytes()).hexdigest(),
        "null_metrics_sha256": hashlib.sha256(null_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "late_prior_confirmation.py",
                "start_prior_validation.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference": (
            "Primary macro effect is paired candidate-minus-uniform detection averaged within "
            "seed and percentile-bootstrap resampled over 2,000 independent seed clusters. "
            "Secondary cellwise exact two-sided McNemar tests use Holm adjustment over 18 cells. "
            "Null bounds are one-sided exact Clopper-Pearson with simultaneous 95% Bonferroni "
            "coverage over 12 method/scenario/query cells."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Late Beta(2,1) start-prior confirmation",
        "",
        "The candidate and analysis were frozen after development. This independent study compares nominal-horizon Beta(2,1) weights with the uniform eight-start reference.",
        "",
        f"- Alternative cells: {len(alternative_cells)} × {config.streams_per_cell} paired streams; seeds {manifest['alternative_seed_interval_per_cell']}.",
        f"- Null cells: {false_family}; streams per cell: {config.null_streams}; seeds {manifest['null_seed_interval_per_scenario']} per scenario.",
        f"- Generator device(s): {', '.join(sorted(resolved_devices))}.",
        f"- Macro detection difference: {macro_difference:.5f}; seed-cluster bootstrap 95% interval [{bootstrap_lower:.5f}, {bootstrap_upper:.5f}].",
        "- Cellwise inference: exact two-sided McNemar with Holm adjustment across 18 cells.",
        "- Null calibration: one-sided exact Clopper-Pearson upper bounds with simultaneous 95% Bonferroni coverage.",
        "",
        "## Paired cell results",
        "",
        cell_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null calibration",
        "",
        null_summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The result applies only to the registered synthetic conditions. A positive result does not establish novelty or external validity; a mixed result leaves uniform as the default.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return alternative, cell_summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/late_prior_confirmation")
    parser.add_argument("--streams-per-cell", type=int, default=2000)
    parser.add_argument("--null-streams", type=int, default=2000)
    parser.add_argument("--alternative-seed-offset", type=int, default=20286000)
    parser.add_argument("--null-seed-offset", type=int, default=20288000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = LatePriorConfirmationConfig(
        streams_per_cell=args.streams_per_cell,
        null_streams=args.null_streams,
        alternative_seed_offset=args.alternative_seed_offset,
        null_seed_offset=args.null_seed_offset,
        device=args.device,
    )
    _alternative, _cells, manifest = run_late_prior_confirmation(args.output_dir, config)
    print(f"macro_difference={manifest['macro_detection_difference']:.5f}")
    print(f"macro_cluster_bootstrap_95={manifest['macro_cluster_bootstrap_95']}")
    print(f"alternative_metrics_sha256={manifest['alternative_metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
