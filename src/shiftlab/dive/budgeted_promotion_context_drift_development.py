"""Explore target-scout utility under positive-signal context-prevalence drift."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import BudgetedPromotionConfig, _run_seed
from .experiment import finalize_manifest

PREVALENCE_PAIRS = ((0.10, 0.90), (0.50, 0.50), (0.90, 0.10))
SIGNAL_STRENGTHS = (0.05, 0.10)
PROXY_ERRORS = (0.0, 0.25)
BUDGET_RATES = (0.20, 0.40)
SWITCHING_COST = 0.05
METHODS = ("rank", "rank_context_volume", "scout_context_policy")
SEED_OFFSET = 20_268_000
MIN_SEEDS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_268_060
FAMILY_CELLS = len(PREVALENCE_PAIRS) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS) * len(BUDGET_RATES)


def _cell_name(
    initial_prevalence: float, final_prevalence: float, signal: float, proxy_error: float
) -> str:
    return (
        f"drift_p{round(100 * initial_prevalence):02d}_to_{round(100 * final_prevalence):02d}_"
        f"delta{round(1000 * signal):03d}_error{round(100 * proxy_error):02d}"
    )


def _summarize_contrasts(detail: pd.DataFrame, *, draws: int) -> pd.DataFrame:
    cells = sorted(
        detail[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    seeds = np.sort(detail["seed"].unique())
    if len(cells) != FAMILY_CELLS or len(seeds) < 2:
        raise ValueError("development result does not contain the frozen cell and seed family")
    contrast_specs = (
        ("scout_minus_rank", "rank"),
        ("scout_minus_nested_volume", "rank_context_volume"),
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    output: list[dict[str, object]] = []
    for contrast, comparator in contrast_specs:
        matrix = np.empty((len(cells), len(seeds)), dtype=float)
        for cell_index, (scenario_name, budget_rate) in enumerate(cells):
            cell = detail.loc[
                detail["scenario"].eq(scenario_name) & detail["budget_rate"].eq(budget_rate)
            ]
            scout = cell.loc[cell["alpha_allocation"].eq("scout_context_policy")].sort_values(
                "seed"
            )
            baseline = cell.loc[cell["alpha_allocation"].eq(comparator)].sort_values("seed")
            if (
                len(scout) != len(seeds)
                or len(baseline) != len(seeds)
                or not np.array_equal(scout["seed"].to_numpy(), seeds)
                or not np.array_equal(baseline["seed"].to_numpy(), seeds)
            ):
                raise ValueError(
                    f"unmatched or incomplete seed block in {scenario_name}, cap={budget_rate}"
                )
            matrix[cell_index] = scout["expected_postpromotion_net_gain"].to_numpy(
                dtype=float
            ) - baseline["expected_postpromotion_net_gain"].to_numpy(dtype=float)
        bootstrap = np.empty(draws, dtype=float)
        for start in range(0, draws, 100):
            stop = min(draws, start + 100)
            indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            bootstrap[start:stop] = np.take(matrix, indices, axis=1).mean(axis=(0, 2))
        output.append(
            {
                "contrast": contrast,
                "metric": "expected_postpromotion_net_gain",
                "n_cells": len(cells),
                "n_matched_seeds": len(seeds),
                "mean_paired_difference": float(matrix.mean()),
                "descriptive_bootstrap_ci_level": 0.95,
                "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                "bootstrap_draws": draws,
                "bootstrap_seed": BOOTSTRAP_SEED,
            }
        )
    return pd.DataFrame(output)


def run_development(
    *,
    output: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    protocol: Path,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> Path:
    if seeds < 2 or n < 1000 or d < 3 or bootstrap_draws < 100:
        raise ValueError(
            "development requires seeds >=2, n >=1000, d >=3, and >=100 bootstrap draws"
        )
    if seed_offset < SEED_OFFSET:
        raise ValueError("development seeds must not overlap earlier scout blocks")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen development protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite development output: {output}")
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    records: list[dict[str, object]] = []
    for initial_prevalence, final_prevalence in PREVALENCE_PAIRS:
        for signal in SIGNAL_STRENGTHS:
            for proxy_error in PROXY_ERRORS:
                cell_name = _cell_name(initial_prevalence, final_prevalence, signal, proxy_error)
                print(
                    f"scout-drift-development cell={cell_name} seeds={seeds} "
                    f"device={resolved_device}",
                    flush=True,
                )
                config = BudgetedPromotionConfig(
                    n=n,
                    d=d,
                    seeds=1,
                    seed_offset=seed_offset,
                    switching_cost=SWITCHING_COST,
                    budget_rates=BUDGET_RATES,
                    query_policies=("uniform",),
                    alpha_allocations=("rank", "rank_context_volume"),
                    estimators=("direct_ipw",),
                    monitoring_rules=("fixed_mixture",),
                    bound_mode="global",
                    context_feature_index=d - 1,
                    context_threshold=0.0,
                    context_target_prevalence=initial_prevalence,
                    context_signal_strength=signal,
                    context_proxy_error=proxy_error,
                    context_certification_prevalence=final_prevalence,
                    include_scout_context_policy=True,
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
                    selected = [row for row in seed_rows if row["alpha_allocation"] in METHODS]
                    if len(selected) != len(METHODS) * len(BUDGET_RATES):
                        raise RuntimeError("stream is missing a method or budget result")
                    for row in selected:
                        row["scenario"] = cell_name
                        row["context_initial_prevalence"] = initial_prevalence
                        row["context_certification_prevalence"] = final_prevalence
                        row["context_signal_strength"] = signal
                        row["context_proxy_error"] = proxy_error
                        row["seed"] = seed
                        records.append(row)

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * FAMILY_CELLS * len(METHODS)
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} development rows; received {len(detail)}")
    if detail.duplicated(["scenario", "budget_rate", "seed", "alpha_allocation"]).any():
        raise RuntimeError("duplicate cell/seed/method records in development output")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("all methods require positive query support")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("development exceeded a realized hard label cap")

    contrasts = _summarize_contrasts(detail, draws=bootstrap_draws)
    summary = detail.groupby(["scenario", "budget_rate", "alpha_allocation"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        mean_expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        mean_labels_queried=("labels_queried", "mean"),
        mean_certification_fraction=("certification_fraction_processed", "mean"),
    )
    detail.to_parquet(metrics_dir / "scout_context_drift_development_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "scout_context_drift_development_cells.parquet", index=False)
    contrasts.to_parquet(
        metrics_dir / "scout_context_drift_development_contrasts.parquet", index=False
    )

    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "scout_context_drift_development.md"
    report = [
        "# Target-scout positive-signal development under abrupt context drift",
        "",
        (
            f"Status: **exploratory development**. Device: {resolved_device}; seeds per cell: {seeds}; "
            f"seed block: {seed_offset}–{seed_offset + seeds - 1}."
        ),
        "",
        (
            "The grid has 24 cells and three methods per matched stream, with both 20% and 40% hard "
            "caps. The target prevalence changes at the scout/certification boundary except in the "
            "stable 50% control. Primary contrasts equally weight the 24 settings and resample matched "
            "seed IDs as clusters."
        ),
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        (
            "These intervals are descriptive development summaries, not confirmation tests. Cellwise "
            "results and the complete stream-level evaluator metrics are saved in Parquet. No method "
            "is selected for publication from this run alone; any follow-up requires a frozen protocol "
            "and disjoint seed block. The separate zero-signal calibration, not this positive-signal "
            "grid, supplies false-promotion evidence."
        ),
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {protocol_hash}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_positive_signal_context_drift_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "exploratory_development",
        "protocol": {"path": protocol.as_posix(), "sha256": protocol_hash},
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "prevalence_pairs": PREVALENCE_PAIRS,
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "switching_cost": SWITCHING_COST,
            "budget_rates": BUDGET_RATES,
            "methods": METHODS,
            "query_policy": "uniform",
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "alpha": 0.05,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "inference": {
            "primary_contrasts": contrasts.to_dict(orient="records"),
            "all_label_caps_respected": True,
            "all_propensities_positive": True,
            "confirmatory": False,
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/scout_context_drift_development_streams.parquet",
            "metrics/scout_context_drift_development_cells.parquet",
            "metrics/scout_context_drift_development_contrasts.parquet",
            "reports/scout_context_drift_development.md",
        ],
        "environment": environment(),
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    print(report_path, flush=True)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/scout_context_policy_positive_drift_development_60"),
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_positive_drift_development_protocol.md"),
    )
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    args = parser.parse_args(argv)
    print(
        run_development(
            output=args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            protocol=args.protocol,
            bootstrap_draws=args.bootstrap_draws,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
