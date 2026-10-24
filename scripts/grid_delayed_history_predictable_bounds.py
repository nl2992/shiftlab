"""Run the frozen development grid over delayed-feedback propensity floors."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import torch

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        HARM_SCENARIOS,
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
    )
    from scripts.validate_delayed_history_predictable_bounds import simulate_delayed_arm
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        HARM_SCENARIOS,
        NULL_SCENARIO,
        STRICT_NEGATIVE_SCENARIO,
        generate_common_random_numbers,
    )
    from validate_delayed_history_predictable_bounds import simulate_delayed_arm

DELAY_GRID = (1, 3, 12, 24)
Q_MIN_GRID = (0.05, 0.10, 0.15)
SCENARIOS = (NULL_SCENARIO, STRICT_NEGATIVE_SCENARIO, *HARM_SCENARIOS)
HORIZON = 2400
SEED_ROOT = 27404027


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*, streams: int, seed: int, device_name: str, output: Path) -> Path:
    if streams < 30:
        raise ValueError("the frozen development grid requires at least 30 streams per cell")
    if seed != SEED_ROOT:
        raise ValueError(f"the frozen development-grid seed is {SEED_ROOT}")
    if device_name not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    device = torch.device(device_name)
    rows: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        scenario_seed = seed + scenario_index * streams
        common = generate_common_random_numbers(
            streams=streams, horizon=HORIZON, seed=scenario_seed, device=device
        )
        for delay in DELAY_GRID:
            for q_min in Q_MIN_GRID:
                for arm in ("fixed", "predictable"):
                    results = simulate_delayed_arm(
                        scenario=scenario,
                        streams=streams,
                        horizon=HORIZON,
                        seed=scenario_seed,
                        data=common,
                        device=device,
                        delay=delay,
                        bound_mode=arm,
                        q_min=q_min,
                    )
                    for row in results:
                        row["q_min"] = q_min
                        rows.append(row)
                print(
                    f"completed scenario={scenario} delay={delay} q_min={q_min}",
                    flush=True,
                )

    metrics = pd.DataFrame(rows)
    expected = streams * len(SCENARIOS) * len(DELAY_GRID) * len(Q_MIN_GRID) * 2
    if len(metrics) != expected:
        raise RuntimeError(f"expected {expected} rows, got {len(metrics)}")
    keys = ["scenario", "feedback_delay", "q_min", "bound_mode", "stream_id"]
    if metrics.duplicated(keys).any():
        raise RuntimeError("duplicate grid stream rows")
    if not metrics["budget_respected"].all():
        raise RuntimeError("at least one grid cell violated its hard label cap")

    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics").mkdir()
    (output / "reports").mkdir()
    metrics_path = output / "metrics/stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    summary = (
        metrics.groupby(["scenario", "feedback_delay", "q_min", "bound_mode"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            detection_rate=("post_onset_detection", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_processed=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
        )
        .reset_index()
    )
    summary_path = output / "metrics/grid_summary.csv"
    summary.to_csv(summary_path, index=False)
    harm = metrics[metrics["scenario"].isin(HARM_SCENARIOS)]
    paired = harm.pivot(
        index=["scenario", "feedback_delay", "q_min", "stream_id"],
        columns="bound_mode",
        values=[
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    paired_rows = []
    for (scenario, delay, q_min), group in paired.groupby(level=[0, 1, 2], sort=True):
        for metric in (
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ):
            diff = group[metric]["predictable"].to_numpy(dtype=float) - group[metric][
                "fixed"
            ].to_numpy(dtype=float)
            paired_rows.append(
                {
                    "scenario": scenario,
                    "feedback_delay": delay,
                    "q_min": q_min,
                    "metric": metric,
                    "predictable_minus_fixed_mean": float(diff.mean()),
                }
            )
    paired_path = output / "metrics/paired_harm_differences.csv"
    pd.DataFrame(paired_rows).to_csv(paired_path, index=False)
    report_path = output / "reports/development_grid.md"
    report = [
        "# Delayed history-predictable propensity and latency grid",
        "",
        f"- Streams per scenario/configuration/arm: {streams}",
        f"- Total stream-arm rows: {len(metrics)}",
        f"- Horizon: {HORIZON}; label cap: 480; root seed: {seed}",
        f"- Stream generation device: {device}; sequential monitor replay: CPU NumPy.",
        "- All cells are development diagnostics. The small null cells do not calibrate the false-escalation rate.",
        "- The registered iid DGP and fixed outcome-independent delays support only the assumptions in `docs/delayed_history_predictable_bound_protocol.md`.",
        "- No research figure was generated because PaperBanana is unavailable in the active environment.",
        "",
        "## Full grid summary",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired harm differences",
        "",
        pd.DataFrame(paired_rows).to_markdown(index=False, floatfmt=".4f"),
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "delayed_history_predictable_propensity_latency_development_grid",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "configuration": {
            "streams_per_scenario_cell_arm": streams,
            "horizon": HORIZON,
            "seed_root": seed,
            "scenario_seed_ranges": {
                scenario: [seed + i * streams, seed + (i + 1) * streams - 1]
                for i, scenario in enumerate(SCENARIOS)
            },
            "delays": DELAY_GRID,
            "q_min_values": Q_MIN_GRID,
            "q_max": 0.80,
            "label_budget_rate": 0.20,
            "bound_arms": ("fixed", "predictable"),
            "generation_device": str(device),
            "monitor_backend": "numpy_cpu_event_order",
        },
        "rows": len(metrics),
        "sha256": {
            "runner": sha256(Path(__file__).resolve()),
            "simulator": sha256(Path("scripts/validate_delayed_history_predictable_bounds.py")),
            "shared_dgp": sha256(Path("scripts/calibrate_history_predictable_query_bounds.py")),
            "protocol": sha256(Path("docs/delayed_history_predictable_grid_protocol.md")),
            "metrics/stream_metrics.parquet": sha256(metrics_path),
            "metrics/grid_summary.csv": sha256(summary_path),
            "metrics/paired_harm_differences.csv": sha256(paired_path),
            "reports/development_grid.md": sha256(report_path),
        },
        "limitations": [
            "30-stream development screen only",
            "not a false-alarm calibration or confirmatory result",
            "iid events and deterministic outcome-independent delays only",
            "no serial-dependence or informative-delay claim",
            "no algorithm novelty claim",
        ],
    }
    (output / "reports/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=30)
    parser.add_argument("--seed", type=int, default=SEED_ROOT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/delayed_history_predictable_grid_30")
    )
    args = parser.parse_args()
    print(
        run(
            streams=args.streams,
            seed=args.seed,
            device_name=args.device,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
