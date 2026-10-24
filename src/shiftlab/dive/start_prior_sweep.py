"""Development-only screen of fixed start-time priors for e-process mixtures."""

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
from scipy.special import betainc

from ..data.gpu.environment import environment
from .delayed_benchmark import DelayedBenchmarkConfig, _generate_stream
from .delayed_calibration import _first_crossing, _restart_log_e_values, calibration_alarm_indices

QUERY_RATES = (0.10, 0.25, 0.50)
ONSETS = (0.20, 0.60)
HARM_INCREASES = (0.12, 0.24)
PRIOR_SHAPES = {
    "uniform_beta_1_1": (1.0, 1.0),
    "early_beta_1_2": (1.0, 2.0),
    "late_beta_2_1": (2.0, 1.0),
    "center_beta_2_2": (2.0, 2.0),
    "edge_beta_half_half": (0.5, 0.5),
}


def beta_start_weights(a: float, b: float, components: int = 8) -> tuple[float, ...]:
    """Assign fixed prior mass to equal-width start-time bins under Beta(a,b)."""
    if not np.isfinite(a) or not np.isfinite(b) or a <= 0 or b <= 0 or components < 1:
        raise ValueError("beta shapes and component count must be positive and finite")
    edges = np.linspace(0.0, 1.0, components + 1)
    weights = np.diff(betainc(a, b, edges))
    weights /= weights.sum()
    return tuple(float(weight) for weight in weights)


@dataclass(frozen=True)
class StartPriorSweepConfig:
    """Paired alternative development grid; never used for final inference."""

    seeds: int = 30
    seed_offset: int = 20262000
    n_events: int = 3000
    query_rates: tuple[float, ...] = QUERY_RATES
    harm_onsets: tuple[float, ...] = ONSETS
    harm_increases: tuple[float, ...] = HARM_INCREASES
    delay_scheme: str = "fixed_3"
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    device: str = "cuda"

    def validate(self) -> StartPriorSweepConfig:
        if self.seeds < 1 or self.n_events < 100:
            raise ValueError("seeds must be positive and n_events at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query_rates must be nonempty and in (0, 1]")
        if not self.harm_onsets or any(not 0 < onset < 1 for onset in self.harm_onsets):
            raise ValueError("harm_onsets must be nonempty and in (0, 1)")
        if not self.harm_increases or any(
            not 0 < effect <= 0.98 * self.amplitude for effect in self.harm_increases
        ):
            raise ValueError("harm increases must yield positive probabilities at most 0.99")
        if self.delay_scheme not in {"fixed_3", "uniform_0_6"}:
            raise ValueError("delay_scheme must be fixed_3 or uniform_0_6")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu or cuda")
        return self


def run_start_prior_sweep(
    output_dir: str | Path, config: StartPriorSweepConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run the paired development screen and select a prior by macro cell power."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cells = list(itertools.product(config.query_rates, config.harm_onsets, config.harm_increases))
    rows: list[dict[str, object]] = []
    resolved_devices: set[str] = set()
    weights_by_prior = {name: beta_start_weights(*shape) for name, shape in PRIOR_SHAPES.items()}
    for query_rate, onset_fraction, harm_increase in cells:
        benchmark_config = DelayedBenchmarkConfig(
            seeds=config.seeds,
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
        expected_horizon = max(1, round(config.n_events * query_rate))
        starts = tuple(sorted({round(expected_horizon * index / 8) for index in range(8)}))
        for seed in range(config.seed_offset, config.seed_offset + config.seeds):
            _source, contrast, queried, delays, onset, resolved_device = _generate_stream(
                benchmark_config,
                seed=seed,
                scenario="boundary_harm",
                delay_scheme=config.delay_scheme,
            )
            resolved_devices.add(resolved_device)
            event_indices = np.flatnonzero(queried)
            arrival_times = event_indices + delays[event_indices]
            shared = calibration_alarm_indices(
                contrast[event_indices],
                event_indices,
                arrival_times,
                query_rate=query_rate,
                n_events=config.n_events,
                margin=config.margin,
                alpha=config.alpha,
                amplitude=config.amplitude,
            )
            alarm_events = {
                "full_stream_betting": shared["paired_cost_betting"][0],
                "uniform_beta_1_1": shared["restart_mixture_8"][0],
            }
            for name, weights in weights_by_prior.items():
                centered = contrast[event_indices] - config.margin
                bound = config.amplitude + config.margin + 1e-6
                log_e = _restart_log_e_values(
                    centered,
                    bound=bound,
                    starts=starts,
                    start_weights=weights,
                )
                crossing = _first_crossing(log_e, np.log(1 / config.alpha))
                alarm_events[name] = int(event_indices[crossing]) if crossing is not None else None
            # Uniform Beta is already the canonical equal-weight component mixture.
            for method, alarm_event in alarm_events.items():
                if alarm_event is None:
                    alarm_wall = None
                else:
                    processed = int(np.searchsorted(event_indices, alarm_event, side="right"))
                    alarm_wall = int(np.maximum.accumulate(arrival_times)[processed - 1])
                detected = alarm_event is not None and alarm_event >= onset
                rows.append(
                    {
                        "seed": seed,
                        "query_rate": query_rate,
                        "harm_onset_fraction": onset_fraction,
                        "harm_contrast_increase": harm_increase,
                        "scenario": "boundary_harm",
                        "delay_scheme": config.delay_scheme,
                        "method": method,
                        "device": resolved_device,
                        "n_events": config.n_events,
                        "labels_queried": len(event_indices),
                        "labels_processed_at_alarm_or_end": (
                            int(np.searchsorted(event_indices, alarm_event, side="right"))
                            if alarm_event is not None
                            else len(event_indices)
                        ),
                        "harm_onset_event": onset,
                        "alarm_event": alarm_event,
                        "alarm_wall_time": alarm_wall,
                        "detected": detected,
                        "false_escalation": alarm_event is not None and alarm_event < onset,
                        "event_detection_delay": alarm_event - onset if detected else None,
                        "wall_detection_delay": alarm_wall - onset if detected else None,
                    }
                )
    frame = pd.DataFrame(rows)
    group_cols = ["query_rate", "harm_onset_fraction", "harm_contrast_increase", "method"]
    summary = (
        frame.groupby(group_cols, sort=True)
        .agg(
            detected=("detected", "sum"),
            streams=("detected", "size"),
            detection_rate=("detected", "mean"),
            mean_event_delay_given_detection=("event_detection_delay", "mean"),
            mean_wall_delay_given_detection=("wall_detection_delay", "mean"),
            false_escalations_before_onset=("false_escalation", "sum"),
        )
        .reset_index()
    )
    ranking = (
        summary.groupby("method", sort=True)
        .agg(
            macro_cell_detection=("detection_rate", "mean"),
            worst_cell_detection=("detection_rate", "min"),
            best_cell_detection=("detection_rate", "max"),
            mean_pre_onset_escalations=("false_escalations_before_onset", "mean"),
        )
        .sort_values(
            ["macro_cell_detection", "worst_cell_detection"],
            ascending=False,
            kind="stable",
        )
        .reset_index()
    )
    # The first row is selected only for the next independent validation/calibration stage.
    selected_prior = str(ranking.iloc[0].method)
    metrics_path = output / "start_prior_development.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "start_prior_development.csv", index=False)
    summary.to_csv(output / "cell_summary.csv", index=False)
    ranking.to_csv(output / "prior_ranking.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "environment": environment(),
        "resolved_devices": sorted(resolved_devices),
        "seed_interval": [config.seed_offset, config.seed_offset + config.seeds - 1],
        "factorial_cells": len(cells),
        "seeds_per_cell": config.seeds,
        "metric_rows": len(frame),
        "start_prior_weights": {name: list(weights) for name, weights in weights_by_prior.items()},
        "selection_rule": (
            "Highest unweighted mean detection rate across the registered alternative cells; "
            "ties use higher worst-cell detection. This is development-only selection."
        ),
        "selected_prior_for_fresh_validation": selected_prior,
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((module_dir / name).read_bytes()).hexdigest()
            for name in (
                "start_prior_sweep.py",
                "delayed_calibration.py",
                "delayed_benchmark.py",
                "eprocess.py",
            )
        },
        "mathematical_scope": (
            "Every candidate uses a fixed, pre-stream convex weight vector over valid e-process "
            "components. Its mixture remains an e-process under the same filtration. Weight selection "
            "uses only the development alternatives and is not evidence of confirmatory power."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = [
        "# Fixed start-time prior development screen",
        "",
        "This development-only screen compares fixed Beta-distributed priors over eight prescribed",
        "start-time bins. Every method receives paired outcomes, queries and delays within each seed.",
        "Candidate priors are fixed before each stream; changing the prior between streams does not",
        "affect the component e-process guarantees. No confirmatory inference is performed here.",
        "",
        f"- Seed interval: {config.seed_offset}–{config.seed_offset + config.seeds - 1}.",
        f"- Cells: {len(cells)}; seeds per cell: {config.seeds}; resolved device: {', '.join(sorted(resolved_devices))}.",
        f"- Selection rule: {manifest['selection_rule']}",
        f"- Selected prior for fresh validation: {selected_prior}",
        "",
        ranking.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Cell-level power and delay are in cell_summary.csv; per-stream outcomes are in",
        "start_prior_development.parquet and start_prior_development.csv. The selected prior remains",
        "a development candidate until it passes fresh null calibration and a disjoint alternative test.",
        "No figure is included because project guidance requires PaperBanana for visuals and that tool",
        "is unavailable in this session.",
        "",
    ]
    (output / "results.md").write_text("\n".join(lines), encoding="utf-8")
    return frame, ranking, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/start_prior_development")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20262000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = StartPriorSweepConfig(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
    )
    _frame, ranking, manifest = run_start_prior_sweep(args.output_dir, config)
    print(ranking.to_string(index=False))
    print(f"selected_prior={manifest['selected_prior_for_fresh_validation']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
