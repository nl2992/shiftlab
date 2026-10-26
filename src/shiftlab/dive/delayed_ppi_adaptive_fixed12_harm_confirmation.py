"""Disjoint harm-power confirmation for adaptive PPI under fixed 12-event delay."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _generate, _simulate_method
from .delayed_evidence_directed_ppi_confirmation import _bootstrap_interval

SEED_OFFSET = 20_430_000
SEEDS = 1_000
CANDIDATE = "evidence_a0p025_p0p5_eventwise"
REFERENCE = "uniform_eventwise"
METHODS = (CANDIDATE, REFERENCE)
PROTOCOL = Path("docs/delayed_ppi_adaptive_fixed12_harm_confirmation_protocol.md")
CALIBRATION_DEFAULT = Path("outputs/delayed_ppi_adaptive_fixed12_replication_2000/manifest.json")
WORKERS = 4
CHUNKS = 4


def _run_chunk(
    task: tuple[
        Config,
        list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]],
    ],
):
    config, streams = task
    rows: list[dict[str, object]] = []
    for seed, x_source, z_source, x_target, z_target, onset in streams:
        delays = np.full(len(z_target), 12, dtype=np.int64)
        for method in METHODS:
            row = _simulate_method(
                config,
                seed=seed,
                scenario="boundary_harm",
                method=method,
                x_source=x_source,
                z_source=z_source,
                x_target=x_target,
                z_target=z_target,
                delays=delays,
                onset=onset,
                monitor_variant="full_stream",
                continue_after_alarm=True,
            )
            rows.append(row)
    return rows


def run(
    *, device: str, calibration_manifest: Path, output: Path, protocol: Path = PROTOCOL
) -> Path:
    config = Config(seeds=SEEDS, seed_offset=SEED_OFFSET, device=device)
    config.validate()
    calibration_bytes = calibration_manifest.read_bytes()
    calibration = json.loads(calibration_bytes)
    if not calibration.get("calibration_gate_pass") or not calibration.get("invariants_pass"):
        raise ValueError(
            "fixed12 harm confirmation requires the passing independent null calibration"
        )
    cal_config = calibration.get("config", {})
    fields = (
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
    mismatches = [
        key
        for key in fields
        if key not in cal_config
        or not np.isclose(float(cal_config[key]), float(asdict(config)[key]))
    ]
    if mismatches:
        raise ValueError(f"calibration configuration mismatch: {', '.join(mismatches)}")
    cal_start = int(cal_config.get("seed_offset", -1))
    cal_end = cal_start + int(cal_config.get("seeds", 0)) - 1
    if cal_start < 0 or not (SEED_OFFSET + SEEDS - 1 < cal_start or SEED_OFFSET > cal_end):
        raise ValueError("confirmation seeds overlap calibration seeds")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol.read_bytes()

    streams: list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]] = []
    resolved = ""
    for i in range(SEEDS):
        seed = SEED_OFFSET + i
        x_source, z_source, x_target, z_target, _delays, onset, resolved = _generate(
            config, seed=seed, scenario="boundary_harm"
        )
        streams.append((seed, x_source, z_source, x_target, z_target, onset))
        if (i + 1) % 200 == 0:
            print(f"generated harm streams on {resolved}: {i + 1}/{SEEDS}", flush=True)

    chunks = [streams[i::CHUNKS] for i in range(CHUNKS)]
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=get_context("spawn")) as executor:
        futures = [executor.submit(_run_chunk, (config, chunk)) for chunk in chunks]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"completed harm replay chunk: {completed}/{CHUNKS}", flush=True)

    frame = pd.DataFrame(rows).sort_values(["seed", "method"], kind="stable")
    keys = ["seed", "method"]
    expected = SEEDS * len(METHODS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("harm confirmation row/key integrity failed")
    if set(frame.method.unique()) != set(METHODS):
        raise RuntimeError("confirmation method coverage failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("pathwise label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    cand = frame.loc[frame.method.eq(CANDIDATE)].sort_values("seed")
    ref = frame.loc[frame.method.eq(REFERENCE)].sort_values("seed")
    paired = cand.merge(ref, on="seed", suffixes=("_candidate", "_uniform"), validate="one_to_one")
    detect_c = paired.alarm_after_onset_candidate.astype(bool).to_numpy()
    detect_u = paired.alarm_after_onset_uniform.astype(bool).to_numpy()
    diff = detect_c.astype(float) - detect_u.astype(float)
    wins = int(np.sum(detect_c & ~detect_u))
    losses = int(np.sum(~detect_c & detect_u))
    discordant = wins + losses
    p_value = (
        float(binomtest(wins, discordant, p=0.5, alternative="greater").pvalue)
        if discordant
        else 1.0
    )
    rng = np.random.default_rng(SEED_OFFSET + 1_333_017)
    detect_ci = _bootstrap_interval(diff, rng=rng)
    label_diff = paired.labels_queried_candidate.to_numpy(
        float
    ) - paired.labels_queried_uniform.to_numpy(float)
    label_ci = _bootstrap_interval(label_diff, rng=rng)
    result = {
        "streams": SEEDS,
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "candidate_post_onset_detection_rate": float(detect_c.mean()),
        "uniform_post_onset_detection_rate": float(detect_u.mean()),
        "paired_detection_difference": float(diff.mean()),
        "paired_detection_ci95_low": detect_ci[0],
        "paired_detection_ci95_high": detect_ci[1],
        "candidate_only_detections": wins,
        "uniform_only_detections": losses,
        "mcnemar_one_sided_p": p_value,
        "candidate_mean_labels": float(cand.labels_queried.mean()),
        "uniform_mean_labels": float(ref.labels_queried.mean()),
        "paired_label_difference": float(label_diff.mean()),
        "paired_label_ci95_low": label_ci[0],
        "paired_label_ci95_high": label_ci[1],
        "candidate_mean_events": float(cand.events_updated.mean()),
        "uniform_mean_events": float(ref.events_updated.mean()),
        "pre_onset_candidate_alarms": int(
            (cand.alarm & cand.alarm_event.lt(cand.onset_event)).sum()
        ),
        "candidate_mean_event_delay_after_onset": float(cand.event_delay_after_onset.mean()),
        "candidate_mean_wall_delay_after_onset": float(cand.wall_delay_after_onset.mean()),
        "gate_pass": bool(
            detect_ci[0] > 0
            and float(cand.labels_queried.mean()) <= float(ref.labels_queried.mean())
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
    }
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    pd.DataFrame([result]).to_csv(output / "confirmation_result.csv", index=False)
    manifest = {
        "experiment": "adaptive_ppi_fixed12_boundary_harm_confirmation",
        "config": asdict(config),
        "scenario": "boundary_harm",
        "delay_profile": "fixed12",
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "rows": len(frame),
        "seed_range": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "calibration_manifest_sha256": hashlib.sha256(calibration_bytes).hexdigest(),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_hashes": {
            "confirmation": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "stream_generator": hashlib.sha256(
                Path(__file__).with_name("delayed_evidence_directed_ppi.py").read_bytes()
            ).hexdigest(),
        },
        "runtime": environment(),
        "resolved_device": resolved,
        "workers": WORKERS,
        "chunks": CHUNKS,
        "result": result,
        "invariants_pass": bool(
            len(frame) == expected
            and not frame.duplicated(keys).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "limitations": [
            "One boundary-harm effect and onset under fixed 12-event delays only.",
            "Alarm detection is not direct evidence of prevented decision harm.",
            "Both query and monitor procedures are established; no novelty claim is made.",
        ],
        "created_utc": datetime.now(UTC).isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in sorted(output.iterdir()):
        if path.name != "checksums.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with (output / "checksums.sha256").open("a", encoding="utf-8") as handle:
                handle.write(f"{digest}  {path.name}\n")
    print(json.dumps(result, indent=2), flush=True)
    print(f"fixed12 harm confirmation: {'PASS' if result['gate_pass'] else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--calibration-manifest", type=Path, default=CALIBRATION_DEFAULT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_ppi_adaptive_fixed12_harm_confirmation_1000"),
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    run(
        device=args.device,
        calibration_manifest=args.calibration_manifest,
        output=args.output_dir,
        protocol=args.protocol,
    )


if __name__ == "__main__":
    main()
