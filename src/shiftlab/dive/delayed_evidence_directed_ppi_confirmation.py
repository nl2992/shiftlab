"""Disjoint positive-signal confirmation after the delayed PPI null gate passes."""

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
from .delayed_evidence_directed_ppi import Config, _generate, _simulate_method

CANDIDATE = "evidence_a0p025_p0p5_eventwise"
REFERENCE = "uniform_eventwise"
METHODS = (CANDIDATE, REFERENCE)
SCENARIO = "boundary_harm"
BOOTSTRAP_REPLICATES = 20_000


def _bootstrap_interval(values: np.ndarray, *, rng: np.random.Generator) -> tuple[float, float]:
    n = len(values)
    indices = rng.integers(0, n, size=(BOOTSTRAP_REPLICATES, n))
    draws = values[indices].mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def run(config: Config, output: Path, *, calibration_manifest: Path) -> Path:
    config.validate()
    calibration_bytes = calibration_manifest.read_bytes()
    calibration = json.loads(calibration_bytes)
    if not calibration.get("gate_pass") or not calibration.get("invariants_pass"):
        raise ValueError("disjoint confirmation requires a passing calibration manifest")
    if CANDIDATE not in calibration.get("methods", ()):
        raise ValueError("candidate was not included in the passing calibration")
    development_hash = hashlib.sha256(
        Path(__file__).with_name("delayed_evidence_directed_ppi.py").read_bytes()
    ).hexdigest()
    if calibration.get("source_hashes", {}).get("development_module") != development_hash:
        raise ValueError("calibration was run against a different development module")
    calibration_config = calibration.get("config", {})
    calibration_start = int(calibration_config.get("seed_offset", -1))
    calibration_end = calibration_start + int(calibration_config.get("seeds", 0)) - 1
    confirmation_end = config.seed_offset + config.seeds - 1
    if calibration_start < 0 or not (
        confirmation_end < calibration_start or config.seed_offset > calibration_end
    ):
        raise ValueError("confirmation and calibration seed blocks must be disjoint")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty confirmation output: {output}")
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, z_target, delays, onset, _ = _generate(
            config, seed=seed, scenario=SCENARIO
        )
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
            print(f"completed confirmation streams: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(["seed", "method"], kind="stable")
    expected = config.seeds * len(METHODS)
    if len(frame) != expected or frame.duplicated(["seed", "method"]).any():
        raise RuntimeError("confirmation row/key integrity failed")
    if set(frame.method.unique()) != set(METHODS):
        raise RuntimeError("confirmation methods are incomplete")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("hard label cap failed")
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
    candidate_detected = paired.alarm_after_onset_candidate.astype(bool).to_numpy()
    uniform_detected = paired.alarm_after_onset_uniform.astype(bool).to_numpy()
    differences = candidate_detected.astype(float) - uniform_detected.astype(float)
    wins = int(np.sum(candidate_detected & ~uniform_detected))
    losses = int(np.sum(~candidate_detected & uniform_detected))
    discordant = wins + losses
    p_value = float(
        binomtest(wins, discordant, p=0.5, alternative="greater").pvalue if discordant else 1.0
    )
    rng = np.random.default_rng(config.seed_offset + 1_733_071)
    detection_ci = _bootstrap_interval(differences, rng=rng)
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
        "candidate_detection_rate": float(candidate_detected.mean()),
        "uniform_detection_rate": float(uniform_detected.mean()),
        "detection_difference": float(differences.mean()),
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
            (
                candidate.alarm & candidate.alarm_event.lt(config.n_target * config.onset_fraction)
            ).sum()
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
        "experiment": "delayed_evidence_directed_ppi_disjoint_harm_confirmation",
        "config": asdict(config),
        "scenario": SCENARIO,
        "candidate": CANDIDATE,
        "reference": REFERENCE,
        "calibration_manifest_sha256": hashlib.sha256(calibration_bytes).hexdigest(),
        "rows": len(frame),
        "result": result,
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "source_hashes": {
            "confirmation": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "development_module": hashlib.sha256(
                Path(__file__).with_name("delayed_evidence_directed_ppi.py").read_bytes()
            ).hexdigest(),
        },
        "limitations": [
            "Power comparison on the single registered synthetic alternative; independent null calibration is a separate necessary gate.",
            "The candidate is an established evidence-directed query rule with a predictable-bound e-process, not a new algorithm or theorem.",
            "No result establishes validity under serial dependence, informative missingness, changing policies, or real decision costs.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"confirmation gate: {'PASS' if result['gate_pass'] else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20282000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path("outputs/delayed_evidence_directed_ppi_calibration_1000/manifest.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_directed_ppi_confirmation_1000"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running delayed PPI confirmation on cuda/CPU generation: {config.device}", flush=True)
    run(config, args.output_dir, calibration_manifest=args.calibration_manifest)


if __name__ == "__main__":
    main()
