"""Matched hyperparameter development grid for predictable-variance e-processes."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import math
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch

from ..data.gpu.environment import environment
from ..data.provenance import sha256, write_json
from ..decision_harm_experiment import SCENARIOS
from .eprocess import BoundedMeanEProcess, VectorizedStartedMixtureEProcess
from .estimators import prediction_powered_bound
from .risk_proxy_monitor_grid import (
    RiskProxyMonitorGridConfig,
    _prepare_stream,
)

SEVERITIES = (1.5, 3.0, 4.5)
QUERY_RATES = (0.80, 1.00)
ALPHA = 0.05
HARM_MARGIN = 0.10
PVA_PRIOR_STRENGTHS = (1.0, 4.0, 16.0)
PVA_PRIOR_MEANS = (0.0, 0.05, 0.10)
PVA_PRIOR_SECOND_MOMENTS = (0.05, 0.25, 0.75)
PVA_MAX_STAKES = (0.25, 0.50, 0.80)
PROTOCOL = Path("docs/residual_variance_pva_grid_protocol.md")


@dataclass(frozen=True)
class GridConfig:
    seeds: int = 60
    seed_offset: int = 31_304_000
    n: int = 2_400
    d: int = 16
    device: str = "cuda"
    batch_streams: int = 60

    def validate(self) -> GridConfig:
        if self.seeds < 2 or self.n < 1_600 or self.d < 2:
            raise ValueError("seeds must be >=2, n>=1600, and d>=2")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        return self


@dataclass(frozen=True)
class PVAConfig:
    prior_strength: float
    prior_mean: float
    prior_second_moment: float
    max_stake: float

    @property
    def name(self) -> str:
        return (
            f"pva_s{self.prior_strength:g}_m{self.prior_mean:g}_"
            f"v{self.prior_second_moment:g}_cap{self.max_stake:g}"
        )


def pva_grid() -> tuple[PVAConfig, ...]:
    return tuple(
        PVAConfig(*values)
        for values in itertools.product(
            PVA_PRIOR_STRENGTHS,
            PVA_PRIOR_MEANS,
            PVA_PRIOR_SECOND_MOMENTS,
            PVA_MAX_STAKES,
        )
    )


def _vectorized_pva(
    increments: np.ndarray,
    bounds: np.ndarray,
    configs: tuple[PVAConfig, ...],
    *,
    alpha: float = ALPHA,
    device: torch.device,
) -> dict[str, np.ndarray]:
    """Run the existing predictable-Kelly recursion over configs and streams on one device."""
    values = np.asarray(increments, dtype=np.float64)
    support = np.asarray(bounds, dtype=np.float64)
    if values.ndim != 2 or support.shape != (values.shape[0],):
        raise ValueError("increments must be stream-by-time and bounds must match streams")
    if not configs or not np.isfinite(support).all() or np.any(support <= 0):
        raise ValueError("configs must be nonempty and bounds finite and positive")
    observed = np.isfinite(values)
    if np.any(np.abs(values[observed]) > np.broadcast_to(support[:, None], values.shape)[observed] + 1e-10):
        raise ValueError("an increment exceeds its stream support bound")

    x = torch.as_tensor(np.nan_to_num(values, nan=0.0), dtype=torch.float64, device=device)
    active = torch.as_tensor(observed, dtype=torch.bool, device=device)
    bound = torch.as_tensor(support, dtype=torch.float64, device=device)[None, :]
    strength = torch.as_tensor([c.prior_strength for c in configs], dtype=torch.float64, device=device)[:, None]
    prior_mean = torch.as_tensor([c.prior_mean for c in configs], dtype=torch.float64, device=device)[:, None]
    prior_second = torch.as_tensor([c.prior_second_moment for c in configs], dtype=torch.float64, device=device)[:, None]
    max_stake = torch.as_tensor([c.max_stake for c in configs], dtype=torch.float64, device=device)[:, None]

    n_configs, n_streams = len(configs), len(values)
    total = torch.zeros((n_configs, n_streams), dtype=torch.float64, device=device)
    square_total = torch.zeros_like(total)
    updates = torch.zeros(n_streams, dtype=torch.float64, device=device)
    log_wealth = torch.zeros_like(total)
    peak_log_wealth = torch.zeros_like(total)
    first_crossing = torch.full((n_configs, n_streams), -1, dtype=torch.int64, device=device)
    threshold = -math.log(alpha)
    for time in range(values.shape[1]):
        available = active[:, time]
        normalized = x[:, time][None, :] / bound
        denominator = strength + updates[None, :]
        mean = (strength * prior_mean + total) / denominator
        second_moment = (strength * prior_second + square_total) / denominator
        stake = torch.clamp(torch.clamp(mean, min=0.0) / second_moment, min=0.0)
        stake = torch.minimum(stake, max_stake)
        factor = 1.0 + stake * normalized
        if torch.any(factor[:, available] <= 0):
            raise RuntimeError("predictable PVA stake produced a nonpositive factor")
        log_wealth += torch.where(available[None, :], torch.log(factor), 0.0)
        peak_log_wealth = torch.maximum(peak_log_wealth, log_wealth)
        total += normalized * available[None, :]
        square_total += normalized.square() * available[None, :]
        updates += available
        crossed_now = (first_crossing < 0) & (log_wealth >= threshold) & available[None, :]
        first_crossing[crossed_now] = time

    return {
        "final_log_e": log_wealth.detach().cpu().numpy(),
        "peak_log_e": peak_log_wealth.detach().cpu().numpy(),
        "first_crossing": first_crossing.detach().cpu().numpy(),
        "updates": updates.detach().cpu().numpy().astype(np.int64),
    }


def _build_paired_query_path(
    *,
    centered: np.ndarray,
    proxy: np.ndarray,
    costs: np.ndarray,
    train_end: int,
    monitor_start: int,
    query_rate: float,
    seed: int,
    max_label_cost: float,
) -> tuple[np.ndarray, float, int, float]:
    available = len(centered) - monitor_start
    budget = query_rate * float(costs[train_end:monitor_start].mean()) * available
    uniforms = np.random.default_rng(seed + 910_2026).random(available)
    updates: list[float] = []
    labels = 0
    spend = 0.0
    remaining = budget
    for offset, event_index in enumerate(range(monitor_start, len(centered))):
        if remaining + 1e-12 < max_label_cost:
            break
        cost = float(costs[event_index])
        queried = bool(uniforms[offset] < query_rate)
        if queried:
            if cost > remaining + 1e-12:
                raise RuntimeError("query cost exceeded the pre-event reserve")
            labels += 1
            spend += cost
            remaining -= cost
            updates.append(float(proxy[offset] + (centered[event_index] - proxy[offset]) / query_rate))
        else:
            updates.append(float(proxy[offset]))
    return np.asarray(updates, dtype=np.float64), budget, labels, spend


def _baseline_rows(
    *,
    increments: np.ndarray,
    bounds: np.ndarray,
    scenario_name: str,
    severity: float,
    query_rate: float,
    seed_ids: list[int],
    onsets: list[int | None],
    labels: list[int],
    spends: list[float],
    budgets: list[float],
    expected_excess: list[float],
    horizon: int,
) -> list[dict[str, Any]]:
    methods: dict[str, Any] = {}
    output: list[dict[str, Any]] = []
    for stream in range(len(increments)):
        bound = float(bounds[stream])
        methods = {
            "fixed_stake_mixture": BoundedMeanEProcess(bound=bound, alpha=ALPHA),
            "uniform_eight_start_mixture": VectorizedStartedMixtureEProcess(
                bound=bound,
                alpha=ALPHA,
                starts=tuple(round(i * horizon / 8) for i in range(8)),
            ),
        }
        first: dict[str, int | None] = {name: None for name in methods}
        for time, value in enumerate(increments[stream]):
            if not np.isfinite(value):
                continue
            for name, process in methods.items():
                log_e = process.update(float(value))
                if first[name] is None and log_e >= -math.log(ALPHA):
                    first[name] = time
        for name, process in methods.items():
            alarm = first[name]
            onset = onsets[stream]
            output.append(
                {
                    "scenario": scenario_name,
                    "severity": severity,
                    "query_rate": query_rate,
                    "seed": seed_ids[stream],
                    "method": name,
                    "prior_strength": None,
                    "prior_mean": None,
                    "prior_second_moment": None,
                    "max_stake": None,
                    "detected": bool(alarm is not None and onset is not None and alarm >= onset),
                    "false_alarm": bool(alarm is not None and (onset is None or alarm < onset)),
                    "alarm_time": alarm,
                    "harm_onset_relative": onset,
                    "labels_queried": labels[stream],
                    "events_processed": int(np.isfinite(increments[stream]).sum()),
                    "budget": budgets[stream],
                    "realized_spend": spends[stream],
                    "expected_excess_cost_mean": expected_excess[stream],
                }
            )
    return output


def run_grid(config: GridConfig, output_dir: Path) -> Path:
    config.validate()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    device_name = config.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    base_scenario = next(s for s in SCENARIOS if s.name == "residual_variance")
    risk_config = RiskProxyMonitorGridConfig(
        n=config.n,
        d=config.d,
        null_seeds=2,
        alternative_seeds=config.seeds,
        seed_offset=config.seed_offset,
        alpha=ALPHA,
        harm_margin=HARM_MARGIN,
        max_label_cost=2.5,
        device=device_name,
    ).validate()
    configs = pva_grid()
    rows: list[dict[str, Any]] = []
    for severity in SEVERITIES:
        scenario = replace(base_scenario, severity=severity)
        prepared_paths = []
        for seed in range(config.seed_offset, config.seed_offset + config.seeds):
            prepared_paths.append((seed, _prepare_stream(scenario, seed, risk_config)))
        for query_rate in QUERY_RATES:
            increments: list[np.ndarray] = []
            bounds: list[float] = []
            seed_ids: list[int] = []
            onsets: list[int | None] = []
            label_counts: list[int] = []
            spends: list[float] = []
            budgets: list[float] = []
            expected_excess: list[float] = []
            maximum_horizon = config.n - prepared_paths[0][1][7]
            for seed, prepared in prepared_paths:
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
                    outcome_bound,
                ) = prepared
                stream, budget, labels, spend = _build_paired_query_path(
                    centered=centered,
                    proxy=proxy,
                    costs=costs,
                    train_end=train_end,
                    monitor_start=monitor_start,
                    query_rate=query_rate,
                    seed=seed,
                    max_label_cost=risk_config.max_label_cost,
                )
                if np.any(np.abs(stream) > prediction_powered_bound(outcome_bound, query_rate) + 1e-10):
                    raise RuntimeError("generated PPI increment exceeded its support bound")
                padded = np.full(maximum_horizon, np.nan, dtype=np.float64)
                padded[: len(stream)] = stream
                increments.append(padded)
                bounds.append(prediction_powered_bound(outcome_bound, query_rate))
                seed_ids.append(seed)
                onsets.append(onset)
                label_counts.append(labels)
                spends.append(spend)
                budgets.append(budget)
                expected_excess.append(float(np.mean(expected[monitor_start : monitor_start + len(stream)])))
                if experiment_config.device != device_name:
                    raise RuntimeError("synthetic generator resolved a different device than requested")

            increment_matrix = np.stack(increments)
            pva_result = _vectorized_pva(increment_matrix, np.asarray(bounds), configs, device=device)
            crossing = pva_result["first_crossing"]
            for config_index, pva_config in enumerate(configs):
                for stream_index in range(config.seeds):
                    alarm_index = int(crossing[config_index, stream_index])
                    alarm = None if alarm_index < 0 else alarm_index
                    onset = onsets[stream_index]
                    rows.append(
                        {
                            "scenario": scenario.name,
                            "severity": severity,
                            "query_rate": query_rate,
                            "seed": seed_ids[stream_index],
                            "method": pva_config.name,
                            **asdict(pva_config),
                            "detected": bool(alarm is not None and onset is not None and alarm >= onset),
                            "false_alarm": bool(alarm is not None and (onset is None or alarm < onset)),
                            "alarm_time": alarm,
                            "harm_onset_relative": onset,
                            "peak_log_e": float(pva_result["peak_log_e"][config_index, stream_index]),
                            "final_log_e": float(pva_result["final_log_e"][config_index, stream_index]),
                            "labels_queried": label_counts[stream_index],
                            "events_processed": int(pva_result["updates"][stream_index]),
                            "budget": budgets[stream_index],
                            "realized_spend": spends[stream_index],
                            "expected_excess_cost_mean": expected_excess[stream_index],
                        }
                    )
            rows.extend(
                _baseline_rows(
                    increments=increment_matrix,
                    bounds=np.asarray(bounds),
                    scenario_name=scenario.name,
                    severity=severity,
                    query_rate=query_rate,
                    seed_ids=seed_ids,
                    onsets=onsets,
                    labels=label_counts,
                    spends=spends,
                    budgets=budgets,
                    expected_excess=expected_excess,
                    horizon=maximum_horizon,
                )
            )

    metrics = pd.DataFrame(rows)
    expected_rows = config.seeds * len(SEVERITIES) * len(QUERY_RATES) * (len(configs) + 2)
    if len(metrics) != expected_rows or metrics.duplicated(
        ["scenario", "severity", "query_rate", "seed", "method"]
    ).any():
        raise RuntimeError("grid row-key or count invariant failed")
    if not metrics.budget.gt(0).all() or not metrics.realized_spend.le(metrics.budget + 1e-9).all():
        raise RuntimeError("grid budget invariant failed")
    if metrics.groupby(["scenario", "severity", "query_rate", "seed"]).events_processed.nunique().max() != 1:
        raise RuntimeError("matched methods did not share a processing horizon")

    grouped = (
        metrics.groupby(["severity", "query_rate", "method"], as_index=False)
        .agg(
            seeds=("seed", "count"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            false_alarms=("false_alarm", "sum"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("events_processed", "mean"),
            mean_peak_log_e=("peak_log_e", "mean"),
        )
    )
    summary = (
        grouped.groupby("method", as_index=False)
        .agg(
            macro_detection_rate=("detection_rate", "mean"),
            worst_cell_detection_rate=("detection_rate", "min"),
            total_false_alarms=("false_alarms", "sum"),
            mean_labels=("mean_labels", "mean"),
            mean_events=("mean_events", "mean"),
            macro_mean_peak_log_e=("mean_peak_log_e", "mean"),
        )
        .sort_values(["macro_detection_rate", "worst_cell_detection_rate"], ascending=False)
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(metrics, preserve_index=False), output_dir / "stream_metrics.parquet")
    pq.write_table(pa.Table.from_pandas(grouped, preserve_index=False), output_dir / "cell_summary.parquet")
    pq.write_table(pa.Table.from_pandas(summary, preserve_index=False), output_dir / "method_summary.parquet")
    metrics.to_csv(output_dir / "stream_metrics.csv", index=False)
    grouped.to_csv(output_dir / "cell_summary.csv", index=False)
    summary.to_csv(output_dir / "method_summary.csv", index=False)
    manifest = {
        "experiment": "residual-variance PVA prior and stake-cap development grid",
        "config": asdict(config),
        "risk_proxy_config": asdict(risk_config),
        "severities": list(SEVERITIES),
        "query_rates": list(QUERY_RATES),
        "pva_configurations": [asdict(item) for item in configs],
        "pva_grid_cardinality": len(configs),
        "baseline_methods": ["fixed_stake_mixture", "uniform_eight_start_mixture"],
        "rows": len(metrics),
        "expected_rows": expected_rows,
        "device": device_name,
        "environment": environment(),
        "seed_ids": list(range(config.seed_offset, config.seed_offset + config.seeds)),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "source_sha256": sha256(Path(__file__)),
        "eprocess_source_sha256": sha256(Path(__file__).with_name("eprocess.py")),
        "generator_source_sha256": sha256(Path(__file__).parent.parent / "data" / "synthetic" / "generators.py"),
        "created_utc": datetime.now(UTC).isoformat(),
        "interpretation": "alternative-only hyperparameter development screen after a broad grid search; no null calibration, confirmation, inferential winner, or novelty claim",
    }
    write_json(output_dir / "manifest.json", manifest)
    report = [
        "# Residual-variance predictable-Kelly hyperparameter screen",
        "",
        f"The CUDA run crossed {len(configs)} predictable-variance prior/stake settings with {len(SEVERITIES)} severities, {len(QUERY_RATES)} query rates, and {config.seeds} matched seed streams per cell ({len(metrics):,} method-stream rows).",
        "",
        "## Macro development ranking",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Cell results",
        "",
        grouped.to_markdown(index=False, floatfmt=".4f"),
        "",
        "All settings use the same predictable Kelly update, with prior strength, prior mean, prior second moment, and stake cap fixed before each stream. Every method shares the same generated stream, Bernoulli query path, PPI increments, horizon, and budget. The candidate parameters remain fixed during monitoring; therefore each candidate preserves the standard predictable bounded-betting validity argument under the same support and conditional-mean assumptions.",
        "",
        "This grid searches 81 configurations on alternatives only. The top-ranked configuration is a development candidate, not a selected winner: cellwise multiple search makes its apparent advantage optimistic. Fresh null calibration and disjoint harm confirmation are required before promotion. Alternative-only zero false alarms are not null calibration. No new validity theorem or novelty claim follows.",
        "",
        f"Protocol: `{PROTOCOL.as_posix()}`. Parquet outputs and the source/environment manifest are in `{output_dir.as_posix()}/`.",
        "",
    ]
    (output_dir / "results.md").write_text("\n".join(report), encoding="utf-8")
    checksums = [
        f"{hashlib.sha256(item.read_bytes()).hexdigest()}  {item.name}"
        for item in sorted(output_dir.iterdir())
        if item.name != "checksums.sha256"
    ]
    (output_dir / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"output_dir={output_dir}")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=31_304_000)
    parser.add_argument("--n", type=int, default=2_400)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/residual_variance_pva_hyperparameter_grid"))
    args = parser.parse_args()
    config = GridConfig(seeds=args.seeds, seed_offset=args.seed_offset, n=args.n, d=args.d, device=args.device)
    run_grid(config, args.output_dir)


if __name__ == "__main__":
    main()
