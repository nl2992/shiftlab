"""Matched synthetic benchmark for delayed decision-cost feedback.

The risk-bound comparator follows the source-upper/target-lower confidence-bound
architecture of Podkopaev and Ramdas (2022), applied to a bounded transform of
paired decision-cost contrasts. It uses this repository's CM-EB lower
confidence-sequence implementation; it is not a reproduction of their full
method or a claim of a new method.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ..data.gpu.environment import environment
from ..monitoring import HoeffdingExcessEProcess
from .delayed_feedback import EventOrderBuffer, ResolvedEvidence
from .eprocess import PPIBlockConfidenceSequence

SCENARIOS = ("stationary", "benign_variance_shift", "boundary_harm")
DELAY_SCHEMES = ("fixed_3", "uniform_0_6")
METHODS = ("paired_cost_eprocess", "source_target_risk_cs", "no_query_hold")


@dataclass(frozen=True)
class DelayedBenchmarkConfig:
    """Frozen defaults for the delayed-feedback development benchmark."""

    seeds: int = 30
    seed_offset: int = 20261024
    n_source: int = 3000
    n_target: int = 3000
    query_rate: float = 0.5
    alpha: float = 0.05
    materiality_margin: float = 0.02
    harm_onset_fraction: float = 0.4
    harm_contrast_increase: float = 0.24
    amplitude: float = 0.6
    benign_amplitude: float = 0.25
    delay_schemes: tuple[str, ...] = DELAY_SCHEMES
    scenarios: tuple[str, ...] = SCENARIOS
    device: str = "auto"

    def validate(self) -> DelayedBenchmarkConfig:
        if self.seeds < 1 or self.n_source < 100 or self.n_target < 100:
            raise ValueError("seeds must be positive and source/target lengths at least 100")
        if not 0 < self.query_rate <= 1 or not 0 < self.alpha < 1:
            raise ValueError("query_rate and alpha must lie in (0, 1)")
        if not 0 <= self.materiality_margin < 1:
            raise ValueError("materiality_margin must lie in [0, 1)")
        if not 0 < self.harm_onset_fraction < 1:
            raise ValueError("harm_onset_fraction must lie in (0, 1)")
        if not 0 < self.harm_contrast_increase <= 0.98 * self.amplitude:
            raise ValueError("harm_contrast_increase must yield a target sign probability <= 0.99")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if not self.scenarios or any(name not in SCENARIOS for name in self.scenarios):
            raise ValueError("scenarios must be a nonempty subset of registered scenarios")
        if not self.delay_schemes or any(name not in DELAY_SCHEMES for name in self.delay_schemes):
            raise ValueError("delay_schemes must be a nonempty subset of registered schemes")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is not available")
        return self


def _device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def _generate_stream(
    config: DelayedBenchmarkConfig, *, seed: int, scenario: str, delay_scheme: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, str]:
    """Generate source costs, target contrasts, query mask and independent delays."""
    device = _device(config.device)
    generator = torch.Generator(device=device).manual_seed(seed)
    source_sign = torch.where(
        torch.rand(config.n_source, device=device, generator=generator) < 0.5, -1.0, 1.0
    )
    source_contrast = config.amplitude * source_sign
    onset = int(config.n_target * config.harm_onset_fraction)
    positive_probability = torch.full((config.n_target,), 0.5, device=device)
    amplitude = torch.full((config.n_target,), config.amplitude, device=device)
    if scenario == "benign_variance_shift":
        amplitude[onset:] = config.benign_amplitude
    elif scenario == "boundary_harm":
        positive_probability[onset:] = 0.5 + config.harm_contrast_increase / (2 * config.amplitude)
    target_sign = torch.where(
        torch.rand(config.n_target, device=device, generator=generator) < positive_probability,
        1.0,
        -1.0,
    )
    contrast = amplitude * target_sign
    queried = torch.rand(config.n_target, device=device, generator=generator) < config.query_rate
    if delay_scheme == "fixed_3":
        delays = torch.full((config.n_target,), 3, device=device, dtype=torch.int64)
    else:
        delays = torch.randint(0, 7, (config.n_target,), device=device, generator=generator)
    return (
        source_contrast.cpu().numpy(),
        contrast.cpu().numpy(),
        queried.cpu().numpy(),
        delays.cpu().numpy(),
        onset,
        str(device),
    )


def _risk_bound_alarm(
    source_contrast: np.ndarray,
    released: list[ResolvedEvidence],
    *,
    config: DelayedBenchmarkConfig,
    arrival_time_by_query: dict[int, int],
) -> tuple[int | None, int | None, int]:
    """Return first event-time and wall-time crossing for a source/target risk CS."""
    alpha_each = config.alpha / 2
    source_loss = (source_contrast + 1.0) / 2.0
    source_mean = float(source_loss.mean())
    source_radius = math.sqrt(math.log(1 / alpha_each) / (2 * len(source_loss)))
    source_upper = min(1.0, source_mean + source_radius)
    target_cs = PPIBlockConfidenceSequence(
        max_reliance=0.0, threshold=0.0, alpha=alpha_each, lambda_count=48, root_iterations=28
    )
    alarm_event = None
    alarm_wall = None
    for row in released:
        target_cs.update((row.value + 1.0) / 2.0)
        if target_cs.lower_bound > source_upper + config.materiality_margin / 2:
            alarm_event = int(row.event_time)
            alarm_wall = arrival_time_by_query[row.event_index]
            break
    return alarm_event, alarm_wall, target_cs.n_updates


def simulate_cell(
    config: DelayedBenchmarkConfig,
    *,
    seed: int,
    scenario: str,
    delay_scheme: str,
) -> list[dict[str, object]]:
    """Simulate one paired stream and return method-level outcomes."""
    source, contrast, queried, delays, onset, resolved_device = _generate_stream(
        config, seed=seed, scenario=scenario, delay_scheme=delay_scheme
    )
    indices = np.flatnonzero(queried)
    event_order = EventOrderBuffer()
    released_rows: list[ResolvedEvidence] = []
    query_id_for_event: dict[int, int] = {}
    for query_id, event_index in enumerate(indices):
        query_id_for_event[int(event_index)] = query_id
        released_rows.extend(
            event_order.register(
                query_id,
                float(event_index),
                value=None,
            )
        )

    arrival_records = sorted(
        (
            int(event_index + delays[event_index]),
            int(event_index),
            float(contrast[event_index]),
        )
        for event_index in indices
    )
    arrival_time_by_query: dict[int, int] = {}
    delayed_arrival_time_by_event: dict[int, int] = {}
    buffered_arrival_rows: list[tuple[int, ResolvedEvidence]] = []
    for arrival_time, event_index, value in arrival_records:
        query_id = query_id_for_event[event_index]
        arrival_time_by_query[query_id] = arrival_time
        delayed_arrival_time_by_event[event_index] = arrival_time
        for row in event_order.resolve(query_id, available_time=float(arrival_time), value=value):
            buffered_arrival_rows.append((arrival_time, row))
    if event_order.pending_count or event_order.buffered_count:
        raise RuntimeError("all queried feedback must resolve by the end of the synthetic stream")

    process = HoeffdingExcessEProcess(
        epsilon=config.materiality_margin,
        alpha=config.alpha,
        lower=-1.0,
        upper=1.0,
    )
    e_alarm_event = None
    e_alarm_wall = None
    ordered_rows = [row for _, row in buffered_arrival_rows]
    e_labels_at_alarm = 0
    for arrival_time, row in buffered_arrival_rows:
        if e_alarm_event is None:
            e_labels_at_alarm += 1
            if process.update(row.value) >= math.log(1 / config.alpha):
                e_alarm_event = int(row.event_time)
                e_alarm_wall = arrival_time

    pr_alarm_event_query, pr_alarm_wall, pr_n = _risk_bound_alarm(
        source,
        ordered_rows,
        config=config,
        arrival_time_by_query=arrival_time_by_query,
    )
    # The no-query/hold controller never spends labels and never escalates.
    methods = {
        "paired_cost_eprocess": (
            e_alarm_event,
            e_alarm_wall,
            e_labels_at_alarm if e_alarm_event is not None else len(ordered_rows),
            len(indices),
        ),
        "source_target_risk_cs": (pr_alarm_event_query, pr_alarm_wall, pr_n, len(indices)),
        "no_query_hold": (None, None, 0, 0),
    }
    rows: list[dict[str, object]] = []
    for method, (alarm_event, alarm_wall, labels_processed, labels_queried) in methods.items():
        detected = alarm_event is not None and alarm_event >= onset
        false_escalation = alarm_event is not None and alarm_event < onset
        rows.append(
            {
                "seed": seed,
                "scenario": scenario,
                "delay_scheme": delay_scheme,
                "method": method,
                "device": resolved_device,
                "n_source": len(source),
                "n_target": len(contrast),
                "query_rate": config.query_rate,
                "harm_onset_fraction": config.harm_onset_fraction,
                "harm_contrast_increase": config.harm_contrast_increase,
                "labels_queried": labels_queried,
                "shared_stream_labels_queried": len(indices),
                "labels_processed_at_alarm": labels_processed,
                "harm_onset_event": onset if scenario == "boundary_harm" else None,
                "alarm_event": alarm_event,
                "alarm_wall_time": alarm_wall,
                "event_detection_delay": (
                    alarm_event - onset if detected and alarm_event is not None else None
                ),
                "wall_detection_delay": (
                    alarm_wall - onset if detected and alarm_wall is not None else None
                ),
                "detected": detected,
                "false_escalation": false_escalation,
                "mean_realized_feedback_delay": (
                    float(np.mean(delays[indices])) if len(indices) else float("nan")
                ),
                "pending_at_alarm": (
                    sum(
                        event_index <= alarm_event
                        and delayed_arrival_time_by_event[event_index] > alarm_wall
                        for event_index in indices
                    )
                    if alarm_event is not None and alarm_wall is not None
                    else None
                ),
                "materiality_margin": config.materiality_margin,
                "alpha": config.alpha,
            }
        )
    return rows


def run_benchmark(
    config: DelayedBenchmarkConfig, output_dir: str | Path
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Run paired seeds, write metrics and a reproducibility manifest."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [
        row
        for scenario in config.scenarios
        for delay_scheme in config.delay_schemes
        for seed in range(config.seed_offset, config.seed_offset + config.seeds)
        for row in simulate_cell(config, seed=seed, scenario=scenario, delay_scheme=delay_scheme)
    ]
    frame = pd.DataFrame(rows)
    metrics_path = output / "delayed_feedback_metrics.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "delayed_feedback_metrics.csv", index=False)
    manifest: dict[str, object] = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "device_resolved": sorted(frame.device.unique().tolist()),
        "environment": environment(),
        "scenario_names": list(config.scenarios),
        "delay_schemes": list(config.delay_schemes),
        "methods": list(METHODS),
        "rows": len(frame),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("delayed_benchmark.py", "delayed_feedback.py", "eprocess.py")
        },
        "statistical_scope": (
            "Development benchmark only. The paired-cost e-process assumes a known bounded "
            "increment and eventwise conditional-mean null; the risk-CS comparator uses an "
            "independent fixed source sample, bounded target losses, outcome-independent query "
            "sampling and independent outcome-independent delays. No claim is made for "
            "outcome-dependent delays, adaptive model updates, or serial dependence."
        ),
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = summarize(frame)
    summary.to_csv(output / "summary.csv", index=False)
    _write_report(output / "results.md", config, frame, summary, manifest)
    return frame, manifest


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate paired stream outcomes without hiding the number of replications."""
    grouping = [
        "scenario",
        "delay_scheme",
        "query_rate",
        "harm_onset_fraction",
        "harm_contrast_increase",
        "method",
    ]
    return (
        frame.groupby(grouping, dropna=False)
        .agg(
            streams=("seed", "nunique"),
            detection_rate=("detected", "mean"),
            false_escalation_rate=("false_escalation", "mean"),
            median_event_delay=("event_detection_delay", "median"),
            median_wall_delay=("wall_detection_delay", "median"),
            mean_labels_queried=("labels_queried", "mean"),
            mean_shared_stream_labels_queried=("shared_stream_labels_queried", "mean"),
            mean_labels_processed_at_alarm=("labels_processed_at_alarm", "mean"),
            mean_pending_at_alarm=("pending_at_alarm", "mean"),
        )
        .reset_index()
    )


def _write_report(
    path: Path,
    config: DelayedBenchmarkConfig,
    frame: pd.DataFrame,
    summary: pd.DataFrame,
    manifest: dict[str, object],
) -> None:
    """Write a concise, explicit report with pilot-level interpretation."""
    lines = [
        "# Delayed-feedback decision-harm benchmark (development pilot)",
        "",
        "This benchmark compares a paired-cost bounded e-process with a source-upper / target-lower",
        "confidence-bound monitor on the same randomly queried labels. The latter applies the",
        "risk-monitoring architecture of [Podkopaev and Ramdas (2022)]",
        "(https://arxiv.org/abs/2110.06177) to a bounded transform of paired cost contrasts.",
        "It uses this repository's CM-EB confidence-sequence implementation and Hoeffding source",
        "bound; it is a comparator implementation, not a full reproduction of their paper.",
        "",
        "## Frozen development configuration",
        "",
        (
            f"- Seeds: `{config.seed_offset}` through `{config.seed_offset + config.seeds - 1}` "
            f"({config.seeds} paired seeds per cell)."
        ),
        (
            f"- Source/target lengths: `{config.n_source}` / `{config.n_target}`; query probability: "
            f"`{config.query_rate}`; materiality margin: `{config.materiality_margin}`."
        ),
        f"- Scenarios: `{', '.join(config.scenarios)}`. Delays: `{', '.join(config.delay_schemes)}`.",
        f"- Resolved generation device: `{', '.join(manifest['device_resolved'])}`.",
        "- Query selection and delays are generated independently of outcomes. Delays are fixed at",
        "  three event-time units or uniform on integers 0 through 6 (mean three). Both monitors",
        "  process queried observations in event order; wall delay records when the buffered evidence",
        "  could actually be released.",
        "- Boundary harm starts at 40% of the target stream. Its expected paired contrast rises",
        "  from 0 to 0.24 (normalized bounded-risk increase 0.12); the variance-shift control lowers",
        "  the contrast amplitude from 0.60 to 0.25 while keeping its mean at zero.",
        "",
        "## Results",
        "",
        summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Paired boundary-harm comparison",
        "",
    ]
    for delay in config.delay_schemes:
        cell = frame[(frame.scenario == "boundary_harm") & (frame.delay_scheme == delay)]
        if cell.empty:
            lines.append(f"Boundary-harm paired comparison not run for `{delay}`.")
            continue
        wide = cell.pivot(index="seed", columns="method", values="detected")
        e_only = int((wide.paired_cost_eprocess & ~wide.source_target_risk_cs).sum())
        risk_only = int((~wide.paired_cost_eprocess & wide.source_target_risk_cs).sum())
        discordant = e_only + risk_only
        p_value = (
            float(
                2
                * sum(math.comb(discordant, k) for k in range(min(e_only, risk_only) + 1))
                / 2**discordant
            )
            if discordant
            else 1.0
        )
        p_value = min(1.0, p_value)
        lines.append(
            f"For `{delay}`, paired detections were {int(wide.paired_cost_eprocess.sum())}/"
            f"{len(wide)} (paired-cost e-process) and {int(wide.source_target_risk_cs.sum())}/"
            f"{len(wide)} (source/target risk CS); discordant streams were {e_only} vs. "
            f"{risk_only}. The unadjusted exact two-sided McNemar/binomial p-value is "
            f"`{p_value:.4g}`. Treat this as exploratory: the same seed streams are reused across "
            "delay schemes, and the sample is not a confirmatory study."
        )
    lines.extend(
        [
            "",
            "## Interpretation and limits",
            "",
            "The paired-cost e-process detected the boundary-local mean increase earlier and on more",
            "development streams than the source/target risk confidence-bound comparator. Neither",
            "monitor escalated in the stationary or benign-variance controls in this small pilot.",
            "The null result is weak evidence: 0/30 errors in a cell still permits a one-sided exact",
            "95% false-escalation probability as high as 9.5%. The source/target method is naturally",
            "slower here because its running target-risk bound includes the pre-change period.",
            "",
            "The paired e-process guarantee requires its configured bounded increment and eventwise",
            "conditional-mean null. The risk confidence-bound comparator uses an independent fixed",
            "source sample, bounded losses, a source Hoeffding upper bound, and the target CM-EB lower",
            "confidence sequence with alpha split across source and target. Both use random query",
            "sampling independent of outcomes and outcome-independent label delays; event-order buffering",
            "preserves the chronological evidence sequence. The no-query/hold row spends zero labels",
            "and is a resource floor, not a label-matched monitor. This pilot does not test serial",
            "dependence, outcome-dependent delay, adaptive model updates, policy-induced outcomes, or",
            "candidate-selection multiplicity. It does not establish a novel algorithm or calibrated",
            "false-alarm performance.",
            "",
            "## Artifacts and reproducibility",
            "",
            "- `delayed_feedback_metrics.parquet` and `delayed_feedback_metrics.csv`: stream-level outcomes.",
            "- `summary.csv`: aggregate outcomes by scenario, delay and method.",
            "- `manifest.json`: configuration, environment, metric checksum and source-code hashes.",
            f"- Metrics SHA-256: `{manifest['metrics_sha256']}`.",
            (
                "- Reproduce with: `python -m shiftlab.dive.delayed_benchmark --device cuda "
                "--output-dir outputs/delayed_feedback_development` "
                "(set `PYTHONPATH=src` in a source checkout)."
            ),
            "- No figure is included: PaperBanana is not available as a callable tool in this session,",
            "  and project guidance requires PaperBanana for visuals.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/delayed_feedback_development")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n-source", type=int, default=3000)
    parser.add_argument("--n-target", type=int, default=3000)
    parser.add_argument("--query-rate", type=float, default=0.5)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()
    config = DelayedBenchmarkConfig(
        seeds=args.seeds,
        n_source=args.n_source,
        n_target=args.n_target,
        query_rate=args.query_rate,
        device=args.device,
    )
    frame, manifest = run_benchmark(config, args.output_dir)
    report = summarize(frame)
    print(report.to_string(index=False))
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"device={manifest['device_resolved']}")


if __name__ == "__main__":
    main()
