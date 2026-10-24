"""Independent null calibration for the feature-dependent intervention gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

from ..data.gpu.environment import environment
from .closed_loop_intervention import _simulate_gate
from .feature_intervention import GAIN_BOUND, generate_feature_cost_streams

CALIBRATION_SCENARIOS = (
    ("stationary", "false_promotion"),
    ("benign_nuisance", "false_promotion"),
    ("rollback_boundary", "false_rollback"),
    ("persistent_benefit", "false_rollback"),
)
CALIBRATION_SEED_OFFSET = 77_102_024
CALIBRATION_SCENARIO_SEED_STRIDE = 103_007


def _cp_upper(events: int, streams: int, alpha: float) -> float:
    if streams < 1 or not 0 <= events <= streams or not 0 < alpha < 1:
        raise ValueError("invalid exact-binomial interval inputs")
    return 1.0 if events == streams else float(beta.ppf(1 - alpha, events + 1, streams - events))


def run_calibration(
    output_dir: str | Path,
    *,
    seeds: int = 2000,
    seed_offset: int = CALIBRATION_SEED_OFFSET,
    horizon: int = 400,
    query_rate: float = 0.80,
    budget_rate: float = 0.40,
    alpha: float = 0.05,
    promotion_cost: float = 0.05,
    rollback_cost: float = 0.05,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Estimate simultaneous upper bounds for two promotion and two rollback nulls."""
    if seeds < 2 or horizon < 100:
        raise ValueError("seeds must be >=2 and horizon >=100")
    if not 0 < query_rate <= 1 or not 0 < budget_rate <= 1 or not 0 < alpha < 1:
        raise ValueError("query_rate, budget_rate and alpha must lie in (0,1)")
    if min(promotion_cost, rollback_cost) < 0:
        raise ValueError("intervention costs must be nonnegative")
    family_alpha = alpha / len(CALIBRATION_SCENARIOS)
    query_generator = torch.Generator(device=device).manual_seed(seed_offset + 9_201_024)
    query_uniforms = (
        torch.rand((seeds, 2 * horizon), generator=query_generator, device=device).cpu().numpy()
    )
    label_budget = int(np.floor(budget_rate * 2 * horizon))
    records = []
    for scenario_index, (scenario, error_type) in enumerate(CALIBRATION_SCENARIOS):
        _features, _outcomes, gains, oracle = generate_feature_cost_streams(
            scenario=scenario,
            seeds=seeds,
            horizon=horizon,
            seed=seed_offset + scenario_index * CALIBRATION_SCENARIO_SEED_STRIDE,
            device=device,
            rollback_cost=rollback_cost,
        )
        gate = _simulate_gate(
            gains,
            query_uniforms,
            query_rate=query_rate,
            label_budget=label_budget,
            alpha=alpha,
            promotion_cost=promotion_cost,
            rollback_cost=rollback_cost,
            horizon=horizon,
            gain_bound=GAIN_BOUND,
        )
        for index in range(seeds):
            promoted = bool(gate["promoted"][index])
            rolled_back = bool(gate["rolled_back"][index])
            at_risk = promoted if error_type == "false_rollback" else True
            error_event = rolled_back if error_type == "false_rollback" else promoted
            records.append(
                {
                    "scenario": scenario,
                    "error_type": error_type,
                    "seed": seed_offset + scenario_index * 103_007 + index,
                    "promoted": promoted,
                    "rolled_back": rolled_back,
                    "at_risk": bool(at_risk),
                    "error_event": bool(error_event and at_risk),
                    "labels_queried": int(gate["labels_queried"][index]),
                    "label_budget": label_budget,
                    "budget_respected": bool(gate["budget_respected"][index]),
                    "population_shadow_gain": float(
                        np.mean(oracle["expected_incumbent_minus_candidate_cost"][:horizon])
                    ),
                    "population_deployment_gain": float(
                        np.mean(oracle["expected_incumbent_minus_candidate_cost"][horizon:])
                    ),
                }
            )
    metrics = pd.DataFrame(records)
    cells = []
    for (scenario, error_type), group in metrics.groupby(["scenario", "error_type"], sort=True):
        at_risk = group[group.at_risk]
        events, n = int(at_risk.error_event.sum()), len(at_risk)
        upper = _cp_upper(events, n, family_alpha) if n else 1.0
        cells.append(
            {
                "scenario": scenario,
                "error_type": error_type,
                "events": events,
                "streams_at_risk": n,
                "rate": events / n if n else np.nan,
                "simultaneous_one_sided_cp_upper": upper,
                "cell_alpha": family_alpha,
                "familywise_alpha": alpha,
                "family_cells": len(CALIBRATION_SCENARIOS),
                "gate_pass": bool(n > 0 and upper <= alpha),
            }
        )
    calibration = pd.DataFrame(cells)
    all_caps = bool(metrics.budget_respected.all())
    passed = bool(calibration.gate_pass.all() and all_caps)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "calibration_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "calibration_metrics.csv", index=False)
    calibration.to_csv(output / "error_calibration.csv", index=False)
    source_paths = {
        "feature_intervention_calibration.py": Path(__file__),
        "feature_intervention.py": Path(__file__).with_name("feature_intervention.py"),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "independent null calibration of the integrated feature-dependent promotion and rollback gates",
        "status": "passed" if passed else "failed",
        "seeds_per_cell": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "query_rate": query_rate,
        "budget_rate": budget_rate,
        "label_budget": label_budget,
        "alpha_total": alpha,
        "gate_alpha_per_stage": alpha / 2,
        "simultaneous_cell_alpha": family_alpha,
        "calibration_scenarios_and_errors": [list(cell) for cell in CALIBRATION_SCENARIOS],
        "promotion_cost": promotion_cost,
        "rollback_cost": rollback_cost,
        "cost_support_bound": GAIN_BOUND,
        "all_budgets_respected": all_caps,
        "retention_rule": "all four exact one-sided Bonferroni Clopper-Pearson upper limits <= 0.05 and no cap violation",
        "metric_rows": len(metrics),
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
        "# Feature-dependent intervention null calibration",
        "",
        f"Calibration status: **{manifest['status']}** under the frozen simultaneous error rule.",
        "",
        f"- Fresh seed block starts at {seed_offset}; {seeds} streams per cell; device `{device}`.",
        f"- `q={query_rate}`, budget `{budget_rate:.0%}`, horizon `{horizon}` per phase, `alpha={alpha}` split equally between gates.",
        "- Four one-sided exact Clopper–Pearson bounds use Bonferroni cell alpha `alpha_total/4`.",
        f"- All pathwise label caps respected: {all_caps}.",
        "",
        calibration.to_markdown(index=False),
        "",
        "This establishes only empirical calibration for these registered synthetic controls and the assumptions in `feature_intervention_protocol.md`. It is not evidence about delayed feedback, dependence, adaptive candidates, or real application costs. No figures were generated.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return metrics, calibration, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/feature_intervention_calibration_2000")
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=CALIBRATION_SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--query-rate", type=float, default=0.80)
    parser.add_argument("--budget-rate", type=float, default=0.40)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, calibration, manifest = run_calibration(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rate=args.query_rate,
        budget_rate=args.budget_rate,
        device=args.device,
    )
    print(calibration.to_string(index=False))
    print(f"status={manifest['status']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
