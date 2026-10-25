"""Development grid for fixed-start mixtures with delayed PPI feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _simulate_method
from .delayed_evidence_directed_ppi_confirmation import _bootstrap_interval
from .delayed_evidence_directed_ppi_markov_calibration import generate
from .delayed_evidence_ppi_markov_confirmation import _harm_outcomes

CANDIDATE = "evidence_a0p025_p0p5_eventwise"
REFERENCE = "uniform_eventwise"
QUERY_METHODS = (REFERENCE, CANDIDATE)
MONITOR_VARIANTS = ("full_stream", "fixed_start_mixture")
STARTS = tuple(range(0, 2400, 300))
ONSET_FRACTIONS = (0.25, 0.50, 0.75)
SCENARIO = "boundary_harm"
BOOTSTRAP_REPLICATES = 20_000


def _cluster_interval(values: pd.Series, *, rng: np.random.Generator) -> tuple[float, float]:
    grouped = values.groupby(level="seed").mean().to_numpy(dtype=float)
    return _bootstrap_interval(grouped, rng=rng)


def run(
    config: Config,
    output: Path,
    *,
    protocol: Path,
    matched_shadow: bool = False,
) -> Path:
    config.validate()
    protocol_bytes = protocol.read_bytes()
    if config.n_target != STARTS[-1] + 300:
        raise ValueError("the frozen start mixture requires a 2,400-event target horizon")
    if not np.isclose(config.harm_shift, 0.20) or not np.isclose(config.epsilon, 0.05):
        raise ValueError("the frozen protocol requires harm_shift=0.20 and epsilon=0.05")
    if config.max_delay != 12:
        raise ValueError("the frozen protocol requires uniform delays on 0 through 12")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, _, delays, _, regimes, _device = generate(config, seed=seed)
        for onset_fraction in ONSET_FRACTIONS:
            onset = int(config.n_target * onset_fraction)
            z_target = _harm_outcomes(config, seed=seed, regimes=regimes, onset=onset)
            for query_method in QUERY_METHODS:
                for monitor_variant in MONITOR_VARIANTS:
                    row = _simulate_method(
                        config,
                        seed=seed,
                        scenario=SCENARIO,
                        method=query_method,
                        x_source=x_source,
                        z_source=z_source,
                        x_target=x_target,
                        z_target=z_target,
                        delays=delays,
                        onset=onset,
                        monitor_variant=monitor_variant,
                        monitor_starts=STARTS if monitor_variant == "fixed_start_mixture" else (),
                        query_driver_variant="full_stream" if matched_shadow else "monitor",
                        continue_after_alarm=matched_shadow,
                    )
                    row["onset_fraction"] = onset_fraction
                    row["monitor_variant"] = monitor_variant
                    row["matched_shadow"] = matched_shadow
                    rows.append(row)
        if (i + 1) % 10 == 0:
            print(f"completed paired streams: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(
        ["seed", "onset_fraction", "method", "monitor_variant"], kind="stable"
    )
    expected_rows = config.seeds * len(ONSET_FRACTIONS) * len(QUERY_METHODS) * len(MONITOR_VARIANTS)
    keys = ["seed", "onset_fraction", "method", "monitor_variant"]
    if len(frame) != expected_rows or frame.duplicated(keys).any():
        raise RuntimeError("start-mixture grid row/key integrity failed")
    if set(frame.method.unique()) != set(QUERY_METHODS):
        raise RuntimeError("start-mixture grid is missing a query policy")
    if set(frame.monitor_variant.unique()) != set(MONITOR_VARIANTS):
        raise RuntimeError("start-mixture grid is missing a monitor")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("start-mixture grid exceeded the hard label cap")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("start-mixture grid delayed-prefix integrity failed")
    if matched_shadow:
        paired_paths = frame.pivot(
            index=["seed", "onset_fraction", "method"],
            columns="monitor_variant",
            values=["query_schedule_sha256", "labels_queried", "events_updated"],
        )
        for measure in ("query_schedule_sha256", "labels_queried", "events_updated"):
            if not (
                paired_paths[measure]["full_stream"] == paired_paths[measure]["fixed_start_mixture"]
            ).all():
                raise RuntimeError(f"matched-shadow pairs differ in {measure}")
    frame["pre_onset_alarm"] = frame.alarm.astype(bool) & frame.alarm_event.lt(frame.onset_event)

    index = ["seed", "onset_fraction", "method"]
    detections = frame.pivot(index=index, columns="monitor_variant", values="alarm_after_onset")
    labels = frame.pivot(index=index, columns="monitor_variant", values="labels_queried")
    detection_diff = detections.fixed_start_mixture.astype(float) - detections.full_stream.astype(
        float
    )
    label_diff = labels.fixed_start_mixture.astype(float) - labels.full_stream.astype(float)
    candidate_detection = detection_diff.xs(CANDIDATE, level="method")
    candidate_labels = label_diff.xs(CANDIDATE, level="method")
    mean_detection_difference = float(candidate_detection.mean())
    mean_label_difference = float(candidate_labels.mean())
    cap_violations = int((~frame.budget_respected.astype(bool)).sum())
    unresolved_labels = int(frame.pending_labels.sum())
    event_count_mismatches = int((frame.events_registered != frame.events_updated).sum())
    rng = np.random.default_rng(config.seed_offset + 6_931_711)
    detection_ci = _cluster_interval(candidate_detection, rng=rng)
    label_ci = _cluster_interval(candidate_labels, rng=rng)

    summary = (
        frame.groupby(["onset_fraction", "method", "monitor_variant"], as_index=False)
        .agg(
            streams=("seed", "nunique"),
            detections=("alarm_after_onset", "sum"),
            detection_rate=("alarm_after_onset", "mean"),
            pre_onset_alarms=("pre_onset_alarm", "sum"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("events_updated", "mean"),
            mean_delay_events=("event_delay_after_onset", "mean"),
            cap_violations=("budget_respected", lambda values: int((~values).sum())),
        )
        .sort_values(["onset_fraction", "method", "monitor_variant"], kind="stable")
    )
    summary.to_csv(output / "cell_summary.csv", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)

    result = {
        "primary_query_method": CANDIDATE,
        "candidate": "fixed_start_mixture",
        "reference": "full_stream",
        "onset_fractions": list(ONSET_FRACTIONS),
        "paired_detection_difference": mean_detection_difference,
        "detection_cluster_bootstrap_95_low": detection_ci[0],
        "detection_cluster_bootstrap_95_high": detection_ci[1],
        "paired_label_difference": mean_label_difference,
        "label_cluster_bootstrap_95_low": label_ci[0],
        "label_cluster_bootstrap_95_high": label_ci[1],
        "candidate_only_detections": int(
            (
                detections.xs(CANDIDATE, level="method").fixed_start_mixture.astype(bool)
                & ~detections.xs(CANDIDATE, level="method").full_stream.astype(bool)
            ).sum()
        ),
        "full_stream_only_detections": int(
            (
                ~detections.xs(CANDIDATE, level="method").fixed_start_mixture.astype(bool)
                & detections.xs(CANDIDATE, level="method").full_stream.astype(bool)
            ).sum()
        ),
        "cap_violations": cap_violations,
        "unresolved_labels": unresolved_labels,
        "event_count_mismatches": event_count_mismatches,
    }
    result["advance_to_independent_validation"] = bool(
        mean_detection_difference > 0
        and detection_ci[0] > 0
        and mean_label_difference <= 0
        and cap_violations == 0
        and unresolved_labels == 0
        and event_count_mismatches == 0
    )
    summary.to_parquet(output / "cell_summary.parquet", index=False)
    (output / "development_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "experiment": (
            "delayed_evidence_ppi_fixed_start_mixture_matched_shadow_development"
            if matched_shadow
            else "delayed_evidence_ppi_fixed_start_mixture_development"
        ),
        "config": asdict(config),
        "scenario": SCENARIO,
        "query_methods": list(QUERY_METHODS),
        "monitor_variants": list(MONITOR_VARIANTS),
        "matched_shadow": matched_shadow,
        "query_driver": "full_stream" if matched_shadow else "monitor",
        "start_events": list(STARTS),
        "start_weights": [1 / len(STARTS)] * len(STARTS),
        "onset_fractions": list(ONSET_FRACTIONS),
        "rows": len(frame),
        "seed_range": [config.seed_offset, config.seed_offset + config.seeds - 1],
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("delayed_evidence_directed_ppi.py"),
                Path(__file__).with_name("delayed_evidence_directed_ppi_markov_calibration.py"),
                Path(__file__).with_name("eprocess.py"),
            )
        },
        "result": result,
        "cell_summary": summary.to_dict(orient="records"),
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "invariants_pass": bool(
            len(frame) == expected_rows
            and not frame.duplicated(keys).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "limitations": [
            "Development-only power screen; no independent null calibration or confirmatory claim.",
            "The fixed mixture uses established e-process convexity; no novelty claim is made.",
            "Only one persistent-scale Markov generator, independent uniform delays, and one harm magnitude are tested.",
            "Seed-cluster bootstrap intervals are descriptive after this development comparison.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        "start-mixture development nomination: "
        f"{'PASS' if result['advance_to_independent_validation'] else 'FAIL'}",
        flush=True,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=20310000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--matched-shadow", action="store_true")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/delayed_evidence_ppi_start_mixture_grid_protocol.md"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_start_mixture_grid_60"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running delayed PPI start-mixture grid on {config.device}", flush=True)
    run(config, args.output_dir, protocol=args.protocol, matched_shadow=args.matched_shadow)


if __name__ == "__main__":
    main()
