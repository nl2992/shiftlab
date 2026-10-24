"""Compare global versus stratum-wise certified promotion and rollback.

The stratum-wise rule is a Bonferroni composition of the existing bounded e-process gate,
not a new test. This synthetic benchmark asks whether keeping policy decisions local to
visible contexts improves utility when decision gains become heterogeneous across contexts.
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
from .closed_loop_intervention import _evaluate_methods, _simulate_gate

SCENARIOS = (
    "stationary_null",
    "benign_nuisance",
    "persistent_benefit",
    "homogeneous_reversal",
    "heterogeneous_reversal",
    "rollback_boundary_global",
    "rollback_boundary_stratified",
)
METHODS = (
    "continue",
    "unconditional_promote",
    "promotion_only",
    "promotion_rollback",
    "stratified_promotion_rollback",
)
QUERY_RATES = (0.40, 0.80)
BUDGET_RATES = (0.20, 0.40)
SEED_OFFSET = 80_102_024
FN_COST = 5.0
FP_COST = 1.0
GAIN_BOUND = 5.0
PROMOTION_COST = 0.05
ROLLBACK_COST = 0.05
LABEL_PRICE = 0.01
ALPHA = 0.05
N_STRATA = 2


def _candidate_probabilities(
    scenario: str, horizon: int, rollback_cost: float = ROLLBACK_COST
) -> tuple[np.ndarray, np.ndarray]:
    """Return candidate-region positive-outcome probabilities by phase and context."""
    shadow = np.full(N_STRATA, 1 / 6, dtype=float)
    deployment = shadow.copy()
    if scenario == "persistent_benefit":
        shadow[:] = deployment[:] = 0.50
    elif scenario == "homogeneous_reversal":
        shadow[:] = 0.50
        deployment[:] = 0.05
    elif scenario == "heterogeneous_reversal":
        shadow[:] = 0.50
        deployment[:] = (0.30, 0.01)
    elif scenario == "rollback_boundary_global":
        shadow[:] = 0.50
        deployment[:] = (1 - 2 * rollback_cost / horizon) / 6
    elif scenario == "rollback_boundary_stratified":
        shadow[:] = 0.50
        stratum_horizon = horizon // N_STRATA
        deployment[:] = (1 - 2 * rollback_cost / stratum_horizon) / 6
    elif scenario not in {"stationary_null", "benign_nuisance"}:
        raise ValueError(f"unknown contextual scenario {scenario!r}")
    return shadow, deployment


def generate_contextual_streams(
    *,
    scenario: str,
    seeds: int,
    horizon: int,
    seed: int,
    device: str,
    rollback_cost: float = ROLLBACK_COST,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate balanced, visible contexts and paired costs on CPU or CUDA."""
    if scenario not in SCENARIOS or seeds < 1 or horizon < 200 or horizon % 2:
        raise ValueError("scenario, seeds or even horizon is invalid (horizon must be >=200)")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")
    generator = torch.Generator(device=device).manual_seed(seed)
    total_events = 2 * horizon
    features = torch.randn((seeds, total_events, 8), generator=generator, device=device)
    stratum = torch.arange(total_events, device=device, dtype=torch.long) % N_STRATA
    # A visible, deterministic context identifier makes the two independent streams explicit.
    features[:, :, 1] = torch.where(stratum == 0, -1.0, 1.0)
    if scenario == "benign_nuisance":
        features[:, horizon:, 2:] += 3.0

    candidate_region = features[:, :, 0] > 0
    candidate_probability = torch.as_tensor(
        np.vstack(_candidate_probabilities(scenario, horizon, rollback_cost)),
        device=device,
        dtype=features.dtype,
    )
    phase = torch.arange(total_events, device=device) >= horizon
    p_candidate = candidate_probability[phase.long(), stratum]
    p = torch.where(candidate_region, p_candidate, torch.full_like(p_candidate, 0.25))
    outcomes = (torch.rand((seeds, total_events), generator=generator, device=device) < p).to(
        features.dtype
    )
    incumbent_cost = FN_COST * outcomes
    candidate_cost = torch.where(
        candidate_region,
        FP_COST * (1.0 - outcomes),
        FN_COST * outcomes,
    )
    gains = incumbent_cost - candidate_cost
    expected_by_stratum = np.stack(
        [
            0.5 * (6 * probability - 1)
            for probability in _candidate_probabilities(scenario, horizon, rollback_cost)
        ],
        axis=0,
    )
    event_context = (np.arange(total_events) % N_STRATA).astype(int)
    expected_event_gain = expected_by_stratum[
        (np.arange(total_events) >= horizon).astype(int), event_context
    ]
    features_np = features.cpu().numpy()
    outcomes_np = outcomes.cpu().numpy().astype(np.int8)
    gains_np = gains.cpu().numpy().astype(float)
    return features_np, outcomes_np, gains_np, expected_event_gain


def _stratified_gate(
    *,
    gains: np.ndarray,
    query_uniforms: np.ndarray,
    contexts: np.ndarray,
    horizon: int,
    query_rate: float,
    budget_rate: float,
    alpha: float,
    promotion_cost: float,
    rollback_cost: float,
) -> tuple[list[dict], dict]:
    per_group_horizon = horizon // N_STRATA
    total_budget = int(np.floor(budget_rate * 2 * horizon))
    group_budget = int(np.floor(budget_rate * 2 * per_group_horizon))
    if group_budget * N_STRATA > total_budget:
        raise RuntimeError("per-stratum budgets exceed the total hard label cap")

    group_gates = []
    group_indices = []
    for group in range(N_STRATA):
        indices = np.flatnonzero(contexts == group)
        if len(indices) != 2 * per_group_horizon:
            raise RuntimeError("context stream is not balanced across phases")
        gate = _simulate_gate(
            gains[:, indices],
            query_uniforms[:, indices],
            query_rate=query_rate,
            label_budget=group_budget,
            alpha=alpha / N_STRATA,
            promotion_cost=promotion_cost,
            rollback_cost=rollback_cost,
            horizon=per_group_horizon,
            gain_bound=GAIN_BOUND,
        )
        group_gates.append(gate)
        group_indices.append(indices)

    promoted = np.stack([gate["promoted"] for gate in group_gates], axis=1)
    rolled_back = np.stack([gate["rolled_back"] for gate in group_gates], axis=1)
    promotion_time = np.stack([gate["promotion_time"] for gate in group_gates], axis=1)
    rollback_time = np.stack([gate["rollback_time"] for gate in group_gates], axis=1)
    labels = np.stack([gate["labels_queried"] for gate in group_gates], axis=1)
    lengths = np.where(rolled_back, rollback_time + 1, per_group_horizon)
    lengths = np.where(promoted, lengths, 0)
    row = {
        "promoted_groups": promoted,
        "rolled_back_groups": rolled_back,
        "promotion_times_by_group": promotion_time,
        "rollback_times_by_group": rollback_time,
        "labels_by_group": labels,
        "deployment_lengths_by_group": lengths,
        "labels_queried": labels.sum(axis=1),
        "label_budget": total_budget,
        "budget_respected": labels.sum(axis=1) <= total_budget,
        "familywise_false_promotion": promoted.any(axis=1),
        "familywise_false_rollback": rolled_back.any(axis=1),
    }
    return group_gates, row


def _summarize_stratified_streams(
    *,
    scenario: str,
    seed_offset: int,
    gains: np.ndarray,
    contexts: np.ndarray,
    expected_event_gain: np.ndarray,
    horizon: int,
    budget_rate: float,
    query_rate: float,
    alpha: float,
    query_uniforms: np.ndarray,
    bootstrap_replicates: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _, gate = _stratified_gate(
        gains=gains,
        query_uniforms=query_uniforms,
        contexts=contexts,
        horizon=horizon,
        query_rate=query_rate,
        budget_rate=budget_rate,
        alpha=alpha,
        promotion_cost=PROMOTION_COST,
        rollback_cost=ROLLBACK_COST,
    )
    streams = len(gains)
    group_lengths = gate["deployment_lengths_by_group"]
    realized_benefit = np.zeros(streams, dtype=float)
    expected_benefit = np.zeros(streams, dtype=float)
    for group in range(N_STRATA):
        indices = np.flatnonzero(contexts == group)
        deployment_indices = indices[horizon // N_STRATA :]
        cumulative_realized = np.cumsum(gains[:, deployment_indices], axis=1)
        group_expected = expected_event_gain[deployment_indices]
        cumulative_expected = np.cumsum(group_expected)
        lengths = group_lengths[:, group]
        active = lengths > 0
        realized_benefit[active] += cumulative_realized[np.flatnonzero(active), lengths[active] - 1]
        expected_benefit[active] += cumulative_expected[lengths[active] - 1]

    promoted_count = gate["promoted_groups"].sum(axis=1)
    rollback_count = gate["rolled_back_groups"].sum(axis=1)
    realized_utility = (
        realized_benefit
        - promoted_count * PROMOTION_COST
        - rollback_count * ROLLBACK_COST
        - gate["labels_queried"] * LABEL_PRICE
    )
    expected_utility = (
        expected_benefit
        - promoted_count * PROMOTION_COST
        - rollback_count * ROLLBACK_COST
        - gate["labels_queried"] * LABEL_PRICE
    )
    deployment_expected = expected_event_gain[horizon:]
    harmful_groups = np.array(
        [np.mean(deployment_expected[contexts[horizon:] == group]) < 0 for group in range(2)]
    )
    safe_groups = ~harmful_groups
    rows = []
    for i in range(streams):
        rows.append(
            {
                "scenario": scenario,
                "seed": seed_offset + i,
                "method": "stratified_promotion_rollback",
                "promoted": bool(gate["promoted_groups"][i].any()),
                "promoted_groups": int(promoted_count[i]),
                "rolled_back": bool(gate["rolled_back_groups"][i].any()),
                "rolled_back_groups": int(rollback_count[i]),
                "harmful_groups_rolled_back": int(
                    (gate["rolled_back_groups"][i] & harmful_groups).sum()
                ),
                "safe_groups_retained": int(
                    (
                        gate["promoted_groups"][i] & ~gate["rolled_back_groups"][i] & safe_groups
                    ).sum()
                ),
                "candidate_events_deployed": int(group_lengths[i].sum()),
                "candidate_events_by_group": group_lengths[i].tolist(),
                "promotion_time_by_group": gate["promotion_times_by_group"][i].tolist(),
                "rollback_time_by_group": gate["rollback_times_by_group"][i].tolist(),
                "labels_queried": int(gate["labels_queried"][i]),
                "labels_by_group": gate["labels_by_group"][i].tolist(),
                "label_budget": gate["label_budget"],
                "budget_respected": bool(gate["budget_respected"][i]),
                "false_promotion_under_null": bool(
                    scenario in {"stationary_null", "benign_nuisance"}
                    and gate["familywise_false_promotion"][i]
                ),
                "false_rollback_under_null": bool(
                    scenario
                    in {
                        "stationary_null",
                        "benign_nuisance",
                        "persistent_benefit",
                        "rollback_boundary_global",
                        "rollback_boundary_stratified",
                    }
                    and gate["familywise_false_rollback"][i]
                ),
                "realized_net_utility": float(realized_utility[i]),
                "expected_net_utility": float(expected_utility[i]),
                "oracle_expected_benefit_before_costs": float(expected_benefit[i]),
                "switching_cost": float(promoted_count[i] * PROMOTION_COST),
                "rollback_cost": float(rollback_count[i] * ROLLBACK_COST),
                "label_price_total": float(gate["labels_queried"][i] * LABEL_PRICE),
                "promotion_alpha_per_stratum": alpha / (2 * N_STRATA),
                "rollback_alpha_per_stratum": alpha / (2 * N_STRATA),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(
        {
            "scenario": [scenario],
            "strata": [N_STRATA],
            "stratified_familywise_alpha": [alpha],
            "per_stratum_label_budget": [int(np.floor(budget_rate * horizon))],
            "total_label_budget": [int(np.floor(budget_rate * 2 * horizon))],
        }
    )


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 500,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 400,
    query_rates: tuple[float, ...] = QUERY_RATES,
    budget_rates: tuple[float, ...] = BUDGET_RATES,
    device: str = "cuda",
    bootstrap_replicates: int = 2_000,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2 or horizon < 200 or horizon % 2 or bootstrap_replicates < 100:
        raise ValueError("seeds >=2, even horizon >=200, and bootstrap >=100 required")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")
    for name, values, lower, upper, upper_inclusive in (
        ("query_rates", query_rates, 0.0, 1.0, True),
        ("budget_rates", budget_rates, 0.0, 1.0, True),
    ):
        if tuple(sorted(set(values))) != values or any(
            value <= lower or (value > upper if upper_inclusive else value >= upper)
            for value in values
        ):
            raise ValueError(f"{name} must be sorted, unique and in (0,1]")

    rows = []
    source_files = {
        "contextual_stratified_intervention.py": Path(__file__),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "streaming.py": Path(__file__).parents[1] / "data" / "streaming.py",
    }
    all_caps = True
    for scenario_index, scenario in enumerate(SCENARIOS):
        features, outcomes, gains, expected_event_gain = generate_contextual_streams(
            scenario=scenario,
            seeds=seeds,
            horizon=horizon,
            seed=seed_offset + scenario_index * 107_003,
            device=device,
        )
        del outcomes
        contexts = np.arange(2 * horizon, dtype=int) % N_STRATA
        for q in query_rates:
            query_generator = torch.Generator(device=device).manual_seed(
                seed_offset + scenario_index * 107_003 + int(q * 100_000) + 38_102_024
            )
            query_uniforms = (
                torch.rand((seeds, 2 * horizon), generator=query_generator, device=device)
                .cpu()
                .numpy()
            )
            for budget_rate in budget_rates:
                baseline = _evaluate_methods(
                    scenario=scenario,
                    budget_rate=budget_rate,
                    gains=gains,
                    benefit=expected_event_gain,
                    query_uniforms=query_uniforms,
                    seed_offset=seed_offset,
                    query_rate=q,
                    promotion_cost=PROMOTION_COST,
                    rollback_cost=ROLLBACK_COST,
                    label_price=LABEL_PRICE,
                    alpha=ALPHA,
                    horizon=horizon,
                    gain_bound=GAIN_BOUND,
                )
                for row in baseline.to_dict(orient="records"):
                    row["query_rate"] = q
                    row["strata"] = 1
                    row["stratified_familywise_alpha"] = None
                    rows.append(row)
                stratified, _ = _summarize_stratified_streams(
                    scenario=scenario,
                    seed_offset=seed_offset,
                    gains=gains,
                    contexts=contexts,
                    expected_event_gain=expected_event_gain,
                    horizon=horizon,
                    budget_rate=budget_rate,
                    query_rate=q,
                    alpha=ALPHA,
                    query_uniforms=query_uniforms,
                    bootstrap_replicates=bootstrap_replicates,
                )
                stratified["query_rate"] = q
                stratified["budget_rate"] = budget_rate
                stratified["strata"] = N_STRATA
                stratified["stratified_familywise_alpha"] = ALPHA
                rows.extend(stratified.to_dict(orient="records"))
                all_caps &= bool(stratified.budget_respected.all())
        del features

    metrics = pd.DataFrame(rows)
    metrics["budget_respected"] = metrics["budget_respected"].fillna(
        metrics.labels_queried <= np.floor(metrics.budget_rate * 2 * horizon)
    )
    all_caps = bool(metrics.budget_respected.all()) and all_caps
    contrasts = []
    for (scenario, q, budget_rate), group in metrics.groupby(
        ["scenario", "query_rate", "budget_rate"], sort=True
    ):
        wide = group.pivot(index="seed", columns="method", values="realized_net_utility")
        for method, reference in (
            ("stratified_promotion_rollback", "continue"),
            ("stratified_promotion_rollback", "promotion_rollback"),
            ("stratified_promotion_rollback", "promotion_only"),
            ("promotion_rollback", "continue"),
        ):
            difference = (wide[method] - wide[reference]).to_numpy(dtype=float)
            rng = np.random.default_rng(seed_offset + len(contrasts) + 85_102_024)
            samples = rng.integers(0, seeds, size=(bootstrap_replicates, seeds))
            interval = np.quantile(difference[samples].mean(axis=1), [0.025, 0.975])
            contrasts.append(
                {
                    "scenario": scenario,
                    "query_rate": q,
                    "budget_rate": budget_rate,
                    "method": method,
                    "reference": reference,
                    "paired_mean_realized_utility_difference": float(difference.mean()),
                    "seed_bootstrap_ci95_low": float(interval[0]),
                    "seed_bootstrap_ci95_high": float(interval[1]),
                    "seed_clusters": seeds,
                }
            )
    contrast_frame = pd.DataFrame(contrasts)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    contrast_frame.to_csv(output / "paired_contrasts.csv", index=False)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development comparison of global and stratum-wise composition of the established promotion/rollback e-process",
        "status": "development_only_no_independent_calibration_or_confirmation",
        "scenarios": list(SCENARIOS),
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "strata": N_STRATA,
        "query_rates": list(query_rates),
        "budget_rates": list(budget_rates),
        "alpha_total": ALPHA,
        "per_stratum_alpha": ALPHA / N_STRATA,
        "per_stage_per_stratum_alpha": ALPHA / (2 * N_STRATA),
        "gain_support": GAIN_BOUND,
        "promotion_cost_per_promoted_stratum": PROMOTION_COST,
        "rollback_cost_per_rolled_back_stratum": ROLLBACK_COST,
        "label_price": LABEL_PRICE,
        "evaluator_oracle_used_by_policy": False,
        "stratum_assignment_visible_and_balanced": True,
        "all_label_caps_respected": all_caps,
        "metric_rows": len(metrics),
        "contrast_rows": len(contrast_frame),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_files.items()
        },
        "environment": environment(),
        "command": sys.argv,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    focus = contrast_frame.loc[
        contrast_frame.scenario.eq("heterogeneous_reversal")
        & contrast_frame.method.eq("stratified_promotion_rollback")
    ]
    report = [
        "# Contextual stratified intervention development grid",
        "",
        f"Status: **{manifest['status']}**; {len(metrics):,} stream-method rows; {len(contrast_frame):,} paired contrasts; device: {device}.",
        "",
        "The learner observes a balanced context identifier. In the heterogeneous reversal profile, shadow gain is positive in both contexts, then deployment gain becomes positive in one context and negative in the other. Global and stratum-wise gates use the same paired outcomes, query paths, query rate, and total hard label cap. The stratum-wise method applies the existing bounded e-process separately to each context, allocating alpha across strata and stages by Bonferroni. This is a standard composition, not a new test.",
        "",
        "## Stratified versus global gate under heterogeneous reversal",
        "",
        "| Query rate | Label cap | Stratified minus global expected utility | Realized utility contrast | 95% paired interval | Mean rollback groups | Mean safe groups retained | Mean labels / cap |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    group_summary = (
        metrics.loc[
            metrics.scenario.eq("heterogeneous_reversal")
            & metrics.method.eq("stratified_promotion_rollback")
        ]
        .groupby(["query_rate", "budget_rate"], as_index=False)
        .agg(
            expected_utility=("expected_net_utility", "mean"),
            rolled_back_groups=("rolled_back_groups", "mean"),
            safe_groups_retained=("safe_groups_retained", "mean"),
            labels_queried=("labels_queried", "mean"),
            label_budget=("label_budget", "first"),
            label_cap_ok=("budget_respected", "all"),
        )
    )
    for row in group_summary.itertuples(index=False):
        contrast = focus.loc[
            focus.query_rate.eq(row.query_rate)
            & focus.budget_rate.eq(row.budget_rate)
            & focus.reference.eq("promotion_rollback")
        ].iloc[0]
        global_mean = metrics.loc[
            metrics.scenario.eq("heterogeneous_reversal")
            & metrics.query_rate.eq(row.query_rate)
            & metrics.budget_rate.eq(row.budget_rate)
            & metrics.method.eq("promotion_rollback"),
            "expected_net_utility",
        ].mean()
        report.append(
            f"| {row.query_rate:.0%} | {row.budget_rate:.0%} | {row.expected_utility - global_mean:.2f} | {contrast.paired_mean_realized_utility_difference:.2f} | [{contrast.seed_bootstrap_ci95_low:.2f}, {contrast.seed_bootstrap_ci95_high:.2f}] | {row.rolled_back_groups:.2f} | {row.safe_groups_retained:.2f} | {row.labels_queried:.1f} / {row.label_budget} |"
        )
    report.extend(
        [
            "",
            "Every row is a development comparison. Context-specific rollback is evaluated on a deliberately visible and balanced context; no hidden regime label or evaluator expected gain enters either policy. Both procedures share the total hard budget. Null alarms in this screen are diagnostics only; independent calibration is required before any error-control claim.",
            "",
            "The method is the standard per-stratum bounded e-process with a Bonferroni alpha split. Any gain would support context-local intervention in this DGP, not algorithmic novelty or general superiority. No figure was generated; all research visuals must use PaperBanana.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "uv run shiftlab-dive-contextual-stratified-grid --seeds 500 --horizon 400 --device cuda --output-dir outputs/contextual_stratified_grid_500",
            "```",
        ]
    )
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return metrics, contrast_frame, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--query-rates", type=float, nargs="+", default=QUERY_RATES)
    parser.add_argument("--budget-rates", type=float, nargs="+", default=BUDGET_RATES)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=2_000)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/contextual_stratified_grid")
    )
    args = parser.parse_args()
    metrics, contrasts, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rates=tuple(args.query_rates),
        budget_rates=tuple(args.budget_rates),
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "metric_rows": len(metrics),
                "contrast_rows": len(contrasts),
                "all_label_caps_respected": manifest["all_label_caps_respected"],
                "metrics_sha256": manifest["metrics_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
