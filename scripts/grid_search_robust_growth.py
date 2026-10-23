"""Development grid for worst-case mixture-growth label acquisition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

RADII = (0.0, 0.05, 0.10, 0.20, 0.40)
SCENARIOS = ("stationary", "benign_nuisance", "boundary_local_harm")
BASELINE_METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
    "exact_mixture_growth_proxy",
)


def _rmse(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(values))))


def _paired_rows(
    candidate: pd.DataFrame,
    baseline: pd.DataFrame,
    *,
    radius: float,
    scenario: str,
    seed: int,
) -> dict[str, object]:
    cand = candidate.set_index("seed").sort_index()
    base = baseline.set_index("seed").sort_index()
    if not cand.index.equals(base.index):
        raise ValueError(f"radius {radius} is not seed-matched in {scenario}")
    detection_delta = (
        cand.single_e_detected.astype(float).to_numpy()
        - base.single_e_detected.astype(float).to_numpy()
    )
    error_candidate = cand.stream_mean_estimation_error.to_numpy(dtype=float)
    error_base = base.stream_mean_estimation_error.to_numpy(dtype=float)
    rng = np.random.default_rng(seed + int(radius * 10_000) + len(scenario))
    indices = rng.integers(0, len(cand), size=(20_000, len(cand)))
    detection_draws = detection_delta[indices].mean(axis=1)
    rmse_draws = np.sqrt(np.mean(error_candidate[indices] ** 2, axis=1)) - np.sqrt(
        np.mean(error_base[indices] ** 2, axis=1)
    )
    return {
        "probability_radius": radius,
        "scenario": scenario,
        "seeds": len(cand),
        "candidate_detections": int(cand.single_e_detected.sum()),
        "uniform_detections": int(base.single_e_detected.sum()),
        "paired_detection_difference": float(detection_delta.mean()),
        "detection_ci_low": float(np.quantile(detection_draws, 0.025)),
        "detection_ci_high": float(np.quantile(detection_draws, 0.975)),
        "candidate_false_escalations": int(cand.single_e_false_escalation.sum()),
        "uniform_false_escalations": int(base.single_e_false_escalation.sum()),
        "candidate_spend": float(cand.realized_label_spend.mean()),
        "uniform_spend": float(base.realized_label_spend.mean()),
        "candidate_labels": float(cand.labels_queried.mean()),
        "uniform_labels": float(base.labels_queried.mean()),
        "candidate_processed": float(cand.processed_events.mean()),
        "uniform_processed": float(base.processed_events.mean()),
        "candidate_rmse": _rmse(error_candidate),
        "uniform_rmse": _rmse(error_base),
        "rmse_difference": _rmse(error_candidate) - _rmse(error_base),
        "rmse_ci_low": float(np.quantile(rmse_draws, 0.025)),
        "rmse_ci_high": float(np.quantile(rmse_draws, 0.975)),
        "mean_probability_interval_coverage": float(
            cand.robust_probability_interval_coverage.mean()
        ),
        "budget_violations": int((~cand.budget_respected).sum()),
    }


def run_grid(
    *,
    output: Path,
    seeds: int = 30,
    seed_offset: int = 28602026,
    n: int = 3200,
    d: int = 16,
    budget_rate: float = 0.20,
    q_min: float = 0.10,
    q_max: float = 0.80,
    device: str = "cuda",
) -> Path:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty grid output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    runs = output / "runs"
    runs.mkdir(exist_ok=True)
    common = {
        "n": n,
        "d": d,
        "seeds": seeds,
        "seed_offset": seed_offset,
        "budget_rate": budget_rate,
        "q_min": q_min,
        "q_max": q_max,
        "common_eprocess_bound": True,
        "device": device,
        "scenario_subset": SCENARIOS,
    }
    baseline_path = runs / "established_baselines"
    run_hard_budget(HardBudgetConfig(**common, method_subset=BASELINE_METHODS), baseline_path)
    baseline = pd.read_parquet(baseline_path / "metrics" / "hard_budget_comparison.parquet")
    run_manifests = {"established_baselines": baseline_path / "reports" / "manifest.json"}
    frames = [baseline]
    summary_rows: list[dict[str, object]] = []
    uniform = baseline.loc[baseline.method.eq("uniform_proxy")]
    for radius in RADII:
        tag = f"probability_radius_{radius:.2f}"
        run_path = runs / tag
        run_hard_budget(
            HardBudgetConfig(
                **common,
                robust_growth_probability_radius=radius,
                method_subset=("robust_mixture_growth_proxy",),
            ),
            run_path,
        )
        robust = pd.read_parquet(run_path / "metrics" / "hard_budget_comparison.parquet")
        robust["probability_radius"] = radius
        frames.append(robust)
        run_manifests[tag] = run_path / "reports" / "manifest.json"
        for scenario in SCENARIOS:
            summary_rows.append(
                _paired_rows(
                    robust.loc[robust.scenario.eq(scenario)],
                    uniform.loc[uniform.scenario.eq(scenario)],
                    radius=radius,
                    scenario=scenario,
                    seed=seed_offset,
                )
            )

    metrics = pd.concat(frames, ignore_index=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for folder in (metrics_dir, reports_dir, figures_dir):
        folder.mkdir(exist_ok=True)
    metrics.to_parquet(metrics_dir / "development_streams.parquet", index=False)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(metrics_dir / "robust_growth_grid_summary.csv", index=False)

    boundary = summary.loc[summary.scenario.eq("boundary_local_harm")].copy()
    nulls = summary.loc[summary.scenario.isin(("stationary", "benign_nuisance"))]
    max_false = max(1, int(0.05 * 2 * seeds))
    eligible = boundary.loc[
        boundary.probability_radius.map(
            lambda radius: (
                int(
                    nulls.loc[
                        nulls.probability_radius.eq(radius), "candidate_false_escalations"
                    ].sum()
                )
                <= max_false
            )
        )
    ]
    if eligible.empty:
        raise RuntimeError("no radius met the predeclared null false-escalation guardrail")
    eligible = eligible.sort_values(
        ["candidate_detections", "candidate_rmse", "candidate_processed"],
        ascending=[False, True, False],
    )
    selected_radius = float(eligible.iloc[0].probability_radius)
    selected_detection = int(eligible.iloc[0].candidate_detections)
    selected_uniform_detection = int(eligible.iloc[0].uniform_detections)
    selected_rmse_signal = bool(eligible.iloc[0].rmse_ci_high < 0)
    fresh_required = selected_detection > selected_uniform_detection or selected_rmse_signal

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    axes[0].plot(
        boundary.probability_radius,
        boundary.candidate_detections / boundary.seeds,
        marker="o",
        label="Robust allocation",
    )
    axes[0].plot(
        boundary.probability_radius,
        boundary.uniform_detections / boundary.seeds,
        linestyle="--",
        label="Uniform baseline",
    )
    axes[0].set_ylabel("Boundary-harm detection rate")
    axes[0].legend(fontsize=8)
    axes[1].plot(boundary.probability_radius, boundary.candidate_rmse, marker="o")
    axes[1].plot(boundary.probability_radius, boundary.uniform_rmse, linestyle="--")
    axes[1].set_ylabel("Stream-mean estimation RMSE")
    axes[2].plot(
        boundary.probability_radius,
        boundary.mean_probability_interval_coverage,
        marker="o",
    )
    axes[2].set_ylabel("Evaluator-only probability interval coverage")
    for ax in axes:
        ax.set_xlabel("Probability uncertainty radius")
        ax.set_xticks(RADII)
        ax.grid(alpha=0.25)
    fig.savefig(figures_dir / "robust_growth_radius_grid.png", dpi=170)
    plt.close(fig)

    lines = [
        "# Development grid: robust exact mixture-growth allocation",
        "",
        f"This development-only grid used {seeds} paired stream seeds per scenario, CUDA request `{device}`, and probability radii {list(RADII)}. The six established methods were run on the same streams as reference baselines. Every candidate shared stream seeds, query uniforms, target dollar budget, propensity bounds, common e-process bound, and hard per-stream dollar cap.",
        "",
        "For each covariate, the algorithm maximizes the worst-case one-step expected log mixture-e-value increment over a fixed interval around the pre-monitor classifier's outcome probability, less a dual label-cost price. This is a model-robust objective only for the declared interval; the true post-shift probability may lie outside it. The query probability remains predictable and the e-process guarantee conditions are unchanged.",
        "",
        "|Radius|Scenario|Detections / uniform|Paired detection difference (95% bootstrap)|False escalations|RMSE / uniform|RMSE difference (95% bootstrap)|Spend / uniform|Labels / uniform|Mean evaluator-only interval coverage|",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['probability_radius']:.2f}|{row['scenario']}|"
            f"{row['candidate_detections']}/{seeds} / {row['uniform_detections']}/{seeds}|"
            f"{row['paired_detection_difference']:+.3f} [{row['detection_ci_low']:+.3f}, {row['detection_ci_high']:+.3f}]|"
            f"{row['candidate_false_escalations']} / {row['uniform_false_escalations']}|"
            f"{row['candidate_rmse']:.4f} / {row['uniform_rmse']:.4f}|"
            f"{row['rmse_difference']:+.4f} [{row['rmse_ci_low']:+.4f}, {row['rmse_ci_high']:+.4f}]|"
            f"{row['candidate_spend']:.2f} / {row['uniform_spend']:.2f}|"
            f"{row['candidate_labels']:.1f} / {row['uniform_labels']:.1f}|"
            f"{row['mean_probability_interval_coverage']:.3f}|"
        )
    lines.extend(
        [
            "",
            "## Development selection",
            "",
            f"Selected probability radius: **{selected_radius:.2f}** ({selected_detection}/{seeds} boundary-harm detections; uniform {selected_uniform_detection}/{seeds}). The predeclared rule maximizes detections under a pooled 5% null false-escalation guardrail, then minimizes boundary stream-mean RMSE and maximizes processed events.",
            (
                "A fresh evaluation is required because the selected candidate exceeded uniform on the primary detection count or showed a bootstrap RMSE improvement. This remains exploratory until that independent block is completed."
                if fresh_required
                else "No candidate beat uniform on boundary-harm detections or showed a paired-bootstrap RMSE improvement. The grid does not justify a confirmatory run or an efficacy claim; retain the method only as an exploratory baseline."
            ),
            "",
            f"Reproduce with `uv run python scripts/grid_search_robust_growth.py --output outputs/robust_growth_grid_development --seeds {seeds} --seed-offset {seed_offset} --n {n} --d {d} --budget-rate {budget_rate} --q-min {q_min} --q-max {q_max} --device {device}`.",
            "",
        ]
    )
    (reports_dir / "robust_growth_grid.md").write_text("\n".join(lines), encoding="utf-8")
    selected = {
        "probability_radius": selected_radius,
        "development_seed_offset": seed_offset,
        "development_seeds_per_scenario": seeds,
        "selection_rule": "maximize boundary-harm detections subject to <=5% pooled null false escalations; tie-break by lower stream-mean RMSE then longer processed horizon",
        "fresh_evaluation_required": fresh_required,
    }
    (reports_dir / "selected_radius.json").write_text(
        json.dumps(selected, indent=2), encoding="utf-8"
    )
    manifest = {
        "experiment": "development_grid_robust_mixture_growth",
        "protocol": {"radii": list(RADII), "scenarios": list(SCENARIOS), **common},
        "selected_probability_radius": selected_radius,
        "fresh_evaluation_required": fresh_required,
        "row_count": len(metrics),
        "script": "scripts/grid_search_robust_growth.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    manifest_path = reports_dir / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["nested_run_manifests"] = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in run_manifests.items()
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/robust_growth_grid_development")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=28602026)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--budget-rate", type=float, default=0.20)
    parser.add_argument("--q-min", type=float, default=0.10)
    parser.add_argument("--q-max", type=float, default=0.80)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    args = parser.parse_args()
    print(
        run_grid(
            output=args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            budget_rate=args.budget_rate,
            q_min=args.q_min,
            q_max=args.q_max,
            device=args.device,
        )
    )


if __name__ == "__main__":
    main()
