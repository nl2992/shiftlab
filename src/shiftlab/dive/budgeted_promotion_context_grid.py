"""Development grid for fitted context-nested promotion under a hard label budget."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import (
    CONTEXT_ALPHA_ALLOCATIONS,
    BudgetedPromotionConfig,
    _run_seed,
    _summarize,
)
from .experiment import finalize_manifest

PREVALENCES = (0.10, 0.50, 0.90)
SIGNAL_STRENGTHS = (0.0, 0.05, 0.10)
PROXY_ERRORS = (0.0, 0.10, 0.25)
BUDGET_RATES = (0.20, 0.40)
ALPHA_ALLOCATIONS = ("rank", *CONTEXT_ALPHA_ALLOCATIONS)
DEVELOPMENT_SEED_OFFSET = 20_261_025
BOOTSTRAP_SEED = 20_261_026


def _cell_name(prevalence: float, signal: float, error: float) -> str:
    return (
        f"context_p{round(100 * prevalence):02d}_"
        f"delta{round(1000 * signal):03d}_error{round(100 * error):02d}"
    )


def _paired_cell_contrasts(detail: pd.DataFrame, *, draws: int = 10_000) -> pd.DataFrame:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows: list[dict[str, object]] = []
    comparisons = (
        ("rank_context_equal", "rank"),
        ("rank_context_volume", "rank"),
        ("rank_context_volume", "rank_context_equal"),
    )
    for (scenario, budget_rate), group in detail.groupby(["scenario", "budget_rate"], sort=False):
        for treatment_name, comparator_name in comparisons:
            treatment = group[group.alpha_allocation.eq(treatment_name)].sort_values("seed")
            comparator = group[group.alpha_allocation.eq(comparator_name)].sort_values("seed")
            if (
                treatment.empty
                or len(treatment) != len(comparator)
                or not np.array_equal(treatment.seed.to_numpy(), comparator.seed.to_numpy())
            ):
                raise ValueError("context allocation contrasts require matched seed sets")
            metrics = (
                "expected_postpromotion_net_gain",
                "promoted",
                "harmful_postpromotion_promotion",
            )
            indices = rng.integers(0, len(treatment), size=(draws, len(treatment)))
            for metric in metrics:
                differences = treatment[metric].to_numpy(dtype=float) - comparator[metric].to_numpy(
                    dtype=float
                )
                bootstrap = differences[indices].mean(axis=1)
                rows.append(
                    {
                        "scenario": scenario,
                        "budget_rate": budget_rate,
                        "contrast": f"{treatment_name}_minus_{comparator_name}",
                        "metric": metric,
                        "n_seed_pairs": len(differences),
                        "mean_paired_difference": float(differences.mean()),
                        "ci_level": 0.95,
                        "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                        "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                        "bootstrap_draws": draws,
                        "bootstrap_seed": BOOTSTRAP_SEED,
                    }
                )
    return pd.DataFrame(rows)


def _macro_signal_contrasts(detail: pd.DataFrame, *, draws: int = 10_000) -> pd.DataFrame:
    """Equal-weight the 18 positive-signal cells and bootstrap matched seed blocks."""
    rng = np.random.default_rng(BOOTSTRAP_SEED + 1)
    alternatives = detail[detail.context_signal_strength.gt(0) & detail.budget_rate.eq(0.40)]
    cells = list(alternatives.scenario.drop_duplicates())
    expected_cells = len(PREVALENCES) * len(PROXY_ERRORS) * (len(SIGNAL_STRENGTHS) - 1)
    if len(cells) != expected_cells:
        raise ValueError(f"expected {expected_cells} positive-signal cells, found {len(cells)}")
    streams: dict[str, list[np.ndarray]] = {
        "rank_context_volume_minus_rank": [],
        "rank_context_volume_minus_rank_context_equal": [],
    }
    for scenario in cells:
        group = alternatives[alternatives.scenario.eq(scenario)]
        by_method = {
            name: group[group.alpha_allocation.eq(name)].sort_values("seed")
            for name in ALPHA_ALLOCATIONS
        }
        for name, frame in by_method.items():
            if frame.empty or not np.array_equal(
                frame.seed.to_numpy(), by_method["rank"].seed.to_numpy()
            ):
                raise ValueError(f"unmatched seeds in macro cell {scenario} for {name}")
        metric = "expected_postpromotion_net_gain"
        streams["rank_context_volume_minus_rank"].append(
            by_method["rank_context_volume"][metric].to_numpy(dtype=float)
            - by_method["rank"][metric].to_numpy(dtype=float)
        )
        streams["rank_context_volume_minus_rank_context_equal"].append(
            by_method["rank_context_volume"][metric].to_numpy(dtype=float)
            - by_method["rank_context_equal"][metric].to_numpy(dtype=float)
        )
    rows = []
    for contrast, by_cell in streams.items():
        matrix = np.stack(by_cell)
        sample_ids = rng.integers(0, matrix.shape[1], size=(draws, matrix.shape[1]))
        bootstrap = np.stack([matrix[:, sample_ids[index]].mean() for index in range(draws)])
        rows.append(
            {
                "budget_rate": 0.40,
                "contrast": contrast,
                "metric": "expected_postpromotion_net_gain",
                "n_settings": int(matrix.shape[0]),
                "n_seed_blocks": int(matrix.shape[1]),
                "mean_paired_difference": float(matrix.mean()),
                "simultaneous_ci_level": 0.975,
                "bootstrap_ci_low": float(np.quantile(bootstrap, 0.0125)),
                "bootstrap_ci_high": float(np.quantile(bootstrap, 0.9875)),
                "practical_margin": 1.0,
                "settings": json.dumps(cells),
                "bootstrap_draws": draws,
                "bootstrap_seed": BOOTSTRAP_SEED + 1,
            }
        )
    return pd.DataFrame(rows)


def run_context_grid(
    *,
    output: Path,
    seeds: int = 30,
    seed_offset: int = DEVELOPMENT_SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    reuse_detail: bool = False,
) -> Path:
    if seeds < 2 or n < 1000 or d < 3:
        raise ValueError("development requires seeds >=2, n >=1000, and d >=3")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metrics_dir / "context_budgeted_promotion_streams.parquet"
    summary_path = metrics_dir / "context_budgeted_promotion_summary.parquet"
    contrasts_path = metrics_dir / "context_budgeted_promotion_cell_contrasts.parquet"
    macro_path = metrics_dir / "context_budgeted_promotion_macro_contrasts.parquet"
    if any(path.exists() for path in (detail_path, summary_path)) and not reuse_detail:
        raise FileExistsError(f"refusing to overwrite existing development run: {output}")

    if reuse_detail:
        if not detail_path.exists():
            raise FileNotFoundError(f"missing seed-level metrics: {detail_path}")
        detail = pd.read_parquet(detail_path)
        expected_seeds = set(range(seed_offset, seed_offset + seeds))
        if (
            set(detail.seed.unique()) != expected_seeds
            or set(detail.alpha_allocation.unique()) != set(ALPHA_ALLOCATIONS)
            or set(detail.budget_rate.unique()) != set(BUDGET_RATES)
            or set(detail.scenario.unique())
            != {
                _cell_name(p, s, e)
                for p in PREVALENCES
                for s in SIGNAL_STRENGTHS
                for e in PROXY_ERRORS
            }
        ):
            raise ValueError("saved development metrics do not match the frozen grid")
    else:
        scenario = SimpleNamespace(
            name="candidate_context_heterogeneity",
            fn_cost=5.0,
            fp_cost=1.0,
            harmful_adaptation=False,
        )
        records: list[dict[str, object]] = []
        for prevalence in PREVALENCES:
            for signal in SIGNAL_STRENGTHS:
                for proxy_error in PROXY_ERRORS:
                    cell_name = _cell_name(prevalence, signal, proxy_error)
                    print(
                        f"context-grid cell={cell_name} seeds={seeds} device={resolved_device}",
                        flush=True,
                    )
                    config = BudgetedPromotionConfig(
                        n=n,
                        d=d,
                        seeds=1,
                        seed_offset=seed_offset,
                        budget_rates=BUDGET_RATES,
                        query_policies=("uniform",),
                        alpha_allocations=ALPHA_ALLOCATIONS,
                        estimators=("direct_ipw",),
                        monitoring_rules=("fixed_mixture",),
                        bound_mode="global",
                        context_feature_index=d - 1,
                        context_threshold=0.0,
                        context_target_prevalence=prevalence,
                        context_signal_strength=signal,
                        context_proxy_error=proxy_error,
                        scenario_subset=("candidate_context_heterogeneity",),
                        create_plot=False,
                        device=resolved_device,
                    )
                    config.validate()
                    for replicate in range(seeds):
                        seed = seed_offset + replicate
                        seed_rows = _run_seed(
                            scenario=scenario,
                            seed=seed,
                            config=config,
                            device=resolved_device,
                        )
                        for row in seed_rows:
                            row["scenario"] = cell_name
                            records.append(row)
        detail = pd.DataFrame(records)

    summary = _summarize(detail)
    parameters = (
        detail[
            [
                "scenario",
                "context_target_prevalence",
                "context_signal_strength",
                "context_proxy_error",
                "context_observed_prevalence",
            ]
        ]
        .groupby("scenario", as_index=False)
        .mean(numeric_only=True)
    )
    summary = summary.merge(parameters, on="scenario", validate="many_to_one")
    cell_contrasts = _paired_cell_contrasts(detail)
    macro_contrasts = _macro_signal_contrasts(detail)
    detail.to_parquet(detail_path, index=False)
    summary.to_parquet(summary_path, index=False)
    cell_contrasts.to_parquet(contrasts_path, index=False)
    macro_contrasts.to_parquet(macro_path, index=False)

    macro = macro_contrasts.set_index("contrast")
    summary_macro = (
        detail[detail.budget_rate.eq(0.40)]
        .groupby(["context_signal_strength", "alpha_allocation"], as_index=False)
        .agg(
            promotion_rate=("promoted", "mean"),
            mean_expected_net_gain=("expected_postpromotion_net_gain", "mean"),
            future_harm_rate=("harmful_postpromotion_promotion", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_cap=("label_budget", "mean"),
            mean_processed_fraction=("monitor_fraction_processed", "mean"),
        )
    )
    report_lines = [
        "# Fitted context-nested promotion development grid",
        "",
        f"This frozen CUDA grid used {seeds} matched seeds in each of 27 cells (`n={n}`, `d={d}`), with uniform direct-IPW monitoring and common 20%/40% hard label caps. It compares pooled candidate-rank alpha with equal-context and validation-volume nested allocations. The exact DGP and analysis were frozen in [the protocol](../../../docs/contextual_budgeted_promotion_grid_protocol.md).",
        "",
        "The monitor/evaluator assumptions are unchanged from the fitted-controller benchmark. The context signal is applied from the monitor boundary; latent group membership is evaluator-only, and the learner's context rule uses the independently misclassified proxy feature. No figure was generated.",
        "",
        "## Primary macro contrasts",
        "",
        "The primary summary equally averages the 18 positive-signal prevalence/error cells at the 40% cap. The two primary contrasts use 97.5% intervals for simultaneous coverage. The +1 cumulative utility margin is the existing development gate; this exploratory grid does not select a confirmation winner.",
        "",
        "| Contrast | Mean paired future net gain | 97.5% bootstrap interval | Settings |",
        "|---|---:|---:|---:|",
    ]
    for contrast in (
        "rank_context_volume_minus_rank",
        "rank_context_volume_minus_rank_context_equal",
    ):
        row = macro.loc[contrast]
        report_lines.append(
            f"| {contrast} | {row.mean_paired_difference:.3f} | [{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}] | {int(row.n_settings)} |"
        )
    report_lines.extend(
        [
            "",
            "## 40% cap results by signal strength",
            "",
            "| Signal delta | Allocation | Promotion rate | Mean future net gain | Future harmful rate | Mean labels / cap | Processed monitor fraction |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary_macro.itertuples(index=False):
        report_lines.append(
            f"| {row.context_signal_strength:.2f} | {row.alpha_allocation} | {row.promotion_rate:.3f} | {row.mean_expected_net_gain:.3f} | {row.future_harm_rate:.3f} | {row.mean_labels:.1f} / {row.mean_cap:.0f} | {row.mean_processed_fraction:.3f} |"
        )
    volume_rank = cell_contrasts[
        cell_contrasts.budget_rate.eq(0.40)
        & cell_contrasts.metric.eq("expected_postpromotion_net_gain")
        & cell_contrasts.contrast.eq("rank_context_volume_minus_rank")
    ]
    positive_signal_scenarios = set(detail.loc[detail.context_signal_strength.gt(0), "scenario"])
    volume_rank = volume_rank[volume_rank.scenario.isin(positive_signal_scenarios)]
    positive_cells = int(volume_rank.mean_paired_difference.gt(0).sum())
    selected_cell = "context_p90_delta100_error00"
    selected_contrast = volume_rank[volume_rank.scenario.eq(selected_cell)].iloc[0]
    selected_methods = (
        detail[detail.scenario.eq(selected_cell) & detail.budget_rate.eq(0.40)]
        .groupby("alpha_allocation")
        .agg(
            promotion_rate=("promoted", "mean"),
            mean_gain=("expected_postpromotion_net_gain", "mean"),
        )
    )
    report_lines.extend(
        [
            "",
            "## Cellwise diagnostic",
            "",
            f"Nested volume exceeded pooled-rank mean net gain in {positive_cells}/18 positive-signal cells at the 40% cap. The largest registered-cell contrast was `{selected_cell}`: nested volume minus rank-only was {selected_contrast.mean_paired_difference:.2f} [{selected_contrast.bootstrap_ci_low:.2f}, {selected_contrast.bootstrap_ci_high:.2f}] cumulative units, with promotion rates {selected_methods.loc['rank_context_volume', 'promotion_rate']:.3f} versus {selected_methods.loc['rank', 'promotion_rate']:.3f}. This cell was identified after examining the development grid; its interval is unadjusted and is not confirmation evidence. The two-way macro comparison remains the registered primary analysis.",
            "",
            "The complete parameter-cell summaries, paired cell contrasts, and seed-level metrics are stored in Parquet. Cellwise intervals are descriptive and unadjusted across the factorial; the macro contrast averages only the registered positive-signal settings. The zero-signal cells are nondegenerate pointwise net-benefit nulls because both actions have equal expected cost before switching cost.",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-budgeted-context-grid develop --seeds {seeds} --seed-offset {seed_offset} --n {n} --d {d} --device {resolved_device} --output {output.as_posix()}`",
            "",
            "This is a development screen. Any method retained for a performance claim needs a new independent null calibration and a disjoint confirmation run. No novelty claim follows from weighted Bonferroni composition.",
        ]
    )
    report_path = reports_dir / "context_budgeted_promotion_grid.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "fitted_context_nested_alpha_development_grid",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": {
            "seeds": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "d": d,
            "device": resolved_device,
            "prevalences": PREVALENCES,
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "budget_rates": BUDGET_RATES,
            "alpha_allocations": ALPHA_ALLOCATIONS,
            "query_policy": "uniform",
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "context_feature_index": d - 1,
            "alpha": 0.05,
            "switching_cost": 0.05,
        },
        "environment": environment(),
        "inference": {
            "cellwise_bootstrap_draws": 10_000,
            "macro_bootstrap_draws": 10_000,
            "macro_positive_signal_cells": 18,
            "macro_interval_level_per_contrast": 0.975,
            "practical_margin": 1.0,
            "development_only": True,
        },
        "artifacts": [
            "metrics/context_budgeted_promotion_streams.parquet",
            "metrics/context_budgeted_promotion_summary.parquet",
            "metrics/context_budgeted_promotion_cell_contrasts.parquet",
            "metrics/context_budgeted_promotion_macro_contrasts.parquet",
            "reports/context_budgeted_promotion_grid.md",
        ],
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    develop = subparsers.add_parser("develop", help="run the frozen development factorial")
    develop.add_argument(
        "--output", type=Path, default=Path("outputs/context_budgeted_promotion_grid_30")
    )
    develop.add_argument("--seeds", type=int, default=30)
    develop.add_argument("--seed-offset", type=int, default=DEVELOPMENT_SEED_OFFSET)
    develop.add_argument("--n", type=int, default=3200)
    develop.add_argument("--d", type=int, default=16)
    develop.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    develop.add_argument("--reuse-detail", action="store_true")
    args = parser.parse_args(argv)
    print(
        run_context_grid(
            output=args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            reuse_detail=args.reuse_detail,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
