"""Frozen disjoint-seed confirmation for delayed paired-cost monitoring."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from ..data.gpu.environment import environment
from .delayed_benchmark import DelayedBenchmarkConfig, _generate_stream
from .delayed_calibration import (
    CALIBRATION_METHODS,
    _exact_interval,
    calibration_alarm_indices,
)


def run_confirmation(
    output_dir: str | Path,
    *,
    device: str = "cuda",
    seeds: int = 2000,
    seed_offset: int = 20266000,
) -> tuple[pd.DataFrame, dict]:
    """Run the preregistered primary alternative on seeds disjoint from development/calibration."""
    config = DelayedBenchmarkConfig(
        seeds=seeds,
        seed_offset=seed_offset,
        n_source=3000,
        n_target=3000,
        query_rate=0.25,
        harm_onset_fraction=0.60,
        harm_contrast_increase=0.12,
        delay_schemes=("uniform_0_6",),
        scenarios=("boundary_harm",),
        device=device,
    ).validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    resolved_devices = set()
    for seed in range(config.seed_offset, config.seed_offset + config.seeds):
        _source, contrast, queried, delays, onset, resolved_device = _generate_stream(
            config,
            seed=seed,
            scenario="boundary_harm",
            delay_scheme="uniform_0_6",
        )
        resolved_devices.add(resolved_device)
        event_indices = np.flatnonzero(queried)
        alarms = calibration_alarm_indices(
            contrast[event_indices],
            event_indices,
            event_indices + delays[event_indices],
            query_rate=config.query_rate,
            n_events=config.n_target,
            margin=config.materiality_margin,
            alpha=config.alpha,
            amplitude=config.amplitude,
        )
        for method, (alarm_event, alarm_wall) in alarms.items():
            detected = alarm_event is not None and alarm_event >= onset
            rows.append(
                {
                    "seed": seed,
                    "scenario": "boundary_harm",
                    "delay_scheme": "uniform_0_6",
                    "method": method,
                    "device": resolved_device,
                    "n_target": config.n_target,
                    "query_rate": config.query_rate,
                    "harm_onset_fraction": config.harm_onset_fraction,
                    "harm_contrast_increase": config.harm_contrast_increase,
                    "labels_queried": len(event_indices),
                    "labels_processed_at_alarm": (
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
                    "pending_at_alarm": (
                        int(
                            (
                                (event_indices <= alarm_event)
                                & (event_indices + delays[event_indices] > alarm_wall)
                            ).sum()
                        )
                        if alarm_event is not None and alarm_wall is not None
                        else None
                    ),
                    "materiality_margin": config.materiality_margin,
                    "alpha": config.alpha,
                }
            )
    frame = pd.DataFrame(rows)
    pivot = frame.pivot(index="seed", columns="method", values="detected")
    comparisons = []
    for method in CALIBRATION_METHODS:
        successes = int(pivot[method].sum())
        lower, upper = _exact_interval(successes, len(pivot))
        comparisons.append(
            {
                "method": method,
                "detected": successes,
                "streams": len(pivot),
                "detection_rate": successes / len(pivot),
                "cp95_lower": lower,
                "cp95_upper": upper,
                "mean_labels_processed_at_alarm_or_end": float(
                    frame.loc[frame.method == method, "labels_processed_at_alarm"].mean()
                ),
                "mean_event_delay_detected": float(
                    frame.loc[
                        (frame.method == method) & frame.detected, "event_detection_delay"
                    ].mean()
                ),
                "mean_wall_delay_detected": float(
                    frame.loc[
                        (frame.method == method) & frame.detected, "wall_detection_delay"
                    ].mean()
                ),
            }
        )
    summary = pd.DataFrame(comparisons)

    restart_only = int((pivot.restart_mixture_8 & ~pivot.paired_cost_betting).sum())
    betting_only = int((~pivot.restart_mixture_8 & pivot.paired_cost_betting).sum())
    discordant = restart_only + betting_only
    p_value = float(binomtest(restart_only, discordant, p=0.5).pvalue) if discordant else 1.0
    primary = {
        "contrast": "restart_mixture_8 versus paired_cost_betting",
        "restart_only_detections": restart_only,
        "betting_only_detections": betting_only,
        "discordant_pairs": discordant,
        "mcnemar_exact_two_sided_p": p_value,
    }
    summary_path = output / "confirmation_summary.csv"
    summary.to_csv(summary_path, index=False)
    (output / "primary_paired_test.json").write_text(
        json.dumps(primary, indent=2), encoding="utf-8"
    )
    metrics_path = output / "confirmation_metrics.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "confirmation_metrics.csv", index=False)
    resolved = sorted(resolved_devices)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "environment": environment(),
        "resolved_devices": resolved,
        "metric_rows": len(frame),
        "seed_interval": [config.seed_offset, config.seed_offset + config.seeds - 1],
        "primary_test": primary,
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "code_sha256": {
            "delayed_confirmation.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "delayed_calibration.py": hashlib.sha256(
                Path(__file__).with_name("delayed_calibration.py").read_bytes()
            ).hexdigest(),
            "delayed_benchmark.py": hashlib.sha256(
                Path(__file__).with_name("delayed_benchmark.py").read_bytes()
            ).hexdigest(),
        },
        "inference_scope": (
            "The restart-versus-full-stream detection comparison is the single registered primary "
            "two-sided exact paired McNemar test. Other method detection rates and delay summaries "
            "are descriptive secondary comparisons. This confirmation covers only the registered "
            "synthetic boundary-harm condition and its eventwise conditional-mean null."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = [
        "# Delayed decision-harm alternative confirmation",
        "",
        "This independent confirmation tests the frozen primary comparison registered after null",
        "calibration. It uses 2,000 paired seeds, late-onset weaker harm (onset 0.60, expected paired",
        "contrast increase 0.12), a 0.25 query probability, and independent uniform delays 0–6.",
        "All methods receive the same outcomes, query masks and delay stream within each seed.",
        "",
        f"- Seed interval: `{config.seed_offset}`–`{config.seed_offset + config.seeds - 1}`.",
        f"- Resolved generation device: `{', '.join(resolved)}`.",
        "- Primary paired test: exact two-sided McNemar test of restart mixture versus full-stream betting.",
        f"- Discordant pairs, restart-only / betting-only: `{restart_only}` / `{betting_only}`.",
        f"- Primary exact p-value: `{p_value:.6g}`.",
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The exact marginal intervals do not replace the paired primary test. Delay summaries are",
        "conditional on detection; nondetections remain censored and are not assigned a numeric delay.",
        "The source/target risk-CS comparator is excluded because it tests a different running-risk null.",
        "The experiment establishes behavior only in this independent synthetic design; it does not",
        "validate outcome-dependent delay, serial dependence, adaptive model updates, or real-data",
        "assumptions. No algorithmic novelty is claimed.",
        "",
        "Stream metrics, paired analysis, summary and manifest are all in this directory. No figure",
        "is included because project guidance requires PaperBanana for visuals, and that tool is",
        "unavailable here.",
        "",
    ]
    (output / "results.md").write_text("\n".join(lines), encoding="utf-8")
    return summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/delayed_feedback_confirmation_2000")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=20266000)
    args = parser.parse_args()
    summary, manifest = run_confirmation(
        args.output_dir,
        device=args.device,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
    )
    print(summary.to_string(index=False))
    print(json.dumps(manifest["primary_test"], indent=2))
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
