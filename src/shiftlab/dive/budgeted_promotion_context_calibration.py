"""Independent null calibration for target-scout contextual promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from scipy.stats import beta

from ..data.gpu.environment import environment, resolve_device
from .budgeted_promotion import BudgetedPromotionConfig, _run_seed
from .experiment import finalize_manifest

PREVALENCES = (0.10, 0.50, 0.90)
PROXY_ERRORS = (0.0, 0.10, 0.25)
SWITCHING_COSTS = (0.0, 0.05)
BUDGET_RATES = (0.20, 0.40)
CALIBRATION_SEED_OFFSET = 20_261_300
DEVELOPMENT_SEED_END = 20_261_260
FAMILY_ALPHA = 0.05
FAMILY_CELLS = len(PREVALENCES) * len(PROXY_ERRORS) * len(SWITCHING_COSTS) * len(BUDGET_RATES)
MIN_CALIBRATION_SEEDS = 1_000


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials or not 0 < alpha < 1:
        raise ValueError("Clopper-Pearson inputs are outside their valid ranges")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def _profile_name(prevalence: float, error: float, switching_cost: float) -> str:
    return (
        f"context_p{round(100 * prevalence):02d}_error{round(100 * error):02d}_"
        f"switch{round(100 * switching_cost):02d}"
    )


def run_calibration(
    *,
    output: Path,
    seeds: int = MIN_CALIBRATION_SEEDS,
    seed_offset: int = CALIBRATION_SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    protocol: Path,
) -> Path:
    """Run all 36 registered null cells on independent, matched seeds."""
    if seeds < 2 or n < 1000 or d < 3:
        raise ValueError("calibration requires seeds >=2, n >=1000, and d >=3")
    if seed_offset <= DEVELOPMENT_SEED_END:
        raise ValueError("calibration seed block must be disjoint from scout development")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen calibration protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite existing calibration output: {output}")
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    records: list[dict[str, object]] = []
    for prevalence in PREVALENCES:
        for proxy_error in PROXY_ERRORS:
            print(
                f"scout-null profile=p{round(100 * prevalence):02d}_error{round(100 * proxy_error):02d} seeds={seeds} device={resolved_device}",
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
                context_target_prevalence=prevalence,
                context_signal_strength=0.0,
                context_proxy_error=proxy_error,
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
                    scout_only=True,
                    scout_switching_costs=SWITCHING_COSTS,
                )
                scout_rows = [
                    row for row in seed_rows if row["alpha_allocation"] == "scout_context_policy"
                ]
                if len(scout_rows) != len(BUDGET_RATES) * len(SWITCHING_COSTS):
                    raise RuntimeError(
                        "scout-only run did not return one row per cap and switching charge"
                    )
                for row in scout_rows:
                    switching_cost = float(row["registered_switching_cost"])
                    row["scenario"] = _profile_name(prevalence, proxy_error, switching_cost)
                    row["context_target_prevalence"] = prevalence
                    row["context_signal_strength"] = 0.0
                    row["context_proxy_error"] = proxy_error
                    row["seed"] = seed
                    if not bool(row["candidate_is_monitor_null"]):
                        raise RuntimeError("registered zero-signal profile violated the null")
                    if float(row["q_min"]) <= 0:
                        raise RuntimeError("calibration requires positive query propensities")
                    records.append(row)

    detail = pd.DataFrame.from_records(records)
    expected_rows = (
        seeds * len(PREVALENCES) * len(PROXY_ERRORS) * len(SWITCHING_COSTS) * len(BUDGET_RATES)
    )
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} calibration rows, received {len(detail)}")
    if detail.duplicated(["scenario", "budget_rate", "seed"]).any():
        raise RuntimeError("duplicate profile/cap/seed rows in calibration output")

    cell_alpha = FAMILY_ALPHA / FAMILY_CELLS
    rows: list[dict[str, object]] = []
    for (profile, budget_rate), group in detail.groupby(["scenario", "budget_rate"], sort=True):
        events = int(group["promoted"].sum())
        trials = len(group)
        upper = _cp_upper(events, trials, cell_alpha)
        cap_violations = int((group["labels_queried"] > group["label_budget"]).sum())
        rows.append(
            {
                "scenario": profile,
                "budget_rate": float(budget_rate),
                "switching_cost": float(group["registered_switching_cost"].iloc[0]),
                "context_target_prevalence": float(group["context_target_prevalence"].iloc[0]),
                "context_proxy_error": float(group["context_proxy_error"].iloc[0]),
                "signal_strength": 0.0,
                "false_promotions": events,
                "streams": trials,
                "observed_false_promotion_rate": events / trials,
                "simultaneous_one_sided_alpha": cell_alpha,
                "simultaneous_cp95_upper": upper,
                "cap_violations": cap_violations,
                "cell_pass": trials >= MIN_CALIBRATION_SEEDS
                and upper <= FAMILY_ALPHA
                and cap_violations == 0,
            }
        )
    summary = pd.DataFrame(rows)
    all_caps_respected = bool(summary["cap_violations"].eq(0).all())
    full_design = seeds >= MIN_CALIBRATION_SEEDS
    passed = bool(full_design and summary["cell_pass"].all() and all_caps_respected)
    status = "passed" if passed else "failed" if full_design else "smoke_only_not_calibration"

    detail_path = metrics_dir / "scout_context_policy_null_streams.parquet"
    summary_path = metrics_dir / "scout_context_policy_null_summary.parquet"
    detail.to_parquet(detail_path, index=False)
    summary.to_parquet(summary_path, index=False)
    report_path = reports_dir / "scout_context_policy_null_calibration.md"
    report = [
        "# Target-scout contextual policy null calibration",
        "",
        f"Status: **{status}**. Device: `{resolved_device}`; seeds: `{seeds}` per cell; seed block: `{seed_offset}`–`{seed_offset + seeds - 1}`.",
        "",
        f"The frozen family has {FAMILY_CELLS} cells: nine prevalence/proxy profiles, two switching charges (0.00 least-favorable boundary and 0.05 registered charge), and two realized label caps (20%/40%). Each cell uses one-sided exact Clopper–Pearson alpha 0.05/{FAMILY_CELLS}={cell_alpha:.8f}, giving simultaneous 95% Bonferroni coverage. Passing requires at least {MIN_CALIBRATION_SEEDS} streams/cell, upper bound no greater than 0.05 in every cell, and no hard-cap breach.",
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The DGP has stochastic outcomes and query decisions. At signal delta zero, every candidate has zero gross expected benefit within each true context; the 0.00 switching-charge cells exercise the boundary null, and 0.05 makes selected interventions weakly harmful. The selected map is frozen before the certification half. These finite results complement, but do not replace, the conditional supermartingale argument. They apply only to the registered IID synthetic process, known positive uniform query propensity, bounded paired costs, fixed candidate family, context proxy, alpha, and caps.",
        "",
        f"Frozen protocol: [`{protocol.as_posix()}`](../../../{protocol.as_posix()}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_context_policy_independent_null_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "protocol": {
            "path": protocol.as_posix(),
            "sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        },
        "configuration": {
            "seeds_per_profile": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "prevalences": PREVALENCES,
            "signal_strengths": [0.0],
            "proxy_errors": PROXY_ERRORS,
            "switching_costs": SWITCHING_COSTS,
            "budget_rates": BUDGET_RATES,
            "query_policy": "uniform",
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "alpha": 0.05,
            "selection_rule": "first half of target monitor; candidate map frozen for certification half",
        },
        "inference": {
            "familywise_alpha": FAMILY_ALPHA,
            "simultaneous_cells": FAMILY_CELLS,
            "per_cell_one_sided_alpha": cell_alpha,
            "minimum_streams_per_cell": MIN_CALIBRATION_SEEDS,
            "calibration_pass": passed,
            "all_caps_respected": all_caps_respected,
            "false_promotions": int(summary.false_promotions.sum()),
            "independent_of_development_seed_blocks": seed_offset > DEVELOPMENT_SEED_END,
            "development_seed_end": DEVELOPMENT_SEED_END,
            "figure_generated": False,
            "assumptions": [
                "IID synthetic events under the registered generator",
                "known strictly positive uniform query propensities",
                "bounded paired decision-cost increments",
                "candidate policy selected on a disjoint scout slice and fixed during certification",
                "aggregate history-conditional expected net gain is nonpositive under every registered null cell",
            ],
            "limitations": [
                "finite Monte Carlo evidence does not replace the supermartingale proof",
                "no evidence for serial dependence, delayed labels, selective feedback, unregistered contexts, or real-world validity",
            ],
        },
        "artifacts": [
            "metrics/scout_context_policy_null_streams.parquet",
            "metrics/scout_context_policy_null_summary.parquet",
            "reports/scout_context_policy_null_calibration.md",
        ],
        "environment": environment(),
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    print(report_path, flush=True)
    return report_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/scout_context_policy_null_calibration_1000")
    )
    parser.add_argument("--seeds", type=int, default=MIN_CALIBRATION_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=CALIBRATION_SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_null_calibration_protocol.md"),
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
            protocol=args.protocol,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
