"""Confirm target-scout utility under abrupt context-prevalence drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import BudgetedPromotionConfig, _run_seed
from .budgeted_promotion_context_drift_development import (
    BUDGET_RATES,
    EVENTWISE_SCOUT_METHOD,
    PREVALENCE_PAIRS,
    PROXY_ERRORS,
    SIGNAL_STRENGTHS,
    SWITCHING_COST,
    _cell_name,
)
from .experiment import finalize_manifest

METHODS = (
    EVENTWISE_SCOUT_METHOD,
    "scout_context_policy",
    "rank",
    "rank_context_volume",
)
COMPARATORS = (
    ("eventwise_minus_rank", "rank", True),
    ("eventwise_minus_nested_volume", "rank_context_volume", True),
    ("eventwise_minus_minimum_bound", "scout_context_policy", False),
)
SEED_OFFSET = 20_270_000
MIN_SEEDS = 600
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_270_600
FAMILY_CELLS = len(PREVALENCE_PAIRS) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS) * len(BUDGET_RATES)


def _run_confirmation_seed(
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    initial_prevalence: float,
    final_prevalence: float,
    signal: float,
    proxy_error: float,
) -> list[dict[str, object]]:
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    rows = _run_seed(
        scenario=scenario,
        seed=seed,
        config=config,
        device=device,
        scout_bound_modes=("minimum_propensity", "eventwise_propensity"),
    )
    selected = [row for row in rows if row["alpha_allocation"] in METHODS]
    if len(selected) != len(METHODS) * len(BUDGET_RATES):
        raise RuntimeError("confirmation stream is missing a method or budget result")
    cell = _cell_name(initial_prevalence, final_prevalence, signal, proxy_error)
    for row in selected:
        row["scenario"] = cell
        row["context_initial_prevalence"] = initial_prevalence
        row["context_certification_prevalence"] = final_prevalence
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["seed"] = seed
    return selected


def _run_profile_seeds(
    *,
    seeds: int,
    seed_offset: int,
    config: BudgetedPromotionConfig,
    device: str,
    initial_prevalence: float,
    final_prevalence: float,
    signal: float,
    proxy_error: float,
    executor: ProcessPoolExecutor | None,
) -> list[list[dict[str, object]]]:
    results: list[list[dict[str, object]] | None] = [None] * seeds
    if executor is None:
        for replicate in range(seeds):
            results[replicate] = _run_confirmation_seed(
                seed_offset + replicate,
                config,
                device,
                initial_prevalence,
                final_prevalence,
                signal,
                proxy_error,
            )
    else:
        futures = {
            executor.submit(
                _run_confirmation_seed,
                seed_offset + replicate,
                config,
                device,
                initial_prevalence,
                final_prevalence,
                signal,
                proxy_error,
            ): replicate
            for replicate in range(seeds)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if completed % 100 == 0 or completed == seeds:
                print(
                    f"scout-drift-confirmation progress={completed}/{seeds} "
                    f"cell={_cell_name(initial_prevalence, final_prevalence, signal, proxy_error)}",
                    flush=True,
                )
    if any(result is None for result in results):
        raise RuntimeError("confirmation profile is missing one or more seed results")
    return [result for result in results if result is not None]


def _paired_contrasts(detail: pd.DataFrame, *, draws: int, seed: int) -> pd.DataFrame:
    cells = sorted(
        detail[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    seeds = np.sort(detail["seed"].unique())
    if len(cells) != FAMILY_CELLS or len(seeds) < 2:
        raise ValueError("confirmation output does not contain the frozen cell and seed family")
    rows: list[dict[str, object]] = []
    for contrast_index, (name, comparator, primary) in enumerate(COMPARATORS):
        rng = np.random.default_rng(seed + contrast_index)
        difference = np.empty((len(cells), len(seeds)), dtype=float)
        for cell_index, (scenario, budget_rate) in enumerate(cells):
            cell = detail.loc[
                detail["scenario"].eq(scenario) & detail["budget_rate"].eq(budget_rate)
            ]
            candidate = cell.loc[cell["alpha_allocation"].eq(EVENTWISE_SCOUT_METHOD)].sort_values(
                "seed"
            )
            baseline = cell.loc[cell["alpha_allocation"].eq(comparator)].sort_values("seed")
            if (
                len(candidate) != len(seeds)
                or len(baseline) != len(seeds)
                or not np.array_equal(candidate["seed"].to_numpy(), seeds)
                or not np.array_equal(baseline["seed"].to_numpy(), seeds)
            ):
                raise ValueError(f"unmatched seed rows in {scenario}, cap={budget_rate}")
            difference[cell_index] = candidate["expected_postpromotion_net_gain"].to_numpy(
                dtype=float
            ) - baseline["expected_postpromotion_net_gain"].to_numpy(dtype=float)

        bootstrap = np.empty(draws, dtype=float)
        for start in range(0, draws, 100):
            stop = min(draws, start + 100)
            indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            bootstrap[start:stop] = np.take(difference, indices, axis=1).mean(axis=(0, 2))
        rows.append(
            {
                "contrast": name,
                "metric": "expected_postpromotion_net_gain",
                "n_cells": len(cells),
                "n_matched_seed_clusters": len(seeds),
                "mean_paired_difference": float(difference.mean()),
                "percentile_bootstrap_ci_level": 0.95,
                "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                "familywise_one_sided_lower": float(np.quantile(bootstrap, 0.025))
                if primary
                else None,
                "familywise_alpha_allocation": 0.025 if primary else None,
                "primary_comparison": primary,
                "bootstrap_draws": draws,
                "bootstrap_seed": seed + contrast_index,
            }
        )
    return pd.DataFrame(rows)


def run_confirmation(
    *,
    output: Path,
    protocol: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    workers: int = 1,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> Path:
    if seeds < 2 or seed_offset <= 20_269_999 or n < 1000 or d < 3:
        raise ValueError("confirmation requires >=2 fresh seeds, n>=1000, and d>=3")
    if workers < 1 or bootstrap_draws < 100:
        raise ValueError("workers must be positive and bootstrap draws must be >=100")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen confirmation protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite confirmation output: {output}")
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    records: list[dict[str, object]] = []
    thread_variables = (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    )
    previous_thread_limits = {key: os.environ.get(key) for key in thread_variables}
    if workers > 1:
        os.environ.update({key: "1" for key in thread_variables})
    pool_context = ProcessPoolExecutor(max_workers=workers) if workers > 1 else nullcontext(None)
    try:
        with pool_context as executor:
            for initial_prevalence, final_prevalence in PREVALENCE_PAIRS:
                for signal in SIGNAL_STRENGTHS:
                    for proxy_error in PROXY_ERRORS:
                        cell_name = _cell_name(
                            initial_prevalence, final_prevalence, signal, proxy_error
                        )
                        print(
                            f"scout-drift-confirmation cell={cell_name} seeds={seeds} "
                            f"device={resolved_device} workers={workers}",
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
                        ).validate()
                        profile_rows = _run_profile_seeds(
                            seeds=seeds,
                            seed_offset=seed_offset,
                            config=config,
                            device=resolved_device,
                            initial_prevalence=initial_prevalence,
                            final_prevalence=final_prevalence,
                            signal=signal,
                            proxy_error=proxy_error,
                            executor=executor,
                        )
                        for replicate, seed_rows in enumerate(profile_rows):
                            seed = seed_offset + replicate
                            for row in seed_rows:
                                row["seed"] = seed
                                records.append(row)
    finally:
        for key, value in previous_thread_limits.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * FAMILY_CELLS * len(METHODS)
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} confirmation rows; received {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate cell/seed/method records in confirmation output")
    counts = detail.groupby(["scenario", "budget_rate", "alpha_allocation"]).size()
    if len(counts) != FAMILY_CELLS * len(METHODS) or not counts.eq(seeds).all():
        raise RuntimeError("confirmation output has missing cell/method/seed records")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("all methods require positive query support")
    cap_violations = int((detail["labels_queried"] > detail["label_budget"]).sum())
    if cap_violations:
        raise RuntimeError("confirmation exceeded a realized hard label cap")
    detail["cap_violation"] = detail["labels_queried"] > detail["label_budget"]
    if not np.isfinite(detail["expected_postpromotion_net_gain"].to_numpy(dtype=float)).all():
        raise RuntimeError("evaluator-known expected utility contains non-finite values")

    contrasts = _paired_contrasts(detail, draws=bootstrap_draws, seed=BOOTSTRAP_SEED)
    primary = contrasts.loc[contrasts.primary_comparison]
    full_design = seeds >= MIN_SEEDS
    confirmation_pass = bool(full_design and primary.familywise_one_sided_lower.gt(0).all())
    status = (
        "confirmed_on_registered_grid"
        if confirmation_pass
        else "not_confirmed"
        if full_design
        else "smoke_only_not_confirmation"
    )
    summary = detail.groupby(["scenario", "budget_rate", "alpha_allocation"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        mean_expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        mean_labels_queried=("labels_queried", "mean"),
        mean_monitor_events=("monitor_events_processed", "mean"),
        cap_violations=("cap_violation", "sum"),
    )
    detail.to_parquet(metrics_dir / "scout_context_drift_confirmation_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "scout_context_drift_confirmation_cells.parquet", index=False)
    contrasts.to_parquet(
        metrics_dir / "scout_context_drift_confirmation_contrasts.parquet", index=False
    )

    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "scout_context_drift_confirmation.md"
    report = [
        "# Eventwise-propensity target-scout confirmation under abrupt context drift",
        "",
        (
            f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; "
            f"seed block: {seed_offset}–{seed_offset + seeds - 1}; worker processes: {workers}."
        ),
        "",
        (
            f"The matched grid contains {FAMILY_CELLS} prevalence, signal, proxy-error, and budget "
            f"cells, {len(METHODS)} methods, and {len(detail):,} method-cell-seed rows. The primary "
            "endpoint is evaluator-known postpromotion net decision utility, equally weighted over "
            "cells. Seed IDs are resampled as clusters across all cells."
        ),
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        (
            "The two primary comparisons are eventwise scout versus pooled rank and nested-volume. "
            "Their one-sided 97.5% seed-cluster bootstrap lower limits are Bonferroni-adjusted for "
            "an approximate simultaneous 95% familywise assessment. The primary gate passes only "
            "when both exceed zero. Bootstrap coverage is approximate, not a finite-sample theorem."
        ),
        "",
        (
            f"Integrity: all expected rows present; positive propensities verified; "
            f"{cap_violations} cap violations; {int(detail.harmful_postpromotion_promotion.sum())} "
            "harmful promotions by evaluator-known future utility. These finite synthetic results "
            "apply only to the frozen DGP and feedback design and establish no novelty claim."
        ),
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {protocol_hash}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_eventwise_context_drift_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "protocol": {"path": protocol.as_posix(), "sha256": protocol_hash},
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "workers": workers,
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
            "primary_comparisons": primary.to_dict(orient="records"),
            "primary_gate_pass": confirmation_pass,
            "total_rows": len(detail),
            "cap_violations": cap_violations,
            "positive_propensities": True,
            "all_expected_rows_present": True,
            "harmful_promotions": int(detail.harmful_postpromotion_promotion.sum()),
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/scout_context_drift_confirmation_streams.parquet",
            "metrics/scout_context_drift_confirmation_cells.parquet",
            "metrics/scout_context_drift_confirmation_contrasts.parquet",
            "reports/scout_context_drift_confirmation.md",
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
        default=Path("outputs/scout_context_policy_eventwise_bound_confirmation_600"),
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_bound_confirmation_protocol.md"),
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    args = parser.parse_args(argv)
    print(
        run_confirmation(
            output=args.output,
            protocol=args.protocol,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            workers=args.workers,
            bootstrap_draws=args.bootstrap_draws,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
