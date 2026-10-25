"""Development grid for direct-IPW monitoring with history-evidence querying."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment
from ..decision_harm_experiment import SCENARIOS
from .hard_budget import EVIDENCE_DIRECTED_GRID_METHODS, HardBudgetConfig, run_hard_budget

DEFAULT_QUERY_FLOORS = (0.05, 0.10, 0.20)
DEFAULT_SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
METHODS = ("uniform_proxy", *EVIDENCE_DIRECTED_GRID_METHODS)


@dataclass(frozen=True)
class DirectIPWQueryGridConfig:
    seeds: int = 30
    seed_offset: int = 31_025_000
    n: int = 3200
    d: int = 16
    budget_rate: float = 0.20
    q_max: float = 0.80
    alpha: float = 0.05
    harm_margin: float = 0.10
    query_floors: tuple[float, ...] = DEFAULT_QUERY_FLOORS
    scenarios: tuple[str, ...] = DEFAULT_SCENARIOS
    device: str = "cuda"
    bootstrap_replicates: int = 5000

    def validate(self) -> DirectIPWQueryGridConfig:
        if self.seeds < 2 or self.n < 1000 or self.d < 2:
            raise ValueError("require seeds >=2, n >=1000, and d >=2")
        if not self.query_floors or len(set(self.query_floors)) != len(self.query_floors):
            raise ValueError("query_floors must be nonempty and unique")
        if any(not 0 < floor <= self.budget_rate for floor in self.query_floors):
            raise ValueError("each query floor must be positive and at most budget_rate")
        if not 0 < self.budget_rate <= self.q_max <= 1:
            raise ValueError("require 0 < budget_rate <= q_max <= 1")
        registered = {scenario.name for scenario in SCENARIOS}
        if not self.scenarios or len(set(self.scenarios)) != len(self.scenarios):
            raise ValueError("scenarios must be nonempty and unique")
        if not set(self.scenarios) <= registered:
            raise ValueError("scenarios must be registered in decision_harm_experiment")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.bootstrap_replicates < 100:
            raise ValueError("bootstrap_replicates must be at least 100")
        return self


def _paired_summary(
    metrics: pd.DataFrame, *, bootstrap_replicates: int, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries: list[dict[str, object]] = []
    contrasts: list[dict[str, object]] = []
    rng = np.random.default_rng(seed)
    for (floor, scenario, method), group in metrics.groupby(
        ["query_floor", "scenario", "method"], sort=True
    ):
        harmful = group.loc[group.material_harm.astype(bool)]
        reached = harmful.loc[harmful.harm_reached_before_budget_stop.astype(bool)]
        summaries.append(
            {
                "query_floor": floor,
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "false_escalations": int(group.single_e_false_escalation.sum()),
                "harmful_streams": len(harmful),
                "reached_harm_streams": len(reached),
                "detections_all_harm": int(harmful.single_e_detected.sum()),
                "detection_rate_all_harm": (
                    float(harmful.single_e_detected.mean()) if len(harmful) else np.nan
                ),
                "detection_rate_reached_harm": (
                    float(reached.single_e_detected.mean()) if len(reached) else np.nan
                ),
                "mean_labels": float(group.labels_queried.mean()),
                "mean_spend": float(group.realized_label_spend.mean()),
                "mean_budget": float(group.hard_budget.mean()),
                "mean_events_processed": float(group.processed_events.mean()),
                "mean_excess_cost_avoided": float(
                    group.evaluator_excess_cost_avoided_by_fallback.mean()
                ),
                "cap_violations": int((~group.budget_respected.astype(bool)).sum()),
            }
        )

    for floor in sorted(metrics.query_floor.unique()):
        for scenario in sorted(metrics.scenario.unique()):
            baseline = metrics.loc[
                metrics.query_floor.eq(floor)
                & metrics.scenario.eq(scenario)
                & metrics.method.eq("uniform_proxy")
            ].sort_values("seed")
            for method in METHODS[1:]:
                candidate = metrics.loc[
                    metrics.query_floor.eq(floor)
                    & metrics.scenario.eq(scenario)
                    & metrics.method.eq(method)
                ].sort_values("seed")
                paired = baseline.merge(
                    candidate,
                    on=["query_floor", "scenario", "seed"],
                    suffixes=("_uniform", "_candidate"),
                    validate="one_to_one",
                )
                if len(paired) != len(baseline) or len(paired) != len(candidate):
                    raise ValueError("grid arms do not contain identical paired seed sets")
                n = len(paired)
                draw_index = rng.integers(0, n, size=(bootstrap_replicates, n))
                contrasts_for_arm: dict[str, tuple[float, float, float]] = {}
                metrics_to_compare = {
                    "detection_all_harm": (
                        paired.single_e_detected_candidate.astype(float).to_numpy()
                        - paired.single_e_detected_uniform.astype(float).to_numpy()
                    ),
                    "false_escalation": (
                        paired.single_e_false_escalation_candidate.astype(float).to_numpy()
                        - paired.single_e_false_escalation_uniform.astype(float).to_numpy()
                    ),
                    "labels": (
                        paired.labels_queried_candidate.to_numpy(dtype=float)
                        - paired.labels_queried_uniform.to_numpy(dtype=float)
                    ),
                    "spend": (
                        paired.realized_label_spend_candidate.to_numpy(dtype=float)
                        - paired.realized_label_spend_uniform.to_numpy(dtype=float)
                    ),
                    "events_processed": (
                        paired.processed_events_candidate.to_numpy(dtype=float)
                        - paired.processed_events_uniform.to_numpy(dtype=float)
                    ),
                    "excess_cost_avoided": (
                        paired.evaluator_excess_cost_avoided_by_fallback_candidate.to_numpy(
                            dtype=float
                        )
                        - paired.evaluator_excess_cost_avoided_by_fallback_uniform.to_numpy(
                            dtype=float
                        )
                    ),
                }
                is_harm = paired.material_harm_uniform.astype(bool).to_numpy()
                for endpoint, differences in metrics_to_compare.items():
                    selected = (
                        differences[is_harm] if endpoint == "detection_all_harm" else differences
                    )
                    if not len(selected):
                        contrasts_for_arm[endpoint] = (float("nan"), float("nan"), float("nan"))
                        continue
                    point = float(selected.mean())
                    indices = (
                        draw_index
                        if len(selected) == n
                        else rng.integers(
                            0, len(selected), size=(bootstrap_replicates, len(selected))
                        )
                    )
                    draws = selected[indices].mean(axis=1)
                    contrasts_for_arm[endpoint] = (
                        point,
                        float(np.quantile(draws, 0.025)),
                        float(np.quantile(draws, 0.975)),
                    )
                contrast = {
                    "query_floor": floor,
                    "scenario": scenario,
                    "method": method,
                    "n_paired_streams": n,
                    "n_harmful_streams": int(is_harm.sum()),
                }
                for endpoint, (point, low, high) in contrasts_for_arm.items():
                    contrast[f"{endpoint}_difference"] = point
                    contrast[f"{endpoint}_ci_low"] = low
                    contrast[f"{endpoint}_ci_high"] = high
                contrasts.append(contrast)
    return pd.DataFrame(summaries), pd.DataFrame(contrasts)


def run_direct_ipw_query_grid(config: DirectIPWQueryGridConfig, output: Path) -> Path:
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty development output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    started_utc = datetime.now(UTC).isoformat()
    frames = []
    for floor in config.query_floors:
        floor_name = f"q_min_{floor:.2f}".replace(".", "p")
        sub_output = output / "runs" / floor_name
        run_config = HardBudgetConfig(
            n=config.n,
            d=config.d,
            seeds=config.seeds,
            seed_offset=config.seed_offset,
            alpha=config.alpha,
            harm_margin=config.harm_margin,
            budget_rate=config.budget_rate,
            monitor_estimator="direct_ipw",
            q_min=floor,
            q_max=config.q_max,
            common_eprocess_bound=True,
            generate_figure=False,
            device=config.device,
            workers=1,
            scenario_subset=config.scenarios,
            method_subset=METHODS,
        )
        print(f"starting direct-IPW grid q_min={floor:.2f} on {config.device}", flush=True)
        run_hard_budget(run_config, sub_output)
        metrics = pd.read_parquet(sub_output / "metrics" / "hard_budget_comparison.parquet")
        metrics["query_floor"] = floor
        metrics["budget_rate_target"] = config.budget_rate
        frames.append(metrics)
    combined = pd.concat(frames, ignore_index=True).sort_values(
        ["query_floor", "scenario", "seed", "method"], kind="stable"
    )
    if not combined.budget_respected.astype(bool).all():
        raise RuntimeError("direct-IPW grid contains a hard-budget violation")
    if set(combined.monitor_estimator.unique()) != {"direct_ipw"}:
        raise RuntimeError("grid contains an unexpected estimator")

    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(metrics_dir / "direct_ipw_query_grid.parquet", index=False)
    summary, contrasts = _paired_summary(
        combined,
        bootstrap_replicates=config.bootstrap_replicates,
        seed=config.seed_offset + 81_773,
    )
    summary.to_csv(metrics_dir / "grid_summary.csv", index=False)
    contrasts.to_csv(metrics_dir / "paired_contrasts_vs_uniform.csv", index=False)

    table = summary[
        [
            "query_floor",
            "scenario",
            "method",
            "detection_rate_all_harm",
            "reached_harm_streams",
            "harmful_streams",
            "false_escalations",
            "mean_labels",
            "mean_spend",
            "mean_events_processed",
            "mean_excess_cost_avoided",
        ]
    ].to_markdown(index=False, floatfmt=".3f")
    paired_table = contrasts[
        [
            "query_floor",
            "scenario",
            "method",
            "detection_all_harm_difference",
            "detection_all_harm_ci_low",
            "detection_all_harm_ci_high",
            "labels_difference",
            "labels_ci_low",
            "labels_ci_high",
            "excess_cost_avoided_difference",
            "excess_cost_avoided_ci_low",
            "excess_cost_avoided_ci_high",
        ]
    ].to_markdown(index=False, floatfmt=".3f")
    report = (
        "# Direct-IPW history-evidence query development grid\n\n"
        f"Completed {config.seeds} paired seeds per scenario and query floor on "
        f"`{config.device}` in {time.perf_counter() - started:.1f} seconds. "
        f"The grid contains {len(combined):,} method-stream rows over "
        f"{len(config.query_floors)} query floors, {len(config.scenarios)} scenarios, "
        f"and {len(METHODS)} methods. All methods within each seed/floor/scenario share "
        "the same synthetic stream, query uniforms, fixed monitor bound, and pathwise "
        "dollar cap. Evidence-directed rates depend only on the prior monitor e-value "
        "and remaining past spend.\n\n"
        "This is exploratory method development, not null calibration or confirmation. "
        "The paired percentile intervals are descriptive and unadjusted across the grid; "
        "zero false alarms in these small null cells would not establish error control. "
        "Detection counts include all evaluator-defined harmful streams, so an onset "
        "missed because the cap stopped monitoring remains a nondetection; the separate "
        "reach counts expose that censoring. No candidate is selected for a paper claim "
        "from this grid alone.\n\n"
        "## Per-cell outcomes\n\n"
        f"{table}\n\n"
        "## Paired contrasts against uniform querying\n\n"
        f"{paired_table}\n\n"
        "Reproduce with `uv run shiftlab-dive-direct-ipw-query-grid --device cuda "
        f"--seeds {config.seeds} --seed-offset {config.seed_offset} "
        f"--output {output.as_posix()}`. No figure is generated in this development run."
    )
    (reports_dir / "direct_ipw_query_grid_results.md").write_text(report, encoding="utf-8")
    manifest = {
        "experiment": "direct_ipw_history_evidence_query_development_grid",
        "status": "exploratory_development_only",
        "started_utc": started_utc,
        "config": asdict(config),
        "methods": METHODS,
        "matched_design": {
            "same_stream_seed_by_floor": True,
            "same_query_uniforms_within_stream": True,
            "common_eprocess_bound_within_floor": True,
            "hard_dollar_cap": True,
            "estimator": "direct_ipw",
            "feedback": "immediate",
            "eventwise_bounds": False,
        },
        "runtime": environment(),
        "elapsed_seconds": time.perf_counter() - started,
        "rows": len(combined),
        "cap_violations": int((~combined.budget_respected.astype(bool)).sum()),
        "output_files": [
            "metrics/direct_ipw_query_grid.parquet",
            "metrics/grid_summary.csv",
            "metrics/paired_contrasts_vs_uniform.csv",
            "reports/direct_ipw_query_grid_results.md",
        ],
        "sha256": {},
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != manifest_path:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest["sha256"][path.relative_to(output).as_posix()] = digest
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/direct_ipw_query_development_30")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=31_025_000)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args(argv)
    config = DirectIPWQueryGridConfig(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        d=args.d,
        device=args.device,
    )
    print(run_direct_ipw_query_grid(config, args.output), flush=True)


if __name__ == "__main__":
    main()
