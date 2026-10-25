"""Develop the eventwise target-scout under gradual and recurring contexts."""

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
from .budgeted_promotion import QUERY_POLICIES, BudgetedPromotionConfig, _run_seed
from .experiment import finalize_manifest

SCHEDULES = (
    "gradual_up",
    "gradual_down",
    "recurring_low_first",
    "recurring_high_first",
)
SIGNAL_STRENGTHS = (0.0, 0.05, 0.10)
PROXY_ERRORS = (0.0, 0.25)
BUDGET_RATES = (0.20, 0.40)
SWITCHING_COST = 0.05
METHODS = (
    "rank",
    "rank_context_volume",
    "scout_context_policy",
    "scout_context_policy_eventwise_propensity_bound",
)
EVENTWISE_METHOD = METHODS[-1]
SEED_OFFSET = 20_274_000
QUERY_SEED_OFFSET = 21_420_000
MIN_SEEDS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_274_060
BASE_FAMILY_CELLS = len(SCHEDULES) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS) * len(BUDGET_RATES)
FAMILY_CELLS = BASE_FAMILY_CELLS
POSITIVE_CELLS = len(SCHEDULES) * 2 * len(PROXY_ERRORS) * len(BUDGET_RATES)
NULL_CELLS = FAMILY_CELLS - POSITIVE_CELLS
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity",
    fn_cost=5.0,
    fp_cost=1.0,
    harmful_adaptation=False,
)


def _cell_name(schedule: str, signal: float, proxy_error: float) -> str:
    return f"{schedule}_delta{round(1000 * signal):03d}_error{round(100 * proxy_error):02d}"


def _run_cell_seed(
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    schedule: str,
    signal: float,
    proxy_error: float,
) -> list[dict[str, object]]:
    rows = _run_seed(
        scenario=SCENARIO,
        seed=seed,
        config=config,
        device=device,
        scout_bound_modes=("minimum_propensity", "eventwise_propensity"),
    )
    selected = [row for row in rows if row["alpha_allocation"] in METHODS]
    if len(selected) != len(METHODS) * len(BUDGET_RATES) * len(config.query_policies):
        raise RuntimeError("temporal development stream is missing a method or cap result")
    for row in selected:
        row["scenario"] = _cell_name(schedule, signal, proxy_error)
        row["context_prevalence_schedule"] = schedule
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["context_schedule_low"] = config.context_schedule_low
        row["context_schedule_high"] = config.context_schedule_high
        row["seed"] = seed
    return selected


def _paired_contrasts(
    detail: pd.DataFrame,
    *,
    draws: int,
    seed: int,
    query_policies: tuple[str, ...] = ("uniform",),
) -> pd.DataFrame:
    positive = detail.loc[detail["context_signal_strength"].gt(0)]
    seeds = np.sort(positive["seed"].unique())
    cells = sorted(
        positive[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    output: list[dict[str, object]] = []
    comparisons: list[tuple[str, str, str, str, str]] = []
    for query in query_policies:
        prefix = "" if query == "uniform" and len(query_policies) == 1 else f"{query}_"
        comparisons.extend(
            (f"{prefix}{name}", query, EVENTWISE_METHOD, query, comparator)
            for name, comparator in (
                ("eventwise_minus_minimum_bound", "scout_context_policy"),
                ("eventwise_minus_rank", "rank"),
                ("eventwise_minus_nested_volume", "rank_context_volume"),
            )
        )
    if set(query_policies) == {"uniform", "variance"}:
        comparisons.append(
            (
                "variance_eventwise_minus_uniform_eventwise",
                "variance",
                EVENTWISE_METHOD,
                "uniform",
                EVENTWISE_METHOD,
            )
        )
    for contrast_index, (
        contrast,
        candidate_query,
        candidate_method,
        baseline_query,
        baseline_method,
    ) in enumerate(comparisons):
        differences = np.empty((len(cells), len(seeds)), dtype=float)
        for cell_index, (scenario, budget_rate) in enumerate(cells):
            cell = positive.loc[
                positive["scenario"].eq(scenario)
                & positive["budget_rate"].eq(budget_rate)
                & positive["query_policy"].eq(candidate_query)
            ]
            candidate = cell.loc[cell["alpha_allocation"].eq(candidate_method)].sort_values("seed")
            baseline_cell = positive.loc[
                positive["scenario"].eq(scenario)
                & positive["budget_rate"].eq(budget_rate)
                & positive["query_policy"].eq(baseline_query)
            ]
            baseline = baseline_cell.loc[
                baseline_cell["alpha_allocation"].eq(baseline_method)
            ].sort_values("seed")
            if (
                len(candidate) != len(seeds)
                or len(baseline) != len(seeds)
                or not np.array_equal(candidate["seed"].to_numpy(), seeds)
                or not np.array_equal(baseline["seed"].to_numpy(), seeds)
            ):
                raise ValueError(f"unmatched seeds in {scenario}, cap={budget_rate}")
            differences[cell_index] = candidate["expected_postpromotion_net_gain"].to_numpy(
                dtype=float
            ) - baseline["expected_postpromotion_net_gain"].to_numpy(dtype=float)
        rng = np.random.default_rng(seed + contrast_index)
        bootstrap = np.empty(draws, dtype=float)
        for start in range(0, draws, 100):
            stop = min(draws, start + 100)
            indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            bootstrap[start:stop] = np.take(differences, indices, axis=1).mean(axis=(0, 2))
        output.append(
            {
                "contrast": contrast,
                "metric": "expected_postpromotion_net_gain",
                "n_cells": len(cells),
                "n_seed_clusters": len(seeds),
                "mean_paired_difference": float(differences.mean()),
                "descriptive_bootstrap_ci_level": 0.95,
                "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                "bootstrap_draws": draws,
                "bootstrap_seed": seed + contrast_index,
                "confirmatory": False,
            }
        )
    return pd.DataFrame(output)


def run_development(
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
    query_policies: tuple[str, ...] = ("uniform",),
) -> Path:
    if seeds < 2 or seed_offset < 0 or n < 1000 or d < 3:
        raise ValueError("development requires >=2 nonnegative seeds, n>=1000, and d>=3")
    if (
        not query_policies
        or len(set(query_policies)) != len(query_policies)
        or any(policy not in QUERY_POLICIES for policy in query_policies)
        or set(query_policies) not in ({"uniform"}, {"uniform", "variance"})
    ):
        raise ValueError("query_policies must be uniform or matched uniform and variance")
    required_seed_offset = SEED_OFFSET if query_policies == ("uniform",) else QUERY_SEED_OFFSET
    if seeds >= MIN_SEEDS and seed_offset != required_seed_offset:
        raise ValueError("full development runs must use the frozen disjoint seed block")
    family_cells = BASE_FAMILY_CELLS * len(query_policies)
    if workers < 1 or bootstrap_draws < 100:
        raise ValueError("workers must be positive and bootstrap draws must be >=100")
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

    thread_variables = (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    )
    previous_thread_limits = {key: os.environ.get(key) for key in thread_variables}
    if workers > 1:
        os.environ.update({key: "1" for key in thread_variables})
    records: list[dict[str, object]] = []
    pool_context = ProcessPoolExecutor(max_workers=workers) if workers > 1 else nullcontext(None)
    try:
        with pool_context as executor:
            for schedule in SCHEDULES:
                for signal in SIGNAL_STRENGTHS:
                    for proxy_error in PROXY_ERRORS:
                        cell_name = _cell_name(schedule, signal, proxy_error)
                        config = BudgetedPromotionConfig(
                            n=n,
                            d=d,
                            seeds=1,
                            seed_offset=seed_offset,
                            switching_cost=SWITCHING_COST,
                            budget_rates=BUDGET_RATES,
                            query_policies=query_policies,
                            shared_query_randomness=len(query_policies) > 1,
                            alpha_allocations=("rank", "rank_context_volume"),
                            estimators=("direct_ipw",),
                            monitoring_rules=("fixed_mixture",),
                            bound_mode="global",
                            context_feature_index=d - 1,
                            context_threshold=0.0,
                            context_target_prevalence=0.5,
                            context_signal_strength=signal,
                            context_proxy_error=proxy_error,
                            context_prevalence_schedule=schedule,
                            include_scout_context_policy=True,
                            scenario_subset=("candidate_context_heterogeneity",),
                            create_plot=False,
                            device=resolved_device,
                        ).validate()
                        print(
                            f"scout-temporal-development cell={cell_name} seeds={seeds} "
                            f"device={resolved_device} workers={workers}",
                            flush=True,
                        )
                        if executor is None:
                            cell_records = [
                                row
                                for replicate in range(seeds)
                                for row in _run_cell_seed(
                                    seed_offset + replicate,
                                    config,
                                    resolved_device,
                                    schedule,
                                    signal,
                                    proxy_error,
                                )
                            ]
                        else:
                            futures = {
                                executor.submit(
                                    _run_cell_seed,
                                    seed_offset + replicate,
                                    config,
                                    resolved_device,
                                    schedule,
                                    signal,
                                    proxy_error,
                                ): replicate
                                for replicate in range(seeds)
                            }
                            by_replicate: list[list[dict[str, object]] | None] = [None] * seeds
                            for completed, future in enumerate(as_completed(futures), start=1):
                                by_replicate[futures[future]] = future.result()
                                if completed % 100 == 0 or completed == seeds:
                                    print(
                                        f"scout-temporal-development progress={completed}/{seeds} "
                                        f"cell={cell_name}",
                                        flush=True,
                                    )
                            if any(rows is None for rows in by_replicate):
                                raise RuntimeError("temporal development lost a seed result")
                            cell_records = [
                                row for rows in by_replicate if rows is not None for row in rows
                            ]
                        records.extend(cell_records)
    finally:
        for key, value in previous_thread_limits.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * family_cells * len(METHODS)
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows; received {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "query_policy", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate cell/seed/method rows")
    counts = detail.groupby(["scenario", "budget_rate", "query_policy", "alpha_allocation"]).size()
    if len(counts) != family_cells * len(METHODS) or not counts.eq(seeds).all():
        raise RuntimeError("development output has missing cell/method/seed rows")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("all methods require positive query support")
    detail["cap_violation"] = detail["labels_queried"] > detail["label_budget"]
    if detail["cap_violation"].any():
        raise RuntimeError("development exceeded a realized hard label cap")
    if not np.isfinite(detail["expected_postpromotion_net_gain"].to_numpy(dtype=float)).all():
        raise RuntimeError("evaluator-known utility contains non-finite values")
    null_rows = detail.loc[detail["context_signal_strength"].eq(0)]
    if null_rows["expected_postpromotion_net_gain"].gt(1e-9).any():
        raise RuntimeError("zero-signal schedule contains positive expected net gain")

    contrasts = _paired_contrasts(
        detail,
        draws=bootstrap_draws,
        seed=BOOTSTRAP_SEED,
        query_policies=query_policies,
    )
    group_fields = [
        "scenario",
        "context_prevalence_schedule",
        "budget_rate",
        "query_policy",
        "alpha_allocation",
        "context_signal_strength",
        "context_proxy_error",
    ]
    summary = detail.groupby(group_fields, as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        mean_expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        mean_labels_queried=("labels_queried", "mean"),
        mean_monitor_events=("monitor_events_processed", "mean"),
        cap_violations=("cap_violation", "sum"),
    )
    detail.to_parquet(
        metrics_dir / "scout_context_temporal_development_streams.parquet", index=False
    )
    summary.to_parquet(
        metrics_dir / "scout_context_temporal_development_cells.parquet", index=False
    )
    contrasts.to_parquet(
        metrics_dir / "scout_context_temporal_development_contrasts.parquet", index=False
    )

    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "scout_context_temporal_development.md"
    status = "exploratory_development" if seeds >= MIN_SEEDS else "smoke_only"
    report = [
        "# Eventwise target-scout development under gradual and recurring contexts",
        "",
        (
            f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: "
            f"{seed_offset}–{seed_offset + seeds - 1}; workers: {workers}."
        ),
        "",
        (
            f"The factorial has {family_cells} query-policy/profile/cap cells ({POSITIVE_CELLS * len(query_policies)} "
            f"positive-signal and {NULL_CELLS * len(query_policies)} zero-signal controls), "
            f"four methods per stream, and {len(detail):,} rows. Query policies: {', '.join(query_policies)}."
        ),
        "",
        "## Paired expected-net-gain contrasts",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        (
            "Intervals are descriptive seed-cluster bootstrap intervals. Zero-signal cells verify the "
            "simulator's event-conditional expected-gain null and are not a false-promotion calibration. "
            "No confirmatory or novelty claim follows from this development run."
        ),
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_eventwise_context_temporal_development",
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
            "schedules": SCHEDULES,
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "switching_cost": SWITCHING_COST,
            "budget_rates": BUDGET_RATES,
            "methods": METHODS,
            "cell_count": family_cells,
            "positive_signal_cells": POSITIVE_CELLS * len(query_policies),
            "null_cells": NULL_CELLS * len(query_policies),
            "query_policies": query_policies,
            "shared_query_randomness": len(query_policies) > 1,
            "alpha": 0.05,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "inference": {
            "paired_contrasts": contrasts.to_dict(orient="records"),
            "all_expected_rows_present": True,
            "all_propensities_positive": True,
            "zero_signal_expected_gain_nonpositive": True,
            "cap_violations": int(detail["cap_violation"].sum()),
            "confirmatory": False,
            "null_calibration": False,
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/scout_context_temporal_development_streams.parquet",
            "metrics/scout_context_temporal_development_cells.parquet",
            "metrics/scout_context_temporal_development_contrasts.parquet",
            "reports/scout_context_temporal_development.md",
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
        default=Path("outputs/scout_context_policy_eventwise_temporal_development_60"),
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_temporal_development_protocol.md"),
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument(
        "--query-policies",
        nargs="+",
        choices=QUERY_POLICIES,
        default=["uniform"],
    )
    args = parser.parse_args(argv)
    print(
        run_development(
            output=args.output,
            protocol=args.protocol,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            workers=args.workers,
            bootstrap_draws=args.bootstrap_draws,
            query_policies=tuple(args.query_policies),
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
