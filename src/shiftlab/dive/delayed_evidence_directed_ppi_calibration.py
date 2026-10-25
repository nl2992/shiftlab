"""Independent null calibration for the frozen delayed history-directed PPI rule."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from scipy.stats import beta

from ..data.gpu.environment import environment
from .delayed_evidence_directed_ppi import (
    METHODS,
    Config,
    _generate,
    _simulate_method,
)

CALIBRATION_METHODS = ("uniform_eventwise", "evidence_a0p025_p0p5_eventwise")
CALIBRATION_SCENARIOS = ("stationary", "benign_variance_shift")
FAMILYWISE_ALPHA = 0.05


def exact_upper(successes: int, trials: int, *, cell_alpha: float) -> float:
    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("successes and trials must be integers")
    if trials < 1 or not 0 <= successes <= trials or not 0 < cell_alpha < 1:
        raise ValueError("invalid exact binomial interval inputs")
    if successes == trials:
        return 1.0
    return float(beta.ppf(1 - cell_alpha, successes + 1, trials - successes))


def run(config: Config, output: Path) -> Path:
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty calibration output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for scenario in CALIBRATION_SCENARIOS:
        for i in range(config.seeds):
            seed = config.seed_offset + i
            x_source, z_source, x_target, z_target, delays, onset, _ = _generate(
                config, seed=seed, scenario=scenario
            )
            for method in CALIBRATION_METHODS:
                rows.append(
                    _simulate_method(
                        config,
                        seed=seed,
                        scenario=scenario,
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
                print(f"completed {scenario}: {i + 1}/{config.seeds} seeds", flush=True)

    frame = pd.DataFrame(rows).sort_values(["scenario", "seed", "method"], kind="stable")
    expected_rows = len(CALIBRATION_SCENARIOS) * config.seeds * len(CALIBRATION_METHODS)
    if len(frame) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, found {len(frame)}")
    if frame.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("duplicate calibration keys")
    if set(frame.method.unique()) != set(CALIBRATION_METHODS):
        raise RuntimeError("missing or unexpected methods in calibration")
    if set(frame.scenario.unique()) != set(CALIBRATION_SCENARIOS):
        raise RuntimeError("missing or unexpected calibration scenarios")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("hard label cap failed in calibration")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("delayed-label event-prefix integrity failed")

    cell_alpha = FAMILYWISE_ALPHA / (len(CALIBRATION_METHODS) * len(CALIBRATION_SCENARIOS))
    summary = frame.groupby(["scenario", "method"], as_index=False).agg(
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
        "experiment": "delayed_evidence_directed_ppi_independent_null_calibration",
        "config": asdict(config),
        "methods": list(CALIBRATION_METHODS),
        "scenarios": list(CALIBRATION_SCENARIOS),
        "familywise_alpha": FAMILYWISE_ALPHA,
        "cell_alpha": cell_alpha,
        "rows": len(frame),
        "candidate_methods_registered_in_grid": list(METHODS),
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
            and not frame.duplicated(["scenario", "seed", "method"]).any()
            and frame.budget_respected.astype(bool).all()
            and frame.pending_labels.eq(0).all()
            and frame.events_registered.eq(frame.events_updated).all()
        ),
        "limitations": [
            "Monte Carlo calibration only for the frozen IID synthetic null family, propensity rule, support, proxy, and resolved-prefix implementation.",
            "It does not establish power, robustness to serial dependence, non-random feedback, changing policy pairs, or real-world validity.",
            "All methods use established evidence-directed query and bounded-mean e-process constructions; no novelty claim is made.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"calibration gate: {'PASS' if manifest['gate_pass'] else 'FAIL'}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=20280000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/delayed_evidence_directed_ppi_calibration_1000"),
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running independent delayed PPI null calibration on {config.device}", flush=True)
    run(config, args.output_dir)


if __name__ == "__main__":
    main()
