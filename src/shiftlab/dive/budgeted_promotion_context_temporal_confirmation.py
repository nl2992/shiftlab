"""Confirm eventwise-scout utility under gradual and recurring contexts."""

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
from .experiment import finalize_manifest

SCHEDULES = (
    "gradual_up",
    "gradual_down",
    "recurring_low_first",
    "recurring_high_first",
)
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
SEED_OFFSET = 20_920_000
MIN_SEEDS = 600
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_920_600
EXPECTED_CALIBRATION_SHA256 = "1c81c4f6812d237d4a455ecdcf10fdfc8e824683e91139f04393b9243a5485e6"
FAMILY_CELLS = len(SCHEDULES) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS) * len(BUDGET_RATES)
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
    if len(selected) != len(METHODS) * len(BUDGET_RATES):
        raise RuntimeError("temporal confirmation stream is missing a method or budget result")
    for row in selected:
        row["scenario"] = _cell_name(schedule, signal, proxy_error)
        row["context_prevalence_schedule"] = schedule
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["seed"] = seed
    return selected


def _run_cell(
    *,
    seeds: int,
    seed_offset: int,
    config: BudgetedPromotionConfig,
    device: str,
    schedule: str,
    signal: float,
    proxy_error: float,
    executor: ProcessPoolExecutor | None,
) -> list[dict[str, object]]:
    if executor is None:
        return [
            row
            for replicate in range(seeds)
            for row in _run_cell_seed(
                seed_offset + replicate,
                config,
                device,
                schedule,
                signal,
                proxy_error,
            )
        ]
    futures = {
        executor.submit(
            _run_cell_seed,
            seed_offset + replicate,
            config,
            device,
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
                f"eventwise-temporal-confirm progress={completed}/{seeds} "
                f"cell={_cell_name(schedule, signal, proxy_error)}",
                flush=True,
            )
    if any(rows is None for rows in by_replicate):
        raise RuntimeError("temporal confirmation lost a seed result")
    return [row for rows in by_replicate if rows is not None for row in rows]


def _paired_contrasts(detail: pd.DataFrame, *, draws: int, seed: int) -> tuple[pd.DataFrame, bool]:
    cells = sorted(
        detail[["scenario", "budget_rate"]].drop_duplicates().itertuples(index=False, name=None)
    )
    seeds = np.sort(detail["seed"].unique())
    if len(cells) != FAMILY_CELLS or len(seeds) < 2:
        raise ValueError("confirmation does not contain the frozen cell and seed family")
    rows: list[dict[str, object]] = []
    for contrast_index, (name, comparator, primary) in enumerate(COMPARATORS):
        difference = np.empty((len(cells), len(seeds)), dtype=float)
        for cell_index, (scenario, budget_rate) in enumerate(cells):
            cell = detail.loc[
                detail["scenario"].eq(scenario) & detail["budget_rate"].eq(budget_rate)
            ]
            candidate = cell.loc[cell["alpha_allocation"].eq(EVENTWISE_METHOD)].sort_values("seed")
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
    contrasts = pd.DataFrame(rows)
    primary = contrasts.loc[contrasts["primary_comparison"]]
    return contrasts, bool(primary["familywise_one_sided_lower"].gt(0).all())


def _verify_null_calibration(manifest_path: Path) -> tuple[dict[str, object], str]:
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"required passed temporal null calibration is missing: {manifest_path}"
        )
    manifest_bytes = manifest_path.read_bytes()
    normalized_hash = hashlib.sha256(manifest_bytes.replace(b"\r\n", b"\n")).hexdigest()
    if normalized_hash != EXPECTED_CALIBRATION_SHA256:
        raise ValueError("temporal calibration manifest hash differs from the frozen protocol")
    calibration = json.loads(manifest_bytes)
    inference = calibration.get("inference", {})
    configuration = calibration.get("configuration", {})
    if (
        calibration.get("status") != "passed"
        or calibration.get("experiment")
        != "target_scout_eventwise_context_temporal_null_calibration"
        or not inference.get("calibration_pass")
        or not inference.get("all_caps_respected")
        or not inference.get("conditional_null_verified")
        or inference.get("familywise_alpha") != 0.05
        or inference.get("simultaneous_cells") != 16
        or configuration.get("method") != EVENTWISE_METHOD
        or tuple(configuration.get("schedules", ())) != SCHEDULES
        or tuple(configuration.get("proxy_errors", ())) != PROXY_ERRORS
        or tuple(configuration.get("budget_rates", ())) != BUDGET_RATES
    ):
        raise ValueError("required temporal null-calibration gate has not passed as registered")
    return calibration, normalized_hash


def run_confirmation(
    *,
    output: Path,
    protocol: Path,
    calibration_manifest: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    workers: int = 6,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> Path:
    if seeds < 2 or seed_offset < 0 or n < 1000 or d < 3:
        raise ValueError("confirmation requires >=2 nonnegative seeds, n>=1000, and d>=3")
    if seeds >= MIN_SEEDS and seed_offset != SEED_OFFSET:
        raise ValueError("full confirmation runs must use the frozen disjoint seed block")
    if workers < 1 or bootstrap_draws < 100:
        raise ValueError("workers must be positive and bootstrap draws must be >=100")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen confirmation protocol not found: {protocol}")
    calibration, calibration_hash = _verify_null_calibration(calibration_manifest)
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
                            f"eventwise-temporal-confirm cell={_cell_name(schedule, signal, proxy_error)} "
                            f"seeds={seeds} device={resolved_device} workers={workers}",
                            flush=True,
                        )
                        records.extend(
                            _run_cell(
                                seeds=seeds,
                                seed_offset=seed_offset,
                                config=config,
                                device=resolved_device,
                                schedule=schedule,
                                signal=signal,
                                proxy_error=proxy_error,
                                executor=executor,
                            )
                        )
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
        raise RuntimeError("duplicate cell/seed/method rows in confirmation")
    counts = detail.groupby(["scenario", "budget_rate", "alpha_allocation"]).size()
    if len(counts) != FAMILY_CELLS * len(METHODS) or not counts.eq(seeds).all():
        raise RuntimeError("confirmation has missing cell/method/seed rows")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("confirmation streams require positive query support")
    detail["cap_violation"] = detail["labels_queried"] > detail["label_budget"]
    cap_violations = int(detail["cap_violation"].sum())
    if cap_violations:
        raise RuntimeError("confirmation exceeded a realized hard label cap")
    if not np.isfinite(detail["expected_postpromotion_net_gain"].to_numpy(dtype=float)).all():
        raise RuntimeError("confirmation contains non-finite evaluator utility")

    contrasts, confirmation_pass = _paired_contrasts(
        detail, draws=bootstrap_draws, seed=BOOTSTRAP_SEED
    )
    status = (
        "confirmed_on_registered_grid"
        if seeds >= MIN_SEEDS and confirmation_pass
        else ("not_confirmed_on_registered_grid" if seeds >= MIN_SEEDS else "smoke_only")
    )
    summary = detail.groupby(
        [
            "scenario",
            "context_prevalence_schedule",
            "budget_rate",
            "alpha_allocation",
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
    detail.to_parquet(metrics_dir / "eventwise_temporal_confirmation_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "eventwise_temporal_confirmation_cells.parquet", index=False)
    contrasts.to_parquet(
        metrics_dir / "eventwise_temporal_confirmation_contrasts.parquet", index=False
    )

    protocol_hash = hashlib.sha256(protocol.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    report_path = reports_dir / "eventwise_temporal_confirmation.md"
    report = [
        "# Eventwise-scout confirmation under gradual and recurring contexts",
        "",
        (
            f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: "
            f"{seed_offset}–{seed_offset + seeds - 1}; workers: {workers}."
        ),
        "",
        (
            f"The matched grid contains {FAMILY_CELLS} positive-signal cells, {len(METHODS)} methods, "
            f"and {len(detail):,} method-cell-seed rows. The endpoint is evaluator-known expected "
            "postpromotion net decision gain, equally weighted over cells and paired by seed cluster."
        ),
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        (
            "The primary comparisons are eventwise versus pooled rank and nested context-volume. "
            "Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation "
            "for approximate simultaneous 95% familywise assessment. The primary gate passes only "
            "when both limits exceed zero; this bootstrap coverage is approximate, not an exact "
            "finite-sample guarantee. The minimum-bound comparison is secondary."
        ),
        "",
        (
            f"Integrity: all expected unique rows present; positive propensities verified; "
            f"{cap_violations} cap violations; "
            f"{int(detail.harmful_postpromotion_promotion.sum())} harmful promotions by "
            "evaluator-known future utility. Results apply only to the frozen synthetic grid and "
            "feedback design."
        ),
        "",
        f"Frozen protocol: {protocol.as_posix()} (normalized SHA-256 {protocol_hash}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_eventwise_context_temporal_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "protocol": {"path": protocol.as_posix(), "normalized_sha256": protocol_hash},
        "prerequisite_null_calibration": {
            "path": calibration_manifest.as_posix(),
            "normalized_manifest_sha256": calibration_hash,
            "status": calibration["status"],
            "familywise_alpha": calibration["inference"]["familywise_alpha"],
            "simultaneous_cells": calibration["inference"]["simultaneous_cells"],
        },
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
            "query_policy": "uniform",
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "alpha": 0.05,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "inference": {
            "primary_comparisons": contrasts.to_dict(orient="records"),
            "primary_gate_pass": confirmation_pass,
            "total_rows": len(detail),
            "cap_violations": cap_violations,
            "positive_propensities": True,
            "all_expected_rows_present": True,
            "harmful_promotions": int(detail.harmful_postpromotion_promotion.sum()),
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/eventwise_temporal_confirmation_streams.parquet",
            "metrics/eventwise_temporal_confirmation_cells.parquet",
            "metrics/eventwise_temporal_confirmation_contrasts.parquet",
            "reports/eventwise_temporal_confirmation.md",
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
        default=Path("outputs/scout_context_policy_eventwise_temporal_confirmation_600"),
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_temporal_confirmation_protocol.md"),
    )
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path(
            "outputs/scout_context_policy_eventwise_temporal_null_1000/reports/manifest.json"
        ),
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
            calibration_manifest=args.calibration_manifest,
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
