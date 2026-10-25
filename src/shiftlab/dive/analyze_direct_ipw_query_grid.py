"""Summarize paired alternative-macro results from a direct-IPW query grid."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ALTERNATIVE_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
ENDPOINTS = {
    "detection_all_harm": "single_e_detected",
    "excess_cost_avoided": "evaluator_excess_cost_avoided_by_fallback",
    "labels": "labels_queried",
    "label_spend": "realized_label_spend",
    "events_processed": "processed_events",
}


def alternative_macro_contrasts(
    metrics: pd.DataFrame, *, bootstrap_replicates: int = 10_000, seed: int = 31_106_773
) -> pd.DataFrame:
    """Return equal-scenario paired effects with stream-seed bootstrap intervals."""
    required = {
        "query_floor",
        "scenario",
        "seed",
        "method",
        "material_harm",
        *ENDPOINTS.values(),
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics are missing required columns: {sorted(missing)}")
    if bootstrap_replicates < 100:
        raise ValueError("bootstrap_replicates must be at least 100")

    rows: list[dict[str, object]] = []
    rng = np.random.default_rng(seed)
    observed_harm_scenarios = set(
        metrics.loc[metrics.material_harm.astype(bool), "scenario"].unique()
    )
    scenarios = tuple(name for name in ALTERNATIVE_SCENARIOS if name in observed_harm_scenarios)
    if not scenarios:
        raise ValueError("grid contains no registered alternative scenarios")

    for floor in sorted(metrics.query_floor.unique()):
        baseline = metrics.loc[
            metrics.query_floor.eq(floor)
            & metrics.method.eq("uniform_proxy")
            & metrics.scenario.isin(scenarios)
        ]
        for method in sorted(set(metrics.method) - {"uniform_proxy"}):
            candidate = metrics.loc[
                metrics.query_floor.eq(floor)
                & metrics.method.eq(method)
                & metrics.scenario.isin(scenarios)
            ]
            paired = baseline.merge(
                candidate,
                on=["query_floor", "scenario", "seed"],
                suffixes=("_uniform", "_candidate"),
                validate="one_to_one",
            )
            if len(paired) != len(baseline) or len(paired) != len(candidate):
                raise ValueError("alternative methods do not share complete paired seed cells")
            paired = paired.loc[paired.material_harm_uniform.astype(bool)]
            if paired.empty:
                continue
            per_seed: dict[str, np.ndarray] = {}
            for endpoint, column in ENDPOINTS.items():
                delta = (
                    paired[f"{column}_candidate"].astype(float).to_numpy()
                    - paired[f"{column}_uniform"].astype(float).to_numpy()
                )
                by_seed = (
                    pd.DataFrame(
                        {"seed": paired.seed.to_numpy(), "delta": delta},
                        index=paired.index,
                    )
                    .groupby("seed", sort=True)
                    .delta.mean()
                )
                per_seed[endpoint] = by_seed.to_numpy(dtype=float)
            seed_count = len(next(iter(per_seed.values())))
            draw_index = rng.integers(0, seed_count, size=(bootstrap_replicates, seed_count))
            row: dict[str, object] = {
                "query_floor": float(floor),
                "method": method,
                "alternative_scenarios": ",".join(scenarios),
                "n_seed_clusters": seed_count,
                "n_seed_scenario_pairs": len(paired),
                "n_harmful_scenarios": paired.scenario.nunique(),
            }
            for endpoint, values in per_seed.items():
                draws = values[draw_index].mean(axis=1)
                row[f"{endpoint}_difference"] = float(values.mean())
                row[f"{endpoint}_ci_low"] = float(np.quantile(draws, 0.025))
                row[f"{endpoint}_ci_high"] = float(np.quantile(draws, 0.975))
            rows.append(row)
    return pd.DataFrame(rows)


def analyze_direct_ipw_query_grid(
    output: Path,
    *,
    bootstrap_replicates: int = 10_000,
    seed: int = 31_106_773,
) -> Path:
    manifest_path = output / "reports" / "manifest.json"
    metrics_path = output / "metrics" / "direct_ipw_query_grid.parquet"
    report_path = output / "reports" / "direct_ipw_query_grid_results.md"
    if not manifest_path.is_file() or not metrics_path.is_file() or not report_path.is_file():
        raise FileNotFoundError("completed direct-IPW development artifacts are required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "exploratory_development_only":
        raise ValueError("refusing to analyze an output with an unexpected status")
    metrics = pd.read_parquet(metrics_path)
    contrasts = alternative_macro_contrasts(
        metrics, bootstrap_replicates=bootstrap_replicates, seed=seed
    )
    contrasts_path = output / "metrics" / "alternative_macro_contrasts.csv"
    contrasts.to_csv(contrasts_path, index=False)

    table = contrasts[
        [
            "query_floor",
            "method",
            "detection_all_harm_difference",
            "detection_all_harm_ci_low",
            "detection_all_harm_ci_high",
            "excess_cost_avoided_difference",
            "excess_cost_avoided_ci_low",
            "excess_cost_avoided_ci_high",
            "labels_difference",
            "labels_ci_low",
            "labels_ci_high",
            "label_spend_difference",
            "label_spend_ci_low",
            "label_spend_ci_high",
        ]
    ].to_markdown(index=False, floatfmt=".3f")
    report = report_path.read_text(encoding="utf-8")
    marker = "\n## Equal-weight alternative macro contrasts"
    if marker in report:
        report = report.split(marker, maxsplit=1)[0]
    report += (
        f"\n\n## Equal-weight alternative macro contrasts\n\n"
        f"Each contrast is candidate minus uniform, averaged equally over the registered "
        f"harmful scenarios within each seed and then bootstrapped by seed cluster "
        f"({bootstrap_replicates:,} resamples). Positive detection and exposure avoided "
        f"are favorable; negative labels and spend indicate resource savings. Intervals "
        f"are descriptive, percentile-based, and unadjusted across this development grid.\n\n"
        f"`excess_cost_avoided` credits evaluator-known avoided excess cost when fallback "
        f"occurs after an alarm or when the hard-budget monitor stops. It can therefore "
        f"reflect both earlier fallback and statistical escalation; detection, processed "
        f"events, label counts, and spend are reported separately. Synthetic tariffs and "
        f"decision-cost units are not combined into a single utility without an explicit "
        f"conversion parameter.\n\n{table}\n"
    )
    report_path.write_text(report, encoding="utf-8")

    manifest["analysis"] = {
        "script": "src/shiftlab/dive/analyze_direct_ipw_query_grid.py",
        "endpoint": "equal-weight average over registered harmful scenarios per seed",
        "bootstrap": "paired seed-cluster percentile bootstrap, descriptive and unadjusted",
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": seed,
        "alternative_scenarios": list(ALTERNATIVE_SCENARIOS),
        "does_not_establish": ["nominal false-alarm control", "confirmation", "novelty"],
    }
    manifest["sha256"] = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.resolve() != manifest_path.resolve():
            manifest["sha256"][path.relative_to(output).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return contrasts_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("outputs/direct_ipw_query_development_30_w4")
    )
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=31_106_773)
    args = parser.parse_args(argv)
    print(
        analyze_direct_ipw_query_grid(
            args.input,
            bootstrap_replicates=args.bootstrap_replicates,
            seed=args.seed,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
