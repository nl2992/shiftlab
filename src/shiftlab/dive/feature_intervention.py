"""Integrate certified promotion and rollback with feature-dependent paired costs.

This is a controlled synthetic development benchmark. Costs are imposed research
utilities, and the conditional outcome law is known only to the evaluator.
"""

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

from ..data.gpu.environment import environment
from ..data.streaming import (
    DecisionFeedback,
    DecisionRequest,
    OracleDecisionRecord,
    PolicyDecision,
    replay_decision_stream,
)
from .closed_loop_intervention import _evaluate_methods, _paired_contrasts

SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "harmful_adaptation",
    "persistent_benefit",
    "rollback_boundary",
)
METHODS = ("continue", "unconditional_promote", "promotion_only", "promotion_rollback")
SEED_OFFSET = 76_102_024
FALSE_NEGATIVE_COST = 5.0
FALSE_POSITIVE_COST = 1.0
GAIN_BOUND = max(FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST)


def _probability_positive(scenario: str, horizon: int, rollback_cost: float = 0.05) -> np.ndarray:
    """Evaluator-only P(Y=1 | candidate action region) for two independent phases."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    shadow = np.full(horizon, 1 / 6, dtype=float)
    deployment = shadow.copy()
    if scenario == "boundary_local_harm":
        deployment[:] = 0.50
    elif scenario == "harmful_adaptation":
        shadow[:] = 0.50
        deployment[:] = 0.05
    elif scenario in {"persistent_benefit", "rollback_boundary"}:
        shadow[:] = deployment[:] = 0.50
        if scenario == "rollback_boundary":
            deployment[:] = 1 / 6 - rollback_cost / (3 * horizon)
    return np.concatenate((shadow, deployment))


def generate_feature_cost_streams(
    *,
    scenario: str,
    seeds: int,
    horizon: int,
    seed: int,
    device: str,
    rollback_cost: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Generate features, paired realized gains and oracle means on device.

    The incumbent always chooses action 0. The frozen candidate chooses action 1
    when X[0] > 0. Potential costs are identifiable from the observed binary Y,
    so this simulator does not require action-propensity weighting for outcomes.
    Querying is a separate, predictable Bernoulli sample with known propensity.
    """
    if seeds < 1 or horizon < 2 or device not in {"cpu", "cuda"}:
        raise ValueError("seeds, horizon or device is invalid")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    probability = _probability_positive(scenario, horizon, rollback_cost)
    generator = torch.Generator(device=device).manual_seed(seed)
    x = torch.randn((seeds, 2 * horizon, 8), generator=generator, device=device)
    if scenario == "benign_nuisance":
        # The shift is deliberately outside the candidate's decision coordinate and
        # leaves P(Y | X[0] > 0) unchanged.
        x[:, horizon:, 1:] += 3.0
    positive_context = x[:, :, 0] > 0
    p = torch.as_tensor(probability, device=device, dtype=x.dtype)[None, :]
    p = torch.where(positive_context, p, torch.full_like(p, 0.25))
    y = (torch.rand((seeds, 2 * horizon), generator=generator, device=device) < p).to(x.dtype)
    candidate = positive_context
    incumbent_loss = FALSE_NEGATIVE_COST * y
    candidate_loss = torch.where(
        candidate,
        FALSE_POSITIVE_COST * (1.0 - y),
        FALSE_NEGATIVE_COST * y,
    )
    gains = (incumbent_loss - candidate_loss).cpu().numpy().astype(float)
    features = x.cpu().numpy()
    outcomes = y.cpu().numpy().astype(np.int8)
    # For X[0]~N(0,1), P(X[0]>0)=1/2. The potential gain conditional on this
    # context is (FN+FP)p-FP, giving the evaluator's exact population mean.
    benefit = 0.5 * (
        (FALSE_NEGATIVE_COST + FALSE_POSITIVE_COST) * probability - FALSE_POSITIVE_COST
    )
    nuisance_shift = 3.0 * np.sqrt(7.0) if scenario == "benign_nuisance" else 0.0
    oracle = {
        "probability_positive_in_candidate_region": probability,
        "expected_incumbent_minus_candidate_cost": benefit,
        "nuisance_mean_shift_l2": nuisance_shift,
        "change_time": horizon
        if scenario
        in {
            "benign_nuisance",
            "boundary_local_harm",
            "harmful_adaptation",
            "rollback_boundary",
        }
        else None,
    }
    return features, outcomes, gains, oracle


def _replay_contract_smoke(
    *,
    features: np.ndarray,
    outcomes: np.ndarray,
    queried_mask: np.ndarray,
    promoted: bool,
    promotion_time: int,
    rollback_time: int,
    horizon: int,
    query_rate: float,
    label_budget: int,
) -> int:
    """Construct and replay one logged stream; evaluator truth is never an input."""
    requests: list[DecisionRequest] = []
    decisions: list[PolicyDecision] = []
    feedback: list[DecisionFeedback] = []
    labels_logged = 0
    for event in range(2 * horizon):
        deployed_candidate = bool(
            promoted
            and event >= horizon
            and (rollback_time < 0 or event < horizon + rollback_time + 1)
        )
        candidate_action = int(features[event, 0] > 0)
        action, reference_action = (
            (candidate_action, 0) if deployed_candidate else (0, candidate_action)
        )
        sample_id = str(event)
        requests.append(
            DecisionRequest(
                sample_id=sample_id,
                event_time=event,
                feature_available_time=event,
                prediction_time=event,
                features=tuple(float(value) for value in features[event]),
                entity_id="synthetic-feature-stream",
                domain_id="synthetic",
                decision_context="fn=5;fp=1",
                policy_version="candidate-v1" if deployed_candidate else "incumbent-v1",
                reference_policy_version="incumbent-v1" if deployed_candidate else "candidate-v1",
                decision_cost_version="binary-fn5-fp1-v1",
            )
        )
        queried = bool(queried_mask[event])
        if event < horizon:
            query_eligible = (
                promotion_time < 0 or event <= promotion_time
            ) and labels_logged < label_budget
        else:
            elapsed = event - horizon
            query_eligible = (
                promoted
                and (rollback_time < 0 or elapsed <= rollback_time)
                and labels_logged < label_budget
            )
        if queried and not query_eligible:
            raise RuntimeError("query log violates the stage or hard-budget rule")
        propensity = query_rate if query_eligible else 0.0
        decisions.append(
            PolicyDecision(sample_id, event, action, reference_action, queried, propensity)
        )
        if queried:
            feedback.append(DecisionFeedback(sample_id, event, event, float(outcomes[event])))
            labels_logged += 1
    events = list(replay_decision_stream(requests, decisions, feedback))
    if len(events) != 2 * (2 * horizon) + len(feedback):
        raise RuntimeError("decision stream replay returned an unexpected event count")
    if any(isinstance(event, OracleDecisionRecord) for event in events):
        raise RuntimeError("evaluator-only oracle record leaked into learner replay")
    return len(events)


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 30,
    seed_offset: int = SEED_OFFSET,
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
    """Run a paired feature-dependent development grid; not a calibration study."""
    if seeds < 2 or horizon < 100:
        raise ValueError("seeds must be >=2 and horizon >=100")
    if not 0 < query_rate <= 1 or not 0 < budget_rate <= 1 or not 0 < alpha < 1:
        raise ValueError("query_rate, budget_rate and alpha must lie in (0,1]")
    if min(promotion_cost, rollback_cost, label_price) < 0:
        raise ValueError("costs must be nonnegative")
    query_generator = torch.Generator(device=device).manual_seed(seed_offset + 9_201_024)
    shared_query_uniforms = (
        torch.rand((seeds, 2 * horizon), generator=query_generator, device=device).cpu().numpy()
    )
    rows = []
    replay_count = None
    for scenario_index, scenario in enumerate(SCENARIOS):
        features, outcomes, gains, oracle = generate_feature_cost_streams(
            scenario=scenario,
            seeds=seeds,
            horizon=horizon,
            seed=seed_offset + scenario_index * 101_003,
            device=device,
            rollback_cost=rollback_cost,
        )
        # All methods see the same predictable query uniforms and potential-cost paths.
        benefit = oracle["expected_incumbent_minus_candidate_cost"]
        label_budget = int(np.floor(budget_rate * 2 * horizon))
        from .closed_loop_intervention import _simulate_gate

        gate = _simulate_gate(
            gains,
            shared_query_uniforms,
            query_rate=query_rate,
            label_budget=label_budget,
            alpha=alpha,
            promotion_cost=promotion_cost,
            rollback_cost=rollback_cost,
            horizon=horizon,
            gain_bound=GAIN_BOUND,
        )
        rows.append(
            _evaluate_methods(
                scenario=scenario,
                budget_rate=budget_rate,
                gains=gains,
                benefit=benefit,
                query_uniforms=shared_query_uniforms,
                seed_offset=seed_offset + scenario_index * 101_003,
                query_rate=query_rate,
                promotion_cost=promotion_cost,
                rollback_cost=rollback_cost,
                label_price=label_price,
                alpha=alpha,
                horizon=horizon,
                gain_bound=GAIN_BOUND,
            )
        )
        if scenario_index == 0:
            idx = 0
            queries = gate["queried_mask"][idx]
            replay_count = _replay_contract_smoke(
                features=features[idx],
                outcomes=outcomes[idx],
                queried_mask=queries,
                promoted=bool(gate["promoted"][idx]),
                promotion_time=int(gate["promotion_time"][idx]),
                rollback_time=int(gate["rollback_time"][idx]),
                horizon=horizon,
                query_rate=query_rate,
                label_budget=label_budget,
            )

    metrics = pd.concat(rows, ignore_index=True)
    metrics["query_rate"] = query_rate
    summary = (
        metrics.groupby(["scenario", "budget_rate", "method"], sort=True)
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
    contrasts = _paired_contrasts(metrics, bootstrap_replicates)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet = output / "metrics.parquet"
    metrics.to_parquet(parquet, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    contrasts.to_csv(output / "paired_utility_contrasts.csv", index=False)
    sources = {
        "feature_intervention.py": Path(__file__),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
        "streaming.py": Path(__file__).parents[1] / "data" / "streaming.py",
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development integration of certified promotion/rollback with feature-dependent paired decision costs",
        "status": "development_only_not_independent_calibration_or_confirmation",
        "scenarios": list(SCENARIOS),
        "methods": list(METHODS),
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "query_rate": query_rate,
        "budget_rate": budget_rate,
        "label_budget_rule": "floor(budget_rate * 2 * horizon)",
        "alpha_total": alpha,
        "stage_alpha": alpha / 2,
        "false_negative_cost": FALSE_NEGATIVE_COST,
        "false_positive_cost": FALSE_POSITIVE_COST,
        "cost_gain_support": [
            f"I/q * paired_gain - intervention_cost/horizon; |paired_gain| <= {GAIN_BOUND}",
            "monitor bound = max_abs_cost_difference/query_rate + amortized intervention cost per event",
        ],
        "filtration_assumptions": [
            "frozen candidate and incumbent actions are predictable from current features",
            "binary labels are immediate and reveal both potential action costs in this simulator",
            "query coin is drawn before and independently of the current outcome with logged fixed propensity",
            "independent event streams; rollback feedback follows the promotion phase",
            "the stage-specific conditional-mean null and known bounded support hold",
        ],
        "oracle_is_evaluator_only": True,
        "contract_replay_events_seed0_stationary": replay_count,
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()
        },
        "environment": environment(),
        "command": sys.argv,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Feature-dependent promotion/rollback development results",
        "",
        "This is a synthetic development screen, not calibration or confirmation. The candidate is frozen before each stream. Querying is randomized with a logged fixed propensity and bounded by a pathwise label cap. Both actions' costs are identifiable from each queried binary outcome in this simulator.",
        "",
        f"- Device: `{device}`; seeds per scenario: {seeds}; horizon: {horizon} events per phase.",
        f"- Query propensity: {query_rate}; total label cap: {budget_rate:.0%}; alpha: {alpha} split equally across promotion and rollback.",
        f"- Data rows: {len(metrics)}; all budget checks passed: {bool(metrics.budget_respected.all())}.",
        "- No figures were generated in this run.",
        "",
        "## Scenario means",
        "",
        summary.to_markdown(index=False),
        "",
        "## Paired expected-utility contrasts",
        "",
        contrasts.to_markdown(index=False),
        "",
        "## Limits",
        "",
        "Costs and shift schedules are controlled synthetic choices. The nominal error guarantees require the listed independent-stream, predictable-query, conditional-mean, bounded-support, frozen-candidate, and stage-specific assumptions. This screen cannot establish general validity, literature novelty, or real-world decision utility. False-alarm counts from this grid are descriptive and do not replace a frozen independent calibration.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return metrics, summary, contrasts, manifest


def run_sensitivity_grid(
    output_dir: str | Path,
    *,
    seeds: int = 30,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 400,
    query_rates: tuple[float, ...] = (0.40, 0.80),
    budget_rates: tuple[float, ...] = (0.20, 0.40),
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Paired, same-stream propensity by hard-budget development grid."""
    if not query_rates or not budget_rates:
        raise ValueError("query_rates and budget_rates must be nonempty")
    if any(not 0 < rate <= 1 for rate in query_rates + budget_rates):
        raise ValueError("all query and budget rates must lie in (0, 1]")
    root = Path(output_dir)
    all_metrics = []
    all_contrasts = []
    child_manifests = {}
    for query_rate in query_rates:
        for budget_rate in budget_rates:
            tag = f"q{round(query_rate * 100):02d}_b{round(budget_rate * 100):02d}"
            metrics, _summary, contrasts, manifest = run_grid(
                root / tag,
                seeds=seeds,
                seed_offset=seed_offset,
                horizon=horizon,
                query_rate=query_rate,
                budget_rate=budget_rate,
                device=device,
            )
            all_metrics.append(metrics)
            contrasts = contrasts.copy()
            contrasts["query_rate"] = query_rate
            all_contrasts.append(contrasts)
            child_manifests[tag] = {
                "metrics_sha256": manifest["metrics_sha256"],
                "promotion_rollback_null_status": manifest["status"],
            }
    metrics = pd.concat(all_metrics, ignore_index=True)
    contrasts = pd.concat(all_contrasts, ignore_index=True)
    summary = (
        metrics.groupby(["scenario", "query_rate", "budget_rate", "method"], sort=True)
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
    root.mkdir(parents=True, exist_ok=True)
    metrics_path = root / "sensitivity_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(root / "sensitivity_metrics.csv", index=False)
    summary.to_csv(root / "sensitivity_summary.csv", index=False)
    contrasts.to_csv(root / "sensitivity_paired_contrasts.csv", index=False)
    sources = {
        "feature_intervention.py": Path(__file__),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "paired development grid over query propensity and hard label budget",
        "status": "development_only_not_calibration_or_confirmation",
        "seeds_per_scenario_cell": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "query_rates": list(query_rates),
        "budget_rates": list(budget_rates),
        "common_random_numbers": "same per-scenario outcomes and query uniforms across propensity/budget cells",
        "scenarios": list(SCENARIOS),
        "methods": list(METHODS),
        "metric_rows": len(metrics),
        "all_budgets_respected": bool(metrics.budget_respected.all()),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "child_cells": child_manifests,
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()
        },
        "environment": environment(),
        "command": sys.argv,
    }
    (root / "sensitivity_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    report = [
        "# Feature-dependent intervention propensity and budget grid",
        "",
        "Paired development comparison over query propensity and hard label cap. All cells use identical outcome streams within each scenario; the same query-uniform stream is used so cap and propensity effects can be compared on matched paths.",
        "",
        f"- Query propensities: {list(query_rates)}; label budget fractions: {list(budget_rates)}.",
        f"- {seeds} seeds per scenario and cell; {len(metrics)} method-stream rows; all caps respected: {manifest['all_budgets_respected']}.",
        "- This screen is not a null calibration or independent confirmation.",
        "",
        "## Promotion and rollback results",
        "",
        summary[summary.method.eq("promotion_rollback")].to_markdown(index=False),
        "",
        "## Paired utility contrasts",
        "",
        contrasts.to_markdown(index=False),
        "",
        "No figures were generated. Any follow-up selection must be followed by fresh, disjoint null calibration and alternative confirmation.",
    ]
    (root / "sensitivity_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return metrics, summary, contrasts, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/feature_intervention_development")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--query-rate", type=float, default=0.80)
    parser.add_argument("--budget-rate", type=float, default=0.40)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, contrasts, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rate=args.query_rate,
        budget_rate=args.budget_rate,
        device=args.device,
    )
    print(summary.to_string(index=False))
    print(contrasts.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


def sensitivity_main() -> None:
    parser = argparse.ArgumentParser(
        description="Run paired propensity and budget sensitivity grid"
    )
    parser.add_argument("--output-dir", default="outputs/feature_intervention_grid")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--query-rates", type=float, nargs="+", default=[0.40, 0.80])
    parser.add_argument("--budget-rates", type=float, nargs="+", default=[0.20, 0.40])
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, contrasts, manifest = run_sensitivity_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rates=tuple(args.query_rates),
        budget_rates=tuple(args.budget_rates),
        device=args.device,
    )
    print(summary[summary.method.eq("promotion_rollback")].to_string(index=False))
    print(contrasts.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
