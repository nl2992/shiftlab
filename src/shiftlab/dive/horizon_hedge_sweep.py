"""Development grid for a fixed e-process mixture across uncertain horizons."""

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
from .eprocess import HorizonHedgedStartedMixtureEProcess
from .start_prior_sweep import HARM_INCREASES, PRIOR_SHAPES, QUERY_RATES, beta_start_weights
from .start_prior_validation import _format_log_p, _holm_log_p, _mcnemar_log_p

HORIZON_SCALES = (0.5, 1.0, 1.5)
HORIZON_PRIORS = tuple(
    f"fixed_{prior}_h{scale:.1f}" for prior in PRIOR_SHAPES for scale in HORIZON_SCALES
)
HEDGED_METHODS = ("hedged_center_multihorizon", "hedged_uniform_multihorizon")
FULL_STREAM = "full_stream_betting"
METHODS = HORIZON_PRIORS + HEDGED_METHODS + (FULL_STREAM,)
REFERENCE_METHOD = "fixed_uniform_beta_1_1_h1.0"
NULL_METHODS = (
    "hedged_center_multihorizon",
    "hedged_uniform_multihorizon",
    "fixed_uniform_beta_1_1_h1.0",
    "fixed_late_beta_2_1_h1.0",
    FULL_STREAM,
)


@dataclass(frozen=True)
class HorizonHedgeSweepConfig:
    seeds_per_cell: int = 200
    null_streams: int = 500
    alternative_seed_offset: int = 20282000
    null_seed_offset: int = 20284000
    n_events: int = 3000
    query_rates: tuple[float, ...] = QUERY_RATES
    harm_onsets: tuple[float, ...] = (0.20, 0.60, 0.80)
    harm_increases: tuple[float, ...] = HARM_INCREASES
    horizon_scales: tuple[float, ...] = HORIZON_SCALES
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    delay_scheme: str = "uniform_0_6"
    device: str = "cuda"

    def validate(self) -> HorizonHedgeSweepConfig:
        if min(self.seeds_per_cell, self.null_streams) < 1 or self.n_events < 100:
            raise ValueError("seed counts must be positive and n_events at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query_rates must be nonempty and lie in (0, 1]")
        if not self.harm_onsets or any(not 0 < onset < 1 for onset in self.harm_onsets):
            raise ValueError("harm_onsets must be nonempty and lie in (0, 1)")
        if not self.harm_increases or any(
            not 0 < effect <= 0.98 * self.amplitude for effect in self.harm_increases
        ):
            raise ValueError("harm increases must yield valid sign probabilities")
        if tuple(self.horizon_scales) != HORIZON_SCALES:
            raise ValueError(f"horizon_scales are frozen at {HORIZON_SCALES}")
        for values, name in (
            (self.query_rates, "query_rates"),
            (self.harm_onsets, "harm_onsets"),
            (self.harm_increases, "harm_increases"),
            (self.horizon_scales, "horizon_scales"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must be unique")
        if self.delay_scheme not in {"fixed_3", "uniform_0_6"}:
            raise ValueError("delay_scheme must be fixed_3 or uniform_0_6")
        if not 0 < self.alpha < 1 or not 0 <= self.margin < 1:
            raise ValueError("alpha and margin are invalid")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        alt_end = self.alternative_seed_offset + self.seeds_per_cell
        null_end = self.null_seed_offset + self.null_streams
        if max(self.alternative_seed_offset, self.null_seed_offset) < min(alt_end, null_end):
            raise ValueError("alternative and null seed blocks must be disjoint")
        return self


def _planned_horizon(query_rate: float, n_events: int, scale: float) -> int:
    return max(1, round(query_rate * n_events * scale))


def _fixed_prior_alarm(
    values: np.ndarray,
    events: np.ndarray,
    *,
    query_rate: float,
    n_events: int,
    scale: float,
    weights: tuple[float, ...],
    margin: float,
    alpha: float,
    amplitude: float,
) -> int | None:
    horizon = _planned_horizon(query_rate, n_events, scale)
    starts = tuple(round(horizon * index / 8) for index in range(8))
    logs = _restart_log_e_values(
        values - margin,
        bound=amplitude + margin + 1e-6,
        starts=starts,
        start_weights=weights,
    )
    crossing = _first_crossing(logs, math.log(1 / alpha))
    return int(events[crossing]) if crossing is not None else None


def _all_method_alarms(
    values: np.ndarray,
    events: np.ndarray,
    arrivals: np.ndarray,
    *,
    query_rate: float,
    n_events: int,
    horizon_scales: tuple[float, ...],
    margin: float,
    alpha: float,
    amplitude: float,
) -> dict[str, int | None]:
    alarms: dict[str, int | None] = {}
    for prior_name, shape in PRIOR_SHAPES.items():
        weights = beta_start_weights(*shape)
        for scale in horizon_scales:
            name = f"fixed_{prior_name}_h{scale:.1f}"
            alarms[name] = _fixed_prior_alarm(
                values,
                events,
                query_rate=query_rate,
                n_events=n_events,
                scale=scale,
                weights=weights,
                margin=margin,
                alpha=alpha,
                amplitude=amplitude,
            )

    horizon_hypotheses = tuple(
        _planned_horizon(query_rate, n_events, scale) for scale in horizon_scales
    )
    fractions = tuple(index / 8 for index in range(8))
    uniform_weights = tuple(np.full(8, 1 / 8, dtype=float))
    for method, inner_weights in (
        ("hedged_center_multihorizon", beta_start_weights(*PRIOR_SHAPES["center_beta_2_2"])),
        ("hedged_uniform_multihorizon", uniform_weights),
    ):
        process = HorizonHedgedStartedMixtureEProcess(
            bound=amplitude + margin + 1e-6,
            alpha=alpha,
            horizons=horizon_hypotheses,
            horizon_weights=tuple(np.full(len(horizon_hypotheses), 1 / len(horizon_hypotheses))),
            start_fractions=fractions,
            start_weights=inner_weights,
        )
        logs = _restart_log_e_values(
            values - margin,
            bound=amplitude + margin + 1e-6,
            starts=process.starts,
            start_weights=tuple(float(weight) for weight in process.weights),
        )
        crossing = _first_crossing(logs, math.log(1 / alpha))
        alarms[method] = int(events[crossing]) if crossing is not None else None

    shared = calibration_alarm_indices(
        values,
        events,
        arrivals,
        query_rate=query_rate,
        n_events=n_events,
        margin=margin,
        alpha=alpha,
        amplitude=amplitude,
    )
    alarms[FULL_STREAM] = shared["paired_cost_betting"][0]
    return alarms


def _holm_values(log_p: list[float]) -> list[float]:
    return _holm_log_p(log_p)


def run_horizon_hedge_sweep(
    output_dir: str | Path, config: HorizonHedgeSweepConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Screen fixed multihorizon mixtures against fixed-horizon priors."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    alt_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()
    center_weights = beta_start_weights(*PRIOR_SHAPES["center_beta_2_2"])
    uniform_weights = tuple(np.full(8, 1 / 8, dtype=float))
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
            for query_rate in config.query_rates:
                events = np.flatnonzero(query_uniforms < query_rate)
                values = contrasts[events]
                alarms = _all_method_alarms(
                    values,
                    events,
                    events + delays[events],
                    query_rate=query_rate,
                    n_events=config.n_events,
                    horizon_scales=config.horizon_scales,
                    margin=config.margin,
                    alpha=config.alpha,
                    amplitude=config.amplitude,
                )
                for method in NULL_METHODS:
                    alarm = alarms[method]
                    null_rows.append(
                        {
                            "scenario": scenario,
                            "query_rate": query_rate,
                            "seed": seed,
                            "method": method,
                            "false_escalation": alarm is not None,
                            "alarm_event": alarm,
                        }
                    )

    alt_cells = list(
        itertools.product(config.query_rates, config.harm_onsets, config.harm_increases)
    )
    for query_rate, onset, harm_increase in alt_cells:
        stream_config = DelayedBenchmarkConfig(
            seeds=config.seeds_per_cell,
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
            config.alternative_seed_offset + config.seeds_per_cell,
        ):
            _source, contrast, queried, delays, onset_event, resolved_device = _generate_stream(
                stream_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved_device)
            events = np.flatnonzero(queried)
            alarms = _all_method_alarms(
                contrast[events],
                events,
                events + delays[events],
                query_rate=query_rate,
                n_events=config.n_events,
                horizon_scales=config.horizon_scales,
                margin=config.margin,
                alpha=config.alpha,
                amplitude=config.amplitude,
            )
            for method, alarm in alarms.items():
                detected = alarm is not None and alarm >= onset_event
                processed = (
                    int(np.searchsorted(events, alarm, side="right"))
                    if alarm is not None
                    else len(events)
                )
                wall = (
                    int(np.maximum.accumulate(events + delays[events])[processed - 1])
                    if alarm is not None
                    else None
                )
                alt_rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset,
                        "harm_increase": harm_increase,
                        "method": method,
                        "device": resolved_device,
                        "alarm_event": alarm,
                        "alarm_wall_time": wall,
                        "detected": bool(detected),
                        "false_escalation_before_onset": bool(
                            alarm is not None and alarm < onset_event
                        ),
                        "event_detection_delay": alarm - onset_event if detected else None,
                        "wall_detection_delay": wall - onset_event if detected else None,
                        "labels_queried": len(events),
                    }
                )

    alt_frame = pd.DataFrame(alt_rows)
    null_frame = pd.DataFrame(null_rows)
    alt_cell_rows = []
    cell_keys = ["query_rate", "harm_onset_fraction", "harm_increase", "method"]
    for keys, group in alt_frame.groupby(cell_keys, sort=True):
        detected = int(group.detected.sum())
        trials = len(group)
        lower = 0.0 if detected == 0 else float(beta.ppf(0.025, detected, trials - detected + 1))
        upper = (
            1.0 if detected == trials else float(beta.ppf(0.975, detected + 1, trials - detected))
        )
        alt_cell_rows.append(
            {
                **dict(zip(cell_keys, keys, strict=True)),
                "detected": detected,
                "streams": trials,
                "detection_rate": detected / trials,
                "cp95_lower": lower,
                "cp95_upper": upper,
                "pre_onset_escalations": int(group.false_escalation_before_onset.sum()),
                "mean_event_delay_given_detection": group.event_detection_delay.mean(),
                "mean_wall_delay_given_detection": group.wall_detection_delay.mean(),
            }
        )
    alt_summary = pd.DataFrame(alt_cell_rows)

    paired_rows = []
    log_ps = []
    group_keys = ["query_rate", "harm_onset_fraction", "harm_increase"]
    for cell, group in alt_frame.groupby(group_keys, sort=True):
        wide = group.pivot(index="seed", columns="method", values="detected")
        cell_values = dict(zip(group_keys, cell, strict=True))
        for method in METHODS:
            if method == REFERENCE_METHOD:
                continue
            candidate_only = int((wide[method] & ~wide[REFERENCE_METHOD]).sum())
            reference_only = int((~wide[method] & wide[REFERENCE_METHOD]).sum())
            log_p = _mcnemar_log_p(candidate_only, reference_only)
            log_ps.append(log_p)
            paired_rows.append(
                {
                    **cell_values,
                    "method": method,
                    "reference_method": REFERENCE_METHOD,
                    "candidate_only": candidate_only,
                    "uniform_only": reference_only,
                    "candidate_rate": float(wide[method].mean()),
                    "reference_rate": float(wide[REFERENCE_METHOD].mean()),
                    "rate_difference": float(wide[method].mean() - wide[REFERENCE_METHOD].mean()),
                    "mcnemar_p": _format_log_p(log_p),
                    "log_p": log_p,
                }
            )
    paired = pd.DataFrame(paired_rows)
    paired["holm_adjusted_p"] = [_format_log_p(value) for value in _holm_values(log_ps)]
    paired = paired.drop(columns="log_p")

    null_cells = len(NULL_SCENARIOS) * len(config.query_rates)
    null_summary_rows = []
    null_keys = ["scenario", "query_rate", "method"]
    for keys, group in null_frame.groupby(null_keys, sort=True):
        count, trials = int(group.false_escalation.sum()), len(group)
        upper = (
            1.0
            if count == trials
            else float(
                beta.ppf(1 - 0.05 / (null_cells * len(NULL_METHODS)), count + 1, trials - count)
            )
        )
        null_summary_rows.append(
            {
                **dict(zip(null_keys, keys, strict=True)),
                "false_escalations": count,
                "streams": trials,
                "false_escalation_rate": count / trials,
                "simultaneous_cp95_upper": upper,
            }
        )
    null_summary = pd.DataFrame(null_summary_rows)
    ranking = (
        alt_summary.groupby("method", sort=True)
        .agg(
            macro_cell_detection=("detection_rate", "mean"),
            worst_cell_detection=("detection_rate", "min"),
            pre_onset_escalations=("pre_onset_escalations", "sum"),
        )
        .sort_values(["macro_cell_detection", "worst_cell_detection"], ascending=False)
        .reset_index()
    )

    alt_path = output / "alternative_metrics.parquet"
    null_path = output / "null_metrics.parquet"
    alt_frame.to_parquet(alt_path, index=False)
    null_frame.to_parquet(null_path, index=False)
    alt_frame.to_csv(output / "alternative_metrics.csv", index=False)
    null_frame.to_csv(output / "null_metrics.csv", index=False)
    alt_summary.to_csv(output / "alternative_cell_summary.csv", index=False)
    null_summary.to_csv(output / "null_summary.csv", index=False)
    paired.to_csv(output / "paired_tests.csv", index=False)
    ranking.to_csv(output / "method_ranking.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "methods": list(METHODS),
        "reference_method": REFERENCE_METHOD,
        "null_methods": list(NULL_METHODS),
        "hedged_horizon_weights": [1 / len(config.horizon_scales)] * len(config.horizon_scales),
        "hedged_center_start_weights": list(center_weights),
        "hedged_uniform_start_weights": list(uniform_weights),
        "alternative_cells": len(alt_cells),
        "alternative_seed_interval": [
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.seeds_per_cell - 1,
        ],
        "null_seed_interval": [
            config.null_seed_offset,
            config.null_seed_offset + config.null_streams - 1,
        ],
        "alternative_metric_rows": len(alt_frame),
        "null_metric_rows": len(null_frame),
        "resolved_devices": sorted(resolved_devices),
        "environment": environment(),
        "alternative_metrics_sha256": hashlib.sha256(alt_path.read_bytes()).hexdigest(),
        "null_metrics_sha256": hashlib.sha256(null_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "horizon_hedge_sweep.py",
                "eprocess.py",
                "start_prior_sweep.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference": (
            "Development screen only. Exact two-sided paired McNemar tests compare each of the 17 "
            "non-reference methods against nominal uniform in 18 cells; Holm adjusts across 306 "
            "tests. Null upper bounds are one-sided exact Clopper-Pearson with simultaneous 95% "
            "Bonferroni coverage across 30 method/null cells and 500 streams per cell."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Fixed multihorizon e-process development screen",
        "",
        "Two fixed horizon-hedged priors are compared with fixed-horizon Beta priors and full-stream betting. All candidate weights are frozen before each stream; no adaptive reweighting is used.",
        "",
        f"- Alternative cells: {len(alt_cells)} with {config.seeds_per_cell} paired streams each; seeds {manifest['alternative_seed_interval']}.",
        f"- Null cells: {null_cells * len(NULL_METHODS)} method/scenario/query cells with {config.null_streams} streams each; seeds {manifest['null_seed_interval']}.",
        f"- Resolved generation device(s): {', '.join(sorted(resolved_devices))}.",
        "- Paired inference: exact two-sided McNemar with Holm adjustment across 306 comparisons.",
        "- Null bounds: one-sided exact Clopper-Pearson with simultaneous 95% Bonferroni coverage.",
        "",
        "## Development ranking",
        "",
        ranking.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Alternative detection",
        "",
        alt_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null screen",
        "",
        null_summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "This screen cannot support a novelty claim or a default-method change. Any promising candidate needs a separately frozen large null calibration and disjoint alternative confirmation. The guarantee requires bounded contrasts, predictable queries, the conditional-mean null, and outcome-independent feedback delays.",
        "",
        "No figure is included. If a visual is useful later, use PaperBanana.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return alt_frame, paired, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/horizon_hedge_development")
    parser.add_argument("--seeds-per-cell", type=int, default=200)
    parser.add_argument("--null-streams", type=int, default=500)
    parser.add_argument("--alternative-seed-offset", type=int, default=20282000)
    parser.add_argument("--null-seed-offset", type=int, default=20284000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = HorizonHedgeSweepConfig(
        seeds_per_cell=args.seeds_per_cell,
        null_streams=args.null_streams,
        alternative_seed_offset=args.alternative_seed_offset,
        null_seed_offset=args.null_seed_offset,
        device=args.device,
    )
    _frame, _paired, manifest = run_horizon_hedge_sweep(args.output_dir, config)
    print(f"alternative_metrics_sha256={manifest['alternative_metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
