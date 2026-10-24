"""Run the paired propensity-floor and monitor-bound development grid."""

from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.dive.eprocess import BoundedMeanEProcess, PredictableBoundMeanEProcess
from shiftlab.dive.estimators import prediction_powered_bound
from shiftlab.dive.hard_budget import HardBudgetConfig, _generate_hard_budget_replicate

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/propensity_floor_bound_development_60"
PROTOCOL = Path("docs/propensity_floor_bound_development_protocol.md")
FLOORS = (0.10, 0.11)
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIO_NAMES = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "recurring_regimes",
    "harmful_adaptation",
)
SEEDS = 60
SEED_OFFSET = 56_000_000
COMMON_BOUND_Q = 0.10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _alarm_outcomes(alarm_time: int | None, harm_onset: int | None) -> tuple[bool, bool]:
    detected = alarm_time is not None and harm_onset is not None and alarm_time >= harm_onset
    false_escalation = alarm_time is not None and (harm_onset is None or alarm_time < harm_onset)
    return bool(detected), bool(false_escalation)


def _analyze_trace(metric: dict, trace: list[dict], config: HardBudgetConfig) -> dict:
    trace.sort(key=lambda event: int(event["event_offset"]))
    expected_events = int(metric["processed_events"])
    if len(trace) != expected_events or [int(row["event_offset"]) for row in trace] != list(
        range(expected_events)
    ):
        raise ValueError("event trace is incomplete or not contiguous")
    propensities = np.asarray([float(row["propensity"]) for row in trace])
    increments = np.asarray([float(row["ppi_increment"]) for row in trace])
    if not np.isfinite(propensities).all() or not np.isfinite(increments).all():
        raise ValueError("event trace contains non-finite learner-side values")
    if np.any((propensities < config.q_min - 1e-12) | (propensities > config.q_max + 1e-12)):
        raise ValueError("event trace violates the registered propensity range")

    harm_onset_value = metric["harm_onset_relative"]
    harm_onset = (
        None if harm_onset_value is None or pd.isna(harm_onset_value) else int(harm_onset_value)
    )
    fixed_alarm_value = metric["single_e_alarm_time"]
    fixed_alarm = (
        None if fixed_alarm_value is None or pd.isna(fixed_alarm_value) else int(fixed_alarm_value)
    )
    fixed_bound = float(metric["eprocess_support_bound"])
    outcome_bound = max(5.0, 1.0) + config.harm_margin
    common_bound = prediction_powered_bound(outcome_bound, COMMON_BOUND_Q)

    fixed_process = BoundedMeanEProcess(bound=fixed_bound, alpha=config.alpha)
    common_process = BoundedMeanEProcess(bound=common_bound, alpha=config.alpha)
    eventwise_process = PredictableBoundMeanEProcess(alpha=config.alpha)
    threshold = -np.log(config.alpha)
    first_fixed = None
    first_common = None
    first_eventwise = None
    eventwise_bounds = np.empty(len(trace), dtype=float)
    for i, (value, propensity) in enumerate(zip(increments, propensities, strict=True)):
        fixed_log_e = fixed_process.update(float(value))
        common_log_e = common_process.update(float(value))
        event_bound = prediction_powered_bound(outcome_bound, float(propensity))
        eventwise_bounds[i] = event_bound
        eventwise_log_e = eventwise_process.update(float(value), bound=event_bound)
        if first_fixed is None and fixed_log_e >= threshold:
            first_fixed = i
        if first_common is None and common_log_e >= threshold:
            first_common = i
        if first_eventwise is None and eventwise_log_e >= threshold:
            first_eventwise = i

    if first_fixed != fixed_alarm:
        raise ValueError("recomputed fixed-bound alarm does not match the registered monitor")
    fixed_detected, fixed_false = _alarm_outcomes(first_fixed, harm_onset)
    common_detected, common_false = _alarm_outcomes(first_common, harm_onset)
    eventwise_detected, eventwise_false = _alarm_outcomes(first_eventwise, harm_onset)
    return {
        "harm_onset_relative": harm_onset,
        "registered_bound_alarm_time": first_fixed,
        "registered_bound_detected": fixed_detected,
        "registered_bound_false_escalation": fixed_false,
        "common_q010_alarm_time": first_common,
        "common_q010_detected": common_detected,
        "common_q010_false_escalation": common_false,
        "eventwise_qt_alarm_time": first_eventwise,
        "eventwise_qt_detected_diagnostic": eventwise_detected,
        "eventwise_qt_false_escalation_diagnostic": eventwise_false,
        "eventwise_bound_mean": float(eventwise_bounds.mean()),
        "eventwise_bound_median": float(np.median(eventwise_bounds)),
        "eventwise_bound_p95": float(np.quantile(eventwise_bounds, 0.95)),
        "eventwise_bound_max": float(eventwise_bounds.max()),
    }


def _run_replicate(task: tuple[str, int, HardBudgetConfig, float]) -> list[dict]:
    scenario_name, replicate, config, floor = task
    _, metric_rows, traces = _generate_hard_budget_replicate((scenario_name, replicate, config))
    by_method: dict[str, list[dict]] = {}
    for trace_row in traces:
        by_method.setdefault(str(trace_row["method"]), []).append(trace_row)
    if set(by_method) != set(METHODS) or {str(row["method"]) for row in metric_rows} != set(
        METHODS
    ):
        raise ValueError("replicate did not return the frozen policy set")
    trace_by_method = {
        method: _analyze_trace(
            next(row for row in metric_rows if row["method"] == method),
            by_method[method],
            config,
        )
        for method in METHODS
    }
    results = []
    for metric in metric_rows:
        method = str(metric["method"])
        summary = trace_by_method[method]
        row = {
            "scenario": metric["scenario"],
            "seed": int(metric["seed"]),
            "method": method,
            "q_min": floor,
            "population_null_control": bool(metric["population_null_control"]),
            "material_harm": bool(metric["material_harm"]),
            "harm_reached_before_budget_stop": bool(metric["harm_reached_before_budget_stop"]),
            "harm_onset_relative": summary["harm_onset_relative"],
            "registered_minimum_propensity": float(metric["eprocess_minimum_propensity"]),
            "registered_support_bound": float(metric["eprocess_support_bound"]),
            "query_propensity_min": float(metric["query_propensity_min"]),
            "query_propensity_mean": float(metric["query_propensity_mean"]),
            "query_propensity_max": float(metric["query_propensity_max"]),
            "labels_queried": int(metric["labels_queried"]),
            "realized_label_spend": float(metric["realized_label_spend"]),
            "hard_budget": float(metric["hard_budget"]),
            "processed_events": int(metric["processed_events"]),
            "budget_respected": bool(metric["budget_respected"]),
            "stream_mean_estimation_rmse": float(metric["stream_mean_estimation_rmse"]),
            **summary,
        }
        results.append(row)
    return results


def _config(floor: float) -> HardBudgetConfig:
    device = resolve_device("cuda", n=3200, d=16, chunk_size=2048)
    if device != "cuda":
        raise RuntimeError("the locked development protocol requires CUDA generation")
    return HardBudgetConfig(
        n=3200,
        d=16,
        seeds=SEEDS,
        seed_offset=SEED_OFFSET,
        alpha=0.05,
        harm_margin=0.10,
        budget_rate=0.20,
        q_min=floor,
        q_max=0.80,
        monitor_comparators=(),
        max_label_cost=2.5,
        common_eprocess_bound=False,
        generate_figure=False,
        record_event_traces=True,
        device=device,
        workers=2,
        scenario_subset=SCENARIO_NAMES,
        method_subset=METHODS,
    ).validate()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite development output: {OUTPUT}")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    tasks = []
    configs = {}
    for floor in FLOORS:
        config = _config(floor)
        configs[f"{floor:.2f}"] = asdict(config)
        for scenario in SCENARIO_NAMES:
            tasks.extend((scenario, replicate, config, floor) for replicate in range(SEEDS))

    rows: list[dict] = []
    completed = 0
    with ProcessPoolExecutor(max_workers=2, mp_context=get_context("spawn")) as executor:
        for result_rows in executor.map(_run_replicate, tasks, chunksize=1):
            rows.extend(result_rows)
            completed += 1
            if completed % 10 == 0 or completed == len(tasks):
                print(
                    f"propensity-floor development replicates={completed}/{len(tasks)}", flush=True
                )

    metrics = pd.DataFrame(rows).sort_values(["q_min", "scenario", "seed", "method"], kind="stable")
    expected_rows = len(FLOORS) * len(SCENARIO_NAMES) * SEEDS * len(METHODS)
    if (
        len(metrics) != expected_rows
        or metrics.duplicated(["q_min", "scenario", "seed", "method"]).any()
    ):
        raise RuntimeError("generated metrics do not match the complete frozen grid")
    if not metrics.budget_respected.all():
        raise RuntimeError("a development stream violated its hard dollar budget")
    if metrics.groupby(["q_min", "scenario"]).material_harm.nunique().gt(1).any():
        raise RuntimeError("harm eligibility differs across methods within a paired cell")

    metrics_dir, reports_dir = OUTPUT / "metrics", OUTPUT / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=False)
    reports_dir.mkdir(parents=True, exist_ok=False)
    metrics_path = metrics_dir / "propensity_floor_bound_grid.parquet"
    metrics.to_parquet(metrics_path, index=False)
    report_path = reports_dir / "manifest.json"
    source_paths = sorted(path for path in (ROOT / "src/shiftlab").rglob("*.py") if path.is_file())
    source_paths.extend(
        ROOT / relative
        for relative in (
            "scripts/run_propensity_floor_bound_development.py",
            PROTOCOL.as_posix(),
        )
    )
    manifest = {
        "experiment": "paired_propensity_floor_and_monitor_bound_development",
        "configuration_by_q_min": configs,
        "seed_block": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "grid_rows": expected_rows,
        "requested_device": "cuda",
        "resolved_device": "cuda",
        "environment": environment(),
        "assumptions": [
            "Registered fixed support bounds use only guaranteed propensity floors and remain valid for the population conditional-on-past null under stated PPI assumptions.",
            "The common q_min=0.10 bound is applied to the same learner-side increments without changing acquisition.",
            "Eventwise q_t bounds require a stronger conditional-mean null given current context and propensity-selection information; eventwise results are diagnostic only.",
            "The two q_min configurations change query policies; same seeds and query uniforms provide pairing but do not isolate monitoring alone.",
            "Immediate paired labels, synthetic iid stream generation, predictable acquisition, and no adaptive post-selection beyond this development grid.",
        ],
        "run_provenance": {
            "protocol": PROTOCOL.as_posix(),
            "protocol_sha256": sha256(ROOT / PROTOCOL),
            "runner_sha256": sha256(Path(__file__).resolve()),
            "source_git_commit_at_run": source_commit,
            "figures_generated": False,
        },
        "sha256": {
            "artifacts": {"metrics/propensity_floor_bound_grid.parquet": sha256(metrics_path)},
            "source_files": {
                path.relative_to(ROOT).as_posix(): sha256(path)
                for path in source_paths
                if path.is_file()
            },
        },
    }
    report_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # The workspace path may contain characters outside a Windows console's
    # active code page. Emit an escaped ASCII path so a completed run exits cleanly.
    print(str(OUTPUT).encode("ascii", errors="backslashreplace").decode("ascii"))


if __name__ == "__main__":
    main()
