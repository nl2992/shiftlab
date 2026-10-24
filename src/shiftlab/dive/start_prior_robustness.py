"""Development grid for fixed start-time priors under delay and horizon mismatch."""

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
from .start_prior_sweep import PRIOR_SHAPES, beta_start_weights
from .start_prior_validation import _format_log_p, _holm_log_p, _mcnemar_log_p

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60, 0.80)
HARM_INCREASES = (0.12, 0.24)
HORIZON_MULTIPLIERS = (0.5, 1.0, 1.5)
DELAY_LAWS = ("fixed_0", "uniform_0_6", "uniform_0_12", "fixed_12")
METHODS = tuple(PRIOR_SHAPES) + ("full_stream_betting",)
REFERENCE_METHOD = "uniform_beta_1_1"


@dataclass(frozen=True)
class StartPriorRobustnessConfig:
    seeds_per_cell: int = 200
    null_streams: int = 500
    alternative_seed_offset: int = 20278000
    null_seed_offset: int = 20280000
    n_events: int = 3000
    query_rates: tuple[float, ...] = QUERY_RATES
    harm_onsets: tuple[float, ...] = ONSETS
    harm_increases: tuple[float, ...] = HARM_INCREASES
    horizon_multipliers: tuple[float, ...] = HORIZON_MULTIPLIERS
    delay_laws: tuple[str, ...] = DELAY_LAWS
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    device: str = "cuda"

    def validate(self) -> StartPriorRobustnessConfig:
        if self.seeds_per_cell < 1 or self.null_streams < 1 or self.n_events < 100:
            raise ValueError("seed counts must be positive and n_events at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query rates must lie in (0, 1]")
        if not self.harm_onsets or any(not 0 < onset < 1 for onset in self.harm_onsets):
            raise ValueError("harm onset fractions must lie in (0, 1)")
        if not self.harm_increases or any(
            not 0 < effect <= 0.98 * self.amplitude for effect in self.harm_increases
        ):
            raise ValueError("harm increases must yield valid sign probabilities")
        if not self.horizon_multipliers or any(
            not np.isfinite(x) or x <= 0 for x in self.horizon_multipliers
        ):
            raise ValueError("horizon multipliers must be positive and finite")
        for values, name in (
            (self.query_rates, "query_rates"),
            (self.harm_onsets, "harm_onsets"),
            (self.harm_increases, "harm_increases"),
            (self.horizon_multipliers, "horizon_multipliers"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must be unique")
        if (
            not self.delay_laws
            or len(set(self.delay_laws)) != len(self.delay_laws)
            or any(law not in DELAY_LAWS for law in self.delay_laws)
        ):
            raise ValueError(f"delay_laws must be selected from {DELAY_LAWS}")
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


def _delay_values(seed: int, n_events: int, law: str) -> np.ndarray:
    """Use independent common uniforms for outcome-independent delay-law comparisons."""
    if law == "fixed_0":
        return np.zeros(n_events, dtype=np.int64)
    if law == "fixed_12":
        return np.full(n_events, 12, dtype=np.int64)
    uniforms = np.random.default_rng(np.random.SeedSequence([seed, 941_207])).random(n_events)
    upper = 6 if law == "uniform_0_6" else 12
    return np.floor(uniforms * (upper + 1)).astype(np.int64)


def _start_locations(query_rate: float, n_events: int, multiplier: float) -> tuple[int, ...]:
    horizon = max(1, round(query_rate * n_events * multiplier))
    return tuple(sorted({round(horizon * index / 8) for index in range(8)}))


def _method_alarms(
    values: np.ndarray,
    events: np.ndarray,
    delays: np.ndarray,
    *,
    query_rate: float,
    n_events: int,
    multiplier: float,
    margin: float,
    alpha: float,
    amplitude: float,
) -> dict[str, int | None]:
    """Evaluate fixed mixtures and full-stream betting on one paired stream."""
    starts = _start_locations(query_rate, n_events, multiplier)
    centered = values - margin
    bound = amplitude + margin + 1e-6
    alarms: dict[str, int | None] = {}
    for method, shape in PRIOR_SHAPES.items():
        log_values = _restart_log_e_values(
            centered,
            bound=bound,
            starts=starts,
            start_weights=beta_start_weights(*shape),
        )
        crossing = _first_crossing(log_values, math.log(1 / alpha))
        alarms[method] = int(events[crossing]) if crossing is not None else None
    shared = calibration_alarm_indices(
        values,
        events,
        events + delays[events],
        query_rate=query_rate,
        n_events=n_events,
        margin=margin,
        alpha=alpha,
        amplitude=amplitude,
    )
    alarms["full_stream_betting"] = shared["paired_cost_betting"][0]
    return alarms


def _cell_summary(frame: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "query_rate",
        "harm_onset_fraction",
        "harm_increase",
        "horizon_multiplier",
        "delay_law",
        "method",
    ]
    return (
        frame.groupby(keys, sort=True)
        .agg(
            detected=("detected", "sum"),
            streams=("detected", "size"),
            detection_rate=("detected", "mean"),
            pre_onset_escalations=("false_escalation_before_onset", "sum"),
            mean_event_delay_given_detection=("event_detection_delay", "mean"),
            mean_wall_delay_given_detection=("wall_detection_delay", "mean"),
        )
        .reset_index()
    )


def _adjusted_p_below_alpha(value: str, alpha: float = 0.05) -> bool:
    """Parse displayed adjusted p-values, including values retained on the log scale."""
    return value.startswith("<") or float(value) < alpha


def run_start_prior_robustness(
    output_dir: str | Path, config: StartPriorRobustnessConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run the frozen mismatch/delay grid and independent screening nulls."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prior_weights = {name: beta_start_weights(*shape) for name, shape in PRIOR_SHAPES.items()}
    null_rows: list[dict[str, object]] = []
    alt_rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()

    null_config = DelayedCalibrationConfig(
        streams_per_cell=config.null_streams,
        seed_offset=config.null_seed_offset,
        n_events=config.n_events,
        query_rates=config.query_rates,
        alpha=config.alpha,
        margin=config.margin,
        amplitude=config.amplitude,
        benign_amplitude=config.benign_amplitude,
        delay_scheme="fixed_3",
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
            contrasts, query_uniforms, _ = _generate_null_stream(
                null_config, seed=seed, scenario=scenario, device=null_device
            )
            resolved_devices.add(str(null_device))
            for delay_law in config.delay_laws:
                delays = _delay_values(seed, config.n_events, delay_law)
                for query_rate in config.query_rates:
                    events = np.flatnonzero(query_uniforms < query_rate)
                    values = contrasts[events]
                    for multiplier in config.horizon_multipliers:
                        alarms = _method_alarms(
                            values,
                            events,
                            delays,
                            query_rate=query_rate,
                            n_events=config.n_events,
                            multiplier=multiplier,
                            margin=config.margin,
                            alpha=config.alpha,
                            amplitude=config.amplitude,
                        )
                        for method, alarm_event in alarms.items():
                            null_rows.append(
                                {
                                    "scenario": scenario,
                                    "query_rate": query_rate,
                                    "horizon_multiplier": multiplier,
                                    "delay_law": delay_law,
                                    "seed": seed,
                                    "method": method,
                                    "false_escalation": alarm_event is not None,
                                    "alarm_event": alarm_event,
                                }
                            )

    alt_cells = list(
        itertools.product(
            config.query_rates,
            config.harm_onsets,
            config.harm_increases,
            config.horizon_multipliers,
            config.delay_laws,
        )
    )
    for query_rate, onset, harm_increase, multiplier, delay_law in alt_cells:
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
            delay_schemes=("fixed_3",),
            scenarios=("boundary_harm",),
            device=config.device,
        ).validate()
        for seed in range(
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.seeds_per_cell,
        ):
            (
                _source,
                contrast,
                queried,
                _base_delays,
                onset_event,
                resolved_device,
            ) = _generate_stream(
                stream_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme="fixed_3",
            )
            resolved_devices.add(resolved_device)
            events = np.flatnonzero(queried)
            delays = _delay_values(seed, config.n_events, delay_law)
            alarms = _method_alarms(
                contrast[events],
                events,
                delays,
                query_rate=query_rate,
                n_events=config.n_events,
                multiplier=multiplier,
                margin=config.margin,
                alpha=config.alpha,
                amplitude=config.amplitude,
            )
            for method, alarm_event in alarms.items():
                detected = alarm_event is not None and alarm_event >= onset_event
                processed = (
                    int(np.searchsorted(events, alarm_event, side="right"))
                    if alarm_event is not None
                    else len(events)
                )
                wall_alarm = (
                    int(np.maximum.accumulate(events + delays[events])[processed - 1])
                    if alarm_event is not None
                    else None
                )
                alt_rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset,
                        "harm_increase": harm_increase,
                        "horizon_multiplier": multiplier,
                        "delay_law": delay_law,
                        "method": method,
                        "device": resolved_device,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": wall_alarm,
                        "detected": bool(detected),
                        "false_escalation_before_onset": bool(
                            alarm_event is not None and alarm_event < onset_event
                        ),
                        "event_detection_delay": alarm_event - onset_event if detected else None,
                        "wall_detection_delay": wall_alarm - onset_event if detected else None,
                        "labels_queried": len(events),
                    }
                )

    null_frame = pd.DataFrame(null_rows)
    alt_frame = pd.DataFrame(alt_rows)
    n_null_cells = (
        len(NULL_SCENARIOS)
        * len(config.query_rates)
        * len(config.horizon_multipliers)
        * len(config.delay_laws)
    )
    null_summary_rows = []
    null_keys = ["scenario", "query_rate", "horizon_multiplier", "delay_law", "method"]
    for keys, group in null_frame.groupby(null_keys, sort=True):
        count = int(group.false_escalation.sum())
        trials = len(group)
        upper = (
            1.0
            if count == trials
            else float(
                beta.ppf(1 - 0.05 / (n_null_cells * len(METHODS)), count + 1, trials - count)
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
    alt_summary = _cell_summary(alt_frame)

    # Pair each nonuniform method with uniform and correct the complete test family with Holm.
    comparisons = []
    cell_keys = [
        "query_rate",
        "harm_onset_fraction",
        "harm_increase",
        "horizon_multiplier",
        "delay_law",
    ]
    for key, group in alt_frame.groupby(cell_keys, sort=True):
        wide = group.pivot(index="seed", columns="method", values="detected")
        cell = dict(zip(cell_keys, key, strict=True))
        for method in METHODS:
            if method == REFERENCE_METHOD:
                continue
            candidate_only = int((wide[method] & ~wide[REFERENCE_METHOD]).sum())
            reference_only = int((~wide[method] & wide[REFERENCE_METHOD]).sum())
            log_p = _mcnemar_log_p(candidate_only, reference_only)
            comparisons.append(
                {
                    **cell,
                    "method": method,
                    "reference_method": REFERENCE_METHOD,
                    "candidate_only": candidate_only,
                    "uniform_only": reference_only,
                    "candidate_rate": float(wide[method].mean()),
                    "uniform_rate": float(wide[REFERENCE_METHOD].mean()),
                    "rate_difference": float(wide[method].mean() - wide[REFERENCE_METHOD].mean()),
                    "mcnemar_p": _format_log_p(log_p),
                    "log_p": log_p,
                }
            )
    paired = pd.DataFrame(comparisons)
    adjusted = _holm_log_p(paired.log_p.tolist())
    paired["holm_adjusted_p"] = [_format_log_p(value) for value in adjusted]
    paired = paired.drop(columns="log_p")

    method_summary = (
        alt_summary.groupby(["method", "delay_law", "horizon_multiplier"], sort=True)
        .agg(
            macro_cell_detection=("detection_rate", "mean"),
            worst_cell_detection=("detection_rate", "min"),
            pre_onset_escalations=("pre_onset_escalations", "sum"),
        )
        .reset_index()
    )
    null_path = output / "null_metrics.parquet"
    alt_path = output / "alternative_metrics.parquet"
    null_frame.to_parquet(null_path, index=False)
    alt_frame.to_parquet(alt_path, index=False)
    null_frame.to_csv(output / "null_metrics.csv", index=False)
    alt_frame.to_csv(output / "alternative_metrics.csv", index=False)
    null_summary.to_csv(output / "null_summary.csv", index=False)
    alt_summary.to_csv(output / "alternative_cell_summary.csv", index=False)
    paired.to_csv(output / "paired_tests.csv", index=False)
    method_summary.to_csv(output / "method_strata_summary.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "methods": list(METHODS),
        "reference_method": REFERENCE_METHOD,
        "fixed_prior_weights": {name: list(weights) for name, weights in prior_weights.items()},
        "alternative_cells": len(alt_cells),
        "null_cells": n_null_cells,
        "alternative_seed_interval_per_cell": [
            config.alternative_seed_offset,
            config.alternative_seed_offset + config.seeds_per_cell - 1,
        ],
        "null_seed_interval_per_cell": [
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
                "start_prior_robustness.py",
                "start_prior_sweep.py",
                "start_prior_validation.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference": (
            "Exploratory robustness screen. Cellwise paired exact two-sided McNemar comparisons "
            "against uniform receive Holm adjustment across all alternative method-by-cell tests. "
            "Null false-escalation upper bounds are one-sided Clopper-Pearson with Bonferroni "
            "simultaneous 95% coverage across all method/null cells. The 500-stream nulls are "
            "screening diagnostics only."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Fixed-prior delay and horizon robustness screen",
        "",
        "Exploratory screen; no method is selected from these data. Fixed-prior mixtures remain convex combinations of valid component e-processes under the same assumptions.",
        "",
        f"- Alternative cells: {len(alt_cells)}; streams per cell: {config.seeds_per_cell}; seed block: {manifest['alternative_seed_interval_per_cell']}.",
        f"- Null cells: {n_null_cells}; streams per cell: {config.null_streams}; seed block: {manifest['null_seed_interval_per_cell']}.",
        f"- CUDA generation resolved to: {', '.join(sorted(resolved_devices))}.",
        "- Paired test family: exact two-sided McNemar, Holm-adjusted across every nonuniform method and alternative cell.",
        "- Null interval family: one-sided exact Clopper-Pearson, simultaneous 95% Bonferroni coverage over all method/null cells.",
        "",
        "## Detection by delay and planned horizon",
        "",
        method_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null calibration screen",
        "",
        null_summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "Cell-level alternative metrics and paired tests are in the CSV/Parquet files. Nondetections are censored in delay summaries. The study covers only the registered independent synthetic streams; dependent or outcome-informative delays require a different validity argument. This screen is not final confirmation. No figure is produced; use PaperBanana for any later visual.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return alt_frame, paired, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/start_prior_robustness")
    parser.add_argument("--seeds-per-cell", type=int, default=200)
    parser.add_argument("--null-streams", type=int, default=500)
    parser.add_argument("--alternative-seed-offset", type=int, default=20278000)
    parser.add_argument("--null-seed-offset", type=int, default=20280000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = StartPriorRobustnessConfig(
        seeds_per_cell=args.seeds_per_cell,
        null_streams=args.null_streams,
        alternative_seed_offset=args.alternative_seed_offset,
        null_seed_offset=args.null_seed_offset,
        device=args.device,
    )
    _frame, paired, manifest = run_start_prior_robustness(args.output_dir, config)
    summary = paired.groupby("method").agg(
        mean_rate_difference=("rate_difference", "mean"),
        significant_cells=(
            "holm_adjusted_p",
            lambda values: sum(_adjusted_p_below_alpha(value) for value in values),
        ),
    )
    print(summary.to_string())
    print(f"alternative_metrics_sha256={manifest['alternative_metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
