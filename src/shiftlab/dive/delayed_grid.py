"""Paired design grid for delayed decision-harm monitoring."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ..data.gpu.environment import environment
from .delayed_benchmark import (
    DELAY_SCHEMES,
    METHODS,
    SCENARIOS,
    DelayedBenchmarkConfig,
    simulate_cell,
)


@dataclass(frozen=True)
class DelayedGridConfig:
    """Exploratory factorial grid; no cell is used to claim confirmatory power."""

    seeds: int = 30
    seed_offset: int = 20262000
    n_source: int = 3000
    n_target: int = 3000
    query_rates: tuple[float, ...] = (0.10, 0.25, 0.50)
    harm_onset_fractions: tuple[float, ...] = (0.20, 0.60)
    harm_contrast_increases: tuple[float, ...] = (0.12, 0.24)
    delay_schemes: tuple[str, ...] = DELAY_SCHEMES
    alpha: float = 0.05
    materiality_margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    device: str = "cuda"

    def validate(self) -> DelayedGridConfig:
        if self.seeds < 1 or self.n_source < 100 or self.n_target < 100:
            raise ValueError("seeds must be positive and source/target lengths at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query_rates must be nonempty and lie in (0, 1]")
        if len(set(self.query_rates)) != len(self.query_rates):
            raise ValueError("query_rates must be unique")
        if not self.harm_onset_fractions or any(not 0 < x < 1 for x in self.harm_onset_fractions):
            raise ValueError("harm onset fractions must be nonempty and lie in (0, 1)")
        if not self.harm_contrast_increases or any(
            not 0 < effect <= 0.98 * self.amplitude for effect in self.harm_contrast_increases
        ):
            raise ValueError("harm contrast increases must produce sign probabilities at most 0.99")
        if not 0 < self.alpha < 1 or not 0 <= self.materiality_margin < 1:
            raise ValueError("alpha and materiality margin are invalid")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if not self.delay_schemes or any(x not in DELAY_SCHEMES for x in self.delay_schemes):
            raise ValueError("delay schemes must be a nonempty registered subset")
        if len(self.delay_schemes) < 2:
            raise ValueError("the design grid requires at least two delay schemes")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        return self

    def base_config(
        self, *, query_rate: float, onset: float, effect: float
    ) -> DelayedBenchmarkConfig:
        return DelayedBenchmarkConfig(
            seeds=self.seeds,
            seed_offset=self.seed_offset,
            n_source=self.n_source,
            n_target=self.n_target,
            query_rate=query_rate,
            alpha=self.alpha,
            materiality_margin=self.materiality_margin,
            harm_onset_fraction=onset,
            harm_contrast_increase=effect,
            amplitude=self.amplitude,
            benign_amplitude=self.benign_amplitude,
            delay_schemes=self.delay_schemes,
            scenarios=SCENARIOS,
            device=self.device,
        ).validate()


def _event_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize one delay copy only so reused seed streams are not double-counted."""
    reference_delay = frame.delay_scheme.iloc[0]
    event_frame = frame[frame.delay_scheme == reference_delay]
    return (
        event_frame.groupby(
            [
                "scenario",
                "query_rate",
                "harm_onset_fraction",
                "harm_contrast_increase",
                "method",
            ],
            dropna=False,
        )
        .agg(
            streams=("seed", "nunique"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            false_escalations=("false_escalation", "sum"),
            false_escalation_rate=("false_escalation", "mean"),
            median_event_delay=("event_detection_delay", "median"),
            mean_labels_queried=("labels_queried", "mean"),
            mean_labels_processed_at_alarm=("labels_processed_at_alarm", "mean"),
        )
        .reset_index()
    )


def _validate_delay_invariance(frame: pd.DataFrame) -> None:
    """Event-time outputs must be unchanged by delay when event order is preserved."""
    compare = [
        "scenario",
        "seed",
        "query_rate",
        "harm_onset_fraction",
        "harm_contrast_increase",
        "method",
    ]
    invariant = ["alarm_event", "detected", "false_escalation", "labels_processed_at_alarm"]
    if frame.groupby(compare, dropna=False)[invariant].nunique(dropna=False).to_numpy().max() != 1:
        raise RuntimeError("event-order monitoring produced delay-dependent event-time outcomes")


def run_grid(config: DelayedGridConfig, output_dir: str | Path) -> tuple[pd.DataFrame, dict]:
    """Run the full paired seed grid and save stream metrics plus an audit manifest."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cells = []
    for scenario in SCENARIOS:
        onset_values = config.harm_onset_fractions if scenario == "boundary_harm" else (0.4,)
        effect_values = config.harm_contrast_increases if scenario == "boundary_harm" else (0.24,)
        for onset in onset_values:
            for effect in effect_values:
                for query_rate in config.query_rates:
                    base = config.base_config(query_rate=query_rate, onset=onset, effect=effect)
                    for delay_scheme in config.delay_schemes:
                        for seed in range(config.seed_offset, config.seed_offset + config.seeds):
                            cells.extend(
                                simulate_cell(
                                    base,
                                    seed=seed,
                                    scenario=scenario,
                                    delay_scheme=delay_scheme,
                                )
                            )
    frame = pd.DataFrame(cells)
    _validate_delay_invariance(frame)
    metrics_path = output / "delayed_feedback_grid.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "delayed_feedback_grid.csv", index=False)
    event_summary = _event_summary(frame)
    event_summary.to_csv(output / "event_summary.csv", index=False)
    wall_summary = (
        frame.groupby(
            [
                "scenario",
                "delay_scheme",
                "query_rate",
                "harm_onset_fraction",
                "harm_contrast_increase",
                "method",
            ],
            dropna=False,
        )
        .agg(
            streams=("seed", "nunique"),
            median_wall_delay=("wall_detection_delay", "median"),
            p90_wall_delay=("wall_detection_delay", lambda x: x.quantile(0.9)),
            mean_pending_at_alarm=("pending_at_alarm", "mean"),
        )
        .reset_index()
    )
    wall_summary.to_csv(output / "wall_delay_summary.csv", index=False)
    current_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "generation_device": config.device,
        "resolved_generation_devices": sorted(frame.device.unique().tolist()),
        "environment": environment(),
        "scenarios": list(SCENARIOS),
        "delay_schemes": list(config.delay_schemes),
        "query_rates": list(config.query_rates),
        "harm_onset_fractions": list(config.harm_onset_fractions),
        "harm_contrast_increases": list(config.harm_contrast_increases),
        "methods": list(METHODS),
        "stream_cells": int(len(frame) / len(METHODS)),
        "metric_rows": len(frame),
        "event_time_invariance_across_delays": True,
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256((current_dir / name).read_bytes()).hexdigest()
            for name in (
                "delayed_grid.py",
                "delayed_benchmark.py",
                "delayed_feedback.py",
                "eprocess.py",
            )
        },
        "interpretation": (
            "Exploratory grid; no algorithm or hyperparameter selected on these outcomes. "
            "Repeated delay conditions reuse the same seeds and are not independent replications."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Delayed-feedback decision-harm design grid",
        "",
        "Exploratory paired-seed grid. It is not a confirmatory analysis and no method was selected",
        f"from these results. Event-time summaries use only the `{config.delay_schemes[0]}` copy for each seed; the",
        "grid verifies that event-time outputs are invariant across independent delay schedules when",
        "the buffer releases evidence in event order. Wall-time results retain both delay schemes.",
        "",
        f"- Seeds: `{config.seed_offset}`–`{config.seed_offset + config.seeds - 1}`.",
        f"- Query rates: `{', '.join(map(str, config.query_rates))}`.",
        f"- Harm onset fractions: `{', '.join(map(str, config.harm_onset_fractions))}`.",
        f"- Expected paired-cost increases: `{', '.join(map(str, config.harm_contrast_increases))}`.",
        f"- Delay schemes: `{', '.join(config.delay_schemes)}`; method comparisons share stream outcomes and queried labels.",
        f"- Stream cells: `{manifest['stream_cells']}`; method rows: `{manifest['metric_rows']}`.",
        f"- CUDA availability: `{manifest['environment']['cuda_available']}`; resolved generation device(s): `{', '.join(manifest['resolved_generation_devices'])}`.",
        "",
        "## Event-time outcomes (one delay copy per seed)",
        "",
        event_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Wall-time delay outcomes",
        "",
        wall_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Interpretation limits",
        "",
        "The eventwise e-process assumes its known increment bound and conditional-mean null. The",
        "source/target risk-CS comparator uses the independent bounded source sample and target",
        "CM-EB lower sequence described in `delayed_feedback_protocol.md`; it is not a faithful full",
        "reproduction of Podkopaev–Ramdas. The two procedures test different nulls. Query selection",
        "and delays are independent of outcomes in this simulation. Results do not establish familywise",
        "power across this grid or nominal false-alarm control: the null cells have only the configured",
        "development seed count. Confirmation requires independent null calibration and disjoint",
        "alternative seeds. No figure is included because PaperBanana is not available as a callable",
        "tool in this session and project guidance requires it for visuals.",
        "",
        "## Files",
        "",
        "- `delayed_feedback_grid.parquet` / `.csv`: stream-level metrics.",
        "- `event_summary.csv`: event-time results without counting delay copies twice.",
        "- `wall_delay_summary.csv`: latency by delay scheme.",
        "- `manifest.json`: configuration, environment, invariance check and hashes.",
        f"- Metrics SHA-256: `{manifest['metrics_sha256']}`.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return frame, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/delayed_feedback_grid_development")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n-source", type=int, default=3000)
    parser.add_argument("--n-target", type=int, default=3000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = DelayedGridConfig(
        seeds=args.seeds,
        n_source=args.n_source,
        n_target=args.n_target,
        device=args.device,
    )
    frame, manifest = run_grid(config, args.output_dir)
    print(f"stream_cells={manifest['stream_cells']} rows={len(frame)}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
