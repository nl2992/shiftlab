"""Development grid for predictable uniform mixtures of adaptive PPI queries."""

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

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _generate, _simulate_method

SEED_OFFSET = 20_450_000
SEEDS = 100
HARM_SHIFTS = (0.10, 0.20, 0.30)
ONSET_FRACTIONS = (0.25, 0.50, 0.75)
BLEND_WEIGHTS = (0.25, 0.50, 0.75)
EVIDENCE = "evidence_a0p025_p0p5_eventwise"
UNIFORM = "uniform_eventwise"
METHODS = (UNIFORM, EVIDENCE, *(f"evidence_blend_{int(w * 100):02d}_a0p025_p0p5_eventwise" for w in BLEND_WEIGHTS))
WORKERS = 4
PROTOCOL = Path("docs/delayed_ppi_uniform_mixture_grid_protocol.md")


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


def _bootstrap(values: np.ndarray, *, seed: int, draws: int = 20_000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[indices].mean(axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return float(lower), float(upper)


def run(*, device: str, output: Path, protocol: Path = PROTOCOL) -> Path:
    base = Config(seeds=SEEDS, seed_offset=SEED_OFFSET, device=device).validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    tasks = []
    resolved = ""
    for shift in HARM_SHIFTS:
        for onset_fraction in ONSET_FRACTIONS:
            config = Config(
                seeds=SEEDS,
                seed_offset=SEED_OFFSET,
                harm_shift=shift,
                onset_fraction=onset_fraction,
                device=device,
            )
            streams = []
            for i in range(SEEDS):
                seed = SEED_OFFSET + i
                xs, zs, xt, zt, _delays, onset, resolved = _generate(
                    config, seed=seed, scenario="boundary_harm"
                )
                streams.append((seed, xs, zs, xt, zt, onset))
            tasks.append((config, shift, onset_fraction, streams))
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=get_context("spawn")) as executor:
        futures = [executor.submit(_run_cell, task) for task in tasks]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"completed uniform-mixture grid cell: {completed}/9", flush=True)

    frame = pd.DataFrame(rows).sort_values(
        ["harm_shift", "onset_fraction", "seed", "method"], kind="stable"
    )
    keys = ["seed", "harm_shift", "onset_fraction", "method"]
    expected = SEEDS * len(HARM_SHIFTS) * len(ONSET_FRACTIONS) * len(METHODS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("uniform-mixture grid row-key integrity failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("pathwise label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    summary_rows: list[dict[str, object]] = []
    macro = {}
    for method in METHODS[1:]:
        compare = frame[frame.method.isin([method, UNIFORM])].pivot(
            index=["seed", "harm_shift", "onset_fraction"],
            columns="method",
            values=["alarm_after_onset", "labels_queried"],
        )
        detection = (
            compare["alarm_after_onset"][method].astype(float)
            - compare["alarm_after_onset"][UNIFORM].astype(float)
        )
        labels = (
            compare["labels_queried"][method].astype(float)
            - compare["labels_queried"][UNIFORM].astype(float)
        )
        by_seed = detection.groupby(level="seed").mean().to_numpy()
        label_by_seed = labels.groupby(level="seed").mean().to_numpy()
        ci = _bootstrap(by_seed, seed=SEED_OFFSET + len(summary_rows) + 811)
        label_ci = _bootstrap(label_by_seed, seed=SEED_OFFSET + len(summary_rows) + 812)
        cell_diffs = detection.groupby(level=["harm_shift", "onset_fraction"]).mean()
        label_mean = float(labels.mean())
        nominated = bool(ci[0] > 0 and label_mean <= 0 and float(cell_diffs.min()) >= -0.05)
        macro[method] = {
            "macro_detection_difference_vs_uniform": float(by_seed.mean()),
            "seed_cluster_bootstrap_95": list(ci),
            "macro_label_difference_vs_uniform": label_mean,
            "label_seed_cluster_bootstrap_95": list(label_ci),
            "worst_cell_detection_difference": float(cell_diffs.min()),
            "nomination_gate": nominated,
        }
        summary_rows.append(
            {
                "method": method,
                **macro[method],
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output / "method_summary.csv", index=False)
    summary.to_parquet(output / "method_summary.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    (output / "macro_result.json").write_text(json.dumps(macro, indent=2) + "\n", encoding="utf-8")
    protocol_bytes = protocol.read_bytes()
    manifest = {
        "experiment": "delayed_ppi_uniform_mixture_development_grid",
        "base_config": asdict(base),
        "harm_shifts": list(HARM_SHIFTS),
        "onset_fractions": list(ONSET_FRACTIONS),
        "blend_weights": list(BLEND_WEIGHTS),
        "methods": list(METHODS),
        "delay_profile": "fixed12",
        "seed_range_per_cell": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "rows": len(frame),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), Path(__file__).with_name("delayed_evidence_directed_ppi.py"))
        },
        "runtime": environment(),
        "resolved_device": resolved,
        "workers": WORKERS,
        "macro_results": macro,
        "invariants_pass": True,
        "interpretation": "Post-selection development screen only; any nominated fixed blend requires independent null calibration and disjoint harm confirmation.",
        "created_utc": datetime.now(UTC).isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with (output / "checksums.sha256").open("w", encoding="utf-8") as handle:
        for path in sorted(output.iterdir()):
            if path.name != "checksums.sha256":
                handle.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    print(json.dumps(macro, indent=2), flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/delayed_ppi_uniform_mixture_grid_100")
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    run(device=args.device, output=args.output_dir, protocol=args.protocol)


if __name__ == "__main__":
    main()
