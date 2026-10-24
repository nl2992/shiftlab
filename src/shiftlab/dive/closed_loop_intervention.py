"""CUDA-generated development grid for certified promotion and rollback."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp
from scipy.stats import beta

from ..data.gpu.environment import environment
from .promotion_timing import _generate_costs

HORIZON = 800
SCENARIOS = (
    "no_benefit",
    "persistent_benefit",
    "shadow_only_benefit",
    "early_reversal",
    "late_benefit",
    "weak_persistent_benefit",
)
METHODS = ("continue", "unconditional_promote", "promotion_only", "promotion_rollback")
DEFAULT_STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
SEED_OFFSET = 31_404_026


def benefit_schedule(scenario: str, horizon: int = HORIZON) -> np.ndarray:
    """Return evaluator-only mean incumbent-minus-candidate cost by event."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    shadow = np.zeros(horizon, dtype=float)
    deployment = np.zeros(horizon, dtype=float)
    if scenario == "persistent_benefit":
        shadow[:] = 0.30
        deployment[:] = 0.12
    elif scenario == "shadow_only_benefit":
        shadow[:] = 0.30
    elif scenario == "early_reversal":
        shadow[:] = 0.30
        deployment[: max(1, horizon // 10)] = 0.30
        deployment[max(1, horizon // 10) :] = -0.15
    elif scenario == "late_benefit":
        deployment[:] = 0.30
    elif scenario == "weak_persistent_benefit":
        shadow[:] = 0.10
        deployment[:] = 0.08
    return np.concatenate((shadow, deployment))


def _update_mixture(
    log_wealth: np.ndarray,
    values: np.ndarray,
    active: np.ndarray,
    *,
    bound: float,
) -> np.ndarray:
    if active.any():
        factors = 1.0 + np.asarray(DEFAULT_STAKES)[None, :] * values[active, None] / bound
        if np.any(factors <= 0):
            raise ValueError("an intervention increment fell outside its betting support")
        log_wealth[active] += np.log(factors)
    return logsumexp(log_wealth - np.log(len(DEFAULT_STAKES)), axis=1)


def _simulate_gate(
    gains: np.ndarray,
    query_uniforms: np.ndarray,
    *,
    query_rate: float,
    label_budget: int,
    alpha: float,
    promotion_cost: float,
    rollback_cost: float,
    horizon: int,
    gain_bound: float = 1.0,
) -> dict[str, np.ndarray]:
    """Vectorized form of CertifiedPromotionRollback for paired seed streams.

    ``gain_bound`` is a known bound on the absolute paired cost difference before
    querying. The default preserves the original Bernoulli-cost benchmark; callers
    with feature-dependent decision costs must pass their actual cost bound.
    """
    streams, total_events = gains.shape
    if total_events != 2 * horizon or query_uniforms.shape != gains.shape:
        raise ValueError("gains and query uniforms must cover shadow plus deployment")
    if not 0 < query_rate <= 1 or label_budget < 0:
        raise ValueError("query_rate must be in (0,1] and label_budget nonnegative")
    if not np.isfinite(gain_bound) or gain_bound <= 0:
        raise ValueError("gain_bound must be finite and positive")

    promotion_alpha = rollback_alpha = alpha / 2
    promotion_rate = promotion_cost / horizon
    rollback_rate = rollback_cost / horizon
    promotion_bound = gain_bound / query_rate + promotion_rate
    rollback_bound = gain_bound / query_rate + rollback_rate
    stakes = np.asarray(DEFAULT_STAKES, dtype=float)
    promotion_log_wealth = np.zeros((streams, len(stakes)), dtype=float)
    rollback_log_wealth = np.zeros((streams, len(stakes)), dtype=float)
    promotion_threshold = -np.log(promotion_alpha)
    rollback_threshold = -np.log(rollback_alpha)

    labels = np.zeros(streams, dtype=np.int64)
    shadow_labels = np.zeros(streams, dtype=np.int64)
    deployment_labels = np.zeros(streams, dtype=np.int64)
    queried_mask = np.zeros((streams, total_events), dtype=bool)
    promoted = np.zeros(streams, dtype=bool)
    promotion_time = np.full(streams, -1, dtype=np.int64)
    for event in range(horizon):
        active = ~promoted & (labels < label_budget)
        queried = active & (query_uniforms[:, event] < query_rate)
        queried_mask[:, event] = queried
        labels += queried
        shadow_labels += queried
        gain_estimate = np.where(queried, gains[:, event] / query_rate, 0.0)
        increment = gain_estimate - promotion_rate
        log_e = _update_mixture(
            promotion_log_wealth,
            increment,
            active,
            bound=promotion_bound,
        )
        crossed = active & (log_e >= promotion_threshold)
        promoted[crossed] = True
        promotion_time[crossed] = event

    rollback = np.zeros(streams, dtype=bool)
    rollback_time = np.full(streams, -1, dtype=np.int64)
    for event in range(horizon):
        active = promoted & ~rollback & (labels < label_budget)
        queried = active & (query_uniforms[:, horizon + event] < query_rate)
        queried_mask[:, horizon + event] = queried
        labels += queried
        deployment_labels += queried
        gain_estimate = np.where(queried, gains[:, horizon + event] / query_rate, 0.0)
        increment = -gain_estimate - rollback_rate
        log_e = _update_mixture(
            rollback_log_wealth,
            increment,
            active,
            bound=rollback_bound,
        )
        crossed = active & (log_e >= rollback_threshold)
        rollback[crossed] = True
        rollback_time[crossed] = event

    return {
        "promoted": promoted,
        "promotion_time": promotion_time,
        "rolled_back": rollback,
        "rollback_time": rollback_time,
        "labels_queried": labels,
        "shadow_labels_queried": shadow_labels,
        "deployment_labels_queried": deployment_labels,
        "queried_mask": queried_mask,
        "budget_respected": labels <= label_budget,
        "promotion_alpha": np.full(streams, promotion_alpha),
        "rollback_alpha": np.full(streams, rollback_alpha),
    }


def _evaluate_methods(
    *,
    scenario: str,
    budget_rate: float,
    gains: np.ndarray,
    benefit: np.ndarray,
    query_uniforms: np.ndarray,
    seed_offset: int,
    query_rate: float,
    promotion_cost: float,
    rollback_cost: float,
    label_price: float,
    alpha: float,
    horizon: int,
    gain_bound: float = 1.0,
) -> pd.DataFrame:
    label_budget = int(np.floor(budget_rate * 2 * horizon))
    gate = _simulate_gate(
        gains,
        query_uniforms,
        query_rate=query_rate,
        label_budget=label_budget,
        alpha=alpha,
        promotion_cost=promotion_cost,
        rollback_cost=rollback_cost,
        horizon=horizon,
        gain_bound=gain_bound,
    )
    streams = len(gains)
    rows = []
    for method in METHODS:
        if method == "continue":
            promoted = np.zeros(streams, dtype=bool)
            rolled_back = np.zeros(streams, dtype=bool)
            promotion_time = np.full(streams, -1, dtype=int)
            rollback_time = np.full(streams, -1, dtype=int)
            labels = np.zeros(streams, dtype=int)
        elif method == "unconditional_promote":
            promoted = np.ones(streams, dtype=bool)
            rolled_back = np.zeros(streams, dtype=bool)
            promotion_time = np.full(streams, -1, dtype=int)
            rollback_time = np.full(streams, -1, dtype=int)
            labels = np.zeros(streams, dtype=int)
        elif method == "promotion_only":
            promoted = gate["promoted"]
            rolled_back = np.zeros(streams, dtype=bool)
            promotion_time = gate["promotion_time"]
            rollback_time = np.full(streams, -1, dtype=int)
            # This comparator only queries until promotion and never monitors rollback.
            labels = gate["shadow_labels_queried"]
        else:
            promoted = gate["promoted"]
            rolled_back = gate["rolled_back"]
            promotion_time = gate["promotion_time"]
            rollback_time = gate["rollback_time"]
            labels = gate["labels_queried"]

        deployment_lengths = np.where(rolled_back, rollback_time + 1, horizon)
        deployment_lengths = np.where(promoted, deployment_lengths, 0)
        cumulative_realized = np.cumsum(gains[:, horizon:], axis=1)
        cumulative_expected = np.cumsum(benefit[horizon:])
        realized_benefit = np.where(
            deployment_lengths > 0,
            cumulative_realized[np.arange(streams), np.maximum(deployment_lengths - 1, 0)],
            0.0,
        )
        expected_benefit = np.where(
            deployment_lengths > 0,
            cumulative_expected[np.maximum(deployment_lengths - 1, 0)],
            0.0,
        )
        realized_utility = (
            realized_benefit
            - promoted.astype(float) * promotion_cost
            - rolled_back.astype(float) * rollback_cost
            - labels * label_price
        )
        expected_utility = (
            expected_benefit
            - promoted.astype(float) * promotion_cost
            - rolled_back.astype(float) * rollback_cost
            - labels * label_price
        )
        promotion_null = np.all(benefit[:horizon] <= promotion_cost / horizon)
        rollback_null = np.all(benefit[horizon:] >= -rollback_cost / horizon)
        false_promotion = promotion_null & promoted
        false_rollback = rollback_null & rolled_back
        for index in range(streams):
            rows.append(
                {
                    "scenario": scenario,
                    "budget_rate": budget_rate,
                    "method": method,
                    "seed": seed_offset + index,
                    "promoted": bool(promoted[index]),
                    "promotion_time": int(promotion_time[index])
                    if promotion_time[index] >= 0
                    else None,
                    "rolled_back": bool(rolled_back[index]),
                    "rollback_time": int(rollback_time[index])
                    if rollback_time[index] >= 0
                    else None,
                    "candidate_events_deployed": int(deployment_lengths[index]),
                    "labels_queried": int(labels[index]),
                    "label_budget": label_budget,
                    "budget_respected": bool(labels[index] <= label_budget),
                    "false_promotion_under_null": bool(false_promotion[index]),
                    "false_rollback_under_null": bool(false_rollback[index]),
                    "realized_net_utility": float(realized_utility[index]),
                    "expected_net_utility": float(expected_utility[index]),
                    "oracle_expected_benefit_before_costs": float(expected_benefit[index]),
                    "switching_cost": promotion_cost if promoted[index] else 0.0,
                    "rollback_cost": rollback_cost if rolled_back[index] else 0.0,
                    "label_price_total": float(labels[index] * label_price),
                    "promotion_alpha": alpha / 2
                    if method in {"promotion_only", "promotion_rollback"}
                    else None,
                    "rollback_alpha": alpha / 2 if method == "promotion_rollback" else None,
                }
            )
    return pd.DataFrame(rows)


def _paired_contrasts(metrics: pd.DataFrame, bootstrap_replicates: int) -> pd.DataFrame:
    rows = []
    for (scenario, budget_rate), group in metrics.groupby(["scenario", "budget_rate"], sort=True):
        wide = group.pivot(index="seed", columns="method", values="expected_net_utility")
        for method, reference in (
            ("promotion_rollback", "promotion_only"),
            ("promotion_rollback", "continue"),
            ("promotion_only", "continue"),
        ):
            differences = (wide[method] - wide[reference]).to_numpy(dtype=float)
            rng = np.random.default_rng(31_404_026 + len(rows))
            samples = rng.integers(
                0,
                len(differences),
                size=(bootstrap_replicates, len(differences)),
            )
            interval = np.quantile(differences[samples].mean(axis=1), [0.025, 0.975])
            rows.append(
                {
                    "scenario": scenario,
                    "budget_rate": budget_rate,
                    "method": method,
                    "reference": reference,
                    "paired_mean_expected_utility_difference": float(differences.mean()),
                    "seed_cluster_ci95_low": float(interval[0]),
                    "seed_cluster_ci95_high": float(interval[1]),
                    "seed_clusters": len(differences),
                }
            )
    return pd.DataFrame(rows)


def _calibration(metrics: pd.DataFrame, alpha: float) -> pd.DataFrame:
    rows = []
    cells = [
        (scenario, method, "false_promotion_under_null")
        for scenario in ("no_benefit", "late_benefit")
        for method in ("promotion_only", "promotion_rollback")
    ]
    cells.extend(
        (scenario, "promotion_rollback", "false_rollback_under_null")
        for scenario in (
            "no_benefit",
            "persistent_benefit",
            "shadow_only_benefit",
            "late_benefit",
            "weak_persistent_benefit",
        )
    )
    groups = []
    for (scenario, _budget), all_rows in metrics.groupby(["scenario", "budget_rate"]):
        for cell_scenario, method, field in cells:
            if cell_scenario == scenario:
                groups.append((scenario, method, field, all_rows[all_rows.method.eq(method)]))
    family_alpha = alpha / max(1, len(groups))
    for scenario, method, field, group in groups:
        events, n = int(group[field].sum()), len(group)
        upper = 1.0 if events == n else float(beta.ppf(1 - family_alpha, events + 1, n - events))
        rows.append(
            {
                "scenario": scenario,
                "budget_rate": float(group.budget_rate.iloc[0]),
                "method": method,
                "error_type": field,
                "events": events,
                "streams": n,
                "rate": events / n,
                "familywise_one_sided_cp95_upper": upper,
                "familywise_alpha": alpha,
                "family_cells": len(groups),
                "component_alpha": alpha / 2,
            }
        )
    return pd.DataFrame(rows)


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 2000,
    seed_offset: int = SEED_OFFSET,
    horizon: int = HORIZON,
    query_rate: float = 0.25,
    budget_rates: tuple[float, ...] = (0.2, 0.4),
    alpha: float = 0.05,
    promotion_cost: float = 0.05,
    rollback_cost: float = 0.05,
    label_price: float = 0.01,
    device: str = "cuda",
    bootstrap_replicates: int = 10_000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2 or horizon < 100:
        raise ValueError("seeds must be >=2 and horizon >=100")
    if not 0 < query_rate <= 1 or not 0 < alpha < 1:
        raise ValueError("query_rate and alpha must lie in (0,1)")
    if tuple(sorted(set(budget_rates))) != budget_rates or any(
        not 0 < rate <= 1 for rate in budget_rates
    ):
        raise ValueError("budget_rates must be sorted, unique, and in (0,1]")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    if device not in {"cuda", "cpu"}:
        raise ValueError("device must be cuda or cpu")
    if not np.isfinite(label_price) or label_price < 0:
        raise ValueError("label_price must be finite and nonnegative")

    # A single seeded CUDA stream supplies common paired potential-cost and query paths.
    generator = torch.Generator(device=device).manual_seed(seed_offset + 800_000)
    uniforms = torch.rand((seeds, 2 * horizon), generator=generator, device=device)
    query_uniforms = uniforms.cpu().numpy()
    rows = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        benefit = benefit_schedule(scenario, horizon)
        incumbent, candidate = _generate_costs(
            benefit,
            seeds=seeds,
            seed=seed_offset + scenario_index * 100_003,
            device=device,
        )
        gains = incumbent.astype(float) - candidate.astype(float)
        for budget_rate in budget_rates:
            rows.append(
                _evaluate_methods(
                    scenario=scenario,
                    budget_rate=budget_rate,
                    gains=gains,
                    benefit=benefit,
                    query_uniforms=query_uniforms,
                    seed_offset=seed_offset + scenario_index * 100_003,
                    query_rate=query_rate,
                    promotion_cost=promotion_cost,
                    rollback_cost=rollback_cost,
                    label_price=label_price,
                    alpha=alpha,
                    horizon=horizon,
                )
            )
    metrics = pd.concat(rows, ignore_index=True)
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
    calibration = _calibration(metrics, alpha)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    contrasts.to_csv(output / "paired_utility_contrasts.csv", index=False)
    calibration.to_csv(output / "error_calibration.csv", index=False)
    source_paths = {
        Path(__file__).name: Path(__file__),
        "controller.py": Path(__file__).with_name("controller.py"),
        "eprocess.py": Path(__file__).with_name("eprocess.py"),
        "promotion_timing.py": Path(__file__).with_name("promotion_timing.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development benchmark for a two-gate promotion and rollback policy",
        "scenarios": list(SCENARIOS),
        "methods": list(METHODS),
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "query_rate": query_rate,
        "budget_rates": list(budget_rates),
        "alpha_total": alpha,
        "alpha_each_gate": alpha / 2,
        "promotion_cost": promotion_cost,
        "rollback_cost": rollback_cost,
        "label_price": label_price,
        "label_budget_rule": "floor(budget_rate * (shadow_horizon + deployment_horizon)); labels cost one unit",
        "promotion_increment": "I * (incumbent_cost - candidate_cost) / q - promotion_cost / horizon",
        "rollback_increment": "-I * (incumbent_cost - candidate_cost) / q - rollback_cost / horizon",
        "monitor_bound_rule": "1/q + amortized intervention cost per event",
        "primary_metrics": [
            "expected_net_utility",
            "realized_net_utility",
            "promotion_rate",
            "rollback_rate",
            "labels_queried",
        ],
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_paths.items()
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, contrasts, calibration, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/closed_loop_intervention")
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--query-rate", type=float, default=0.25)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    _metrics, summary, _contrasts, calibration, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        query_rate=args.query_rate,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(summary.to_string(index=False))
    print(calibration.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
