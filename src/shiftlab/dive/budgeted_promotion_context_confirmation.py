"""Independent positive-signal confirmation for target-scout promotion."""

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

PREVALENCES = (0.10, 0.50, 0.90)
SIGNAL_STRENGTHS = (0.05, 0.10)
PROXY_ERRORS = (0.0, 0.10, 0.25)
METHODS = ("rank", "rank_context_volume", "scout_context_policy")
BUDGET_RATE = 0.40
SWITCHING_COST = 0.05
FAMILY_ALPHA = 0.05
PRACTICAL_MARGIN = 1.0
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20_261_028
CALIBRATION_SEED_END = 20_262_299
CONFIRMATION_SEED_OFFSET = 20_264_000
MIN_CONFIRMATION_SEEDS = 600


def _cell_name(prevalence: float, signal: float, error: float) -> str:
    return (
        f"context_p{round(100 * prevalence):02d}_"
        f"delta{round(1000 * signal):03d}_error{round(100 * error):02d}"
    )


def _macro_contrasts(detail: pd.DataFrame, *, draws: int = BOOTSTRAP_DRAWS) -> pd.DataFrame:
    """Compute registered matched, equal-cell-weighted utility contrasts."""
    if draws < 100 or detail.empty:
        raise ValueError("confirmation bootstrap requires data and at least 100 draws")
    scenarios = sorted(detail["scenario"].unique())
    expected_cells = len(PREVALENCES) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS)
    if len(scenarios) != expected_cells:
        raise ValueError(f"expected {expected_cells} positive-signal cells")
    seeds = np.sort(detail["seed"].unique())
    if len(seeds) < 2:
        raise ValueError("at least two matched seed blocks are required")

    contrasts = (
        ("scout_context_policy_minus_rank", "rank"),
        ("scout_context_policy_minus_rank_context_volume", "rank_context_volume"),
    )
    matrices: dict[str, np.ndarray] = {}
    for contrast, comparator in contrasts:
        matrix = np.empty((len(scenarios), len(seeds)), dtype=float)
        for cell_index, scenario in enumerate(scenarios):
            cell = detail.loc[detail["scenario"].eq(scenario)]
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
                raise ValueError(f"unmatched or incomplete seed block in {scenario}")
            matrix[cell_index] = scout["expected_postpromotion_net_gain"].to_numpy(
                dtype=float
            ) - baseline["expected_postpromotion_net_gain"].to_numpy(dtype=float)
        matrices[contrast] = matrix

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []
    for contrast, _ in contrasts:
        matrix = matrices[contrast]
        bootstrap = np.empty(draws, dtype=float)
        for start in range(0, draws, 100):
            stop = min(draws, start + 100)
            indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            bootstrap[start:stop] = np.take(matrix, indices, axis=1).mean(axis=(0, 2))
        rows.append(
            {
                "contrast": contrast,
                "metric": "expected_postpromotion_net_gain",
                "n_settings": len(scenarios),
                "n_seed_blocks": len(seeds),
                "mean_paired_difference": float(matrix.mean()),
                "simultaneous_ci_level": 0.975,
                "bootstrap_ci_low": float(np.quantile(bootstrap, 0.0125)),
                "bootstrap_ci_high": float(np.quantile(bootstrap, 0.9875)),
                "practical_margin": PRACTICAL_MARGIN,
                "bootstrap_draws": draws,
                "bootstrap_seed": BOOTSTRAP_SEED,
            }
        )
    return pd.DataFrame(rows)


def run_confirmation(
    *,
    output: Path,
    seeds: int = MIN_CONFIRMATION_SEEDS,
    seed_offset: int = CONFIRMATION_SEED_OFFSET,
    n: int = 3200,
    d: int = 16,
    device: str = "cuda",
    protocol: Path,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> Path:
    """Run the frozen, matched positive-signal grid and assess both gates."""
    if seeds < 2 or n < 1000 or d < 3:
        raise ValueError("confirmation requires seeds >=2, n >=1000, and d >=3")
    if seed_offset <= CALIBRATION_SEED_END:
        raise ValueError("confirmation seed block must follow independent calibration")
    if not protocol.is_file():
        raise FileNotFoundError(f"frozen protocol not found: {protocol}")
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite existing confirmation output: {output}")
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
        for signal in SIGNAL_STRENGTHS:
            for proxy_error in PROXY_ERRORS:
                cell_name = _cell_name(prevalence, signal, proxy_error)
                print(
                    f"scout-confirm cell={cell_name} seeds={seeds} device={resolved_device}",
                    flush=True,
                )
                config = BudgetedPromotionConfig(
                    n=n,
                    d=d,
                    seeds=1,
                    seed_offset=seed_offset,
                    switching_cost=SWITCHING_COST,
                    budget_rates=(BUDGET_RATE,),
                    query_policies=("uniform",),
                    alpha_allocations=("rank", "rank_context_volume"),
                    estimators=("direct_ipw",),
                    monitoring_rules=("fixed_mixture",),
                    bound_mode="global",
                    context_feature_index=d - 1,
                    context_threshold=0.0,
                    context_target_prevalence=prevalence,
                    context_signal_strength=signal,
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
                    )
                    selected = [row for row in seed_rows if row["alpha_allocation"] in METHODS]
                    if len(selected) != len(METHODS):
                        raise RuntimeError("confirmation stream is missing a registered method")
                    for row in selected:
                        row["scenario"] = cell_name
                        row["context_target_prevalence"] = prevalence
                        row["context_signal_strength"] = signal
                        row["context_proxy_error"] = proxy_error
                        row["seed"] = seed
                        records.append(row)

    detail = pd.DataFrame.from_records(records)
    expected_rows = (
        seeds * len(PREVALENCES) * len(SIGNAL_STRENGTHS) * len(PROXY_ERRORS) * len(METHODS)
    )
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} confirmation rows; received {len(detail)}")
    if detail.duplicated(["scenario", "seed", "alpha_allocation"]).any():
        raise RuntimeError("duplicate scenario/seed/method records in confirmation output")
    if not detail["budget_rate"].eq(BUDGET_RATE).all():
        raise RuntimeError("confirmation rows do not use the registered 40% cap")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("confirmation exceeded the realized hard label cap")

    contrasts = _macro_contrasts(detail, draws=bootstrap_draws)
    passed = bool(contrasts["bootstrap_ci_low"].gt(PRACTICAL_MARGIN).all())
    status = (
        "passed"
        if passed and seeds >= MIN_CONFIRMATION_SEEDS
        else "failed"
        if seeds >= MIN_CONFIRMATION_SEEDS
        else "smoke_only_not_confirmation"
    )
    summary = detail.groupby(["scenario", "alpha_allocation"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        mean_expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        mean_labels_queried=("labels_queried", "mean"),
        mean_certification_fraction=("certification_fraction_processed", "mean"),
    )
    detail.to_parquet(
        metrics_dir / "scout_context_policy_confirmation_streams.parquet", index=False
    )
    summary.to_parquet(metrics_dir / "scout_context_policy_confirmation_cells.parquet", index=False)
    contrasts.to_parquet(
        metrics_dir / "scout_context_policy_confirmation_contrasts.parquet", index=False
    )

    report_path = reports_dir / "scout_context_policy_confirmation.md"
    report = [
        "# Target-scout contextual policy independent confirmation",
        "",
        f"Status: **{status}**. Device: {resolved_device}; seeds per cell: {seeds}; seed block: {seed_offset}–{seed_offset + seeds - 1}.",
        "",
        "The registered grid has 18 positive-signal prevalence × signal × proxy-error cells, the common 40% hard cap, and three methods on matched seeds and query uniforms. The primary endpoint is evaluator-known cumulative future net decision gain. The two contrasts equally weight all 18 cells and resample matched seed IDs as blocks.",
        "",
        "| Contrast | Mean paired difference | Simultaneous 97.5% interval | Practical margin |",
        "|---|---:|---:|---:|",
    ]
    for row in contrasts.itertuples(index=False):
        report.append(
            f"| {row.contrast} | {row.mean_paired_difference:.3f} | [{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}] | {row.practical_margin:.1f} |"
        )
    report.extend(
        [
            "",
            "The performance gate passes only when both lower limits exceed +1.0 and all hard caps hold. Cellwise metrics are descriptive. Claims are limited to this IID synthetic family, known positive uniform propensities, bounded paired costs, frozen candidate family, learner-visible contexts and registered budget. The independent null calibration does not extend to serial dependence, delayed/selective labels, context drift, or real applications. No novelty claim follows.",
            "",
            f"Frozen protocol: {protocol.as_posix()} (SHA-256 {hashlib.sha256(protocol.read_bytes()).hexdigest()}). No figure was generated.",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "target_scout_context_policy_independent_confirmation",
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
            "signal_strengths": SIGNAL_STRENGTHS,
            "proxy_errors": PROXY_ERRORS,
            "budget_rate": BUDGET_RATE,
            "switching_cost": SWITCHING_COST,
            "methods": METHODS,
            "query_policy": "uniform",
            "estimator": "direct_ipw",
            "monitoring_rule": "fixed_mixture",
            "alpha": FAMILY_ALPHA,
        },
        "inference": {
            "primary_contrasts": contrasts.to_dict(orient="records"),
            "simultaneous_ci_coverage": 0.95,
            "bonferroni_comparisons": 2,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "practical_margin": PRACTICAL_MARGIN,
            "all_label_caps_respected": True,
            "seed_block_after_calibration": seed_offset > CALIBRATION_SEED_END,
            "figure_generated": False,
        },
        "artifacts": [
            "metrics/scout_context_policy_confirmation_streams.parquet",
            "metrics/scout_context_policy_confirmation_cells.parquet",
            "metrics/scout_context_policy_confirmation_contrasts.parquet",
            "reports/scout_context_policy_confirmation.md",
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
        "--output", type=Path, default=Path("outputs/scout_context_policy_confirmation_600")
    )
    parser.add_argument("--seeds", type=int, default=MIN_CONFIRMATION_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=CONFIRMATION_SEED_OFFSET)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("docs/scout_context_policy_confirmation_protocol.md"),
    )
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    args = parser.parse_args(argv)
    print(
        run_confirmation(
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
