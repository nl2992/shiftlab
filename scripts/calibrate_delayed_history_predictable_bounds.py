"""Run the frozen independent null calibration for delayed history-only PPI."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
    )
    from scripts.validate_delayed_history_predictable_bounds import (
        simulate_delayed_arm,
    )
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
    )
    from validate_delayed_history_predictable_bounds import simulate_delayed_arm

DEFAULT_SEED = 27304027
HORIZON = 2400
ARMS = ("fixed", "predictable")
SCENARIOS = (NULL_SCENARIO, STRICT_NEGATIVE_SCENARIO)
FAMILY_ALPHA = 0.05


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_one_sided_upper(successes: int, total: int, alpha: float) -> float:
    if not 0 <= successes <= total or total <= 0 or not 0 < alpha < 1:
        raise ValueError("invalid binomial confidence-limit arguments")
    if successes == total:
        return 1.0
    return float(beta.ppf(1 - alpha, successes + 1, total - successes))


def run(*, streams: int, seed: int, delay: int, device_name: str, output: Path) -> Path:
    if streams < 2000:
        raise ValueError("independent calibration requires at least 2,000 streams per cell")
    if seed < DEFAULT_SEED:
        raise ValueError(f"calibration seeds must start at {DEFAULT_SEED} or later")
    if delay != 12:
        raise ValueError("the frozen calibration delay is 12 events")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(device_name)
    protocol_path = Path(
        "docs/delayed_history_predictable_calibration_protocol.md"
        if seed == DEFAULT_SEED
        else "docs/delayed_history_predictable_selected_calibration_protocol.md"
    )
    rows: list[dict[str, object]] = []

    for scenario_index, scenario in enumerate(SCENARIOS):
        scenario_seed = seed + scenario_index * streams
        common = generate_common_random_numbers(
            streams=streams, horizon=HORIZON, seed=scenario_seed, device=device
        )
        for arm in ARMS:
            arm_rows = simulate_delayed_arm(
                scenario=scenario,
                streams=streams,
                horizon=HORIZON,
                seed=scenario_seed,
                data=common,
                device=device,
                delay=delay,
                bound_mode=arm,
            )
            rows.extend(arm_rows)
            print(
                f"completed scenario={scenario} arm={arm} streams={len(arm_rows)}",
                flush=True,
            )

    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(SCENARIOS) * len(ARMS)
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} stream-arm rows, got {len(metrics)}")
    if metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("duplicate scenario-arm-stream metrics")
    if not metrics["budget_respected"].all():
        raise RuntimeError("at least one stream exceeded its hard request cap")

    alpha_cell = FAMILY_ALPHA / (len(SCENARIOS) * len(ARMS))
    calibration_rows = []
    for (scenario, arm), group in metrics.groupby(["scenario", "bound_mode"], sort=True):
        alarms = int(group["false_escalation"].sum())
        upper = exact_one_sided_upper(alarms, len(group), alpha_cell)
        calibration_rows.append(
            {
                "scenario": scenario,
                "arm": arm,
                "streams": len(group),
                "false_escalations": alarms,
                "false_rate": alarms / len(group),
                "simultaneous_one_sided_95_upper": upper,
                "per_cell_alpha": alpha_cell,
                "passes_5pct_calibration_gate": upper <= 0.05,
                "mean_labels": float(group["labels_queried"].mean()),
                "mean_events_processed": float(group["events_processed"].mean()),
            }
        )
    calibration = pd.DataFrame(calibration_rows)
    if len(calibration) != 4:
        raise RuntimeError("calibration family is incomplete")

    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics").mkdir()
    (output / "reports").mkdir()
    metrics_path = output / "metrics/stream_metrics.parquet"
    calibration_path = output / "metrics/calibration_summary.csv"
    metrics.to_parquet(metrics_path, index=False)
    calibration.to_csv(calibration_path, index=False)
    gate = bool(calibration["passes_5pct_calibration_gate"].all())
    report = [
        "# Delayed history-predictable independent null calibration",
        "",
        f"- Streams per scenario and arm: {streams}",
        f"- Total stream-arm rows: {len(metrics)}",
        f"- Horizon / fixed delay / hard cap: {HORIZON} / {delay} / 480 labels",
        f"- Root seed: {seed}; stream generation: {device}; sequential monitor replay: CPU NumPy.",
        f"- Four-cell Bonferroni family uses per-cell alpha {alpha_cell:.5f}.",
        f"- Frozen protocol: `{protocol_path.as_posix()}`.",
        f"- Calibration gate: {'PASS' if gate else 'FAIL'}.",
        "- A pass applies only to the registered iid synthetic controls and stated filtration. It does not establish power, serial-dependence validity, or novelty.",
        "- No figure was generated; PaperBanana is unavailable in this environment.",
        "",
        calibration.to_markdown(index=False, floatfmt=".5f"),
    ]
    report_path = output / "reports/calibration_results.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    gpu_name = torch.cuda.get_device_name(0) if device.type == "cuda" else None
    manifest = {
        "experiment": "delayed_history_predictable_independent_null_calibration",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "configuration": {
            "streams_per_scenario_per_arm": streams,
            "horizon": HORIZON,
            "seed_root": seed,
            "scenario_seed_ranges": {
                scenario: [seed + i * streams, seed + (i + 1) * streams - 1]
                for i, scenario in enumerate(SCENARIOS)
            },
            "delay": delay,
            "generation_device": str(device),
            "gpu_name": gpu_name,
            "monitor_backend": "numpy_cpu_event_order",
            "scenarios": SCENARIOS,
            "arms": ARMS,
            "label_budget_rate": 0.20,
            "hard_label_cap": math.floor(0.20 * HORIZON),
            "q_min": 0.05,
            "q_max": 0.80,
            "family_alpha": FAMILY_ALPHA,
            "per_cell_alpha": alpha_cell,
            "calibration_gate_passed": gate,
            "protocol": protocol_path.as_posix(),
        },
        "runtime": {
            "python": __import__("platform").python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "rows": len(metrics),
        "sha256": {
            "runner": sha256(Path(__file__).resolve()),
            "delayed_simulator": sha256(
                Path("scripts/validate_delayed_history_predictable_bounds.py")
            ),
            "shared_dgp": sha256(Path("scripts/calibrate_history_predictable_query_bounds.py")),
            "protocol": sha256(protocol_path),
            "metrics/stream_metrics.parquet": sha256(metrics_path),
            "metrics/calibration_summary.csv": sha256(calibration_path),
            "reports/calibration_results.md": sha256(report_path),
        },
        "limitations": [
            "iid event records only",
            "deterministic outcome-independent feedback delay only",
            "fixed action pair and complete queried labels",
            "finite-run calibration is not a proof of filtration assumptions",
            "no harm-power confirmation is included",
        ],
    }
    (output / "reports/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--delay", type=int, default=12)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/delayed_history_predictable_calibration_2000")
    )
    args = parser.parse_args()
    print(
        run(
            streams=args.streams,
            seed=args.seed,
            delay=args.delay,
            device_name=args.device,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
