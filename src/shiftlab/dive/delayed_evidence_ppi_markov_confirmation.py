"""Disjoint power confirmation under persistent outcome-scale regimes."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import binomtest

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _simulate_method
from .delayed_evidence_directed_ppi_confirmation import _bootstrap_interval
from .delayed_evidence_directed_ppi_markov_calibration import generate

CANDIDATE = "evidence_a0p025_p0p5_eventwise"
REFERENCE = "uniform_eventwise"
METHODS = (CANDIDATE, REFERENCE)
SCENARIO = "boundary_harm"
HARM_SHIFT = 0.20


def _harm_outcomes(config: Config, *, seed: int, regimes: np.ndarray, onset: int) -> np.ndarray:
    device = (
        torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if config.device == "auto"
        else torch.device(config.device)
    )
    generator = torch.Generator(device=device).manual_seed(seed + 74_931_017)
    amplitude = torch.where(torch.as_tensor(regimes, device=device).bool(), 1.0, 0.55)
    probability_positive = torch.full((config.n_target,), 0.5, device=device, dtype=torch.float32)
    probability_positive[onset:] = 0.5 + HARM_SHIFT / (2 * amplitude[onset:])
    if torch.any((probability_positive < 0) | (probability_positive > 1)):
        raise RuntimeError("harm generator probabilities leave [0,1]")
    signs_positive = (
        torch.rand(config.n_target, device=device, generator=generator) < probability_positive
    )
    return torch.where(signs_positive, amplitude, -amplitude).cpu().numpy()


def run(config: Config, output: Path, *, calibration_manifest: Path) -> Path:
    config.validate()
    if not np.isclose(config.harm_shift, HARM_SHIFT):
        raise ValueError(f"the frozen Markov alternative requires harm_shift={HARM_SHIFT}")
    calibration_bytes = calibration_manifest.read_bytes()
    calibration = json.loads(calibration_bytes)
    if not calibration.get("gate_pass") or not calibration.get("invariants_pass"):
        raise ValueError("Markov harm confirmation requires a passing null calibration")
    if calibration.get("scenario") != "markov_variance_null":
        raise ValueError("the calibration manifest is not the frozen Markov-scale null")
    if not set(METHODS).issubset(set(calibration.get("methods", []))):
        raise ValueError("the Markov calibration does not cover both confirmation methods")
    generator_hash = hashlib.sha256(
        Path(__file__).with_name("delayed_evidence_directed_ppi_markov_calibration.py").read_bytes()
    ).hexdigest()
    if calibration.get("source_hashes", {}).get("calibration") != generator_hash:
        raise ValueError("Markov calibration was run with a different generator module")
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
    mismatched = [
        field
        for field in matched_fields
        if field not in calibration_config
        or not np.isclose(float(calibration_config[field]), float(asdict(config)[field]))
    ]
    if mismatched:
        raise ValueError(f"Markov calibration configuration mismatch: {', '.join(mismatched)}")
    calibration_start = int(calibration_config.get("seed_offset", -1))
    calibration_end = calibration_start + int(calibration_config.get("seeds", 0)) - 1
    confirmation_end = config.seed_offset + config.seeds - 1
    if calibration_start < 0 or not (
        confirmation_end < calibration_start or config.seed_offset > calibration_end
    ):
        raise ValueError("Markov confirmation and calibration seeds must be disjoint")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    onset = int(config.n_target * config.onset_fraction)
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, _, delays, _, regimes, _ = generate(config, seed=seed)
        z_target = _harm_outcomes(config, seed=seed, regimes=regimes, onset=onset)
        for method in METHODS:
            rows.append(
                _simulate_method(
                    config,
                    seed=seed,
                    scenario=SCENARIO,
                    method=method,
                    x_source=x_source,
                    z_source=z_source,
                    x_target=x_target,
                    z_target=z_target,
                    delays=delays,
                    onset=onset,
                )
            )
        if (i + 1) % 100 == 0:
            print(f"completed Markov harm streams: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(["seed", "method"], kind="stable")
    expected_rows = config.seeds * len(METHODS)
    if len(frame) != expected_rows or frame.duplicated(["seed", "method"]).any():
        raise RuntimeError("Markov confirmation row/key integrity failed")
    if set(frame.method.unique()) != set(METHODS):
        raise RuntimeError("Markov confirmation methods are incomplete")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("hard label cap failed in Markov confirmation")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    candidate = frame.loc[frame.method.eq(CANDIDATE)].sort_values("seed")
    reference = frame.loc[frame.method.eq(REFERENCE)].sort_values("seed")
    paired = candidate.merge(
        reference,
        on="seed",
        suffixes=("_candidate", "_uniform"),
        validate="one_to_one",
    )
    detected_candidate = paired.alarm_after_onset_candidate.astype(bool).to_numpy()
    detected_uniform = paired.alarm_after_onset_uniform.astype(bool).to_numpy()
    difference = detected_candidate.astype(float) - detected_uniform.astype(float)
    wins = int(np.sum(detected_candidate & ~detected_uniform))
    losses = int(np.sum(~detected_candidate & detected_uniform))
    discordant = wins + losses
    p_value = float(
        binomtest(wins, discordant, p=0.5, alternative="greater").pvalue if discordant else 1.0
    )
    rng = np.random.default_rng(config.seed_offset + 9_307_111)
    detection_ci = _bootstrap_interval(difference, rng=rng)
    label_difference = paired.labels_queried_candidate.to_numpy(
        dtype=float
    ) - paired.labels_queried_uniform.to_numpy(dtype=float)
    label_ci = _bootstrap_interval(label_difference, rng=rng)
    mean_candidate_labels = float(candidate.labels_queried.mean())
    mean_uniform_labels = float(reference.labels_queried.mean())
    result = {
        "streams": config.seeds,
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "candidate_detection_rate": float(detected_candidate.mean()),
        "uniform_detection_rate": float(detected_uniform.mean()),
        "detection_difference": float(difference.mean()),
        "detection_ci_low": detection_ci[0],
        "detection_ci_high": detection_ci[1],
        "candidate_only_detections": wins,
        "uniform_only_detections": losses,
        "mcnemar_one_sided_p": p_value,
        "candidate_mean_labels": mean_candidate_labels,
        "uniform_mean_labels": mean_uniform_labels,
        "label_difference": float(label_difference.mean()),
        "label_ci_low": label_ci[0],
        "label_ci_high": label_ci[1],
        "candidate_mean_events": float(candidate.events_updated.mean()),
        "uniform_mean_events": float(reference.events_updated.mean()),
        "candidate_mean_delay_events": float(candidate.event_delay_after_onset.mean()),
        "candidate_mean_delay_wall": float(candidate.wall_delay_after_onset.mean()),
        "pre_onset_candidate_alarms": int(
            (candidate.alarm & candidate.alarm_event.lt(onset)).sum()
        ),
        "gate_pass": bool(
            p_value < 0.05
            and detection_ci[0] > 0
            and mean_candidate_labels <= mean_uniform_labels
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
    }
    frame.to_parquet(output / "metrics.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    pd.DataFrame([result]).to_csv(output / "confirmation_result.csv", index=False)
    manifest = {
        "experiment": "delayed_evidence_directed_ppi_markov_scale_harm_confirmation",
        "config": asdict(config),
        "scenario": SCENARIO,
        "markov_flip_probability": 0.05,
        "amplitudes": [0.55, 1.0],
        "harm_shift": HARM_SHIFT,
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "calibration_manifest_sha256": hashlib.sha256(calibration_bytes).hexdigest(),
        "rows": len(frame),
        "result": result,
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "source_hashes": {
            "confirmation": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "markov_generator": generator_hash,
            "development_module": hashlib.sha256(
                Path(__file__).with_name("delayed_evidence_directed_ppi.py").read_bytes()
            ).hexdigest(),
        },
        "conditional_mean": "0 before onset and exactly 0.20 after onset conditional on the persistent regime and complete prior history.",
        "limitations": [
            "Power comparison under one registered Markov-scale alternative only; type-I calibration is recorded separately.",
            "Signs are independent conditional on regime; persistent sign dependence and informative delays are out of scope.",
            "The query rule and e-process use established constructions; no novelty claim is made.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Markov harm confirmation gate: {'PASS' if result['gate_pass'] else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20292000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_markov_calibration_1000/manifest.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_markov_confirmation_1000"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running Markov-scale delayed PPI confirmation on {config.device}", flush=True)
    run(config, args.output_dir, calibration_manifest=args.calibration_manifest)


if __name__ == "__main__":
    main()
