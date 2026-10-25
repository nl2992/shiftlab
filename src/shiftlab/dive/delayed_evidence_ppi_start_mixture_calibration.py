"""Markov-scale null calibration for the matched shadow PPI monitors."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _simulate_method
from .delayed_evidence_directed_ppi_calibration import exact_upper
from .delayed_evidence_directed_ppi_markov_calibration import generate

QUERY_METHODS = ("evidence_a0p025_p0p5_eventwise",)
MONITOR_VARIANTS = ("full_stream", "fixed_start_mixture")
STARTS = tuple(range(0, 2400, 300))
SCENARIO = "markov_variance_null"
FAMILYWISE_ALPHA = 0.05


def run(config: Config, output: Path, *, protocol: Path) -> Path:
    config.validate()
    if config.n_target != STARTS[-1] + 300 or config.max_delay != 12:
        raise ValueError("the frozen Markov calibration requires 2,400 events and delays 0–12")
    protocol_bytes = protocol.read_bytes()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, z_target, delays, onset, _regimes, _device = generate(
            config, seed=seed
        )
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
                    query_driver_variant="full_stream",
                    continue_after_alarm=True,
                )
                row["monitor_variant"] = monitor_variant
                rows.append(row)
        if (i + 1) % 100 == 0:
            print(f"completed matched-shadow null streams: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(["seed", "method", "monitor_variant"], kind="stable")
    keys = ["seed", "method", "monitor_variant"]
    expected = config.seeds * len(QUERY_METHODS) * len(MONITOR_VARIANTS)
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("matched-shadow calibration row/key integrity failed")
    if set(frame.method.unique()) != set(QUERY_METHODS):
        raise RuntimeError("matched-shadow calibration query methods are incomplete")
    if set(frame.monitor_variant.unique()) != set(MONITOR_VARIANTS):
        raise RuntimeError("matched-shadow calibration monitors are incomplete")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("matched-shadow calibration exceeded its label cap")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("matched-shadow calibration delayed-prefix integrity failed")

    paired = frame.pivot(
        index=["seed", "method"],
        columns="monitor_variant",
        values=["query_schedule_sha256", "labels_queried", "events_updated"],
    )
    matched_fields = ("query_schedule_sha256", "labels_queried", "events_updated")
    matched_paths = all(
        (paired[field]["full_stream"] == paired[field]["fixed_start_mixture"]).all()
        for field in matched_fields
    )
    if not matched_paths:
        raise RuntimeError("matched-shadow calibration query paths or costs differ")

    family_cells = len(QUERY_METHODS) * len(MONITOR_VARIANTS)
    cell_alpha = FAMILYWISE_ALPHA / family_cells
    summary = (
        frame.groupby(["method", "monitor_variant"], as_index=False)
        .agg(
            streams=("seed", "count"),
            false_escalations=("alarm", "sum"),
            alarm_rate=("alarm", "mean"),
            mean_labels=("labels_queried", "mean"),
            cap_violations=("budget_respected", lambda values: int((~values).sum())),
        )
        .sort_values(["method", "monitor_variant"], kind="stable")
    )
    summary["simultaneous_one_sided_upper"] = [
        exact_upper(int(k), int(n), cell_alpha=cell_alpha)
        for k, n in zip(summary.false_escalations, summary.streams, strict=True)
    ]
    summary["cell_alpha"] = cell_alpha
    summary["calibration_gate_cell_pass"] = summary.simultaneous_one_sided_upper.le(
        FAMILYWISE_ALPHA
    )
    summary.to_csv(output / "calibration_summary.csv", index=False)
    summary.to_parquet(output / "calibration_summary.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    invariants_pass = bool(
        len(frame) == expected
        and not frame.duplicated(keys).any()
        and frame.budget_respected.astype(bool).all()
        and frame.pending_labels.eq(0).all()
        and frame.events_registered.eq(frame.events_updated).all()
        and matched_paths
    )
    manifest = {
        "experiment": "delayed_evidence_ppi_fixed_start_matched_shadow_markov_null_calibration",
        "config": asdict(config),
        "query_methods": list(QUERY_METHODS),
        "monitor_variants": list(MONITOR_VARIANTS),
        "start_events": list(STARTS),
        "start_weights": [1 / len(STARTS)] * len(STARTS),
        "query_driver": "full_stream",
        "continue_after_alarm": True,
        "scenario": SCENARIO,
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
        "familywise_alpha": FAMILYWISE_ALPHA,
        "cell_alpha": cell_alpha,
        "summary": summary.to_dict(orient="records"),
        "gate_pass": bool(summary.calibration_gate_cell_pass.all()),
        "invariants_pass": invariants_pass,
        "matched_query_paths_pass": matched_paths,
        "conditional_null": "E[Z_t | complete prior event history] = 0 under fresh fair sign innovations; the amplitude regime may be persistent.",
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "limitations": [
            "Finite calibration for one Markov-persistent-scale null with independent fair signs only.",
            "Does not cover persistent signs, informative delays, nonstationary conditional means, or real data.",
            "The fixed start mixture is a standard convex mixture of valid e-processes, not a novelty claim.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"matched-shadow Markov calibration gate: {'PASS' if manifest['gate_pass'] else 'FAIL'}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--seed-offset", type=int, default=20321000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/delayed_evidence_ppi_start_mixture_calibration_protocol.md"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_start_mixture_calibration_500"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running matched-shadow Markov null calibration on {config.device}", flush=True)
    run(config, args.output_dir, protocol=args.protocol)


if __name__ == "__main__":
    main()
