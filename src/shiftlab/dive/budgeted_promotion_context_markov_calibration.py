"""Null calibration of target-scout promotion under persistent contexts."""

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
PROXY_ERRORS = (0.0, 0.25)
SWITCHING_COSTS = (0.0, 0.05)
BUDGET_RATES = (0.20, 0.40)
PERSISTENCE = 0.80
SEED_OFFSET = 20_265_000
DEVELOPMENT_SEED_END = 20_264_599
FAMILY_ALPHA = 0.05
FAMILY_CELLS = len(PREVALENCES) * len(PROXY_ERRORS) * len(SWITCHING_COSTS) * len(BUDGET_RATES)
MIN_SEEDS = 1_000


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials or not 0 < alpha < 1:
        raise ValueError("Clopper-Pearson inputs are outside their valid ranges")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def _profile_name(prevalence: float, proxy_error: float, switching_cost: float) -> str:
    return (
        f"markov_p{round(100 * prevalence):02d}_error{round(100 * proxy_error):02d}_"
        f"switch{round(100 * switching_cost):02d}"
    )


def run_calibration(
    *,
    output: Path,
    seeds: int = MIN_SEEDS,
    seed_offset: int = SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    protocol: Path,
) -> Path:
    if seeds < 2 or n < 1000 or d < 3:
        raise ValueError("calibration requires seeds >=2, n >=1000, and d >=3")
    if seed_offset <= DEVELOPMENT_SEED_END:
        raise ValueError("Markov calibration seeds must follow prior confirmation")
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
    for prevalence in PREVALENCES:
        for proxy_error in PROXY_ERRORS:
            print(
                f"markov-null profile=p{round(100 * prevalence):02d}_error{round(100 * proxy_error):02d} "
                f"seeds={seeds} device={resolved_device}",
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
                context_persistence=PERSISTENCE,
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
                    raise RuntimeError("scout run did not return every cap and switching charge")
                for row in scout_rows:
                    switching_cost = float(row["registered_switching_cost"])
                    row["scenario"] = _profile_name(prevalence, proxy_error, switching_cost)
                    row["context_target_prevalence"] = prevalence
                    row["context_signal_strength"] = 0.0
                    row["context_proxy_error"] = proxy_error
                    row["context_persistence"] = PERSISTENCE
                    row["seed"] = seed
                    if not bool(row["candidate_is_monitor_null"]):
                        raise RuntimeError("Markov zero-signal profile violated the aggregate null")
                    records.append(row)

    detail = pd.DataFrame.from_records(records)
    expected_rows = seeds * FAMILY_CELLS
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows; received {len(detail)}")
    if detail.duplicated(["scenario", "budget_rate", "seed"]).any():
        raise RuntimeError("duplicate scenario/cap/seed rows")
    cell_alpha = FAMILY_ALPHA / FAMILY_CELLS
    rows: list[dict[str, object]] = []
    for (profile, budget_rate), group in detail.groupby(["scenario", "budget_rate"], sort=True):
        events = int(group["promoted"].sum())
        trials = len(group)
        cap_violations = int((group["labels_queried"] > group["label_budget"]).sum())
        upper = _cp_upper(events, trials, cell_alpha)
        rows.append(
            {
                "scenario": profile,
                "budget_rate": float(budget_rate),
                "switching_cost": float(group["registered_switching_cost"].iloc[0]),
                "context_target_prevalence": float(group["context_target_prevalence"].iloc[0]),
                "context_proxy_error": float(group["context_proxy_error"].iloc[0]),
                "context_persistence": PERSISTENCE,
                "false_promotions": events,
                "streams": trials,
                "observed_false_promotion_rate": events / trials,
                "simultaneous_one_sided_alpha": cell_alpha,
                "simultaneous_cp95_upper": upper,
                "cap_violations": cap_violations,
                "cell_pass": trials >= MIN_SEEDS and upper <= FAMILY_ALPHA and cap_violations == 0,
            }
        )
    summary = pd.DataFrame(rows)
    full_design = seeds >= MIN_SEEDS
    caps_ok = bool(summary["cap_violations"].eq(0).all())
    passed = bool(full_design and summary["cell_pass"].all() and caps_ok)
    status = "passed" if passed else "failed" if full_design else "smoke_only_not_calibration"

    detail.to_parquet(metrics_dir / "scout_context_markov_null_streams.parquet", index=False)
    summary.to_parquet(metrics_dir / "scout_context_markov_null_summary.parquet", index=False)
    report_path = reports_dir / "scout_context_markov_null_calibration.md"
    report = [
        "# Target-scout null calibration under persistent contexts",
        "",
        f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: {seed_offset}–{seed_offset + seeds - 1}.",
        "",
        f"The family has {FAMILY_CELLS} cells: three stationary latent prevalences, two proxy-error levels, two switching charges, and two caps. Target context is generated by a stationary two-state Markov chain with persistence {PERSISTENCE:.2f}. Each cell uses simultaneous one-sided exact Clopper–Pearson alpha 0.05/{FAMILY_CELLS}={cell_alpha:.8f}; passing requires at least {MIN_SEEDS} streams and an upper limit at most 0.05.",
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "At signal delta zero, the label probability remains at the decision threshold at every event and in every context. Thus each candidate has zero gross conditional expected gain despite serial dependence in the learner-visible context. These finite results complement the supermartingale argument only for this registered Markov context process and do not cover delayed/selective feedback or changing conditional outcome laws.",
        "",
        f"Frozen protocol: {protocol.as_posix()} (SHA-256 {hashlib.sha256(protocol.read_bytes()).hexdigest()}). No figure was generated.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_context_markov_null_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "protocol": {
            "path": protocol.as_posix(),
            "sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        },
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "prevalences": PREVALENCES,
            "signal_strength": 0.0,
            "proxy_errors": PROXY_ERRORS,
            "context_persistence": PERSISTENCE,
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
            "metrics/scout_context_markov_null_streams.parquet",
            "metrics/scout_context_markov_null_summary.parquet",
            "reports/scout_context_markov_null_calibration.md",
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
        "--output", type=Path, default=Path("outputs/scout_context_policy_markov_null_1000")
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument(
        "--protocol", type=Path, default=Path("docs/scout_context_policy_markov_null_protocol.md")
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
