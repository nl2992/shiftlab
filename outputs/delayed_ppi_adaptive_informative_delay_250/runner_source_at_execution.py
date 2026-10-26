"""Null calibration for adaptive delayed PPI with outcome-dependent label latency."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path

import pandas as pd

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _generate, _simulate_method
from .delayed_evidence_directed_ppi_calibration import exact_upper

SEED_OFFSET = 20_410_000
SEEDS = 250
METHODS = ("uniform_eventwise", "evidence_a0p025_p0p5_eventwise")
MONITORS = ("full_stream", "fixed_start_mixture")
DELAY_PROFILES = ("fixed12", "positive_fast", "positive_slow")
STARTS = tuple(range(0, 2400, 300))
FAMILYWISE_ALPHA = 0.05
PROTOCOL = Path("docs/delayed_ppi_adaptive_informative_delay_protocol.md")


def _outcome_delays(z: pd.Series, profile: str) -> list[int]:
    if profile == "fixed12":
        return [12] * len(z)
    if profile == "positive_fast":
        return [0 if value > 0 else 12 for value in z]
    if profile == "positive_slow":
        return [12 if value > 0 else 0 for value in z]
    raise ValueError(f"unknown delay profile {profile}")


def _run_cell(task: tuple[Config, str, str, str, list[tuple]]):
    config, profile, method, monitor, streams = task
    rows: list[dict[str, object]] = []
    for seed, x_source, z_source, x_target, z_target, onset in streams:
        row = _simulate_method(
            config,
            seed=seed,
            scenario="stationary",
            method=method,
            x_source=x_source,
            z_source=z_source,
            x_target=x_target,
            z_target=z_target,
            delays=_outcome_delays(pd.Series(z_target), profile),
            onset=onset,
            monitor_variant=monitor,
            monitor_starts=STARTS if monitor == "fixed_start_mixture" else (),
            continue_after_alarm=True,
        )
        row["delay_profile"] = profile
        row["monitor_variant"] = monitor
        rows.append(row)
    return rows


def run(*, device: str, output: Path, protocol: Path = PROTOCOL) -> Path:
    config = Config(seeds=SEEDS, seed_offset=SEED_OFFSET, device=device)
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol.read_bytes()
    streams: list[tuple] = []
    resolved = ""
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, z_target, _base_delays, onset, resolved = _generate(
            config, seed=seed, scenario="stationary"
        )
        streams.append((seed, x_source, z_source, x_target, z_target, onset))
        if (i + 1) % 50 == 0:
            print(
                f"generated source/target streams on {resolved}: {i + 1}/{config.seeds}",
                flush=True,
            )

    tasks = [
        (config, profile, method, monitor, streams)
        for profile in DELAY_PROFILES
        for method in METHODS
        for monitor in MONITORS
    ]
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as executor:
        futures = [executor.submit(_run_cell, task) for task in tasks]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"completed adaptive informative-delay arm: {completed}/{len(tasks)}", flush=True)
    for row in rows:
        row["resolved_device"] = resolved

    frame = pd.DataFrame(rows).sort_values(
        ["delay_profile", "method", "monitor_variant", "seed"], kind="stable"
    )
    keys = ["seed", "delay_profile", "method", "monitor_variant"]
    expected = SEEDS * len(DELAY_PROFILES) * len(METHODS) * len(MONITORS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("row/key integrity failed")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("pathwise label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    cell_alpha = FAMILYWISE_ALPHA / (len(DELAY_PROFILES) * len(METHODS) * len(MONITORS))
    summary = (
        frame.groupby(["delay_profile", "method", "monitor_variant"], as_index=False)
        .agg(
            streams=("seed", "count"),
            false_escalations=("alarm", "sum"),
            alarm_rate=("alarm", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("events_updated", "mean"),
            mean_alarm_event=("alarm_event", lambda x: x[x.notna()].mean()),
            mean_alarm_wall=("alarm_wall_time", lambda x: x[x.notna()].mean()),
            cap_violations=("budget_respected", lambda x: int((~x.astype(bool)).sum())),
        )
        .sort_values(["delay_profile", "method", "monitor_variant"], kind="stable")
    )
    summary["simultaneous_95_one_sided_upper"] = [
        exact_upper(int(k), int(n), cell_alpha=cell_alpha)
        for k, n in zip(summary.false_escalations, summary.streams, strict=True)
    ]
    summary["cell_alpha"] = cell_alpha
    summary["cell_pass"] = summary.simultaneous_95_one_sided_upper.le(0.05)
    summary.to_csv(output / "cell_summary.csv", index=False)
    summary.to_parquet(output / "cell_summary.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    manifest = {
        "experiment": "adaptive_delayed_ppi_outcome_dependent_delay_null_calibration",
        "config": asdict(config),
        "scenario": "stationary_iid_context_and_outcomes",
        "methods": list(METHODS),
        "monitor_variants": list(MONITORS),
        "delay_profiles": list(DELAY_PROFILES),
        "start_events": list(STARTS),
        "familywise_alpha": FAMILYWISE_ALPHA,
        "cell_alpha": cell_alpha,
        "rows": len(frame),
        "seed_range": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
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
        "resolved_device": str(frame.resolved_device.iloc[0]),
        "summary": summary.to_dict(orient="records"),
        "calibration_gate_pass": bool(summary.cell_pass.all()),
        "invariants_pass": bool(
            len(frame) == expected
            and not frame.duplicated(keys).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "conditional_null": "E[Z_t | complete prior event history] = 0 <= epsilon; current X_t is fresh and symmetric, and the propensity is chosen from the prior resolved prefix.",
        "limitations": [
            "Finite calibration for the registered IID synthetic process and three finite outcome-dependent delay rules only.",
            "Delay is not used as evidence; the screen does not cover non-arrival or delayed features.",
            "The screen does not establish power, arbitrary dependence validity, or real-world performance.",
            "Both query and monitor constructions are established methods; no novelty claim is made.",
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
    print(
        f"informative-delay null calibration: {'PASS' if manifest['calibration_gate_pass'] else 'FAIL'}",
        flush=True,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_ppi_adaptive_informative_delay_250"),
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    run(device=args.device, output=args.output_dir, protocol=args.protocol)


if __name__ == "__main__":
    main()
