"""Development grid for fixed-delay PPI detection across harm doses and onsets."""

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

SEED_OFFSET = 20_440_000
SEEDS = 200
HARM_SHIFTS = (0.10, 0.20, 0.30)
ONSET_FRACTIONS = (0.25, 0.50, 0.75)
CANDIDATE = "evidence_a0p025_p0p5_eventwise"
REFERENCE = "uniform_eventwise"
METHODS = (CANDIDATE, REFERENCE)
WORKERS = 4
PROTOCOL = Path("docs/delayed_ppi_fixed12_dose_onset_grid_protocol.md")


def _run_cell(task: tuple[Config, float, float, list[tuple]]):
    config, harm_shift, onset_fraction, streams = task
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
            row["harm_shift"] = harm_shift
            row["onset_fraction"] = onset_fraction
            rows.append(row)
    return rows


def run(*, device: str, output: Path, protocol: Path = PROTOCOL) -> Path:
    base_config = Config(seeds=SEEDS, seed_offset=SEED_OFFSET, device=device)
    base_config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol.read_bytes()

    tasks = []
    resolved = ""
    for harm_shift in HARM_SHIFTS:
        for onset_fraction in ONSET_FRACTIONS:
            config = Config(
                seeds=SEEDS,
                seed_offset=SEED_OFFSET,
                harm_shift=harm_shift,
                onset_fraction=onset_fraction,
                device=device,
            )
            streams = []
            for i in range(SEEDS):
                seed = SEED_OFFSET + i
                x_source, z_source, x_target, z_target, _delays, onset, resolved = _generate(
                    config, seed=seed, scenario="boundary_harm"
                )
                streams.append((seed, x_source, z_source, x_target, z_target, onset))
            tasks.append((config, harm_shift, onset_fraction, streams))
            print(
                f"generated CUDA grid cell: shift={harm_shift:.2f}, onset={onset_fraction:.2f}",
                flush=True,
            )

    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=get_context("spawn")) as executor:
        futures = [executor.submit(_run_cell, task) for task in tasks]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"completed dose/onset cell: {completed}/9", flush=True)

    frame = pd.DataFrame(rows).sort_values(
        ["harm_shift", "onset_fraction", "seed", "method"], kind="stable"
    )
    keys = ["seed", "harm_shift", "onset_fraction", "method"]
    expected = SEEDS * len(HARM_SHIFTS) * len(ONSET_FRACTIONS) * len(METHODS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("dose/onset row-key integrity failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("pathwise label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    pivots = frame.pivot(
        index=["seed", "harm_shift", "onset_fraction"],
        columns="method",
        values=["alarm_after_onset", "labels_queried"],
    )
    detection_diff = pivots["alarm_after_onset"][CANDIDATE].astype(float) - pivots[
        "alarm_after_onset"
    ][REFERENCE].astype(float)
    label_diff = pivots["labels_queried"][CANDIDATE].astype(float) - pivots["labels_queried"][
        REFERENCE
    ].astype(float)
    seed_detection = detection_diff.groupby(level="seed").mean()
    seed_labels = label_diff.groupby(level="seed").mean()
    rng = np.random.default_rng(SEED_OFFSET + 5_240_117)
    macro_detection_ci = _bootstrap_interval(seed_detection.to_numpy(), rng=rng)
    macro_label_ci = _bootstrap_interval(seed_labels.to_numpy(), rng=rng)

    cell_rows = []
    for (shift, onset_fraction), group in frame.groupby(
        ["harm_shift", "onset_fraction"], sort=True
    ):
        candidate = group[group.method.eq(CANDIDATE)].sort_values("seed")
        reference = group[group.method.eq(REFERENCE)].sort_values("seed")
        cand_detect = candidate.alarm_after_onset.astype(bool).to_numpy()
        ref_detect = reference.alarm_after_onset.astype(bool).to_numpy()
        diff = cand_detect.astype(float) - ref_detect.astype(float)
        wins = int(np.sum(cand_detect & ~ref_detect))
        losses = int(np.sum(~cand_detect & ref_detect))
        discordant = wins + losses
        cell_rng = np.random.default_rng(
            SEED_OFFSET + int(shift * 1000) + int(onset_fraction * 10000)
        )
        ci = _bootstrap_interval(diff, rng=cell_rng)
        cell_rows.append(
            {
                "harm_shift": shift,
                "onset_fraction": onset_fraction,
                "streams": SEEDS,
                "candidate_detections": int(cand_detect.sum()),
                "candidate_rate": float(cand_detect.mean()),
                "uniform_detections": int(ref_detect.sum()),
                "uniform_rate": float(ref_detect.mean()),
                "paired_detection_difference": float(diff.mean()),
                "paired_detection_ci95_low": ci[0],
                "paired_detection_ci95_high": ci[1],
                "candidate_only": wins,
                "uniform_only": losses,
                "mcnemar_one_sided_p_descriptive": float(
                    binomtest(wins, discordant, p=0.5, alternative="greater").pvalue
                    if discordant
                    else 1.0
                ),
                "candidate_mean_labels": float(candidate.labels_queried.mean()),
                "uniform_mean_labels": float(reference.labels_queried.mean()),
                "mean_label_difference": float(
                    candidate.labels_queried.mean() - reference.labels_queried.mean()
                ),
                "candidate_pre_onset_alarms": int(
                    (candidate.alarm & candidate.alarm_event.lt(candidate.onset_event)).sum()
                ),
                "candidate_mean_event_delay": float(candidate.event_delay_after_onset.mean()),
                "candidate_mean_wall_delay": float(candidate.wall_delay_after_onset.mean()),
            }
        )
    summary = pd.DataFrame(cell_rows).sort_values(["harm_shift", "onset_fraction"])
    summary.to_csv(output / "cell_summary.csv", index=False)
    summary.to_parquet(output / "cell_summary.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    macro = {
        "design_cells": len(HARM_SHIFTS) * len(ONSET_FRACTIONS),
        "seed_clusters": SEEDS,
        "equal_weight_macro_detection_difference": float(seed_detection.mean()),
        "seed_cluster_bootstrap_95_low": macro_detection_ci[0],
        "seed_cluster_bootstrap_95_high": macro_detection_ci[1],
        "equal_weight_macro_label_difference": float(seed_labels.mean()),
        "label_seed_cluster_bootstrap_95_low": macro_label_ci[0],
        "label_seed_cluster_bootstrap_95_high": macro_label_ci[1],
        "worst_cell_detection_difference": float(summary.paired_detection_difference.min()),
        "development_nomination_gate": bool(
            macro_detection_ci[0] > 0
            and seed_labels.mean() <= 0
            and summary.paired_detection_difference.min() >= -0.05
        ),
    }
    summary_records = (
        summary.astype(object).where(pd.notna(summary), None).to_dict(orient="records")
    )
    (output / "macro_result.json").write_text(json.dumps(macro, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "delayed_ppi_fixed12_dose_onset_development_grid",
        "base_config": asdict(base_config),
        "harm_shifts": list(HARM_SHIFTS),
        "onset_fractions": list(ONSET_FRACTIONS),
        "methods": list(METHODS),
        "delay_profile": "fixed12",
        "seed_range_per_cell": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "rows": len(frame),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("delayed_evidence_directed_ppi.py"),
                Path(__file__).with_name("eprocess.py"),
            )
        },
        "runtime": environment(),
        "resolved_device": resolved,
        "workers": WORKERS,
        "macro_result": macro,
        "cell_summary": summary_records,
        "invariants_pass": bool(
            len(frame) == expected
            and not frame.duplicated(keys).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "interpretation": "Development screen only; cellwise p-values and intervals are descriptive, and the macro interval applies only to the equally weighted registered nine-cell design.",
        "created_utc": datetime.now(UTC).isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in sorted(output.iterdir()):
        if path.name != "checksums.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with (output / "checksums.sha256").open("a", encoding="utf-8") as handle:
                handle.write(f"{digest}  {path.name}\n")
    print(json.dumps(macro, indent=2), flush=True)
    print(summary.to_string(index=False), flush=True)
    print(
        f"fixed12 dose/onset development nomination: {'PASS' if macro['development_nomination_gate'] else 'FAIL'}",
        flush=True,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/delayed_ppi_fixed12_dose_onset_grid_200")
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    run(device=args.device, output=args.output_dir, protocol=args.protocol)


if __name__ == "__main__":
    main()
