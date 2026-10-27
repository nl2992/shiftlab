"""Matched paired-cost adaptation of the UAI 2025 unknown-shift risk monitor.

The scalar GRAPA formulas are implemented here independently, then checked
against the pinned official reference implementation on deterministic streams.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest

from shiftlab.data.gpu.environment import environment
from shiftlab.decision_harm_experiment import SCENARIOS as GENERATOR_SCENARIOS
from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.dive.risk_proxy_monitor_grid import (
    ALTERNATIVE_SCENARIOS,
    NULL_SCENARIOS,
    RiskProxyMonitorGridConfig,
    _prepare_stream,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/timans_unknown_shift_paired_cost_protocol_v1.md"
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/timans_unknown_shift_paired_cost_v1"
EXPECTED_UPSTREAM_COMMIT = "4bf66a37dc2a3d7959bb9dcb325b61e8bb3c28e5"
SEED_START = 1_500_000_000
NULL_SEEDS = 1_000
ALTERNATIVE_SEEDS = 300
N = 2_400
D = 16
ALPHA = 0.05
EPSILON = 0.5
BURN_IN = 100
GRAPA_LAMBDAS = np.arange(1, 20, dtype=np.float64) / 10.0
METHODS = (
    "shiftlab_fixed_stake_mixture",
    "timans_approx_grapa",
    "timans_grapa_grid",
)
SCENARIO_NAMES = (*NULL_SCENARIOS, *ALTERNATIVE_SCENARIOS)
FAMILYWISE_ALPHA = 0.05
BOOTSTRAP_REPLICATES = 10_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _first_crossing(log_values: np.ndarray, alpha: float) -> int | None:
    indices = np.flatnonzero(log_values >= -np.log(alpha))
    return int(indices[0]) if len(indices) else None


def _timans_logs(
    score: np.ndarray,
    *,
    rule: str,
    epsilon: float = EPSILON,
    alpha: float = ALPHA,
    burn_in: int = BURN_IN,
) -> np.ndarray:
    """Replay the paper's predictable approximate-GRAPA or grid-GRAPA wealth."""
    values = np.asarray(score, dtype=np.float64)
    if values.ndim != 1 or not len(values) or np.any(~np.isfinite(values)):
        raise ValueError("score must be a nonempty finite vector")
    if np.any((values < 0) | (values > 1)):
        raise ValueError("score must stay within [0, 1]")
    if not 0 < epsilon < 1 or not 0 < alpha < 1 or burn_in < 1:
        raise ValueError("epsilon/alpha/burn-in are outside their valid ranges")
    if rule not in {"approx_grapa", "grapa"}:
        raise ValueError(f"unsupported Timans betting rule: {rule}")

    result = np.zeros(len(values), dtype=np.float64)
    log_wealth = 0.0
    count = 0
    mean = 0.0
    m2 = 0.0
    candidate_log_growth = np.zeros(len(GRAPA_LAMBDAS), dtype=np.float64)

    for time, observation in enumerate(values):
        if time < burn_in:
            bet = 0.0
        elif rule == "approx_grapa":
            sample_variance = m2 / (count - 1) if count > 1 else float("nan")
            mu = mean + 1e-10
            variance = sample_variance + 1e-10
            term = (mu - epsilon) / (variance + (mu - epsilon) ** 2) + 1e-10
            bet = max(0.0, min(term, 0.5 / epsilon))
            if not np.isfinite(bet):
                raise FloatingPointError("approx-GRAPA selected a nonfinite predictable bet")
        else:
            bet = float(GRAPA_LAMBDAS[int(np.argmax(candidate_log_growth))])

        factor = 1.0 + bet * (observation - epsilon)
        if not np.isfinite(factor) or factor <= 0:
            raise FloatingPointError("Timans betting factor must be positive and finite")
        log_wealth += float(np.log(factor))
        result[time] = log_wealth

        # Update all history summaries only after the current predictable bet
        # has been chosen and its score observed.
        if rule == "grapa":
            factors = 1.0 + GRAPA_LAMBDAS * (observation - epsilon)
            if np.any(factors <= 0):
                raise FloatingPointError("GRAPA candidate bet left its valid range")
            candidate_log_growth += np.log(factors)
        delta = observation - mean
        count = time + 1
        mean += delta / count
        m2 += delta * (observation - mean)
    return result


def _fixed_mixture_logs(increments: np.ndarray, *, bound: float, alpha: float) -> np.ndarray:
    process = BoundedMeanEProcess(bound=bound, alpha=alpha)
    values = np.empty(len(increments), dtype=np.float64)
    for index, value in enumerate(increments):
        values[index] = process.update(float(value))
    return values


def _load_official_tracker(source: Path):
    root_str = str(source.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from exp.tracker_uci import EProcessTracker  # type: ignore[import-not-found]

    return EProcessTracker


def verify_upstream_replay(source: Path) -> dict[str, float]:
    """Compare the independent formulas with the official PyTorch class."""
    import torch

    tracker_class = _load_official_tracker(source)
    sample = np.linspace(0.02, 0.98, 137, dtype=np.float64)
    observed: dict[str, float] = {}
    for rule in ("approx_grapa", "grapa"):
        cfg = SimpleNamespace(
            EXP=SimpleNamespace(
                NR_TRIALS=1,
                NR_TIMESTEPS=len(sample),
                NR_BURNIN=BURN_IN,
                BATCH_TIMESTEP=1,
                TRACKER_WINDOW=[0, 0, 0],
                STOP_COUNTER=[0, 0, 0],
                BET_TYPE=rule,
                EPS=EPSILON,
                DELTA=ALPHA,
            )
        )
        upstream = tracker_class(cfg, None, [0.0])
        tensor = torch.as_tensor(sample, dtype=torch.float32).reshape(-1, 1)
        reference = np.empty(len(sample), dtype=np.float64)
        for time in range(len(sample)):
            bet = upstream.get_bets(tensor, time)
            e_value = upstream.get_evalues(tensor[time : time + 1], bet, reduction="mean")
            wealth = upstream.get_eprocess(e_value, 0, time)
            upstream.eprocess[0, time, :] = wealth
            reference[time] = float(torch.log(wealth[0]).item())
        local = _timans_logs(sample, rule=rule)
        maximum_error = float(np.max(np.abs(reference - local)))
        observed[rule] = maximum_error
        if maximum_error > 2e-5:
            raise RuntimeError(f"local {rule} replay differs from official code: {maximum_error}")
    return observed


def _null_upper(events: int, trials: int, *, family_cells: int) -> float:
    if events == trials:
        return 1.0
    return float(beta.ppf(1 - FAMILYWISE_ALPHA / family_cells, events + 1, trials - events))


def _family_interval(events: int, trials: int, *, family_cells: int) -> tuple[float, float]:
    tail = FAMILYWISE_ALPHA / (2 * family_cells)
    lower = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    upper = 1.0 if events == trials else float(beta.ppf(1 - tail, events + 1, trials - events))
    return lower, upper


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=np.float64)
    running = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (count - rank) * p_values[int(index)])
        adjusted[int(index)] = min(1.0, running)
    return adjusted.tolist()


def _paired_comparisons(metrics: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20261026)
    alternatives = ALTERNATIVE_SCENARIOS
    pairs = (
        (METHODS[1], METHODS[0]),
        (METHODS[2], METHODS[0]),
        (METHODS[1], METHODS[2]),
    )
    pending: list[dict[str, Any]] = []
    for scenario in alternatives:
        table = metrics.loc[metrics.scenario.eq(scenario)].pivot(
            index="seed", columns="method", values="post_onset_detection"
        )
        if len(table) != ALTERNATIVE_SEEDS or table.isna().any().any():
            raise RuntimeError(f"paired comparison is incomplete for {scenario}")
        for left, right in pairs:
            left_detect = table[left].to_numpy(dtype=bool)
            right_detect = table[right].to_numpy(dtype=bool)
            differences = left_detect.astype(np.float64) - right_detect.astype(np.float64)
            bootstrap_indices = rng.integers(
                0, len(differences), size=(BOOTSTRAP_REPLICATES, len(differences))
            )
            bootstrap_means = differences[bootstrap_indices].mean(axis=1)
            left_only = int(np.sum(left_detect & ~right_detect))
            right_only = int(np.sum(right_detect & ~left_detect))
            p_value = (
                float(binomtest(min(left_only, right_only), left_only + right_only, 0.5).pvalue)
                if left_only + right_only
                else 1.0
            )
            pending.append(
                {
                    "scenario": scenario,
                    "left_method": left,
                    "right_method": right,
                    "left_minus_right_detection_rate": float(differences.mean()),
                    "bootstrap_ci_lower": float(np.quantile(bootstrap_means, 0.025)),
                    "bootstrap_ci_upper": float(np.quantile(bootstrap_means, 0.975)),
                    "left_only_detections": left_only,
                    "right_only_detections": right_only,
                    "mcnemar_p_value": p_value,
                }
            )
    adjusted = _holm([float(row["mcnemar_p_value"]) for row in pending])
    for row, p_adjusted in zip(pending, adjusted, strict=True):
        row["holm_adjusted_mcnemar_p"] = p_adjusted
    return pd.DataFrame(pending)


def _source_commit(source: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()


def _audit_seed_overlap() -> list[str]:
    start = SEED_START
    end = SEED_START + NULL_SEEDS + ALTERNATIVE_SEEDS - 1
    overlapping: list[str] = []
    root = ROOT / "outputs/shiftguard_unified"
    for path in root.rglob("manifest.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        config = manifest.get("config", {})
        offsets = [config.get("seed_offset"), manifest.get("seed_start")]
        ranges = [manifest.get("seed_range"), manifest.get("seed_range_inclusive")]
        for candidate in offsets:
            if isinstance(candidate, int) and candidate <= end and candidate + 100_000 >= start:
                overlapping.append(str(path.relative_to(ROOT)))
        for candidate in ranges:
            if (
                isinstance(candidate, list)
                and len(candidate) == 2
                and all(isinstance(item, int) for item in candidate)
                and candidate[0] <= end
                and candidate[1] >= start
            ):
                overlapping.append(str(path.relative_to(ROOT)))
    return sorted(set(overlapping))


def run(
    *,
    source_dir: Path,
    output_dir: Path = OUTPUT,
    null_seeds: int = NULL_SEEDS,
    alternative_seeds: int = ALTERNATIVE_SEEDS,
    seed_start: int = SEED_START,
    device: str = "cuda",
) -> dict[str, Any]:
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    if _source_commit(source_dir) != EXPECTED_UPSTREAM_COMMIT:
        raise RuntimeError(
            "official risk-monitor repository commit does not match the frozen protocol"
        )
    if (
        null_seeds != NULL_SEEDS
        or alternative_seeds != ALTERNATIVE_SEEDS
        or seed_start != SEED_START
    ):
        raise ValueError("run dimensions and seed block are frozen by protocol v1")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    if _audit_seed_overlap():
        raise RuntimeError(
            f"seed block overlaps existing manifest declarations: {_audit_seed_overlap()}"
        )
    replay_errors = verify_upstream_replay(source_dir)

    import torch

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    config = RiskProxyMonitorGridConfig(
        n=N,
        d=D,
        null_seeds=null_seeds,
        alternative_seeds=alternative_seeds,
        seed_offset=seed_start,
        alpha=ALPHA,
        harm_margin=0.10,
        device=device,
    ).validate()
    scenarios = {scenario.name: scenario for scenario in GENERATOR_SCENARIOS}
    rows: list[dict[str, Any]] = []

    for scenario_name in SCENARIO_NAMES:
        seed_count = null_seeds if scenario_name in NULL_SCENARIOS else alternative_seeds
        seed_offset = seed_start if scenario_name in NULL_SCENARIOS else seed_start + null_seeds
        print(
            f"Generating {scenario_name}: {seed_count} streams on {config.device}.",
            flush=True,
        )
        for seed in range(seed_offset, seed_offset + seed_count):
            prepared = _prepare_stream(scenarios[scenario_name], seed, config)
            centered = np.asarray(prepared[3], dtype=np.float64)
            expected = np.asarray(prepared[4], dtype=np.float64)
            monitor_start = int(prepared[7])
            onset = prepared[9]
            bound = float(prepared[10])
            increments = centered[monitor_start:]
            if len(increments) != N - monitor_start:
                raise RuntimeError(f"wrong horizon for {scenario_name}/{seed}")
            if not np.isfinite(increments).all() or np.any(np.abs(increments) > bound + 1e-12):
                raise RuntimeError(f"paired cost left its declared support: {scenario_name}/{seed}")
            score = 0.5 + increments / (2 * bound)
            if np.any((score < 0) | (score > 1)):
                raise RuntimeError(f"transformed score left [0,1]: {scenario_name}/{seed}")

            log_paths = {
                METHODS[0]: _fixed_mixture_logs(increments, bound=bound, alpha=ALPHA),
                METHODS[1]: _timans_logs(score, rule="approx_grapa"),
                METHODS[2]: _timans_logs(score, rule="grapa"),
            }
            for method, log_values in log_paths.items():
                crossing = _first_crossing(log_values, ALPHA)
                onset_relative = None if onset is None else int(onset)
                post_onset = bool(
                    crossing is not None
                    and onset_relative is not None
                    and crossing >= onset_relative
                )
                pre_onset = bool(
                    crossing is not None and (onset_relative is None or crossing < onset_relative)
                )
                rows.append(
                    {
                        "scenario": scenario_name,
                        "seed": seed,
                        "method": method,
                        "events_processed": len(increments),
                        "alarm": crossing is not None,
                        "first_crossing_relative": crossing,
                        "harm_onset_relative": onset_relative,
                        "onset_eligible": onset_relative is not None,
                        "post_onset_detection": post_onset,
                        "pre_onset_alarm": pre_onset,
                        "max_log_e_value": float(np.max(log_values)),
                        "mean_expected_margin_excess": float(
                            np.mean(expected[monitor_start:] - 0.10)
                        ),
                        "score_lower": float(np.min(score)),
                        "score_upper": float(np.max(score)),
                        "score_bound": bound,
                        "generator_device": config.device,
                    }
                )
        print(f"Completed {scenario_name}: {seed_count} streams.", flush=True)

    metrics = pd.DataFrame(rows)
    expected_rows = len(METHODS) * (
        len(NULL_SCENARIOS) * null_seeds + len(ALTERNATIVE_SCENARIOS) * alternative_seeds
    )
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("metric completeness or uniqueness check failed")
    if not metrics.events_processed.eq(N - 800).all():
        raise RuntimeError("not all registered stream events were processed")

    summary_rows: list[dict[str, Any]] = []
    null_cells = len(METHODS) * len(NULL_SCENARIOS)
    alternative_cells = len(METHODS) * len(ALTERNATIVE_SCENARIOS)
    for scenario in SCENARIO_NAMES:
        for method in METHODS:
            group = metrics.loc[metrics.scenario.eq(scenario) & metrics.method.eq(method)]
            is_null = scenario in NULL_SCENARIOS
            trials = null_seeds if is_null else alternative_seeds
            event_name = "alarms" if is_null else "post_onset_detections"
            successes = int(group.alarm.sum()) if is_null else int(group.post_onset_detection.sum())
            lower, upper = _family_interval(
                successes,
                trials,
                family_cells=null_cells if is_null else alternative_cells,
            )
            detected = group.loc[group.post_onset_detection, "first_crossing_relative"].to_numpy(
                dtype=np.float64
            )
            onsets = group.loc[group.post_onset_detection, "harm_onset_relative"].to_numpy(
                dtype=np.float64
            )
            delays = detected - onsets if len(detected) else np.asarray([], dtype=np.float64)
            summary_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "streams": len(group),
                    event_name: successes,
                    "rate": successes / trials,
                    "simultaneous_cp_lower": lower,
                    "simultaneous_cp_upper": upper,
                    "pre_onset_alarms": int(group.pre_onset_alarm.sum()),
                    "onset_eligible_streams": int(group.onset_eligible.sum()),
                    "mean_delay_among_detections": float(np.mean(delays)) if len(delays) else None,
                    "median_delay_among_detections": float(np.median(delays))
                    if len(delays)
                    else None,
                    "mean_max_log_e_value": float(group.max_log_e_value.mean()),
                    "mean_expected_margin_excess": float(group.mean_expected_margin_excess.mean()),
                }
            )

    summary = pd.DataFrame(summary_rows)
    paired = _paired_comparisons(metrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    metrics.to_parquet(output_dir / "metrics.parquet", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    summary.to_parquet(output_dir / "summary.parquet", index=False)
    paired.to_csv(output_dir / "paired_detection_comparisons.csv", index=False)
    paired.to_parquet(output_dir / "paired_detection_comparisons.parquet", index=False)

    upstream_paths = (
        source_dir / "exp/tracker_uci.py",
        source_dir / "config/cfg_exp.py",
        source_dir / "config/exp_cp/cfg_uci.yaml",
        source_dir / "LICENSE",
    )
    manifest: dict[str, Any] = {
        "experiment": "timans_unknown_shift_paired_cost_matched_comparison",
        "status": "registered_synthetic_comparator_development_complete",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "source": {
            "paper": "https://proceedings.mlr.press/v286/timans25a.html",
            "repository": "https://github.com/alextimans/risk-monitor",
            "commit": _source_commit(source_dir),
            "license": "AGPL-3.0",
            "sha256": {
                str(path.relative_to(source_dir)).replace("\\", "/"): sha256(path)
                for path in upstream_paths
            },
            "independent_formula_replay_max_abs_log_wealth_error": replay_errors,
        },
        "config": {
            "n": N,
            "d": D,
            "monitor_start": 800,
            "events_per_stream": N - 800,
            "null_seeds_per_scenario": null_seeds,
            "alternative_seeds_per_scenario": alternative_seeds,
            "null_seed_range_inclusive": [seed_start, seed_start + null_seeds - 1],
            "alternative_seed_range_inclusive": [
                seed_start + null_seeds,
                seed_start + null_seeds + alternative_seeds - 1,
            ],
            "device": config.device,
            "alpha": ALPHA,
            "harm_margin": 0.10,
            "score_transform": "z=(paired_cost_minus_margin+bound)/(2*bound), epsilon=0.5",
            "methods": list(METHODS),
            "scenarios": list(SCENARIO_NAMES),
        },
        "hypotheses": {
            "all_methods": "E[z_t | F_(t-1)] <= 0.5 at every event",
            "equivalent_paired_cost": "E[deployed_cost-reference_cost | F_(t-1)] <= 0.10",
            "shiftlab_fixed_mixture": "equal mixture over fixed bets (0.05,0.1,0.2,0.4,0.8) on centered excess cost, support bound b",
            "timans_approx_grapa": "official default predictable approximate-GRAPA bet with c=0.5 and 100-event burn-in",
            "timans_grapa_grid": "official predictable grid-GRAPA bet over lambda 0.1..1.9 with 100-event burn-in",
        },
        "results": summary.to_dict(orient="records"),
        "paired_detection_comparisons": paired.to_dict(orient="records"),
        "environment": environment(),
        "interpretation": [
            "The paired-cost score adaptation places the published generic bounded-risk monitor on the same eventwise conditional-mean null as ShiftLab.",
            "Null upper bounds are familywise adjusted over the six method-by-control cells; the theorem is conditional on the stated filtration, boundedness, predictable bet, and immediate observed-label assumptions.",
            "Alternative paired comparisons are synthetic development evidence only and do not establish real-data transfer, integrated intervention value, or novelty.",
            "The official source is AGPL-3.0 and was not vendored; only its published formulas were independently implemented and checked against the pinned reference code.",
        ],
        "artifact_sha256": {},
    }
    for name in (
        "metrics.csv",
        "metrics.parquet",
        "summary.csv",
        "summary.parquet",
        "paired_detection_comparisons.csv",
        "paired_detection_comparisons.parquet",
    ):
        manifest["artifact_sha256"][name] = sha256(output_dir / name)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_report(output_dir, summary, paired, manifest)
    manifest["artifact_sha256"]["report.md"] = sha256(output_dir / "report.md")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _write_report(
    output_dir: Path, summary: pd.DataFrame, paired: pd.DataFrame, manifest: dict[str, Any]
) -> None:
    lines = [
        "# Timans et al. paired-cost monitor comparison",
        "",
        f"**Status:** completed registered synthetic development comparison on `{manifest['config']['device']}`.",
        "",
        "The paired-cost risk was transformed to the `[0,1]` score and fixed threshold `epsilon=0.5`; this makes the published bounded-risk null algebraically match the ShiftLab eventwise conditional-mean excess-cost null. No real-data or integrated-system claim follows.",
        "",
        "| Scenario | Method | Streams | Alarms / post-onset detections | Rate | Simultaneous exact 95% interval | Pre-onset alarms | Mean delay among detections |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict(orient="records"):
        count = row["alarms"] if row["scenario"] in NULL_SCENARIOS else row["post_onset_detections"]
        interval = f"[{row['simultaneous_cp_lower']:.4f}, {row['simultaneous_cp_upper']:.4f}]"
        delay = row["mean_delay_among_detections"]
        delay_text = f"{delay:.2f}" if delay is not None and np.isfinite(delay) else "n/a"
        lines.append(
            f"| {row['scenario']} | {row['method']} | {row['streams']} | {int(count)} | {row['rate']:.4f} | {interval} | {row['pre_onset_alarms']} | {delay_text} |"
        )
    lines.extend(
        [
            "",
            "Paired alternative detection contrasts use same-seed paths. Their bootstrap intervals are descriptive; Holm-adjusted exact McNemar tests address the 12 registered comparisons.",
            "",
            "| Scenario | Left method | Right method | Detection-rate difference | Paired bootstrap 95% interval | Holm-adjusted McNemar p |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in paired.to_dict(orient="records"):
        lines.append(
            f"| {row['scenario']} | {row['left_method']} | {row['right_method']} | {row['left_minus_right_detection_rate']:.4f} | [{row['bootstrap_ci_lower']:.4f}, {row['bootstrap_ci_upper']:.4f}] | {row['holm_adjusted_mcnemar_p']:.6g} |"
        )
    lines.extend(
        [
            "",
            f"Protocol SHA-256: `{manifest['protocol']['sha256']}`. Upstream source commit: `{manifest['source']['commit']}`. Independent short-stream maximum absolute log-wealth errors: `{manifest['source']['independent_formula_replay_max_abs_log_wealth_error']}`.",
            "",
            "Artifacts: `metrics.parquet`, `summary.parquet`, `paired_detection_comparisons.parquet`, and `manifest.json`.",
            "",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--null-seeds", type=int, default=NULL_SEEDS)
    parser.add_argument("--alternative-seeds", type=int, default=ALTERNATIVE_SEEDS)
    parser.add_argument("--seed-start", type=int, default=SEED_START)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    result = run(
        source_dir=args.reference_source,
        output_dir=args.output_dir,
        null_seeds=args.null_seeds,
        alternative_seeds=args.alternative_seeds,
        seed_start=args.seed_start,
        device=args.device,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "output_dir": str(args.output_dir),
                "rows": len(result["results"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
