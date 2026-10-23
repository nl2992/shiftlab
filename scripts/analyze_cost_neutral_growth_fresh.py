"""Create paired summaries for the fresh cost-neutral growth evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from shiftlab.dive.experiment import finalize_manifest

METHOD_ORDER = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
    "exact_mixture_growth_proxy",
)


def _bootstrap_mean_interval(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    indices = rng.integers(0, len(values), size=(50_000, len(values)))
    draws = values[indices].mean(axis=1)
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return float(lower), float(upper)


def analyze(output: Path) -> Path:
    metrics_path = output / "metrics" / "hard_budget_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    if not metrics.budget_respected.all():
        raise ValueError("fresh evaluation contains a hard-budget violation")
    if set(metrics.method) != set(METHOD_ORDER):
        raise ValueError("fresh evaluation is missing an expected acquisition method")

    seed = int(metrics.seed.min())
    baseline = metrics.loc[metrics.method.eq("uniform_proxy")]
    summary_rows: list[dict[str, object]] = []
    report_lines = [
        "# Fresh evaluation of cost-neutral exact mixture-growth acquisition",
        "",
        "This independent 60-seed-per-scenario evaluation follows the registered development grid. The selected development weight was `w=0`, so the exact-growth method reduces to the predictable cost-neutral propensity `q0(x)=b/k(x)`. Metrics are synthetic and evaluator truth is not visible to the query policy. All methods use the same per-stream budget, stream seed, query random uniforms, and fixed e-process bound.",
        "",
        "The paired intervals below resample stream seeds. They are descriptive comparisons for this preselected candidate and are not adjusted for the development search. Detection is shown only for the boundary-local-harm alternative; every one of its 60 onsets was reached by every method. Null false-escalation rates are reported separately.",
        "",
        "|Scenario|Method|Detection / harmful streams|Paired detection difference vs uniform (95% bootstrap CI)|False escalations / null streams|RMSE difference vs uniform (95% bootstrap CI)|Spend difference|Label difference|Monitor fraction difference|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for scenario in sorted(metrics.scenario.unique()):
        base = baseline.loc[baseline.scenario.eq(scenario)].set_index("seed").sort_index()
        for method in METHOD_ORDER:
            candidate = (
                metrics.loc[metrics.scenario.eq(scenario) & metrics.method.eq(method)]
                .set_index("seed")
                .sort_index()
            )
            if not candidate.index.equals(base.index):
                raise ValueError(f"{method} is not seed-matched to uniform in {scenario}")

            detection_delta = (
                candidate.single_e_detected.astype(float).to_numpy()
                - base.single_e_detected.astype(float).to_numpy()
            )
            # Bootstrap RMSE itself, not squared error, to match the reported estimand.
            rng = np.random.default_rng(seed + len(scenario) + METHOD_ORDER.index(method) * 101)
            indices = rng.integers(0, len(candidate), size=(50_000, len(candidate)))
            candidate_error = candidate.stream_mean_estimation_error.to_numpy(dtype=float)
            baseline_error = base.stream_mean_estimation_error.to_numpy(dtype=float)
            rmse_draws = np.sqrt(np.mean(candidate_error[indices] ** 2, axis=1)) - np.sqrt(
                np.mean(baseline_error[indices] ** 2, axis=1)
            )
            rmse_ci = np.quantile(rmse_draws, [0.025, 0.975])
            detection_rng = np.random.default_rng(seed + len(scenario) + 7919)
            detection_ci = _bootstrap_mean_interval(detection_delta, detection_rng)

            harmful = bool(candidate.material_harm.any())
            detected = int(candidate.loc[candidate.material_harm, "single_e_detected"].sum())
            harmful_n = int(candidate.material_harm.sum())
            null_streams = int(candidate.population_null_control.sum())
            false_escalations = int(candidate.single_e_false_escalation.sum())
            row: dict[str, object] = {
                "scenario": scenario,
                "method": method,
                "streams": len(candidate),
                "harmful_streams": harmful_n,
                "detections": detected if harmful else None,
                "detection_rate": detected / harmful_n if harmful_n else None,
                "detection_difference_vs_uniform": float(detection_delta.mean())
                if harmful
                else None,
                "detection_ci_low": detection_ci[0] if harmful else None,
                "detection_ci_high": detection_ci[1] if harmful else None,
                "false_escalations": false_escalations,
                "null_streams": null_streams,
                "false_escalation_rate": false_escalations / null_streams if null_streams else None,
                "rmse": float(np.sqrt(np.mean(candidate_error**2))),
                "rmse_difference_vs_uniform": float(
                    np.sqrt(np.mean(candidate_error**2)) - np.sqrt(np.mean(baseline_error**2))
                ),
                "rmse_ci_low": float(rmse_ci[0]),
                "rmse_ci_high": float(rmse_ci[1]),
                "spend_difference_vs_uniform": float(
                    (candidate.realized_label_spend - base.realized_label_spend).mean()
                ),
                "labels_difference_vs_uniform": float(
                    (candidate.labels_queried - base.labels_queried).mean()
                ),
                "monitor_fraction_difference_vs_uniform": float(
                    (candidate.monitor_fraction_processed - base.monitor_fraction_processed).mean()
                ),
                "harm_reached_streams": int(candidate.harm_reached_before_budget_stop.sum()),
                "budget_violations": int((~candidate.budget_respected).sum()),
            }
            summary_rows.append(row)

            detection_text = f"{detected}/{harmful_n}" if harmful else "n/a"
            detection_diff_text = (
                f"{detection_delta.mean():+.3f} [{detection_ci[0]:+.3f}, {detection_ci[1]:+.3f}]"
                if harmful
                else "n/a"
            )
            false_text = f"{false_escalations}/{null_streams}" if null_streams else "n/a"
            report_lines.append(
                f"|{scenario}|{method}|{detection_text}|{detection_diff_text}|{false_text}|"
                f"{row['rmse_difference_vs_uniform']:+.4f} [{rmse_ci[0]:+.4f}, {rmse_ci[1]:+.4f}]|"
                f"{row['spend_difference_vs_uniform']:+.2f}|"
                f"{row['labels_difference_vs_uniform']:+.1f}|"
                f"{row['monitor_fraction_difference_vs_uniform']:+.3f}|"
            )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output / "metrics" / "cost_neutral_growth_fresh_paired.csv", index=False)
    boundary = metrics.loc[metrics.scenario.eq("boundary_local_harm")].pivot(
        index="seed", columns="method", values="single_e_detected"
    )
    exact_wins = int((boundary.exact_mixture_growth_proxy & ~boundary.uniform_proxy).sum())
    exact_losses = int((~boundary.exact_mixture_growth_proxy & boundary.uniform_proxy).sum())
    mcnemar_p = float(binomtest(exact_wins, exact_wins + exact_losses, p=0.5).pvalue)
    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The development selection had 3/30 detections for `w=0`, compared with 2/30 for uniform; all other candidate weights had 0/30. In this independent evaluation, `w=0` detected {int(boundary.exact_mixture_growth_proxy.sum())}/60 versus {int(boundary.uniform_proxy.sum())}/60 for uniform. {exact_wins} paired streams favored `w=0` and {exact_losses} favored uniform; the exact two-sided McNemar/binomial test conditional on discordant pairs gives p={mcnemar_p:.3f}. The paired bootstrap summarizes the same small number of discordances, and this is one synthetic boundary-local alternative. It does not establish general detection superiority.",
            "",
            "The selected branch has a positive stream-mean RMSE difference versus uniform in this evaluation. Therefore the result is a detection-versus-estimation tradeoff, not an overall improvement. The cost-neutral derivation controls conditional expected label spend per event under the specified tariff support; the implemented hard cap controls realized spend. Neither property implies optimality across other shift mechanisms, budgets, costs, or policy losses.",
            "",
            "Reproduce the acquisition run with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28502026 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --exact-growth-adaptive-weight 0.0 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy --device cuda --output outputs/cost_neutral_growth_grid_fresh_60`, then run `uv run python scripts/analyze_cost_neutral_growth_fresh.py --output outputs/cost_neutral_growth_grid_fresh_60`.",
            "",
        ]
    )
    report_path = output / "reports" / "cost_neutral_growth_fresh_analysis.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    finalize_manifest(output)
    manifest_path = output / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["paired_analysis"] = {
        "script": "scripts/analyze_cost_neutral_growth_fresh.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bootstrap_resamples": 50_000,
        "seed": seed,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/cost_neutral_growth_grid_fresh_60")
    )
    args = parser.parse_args()
    print(analyze(args.output))


if __name__ == "__main__":
    main()
