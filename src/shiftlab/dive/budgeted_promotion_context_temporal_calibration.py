"""Calibrate eventwise-scout false promotions under gradual and recurring contexts."""

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

import pandas as pd
from scipy.stats import beta

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import BudgetedPromotionConfig, _run_seed
from .experiment import finalize_manifest

SCHEDULES = (
    "gradual_up",
    "gradual_down",
    "recurring_low_first",
    "recurring_high_first",
)
PROXY_ERRORS = (0.0, 0.25)
BUDGET_RATES = (0.20, 0.40)
SWITCHING_COST = 0.05
SEED_OFFSET = 20_275_000
MIN_SEEDS = 1_000
FAMILY_ALPHA = 0.05
FAMILY_CELLS = len(SCHEDULES) * len(PROXY_ERRORS) * len(BUDGET_RATES)
EVENTWISE_METHOD = "scout_context_policy_eventwise_propensity_bound"
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity",
    fn_cost=5.0,
    fp_cost=1.0,
    harmful_adaptation=False,
)


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials or not 0 < alpha < 1:
        raise ValueError("Clopper-Pearson inputs are outside their valid ranges")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def _profile_name(schedule: str, proxy_error: float) -> str:
    return f"{schedule}_error{round(100 * proxy_error):02d}"


def _run_null_seed(
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    schedule: str,
    proxy_error: float,
) -> list[dict[str, object]]:
    rows = _run_seed(
        scenario=SCENARIO,
        seed=seed,
        config=config,
        device=device,
        scout_only=True,
        scout_bound_modes=("eventwise_propensity",),
    )
    selected = [row for row in rows if row["alpha_allocation"] == EVENTWISE_METHOD]
    if len(selected) != len(BUDGET_RATES):
        raise RuntimeError("temporal calibration stream is missing a label-cap result")
    for row in selected:
        row["scenario"] = _profile_name(schedule, proxy_error)
        row["context_prevalence_schedule"] = schedule
        row["context_signal_strength"] = 0.0
        row["context_proxy_error"] = proxy_error
        row["registered_switching_cost"] = SWITCHING_COST
        row["seed"] = seed
        if not bool(row["candidate_is_monitor_null"]):
            raise RuntimeError("temporal calibration stream violated the evaluator null")
    return selected


def _run_profile(
    *,
    seeds: int,
    seed_offset: int,
    config: BudgetedPromotionConfig,
    device: str,
    schedule: str,
    proxy_error: float,
    executor: ProcessPoolExecutor | None,
) -> list[dict[str, object]]:
    if executor is None:
        return [
            row
            for replicate in range(seeds)
            for row in _run_null_seed(
                seed_offset + replicate, config, device, schedule, proxy_error
            )
        ]
    futures = {
        executor.submit(
            _run_null_seed,
            seed_offset + replicate,
            config,
            device,
            schedule,
            proxy_error,
        ): replicate
        for replicate in range(seeds)
    }
    by_replicate: list[list[dict[str, object]] | None] = [None] * seeds
    for completed, future in enumerate(as_completed(futures), start=1):
        by_replicate[futures[future]] = future.result()
        if completed % 100 == 0 or completed == seeds:
            print(
                f"eventwise-temporal-null progress={completed}/{seeds} "
                f"profile={_profile_name(schedule, proxy_error)}",
                flush=True,
            )
    if any(rows is None for rows in by_replicate):
        raise RuntimeError("temporal null profile is missing seed results")
    return [row for rows in by_replicate if rows is not None for row in rows]


def run_calibration(
    *,
    output: Path,
    protocol: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    workers: int = 6,
) -> Path:
    if seeds < 2 or seed_offset < 0 or n < 1000 or d < 3:
        raise ValueError("calibration requires >=2 nonnegative seeds, n>=1000, and d>=3")
    if seeds >= MIN_SEEDS and seed_offset != SEED_OFFSET:
        raise ValueError("full calibration runs must use the frozen disjoint seed block")
    if workers < 1:
        raise ValueError("workers must be positive")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen calibration protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite calibration output: {output}")
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
                for proxy_error in PROXY_ERRORS:
                    profile = _profile_name(schedule, proxy_error)
                    print(
                        f"eventwise-temporal-null profile={profile} seeds={seeds} "
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
                        alpha_allocations=("rank",),
                        estimators=("direct_ipw",),
                        monitoring_rules=("fixed_mixture",),
                        bound_mode="global",
                        context_feature_index=d - 1,
                        context_threshold=0.0,
                        context_target_prevalence=0.5,
                        context_signal_strength=0.0,
                        context_proxy_error=proxy_error,
                        context_prevalence_schedule=schedule,
                        include_scout_context_policy=True,
                        scenario_subset=("candidate_context_heterogeneity",),
                        create_plot=False,
                        device=resolved_device,
                    ).validate()
                    records.extend(
                        _run_profile(
                            seeds=seeds,
                            seed_offset=seed_offset,
                            config=config,
                            device=resolved_device,
                            schedule=schedule,
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
    expected_rows = seeds * FAMILY_CELLS
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} calibration rows; received {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate temporal calibration cell/seed rows")
    if not detail["candidate_is_monitor_null"].astype(bool).all():
        raise RuntimeError("one or more calibration streams failed the evaluator null check")
    if detail["propensity_min"].isna().any() or not detail["propensity_min"].gt(0).all():
        raise RuntimeError("calibration streams require positive query support")
    detail["cap_violation"] = detail["labels_queried"] > detail["label_budget"]
    family_cell_alpha = FAMILY_ALPHA / FAMILY_CELLS
    cell_rows = []
    for (profile, budget_rate), group in detail.groupby(["scenario", "budget_rate"], sort=True):
        events = int(group["promoted"].sum())
        trials = len(group)
        cap_violations = int(group["cap_violation"].sum())
        upper = _cp_upper(events, trials, family_cell_alpha)
        cell_rows.append(
            {
                "scenario": profile,
                "context_prevalence_schedule": str(group["context_prevalence_schedule"].iloc[0]),
                "budget_rate": float(budget_rate),
                "context_signal_strength": 0.0,
                "context_proxy_error": float(group["context_proxy_error"].iloc[0]),
                "switching_cost": SWITCHING_COST,
                "false_promotions": events,
                "streams": trials,
                "observed_false_promotion_rate": events / trials,
                "simultaneous_one_sided_alpha": family_cell_alpha,
                "simultaneous_cp95_upper": upper,
                "cap_violations": cap_violations,
                "cell_pass": (
                    trials >= MIN_SEEDS and upper <= FAMILY_ALPHA and cap_violations == 0
                ),
            }
        )
    summary = pd.DataFrame(cell_rows)
    full_design = seeds >= MIN_SEEDS
    caps_ok = bool(summary["cap_violations"].eq(0).all())
    nulls_ok = bool(detail["candidate_is_monitor_null"].astype(bool).all())
    passed = bool(full_design and summary["cell_pass"].all() and caps_ok and nulls_ok)
    status = "passed" if passed else "failed" if full_design else "smoke_only_not_calibration"

    detail.to_parquet(metrics_dir / "eventwise_temporal_null_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "eventwise_temporal_null_summary.parquet", index=False)
    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "eventwise_temporal_null_calibration.md"
    report = [
        "# Eventwise-scout null calibration under gradual and recurring contexts",
        "",
        (
            f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: "
            f"{seed_offset}–{seed_offset + seeds - 1}; workers: {workers}."
        ),
        "",
        (
            f"The family has {FAMILY_CELLS} cells and {len(detail):,} eventwise stream records. It "
            f"crosses four deterministic prevalence schedules, two proxy-error levels, and two hard "
            f"label caps. Simultaneous one-sided exact Clopper–Pearson limits use per-cell alpha "
            f"0.05/{FAMILY_CELLS}={family_cell_alpha:.8f}; each cell requires at least {MIN_SEEDS} "
            "streams, upper limit at most 0.05, and zero cap violations."
        ),
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        (
            f"Integrity: {len(detail):,}/{expected_rows:,} expected unique rows; evaluator nulls "
            f"verified: {nulls_ok}; positive propensity support: "
            f"{bool(detail.propensity_min.gt(0).all())}; cap violations: "
            f"{int(detail.cap_violation.sum())}; family gate: {passed}."
        ),
        "",
        (
            "This is finite calibration evidence for the registered event-conditional null and "
            "eventwise rule. It does not extend to delayed/selective feedback, adaptive propensities, or "
            "other outcome processes. No figure was generated."
        ),
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {protocol_hash}).",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_eventwise_context_temporal_null_calibration",
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
            "signal_strength": 0.0,
            "proxy_errors": PROXY_ERRORS,
            "switching_cost": SWITCHING_COST,
            "budget_rates": BUDGET_RATES,
            "method": EVENTWISE_METHOD,
            "query_policy": "uniform",
            "alpha": FAMILY_ALPHA,
        },
        "inference": {
            "familywise_alpha": FAMILY_ALPHA,
            "simultaneous_cells": FAMILY_CELLS,
            "per_cell_one_sided_alpha": family_cell_alpha,
            "minimum_streams_per_cell": MIN_SEEDS,
            "calibration_pass": passed,
            "all_caps_respected": caps_ok,
            "conditional_null_verified": nulls_ok,
            "false_promotions": int(summary.false_promotions.sum()),
            "cap_violations": int(detail.cap_violation.sum()),
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/eventwise_temporal_null_streams.parquet",
            "metrics/eventwise_temporal_null_summary.parquet",
            "reports/eventwise_temporal_null_calibration.md",
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
        default=Path("outputs/scout_context_policy_eventwise_temporal_null_1000"),
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_eventwise_temporal_null_protocol.md"),
    )
    args = parser.parse_args(argv)
    print(
        run_calibration(
            output=args.output,
            protocol=args.protocol,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            workers=args.workers,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
