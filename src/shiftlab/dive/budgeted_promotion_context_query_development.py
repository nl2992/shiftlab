"""Screen predictable query policies for the eventwise target-scout monitor."""

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
from .budgeted_promotion import (
    QUERY_POLICIES,
    SCOUT_BOUND_MODES,
    BudgetedPromotionConfig,
    _run_seed,
)
from .experiment import finalize_manifest
from .promotion_grid import _time_splits

PREVALENCES = (0.10, 0.50, 0.90)
PERSISTENCES = (0.0, 0.80)
SIGNAL_STRENGTHS = (0.0, 0.05, 0.10)
PROXY_ERRORS = (0.0, 0.25)
BUDGET_RATES = (0.20, 0.40)
METHODS = (
    "rank",
    "rank_context_volume",
    "scout_context_policy",
    "scout_context_policy_eventwise_propensity_bound",
)
EVENTWISE = METHODS[-1]
MINIMUM_BOUND = METHODS[-2]
SEED_OFFSET = 20_930_000
MIN_SEEDS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_930_060
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity",
    fn_cost=5.0,
    fp_cost=1.0,
    harmful_adaptation=False,
)


def _run_seed_profile(
    *,
    seed: int,
    prevalence: float,
    persistence: float,
    signal: float,
    proxy_error: float,
    config: BudgetedPromotionConfig,
    device: str,
) -> list[dict[str, object]]:
    rows = _run_seed(
        scenario=SCENARIO,
        seed=seed,
        config=config,
        device=device,
        scout_bound_modes=SCOUT_BOUND_MODES,
    )
    selected = [
        row
        for row in rows
        if row["alpha_allocation"] in METHODS and row["query_policy"] in QUERY_POLICIES
    ]
    expected = len(QUERY_POLICIES) * len(BUDGET_RATES) * len(METHODS)
    if len(selected) != expected:
        raise RuntimeError(f"expected {expected} scout/query rows, received {len(selected)}")
    scenario = (
        f"p{round(prevalence * 100):02d}_rho{round(persistence * 100):02d}_"
        f"delta{round(signal * 1000):03d}_error{round(proxy_error * 100):02d}"
    )
    for row in selected:
        row["scenario"] = scenario
        row["context_target_prevalence"] = prevalence
        row["context_persistence"] = persistence
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["seed"] = seed
    return selected


def _paired_contrasts(detail: pd.DataFrame, *, draws: int, seed: int) -> pd.DataFrame:
    positive = detail.loc[detail.context_signal_strength.gt(0)]
    seeds = np.sort(positive.seed.unique())
    cells = sorted(
        positive[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    comparisons = [
        (
            f"eventwise_minus_minimum_bound__{query}",
            (query, EVENTWISE),
            (query, MINIMUM_BOUND),
        )
        for query in QUERY_POLICIES
    ] + [
        (
            f"eventwise_{query}_minus_uniform",
            (query, EVENTWISE),
            ("uniform", EVENTWISE),
        )
        for query in QUERY_POLICIES
        if query != "uniform"
    ]
    metrics = (
        "expected_postpromotion_net_gain",
        "labels_queried",
        "mean_event_process_bound",
    )
    records: list[dict[str, object]] = []
    for comparison_index, (name, candidate_key, baseline_key) in enumerate(comparisons):
        for metric_index, metric in enumerate(metrics):
            differences = np.empty((len(cells), len(seeds)), dtype=float)
            for cell_index, (scenario, budget_rate) in enumerate(cells):
                cell = positive.loc[
                    positive.scenario.eq(scenario) & positive.budget_rate.eq(budget_rate)
                ]
                candidate = cell.loc[
                    cell.query_policy.eq(candidate_key[0])
                    & cell.alpha_allocation.eq(candidate_key[1])
                ].sort_values("seed")
                baseline = cell.loc[
                    cell.query_policy.eq(baseline_key[0])
                    & cell.alpha_allocation.eq(baseline_key[1])
                ].sort_values("seed")
                if (
                    len(candidate) != len(seeds)
                    or len(baseline) != len(seeds)
                    or not np.array_equal(candidate.seed.to_numpy(), seeds)
                    or not np.array_equal(baseline.seed.to_numpy(), seeds)
                ):
                    raise ValueError(f"unmatched seeds in {scenario}, cap={budget_rate}")
                differences[cell_index] = candidate[metric].to_numpy(dtype=float) - baseline[
                    metric
                ].to_numpy(dtype=float)
            per_seed = differences.mean(axis=0)
            rng = np.random.default_rng(seed + comparison_index * len(metrics) + metric_index)
            bootstrap = np.empty(draws, dtype=float)
            for start in range(0, draws, 100):
                stop = min(draws, start + 100)
                indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
                bootstrap[start:stop] = per_seed[indices].mean(axis=1)
            records.append(
                {
                    "comparison": name,
                    "metric": metric,
                    "n_positive_cells": len(cells),
                    "n_seed_clusters": len(seeds),
                    "equal_cell_mean_difference": float(per_seed.mean()),
                    "descriptive_bootstrap_ci_level": 0.95,
                    "bootstrap_ci_low": float(np.quantile(bootstrap, 0.025)),
                    "bootstrap_ci_high": float(np.quantile(bootstrap, 0.975)),
                    "bootstrap_draws": draws,
                    "bootstrap_seed": seed + comparison_index * len(metrics) + metric_index,
                    "confirmatory": False,
                }
            )
    return pd.DataFrame.from_records(records)


def run_development(
    *,
    output: Path,
    protocol: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    workers: int = 6,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> Path:
    if seeds < 2 or workers < 1 or bootstrap_draws < 100:
        raise ValueError("seeds must be >=2, workers positive, and bootstrap draws >=100")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty development output: {output}")
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()

    profiles = [
        (prevalence, persistence, signal, proxy_error)
        for prevalence in PREVALENCES
        for persistence in PERSISTENCES
        for signal in SIGNAL_STRENGTHS
        for proxy_error in PROXY_ERRORS
    ]
    thread_variables = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
    previous_thread_limits = {key: os.environ.get(key) for key in thread_variables}
    if workers > 1:
        os.environ.update({key: "1" for key in thread_variables})
    pool_context = ProcessPoolExecutor(max_workers=workers) if workers > 1 else nullcontext(None)
    rows: list[dict[str, object]] = []
    try:
        with pool_context as executor:
            for prevalence, persistence, signal, proxy_error in profiles:
                name = (
                    f"p{round(prevalence * 100):02d}_rho{round(persistence * 100):02d}_"
                    f"delta{round(signal * 1000):03d}_error{round(proxy_error * 100):02d}"
                )
                config = BudgetedPromotionConfig(
                    n=n,
                    d=d,
                    seeds=1,
                    seed_offset=seed_offset,
                    switching_cost=0.05,
                    budget_rates=BUDGET_RATES,
                    query_policies=QUERY_POLICIES,
                    shared_query_randomness=True,
                    alpha_allocations=("rank", "rank_context_volume"),
                    estimators=("direct_ipw",),
                    monitoring_rules=("fixed_mixture",),
                    bound_mode="global",
                    context_feature_index=d - 1,
                    context_target_prevalence=prevalence,
                    context_signal_strength=signal,
                    context_proxy_error=proxy_error,
                    context_persistence=persistence,
                    include_scout_context_policy=True,
                    scenario_subset=("candidate_context_heterogeneity",),
                    create_plot=False,
                    device=resolved_device,
                ).validate()
                print(
                    f"scout-query-development cell={name} seeds={seeds} "
                    f"device={resolved_device} workers={workers}",
                    flush=True,
                )
                if executor is None:
                    profile_rows = [
                        _run_seed_profile(
                            seed=seed_offset + offset,
                            prevalence=prevalence,
                            persistence=persistence,
                            signal=signal,
                            proxy_error=proxy_error,
                            config=config,
                            device=resolved_device,
                        )
                        for offset in range(seeds)
                    ]
                else:
                    futures = {
                        executor.submit(
                            _run_seed_profile,
                            seed=seed_offset + offset,
                            prevalence=prevalence,
                            persistence=persistence,
                            signal=signal,
                            proxy_error=proxy_error,
                            config=config,
                            device=resolved_device,
                        ): offset
                        for offset in range(seeds)
                    }
                    profile_rows = [None] * seeds
                    for completed, future in enumerate(as_completed(futures), start=1):
                        profile_rows[futures[future]] = future.result()
                        if completed % 20 == 0 or completed == seeds:
                            print(
                                f"scout-query-development progress={completed}/{seeds} cell={name}",
                                flush=True,
                            )
                rows.extend(row for seed_rows in profile_rows for row in seed_rows)
    finally:
        for key, value in previous_thread_limits.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    detail = pd.DataFrame.from_records(rows).sort_values(
        ["scenario", "budget_rate", "seed", "query_policy", "alpha_allocation"],
        kind="stable",
    )
    expected_rows = seeds * len(profiles) * len(BUDGET_RATES) * len(QUERY_POLICIES) * len(METHODS)
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, received {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "query_policy", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate scenario/cap/seed/query/method keys")
    if set(detail.query_policy) != set(QUERY_POLICIES) or set(detail.alpha_allocation) != set(
        METHODS
    ):
        raise RuntimeError("development output is missing a frozen policy or method")
    if (
        detail.propensity_min.isna().any()
        or not detail.propensity_min.ge(detail.budget_rate / 2 - 1e-12).all()
    ):
        raise RuntimeError("query propensity fell below its registered support floor")
    if not detail.propensity_max.le(np.maximum(0.5, detail.budget_rate) + 1e-12).all():
        raise RuntimeError("query propensity exceeded its registered ceiling")
    if detail.labels_queried.gt(detail.label_budget).any():
        raise RuntimeError("development exceeded a realized hard label cap")
    if not np.isfinite(detail.expected_postpromotion_net_gain.to_numpy(dtype=float)).all():
        raise RuntimeError("evaluator utility contains non-finite values")

    eventwise = detail.loc[detail.alpha_allocation.eq(EVENTWISE)]
    if not np.allclose(
        eventwise.mean_event_process_bound,
        5.0 * eventwise.mean_reciprocal_propensity + 0.05 / (n - _time_splits(n)[2]),
        rtol=1e-10,
        atol=1e-10,
    ):
        raise RuntimeError("eventwise support bounds do not match C times mean(1/q_t) plus charge")

    contrasts = _paired_contrasts(detail, draws=bootstrap_draws, seed=BOOTSTRAP_SEED)
    null_detail = detail.loc[detail.context_signal_strength.eq(0)]
    null_summary = (
        null_detail.groupby(["query_policy", "alpha_allocation"], sort=True)
        .agg(
            streams=("seed", "size"),
            promotions=("promoted", "sum"),
            harmful_promotions=("harmful_postpromotion_promotion", "sum"),
            promotion_rate=("promoted", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_bound=("mean_event_process_bound", "mean"),
        )
        .reset_index()
    )
    detail.to_parquet(metrics_dir / "scout_query_development_streams.parquet", index=False)
    contrasts.to_csv(metrics_dir / "scout_query_development_contrasts.csv", index=False)
    null_summary.to_csv(metrics_dir / "scout_query_development_null_controls.csv", index=False)
    cell_summary = (
        detail.groupby(["scenario", "budget_rate", "query_policy", "alpha_allocation"], sort=True)
        .agg(
            streams=("seed", "size"),
            mean_expected_net_gain=("expected_postpromotion_net_gain", "mean"),
            promotion_rate=("promoted", "mean"),
            harmful_promotions=("harmful_postpromotion_promotion", "sum"),
            mean_labels=("labels_queried", "mean"),
            mean_monitor_fraction=("monitor_fraction_processed", "mean"),
            mean_event_bound=("mean_event_process_bound", "mean"),
        )
        .reset_index()
    )
    cell_summary.to_parquet(metrics_dir / "scout_query_development_cells.parquet", index=False)

    report_path = reports_dir / "scout_query_development.md"
    status = "exploratory_development" if seeds >= MIN_SEEDS else "smoke_only"
    report = [
        "# Predictable query allocation for the eventwise target scout",
        "",
        (
            f"Status: **{status}**. Device: `{resolved_device}`; seeds/cell: {seeds}; seed block: "
            f"{seed_offset}–{seed_offset + seeds - 1}; workers: {workers}."
        ),
        "",
        (
            f"The grid covers {len(profiles) * len(BUDGET_RATES)} profile/cap cells, three query "
            f"policies, four decision rules, and {len(detail):,} matched stream-method rows. Query "
            "policies are uniform, variance-weighted, and decision-value-weighted; every method uses "
            "the same seed-specific uniforms across these policies. The eventwise monitor sees each "
            "propensity before its label and uses the corresponding predictable bound."
        ),
        "",
        "## Paired positive-signal development contrasts",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        (
            "Intervals resample seed clusters and equally weight profile/cap cells. They are "
            "development summaries after scanning query and decision rules, not confirmatory "
            "inference. Zero-signal promotion rates are diagnostic only; any candidate requires a "
            "fresh null calibration and a disjoint confirmation before a power or utility claim."
        ),
        "",
        "## Zero-signal controls",
        "",
        null_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Mathematical condition and scope",
        "",
        (
            "For a fixed candidate selected on the disjoint scout slice, let `G_t` be its bounded "
            "paired cost improvement, `Q_t` the randomized label indicator, `q_t` its learner-visible "
            "predictable query probability, and `kappa` the per-event switching charge. Under the "
            "certification null `E[G_t | F_{t-1}, X_t] <= kappa`, independent Bernoulli querying gives "
            "`E[Q_t G_t/q_t - kappa | F_{t-1}, X_t] <= 0`. If `|G_t| <= C`, the increment is bounded "
            "by `B_t=C/q_t+kappa`, known before the label. Therefore each fixed bounded-betting factor "
            "`1 + lambda * increment / B_t`, for `lambda in [0,1]`, has conditional expectation at "
            "most one; the frozen mixture is an e-process under this filtration. This is a "
            "predictable-bound application of the standard betting argument, not a new theorem."
        ),
        "",
        (
            "The query policies here are covariate-adaptive but fixed from pre-monitor fits; this grid "
            "does not test propensities adapted to prior certification evidence, delayed or "
            "outcome-dependent feedback, conditional-null violations, or real data. These results "
            "cannot support a novelty claim."
        ),
        "",
        (
            f"Frozen protocol: `{protocol.as_posix()}` (SHA-256 `{hashlib.sha256(protocol.read_bytes()).hexdigest()}`). "
            "No figure was generated."
        ),
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    manifest = {
        "experiment": "eventwise_target_scout_predictable_query_policy_development",
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
            "prevalences": PREVALENCES,
            "context_persistences": PERSISTENCES,
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "budgets": BUDGET_RATES,
            "query_policies": QUERY_POLICIES,
            "shared_query_randomness": True,
            "methods": METHODS,
            "shared_scout_split_fraction": 0.5,
            "scout_bound_modes": SCOUT_BOUND_MODES,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "inference": {
            "all_expected_rows_present": True,
            "unique_method_stream_keys": True,
            "all_propensity_support_checks_passed": True,
            "all_hard_label_caps_passed": True,
            "all_eventwise_bound_formula_checks_passed": True,
            "null_calibration": False,
            "confirmatory": False,
            "figure_generated": False,
        },
        "source_files": {},
        "environment": environment(),
    }
    source_paths = (
        Path("pyproject.toml"),
        Path("src/shiftlab/dive/budgeted_promotion.py"),
        Path("src/shiftlab/dive/budgeted_promotion_context_query_development.py"),
        Path("src/shiftlab/dive/query.py"),
        Path("src/shiftlab/dive/eprocess.py"),
    )
    manifest["source_files"] = {
        path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    print(report_path, flush=True)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/scout_query_development_60"))
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_query_development_protocol.md"),
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
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
