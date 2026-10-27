"""Exploratory residual-variance comparison for pooled and context-stratified monitors."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ..data.gpu.environment import environment
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate
from .eprocess import BoundedMeanEProcess, VectorizedStartedMixtureEProcess
from .estimators import prediction_powered_bound, prediction_powered_estimate
from .risk_proxy_monitor_grid import RiskProxyMonitorGridConfig, _prepare_stream
from .stratified_eprocess import ContextStratifiedEProcess

SEVERITIES = (1.5, 3.0, 4.5)
QUERY_RATES = (0.8, 1.0)
CONTEXTS = ("boundary", "non_boundary")
SEED_OFFSET = 31_305_000
ALPHA = 0.05
HARM_MARGIN = 0.10
MAX_LABEL_COST = 2.5
PROTOCOL = Path("docs/residual_variance_context_grid_protocol.md")


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 60,
    seed_offset: int = SEED_OFFSET,
    n: int = 2400,
    d: int = 16,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2 or n < 1600 or d < 2:
        raise ValueError("seeds must be >=2, n>=1600, and d>=2")
    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu, or cuda")
    if device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    resolved_device = "cuda" if device == "auto" and torch.cuda.is_available() else device
    if resolved_device == "auto":
        resolved_device = "cpu"
    config = RiskProxyMonitorGridConfig(
        n=n,
        d=d,
        null_seeds=2,
        alternative_seeds=seeds,
        seed_offset=seed_offset,
        alpha=ALPHA,
        harm_margin=HARM_MARGIN,
        max_label_cost=MAX_LABEL_COST,
        device=resolved_device,
    ).validate()
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")

    template = next(scenario for scenario in SCENARIOS if scenario.name == "residual_variance")
    rows: list[dict] = []
    for severity in SEVERITIES:
        scenario = replace(template, severity=severity)
        for seed in range(seed_offset, seed_offset + seeds):
            (
                _scenario,
                _seed,
                experiment_config,
                centered,
                expected,
                proxy,
                costs,
                monitor_start,
                train_end,
                onset,
                clip,
            ) = _prepare_stream(scenario, seed, config)
            # Reconstruct the learner-visible fixed context from the same
            # deterministic seed. This keeps the shared, historically hashed
            # monitor runner byte-for-byte unchanged.
            context_config = ExperimentConfig(
                n=config.n,
                d=config.d,
                evaluation_seeds=1,
                calibration_seeds=2,
                calibration_start=max(800, int(config.n * 0.25)),
                alpha=config.alpha,
                eprocess_epsilon=config.harm_margin,
                seed_offset=seed,
                device=config.device,
            )
            _, context_frame, _, _ = _generate(scenario, seed, context_config)
            x = np.stack(context_frame.features.to_numpy()).astype(float)
            monitor_start = max(800, int(config.n * 0.25))
            score = x[:, 0] - 0.9 * x[:, 1]
            contexts = np.where(np.abs(score[monitor_start:]) <= 0.3, "boundary", "non_boundary")
            available = n - monitor_start
            # Budget is rate-specific; construct a shared query path for each arm.
            for query_rate in QUERY_RATES:
                budget = query_rate * float(costs[train_end:monitor_start].mean()) * available
                uniforms = np.random.default_rng(seed + 910_2026).random(available)
                increments: list[float] = []
                used_contexts: list[str] = []
                labels = 0
                spend = 0.0
                remaining = budget
                for offset, event_index in enumerate(range(monitor_start, n)):
                    if remaining + 1e-12 < MAX_LABEL_COST:
                        break
                    queried = bool(uniforms[offset] < query_rate)
                    cost = float(costs[event_index])
                    if queried:
                        if cost > remaining + 1e-12:
                            raise RuntimeError("query cost exceeded its pre-event reserve")
                        labels += 1
                        spend += cost
                        remaining -= cost
                    increments.append(
                        prediction_powered_estimate(
                            float(proxy[offset]),
                            queried,
                            float(centered[event_index]) if queried else None,
                            query_rate,
                        )
                    )
                    used_contexts.append(str(contexts[offset]))

                bound = prediction_powered_bound(clip, query_rate)
                horizon = len(increments)
                starts = tuple(round(index * available / 8) for index in range(8))
                methods = {
                    "pooled_fixed_mixture": BoundedMeanEProcess(bound=bound, alpha=ALPHA),
                    "pooled_uniform_eight_start": VectorizedStartedMixtureEProcess(
                        bound=bound, alpha=ALPHA, starts=starts
                    ),
                    "context_stratified": ContextStratifiedEProcess(
                        contexts=CONTEXTS, bound=bound, alpha=ALPHA
                    ),
                }
                first_crossing = {name: None for name in methods}
                alarmed_groups: tuple[str, ...] = ()
                for time, (increment, context) in enumerate(
                    zip(increments, used_contexts, strict=True)
                ):
                    for name, method in methods.items():
                        if name == "context_stratified":
                            method.update(increment, context=context)
                            alarmed_groups = method.alarmed_contexts
                            alarm = method.alarm
                        else:
                            method.update(increment)
                            alarm = method.alarm
                        if first_crossing[name] is None and alarm:
                            first_crossing[name] = time

                expected_path = (
                    np.asarray(expected[monitor_start : monitor_start + horizon]) - HARM_MARGIN
                )
                context_array = np.asarray(used_contexts)
                for name, method in methods.items():
                    crossing = first_crossing[name]
                    detected = crossing is not None and onset is not None and crossing >= onset
                    pre_onset = crossing is not None and (onset is None or crossing < onset)
                    row = {
                        "scenario": scenario.name,
                        "severity": severity,
                        "seed": seed,
                        "query_rate": query_rate,
                        "method": name,
                        "detected": bool(detected),
                        "pre_onset_alarm": bool(pre_onset),
                        "first_crossing": crossing,
                        "harm_onset_relative": onset,
                        "events_processed": horizon,
                        "labels_queried": labels,
                        "hard_budget": budget,
                        "realized_label_spend": spend,
                        "budget_respected": spend <= budget + 1e-9,
                        "mean_paired_cost_margin_excess": float(expected_path.mean()),
                        "boundary_support": int(np.sum(context_array == "boundary")),
                        "non_boundary_support": int(np.sum(context_array == "non_boundary")),
                        "boundary_expected_margin_excess": float(
                            expected_path[context_array == "boundary"].mean()
                        ),
                        "non_boundary_expected_margin_excess": float(
                            expected_path[context_array == "non_boundary"].mean()
                        ),
                        "generator_device": experiment_config.device,
                    }
                    if name == "context_stratified":
                        row["alarmed_contexts"] = ",".join(alarmed_groups)
                        row["boundary_log_e"] = method.log_e_values["boundary"]
                        row["non_boundary_log_e"] = method.log_e_values["non_boundary"]
                    else:
                        row["alarmed_contexts"] = ""
                        row["boundary_log_e"] = np.nan
                        row["non_boundary_log_e"] = np.nan
                    rows.append(row)

    metrics = pd.DataFrame(rows)
    summary = (
        metrics.groupby(["severity", "query_rate", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            pre_onset_alarms=("pre_onset_alarm", "sum"),
            mean_events=("events_processed", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_boundary_cost_excess=("boundary_expected_margin_excess", "mean"),
            mean_non_boundary_cost_excess=("non_boundary_expected_margin_excess", "mean"),
            all_caps_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    output.mkdir(parents=True, exist_ok=True)
    metric_csv = output / "metrics.csv"
    metric_parquet = output / "metrics.parquet"
    summary_csv = output / "summary.csv"
    summary_parquet = output / "summary.parquet"
    metrics.to_csv(metric_csv, index=False)
    metrics.to_parquet(metric_parquet, index=False)
    summary.to_csv(summary_csv, index=False)
    summary.to_parquet(summary_parquet, index=False)
    source = Path(__file__)
    report = [
        "# Residual-variance context-stratified monitor development results",
        "",
        "This alternative-only development screen is descriptive. The context-stratified procedure tests the intersection of context-conditional mean nulls; it does not test population-average harm when contexts can offset one another. No false-alarm rate or novelty claim is established.",
        "",
        f"CUDA/requested device: `{resolved_device}`; seeds: `{seeds}`; rows: `{len(metrics)}`.",
        "",
        summary.to_markdown(index=False),
        "",
        "Any selected candidate requires fresh independent null calibration and disjoint positive-signal confirmation. The Bonferroni family is a composition of established bounded-mean e-processes, conditional on the registered context-specific null and predictable context membership.",
        "",
    ]
    report_path = output / "results.md"
    report_path.write_text("\n".join(report), encoding="utf-8")
    files = (metric_csv, metric_parquet, summary_csv, summary_parquet, report_path)
    manifest = {
        "experiment": "residual_variance_context_stratified_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "design": {
            "severities": list(SEVERITIES),
            "query_rates": list(QUERY_RATES),
            "seeds": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "d": d,
            "device": resolved_device,
            "contexts": list(CONTEXTS),
            "context_rule": "boundary iff abs(x1 - 0.9*x2) <= 0.3; features available before labels",
            "methods": ["pooled_fixed_mixture", "pooled_uniform_eight_start", "context_stratified"],
            "claim": "exploratory; stratified procedure tests intersection of subgroup conditional-mean nulls, not population-average harm",
        },
        "metric_rows": len(metrics),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "environment": environment(),
        "checksums": {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in files},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    checksum_lines = [f"{digest}  {name}" for name, digest in manifest["checksums"].items()]
    checksum_lines.append(f"{manifest['source_sha256']}  source_sha256:{source.name}")
    checksum_lines.append(f"{manifest['protocol_sha256']}  protocol_sha256:{PROTOCOL.as_posix()}")
    (output / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return metrics, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/residual_variance_context_grid_60")
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        d=args.d,
        device=args.device,
    )
    print(summary.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
