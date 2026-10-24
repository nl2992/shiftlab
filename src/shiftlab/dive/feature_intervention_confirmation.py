"""Disjoint utility confirmation after independent feature-gate calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import torch

from ..data.gpu.environment import environment
from .closed_loop_intervention import _evaluate_methods, _paired_contrasts
from .feature_intervention import (
    GAIN_BOUND,
    METHODS,
    _probability_positive,
    generate_feature_cost_streams,
)
from .feature_intervention_calibration import (
    CALIBRATION_SCENARIO_SEED_STRIDE,
    CALIBRATION_SCENARIOS,
)

CONFIRMATION_SCENARIOS = ("harmful_adaptation", "boundary_local_harm", "persistent_benefit")
CONFIRMATION_SEED_OFFSET = 78_102_024


def run_confirmation(
    output_dir: str | Path,
    *,
    calibration_manifest: str
    | Path = "outputs/feature_intervention_calibration_2000/manifest.json",
    seeds: int = 2000,
    seed_offset: int = CONFIRMATION_SEED_OFFSET,
    horizon: int = 400,
    query_rate: float = 0.80,
    budget_rate: float = 0.40,
    alpha: float = 0.05,
    promotion_cost: float = 0.05,
    rollback_cost: float = 0.05,
    label_price: float = 0.01,
    device: str = "cuda",
    bootstrap_replicates: int = 10_000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Run fresh alternatives only after the frozen independent calibration passes."""
    calibration_path = Path(calibration_manifest)
    if not calibration_path.is_file():
        raise FileNotFoundError(f"required calibration manifest not found: {calibration_path}")
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if calibration.get("status") != "passed":
        raise ValueError("independent calibration did not pass; confirmation is not authorized")
    required = {
        "horizon_per_phase": horizon,
        "query_rate": query_rate,
        "budget_rate": budget_rate,
        "alpha_total": alpha,
        "promotion_cost": promotion_cost,
        "rollback_cost": rollback_cost,
    }
    mismatches = {
        key: (calibration.get(key), value)
        for key, value in required.items()
        if calibration.get(key) != value
    }
    if mismatches:
        raise ValueError(
            f"confirmation configuration differs from calibrated protocol: {mismatches}"
        )
    calibration_last_seed = (
        int(calibration["seed_offset"])
        + (len(CALIBRATION_SCENARIOS) - 1) * CALIBRATION_SCENARIO_SEED_STRIDE
        + int(calibration["seeds_per_cell"])
        - 1
    )
    if seed_offset <= calibration_last_seed:
        raise ValueError("confirmation seed block must be disjoint from calibration seed block")
    if seeds < 2 or horizon < 100:
        raise ValueError("seeds must be >=2 and horizon >=100")
    if not 0 < query_rate <= 1 or not 0 < budget_rate <= 1 or not 0 < alpha < 1:
        raise ValueError("query_rate, budget_rate and alpha must lie in (0,1)")
    if min(promotion_cost, rollback_cost, label_price) < 0:
        raise ValueError("costs must be nonnegative")
    query_generator = torch.Generator(device=device).manual_seed(seed_offset + 9_201_024)
    query_uniforms = (
        torch.rand((seeds, 2 * horizon), generator=query_generator, device=device).cpu().numpy()
    )
    rows = []
    for scenario_index, scenario in enumerate(CONFIRMATION_SCENARIOS):
        _features, _outcomes, gains, _oracle = generate_feature_cost_streams(
            scenario=scenario,
            seeds=seeds,
            horizon=horizon,
            seed=seed_offset + scenario_index * 107_009,
            device=device,
            rollback_cost=rollback_cost,
        )
        # The evaluator's expected gain is analytically registered by the generator;
        # realized outcomes are used only for queried evidence and diagnostics.
        probability = _probability_positive(scenario, horizon, rollback_cost)
        benefit = 0.5 * (6 * probability - 1)
        rows.append(
            _evaluate_methods(
                scenario=scenario,
                budget_rate=budget_rate,
                gains=gains,
                benefit=benefit,
                query_uniforms=query_uniforms,
                seed_offset=seed_offset + scenario_index * 107_009,
                query_rate=query_rate,
                promotion_cost=promotion_cost,
                rollback_cost=rollback_cost,
                label_price=label_price,
                alpha=alpha,
                horizon=horizon,
                gain_bound=GAIN_BOUND,
            )
        )
    metrics = pd.concat(rows, ignore_index=True)
    metrics["query_rate"] = query_rate
    summary = (
        metrics.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            promotions=("promoted", "sum"),
            promotion_rate=("promoted", "mean"),
            rollbacks=("rolled_back", "sum"),
            rollback_rate=("rolled_back", "mean"),
            mean_rollback_event=("rollback_time", "mean"),
            mean_expected_net_utility=("expected_net_utility", "mean"),
            mean_realized_net_utility=("realized_net_utility", "mean"),
            mean_labels=("labels_queried", "mean"),
            maximum_labels=("labels_queried", "max"),
            budget_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    contrasts = _paired_contrasts(metrics, bootstrap_replicates)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "confirmation_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "confirmation_metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    contrasts.to_csv(output / "paired_utility_contrasts.csv", index=False)
    primary = contrasts[
        contrasts.scenario.eq("harmful_adaptation")
        & contrasts.method.eq("promotion_rollback")
        & contrasts.reference.eq("promotion_only")
    ].iloc[0]
    net_control = contrasts[
        contrasts.scenario.eq("harmful_adaptation")
        & contrasts.method.eq("promotion_rollback")
        & contrasts.reference.eq("continue")
    ].iloc[0]
    primary_pass = bool(primary.seed_cluster_ci95_low > 0 and metrics.budget_respected.all())
    end_to_end_pass = bool(net_control.seed_cluster_ci95_low > 0)
    source_paths = {
        "feature_intervention_confirmation.py": Path(__file__),
        "feature_intervention.py": Path(__file__).with_name("feature_intervention.py"),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "disjoint utility confirmation after integrated gate calibration",
        "status": "rollback_mechanism_retained"
        if primary_pass
        else "rollback_mechanism_not_retained",
        "end_to_end_status": "positive_net_utility_confirmed"
        if end_to_end_pass
        else "positive_net_utility_not_confirmed",
        "calibration_manifest": str(calibration_path),
        "calibration_manifest_sha256": hashlib.sha256(calibration_path.read_bytes()).hexdigest(),
        "scenarios": list(CONFIRMATION_SCENARIOS),
        "methods": list(METHODS),
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "query_rate": query_rate,
        "budget_rate": budget_rate,
        "alpha_total": alpha,
        "promotion_cost": promotion_cost,
        "rollback_cost": rollback_cost,
        "label_price": label_price,
        "primary_contrast": "promotion_rollback minus promotion_only expected net utility under harmful_adaptation",
        "primary_retention_rule": "paired 95% seed-cluster bootstrap interval lower endpoint > 0 and all caps respected",
        "primary_paired_difference": float(primary.paired_mean_expected_utility_difference),
        "primary_ci95": [
            float(primary.seed_cluster_ci95_low),
            float(primary.seed_cluster_ci95_high),
        ],
        "harmful_adaptation_net_utility_vs_continue": float(
            net_control.paired_mean_expected_utility_difference
        ),
        "harmful_adaptation_net_utility_vs_continue_ci95": [
            float(net_control.seed_cluster_ci95_low),
            float(net_control.seed_cluster_ci95_high),
        ],
        "metric_rows": len(metrics),
        "all_budgets_respected": bool(metrics.budget_respected.all()),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_paths.items()
        },
        "environment": environment(),
        "command": sys.argv,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Feature-dependent intervention confirmation",
        "",
        f"Rollback mechanism retention: **{manifest['status']}**.",
        "",
        f"- Calibration manifest SHA-256: `{manifest['calibration_manifest_sha256']}`.",
        f"- Fresh confirmation block begins at seed offset {seed_offset}; {seeds} seeds per scenario; CUDA device `{device}`.",
        f"- Primary harmful-reversal contrast: {manifest['primary_paired_difference']:.4f} expected utility units, paired 95% seed-bootstrap interval [{manifest['primary_ci95'][0]:.4f}, {manifest['primary_ci95'][1]:.4f}].",
        f"- Net utility against `continue` under harmful reversal: {manifest['harmful_adaptation_net_utility_vs_continue']:.4f}, paired 95% interval [{manifest['harmful_adaptation_net_utility_vs_continue_ci95'][0]:.4f}, {manifest['harmful_adaptation_net_utility_vs_continue_ci95'][1]:.4f}].",
        f"- All hard label caps respected: {manifest['all_budgets_respected']}.",
        "",
        "## Scenario results",
        "",
        summary.to_markdown(index=False),
        "",
        "## Paired expected-utility contrasts",
        "",
        contrasts.to_markdown(index=False),
        "",
        "These results apply only to the frozen, immediate-label simulator and its registered cost schedules. No figures were generated.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return metrics, summary, contrasts, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/feature_intervention_confirmation_2000")
    parser.add_argument(
        "--calibration-manifest",
        default="outputs/feature_intervention_calibration_2000/manifest.json",
    )
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=CONFIRMATION_SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--query-rate", type=float, default=0.80)
    parser.add_argument("--budget-rate", type=float, default=0.40)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, contrasts, manifest = run_confirmation(
        args.output_dir,
        calibration_manifest=args.calibration_manifest,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rate=args.query_rate,
        budget_rate=args.budget_rate,
        device=args.device,
    )
    print(summary.to_string(index=False))
    print(contrasts.to_string(index=False))
    print(f"status={manifest['status']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
