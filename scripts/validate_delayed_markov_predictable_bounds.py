"""Development screen for delayed-label monitoring under Markov volatility."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

try:
    from scripts.validate_delayed_history_predictable_bounds import simulate_delayed_arm
    from scripts.validate_markov_predictable_query_bounds import (
        DEFAULT_SEED,
        HARM_EFFECTS,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from validate_delayed_history_predictable_bounds import simulate_delayed_arm
    from validate_markov_predictable_query_bounds import (
        DEFAULT_SEED,
        HARM_EFFECTS,
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

try:
    from scripts.calibrate_history_predictable_query_bounds import HARM_ONSET_FRACTION
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from calibrate_history_predictable_query_bounds import HARM_ONSET_FRACTION

DEFAULT_OUTPUT = Path("outputs/delayed_markov_predictable_development_60")
DEFAULT_SEED_ROOT = 28104027
DELAYS = (1, 12)
SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO, *MARKOV_HARM_SCENARIOS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_evaluator_exposure(
    rows: list[dict[str, object]],
    *,
    states: np.ndarray,
    horizon: int,
) -> None:
    """Replace iid exposure shortcut with state-conditional Markov oracle costs."""
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    coefficient = np.where(states == 0, 4 / 3, 2 / 3)
    for row in rows:
        scenario = str(row["scenario"])
        effect = None
        for candidate, delta in zip(MARKOV_HARM_SCENARIOS, HARM_EFFECTS, strict=True):
            if scenario == candidate:
                effect = float(delta)
                break
        if effect is None:
            row["evaluator_cumulative_expected_harm_cost"] = 0.0
            continue
        stream = int(row["stream_id"])
        alarm = row["first_alarm_event"]
        stop = int(alarm) if alarm is not None else int(row["events_processed"]) - 1
        first = max(onset, 0)
        last = min(stop, horizon - 1)
        row["evaluator_cumulative_expected_harm_cost"] = (
            float(effect * coefficient[first : last + 1, stream].sum()) if first <= last else 0.0
        )


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_development(
    *,
    streams: int = 60,
    horizon: int = 2400,
    seed: int = DEFAULT_SEED_ROOT,
    device_name: str = "cuda",
    output: Path = DEFAULT_OUTPUT,
) -> Path:
    if streams < 30 or horizon < 100:
        raise ValueError("development screen requires at least 30 streams and horizon 100")
    if seed < DEFAULT_SEED_ROOT or seed < DEFAULT_SEED:
        raise ValueError(f"development seed must be at least {DEFAULT_SEED_ROOT}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")

    verify_dgp_algebra()
    device = torch.device(device_name)
    rows: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        # Scenario blocks have disjoint stream seeds. Every arm within a block
        # shares generated Markov states, contexts, outcomes and query uniforms.
        scenario_seed = seed + scenario_index * streams
        data = generate_markov_dependent_data(
            streams=streams,
            horizon=horizon,
            seed=scenario_seed,
            device=device,
        )
        states = data["regime_state"].detach().cpu().numpy()
        scenario_rows: list[dict[str, object]] = []
        for delay in DELAYS:
            for bound_mode in ("fixed", "predictable"):
                arm_rows = simulate_delayed_arm(
                    scenario=scenario,
                    streams=streams,
                    horizon=horizon,
                    seed=scenario_seed,
                    data=data,
                    device=device,
                    delay=delay,
                    bound_mode=bound_mode,
                    delay_profile="fixed",
                    q_min=0.05,
                )
                for row in arm_rows:
                    row["scenario"] = scenario
                    row["regime"] = "markov_volatility"
                    row["stream_seed_id"] = scenario_seed + int(row["stream_id"])
                    row["arm"] = f"delay_{delay}_{bound_mode}"
                    row["bound_mode"] = bound_mode
                    row["feedback_delay"] = delay
                    row["device_generation"] = str(device)
                scenario_rows.extend(arm_rows)
        add_evaluator_exposure(scenario_rows, states=states, horizon=horizon)
        rows.extend(scenario_rows)

    metrics = pd.DataFrame(rows)
    expected = streams * len(SCENARIOS) * len(DELAYS) * 2
    if len(metrics) != expected:
        raise RuntimeError(f"expected {expected} rows, received {len(metrics)}")
    if metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("duplicate scenario/arm/stream metrics")
    if not metrics["budget_respected"].all():
        raise RuntimeError("hard label cap was violated")
    if not metrics["onset_reached"].all() and metrics["scenario"].isin(MARKOV_HARM_SCENARIOS).any():
        # Nondetection from budget exhaustion is a valid result; preserve it in
        # the output and report it rather than treating it as a run failure.
        pass

    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    metrics_path = metrics_dir / "stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)

    summary = (
        metrics.groupby(["scenario", "feedback_delay", "bound_mode"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            false_escalation_rate=("false_escalation", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            detection_rate=("post_onset_detection", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events_processed=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    summary_path = metrics_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)

    paired_rows: list[dict[str, object]] = []
    for delay in DELAYS:
        subset = metrics[metrics["feedback_delay"] == delay]
        wide = subset.pivot(index=["scenario", "stream_id"], columns="bound_mode")
        for scenario in SCENARIOS:
            scenario_wide = wide.loc[scenario]
            for metric in (
                "post_onset_detection",
                "labels_queried",
                "events_processed",
                "evaluator_cumulative_expected_harm_cost",
            ):
                diff = scenario_wide[(metric, "predictable")].to_numpy(dtype=float) - scenario_wide[
                    (metric, "fixed")
                ].to_numpy(dtype=float)
                paired_rows.append(
                    {
                        "scenario": scenario,
                        "feedback_delay": delay,
                        "metric": metric,
                        "contrast": "predictable_minus_fixed",
                        "mean_difference": float(diff.mean()),
                        "streams": len(diff),
                    }
                )
    paired_path = metrics_dir / "paired_bound_differences.csv"
    pd.DataFrame(paired_rows).to_csv(paired_path, index=False)

    report_path = reports_dir / "development_results.md"
    report = [
        "# Delayed Markov-volatility development screen",
        "",
        f"- Streams per scenario and arm: {streams}",
        f"- Horizon: {horizon}; harm onset index: {math.floor(HARM_ONSET_FRACTION * horizon)}",
        f"- Feedback delays: {', '.join(map(str, DELAYS))} events; all labels resolve and evidence is committed in event order.",
        f"- Hard query budget: {math.floor(0.20 * horizon)} labels; q floor: 0.05.",
        f"- Requested/resolved generation device: {device}/{device}; monitor replay uses the existing CPU vectorized recursion.",
        "- This is a development screen. The 60-stream null cells are diagnostics and do not establish a 5% calibration gate.",
        "- The DGP's statewise conditional means are exactly zero on the exact-null control; the full-history martingale null and predictable-query assumptions are specific to this frozen Markov construction.",
        "- The learner receives no latent regime state. Oracle state-conditioned costs are evaluator-only and used only for the exposure metric.",
        "- No figure was generated; the protocol requires PaperBanana for visuals, and no visual is needed for this numeric screen.",
        "",
        "## Aggregate results",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Limits",
        "",
        "This screen does not establish null calibration, arbitrary delayed-feedback validity, validity under outcome-dependent delays, general serial dependence, adaptive candidate promotion, or novelty. Any selection requires a fresh independent null calibration and a disjoint harm confirmation. See [`delayed_markov_bound_development_protocol.md`](../../../docs/delayed_markov_bound_development_protocol.md) and [`delayed_event_prefix_validity.md`](../../../docs/delayed_event_prefix_validity.md).",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    sources = [
        Path(__file__),
        Path("scripts/validate_delayed_history_predictable_bounds.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("docs/delayed_markov_bound_development_protocol.md"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    manifest = {
        "experiment": "delayed_markov_predictable_bound_development",
        "status": "development_only_not_calibration_or_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "seed_root": seed,
        "streams_per_scenario_arm": streams,
        "horizon": horizon,
        "scenario_names": list(SCENARIOS),
        "delays": list(DELAYS),
        "bound_modes": ["fixed", "predictable"],
        "q_min": 0.05,
        "budget_rate": 0.20,
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "source_sha256": {str(path): sha256(path) for path in sources},
        "artifact_sha256": {
            str(path.relative_to(output)): sha256(path)
            for path in (metrics_path, summary_path, paired_path, report_path)
        },
        "limitations": [
            "development-only; no calibration or confirmatory claim",
            "two-state Markov volatility process with statewise zero-mean null",
            "fixed outcome-independent delays of 1 and 12 events",
            "frozen action pair and source proxy; no policy changes",
            "event-order prefix alarms; delay is not evidence",
        ],
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=60)
    parser.add_argument("--horizon", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED_ROOT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(
        run_development(
            streams=args.streams,
            horizon=args.horizon,
            seed=args.seed,
            device_name=args.device,
            output=args.output,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
