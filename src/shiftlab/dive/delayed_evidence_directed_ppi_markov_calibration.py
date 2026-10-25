"""Null calibration under persistent outcome scale and delayed feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import torch

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import Config, _simulate_method
from .delayed_evidence_directed_ppi_calibration import exact_upper

METHODS = ("uniform_eventwise", "evidence_a0p025_p0p5_eventwise")
SCENARIO = "markov_variance_null"
FLIP_PROBABILITY = 0.05
AMPLITUDES = (0.55, 1.0)
FAMILYWISE_ALPHA = 0.05


def generate(config: Config, *, seed: int):
    """Generate persistent variance regimes with conditionally fair signs.

    The regime is evaluator-only. Since the sign at each event is fresh and
    fair conditional on the entire past and current regime, E[Z_t|G_(t-1)]=0
    despite persistent outcome scale.
    """
    device = torch.device(
        "cuda"
        if config.device == "auto" and torch.cuda.is_available()
        else "cpu"
        if config.device == "auto"
        else config.device
    )
    gen = torch.Generator(device=device).manual_seed(seed)

    def stream(n: int):
        initial = torch.randint(2, (), device=device, generator=gen)
        flips = torch.rand(n, device=device, generator=gen) < FLIP_PROBABILITY
        regime = (initial + flips.to(torch.int64).cumsum(0)) % 2
        amplitude = torch.where(regime.bool(), AMPLITUDES[1], AMPLITUDES[0])
        signs = torch.where(torch.rand(n, device=device, generator=gen) < 0.5, -1.0, 1.0)
        contexts = torch.where(torch.rand(n, device=device, generator=gen) < 0.5, -1.0, 1.0)
        return contexts.cpu().numpy(), (amplitude * signs).cpu().numpy(), regime.cpu().numpy()

    x_source, z_source, _ = stream(config.n_source)
    x_target, z_target, regimes = stream(config.n_target)
    delays = (
        torch.randint(config.max_delay + 1, (config.n_target,), device=device, generator=gen)
        .cpu()
        .numpy()
        if config.max_delay
        else torch.zeros(config.n_target, dtype=torch.int64).numpy()
    )
    onset = config.n_target
    return x_source, z_source, x_target, z_target, delays, onset, regimes, str(device)


def run(config: Config, output: Path) -> Path:
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for i in range(config.seeds):
        seed = config.seed_offset + i
        x_source, z_source, x_target, z_target, delays, onset, _regimes, _ = generate(
            config, seed=seed
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
            print(f"completed Markov-null seeds: {i + 1}/{config.seeds}", flush=True)

    frame = pd.DataFrame(rows).sort_values(["seed", "method"], kind="stable")
    expected_rows = config.seeds * len(METHODS)
    if len(frame) != expected_rows or frame.duplicated(["seed", "method"]).any():
        raise RuntimeError("Markov calibration row/key integrity failed")
    if set(frame.method.unique()) != set(METHODS):
        raise RuntimeError("Markov calibration methods are incomplete")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("hard label cap failed in Markov calibration")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed event-prefix integrity failed")

    cell_alpha = FAMILYWISE_ALPHA / len(METHODS)
    summary = frame.groupby("method", as_index=False).agg(
        streams=("seed", "count"),
        false_escalations=("alarm", "sum"),
        alarm_rate=("alarm", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_events=("events_updated", "mean"),
        cap_violations=("budget_respected", lambda x: int((~x).sum())),
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
    frame.to_parquet(output / "metrics.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    manifest = {
        "experiment": "delayed_evidence_directed_ppi_markov_variance_null_calibration",
        "config": asdict(config),
        "methods": list(METHODS),
        "scenario": SCENARIO,
        "flip_probability": FLIP_PROBABILITY,
        "amplitudes": list(AMPLITUDES),
        "familywise_alpha": FAMILYWISE_ALPHA,
        "cell_alpha": cell_alpha,
        "rows": len(frame),
        "source_hashes": {
            "calibration": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "development_module": hashlib.sha256(
                Path(__file__).with_name("delayed_evidence_directed_ppi.py").read_bytes()
            ).hexdigest(),
        },
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "summary": summary.to_dict(orient="records"),
        "gate_pass": bool(summary.calibration_gate_cell_pass.all()),
        "invariants_pass": bool(
            len(frame) == expected_rows
            and not frame.duplicated(["seed", "method"]).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "conditional_null": "E[Z_t | complete prior event history] = 0: fresh fair signs are independent of the persistent amplitude regime.",
        "limitations": [
            "Finite Monte Carlo calibration for one IID-sign, persistent-scale Markov generator only.",
            "It does not establish validity for Markov-persistent signs, outcome-dependent delays, changing conditional means, or real data.",
            "The query policy and e-process are established constructions; this is not a novelty claim.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Markov calibration gate: {'PASS' if manifest['gate_pass'] else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20290000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_ppi_markov_calibration_1000"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running delayed Markov-variance null calibration on {config.device}", flush=True)
    run(config, args.output_dir)


if __name__ == "__main__":
    main()
