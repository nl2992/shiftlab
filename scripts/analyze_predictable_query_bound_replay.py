"""Replay history-predictable PPI bounds on an existing hard-budget trace set."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.estimators import prediction_powered_bound
from shiftlab.dive.predictable_bound_replay import first_crossing, replay_mixture_log_e

STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
TRACE_RELATIVE_PATH = Path("metrics/event_traces.parquet")
DEFAULT_INPUT = Path("outputs/monitor_signal_diagnostic_20_60_v2")
DEFAULT_OUTPUT = Path("outputs/predictable_query_bound_replay_60")
REQUIRED_COLUMNS = {
    "seed",
    "scenario",
    "method",
    "event_offset",
    "stream_index",
    "propensity",
    "ppi_increment",
    "learner_log_e",
    "evaluator_harm_onset_event",
}


def classify_alarm(
    alarm: int | None, *, onset_offset: int | None, harm_scenario: bool
) -> tuple[bool, bool]:
    """Return (pre-onset escalation, post-onset detection)."""
    if alarm is None:
        return False, False
    if not harm_scenario or onset_offset is None:
        return True, False
    return alarm < onset_offset, alarm >= onset_offset


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replay(input_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    manifest_path = input_dir / "reports" / "manifest.json"
    trace_path = input_dir / TRACE_RELATIVE_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    trace_hash = sha256(trace_path)
    recorded_hash = (
        manifest.get("sha256", {}).get("artifacts", {}).get(TRACE_RELATIVE_PATH.as_posix())
    )
    # Manifests created on Windows serialize relative paths with backslashes.
    if recorded_hash is None:
        recorded_hash = (
            manifest.get("sha256", {})
            .get("artifacts", {})
            .get(str(TRACE_RELATIVE_PATH).replace("/", "\\"))
        )
    if recorded_hash != trace_hash:
        raise ValueError("event trace SHA-256 does not match its source manifest")

    config = manifest["configuration"]
    alpha = float(config["alpha"])
    q_min = float(config["q_min"])
    if not config.get("common_eprocess_bound"):
        raise ValueError("source run must use its registered common e-process bound")
    traces = pd.read_parquet(trace_path)
    missing = REQUIRED_COLUMNS.difference(traces.columns)
    if missing:
        raise ValueError(f"trace is missing columns: {sorted(missing)}")

    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    rows: list[dict[str, object]] = []
    max_fixed_replay_error = 0.0
    min_bound_ratio = float("inf")
    for (scenario_name, method, seed), group in traces.groupby(
        ["scenario", "method", "seed"], sort=True
    ):
        if scenario_name not in scenarios:
            raise ValueError(f"unknown source scenario: {scenario_name}")
        group = group.sort_values("event_offset", kind="stable")
        offsets = group["event_offset"].to_numpy(dtype=int)
        if not np.array_equal(offsets, np.arange(len(group))):
            raise ValueError(f"noncontiguous event offsets in {scenario_name}/{method}/{seed}")
        q = group["propensity"].to_numpy(dtype=float)
        values = group["ppi_increment"].to_numpy(dtype=float)
        logged = group["learner_log_e"].to_numpy(dtype=float)
        if np.any((q < q_min - 1e-12) | (q > float(config["q_max"]) + 1e-12)):
            raise ValueError(
                f"query propensity outside registered range in {scenario_name}/{method}/{seed}"
            )

        scenario = scenarios[str(scenario_name)]
        margin = float(group["evaluator_harm_margin"].iloc[0])
        outcome_bound = max(scenario.fn_cost, scenario.fp_cost) + margin
        fixed_bound = prediction_powered_bound(outcome_bound, q_min)
        fixed_log_e = replay_mixture_log_e(values, fixed_bound, alpha=alpha, stakes=STAKES)
        replay_error = float(np.max(np.abs(fixed_log_e - logged)))
        max_fixed_replay_error = max(max_fixed_replay_error, replay_error)
        if replay_error > 1e-9:
            raise ValueError(
                f"fixed-bound replay did not reproduce learner logs in {scenario_name}/{method}/{seed}: {replay_error}"
            )

        dynamic_bounds = outcome_bound * (2 / q - 1)
        if np.any(np.abs(values) > dynamic_bounds + 1e-9):
            raise ValueError(
                f"increment exceeds its eventwise propensity bound in {scenario_name}/{method}/{seed}"
            )
        min_bound_ratio = min(min_bound_ratio, float(np.min(dynamic_bounds / fixed_bound)))
        dynamic_log_e = replay_mixture_log_e(values, dynamic_bounds, alpha=alpha, stakes=STAKES)
        fixed_alarm = first_crossing(fixed_log_e, alpha=alpha)
        dynamic_alarm = first_crossing(dynamic_log_e, alpha=alpha)
        onset_global = group["evaluator_harm_onset_event"].iloc[0]
        onset_offset = (
            int(onset_global - int(group["stream_index"].iloc[0]))
            if pd.notna(onset_global)
            else None
        )
        harm_scenario = scenario_name in {
            "boundary_local_harm",
            "recurring_regimes",
            "harmful_adaptation",
        }
        onset_reached = bool(
            harm_scenario and onset_offset is not None and onset_offset < len(group)
        )

        fixed_early, fixed_detected = classify_alarm(
            fixed_alarm, onset_offset=onset_offset, harm_scenario=harm_scenario
        )
        dynamic_early, dynamic_detected = classify_alarm(
            dynamic_alarm, onset_offset=onset_offset, harm_scenario=harm_scenario
        )
        rows.append(
            {
                "scenario": scenario_name,
                "method": method,
                "seed": int(seed),
                "events_processed": len(group),
                "mean_propensity": float(q.mean()),
                "max_propensity": float(q.max()),
                "outcome_bound": outcome_bound,
                "fixed_bound": fixed_bound,
                "mean_dynamic_bound": float(dynamic_bounds.mean()),
                "onset_offset": onset_offset,
                "onset_reached": onset_reached,
                "fixed_first_crossing": fixed_alarm,
                "dynamic_first_crossing": dynamic_alarm,
                "fixed_early_escalation": fixed_early,
                "dynamic_early_escalation": dynamic_early,
                "fixed_post_onset_detection": fixed_detected,
                "dynamic_post_onset_detection": dynamic_detected,
                "fixed_detection_delay": (
                    fixed_alarm - onset_offset
                    if fixed_detected and onset_offset is not None
                    else None
                ),
                "dynamic_detection_delay": (
                    dynamic_alarm - onset_offset
                    if dynamic_detected and onset_offset is not None
                    else None
                ),
                "fixed_replay_max_abs_log_error": replay_error,
            }
        )
    return pd.DataFrame(rows), {
        "source_manifest": str(manifest_path),
        "source_trace": str(trace_path),
        "source_trace_sha256": trace_hash,
        "source_run": manifest.get("experiment"),
        "configuration": config,
        "alpha": alpha,
        "stakes": STAKES,
        "max_fixed_replay_log_error": max_fixed_replay_error,
        "min_dynamic_to_fixed_bound_ratio": min_bound_ratio,
        "streams": len(rows),
    }


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (scenario, method), group in metrics.groupby(["scenario", "method"], sort=True):
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "onsets_reached": int(group["onset_reached"].sum()),
                "fixed_any_crossings": int(group["fixed_first_crossing"].notna().sum()),
                "dynamic_any_crossings": int(group["dynamic_first_crossing"].notna().sum()),
                "fixed_early_escalations": int(group["fixed_early_escalation"].sum()),
                "dynamic_early_escalations": int(group["dynamic_early_escalation"].sum()),
                "fixed_post_onset_detections": int(group["fixed_post_onset_detection"].sum()),
                "dynamic_post_onset_detections": int(group["dynamic_post_onset_detection"].sum()),
                "fixed_detection_delay_mean": group["fixed_detection_delay"].mean(),
                "dynamic_detection_delay_mean": group["dynamic_detection_delay"].mean(),
                "mean_events_processed": float(group["events_processed"].mean()),
                "mean_propensity": float(group["mean_propensity"].mean()),
                "mean_dynamic_bound": float(group["mean_dynamic_bound"].mean()),
            }
        )
    return pd.DataFrame(rows)


def report_text(metrics: pd.DataFrame, summary: pd.DataFrame, provenance: dict[str, object]) -> str:
    boundary = metrics[metrics["scenario"] == "boundary_local_harm"]
    details = []
    for method, group in boundary.groupby("method", sort=True):
        fixed = int(group["fixed_post_onset_detection"].sum())
        dynamic = int(group["dynamic_post_onset_detection"].sum())
        reached = int(group["onset_reached"].sum())
        early_f = int(group["fixed_early_escalation"].sum())
        early_d = int(group["dynamic_early_escalation"].sum())
        fixed_delays = group["fixed_detection_delay"].dropna()
        dynamic_delays = group["dynamic_detection_delay"].dropna()
        details.append(
            f"- `{method}`: {reached} onsets reached; post-onset detections {fixed}/{len(group)} fixed versus {dynamic}/{len(group)} predictable-bound; pre-onset crossings {early_f} versus {early_d}; mean delay among detected streams {fixed_delays.mean():.1f} versus {dynamic_delays.mean():.1f} events."
        )
    return f"""# History-predictable propensity-bound replay

## Scope and method

This is a post hoc replay of the existing 60-seed hard-budget run at `{provenance["source_trace"]}`. It changes no query, label, proxy, stopping, or synthetic stream path. The first process uses the run's registered fixed common support bound; the second uses `B_t = M(2/q_t - 1)` on each event, where `q_t` comes only from the prior fixed-bound e-value and remaining budget in the `evidence_curve_a0.05_p0.5` policy. The policy does not use current covariates or current outcomes. Since `q_t` is measurable from prior history, this eventwise scale is predictable under the registered past-conditional marginal null. It is standard predictable-bound betting, not a new e-process or a novelty claim.

The fixed replay reproduces every stored learner log-e value to maximum absolute error `{provenance["max_fixed_replay_log_error"]:.3g}`. The smallest eventwise bound was `{provenance["min_dynamic_to_fixed_bound_ratio"]:.3f}` times the common fixed bound. All event increments were inside their eventwise bounds. The input Parquet checksum matched the source manifest.

## Exploratory results

On boundary-local harm, the observed post-onset detection counts and delays were:

{chr(10).join(details)}

All onsets were reached in this scenario. Across stationary and benign-nuisance controls, crossings were:

{summary[summary.scenario.isin(["stationary", "benign_nuisance"])][["scenario", "method", "streams", "fixed_any_crossings", "dynamic_any_crossings"]].to_markdown(index=False)}

The predictable-bound replay markedly increases crossings for both querying policies on this harmful path. The evidence-directed policy remains slightly below uniform in detections here, so the result does not show an acquisition advantage. The dynamic bound can change its scale when the learned query policy changes; a monitor that crosses can in turn influence future propensities. This replay follows the original fixed-monitor acquisition path and therefore measures monitor-only sensitivity.

### Stream-level summary

{summary.to_markdown(index=False, floatfmt=".3f")}

These reused streams do not independently establish 5% calibration, power, or superiority. The zero crossings in 120 null-control streams are a diagnostic only. A valid next step is a frozen, fresh-seed comparison that evaluates fixed and history-predictable bounds under nondegenerate marginal-null controls and disjoint harms, with the propensity rule defined entirely from past monitor state and spend. The eventwise scaling result from current-context-dependent propensities remains invalid for the marginal null.

No figure was generated for this tabular replay. Any research visual added later must be generated with PaperBanana.

## Reproduction

```powershell
uv run python scripts/analyze_predictable_query_bound_replay.py --input outputs/monitor_signal_diagnostic_20_60_v2 --output outputs/predictable_query_bound_replay_60
```

The output contains per-stream Parquet metrics, a seed-aggregated CSV, this report, and a checksum manifest.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    metrics, provenance = replay(args.input)
    summary = summarize(metrics)
    metrics_path = args.output / "metrics.parquet"
    summary_path = args.output / "summary.csv"
    report_path = args.output / "predictable_query_bound_replay.md"
    metrics.to_parquet(metrics_path, index=False)
    summary.to_csv(summary_path, index=False)
    report_path.write_text(report_text(metrics, summary, provenance), encoding="utf-8")
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = None
    output_files = (metrics_path, summary_path, report_path)
    manifest = {
        "experiment": "history_predictable_query_bound_trace_replay",
        "status": "exploratory_post_hoc_replay",
        "source": provenance,
        "code_commit": git_commit,
        "visuals_generated": False,
        "artifact_sha256": {path.name: sha256(path) for path in output_files},
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Wrote {len(metrics)} stream metrics to {args.output}")
    print(f"Maximum fixed replay log-e error: {provenance['max_fixed_replay_log_error']:.3g}")


if __name__ == "__main__":
    main()
