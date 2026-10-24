"""Development grid for label and intervention costs under reversal scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ..data.gpu.environment import environment
from .closed_loop_intervention import _evaluate_methods, benefit_schedule
from .promotion_timing import _generate_costs

SEED_OFFSET = 42_102_626
QUERY_RATES = (0.25, 0.5, 0.8)
BUDGET_RATES = (0.2, 0.4)
LABEL_PRICES = (0.0, 0.01)
INTERVENTION_COSTS = ((0.05, 0.05), (0.25, 0.05), (0.05, 0.25))
REVERSAL_ONSETS = (0.1, 0.5, 0.8)
REVERSAL_HARMS = (0.1, 0.2)
CONTROL_SCENARIOS = (
    "no_benefit",
    "persistent_benefit",
    "shadow_only_benefit",
    "late_benefit",
)
METHODS = ("continue", "unconditional_promote", "promotion_only", "promotion_rollback")
CELL_COLUMNS = (
    "scenario",
    "query_rate",
    "budget_rate",
    "label_price",
    "promotion_cost",
    "rollback_cost",
)
DESIGN_COLUMNS = (
    "query_rate",
    "budget_rate",
    "label_price",
    "promotion_cost",
    "rollback_cost",
)


def scenario_schedules(horizon: int) -> dict[str, np.ndarray]:
    """Return the frozen evaluator-only control and reversal mean-gain schedules."""
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 100:
        raise ValueError("horizon must be an integer of at least 100 events per phase")
    schedules = {name: benefit_schedule(name, horizon) for name in CONTROL_SCENARIOS}
    for onset_fraction, harm in product(REVERSAL_ONSETS, REVERSAL_HARMS):
        shadow = np.full(horizon, 0.30, dtype=float)
        deployment = np.full(horizon, -harm, dtype=float)
        onset = max(1, round(horizon * onset_fraction))
        deployment[:onset] = 0.30
        name = f"reversal_onset_{onset_fraction:.1f}_harm_{harm:.1f}"
        schedules[name] = np.concatenate((shadow, deployment))
    return schedules


def _designs() -> tuple[dict[str, float], ...]:
    designs = []
    for query_rate, budget_rate, label_price, (promotion_cost, rollback_cost) in product(
        QUERY_RATES, BUDGET_RATES, LABEL_PRICES, INTERVENTION_COSTS
    ):
        designs.append(
            {
                "query_rate": query_rate,
                "budget_rate": budget_rate,
                "label_price": label_price,
                "promotion_cost": promotion_cost,
                "rollback_cost": rollback_cost,
            }
        )
    return tuple(designs)


def _paired_contrasts(metrics: pd.DataFrame, replicates: int, seed: int) -> pd.DataFrame:
    rows = []
    for index, (keys, group) in enumerate(metrics.groupby(list(CELL_COLUMNS), sort=True)):
        wide = group.pivot(index="seed", columns="method", values="expected_net_utility")
        for method, reference in (
            ("promotion_rollback", "promotion_only"),
            ("promotion_rollback", "continue"),
            ("promotion_only", "continue"),
        ):
            difference = (wide[method] - wide[reference]).to_numpy(dtype=float)
            rng = np.random.default_rng(seed + index * 101 + len(rows))
            draw_indices = rng.integers(0, len(difference), size=(replicates, len(difference)))
            interval = np.quantile(difference[draw_indices].mean(axis=1), (0.025, 0.975))
            row = dict(zip(CELL_COLUMNS, keys, strict=True))
            row.update(
                {
                    "method": method,
                    "reference": reference,
                    "paired_mean_expected_utility_difference": float(difference.mean()),
                    "seed_cluster_ci95_low": float(interval[0]),
                    "seed_cluster_ci95_high": float(interval[1]),
                    "seed_clusters": len(difference),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def _macro_selection(
    metrics: pd.DataFrame, bootstrap_replicates: int, bootstrap_seed: int
) -> pd.DataFrame:
    reversal = metrics[metrics.scenario.str.startswith("reversal_")]
    macro = (
        reversal.groupby([*DESIGN_COLUMNS, "method"], sort=True)
        .agg(
            mean_expected_net_utility=("expected_net_utility", "mean"),
            mean_realized_net_utility=("realized_net_utility", "mean"),
            mean_labels=("labels_queried", "mean"),
            promotion_rate=("promoted", "mean"),
            rollback_rate=("rolled_back", "mean"),
            reversal_cells=("scenario", "nunique"),
            streams=("seed", "size"),
            all_budgets_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    wide = macro.pivot(
        index=list(DESIGN_COLUMNS), columns="method", values="mean_expected_net_utility"
    )
    output = wide.reset_index()
    compliance = (
        reversal.groupby(list(DESIGN_COLUMNS), sort=True)["budget_respected"]
        .all()
        .rename("all_budgets_respected")
        .reset_index()
    )
    output = output.merge(compliance, on=list(DESIGN_COLUMNS), validate="one_to_one")
    output["rollback_vs_promotion_only"] = output["promotion_rollback"] - output["promotion_only"]
    output["rollback_vs_continue"] = output["promotion_rollback"] - output["continue"]
    output["promotion_only_vs_continue"] = output["promotion_only"] - output["continue"]
    output["reversal_cells"] = len(REVERSAL_ONSETS) * len(REVERSAL_HARMS)
    output["streams_per_reversal_cell"] = reversal.groupby("scenario")["seed"].nunique().min()
    paired = reversal.pivot(
        index=[*DESIGN_COLUMNS, "scenario", "seed"],
        columns="method",
        values="expected_net_utility",
    ).reset_index()
    paired["replicate"] = paired["seed"] - paired.groupby("scenario")["seed"].transform("min")
    paired["rollback_vs_promotion_only"] = paired["promotion_rollback"] - paired["promotion_only"]
    paired["rollback_vs_continue"] = paired["promotion_rollback"] - paired["continue"]
    cluster_differences = paired.groupby([*DESIGN_COLUMNS, "replicate"], sort=True)[
        ["rollback_vs_promotion_only", "rollback_vs_continue"]
    ].mean()
    intervals = []
    for index, (design, group) in enumerate(
        cluster_differences.groupby(level=list(range(len(DESIGN_COLUMNS))), sort=True)
    ):
        row = dict(zip(DESIGN_COLUMNS, design, strict=True))
        for contrast in ("rollback_vs_promotion_only", "rollback_vs_continue"):
            differences = group[contrast].to_numpy(dtype=float)
            rng = np.random.default_rng(bootstrap_seed + 10_007 * index)
            draws = rng.integers(0, len(differences), size=(bootstrap_replicates, len(differences)))
            interval = np.quantile(differences[draws].mean(axis=1), (0.025, 0.975))
            row[f"{contrast}_ci95_low"] = float(interval[0])
            row[f"{contrast}_ci95_high"] = float(interval[1])
        intervals.append(row)
    output = output.merge(pd.DataFrame(intervals), on=list(DESIGN_COLUMNS), validate="one_to_one")
    return output.sort_values(
        ["promotion_rollback", "rollback_vs_promotion_only"], ascending=False
    ).reset_index(drop=True)


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 60,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 800,
    device: str = "cuda",
    bootstrap_replicates: int = 2000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2:
        raise ValueError("seeds must be at least two")
    if device not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if bootstrap_replicates < 100:
        raise ValueError("bootstrap_replicates must be at least 100")

    schedules = scenario_schedules(horizon)
    designs = _designs()
    base_design = {
        "query_rate": 0.25,
        "budget_rate": 0.2,
        "label_price": 0.01,
        "promotion_cost": 0.05,
        "rollback_cost": 0.05,
    }
    generator = torch.Generator(device=device)
    row_groups = []
    cell_index = 0
    for scenario_index, (scenario, benefit) in enumerate(schedules.items()):
        scenario_seed = seed_offset + scenario_index * 1_000_003
        incumbent, candidate = _generate_costs(
            benefit,
            seeds=seeds,
            seed=scenario_seed,
            device=device,
        )
        gains = incumbent.astype(float) - candidate.astype(float)
        generator.manual_seed(scenario_seed + 900_001)
        query_uniforms = (
            torch.rand((seeds, 2 * horizon), generator=generator, device=device).cpu().numpy()
        )
        scenario_designs = (base_design,) if scenario in CONTROL_SCENARIOS else designs
        for design in scenario_designs:
            rows = _evaluate_methods(
                scenario=scenario,
                budget_rate=design["budget_rate"],
                gains=gains,
                benefit=benefit,
                query_uniforms=query_uniforms,
                seed_offset=scenario_seed,
                query_rate=design["query_rate"],
                promotion_cost=design["promotion_cost"],
                rollback_cost=design["rollback_cost"],
                label_price=design["label_price"],
                alpha=0.05,
                horizon=horizon,
            )
            for column, value in design.items():
                rows[column] = value
            row_groups.append(rows)
            cell_index += 1

    metrics = pd.concat(row_groups, ignore_index=True)
    summary = (
        metrics.groupby([*CELL_COLUMNS, "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            promotions=("promoted", "sum"),
            promotion_rate=("promoted", "mean"),
            rollbacks=("rolled_back", "sum"),
            rollback_rate=("rolled_back", "mean"),
            false_promotions=("false_promotion_under_null", "sum"),
            false_rollbacks=("false_rollback_under_null", "sum"),
            mean_expected_net_utility=("expected_net_utility", "mean"),
            mean_realized_net_utility=("realized_net_utility", "mean"),
            mean_labels=("labels_queried", "mean"),
            maximum_labels=("labels_queried", "max"),
            budget_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    contrasts = _paired_contrasts(metrics, bootstrap_replicates, seed_offset)
    macro = _macro_selection(metrics, bootstrap_replicates, seed_offset)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    contrasts.to_csv(output / "paired_utility_contrasts.csv", index=False)
    macro.to_csv(output / "reversal_macro_ranking.csv", index=False)
    source_paths = {
        "intervention_sensitivity.py": Path(__file__),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
        "eprocess.py": Path(__file__).with_name("eprocess.py"),
        "promotion_timing.py": Path(__file__).with_name("promotion_timing.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development-only sensitivity grid; do not use its seeds for confirmation",
        "seeds_per_cell": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "device_requested": device,
        "query_rates": list(QUERY_RATES),
        "budget_rates": list(BUDGET_RATES),
        "label_prices": list(LABEL_PRICES),
        "promotion_rollback_cost_pairs": [list(pair) for pair in INTERVENTION_COSTS],
        "reversal_onsets": list(REVERSAL_ONSETS),
        "reversal_harms": list(REVERSAL_HARMS),
        "control_scenarios": list(CONTROL_SCENARIOS),
        "reversal_cells": len(REVERSAL_ONSETS) * len(REVERSAL_HARMS),
        "development_cells": cell_index,
        "methods": list(METHODS),
        "primary_selection_metric": "macro expected net utility of promotion_rollback over six reversal profiles",
        "secondary_selection_metric": "paired macro expected-utility difference vs promotion_only",
        "bootstrap_replicates": bootstrap_replicates,
        "contrast_intervals": "descriptive 95% seed-cluster bootstrap; not multiplicity adjusted",
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_paths.items()
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, contrasts, macro, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/intervention_sensitivity_development")
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=800)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args()
    _metrics, _summary, _contrasts, macro, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(macro.head(12).to_string(index=False))
    print(f"development_cells={manifest['development_cells']}")
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
