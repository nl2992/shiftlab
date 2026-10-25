"""Calibrate target-scout promotion under abrupt context-prevalence drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from scipy.stats import beta

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import SCOUT_BOUND_MODES, BudgetedPromotionConfig, _run_seed
from .experiment import finalize_manifest

PREVALENCE_PAIRS = ((0.10, 0.90), (0.50, 0.50), (0.90, 0.10))
PROXY_ERRORS = (0.0, 0.25)
SWITCHING_COSTS = (0.0, 0.05)
BUDGET_RATES = (0.20, 0.40)
SEED_OFFSET = 20_267_000
DEVELOPMENT_SEED_END = 20_266_999
FAMILY_ALPHA = 0.05
FAMILY_CELLS = len(PREVALENCE_PAIRS) * len(PROXY_ERRORS) * len(SWITCHING_COSTS) * len(BUDGET_RATES)
MIN_SEEDS = 1_000


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials or not 0 < alpha < 1:
        raise ValueError("Clopper-Pearson inputs are outside their valid ranges")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def _profile_name(
    initial_prevalence: float, final_prevalence: float, proxy_error: float, switching_cost: float
) -> str:
    return (
        f"drift_p{round(100 * initial_prevalence):02d}_to_{round(100 * final_prevalence):02d}_"
        f"error{round(100 * proxy_error):02d}_switch{round(100 * switching_cost):02d}"
    )


def _run_calibration_replicate(
    seed: int,
    config: BudgetedPromotionConfig,
    device: str,
    fn_cost: float,
    fp_cost: float,
) -> list[dict[str, object]]:
    """Run one seed independently using only its explicit seed-derived generators."""
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=fn_cost,
        fp_cost=fp_cost,
        harmful_adaptation=False,
    )
    return _run_seed(
        scenario=scenario,
        seed=seed,
        config=config,
        device=device,
        scout_only=True,
        scout_switching_costs=SWITCHING_COSTS,
    )


def run_calibration(
    *,
    output: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    bound_mode: str = "minimum_propensity",
    workers: int = 1,
    protocol: Path,
) -> Path:
    if seeds < 2 or n < 1000 or d < 3 or workers < 1:
        raise ValueError("calibration requires seeds >=2, n >=1000, and d >=3")
    if seed_offset <= DEVELOPMENT_SEED_END:
        raise ValueError("drift calibration seeds must follow the frozen development block")
    if bound_mode not in SCOUT_BOUND_MODES:
        raise ValueError(f"bound_mode must be one of {SCOUT_BOUND_MODES}")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen protocol not found: {protocol}")
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

    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    records: list[dict[str, object]] = []
    for initial_prevalence, final_prevalence in PREVALENCE_PAIRS:
        for proxy_error in PROXY_ERRORS:
            print(
                f"drift-null profile=p{round(100 * initial_prevalence):02d}"
                f"_to_{round(100 * final_prevalence):02d}"
                f"_error{round(100 * proxy_error):02d} seeds={seeds} device={resolved_device}",
                flush=True,
            )
            config = BudgetedPromotionConfig(
                n=n,
                d=d,
                seeds=1,
                seed_offset=seed_offset,
                switching_cost=0.0,
                budget_rates=BUDGET_RATES,
                query_policies=("uniform",),
                alpha_allocations=("rank",),
                estimators=("direct_ipw",),
                monitoring_rules=("fixed_mixture",),
                bound_mode="global",
                context_feature_index=d - 1,
                context_threshold=0.0,
                context_target_prevalence=initial_prevalence,
                context_signal_strength=0.0,
                context_proxy_error=proxy_error,
                context_persistence=0.0,
                context_certification_prevalence=final_prevalence,
                scout_bound_mode=bound_mode,
                include_scout_context_policy=True,
                scenario_subset=("candidate_context_heterogeneity",),
                create_plot=False,
                device=resolved_device,
            )
            config.validate()
            seed_results: list[list[dict[str, object]] | None] = [None] * seeds
            if workers == 1:
                for replicate in range(seeds):
                    seed_results[replicate] = _run_calibration_replicate(
                        seed_offset + replicate,
                        config,
                        resolved_device,
                        scenario.fn_cost,
                        scenario.fp_cost,
                    )
            else:
                thread_variables = (
                    "OPENBLAS_NUM_THREADS",
                    "OMP_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
                previous_thread_limits = {key: os.environ.get(key) for key in thread_variables}
                os.environ.update({key: "1" for key in thread_variables})
                try:
                    with ProcessPoolExecutor(max_workers=workers) as executor:
                        futures = {
                            executor.submit(
                                _run_calibration_replicate,
                                seed_offset + replicate,
                                config,
                                resolved_device,
                                scenario.fn_cost,
                                scenario.fp_cost,
                            ): replicate
                            for replicate in range(seeds)
                        }
                        for completed, future in enumerate(as_completed(futures), start=1):
                            seed_results[futures[future]] = future.result()
                            if completed % 100 == 0 or completed == seeds:
                                print(
                                    f"drift-null progress={completed}/{seeds} "
                                    f"profile=p{round(100 * initial_prevalence):02d}"
                                    f"_to_{round(100 * final_prevalence):02d}"
                                    f"_error{round(100 * proxy_error):02d}",
                                    flush=True,
                                )
                finally:
                    for key, value in previous_thread_limits.items():
                        if value is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = value

            for replicate, seed_rows in enumerate(seed_results):
                if seed_rows is None:
                    raise RuntimeError(f"missing result for calibration replicate {replicate}")
                seed = seed_offset + replicate
                scout_rows = [
                    row
                    for row in seed_rows
                    if row["alpha_allocation"]
                    == (
                        "scout_context_policy"
                        if bound_mode == "minimum_propensity"
                        else "scout_context_policy_eventwise_propensity_bound"
                    )
                ]
                expected_per_seed = len(BUDGET_RATES) * len(SWITCHING_COSTS)
                if len(scout_rows) != expected_per_seed:
                    raise RuntimeError("scout run did not return every cap and switching charge")
                for row in scout_rows:
                    switching_cost = float(row["registered_switching_cost"])
                    row["scenario"] = _profile_name(
                        initial_prevalence, final_prevalence, proxy_error, switching_cost
                    )
                    row["context_initial_prevalence"] = initial_prevalence
                    row["context_certification_prevalence"] = final_prevalence
                    row["context_signal_strength"] = 0.0
                    row["context_proxy_error"] = proxy_error
                    row["context_persistence"] = 0.0
                    row["scout_bound_mode"] = bound_mode
                    row["seed"] = seed
                    if not bool(row["candidate_is_monitor_null"]):
                        raise RuntimeError(
                            "zero-signal drift profile violated the conditional null"
                        )
                    if row["propensity_min"] is None or float(row["propensity_min"]) <= 0:
                        raise RuntimeError("certification query support must be positive")
                    records.append(row)

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * FAMILY_CELLS
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows; received {len(detail)}")
    if detail.duplicated(["scenario", "budget_rate", "seed"]).any():
        raise RuntimeError("duplicate scenario/cap/seed rows")
    cell_alpha = FAMILY_ALPHA / FAMILY_CELLS
    summary_rows: list[dict[str, object]] = []
    for (profile, budget_rate), group in detail.groupby(["scenario", "budget_rate"], sort=True):
        events = int(group["promoted"].sum())
        trials = len(group)
        cap_violations = int((group["labels_queried"] > group["label_budget"]).sum())
        upper = _cp_upper(events, trials, cell_alpha)
        summary_rows.append(
            {
                "scenario": profile,
                "budget_rate": float(budget_rate),
                "switching_cost": float(group["registered_switching_cost"].iloc[0]),
                "context_initial_prevalence": float(group["context_initial_prevalence"].iloc[0]),
                "context_certification_prevalence": float(
                    group["context_certification_prevalence"].iloc[0]
                ),
                "context_proxy_error": float(group["context_proxy_error"].iloc[0]),
                "false_promotions": events,
                "streams": trials,
                "observed_false_promotion_rate": events / trials,
                "simultaneous_one_sided_alpha": cell_alpha,
                "simultaneous_cp95_upper": upper,
                "cap_violations": cap_violations,
                "cell_pass": trials >= MIN_SEEDS and upper <= FAMILY_ALPHA and cap_violations == 0,
            }
        )
    summary = pd.DataFrame(summary_rows)
    full_design = seeds >= MIN_SEEDS
    caps_ok = bool(summary["cap_violations"].eq(0).all())
    passed = bool(full_design and summary["cell_pass"].all() and caps_ok)
    status = "passed" if passed else "failed" if full_design else "smoke_only_not_calibration"

    detail.to_parquet(metrics_dir / "scout_context_drift_null_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "scout_context_drift_null_summary.parquet", index=False)
    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report_path = reports_dir / "scout_context_drift_null_calibration.md"
    report = [
        "# Target-scout null calibration under abrupt context-prevalence drift",
        "",
        (
            f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; "
            f"seed block: {seed_offset}–{seed_offset + seeds - 1}; worker processes: {workers}."
        ),
        "",
        (
            f"The family has {FAMILY_CELLS} cells: three pre/post prevalence pairs, two proxy-error "
            "levels, two switching charges, and two caps. Each cell uses simultaneous one-sided exact "
            f"Clopper–Pearson alpha 0.05/{FAMILY_CELLS}={cell_alpha:.8f}; passing requires at least "
            f"{MIN_SEEDS} streams and an upper limit at most 0.05."
        ),
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        (
            "At signal delta zero, the outcome probability remains at the decision threshold at every "
            "event and in every context, including after the abrupt prevalence change. Thus the "
            "eventwise conditional expected gross candidate gain is zero. The finite calibration "
            f"Bound mode: {bound_mode}. The eventwise mode uses the registered uniform query probability "
            "and the same eventwise conditional-mean null. This finite calibration addresses this "
            "registered context-distribution shift only; it does not cover delayed or "
            "selective feedback, shifts that violate the conditional null, or real applications."
        ),
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {protocol_hash}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": f"target_scout_context_drift_null_calibration_{bound_mode}",
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
            "bound_mode": bound_mode,
            "prevalence_pairs": PREVALENCE_PAIRS,
            "signal_strength": 0.0,
            "proxy_errors": PROXY_ERRORS,
            "switching_costs": SWITCHING_COSTS,
            "budget_rates": BUDGET_RATES,
            "alpha": FAMILY_ALPHA,
        },
        "inference": {
            "familywise_alpha": FAMILY_ALPHA,
            "simultaneous_cells": FAMILY_CELLS,
            "per_cell_one_sided_alpha": cell_alpha,
            "minimum_streams_per_cell": MIN_SEEDS,
            "calibration_pass": passed,
            "all_caps_respected": caps_ok,
            "false_promotions": int(summary.false_promotions.sum()),
            "conditional_null_verified": bool(detail.candidate_is_monitor_null.all()),
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/scout_context_drift_null_streams.parquet",
            "metrics/scout_context_drift_null_summary.parquet",
            "reports/scout_context_drift_null_calibration.md",
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
        "--output", type=Path, default=Path("outputs/scout_context_policy_drift_null_1000")
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument(
        "--workers",
        type=int,
        default=min(6, os.cpu_count() or 1),
        help="independent seed worker processes; use 1 for serial execution",
    )
    parser.add_argument("--bound-mode", choices=SCOUT_BOUND_MODES, default="minimum_propensity")
    parser.add_argument(
        "--protocol", type=Path, default=Path("docs/scout_context_policy_drift_null_protocol.md")
    )
    args = parser.parse_args(argv)
    print(
        run_calibration(
            output=args.output,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            bound_mode=args.bound_mode,
            workers=args.workers,
            protocol=args.protocol,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
