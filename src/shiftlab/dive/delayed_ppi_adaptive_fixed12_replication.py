"""Independent fixed-delay null replication for the adaptive PPI monitor."""

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
from .delayed_evidence_directed_ppi_calibration import exact_upper

SEED_OFFSET = 20_420_000
SEEDS = 2_000
METHOD = "evidence_a0p025_p0p5_eventwise"
PROFILE = "fixed12"
PROTOCOL = Path("docs/delayed_ppi_adaptive_fixed12_replication_protocol.md")
FAMILYWISE_ALPHA = 0.05
WORKERS = 4
CHUNKS = 4


def _run_chunk(
    task: tuple[Config, list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]]],
):
    config, streams = task
    rows: list[dict[str, object]] = []
    for seed, x_source, z_source, x_target, z_target, onset in streams:
        delays = np.full(len(z_target), 12, dtype=np.int64)
        row = _simulate_method(
            config,
            seed=seed,
            scenario="stationary",
            method=METHOD,
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


def run(*, device: str, output: Path, protocol: Path = PROTOCOL) -> Path:
    config = Config(seeds=SEEDS, seed_offset=SEED_OFFSET, device=device)
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol.read_bytes()
    streams: list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]] = []
    resolved = ""
    for i in range(SEEDS):
        seed = SEED_OFFSET + i
        x_source, z_source, x_target, z_target, _delays, onset, resolved = _generate(
            config, seed=seed, scenario="stationary"
        )
        streams.append((seed, x_source, z_source, x_target, z_target, onset))
        if (i + 1) % 250 == 0:
            print(f"generated {i + 1}/{SEEDS} streams on {resolved}", flush=True)

    chunks = [streams[i::CHUNKS] for i in range(CHUNKS)]
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=get_context("spawn")) as executor:
        futures = [executor.submit(_run_chunk, (config, chunk)) for chunk in chunks]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"completed independent replay chunk: {completed}/{CHUNKS}", flush=True)

    frame = pd.DataFrame(rows).sort_values("seed", kind="stable")
    if len(frame) != SEEDS or frame.seed.duplicated().any():
        raise RuntimeError("seed row integrity failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("pathwise label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    false_escalations = int(frame.alarm.astype(bool).sum())
    upper = exact_upper(false_escalations, len(frame), cell_alpha=FAMILYWISE_ALPHA)
    summary = pd.DataFrame(
        [
            {
                "method": METHOD,
                "delay_profile": PROFILE,
                "monitor_variant": "full_stream",
                "streams": len(frame),
                "false_escalations": false_escalations,
                "alarm_rate": false_escalations / len(frame),
                "one_sided_95_upper": upper,
                "gate_pass": upper <= 0.05,
                "mean_labels_queried": float(frame.labels_queried.mean()),
                "mean_events_updated": float(frame.events_updated.mean()),
                "cap_violations": int((~frame.budget_respected.astype(bool)).sum()),
                "pending_labels_total": int(frame.pending_labels.sum()),
            }
        ]
    )
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    manifest = {
        "experiment": "adaptive_ppi_fixed12_independent_null_replication",
        "config": asdict(config),
        "method": METHOD,
        "delay_profile": PROFILE,
        "monitor_variant": "full_stream",
        "seed_range": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "rows": len(frame),
        "false_escalations": false_escalations,
        "alarm_rate": false_escalations / len(frame),
        "one_sided_95_exact_upper": upper,
        "calibration_gate_pass": upper <= 0.05,
        "invariants_pass": bool(
            len(frame) == SEEDS
            and not frame.seed.duplicated().any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("delayed_evidence_directed_ppi.py"),
                Path(__file__).with_name("delayed_evidence_directed_ppi_calibration.py"),
                Path(__file__).with_name("eprocess.py"),
            )
        },
        "runtime": environment(),
        "resolved_device": resolved,
        "workers": WORKERS,
        "chunks": CHUNKS,
        "summary": summary.to_dict(orient="records"),
        "conditional_null": "E[Z_t | complete prior event history] = 0 <= epsilon under the IID stationary synthetic generator.",
        "limitations": [
            "Independent finite calibration of one frozen synthetic cell only.",
            "Does not validate power, informative delays, persistent-sign dependence, or real data.",
            "Existing e-process and query allocation are established constructions; no novelty claim is made.",
        ],
        "created_utc": datetime.now(UTC).isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in sorted(output.iterdir()):
        if path.name != "checksums.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with (output / "checksums.sha256").open("a", encoding="utf-8") as handle:
                handle.write(f"{digest}  {path.name}\n")
    print(summary.to_string(index=False), flush=True)
    print(f"independent fixed12 calibration: {'PASS' if upper <= 0.05 else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_ppi_adaptive_fixed12_replication_2000"),
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    run(device=args.device, output=args.output_dir, protocol=args.protocol)


if __name__ == "__main__":
    main()
