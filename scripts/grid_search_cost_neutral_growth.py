"""Development-only grid for the cost-neutral robustification of exact mixture growth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

WEIGHTS = (0.0, 0.25, 0.50, 0.75, 1.0)
SCENARIOS = ("stationary", "benign_nuisance", "boundary_local_harm")
METHODS = ("uniform_proxy", "exact_mixture_growth_proxy")


def _rmse(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(values))))


def run_grid(
    *,
    output: Path,
    seeds: int = 30,
    seed_offset: int = 28402026,
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
    baseline_path = runs / "uniform"
    run_hard_budget(HardBudgetConfig(**common, method_subset=("uniform_proxy",)), baseline_path)
    frames = [pd.read_parquet(baseline_path / "metrics" / "hard_budget_comparison.parquet")]
    run_manifests = {"uniform": baseline_path / "reports" / "manifest.json"}

    for weight in WEIGHTS:
        tag = f"adaptive_weight_{weight:.2f}"
        run_path = runs / tag
        run_hard_budget(
            HardBudgetConfig(
                **common,
                exact_growth_adaptive_weight=weight,
                method_subset=("exact_mixture_growth_proxy",),
            ),
            run_path,
        )
        frame = pd.read_parquet(run_path / "metrics" / "hard_budget_comparison.parquet")
        frame["grid_weight"] = weight
        frames.append(frame)
        run_manifests[tag] = run_path / "reports" / "manifest.json"

    metrics = pd.concat(frames, ignore_index=True)
    metrics_path = output / "metrics"
    reports_path = output / "reports"
    figures_path = output / "figures"
    for folder in (metrics_path, reports_path, figures_path):
        folder.mkdir(exist_ok=True)
    metrics.to_parquet(metrics_path / "development_streams.parquet", index=False)

    baseline = metrics.loc[metrics.method.eq("uniform_proxy")].set_index(["scenario", "seed"])
    rows: list[dict[str, float | int]] = []
    for weight in WEIGHTS:
        candidate = metrics.loc[
            metrics.method.eq("exact_mixture_growth_proxy") & metrics.grid_weight.eq(weight)
        ].set_index(["scenario", "seed"])
        for scenario in SCENARIOS:
            cand = candidate.loc[scenario].sort_index()
            base = baseline.loc[scenario].sort_index()
            if not cand.index.equals(base.index):
                raise ValueError("candidate and uniform streams are not seed matched")
            pair_difference = (
                cand.single_e_detected.astype(float).to_numpy()
                - base.single_e_detected.astype(float).to_numpy()
            )
            rng = np.random.default_rng(seed_offset + int(weight * 1000) + len(scenario))
            indices = rng.integers(0, len(pair_difference), size=(20_000, len(pair_difference)))
            detection_draws = pair_difference[indices].mean(axis=1)
            error_candidate = cand.stream_mean_estimation_error.to_numpy(dtype=float)
            error_baseline = base.stream_mean_estimation_error.to_numpy(dtype=float)
            rmse_difference_draws = np.sqrt(
                np.mean(error_candidate[indices] ** 2, axis=1)
            ) - np.sqrt(np.mean(error_baseline[indices] ** 2, axis=1))
            rows.append(
                {
                    "adaptive_weight": weight,
                    "scenario": scenario,
                    "seeds": len(cand),
                    "candidate_detections": int(cand.single_e_detected.sum()),
                    "uniform_detections": int(base.single_e_detected.sum()),
                    "paired_detection_difference": float(pair_difference.mean()),
                    "detection_ci_low": float(np.quantile(detection_draws, 0.025)),
                    "detection_ci_high": float(np.quantile(detection_draws, 0.975)),
                    "candidate_false_escalations": int(cand.single_e_false_escalation.sum()),
                    "uniform_false_escalations": int(base.single_e_false_escalation.sum()),
                    "candidate_mean_spend": float(cand.realized_label_spend.mean()),
                    "uniform_mean_spend": float(base.realized_label_spend.mean()),
                    "candidate_mean_labels": float(cand.labels_queried.mean()),
                    "uniform_mean_labels": float(base.labels_queried.mean()),
                    "candidate_mean_processed_events": float(cand.processed_events.mean()),
                    "uniform_mean_processed_events": float(base.processed_events.mean()),
                    "candidate_mean_square_error": float(np.mean(error_candidate**2)),
                    "uniform_mean_square_error": float(np.mean(error_baseline**2)),
                    "paired_rmse_difference": _rmse(error_candidate) - _rmse(error_baseline),
                    "rmse_ci_low": float(np.quantile(rmse_difference_draws, 0.025)),
                    "rmse_ci_high": float(np.quantile(rmse_difference_draws, 0.975)),
                    "budget_violations": int((~cand.budget_respected).sum()),
                }
            )
    summary = pd.DataFrame(rows)
    summary.to_csv(metrics_path / "development_grid_summary.csv", index=False)

    boundary = summary.loc[summary.scenario.eq("boundary_local_harm")].copy()
    null_errors = summary.loc[summary.scenario.isin(("stationary", "benign_nuisance"))]
    eligible = boundary.loc[
        boundary.adaptive_weight.map(
            lambda w: (
                int(
                    null_errors.loc[
                        null_errors.adaptive_weight.eq(w), "candidate_false_escalations"
                    ].sum()
                )
                <= max(1, int(0.05 * 2 * seeds))
            )
        )
    ].copy()
    if eligible.empty:
        raise RuntimeError("no development-grid point met the predeclared null-alarm guardrail")
    # Detection is primary. If the weak pilot grid ties, choose lower boundary-stream RMSE.
    eligible = eligible.sort_values(
        ["candidate_detections", "candidate_mean_square_error", "candidate_mean_processed_events"],
        ascending=[False, True, False],
    )
    selected_weight = float(eligible.iloc[0].adaptive_weight)
    selected_detection_count = int(eligible.iloc[0].candidate_detections)
    all_zero_power = int(boundary.candidate_detections.max()) == 0

    fig, ax_det = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    ax_rmse = ax_det.twinx()
    ax_det.plot(
        boundary.adaptive_weight,
        boundary.candidate_detections / boundary.seeds,
        marker="o",
        color="tab:blue",
        label="Boundary-harm detection",
    )
    ax_rmse.plot(
        boundary.adaptive_weight,
        np.sqrt(boundary.candidate_mean_square_error),
        marker="s",
        color="tab:orange",
        label="Boundary-harm stream-mean RMSE",
    )
    ax_det.set_xlabel("Adaptive growth weight; remainder uses cost-neutral propensity")
    ax_det.set_ylabel("Detection rate", color="tab:blue")
    ax_rmse.set_ylabel("Stream-mean estimation RMSE", color="tab:orange")
    ax_det.set_xticks(WEIGHTS)
    ax_det.grid(alpha=0.25)
    handles_a, labels_a = ax_det.get_legend_handles_labels()
    handles_b, labels_b = ax_rmse.get_legend_handles_labels()
    ax_det.legend(handles_a + handles_b, labels_a + labels_b, loc="best")
    fig.savefig(figures_path / "cost_neutral_growth_grid.png", dpi=170)
    plt.close(fig)

    lines = [
        "# Development grid: cost-neutral exact mixture-growth acquisition",
        "",
        f"This development-only grid used {seeds} independent paired stream seeds for each scenario, CUDA request `{device}`, and adaptive weights {list(WEIGHTS)}. The uniform baseline and each candidate used the same seed-generated streams, query random uniforms, 20% target dollar budget, `[0.10, 0.80]` propensity bounds, common `q_min` e-process bound, and hard per-stream dollar cap.",
        "",
        "For each candidate, `w=1` is the original exact growth optimizer; `w=0` is the per-event cost-neutral branch `q0=b/k`; intermediate values are convex mixtures. The selection criterion was predeclared: maximize boundary-harm detections among weights with at most 5% observed false escalations pooled over the two population-null scenarios, then break ties by lower boundary-harm stream-mean RMSE and longer processed horizon. These are development results only; any selected weight requires a fresh independent evaluation.",
        "",
        "| Adaptive weight | Scenario | Detection candidate / uniform | Paired detection difference (95% seed bootstrap) | False escalations candidate / uniform | Mean spend candidate / uniform | Mean processed events candidate / uniform | Stream-mean RMSE difference (95% seed bootstrap) |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['adaptive_weight']:.2f}|{row['scenario']}|{row['candidate_detections']}/{seeds} / {row['uniform_detections']}/{seeds}|{row['paired_detection_difference']:+.3f} [{row['detection_ci_low']:+.3f}, {row['detection_ci_high']:+.3f}]|{row['candidate_false_escalations']} / {row['uniform_false_escalations']}|{row['candidate_mean_spend']:.2f} / {row['uniform_mean_spend']:.2f}|{row['candidate_mean_processed_events']:.1f} / {row['uniform_mean_processed_events']:.1f}|{row['paired_rmse_difference']:+.4f} [{row['rmse_ci_low']:+.4f}, {row['rmse_ci_high']:+.4f}]|"
        )
    lines.extend(
        [
            "",
            "## Development selection",
            "",
            f"Selected adaptive weight: **{selected_weight:.2f}** ({selected_detection_count}/{seeds} boundary-harm detections in development).",
            (
                "All five weights detected zero boundary-harm streams. The RMSE/horizon tie-break only nominates a setting for a fresh study; it does not show improved decision-harm detection."
                if all_zero_power
                else "This selection is exploratory and uses only these development streams; it is not a confirmatory performance claim."
            ),
            "",
            f"Reproduce with `uv run python scripts/grid_search_cost_neutral_growth.py --output outputs/cost_neutral_growth_grid_development --seeds {seeds} --seed-offset {seed_offset} --n {n} --d {d} --device {device}`.",
            "",
        ]
    )
    (reports_path / "development_grid.md").write_text("\n".join(lines), encoding="utf-8")
    selected = {
        "adaptive_weight": selected_weight,
        "development_seed_offset": seed_offset,
        "development_seeds_per_scenario": seeds,
        "selection_rule": "maximize boundary-harm detections; tie-break by lower boundary stream-mean RMSE then longer processed horizon, subject to pooled null false escalations <=5%",
        "fresh_evaluation_required": True,
    }
    (reports_path / "selected_weight.json").write_text(
        json.dumps(selected, indent=2), encoding="utf-8"
    )
    manifest = {
        "experiment": "development_grid_cost_neutral_exact_mixture_growth",
        "protocol": {
            "weights": list(WEIGHTS),
            "scenarios": list(SCENARIOS),
            "methods": list(METHODS),
            **common,
        },
        "selected_weight": selected_weight,
        "grid_rows": len(metrics),
        "nested_run_manifests": {},
        "script": "scripts/grid_search_cost_neutral_growth.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (reports_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    manifest_data = json.loads((reports_path / "manifest.json").read_text(encoding="utf-8"))
    manifest_data["nested_run_manifests"] = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in run_manifests.items()
    }
    (reports_path / "manifest.json").write_text(
        json.dumps(manifest_data, indent=2), encoding="utf-8"
    )
    return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/cost_neutral_growth_grid_development")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=28402026)
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
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
