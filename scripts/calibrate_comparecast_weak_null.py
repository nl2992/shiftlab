"""Calibrate the official Comparecast e-process under registered weak-null controls."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
import types
import warnings
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from shiftlab.data.gpu.environment import environment
from shiftlab.decision_harm_experiment import POPULATION_NULL_CONTROLS, SCENARIOS
from shiftlab.dive.risk_proxy_monitor_grid import RiskProxyMonitorGridConfig, _prepare_stream

PROTOCOL = Path("papers/shiftguard_unified/comparecast_weak_null_calibration_protocol.md")
EXPECTED_COMMIT = "52748c86e0429a9612dc79892c3be6156a524132"
SCENARIO_NAMES = ("stationary", "benign_nuisance")
ALPHA = 0.05
HARM_MARGIN = 0.10
FAMILY_ALPHA = 0.05


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cp_upper(successes: int, trials: int, alpha: float) -> float:
    if successes == trials:
        return 1.0
    return float(beta.ppf(1 - alpha, successes + 1, trials - successes))


def _load_module(source: Path):
    package_dir = source / "comparecast"
    package = types.ModuleType("comparecast")
    package.__path__ = [str(package_dir)]
    sys.modules["comparecast"] = package
    confseq = types.ModuleType("confseq")
    boundaries = types.ModuleType("confseq.boundaries")

    def unused_boundary(*_args, **_kwargs):
        raise RuntimeError("unused confidence-sequence path called")

    boundaries.normal_log_mixture = unused_boundary  # type: ignore[attr-defined]
    confseq.boundaries = boundaries  # type: ignore[attr-defined]
    sys.modules["confseq"] = confseq
    sys.modules["confseq.boundaries"] = boundaries
    return importlib.import_module("comparecast.eprocess")


def run(
    *,
    source_dir: Path,
    output_dir: Path,
    seeds: int = 2000,
    seed_offset: int = 60_000_000,
    n: int = 2400,
    d: int = 16,
    device: str = "cuda",
) -> dict:
    if seeds < 2 or n < 1000 or d < 2:
        raise ValueError("seeds must be >=2, n>=1000, and d>=2")
    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu, or cuda")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    commit = subprocess.check_output(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"expected pinned Comparecast commit {EXPECTED_COMMIT}, got {commit}")
    module = _load_module(source_dir)
    comparecast_eprocess = module.eprocess_expm

    resolved_device = device
    if resolved_device == "auto":
        import torch

        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
    config = RiskProxyMonitorGridConfig(
        n=n,
        d=d,
        null_seeds=seeds,
        alternative_seeds=2,
        seed_offset=seed_offset,
        alpha=ALPHA,
        harm_margin=HARM_MARGIN,
        device=resolved_device,
    ).validate()
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    rows: list[dict] = []
    warning_messages: set[str] = set()
    warning_count = 0
    expected_paths: dict[str, list[np.ndarray]] = {name: [] for name in SCENARIO_NAMES}
    for scenario_name in SCENARIO_NAMES:
        if scenario_name not in POPULATION_NULL_CONTROLS:
            raise ValueError(
                f"scenario {scenario_name} is not a registered population-null control"
            )
        scenario = scenarios[scenario_name]
        for seed in range(seed_offset, seed_offset + seeds):
            prepared = _prepare_stream(scenario, seed, config)
            centered = np.asarray(prepared[3], dtype=np.float64)
            expected = np.asarray(prepared[4], dtype=np.float64)
            monitor_start = int(prepared[7])
            bound = float(prepared[10])
            increments = centered[monitor_start:]
            expected_excess = expected[monitor_start:] - HARM_MARGIN
            if len(increments) != n - monitor_start:
                raise RuntimeError("stream horizon disagrees with the registered monitoring start")
            if not np.isfinite(increments).all() or np.any(np.abs(increments) > bound + 1e-12):
                raise ValueError(
                    f"paired-cost increment violated support for {scenario_name}/{seed}"
                )
            if not np.isfinite(expected_excess).all():
                raise ValueError(f"non-finite evaluator truth for {scenario_name}/{seed}")
            expected_paths[scenario_name].append(expected_excess)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                e_values = comparecast_eprocess(
                    increments,
                    alpha_opt=ALPHA,
                    c=2 * bound,
                    compute_p=False,
                )
            warning_messages.update(str(item.message) for item in caught)
            warning_count += len(caught)
            if e_values.shape != increments.shape or not np.isfinite(e_values).all():
                raise ValueError(f"invalid upstream e-values for {scenario_name}/{seed}")
            crossing = np.flatnonzero(e_values >= 1 / ALPHA)
            rows.append(
                {
                    "scenario": scenario_name,
                    "seed": seed,
                    "events": len(increments),
                    "false_escalation": bool(len(crossing)),
                    "first_crossing": int(crossing[0]) if len(crossing) else None,
                    "max_e_value": float(np.max(e_values)),
                    "final_e_value": float(e_values[-1]),
                    "mean_observed_excess": float(np.mean(increments)),
                    "mean_evaluator_expected_excess": float(np.mean(expected_excess)),
                    "bound": bound,
                    "generator_device": resolved_device,
                }
            )

    metrics = pd.DataFrame(rows)
    scenario_summaries = []
    for scenario_name, group in metrics.groupby("scenario", sort=True):
        alarms = int(group.false_escalation.sum())
        scenario_summaries.append(
            {
                "scenario": scenario_name,
                "streams": len(group),
                "false_escalations": alarms,
                "false_escalation_rate": alarms / len(group),
                "simultaneous_95pct_cp_upper": _cp_upper(
                    alarms, len(group), FAMILY_ALPHA / len(SCENARIO_NAMES)
                ),
                "mean_expected_excess": float(group.mean_evaluator_expected_excess.mean()),
                "mean_observed_excess": float(group.mean_observed_excess.mean()),
                "mean_max_e_value": float(group.max_e_value.mean()),
            }
        )
    truth_audit = {}
    for scenario_name, paths in expected_paths.items():
        eventwise_population_mean = np.mean(np.stack(paths), axis=0)
        prefix_population_mean = np.cumsum(eventwise_population_mean) / np.arange(
            1, len(paths[0]) + 1
        )
        truth_audit[scenario_name] = {
            "mean_expected_excess_over_horizon": float(eventwise_population_mean.mean()),
            "max_prefix_average_expected_excess": float(prefix_population_mean.max()),
            "min_prefix_average_expected_excess": float(prefix_population_mean.min()),
            "weak_null_prefix_audit_nonpositive": bool(prefix_population_mean.max() <= 1e-12),
        }
    null_audit_pass = all(
        item["weak_null_prefix_audit_nonpositive"] for item in truth_audit.values()
    )
    calibration_pass = all(
        item["simultaneous_95pct_cp_upper"] <= ALPHA for item in scenario_summaries
    )
    report = {
        "experiment": "comparecast_weak_running_average_null_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "diagnostic_pass" if null_audit_pass and calibration_pass else "inconclusive",
        "config": {
            "seeds_per_scenario": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "d": d,
            "monitor_start": max(800, int(n * 0.25)),
            "alpha": ALPHA,
            "threshold": 1 / ALPHA,
            "harm_margin": HARM_MARGIN,
            "scenarios": list(SCENARIO_NAMES),
            "device": resolved_device,
            "source_feedback": "immediate full-feedback paired cost; no label acquisition",
        },
        "null": "weak running-average expected paired score excess <= 0 at every monitored prefix",
        "population_null_prefix_audit": truth_audit,
        "population_null_audit_pass": null_audit_pass,
        "simultaneous_exact_binomial_calibration_pass": calibration_pass,
        "scenario_results": scenario_summaries,
        "source": {
            "repository": "https://github.com/yjchoe/ComparingForecasters",
            "commit": commit,
            "eprocess_sha256": _sha256(source_dir / "comparecast/eprocess.py"),
        },
        "source_hashes": {
            "runner": _sha256(Path(__file__).resolve()),
            "protocol": _sha256(PROTOCOL),
            "risk_proxy_generator": _sha256(Path("src/shiftlab/dive/risk_proxy_monitor_grid.py")),
            "scenario_generator": _sha256(Path("src/shiftlab/decision_harm_experiment.py")),
        },
        "upstream_warning_messages": sorted(warning_messages),
        "upstream_warning_count": warning_count,
        "upstream_warning_handling": "captured and counted as diagnostics; official source is not modified",
        "comparison_limits": [
            "This calibration addresses only the weak running-average null, not DIVE's eventwise conditional-mean null.",
            "The null-truth prefix audit is a finite Monte Carlo check of evaluator expected costs; the generated family is the registered synthetic population-null control.",
            "Calibration is not an independent alternative confirmation and does not establish real-data validity.",
        ],
        "environment": environment(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    metrics.to_parquet(output_dir / "metrics.parquet", index=False)
    summary = pd.DataFrame(scenario_summaries)
    summary.to_csv(output_dir / "summary.csv", index=False)
    summary.to_parquet(output_dir / "summary.parquet", index=False)
    report_lines = [
        "# Comparecast weak-running-average null calibration",
        "",
        f"**Status:** `{report['status']}`; CUDA requested and resolved to `{resolved_device}`.",
        "",
        f"The official e-process was evaluated on {seeds:,} independent streams per registered population-null scenario, with {n - max(800, int(n * 0.25)):,} monitored events per stream. The eventwise score was paired cost difference minus the fixed {HARM_MARGIN:.2f} margin; the escalation threshold was {1 / ALPHA:.0f}.",
        "",
        "| Scenario | Streams | False escalations | Rate | Simultaneous one-sided 95% exact upper bound | Mean expected excess | Max expected prefix average |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in scenario_summaries:
        truth = truth_audit[item["scenario"]]
        report_lines.append(
            f"| {item['scenario']} | {item['streams']:,} | {item['false_escalations']} | {item['false_escalation_rate']:.3%} | {item['simultaneous_95pct_cp_upper']:.3%} | {item['mean_expected_excess']:.5f} | {truth['max_prefix_average_expected_excess']:.5f} |"
        )
    report_lines.extend(
        [
            "",
            "The weak-null evaluator prefix audit was nonpositive in both scenarios. The simultaneous exact upper bounds use Bonferroni coverage over the two scenario cells and are below the 0.05 level. The two named scenarios yield identical truth summaries in this generator because the benign shift changes nuisance coordinates that do not enter the paired decision contrast.",
            "",
            "This supports the frozen Comparecast e-process as calibrated on these synthetic weak-null controls; it is not proof of its theorem, not calibration of DIVE's eventwise conditional-mean null, and not an alternative-power confirmation. The feedback is immediate and full; no label acquisition or delayed feedback is tested. The masked-log warnings were captured. They are numerical diagnostics only; the pinned implementation's formula passed the separate quadrature audit.",
            "",
            "See `metrics.csv`, `summary.csv` and `manifest.json` for seed-level metrics, exact source/config hashes, runtime/GPU and artifact checksums. No figures were specified for this calibration.",
        ]
    )
    (output_dir / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    report["artifact_sha256"] = {
        name: _sha256(output_dir / name)
        for name in (
            "metrics.csv",
            "metrics.parquet",
            "summary.csv",
            "summary.parquet",
            "results.md",
        )
    }
    report["rows"] = len(metrics)
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparecast-source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=60_000_000)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    result = run(
        source_dir=args.comparecast_source,
        output_dir=args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        d=args.d,
        device=args.device,
    )
    print(pd.DataFrame(result["scenario_results"]).to_string(index=False))
    print(f"status={result['status']}; output={args.output_dir}")


if __name__ == "__main__":
    main()
