"""Disjoint confirmation of the fixed-start delayed PPI shadow monitor."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import (
    Config,
    _fit_source_proxy,
    _method_parameters,
)
from .delayed_evidence_directed_ppi_markov_calibration import generate
from .delayed_evidence_ppi_markov_confirmation import _harm_outcomes
from .delayed_evidence_ppi_start_mixture import ONSET_FRACTIONS, STARTS
from .delayed_feedback import EventOrderBuffer, ResolvedEvidence
from .eprocess import PredictableBoundMeanEProcess, PredictableStartedMixtureEProcess
from .query import EvidenceDirectedQueryPolicy

CANDIDATE = "evidence_a0p025_p0p5_eventwise"
MONITOR_VARIANTS = ("full_stream", "fixed_start_mixture")
BOOTSTRAP_REPLICATES = 20_000
HARM_SHIFT = 0.20


def _bootstrap_interval(values: np.ndarray, *, rng: np.random.Generator) -> tuple[float, float]:
    n = len(values)
    indices = rng.integers(0, n, size=(BOOTSTRAP_REPLICATES, n))
    draws = values[indices].mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def simulate_pair(
    config: Config,
    *,
    seed: int,
    x_source: np.ndarray,
    z_source: np.ndarray,
    x_target: np.ndarray,
    z_target: np.ndarray,
    delays: np.ndarray,
    onset: int,
) -> list[dict[str, object]]:
    """Run both shadow monitors in one matched event-order simulation."""
    kind, activation, power = _method_parameters(CANDIDATE)
    if kind != "eventwise":
        raise RuntimeError("the frozen candidate must use the eventwise query rule")
    intercept, slope = _fit_source_proxy(x_source, z_source)
    proxy = np.clip(intercept + slope * x_target, -config.amplitude, config.amplitude)
    policy = EvidenceDirectedQueryPolicy(
        q_min=config.q_min,
        q_max=config.q_max,
        alpha=config.alpha,
        activation_fraction=activation,
        urgency_power=power,
        budget_taper_power=1.0,
    )
    full_process = PredictableBoundMeanEProcess(alpha=config.alpha)
    start_process = PredictableStartedMixtureEProcess(alpha=config.alpha, starts=STARTS)
    shared_query_uniforms = np.random.default_rng(seed + 6_512_819).random(config.n_target)
    budget = math.floor(config.n_target * config.budget_rate)
    remaining = budget
    buffer = EventOrderBuffer()
    arrivals: dict[int, list[int]] = {}
    q_values: list[float] = []
    queried_events: list[int] = []
    event_bounds: dict[int, float] = {}
    event_count = 0
    query_cost = 0
    first_alarm: dict[str, tuple[int, int] | None] = {
        "full_stream": None,
        "fixed_start_mixture": None,
    }

    def update_rows(wall_time: int, rows: list[ResolvedEvidence]) -> None:
        for row in rows:
            bound = event_bounds[row.event_index]
            full_value = full_process.update(row.value, bound=bound)
            start_value = start_process.update(row.value, bound=bound)
            if first_alarm["full_stream"] is None and full_process.alarm:
                first_alarm["full_stream"] = (row.event_index, wall_time)
            if first_alarm["fixed_start_mixture"] is None and start_process.alarm:
                first_alarm["fixed_start_mixture"] = (row.event_index, wall_time)
            if not np.isfinite(full_value) or not np.isfinite(start_value):
                raise RuntimeError("non-finite matched-shadow e-value")

    for wall in range(config.n_target + config.max_delay + 1):
        for event in arrivals.pop(wall, []):
            propensity = q_values[event]
            centered_proxy = float(proxy[event]) - config.epsilon
            increment = centered_proxy + (float(z_target[event]) - float(proxy[event])) / propensity
            update_rows(
                wall,
                buffer.resolve(event, available_time=float(wall), value=increment),
            )

        if wall >= config.n_target or remaining == 0:
            continue
        remaining_fraction = remaining / budget if budget else 0.0
        propensity = policy.propensity(
            log_e_value=full_process.log_e_value,
            remaining_fraction=remaining_fraction,
        )
        if not config.q_min - 1e-12 <= propensity <= config.q_max + 1e-12:
            raise RuntimeError("query propensity is outside the registered support")
        event = wall
        q_values.append(float(propensity))
        centered_proxy = float(proxy[event]) - config.epsilon
        bound = (config.amplitude + config.epsilon + 1e-6) * (2 / propensity - 1)
        event_bounds[event] = bound
        queried = shared_query_uniforms[event] < propensity
        event_count += 1
        if queried:
            if remaining < 1:
                raise RuntimeError("pathwise label cap would be exceeded")
            remaining -= 1
            query_cost += 1
            queried_events.append(event)
            update_rows(wall, buffer.register(event, float(event), value=None))
            delay = int(delays[event])
            if delay == 0:
                increment = (
                    centered_proxy + (float(z_target[event]) - float(proxy[event])) / propensity
                )
                update_rows(
                    wall,
                    buffer.resolve(event, available_time=float(wall), value=increment),
                )
            else:
                arrivals.setdefault(wall + delay, []).append(event)
        else:
            update_rows(wall, buffer.register(event, float(event), value=centered_proxy))

    if buffer.pending_count or buffer.buffered_count:
        raise RuntimeError("matched-shadow labels did not resolve into a complete event prefix")
    if event_count != full_process.n_updates or event_count != start_process.time:
        raise RuntimeError("matched-shadow monitors did not consume the complete event prefix")
    if query_cost > budget:
        raise RuntimeError("matched-shadow label cap was exceeded")

    query_hash = hashlib.sha256(
        np.asarray(q_values, dtype="<f8").tobytes()
        + np.asarray(queried_events, dtype="<i8").tobytes()
    ).hexdigest()
    rows: list[dict[str, object]] = []
    for monitor, process in (
        ("full_stream", full_process),
        ("fixed_start_mixture", start_process),
    ):
        alarm = first_alarm[monitor]
        alarm_event = alarm[0] if alarm is not None else None
        alarm_wall = alarm[1] if alarm is not None else None
        detected = alarm_event is not None and alarm_event >= onset
        event_delay = (
            alarm_event - onset if alarm_event is not None and alarm_event >= onset else np.nan
        )
        wall_delay = (
            alarm_wall - onset
            if alarm_wall is not None and alarm_event is not None and alarm_event >= onset
            else np.nan
        )
        rows.append(
            {
                "seed": seed,
                "scenario": "boundary_harm",
                "method": CANDIDATE,
                "monitor_variant": monitor,
                "harmful_stream": True,
                "onset_event": onset,
                "alarm": alarm is not None,
                "alarm_event": alarm_event,
                "alarm_wall_time": alarm_wall,
                "alarm_after_onset": bool(detected),
                "event_delay_after_onset": event_delay,
                "wall_delay_after_onset": wall_delay,
                "labels_queried": query_cost,
                "query_schedule_sha256": query_hash,
                "hard_label_cap": budget,
                "budget_respected": query_cost <= budget,
                "budget_exhausted": remaining == 0,
                "events_registered": event_count,
                "events_updated": event_count,
                "mean_propensity": float(np.mean(q_values)) if q_values else np.nan,
                "min_propensity": min(q_values) if q_values else np.nan,
                "max_propensity": max(q_values) if q_values else np.nan,
                "final_e_value": process.log_e_value,
                "proxy_source_intercept": intercept,
                "proxy_source_slope": slope,
                "pending_labels": buffer.pending_count,
                "device": config.device,
            }
        )
    return rows


def run(
    config: Config,
    output: Path,
    *,
    protocol: Path,
    calibration_manifest: Path,
) -> Path:
    config.validate()
    calibration_bytes = calibration_manifest.read_bytes()
    calibration = json.loads(calibration_bytes)
    if not (
        calibration.get("gate_pass")
        and calibration.get("invariants_pass")
        and calibration.get("matched_query_paths_pass")
    ):
        raise ValueError("confirmation requires a passing matched-shadow Markov calibration")
    if calibration.get("scenario") != "markov_variance_null":
        raise ValueError("calibration manifest is not the registered Markov-scale null")
    if CANDIDATE not in calibration.get("query_methods", ()) or set(MONITOR_VARIANTS) != set(
        calibration.get("monitor_variants", ())
    ):
        raise ValueError("calibration did not cover the registered query method and both monitors")
    source_hashes = calibration.get("source_hashes", {})
    for filename in (
        "delayed_evidence_directed_ppi.py",
        "delayed_evidence_directed_ppi_markov_calibration.py",
        "eprocess.py",
    ):
        actual = hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()
        if source_hashes.get(filename) != actual:
            raise ValueError(f"calibration source hash does not match {filename}")
    calibration_config = calibration.get("config", {})
    matched_fields = (
        "n_source",
        "n_target",
        "budget_rate",
        "alpha",
        "epsilon",
        "q_min",
        "q_max",
        "amplitude",
        "harm_shift",
        "onset_fraction",
        "max_delay",
        "benign_amplitude",
    )
    config_values = asdict(config)
    mismatched = [
        field
        for field in matched_fields
        if field not in calibration_config
        or not np.isclose(float(calibration_config[field]), float(config_values[field]))
    ]
    if mismatched:
        raise ValueError(f"calibration configuration mismatch: {', '.join(mismatched)}")
    calibration_start = int(calibration_config.get("seed_offset", -1))
    calibration_end = calibration_start + int(calibration_config.get("seeds", 0)) - 1
    confirmation_end = config.seed_offset + config.seeds - 1
    if calibration_start < 0 or not (
        confirmation_end < calibration_start or config.seed_offset > calibration_end
    ):
        raise ValueError("confirmation and calibration seed blocks must be disjoint")
    protocol_bytes = protocol.read_bytes()
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
            paired_rows = simulate_pair(
                config,
                seed=seed,
                x_source=x_source,
                z_source=z_source,
                x_target=x_target,
                z_target=z_target,
                delays=delays,
                onset=onset,
            )
            for row in paired_rows:
                row["onset_fraction"] = onset_fraction
                rows.append(row)
        if (i + 1) % 25 == 0:
            print(f"completed confirmation seed clusters: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(
        ["seed", "onset_fraction", "monitor_variant"], kind="stable"
    )
    keys = ["seed", "onset_fraction", "monitor_variant"]
    expected = config.seeds * len(ONSET_FRACTIONS) * len(MONITOR_VARIANTS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("confirmation row/key integrity failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("confirmation exceeded its label cap")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("confirmation delayed-prefix integrity failed")

    paired = frame.pivot(
        index=["seed", "onset_fraction"],
        columns="monitor_variant",
        values=["alarm_after_onset", "labels_queried", "events_updated", "query_schedule_sha256"],
    )
    confirmation_matched_fields = (
        "labels_queried",
        "events_updated",
        "query_schedule_sha256",
    )
    matched_paths = all(
        (paired[field]["full_stream"] == paired[field]["fixed_start_mixture"]).all()
        for field in confirmation_matched_fields
    )
    if not matched_paths:
        raise RuntimeError("confirmation monitor pairs differ in query schedule or cost")
    difference = paired["alarm_after_onset"]["fixed_start_mixture"].astype(float) - paired[
        "alarm_after_onset"
    ]["full_stream"].astype(float)
    cluster_difference = difference.groupby(level="seed").mean().to_numpy(dtype=float)
    mean_difference = float(cluster_difference.mean())
    rng = np.random.default_rng(config.seed_offset + 5_990_311)
    detection_ci = _bootstrap_interval(cluster_difference, rng=rng)
    label_difference = float(
        (
            paired["labels_queried"]["fixed_start_mixture"].astype(float)
            - paired["labels_queried"]["full_stream"].astype(float)
        ).mean()
    )
    event_difference = int(
        (paired["events_updated"]["fixed_start_mixture"] - paired["events_updated"]["full_stream"])
        .abs()
        .sum()
    )
    cap_violations = int((~frame.budget_respected.astype(bool)).sum())
    unresolved_labels = int(frame.pending_labels.sum())
    event_count_mismatches = int((frame.events_registered != frame.events_updated).sum())
    frame["pre_onset_alarm"] = frame.alarm.astype(bool) & frame.alarm_event.lt(frame.onset_event)
    result = {
        "seed_clusters": config.seeds,
        "onset_fractions": list(ONSET_FRACTIONS),
        "candidate": "fixed_start_mixture",
        "reference": "full_stream",
        "candidate_detection_rate": float(
            paired["alarm_after_onset"]["fixed_start_mixture"].astype(bool).mean()
        ),
        "full_stream_detection_rate": float(
            paired["alarm_after_onset"]["full_stream"].astype(bool).mean()
        ),
        "paired_detection_difference": mean_difference,
        "cluster_bootstrap_95_low": detection_ci[0],
        "cluster_bootstrap_95_high": detection_ci[1],
        "candidate_only_detections": int(
            (
                paired["alarm_after_onset"]["fixed_start_mixture"].astype(bool)
                & ~paired["alarm_after_onset"]["full_stream"].astype(bool)
            ).sum()
        ),
        "full_stream_only_detections": int(
            (
                ~paired["alarm_after_onset"]["fixed_start_mixture"].astype(bool)
                & paired["alarm_after_onset"]["full_stream"].astype(bool)
            ).sum()
        ),
        "candidate_mean_labels": float(paired["labels_queried"]["fixed_start_mixture"].mean()),
        "full_stream_mean_labels": float(paired["labels_queried"]["full_stream"].mean()),
        "paired_label_difference": label_difference,
        "paired_event_count_mismatches": event_difference,
        "pre_onset_candidate_alarms": int(
            (
                frame.loc[frame.monitor_variant.eq("fixed_start_mixture"), "alarm"]
                & frame.loc[frame.monitor_variant.eq("fixed_start_mixture"), "alarm_event"].lt(
                    frame.loc[frame.monitor_variant.eq("fixed_start_mixture"), "onset_event"]
                )
            ).sum()
        ),
        "cap_violations": cap_violations,
        "unresolved_labels": unresolved_labels,
        "event_count_mismatches": event_count_mismatches,
        "matched_query_paths_pass": matched_paths,
    }
    result["confirmation_gate_pass"] = bool(
        mean_difference > 0
        and detection_ci[0] > 0
        and label_difference == 0
        and event_difference == 0
        and cap_violations == 0
        and unresolved_labels == 0
        and event_count_mismatches == 0
        and matched_paths
    )

    summary = (
        frame.groupby(["onset_fraction", "monitor_variant"], as_index=False)
        .agg(
            streams=("seed", "nunique"),
            detections=("alarm_after_onset", "sum"),
            detection_rate=("alarm_after_onset", "mean"),
            pre_onset_alarms=("pre_onset_alarm", "sum"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("events_updated", "mean"),
            mean_delay_events=("event_delay_after_onset", "mean"),
        )
        .sort_values(["onset_fraction", "monitor_variant"], kind="stable")
    )
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    summary.to_csv(output / "cell_summary.csv", index=False)
    summary.to_parquet(output / "cell_summary.parquet", index=False)
    (output / "confirmation_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "experiment": "delayed_evidence_ppi_fixed_start_matched_shadow_confirmation",
        "config": asdict(config),
        "scenario": "boundary_harm",
        "monitor_variants": list(MONITOR_VARIANTS),
        "start_events": list(STARTS),
        "start_weights": [1 / len(STARTS)] * len(STARTS),
        "onset_fractions": list(ONSET_FRACTIONS),
        "query_method": CANDIDATE,
        "query_driver": "full_stream",
        "continue_after_alarm": True,
        "calibration_manifest_sha256": hashlib.sha256(calibration_bytes).hexdigest(),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "seed_range": [config.seed_offset, config.seed_offset + config.seeds - 1],
        "rows": len(frame),
        "result": result,
        "cell_summary": summary.to_dict(orient="records"),
        "source_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("delayed_evidence_directed_ppi.py"),
                Path(__file__).with_name("eprocess.py"),
                Path(__file__).with_name("delayed_evidence_directed_ppi_markov_calibration.py"),
            )
        },
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "invariants_pass": bool(
            len(frame) == expected
            and not frame.duplicated(keys).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
            and matched_paths
        ),
        "limitations": [
            "Confirmatory power claim applies only to the registered Markov-scale harm family, three onsets, and matched full-stream acquisition policy.",
            "Finite null calibration and Monte Carlo confirmation do not cover persistent signs, informative delays, conditional-mean drift, or real data.",
            "The fixed-start mixture is a standard convex mixture of e-processes, not a novelty claim.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"matched-shadow confirmation gate: {'PASS' if result['confirmation_gate_pass'] else 'FAIL'}",
        flush=True,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=300)
    parser.add_argument("--seed-offset", type=int, default=20322000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/delayed_evidence_ppi_start_mixture_confirmation_protocol.md"),
    )
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_start_mixture_calibration_500/manifest.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_start_mixture_confirmation_300"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running matched-shadow PPI confirmation on {config.device}", flush=True)
    run(
        config,
        args.output_dir,
        protocol=args.protocol,
        calibration_manifest=args.calibration_manifest,
    )


if __name__ == "__main__":
    main()
