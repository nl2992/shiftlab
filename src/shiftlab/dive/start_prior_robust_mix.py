"""Development grid for fixed convex blends of late and uniform start priors."""

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

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60, 0.80)
HARM_INCREASES = (0.12, 0.24)
RHO_GRID = (0.0, 0.25, 0.50, 0.75, 1.0)
LATE_WEIGHTS = beta_start_weights(2.0, 1.0)
UNIFORM_WEIGHTS = beta_start_weights(1.0, 1.0)


def mixture_weights(rho: float) -> tuple[float, ...]:
    """Return a fixed convex blend of Beta(2,1) and uniform start masses."""
    if not 0 <= rho <= 1:
        raise ValueError("rho must lie in [0, 1]")
    weights = tuple(
        rho * late + (1.0 - rho) * uniform
        for late, uniform in zip(LATE_WEIGHTS, UNIFORM_WEIGHTS, strict=True)
    )
    if any(weight <= 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-12:
        raise RuntimeError("mixture weights must be positive and sum to one")
    return weights


@dataclass(frozen=True)
class StartPriorRobustMixConfig:
    streams_per_cell: int = 500
    null_streams: int = 1000
    alternative_seed_offset: int = 20290000
    null_seed_offset: int = 20291000
    n_events: int = 3000
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    delay_scheme: str = "uniform_0_6"
    device: str = "cuda"

    def validate(self) -> StartPriorRobustMixConfig:
        if min(self.streams_per_cell, self.null_streams) < 1 or self.n_events < 100:
            raise ValueError("stream counts must be positive and n_events at least 100")
        if not 0 < self.alpha < 1 or not 0 <= self.margin < 1:
            raise ValueError("alpha and margin are invalid")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if self.delay_scheme != "uniform_0_6":
            raise ValueError("the development delay scheme is frozen at uniform_0_6")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        alt = range(
            self.alternative_seed_offset, self.alternative_seed_offset + self.streams_per_cell
        )
        nul = range(self.null_seed_offset, self.null_seed_offset + self.null_streams)
        if max(alt.start, nul.start) <= min(alt.stop - 1, nul.stop - 1):
            raise ValueError("alternative and null seed blocks must be disjoint")
        return self


def _method_name(rho: float) -> str:
    return f"rho_{rho:.2f}"


def run_start_prior_robust_mix(
    output_dir: str | Path, config: StartPriorRobustMixConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run development alternatives and independent null calibration for fixed priors."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    weights_by_rho = {rho: mixture_weights(rho) for rho in RHO_GRID}
    resolved_devices: set[str] = set()
    alternative_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []

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
                for rho, weights in weights_by_rho.items():
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
                            "rho": rho,
                            "method": _method_name(rho),
                            "alarm_event": alarm_event,
                            "alarm_wall_time": alarm_wall,
                            "false_escalation": alarm_event is not None,
                        }
                    )

    for query_rate, onset, harm_increase in itertools.product(QUERY_RATES, ONSETS, HARM_INCREASES):
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
            _source, contrasts, queried, delays, onset_event, resolved = _generate_stream(
                stream_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved)
            events = queried.nonzero()[0]
            values = contrasts[events]
            arrivals = events + delays[events]
            for rho, weights in weights_by_rho.items():
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
                alternative_rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset,
                        "harm_increase": harm_increase,
                        "rho": rho,
                        "method": _method_name(rho),
                        "device": resolved,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": alarm_wall,
                        "detected": bool(detected),
                        "false_escalation_before_onset": bool(
                            alarm_event is not None and alarm_event < onset_event
                        ),
                        "event_detection_delay": alarm_event - onset_event if detected else None,
                        "wall_detection_delay": alarm_wall - onset_event if detected else None,
                        "labels_queried": len(events),
                    }
                )

    alternative = pd.DataFrame(alternative_rows)
    null = pd.DataFrame(null_rows)
    cell_summary = (
        alternative.groupby(
            ["rho", "method", "query_rate", "harm_onset_fraction", "harm_increase"],
            sort=True,
        )
        .agg(
            detected=("detected", "sum"),
            streams=("detected", "size"),
            detection_rate=("detected", "mean"),
            pre_onset_escalations=("false_escalation_before_onset", "sum"),
            mean_event_delay=("event_detection_delay", "mean"),
            mean_wall_delay=("wall_detection_delay", "mean"),
        )
        .reset_index()
    )
    groups = (
        cell_summary.groupby(["rho", "method", "harm_onset_fraction", "harm_increase"])
        .detection_rate.mean()
        .rename("group_detection_rate")
        .reset_index()
    )
    ranking = (
        groups.groupby(["rho", "method"])
        .agg(
            maximin_group_detection=("group_detection_rate", "min"),
            macro_group_detection=("group_detection_rate", "mean"),
        )
        .reset_index()
        .sort_values(["maximin_group_detection", "rho"], ascending=[False, True])
        .reset_index(drop=True)
    )
    selected = ranking.iloc[0]
    best_rate = float(selected.maximin_group_detection)
    tied = ranking[ranking.maximin_group_detection >= best_rate - 1e-12]
    selected_rho = float(tied.rho.min())

    null_family = len(NULL_SCENARIOS) * len(QUERY_RATES) * len(RHO_GRID)
    null_summary_rows = []
    for keys, group in null.groupby(["scenario", "query_rate", "rho", "method"], sort=True):
        errors = int(group.false_escalation.sum())
        trials = len(group)
        upper = (
            1.0
            if errors == trials
            else float(beta.ppf(1 - 0.05 / null_family, errors + 1, trials - errors))
        )
        null_summary_rows.append(
            {
                "scenario": keys[0],
                "query_rate": keys[1],
                "rho": keys[2],
                "method": keys[3],
                "false_escalations": errors,
                "streams": trials,
                "false_escalation_rate": errors / trials,
                "simultaneous_cp95_upper": upper,
            }
        )
    null_summary = pd.DataFrame(null_summary_rows)

    alt_path = output / "alternative_metrics.parquet"
    null_path = output / "null_metrics.parquet"
    alternative.to_parquet(alt_path, index=False)
    null.to_parquet(null_path, index=False)
    alternative.to_csv(output / "alternative_metrics.csv", index=False)
    null.to_csv(output / "null_metrics.csv", index=False)
    cell_summary.to_csv(output / "alternative_cell_summary.csv", index=False)
    null_summary.to_csv(output / "null_calibration_summary.csv", index=False)
    ranking.to_csv(output / "prior_ranking.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "rho_grid": list(RHO_GRID),
        "weights_by_rho": {str(rho): list(weights) for rho, weights in weights_by_rho.items()},
        "selection_objective": "maximize minimum detection rate over six onset/severity groups, each averaging three query rates; ties favor smaller rho",
        "selected_rho_development_only": selected_rho,
        "alternative_cells": len(QUERY_RATES) * len(ONSETS) * len(HARM_INCREASES),
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
        "null_family_size": null_family,
        "resolved_devices": sorted(resolved_devices),
        "environment": environment(),
        "alternative_metrics_sha256": hashlib.sha256(alt_path.read_bytes()).hexdigest(),
        "null_metrics_sha256": hashlib.sha256(null_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "start_prior_robust_mix.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
            )
        },
        "inference": "Development-only descriptive ranking; no confirmatory p-values or intervals. Null intervals are one-sided exact Clopper-Pearson with simultaneous 95% Bonferroni coverage over all 30 rho/scenario/query cells.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Robust fixed-mixture start-prior development screen",
        "",
        f"Selected development rho: **{selected_rho:.2f}** by the prespecified maximin onset/severity objective. This is a development selection, not a confirmation.",
        "",
        f"Alternative rows: {len(alternative)}; null rows: {len(null)}; generator device(s): {', '.join(sorted(resolved_devices))}.",
        "",
        "## Prior ranking",
        "",
        ranking.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Cellwise alternatives",
        "",
        cell_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null calibration",
        "",
        null_summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "A later comparison may use only the frozen selected rho and must use independent seeds. A convex mixture of valid e-processes has the stated validity under their shared null and filtration; the grid itself does not prove that null or establish novelty.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return alternative, ranking, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/start_prior_robust_mix_development")
    parser.add_argument("--streams-per-cell", type=int, default=500)
    parser.add_argument("--null-streams", type=int, default=1000)
    parser.add_argument("--alternative-seed-offset", type=int, default=20290000)
    parser.add_argument("--null-seed-offset", type=int, default=20291000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _alternative, ranking, manifest = run_start_prior_robust_mix(
        args.output_dir,
        StartPriorRobustMixConfig(
            streams_per_cell=args.streams_per_cell,
            null_streams=args.null_streams,
            alternative_seed_offset=args.alternative_seed_offset,
            null_seed_offset=args.null_seed_offset,
            device=args.device,
        ),
    )
    print(f"selected_rho={manifest['selected_rho_development_only']:.2f}")
    print(ranking.to_string(index=False))
    print(f"alternative_metrics_sha256={manifest['alternative_metrics_sha256']}")
    print(f"null_metrics_sha256={manifest['null_metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
