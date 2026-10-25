"""Confirm eventwise-scout utility under persistent Markov contexts."""

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

PREVALENCES = (0.10, 0.50, 0.90)
PERSISTENCES = (0.0, 0.50, 0.80)
SIGNAL_STRENGTHS = (0.05, 0.10)
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
COMPARATORS = (
    ("eventwise_minus_rank", "rank", True),
    ("eventwise_minus_nested_volume", "rank_context_volume", True),
    ("eventwise_minus_minimum_bound", "scout_context_policy", False),
)
SEED_OFFSET = 20_910_000
MIN_SEEDS = 600
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_910_600
NULL_CALIBRATION_MANIFEST = Path(
    "outputs/scout_context_policy_eventwise_markov_eventwise_null_1000/reports/manifest.json"
)
PROFILE_COUNT = len(PREVALENCES) * len(PERSISTENCES) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS)
FAMILY_CELLS = PROFILE_COUNT * len(BUDGET_RATES)
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity",
    fn_cost=5.0,
    fp_cost=1.0,
    harmful_adaptation=False,
)


def _cell_name(prevalence: float, persistence: float, signal: float, proxy_error: float) -> str:
    return (
        f"markov_p{round(100 * prevalence):02d}_rho{round(100 * persistence):02d}_"
        f"delta{round(1000 * signal):03d}_error{round(100 * proxy_error):02d}"
    )


def _run_seed_profile(
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    prevalence: float,
    persistence: float,
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
        raise RuntimeError("Markov confirmation stream is missing a method or budget result")
    cell = _cell_name(prevalence, persistence, signal, proxy_error)
    for row in selected:
        row["scenario"] = cell
        row["context_target_prevalence"] = prevalence
        row["context_persistence"] = persistence
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["seed"] = seed
    return selected


def _run_profile(
    *,
    seeds: int,
    seed_offset: int,
    config: BudgetedPromotionConfig,
    device: str,
    prevalence: float,
    persistence: float,
    signal: float,
    proxy_error: float,
    executor: ProcessPoolExecutor | None,
) -> list[list[dict[str, object]]]:
    results: list[list[dict[str, object]] | None] = [None] * seeds
    if executor is None:
        for replicate in range(seeds):
            results[replicate] = _run_seed_profile(
                seed_offset + replicate,
                config,
                device,
                prevalence,
                persistence,
                signal,
                proxy_error,
            )
    else:
        futures = {
            executor.submit(
                _run_seed_profile,
                seed_offset + replicate,
                config,
                device,
                prevalence,
                persistence,
                signal,
                proxy_error,
            ): replicate
            for replicate in range(seeds)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if completed % 100 == 0 or completed == seeds:
                print(
                    f"eventwise-markov-confirm progress={completed}/{seeds} "
                    f"cell={_cell_name(prevalence, persistence, signal, proxy_error)}",
                    flush=True,
                )
    if any(result is None for result in results):
        raise RuntimeError("Markov confirmation profile is missing seed results")
    return [result for result in results if result is not None]


def _paired_contrasts(
    detail: pd.DataFrame,
    *,
    draws: int,
    seed: int,
    query_policies: tuple[str, ...] = ("uniform",),
    expected_cells: int = FAMILY_CELLS,
) -> pd.DataFrame:
    cells = sorted(
        detail[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    seeds = np.sort(detail["seed"].unique())
    if len(cells) != expected_cells or len(seeds) < 2:
        raise ValueError("confirmation does not contain the frozen cell and seed family")
    if query_policies == ("uniform",):
        comparisons = [
            (name, "uniform", EVENTWISE_METHOD, "uniform", comparator, primary)
            for name, comparator, primary in COMPARATORS
        ]
    elif set(query_policies) == {"uniform", "variance"}:
        comparisons = [
            (
                "variance_eventwise_minus_rank",
                "variance",
                EVENTWISE_METHOD,
                "variance",
                "rank",
                True,
            ),
            (
                "variance_eventwise_minus_nested_volume",
                "variance",
                EVENTWISE_METHOD,
                "variance",
                "rank_context_volume",
                True,
            ),
            (
                "variance_eventwise_minus_minimum_bound",
                "variance",
                EVENTWISE_METHOD,
                "variance",
                "scout_context_policy",
                False,
            ),
            (
                "variance_eventwise_minus_uniform_eventwise",
                "variance",
                EVENTWISE_METHOD,
                "uniform",
                EVENTWISE_METHOD,
                False,
            ),
        ]
    else:
        raise ValueError("confirmation supports the uniform baseline or matched uniform/variance")
    rows: list[dict[str, object]] = []
    for contrast_index, (
        name,
        candidate_query,
        candidate_method,
        comparator_query,
        comparator_method,
        primary,
    ) in enumerate(comparisons):
        difference = np.empty((len(cells), len(seeds)), dtype=float)
        for cell_index, (scenario, budget_rate) in enumerate(cells):
            cell = detail.loc[
                detail["scenario"].eq(scenario) & detail["budget_rate"].eq(budget_rate)
            ]
            candidate = cell.loc[
                cell["query_policy"].eq(candidate_query)
                & cell["alpha_allocation"].eq(candidate_method)
            ].sort_values("seed")
            baseline = cell.loc[
                cell["query_policy"].eq(comparator_query)
                & cell["alpha_allocation"].eq(comparator_method)
            ].sort_values("seed")
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

        rng = np.random.default_rng(seed + contrast_index)
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


def _verify_null_calibration(
    manifest_path: Path = NULL_CALIBRATION_MANIFEST,
    query_policies: tuple[str, ...] = ("uniform",),
) -> tuple[dict[str, object], str]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"required passed null calibration is missing: {manifest_path}")
    manifest_bytes = manifest_path.read_bytes()
    calibration = json.loads(manifest_bytes)
    inference = calibration.get("inference", {})
    configuration = calibration.get("configuration", {})
    calibrated_query_policies = tuple(
        configuration.get(
            "query_policies",
            (
                configuration.get(
                    "query_policy",
                ),
            ),
        )
    )
    if (
        calibration.get("status") != "passed"
        or calibration.get("experiment") != "target_scout_eventwise_context_markov_null_calibration"
        or not inference.get("calibration_pass")
        or not inference.get("all_caps_respected")
        or not inference.get("conditional_null_verified")
        or configuration.get("method") != EVENTWISE_METHOD
        or tuple(configuration.get("context_persistences", ())) != PERSISTENCES
        or tuple(configuration.get("prevalences", ())) != PREVALENCES
        or tuple(configuration.get("proxy_errors", ())) != PROXY_ERRORS
        or tuple(configuration.get("budget_rates", ())) != BUDGET_RATES
        or not set(query_policies).issubset(calibrated_query_policies)
    ):
        raise ValueError(
            "required eventwise Markov null-calibration gate has not passed as registered"
        )
    return calibration, hashlib.sha256(manifest_bytes).hexdigest()


def run_confirmation(
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
    bootstrap_seed: int = BOOTSTRAP_SEED,
    query_policies: tuple[str, ...] = ("uniform",),
    persistence_values: tuple[float, ...] = PERSISTENCES,
    null_calibration_manifest: Path = NULL_CALIBRATION_MANIFEST,
) -> Path:
    if seeds < 2 or seed_offset < 0 or n < 1000 or d < 3:
        raise ValueError("confirmation requires >=2 nonnegative seeds, n>=1000, and d>=3")
    if seeds >= MIN_SEEDS and seed_offset < SEED_OFFSET:
        raise ValueError("full confirmation runs must use the frozen disjoint seed block")
    if workers < 1 or bootstrap_draws < 100:
        raise ValueError("workers must be positive and bootstrap draws must be >=100")
    if (
        not query_policies
        or len(set(query_policies)) != len(query_policies)
        or any(policy not in QUERY_POLICIES for policy in query_policies)
        or not persistence_values
        or len(set(persistence_values)) != len(persistence_values)
        or any(value not in PERSISTENCES for value in persistence_values)
    ):
        raise ValueError("query policies or persistence values are invalid")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen confirmation protocol not found: {protocol}")
    calibration_manifest, calibration_manifest_hash = _verify_null_calibration(
        null_calibration_manifest, query_policies
    )
    profile_count = (
        len(PREVALENCES) * len(persistence_values) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS)
    )
    family_cells = profile_count * len(BUDGET_RATES)
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
            for prevalence in PREVALENCES:
                for persistence in persistence_values:
                    for signal in SIGNAL_STRENGTHS:
                        for proxy_error in PROXY_ERRORS:
                            cell = _cell_name(prevalence, persistence, signal, proxy_error)
                            print(
                                f"eventwise-markov-confirm cell={cell} seeds={seeds} "
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
                                query_policies=query_policies,
                                shared_query_randomness=len(query_policies) > 1,
                                alpha_allocations=("rank", "rank_context_volume"),
                                estimators=("direct_ipw",),
                                monitoring_rules=("fixed_mixture",),
                                bound_mode="global",
                                context_feature_index=d - 1,
                                context_threshold=0.0,
                                context_target_prevalence=prevalence,
                                context_signal_strength=signal,
                                context_proxy_error=proxy_error,
                                context_persistence=persistence,
                                include_scout_context_policy=True,
                                scenario_subset=("candidate_context_heterogeneity",),
                                create_plot=False,
                                device=resolved_device,
                            ).validate()
                            profile = _run_profile(
                                seeds=seeds,
                                seed_offset=seed_offset,
                                config=config,
                                device=resolved_device,
                                prevalence=prevalence,
                                persistence=persistence,
                                signal=signal,
                                proxy_error=proxy_error,
                                executor=executor,
                            )
                            records.extend(row for seed_rows in profile for row in seed_rows)
    finally:
        for key, value in previous_thread_limits.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * family_cells * len(METHODS) * len(query_policies)
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} confirmation rows; received {len(detail)}")
    key = ["scenario", "query_policy", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate cell/seed/method rows in confirmation")
    counts = detail.groupby(["scenario", "query_policy", "budget_rate", "alpha_allocation"]).size()
    if (
        len(counts) != family_cells * len(METHODS) * len(query_policies)
        or not counts.eq(seeds).all()
    ):
        raise RuntimeError("confirmation has missing cell/method/seed rows")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("all methods require positive query support")
    detail["cap_violation"] = detail["labels_queried"] > detail["label_budget"]
    cap_violations = int(detail["cap_violation"].sum())
    if cap_violations:
        raise RuntimeError("confirmation exceeded a realized hard label cap")
    if not np.isfinite(detail["expected_postpromotion_net_gain"].to_numpy(dtype=float)).all():
        raise RuntimeError("evaluator-known expected utility contains non-finite values")

    contrasts = _paired_contrasts(
        detail,
        draws=bootstrap_draws,
        seed=bootstrap_seed,
        query_policies=query_policies,
        expected_cells=family_cells,
    )
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
    summary = detail.groupby(
        [
            "scenario",
            "query_policy",
            "budget_rate",
            "alpha_allocation",
            "context_target_prevalence",
            "context_persistence",
            "context_signal_strength",
            "context_proxy_error",
        ],
        as_index=False,
    ).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        mean_expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        mean_labels_queried=("labels_queried", "mean"),
        mean_monitor_events=("monitor_events_processed", "mean"),
        cap_violations=("cap_violation", "sum"),
    )
    detail.to_parquet(metrics_dir / "eventwise_markov_confirmation_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "eventwise_markov_confirmation_cells.parquet", index=False)
    contrasts.to_parquet(
        metrics_dir / "eventwise_markov_confirmation_contrasts.parquet", index=False
    )

    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "eventwise_markov_confirmation.md"
    report = [
        "# Eventwise-scout confirmation under persistent contexts",
        "",
        f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: {seed_offset}–{seed_offset + seeds - 1}; workers: {workers}.",
        "",
        f"The matched grid contains {family_cells} positive-signal cells, query policies {', '.join(query_policies)}, {len(METHODS)} methods, and {len(detail):,} method-cell-seed-query rows. The primary endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over cells and paired by seed cluster.",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        "For the variance-query candidate, the primary comparisons are eventwise versus pooled rank and nested context-volume under the same variance query policy. Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation for approximate simultaneous 95% familywise assessment. The uniform eventwise contrast isolates query allocation; the minimum-bound contrast is secondary. The original uniform-only design retains its registered comparison interpretation. Bootstrap coverage is approximate, not an exact finite-sample guarantee.",
        "",
        f"Integrity: all expected unique rows present; positive propensities verified; {cap_violations} cap violations; {int(detail.harmful_postpromotion_promotion.sum())} harmful promotions by evaluator-known future utility. These results apply only to the frozen synthetic grid and feedback design.",
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {protocol_hash}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_eventwise_context_markov_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "protocol": {"path": protocol.as_posix(), "sha256": protocol_hash},
        "prerequisite_null_calibration": {
            "path": null_calibration_manifest.as_posix(),
            "manifest_sha256": calibration_manifest_hash,
            "status": calibration_manifest["status"],
            "familywise_alpha": calibration_manifest["inference"]["familywise_alpha"],
            "simultaneous_cells": calibration_manifest["inference"]["simultaneous_cells"],
        },
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "workers": workers,
            "prevalences": PREVALENCES,
            "context_persistences": persistence_values,
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "switching_cost": SWITCHING_COST,
            "budget_rates": BUDGET_RATES,
            "methods": METHODS,
            "query_policies": query_policies,
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "alpha": 0.05,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": bootstrap_seed,
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
            "metrics/eventwise_markov_confirmation_streams.parquet",
            "metrics/eventwise_markov_confirmation_cells.parquet",
            "metrics/eventwise_markov_confirmation_contrasts.parquet",
            "reports/eventwise_markov_confirmation.md",
        ],
        "environment": environment(),
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    print(report_path, flush=True)
    return report_path


def reanalyze_existing_confirmation(
    *,
    output: Path,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
    bootstrap_seed: int = BOOTSTRAP_SEED,
) -> Path:
    """Recompute frozen paired contrasts from an existing, integrity-checked stream table."""
    reports_dir = output / "reports"
    metrics_dir = output / "metrics"
    manifest_path = reports_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    detail_path = metrics_dir / "eventwise_markov_confirmation_streams.parquet"
    detail = pd.read_parquet(detail_path)
    configuration = manifest["configuration"]
    query_policies = tuple(configuration.get("query_policies", ("uniform",)))
    seeds = int(configuration["seeds_per_cell"])
    expected_cells = detail[["scenario", "budget_rate"]].drop_duplicates().shape[0]
    expected_rows = seeds * expected_cells * len(METHODS) * len(query_policies)
    key = ["scenario", "query_policy", "budget_rate", "seed", "alpha_allocation"]
    if len(detail) != expected_rows or detail.duplicated(key).any():
        raise ValueError("cannot reanalyze an incomplete or duplicated confirmation stream table")
    if set(detail.query_policy) != set(query_policies):
        raise ValueError("confirmation stream query policies disagree with its manifest")
    if detail.cap_violation.any() or detail.propensity_min.isna().any():
        raise ValueError("cannot reanalyze streams that failed cap or support checks")

    contrasts = _paired_contrasts(
        detail,
        draws=bootstrap_draws,
        seed=bootstrap_seed,
        query_policies=query_policies,
        expected_cells=expected_cells,
    )
    contrasts_path = metrics_dir / "eventwise_markov_confirmation_contrasts.parquet"
    contrasts.to_parquet(contrasts_path, index=False)
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

    previous_hashes = manifest.get("sha256", {})
    manifest.setdefault(
        "simulation_source_hashes_before_analysis_correction",
        previous_hashes.get("source_files", {}),
    )
    raw_stream_hash = hashlib.sha256(detail_path.read_bytes()).hexdigest()
    manifest["status"] = status
    manifest["analysis_correction"] = {
        "raw_stream_metrics_sha256": raw_stream_hash,
        "description": (
            "A post-run audit corrected the paired-contrast method mapping: the variance-query "
            "eventwise-minus-rank contrast had selected the eventwise method on both sides. "
            "The frozen candidate, comparator, endpoint, seed block, simulator, and raw stream "
            "metrics are unchanged; all registered contrasts were recomputed from the saved rows."
        ),
        "bootstrap_draws": bootstrap_draws,
        "bootstrap_seed": bootstrap_seed,
        "method": "seed-cluster percentile bootstrap, equal weight over registered cells",
    }
    manifest["inference"]["primary_comparisons"] = primary.to_dict(orient="records")
    manifest["inference"]["primary_gate_pass"] = confirmation_pass
    manifest["inference"]["total_rows"] = len(detail)
    report_path = reports_dir / "eventwise_markov_confirmation.md"
    protocol = manifest["protocol"]
    report = [
        "# Eventwise-scout confirmation under persistent contexts",
        "",
        f"Status: **{status}**. Device: {configuration['device']}; seeds per cell: {seeds}; seed block: {configuration['seed_offset']}–{configuration['seed_end_inclusive']}; workers: {configuration['workers']}.",
        "",
        f"The matched grid contains {expected_cells} positive-signal cells, query policies {', '.join(query_policies)}, {len(METHODS)} methods, and {len(detail):,} method-cell-seed-query rows. The endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over cells and paired by seed cluster.",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        "The primary comparisons are eventwise variance-query scouting versus pooled rank and nested context-volume under variance querying. Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation for approximate simultaneous 95% familywise assessment. The gate passes only when both limits exceed zero. The minimum-bound and uniform-query contrasts are secondary. Bootstrap coverage is approximate, not an exact finite-sample guarantee.",
        "",
        f"Integrity: {len(detail):,}/{expected_rows:,} expected unique rows; positive propensities verified; {int(detail.cap_violation.sum())} cap violations; {int(detail.harmful_postpromotion_promotion.sum())} harmful promotions by evaluator-known future utility.",
        "",
        "Analysis correction: a post-run audit found that the initial primary variance-eventwise-minus-rank contrast selected eventwise on both sides. The saved streams were not changed; the frozen contrast mapping was corrected and all contrasts recomputed from the row-level metrics. This correction does not tune or select a method using confirmation outcomes.",
        "",
        f"Frozen protocol: {protocol['path']} (SHA-256 {protocol['sha256']}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/scout_context_policy_eventwise_markov_confirmation_600"),
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_markov_confirmation_protocol.md"),
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    parser.add_argument("--query-policies", nargs="+", choices=QUERY_POLICIES, default=["uniform"])
    parser.add_argument(
        "--persistences", nargs="+", type=float, choices=PERSISTENCES, default=list(PERSISTENCES)
    )
    parser.add_argument("--null-calibration-manifest", type=Path, default=NULL_CALIBRATION_MANIFEST)
    parser.add_argument("--reanalyze-existing-output", type=Path)
    args = parser.parse_args(argv)
    if args.reanalyze_existing_output is not None:
        print(
            reanalyze_existing_confirmation(
                output=args.reanalyze_existing_output,
                bootstrap_draws=args.bootstrap_draws,
                bootstrap_seed=args.bootstrap_seed,
            ),
            flush=True,
        )
        return
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
            bootstrap_seed=args.bootstrap_seed,
            query_policies=tuple(args.query_policies),
            persistence_values=tuple(args.persistences),
            null_calibration_manifest=args.null_calibration_manifest,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
