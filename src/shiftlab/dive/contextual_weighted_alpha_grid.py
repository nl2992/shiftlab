"""Development grid for prevalence-weighted contextual e-process allocation.

The weighted rule is standard weighted Bonferroni applied to anytime-valid
per-context tests. It is included as a mathematically grounded comparator,
not as a novelty claim.
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
from .closed_loop_intervention import _simulate_gate

SCENARIOS = ("heterogeneous_reversal", "homogeneous_reversal", "persistent_heterogeneity")
METHODS = (
    "continue",
    "global_gate",
    "equal_alpha",
    "volume_weighted_alpha",
    "rare_protected_alpha",
)
TRUE_HARMFUL_PREVALENCES = (0.05, 0.25, 0.50)
PROXY_ERROR_RATES = (0.0, 0.05, 0.10)
INTERVENTION_COST_MULTIPLIERS = (0.0, 1.0, 2.0, 4.0)
BUDGET_RATES = (0.20, 0.40, 0.60)
SEED_OFFSET = 92_102_024
DEVELOPMENT_PREVIOUS_OFFSET = 80_102_024
HORIZON = 400
SEEDS = 200
QUERY_RATE = 0.80
BASE_PROMOTION_COST = 0.05
BASE_ROLLBACK_COST = 0.05
LABEL_PRICE = 0.01
GAIN_BOUND = 5.0
ALPHA = 0.05
PILOT_SIZE = 500

THETA_BY_SCENARIO = {
    "heterogeneous_reversal": (0.40, -0.47),
    "homogeneous_reversal": (-0.47, -0.47),
    "persistent_heterogeneity": (0.40, 0.15),
}


def _posterior_harm_probability(
    true_harmful_prevalence: float, proxy_error_rate: float
) -> tuple[float, float, float]:
    """Return P(proxy=1), P(true=1|proxy=0), and P(true=1|proxy=1)."""
    prevalence = true_harmful_prevalence
    error = proxy_error_rate
    proxy_harmful = prevalence * (1 - error) + (1 - prevalence) * error
    if not 0 < proxy_harmful < 1:
        raise ValueError("grid must leave both proxy groups nonempty")
    p_harm_given_safe_proxy = prevalence * error / (1 - proxy_harmful)
    p_harm_given_harm_proxy = prevalence * (1 - error) / proxy_harmful
    return proxy_harmful, p_harm_given_safe_proxy, p_harm_given_harm_proxy


def _alpha_weights(pilot_counts: np.ndarray) -> dict[str, np.ndarray]:
    """Pre-stream weights; the pilot contains context IDs only, never outcomes."""
    if pilot_counts.shape != (2,) or pilot_counts.sum() <= 0:
        raise ValueError("pilot_counts must contain two observed context counts")
    volume = (pilot_counts + 0.5) / (pilot_counts.sum() + 1.0)
    inverse = 1 / (pilot_counts + 0.5)
    inverse /= inverse.sum()
    return {
        "equal_alpha": np.array([0.5, 0.5]),
        "volume_weighted_alpha": volume,
        "rare_protected_alpha": inverse,
    }


def generate_proxy_streams(
    *,
    scenario: str,
    seeds: int,
    horizon: int,
    true_harmful_prevalence: float,
    proxy_error_rate: float,
    seed: int,
    device: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate paired decision costs with a noisy, visible proxy context.

    The pre-stream pilot provides only observed proxy labels. Within each proxy
    group, latent membership and outcomes are iid, so the per-context test has
    a stable conditional mean. The evaluator alone knows latent membership.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    if seeds < 1 or horizon < 200 or horizon % 2:
        raise ValueError("seeds >=1 and even horizon >=200 required")
    if not 0 < true_harmful_prevalence < 1 or not 0 <= proxy_error_rate < 0.5:
        raise ValueError("invalid prevalence or proxy error")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")

    p_proxy, p_true_harm_if_safe, p_true_harm_if_harm = _posterior_harm_probability(
        true_harmful_prevalence, proxy_error_rate
    )
    generator = torch.Generator(device=device).manual_seed(seed)
    n_proxy_harm = round(horizon * p_proxy)
    if not 0 < n_proxy_harm < horizon:
        raise ValueError("rounded proxy prevalence must leave both contexts represented")
    n_proxy_safe = horizon - n_proxy_harm
    phase_contexts = []
    for _ in range(2):
        context = torch.cat(
            (
                torch.zeros(n_proxy_safe, dtype=torch.long, device=device),
                torch.ones(n_proxy_harm, dtype=torch.long, device=device),
            )
        )
        phase_contexts.append(context[torch.randperm(horizon, generator=generator, device=device)])
    contexts = torch.cat(phase_contexts)

    pilot = torch.rand(PILOT_SIZE, generator=generator, device=device) < p_proxy
    pilot_counts = torch.stack((~pilot, pilot)).sum(dim=1).cpu().numpy().astype(int)
    features = torch.zeros((seeds, 2 * horizon, 1), dtype=torch.float32, device=device)
    features[:, :, 0] = contexts.to(torch.float32)
    true_harm_probability = torch.where(
        contexts == 1,
        torch.full((2 * horizon,), p_true_harm_if_harm, device=device),
        torch.full((2 * horizon,), p_true_harm_if_safe, device=device),
    )
    true_harmful = torch.rand(
        (seeds, 2 * horizon), generator=generator, device=device
    ) < true_harm_probability.unsqueeze(0)

    theta_safe, theta_harm = THETA_BY_SCENARIO[scenario]
    deployment_theta = torch.where(
        true_harmful,
        torch.tensor(theta_harm, device=device),
        torch.tensor(theta_safe, device=device),
    )
    shadow_theta = torch.ones_like(deployment_theta)
    theta = torch.where(
        torch.arange(2 * horizon, device=device).unsqueeze(0) < horizon,
        shadow_theta,
        deployment_theta,
    )
    # Incumbent predicts class 0; candidate predicts class 1. Their paired
    # cost gain is +5 on Y=1 and -1 on Y=0, hence E[g]=6 P(Y=1)-1.
    outcome_probability = (theta + 1.0) / 6.0
    outcomes = torch.rand((seeds, 2 * horizon), generator=generator, device=device) < (
        outcome_probability
    )
    gains = torch.where(outcomes, 5.0, -1.0)

    expected = np.ones(2 * horizon, dtype=float)
    expected_proxy = np.array(
        [
            (1 - p_true_harm_if_safe) * theta_safe + p_true_harm_if_safe * theta_harm,
            (1 - p_true_harm_if_harm) * theta_safe + p_true_harm_if_harm * theta_harm,
        ],
        dtype=float,
    )
    expected[horizon:] = expected_proxy[contexts[horizon:].cpu().numpy()]
    return (
        features.cpu().numpy(),
        gains.cpu().numpy().astype(float),
        expected,
        contexts.cpu().numpy().astype(int),
        pilot_counts,
    )


def _score_gate(
    gate: dict[str, np.ndarray],
    *,
    gains: np.ndarray,
    expected: np.ndarray,
    horizon: int,
    promotion_cost: float,
    rollback_cost: float,
    label_price: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    length = np.where(gate["rolled_back"], gate["rollback_time"] + 1, horizon)
    length = np.where(gate["promoted"], length, 0)
    realized = np.cumsum(gains[:, horizon:], axis=1)
    realized_benefit = np.where(
        length > 0, realized[np.arange(len(length)), np.maximum(length - 1, 0)], 0.0
    )
    expected_cumulative = np.cumsum(expected[horizon:])
    expected_benefit = np.where(length > 0, expected_cumulative[np.maximum(length - 1, 0)], 0.0)
    realized_utility = (
        realized_benefit
        - gate["promoted"] * promotion_cost
        - gate["rolled_back"] * rollback_cost
        - gate["labels_queried"] * label_price
    )
    expected_utility = (
        expected_benefit
        - gate["promoted"] * promotion_cost
        - gate["rolled_back"] * rollback_cost
        - gate["labels_queried"] * label_price
    )
    return realized_utility, expected_utility, length


def _score_stratified(
    *,
    gains: np.ndarray,
    expected: np.ndarray,
    contexts: np.ndarray,
    query_uniforms: np.ndarray,
    horizon: int,
    budget_rate: float,
    alpha_weights: np.ndarray,
    promotion_cost: float,
    rollback_cost: float,
    label_price: float,
    query_rate: float,
) -> dict[str, np.ndarray]:
    streams = gains.shape[0]
    total_budget = int(np.floor(budget_rate * 2 * horizon))
    aggregate = {
        "promoted": np.zeros((streams, 2), dtype=bool),
        "rolled_back": np.zeros((streams, 2), dtype=bool),
        "rollback_time": np.full((streams, 2), -1, dtype=int),
        "labels": np.zeros((streams, 2), dtype=int),
        "length": np.zeros((streams, 2), dtype=int),
        "realized_benefit": np.zeros(streams),
        "expected_benefit": np.zeros(streams),
    }
    budgets = []
    for group in range(2):
        indices = np.flatnonzero(contexts == group)
        if len(indices) % 2 or len(indices) != 2 * (len(indices) // 2):
            raise RuntimeError("proxy context must have equal per-phase event counts")
        group_horizon = len(indices) // 2
        group_budget = int(np.floor(budget_rate * 2 * group_horizon))
        budgets.append(group_budget)
        gate = _simulate_gate(
            gains[:, indices],
            query_uniforms[:, indices],
            query_rate=query_rate,
            label_budget=group_budget,
            alpha=ALPHA * float(alpha_weights[group]),
            promotion_cost=promotion_cost,
            rollback_cost=rollback_cost,
            horizon=group_horizon,
            gain_bound=GAIN_BOUND,
        )
        aggregate["promoted"][:, group] = gate["promoted"]
        aggregate["rolled_back"][:, group] = gate["rolled_back"]
        aggregate["rollback_time"][:, group] = gate["rollback_time"]
        aggregate["labels"][:, group] = gate["labels_queried"]
        group_length = np.where(gate["rolled_back"], gate["rollback_time"] + 1, group_horizon)
        group_length = np.where(gate["promoted"], group_length, 0)
        aggregate["length"][:, group] = group_length
        deploy_idx = indices[group_horizon:]
        group_realized = np.cumsum(gains[:, deploy_idx], axis=1)
        group_expected = np.cumsum(expected[deploy_idx])
        active = group_length > 0
        aggregate["realized_benefit"][active] += group_realized[
            np.flatnonzero(active), group_length[active] - 1
        ]
        aggregate["expected_benefit"][active] += group_expected[group_length[active] - 1]
    if sum(budgets) > total_budget:
        raise RuntimeError("context-wise label allocations exceed the shared hard cap")
    promoted_count = aggregate["promoted"].sum(axis=1)
    rollback_count = aggregate["rolled_back"].sum(axis=1)
    labels = aggregate["labels"].sum(axis=1)
    aggregate["realized_utility"] = (
        aggregate["realized_benefit"]
        - promoted_count * promotion_cost
        - rollback_count * rollback_cost
        - labels * label_price
    )
    aggregate["expected_utility"] = (
        aggregate["expected_benefit"]
        - promoted_count * promotion_cost
        - rollback_count * rollback_cost
        - labels * label_price
    )
    aggregate["labels_queried"] = labels
    aggregate["label_budget"] = np.full(streams, total_budget)
    aggregate["budget_respected"] = labels <= total_budget
    return aggregate


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = SEEDS,
    seed_offset: int = SEED_OFFSET,
    horizon: int = HORIZON,
    true_harmful_prevalences: tuple[float, ...] = TRUE_HARMFUL_PREVALENCES,
    proxy_error_rates: tuple[float, ...] = PROXY_ERROR_RATES,
    intervention_cost_multipliers: tuple[float, ...] = INTERVENTION_COST_MULTIPLIERS,
    budget_rates: tuple[float, ...] = BUDGET_RATES,
    device: str = "cuda",
    bootstrap_replicates: int = 1_000,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2 or horizon < 200 or horizon % 2 or bootstrap_replicates < 100:
        raise ValueError("seeds >=2, even horizon >=200, and bootstrap >=100 required")
    for values, name in (
        (true_harmful_prevalences, "prevalence"),
        (proxy_error_rates, "proxy error"),
        (intervention_cost_multipliers, "cost multiplier"),
        (budget_rates, "budget rate"),
    ):
        if not values or tuple(sorted(set(values))) != values:
            raise ValueError(f"{name} values must be nonempty, sorted and unique")
    if any(not 0 < p < 1 for p in true_harmful_prevalences):
        raise ValueError("true harmful prevalences must be in (0,1)")
    if any(not 0 <= e < 0.5 for e in proxy_error_rates):
        raise ValueError("proxy errors must be in [0,0.5)")
    if any(c < 0 for c in intervention_cost_multipliers):
        raise ValueError("intervention cost multipliers must be nonnegative")
    if any(not 0 < b <= 1 for b in budget_rates):
        raise ValueError("budget rates must be in (0,1]")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")

    rows: list[dict] = []
    contrasts: list[dict] = []
    all_caps = True
    profile_index = 0
    source_files = {
        "contextual_weighted_alpha_grid.py": Path(__file__),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
    }
    for scenario in SCENARIOS:
        for prevalence in true_harmful_prevalences:
            for proxy_error in proxy_error_rates:
                profile_seed = seed_offset + profile_index * 211_019
                features, gains, expected, contexts, pilot_counts = generate_proxy_streams(
                    scenario=scenario,
                    seeds=seeds,
                    horizon=horizon,
                    true_harmful_prevalence=prevalence,
                    proxy_error_rate=proxy_error,
                    seed=profile_seed,
                    device=device,
                )
                del features
                weights_by_method = _alpha_weights(pilot_counts)
                observed_prevalence = float(contexts[horizon:].mean())
                theta_obs = np.array(
                    [expected[horizon:][contexts[horizon:] == c].mean() for c in range(2)]
                )
                harmful_proxy = theta_obs < 0
                # Reuse identical query paths over cost and cap settings for
                # paired comparisons across the entire profile grid.
                query_generator = torch.Generator(device=device).manual_seed(
                    profile_seed + 38_102_024
                )
                query_uniforms = (
                    torch.rand((seeds, 2 * horizon), generator=query_generator, device=device)
                    .cpu()
                    .numpy()
                )
                for cost_multiplier in intervention_cost_multipliers:
                    promotion_cost = BASE_PROMOTION_COST * cost_multiplier
                    rollback_cost = BASE_ROLLBACK_COST * cost_multiplier
                    for budget_rate in budget_rates:
                        for query_rate in (QUERY_RATE,):
                            total_budget = int(np.floor(budget_rate * 2 * horizon))
                            global_gate = _simulate_gate(
                                gains,
                                query_uniforms,
                                query_rate=query_rate,
                                label_budget=total_budget,
                                alpha=ALPHA,
                                promotion_cost=promotion_cost,
                                rollback_cost=rollback_cost,
                                horizon=horizon,
                                gain_bound=GAIN_BOUND,
                            )
                            global_realized, global_expected, global_length = _score_gate(
                                global_gate,
                                gains=gains,
                                expected=expected,
                                horizon=horizon,
                                promotion_cost=promotion_cost,
                                rollback_cost=rollback_cost,
                                label_price=LABEL_PRICE,
                            )
                            cell_rows = [
                                {
                                    "scenario": scenario,
                                    "true_harmful_prevalence": prevalence,
                                    "proxy_error_rate": proxy_error,
                                    "observed_proxy_prevalence": observed_prevalence,
                                    "cost_multiplier": cost_multiplier,
                                    "query_rate": query_rate,
                                    "budget_rate": budget_rate,
                                    "pilot_safe_count": int(pilot_counts[0]),
                                    "pilot_harmful_count": int(pilot_counts[1]),
                                    "method": "continue",
                                    "seed": seed_offset + profile_index * 1_000_003 + i,
                                    "promoted_groups": 0,
                                    "rolled_back_groups": 0,
                                    "harmful_proxy_groups_rolled_back": 0,
                                    "safe_proxy_groups_retained": 0,
                                    "candidate_events_deployed": 0,
                                    "labels_queried": 0,
                                    "label_budget": total_budget,
                                    "budget_respected": True,
                                    "realized_net_utility": 0.0,
                                    "expected_net_utility": 0.0,
                                }
                                for i in range(seeds)
                            ]
                            for method, gate, realized, exp_utility, lengths in [
                                (
                                    "global_gate",
                                    global_gate,
                                    global_realized,
                                    global_expected,
                                    global_length,
                                )
                            ]:
                                for i in range(seeds):
                                    cell_rows.append(
                                        {
                                            "scenario": scenario,
                                            "true_harmful_prevalence": prevalence,
                                            "proxy_error_rate": proxy_error,
                                            "observed_proxy_prevalence": observed_prevalence,
                                            "cost_multiplier": cost_multiplier,
                                            "query_rate": query_rate,
                                            "budget_rate": budget_rate,
                                            "pilot_safe_count": int(pilot_counts[0]),
                                            "pilot_harmful_count": int(pilot_counts[1]),
                                            "method": method,
                                            "seed": seed_offset + profile_index * 1_000_003 + i,
                                            "promoted_groups": int(gate["promoted"][i]),
                                            "rolled_back_groups": int(gate["rolled_back"][i]),
                                            "harmful_proxy_groups_rolled_back": int(
                                                gate["rolled_back"][i] * harmful_proxy.sum()
                                            ),
                                            "safe_proxy_groups_retained": int(
                                                gate["promoted"][i] and not gate["rolled_back"][i]
                                            )
                                            * int((~harmful_proxy).sum()),
                                            "candidate_events_deployed": int(lengths[i]),
                                            "labels_queried": int(gate["labels_queried"][i]),
                                            "label_budget": total_budget,
                                            "budget_respected": bool(gate["budget_respected"][i]),
                                            "realized_net_utility": float(realized[i]),
                                            "expected_net_utility": float(exp_utility[i]),
                                        }
                                    )
                            for method, weights in weights_by_method.items():
                                strat = _score_stratified(
                                    gains=gains,
                                    expected=expected,
                                    contexts=contexts,
                                    query_uniforms=query_uniforms,
                                    horizon=horizon,
                                    budget_rate=budget_rate,
                                    alpha_weights=weights,
                                    promotion_cost=promotion_cost,
                                    rollback_cost=rollback_cost,
                                    label_price=LABEL_PRICE,
                                    query_rate=query_rate,
                                )
                                for i in range(seeds):
                                    rolled = strat["rolled_back"][i]
                                    promoted = strat["promoted"][i]
                                    cell_rows.append(
                                        {
                                            "scenario": scenario,
                                            "true_harmful_prevalence": prevalence,
                                            "proxy_error_rate": proxy_error,
                                            "observed_proxy_prevalence": observed_prevalence,
                                            "cost_multiplier": cost_multiplier,
                                            "query_rate": query_rate,
                                            "budget_rate": budget_rate,
                                            "pilot_safe_count": int(pilot_counts[0]),
                                            "pilot_harmful_count": int(pilot_counts[1]),
                                            "method": method,
                                            "seed": seed_offset + profile_index * 1_000_003 + i,
                                            "promoted_groups": int(promoted.sum()),
                                            "rolled_back_groups": int(rolled.sum()),
                                            "harmful_proxy_groups_rolled_back": int(
                                                (rolled & harmful_proxy).sum()
                                            ),
                                            "safe_proxy_groups_retained": int(
                                                (promoted & ~rolled & ~harmful_proxy).sum()
                                            ),
                                            "candidate_events_deployed": int(
                                                strat["length"][i].sum()
                                            ),
                                            "labels_queried": int(strat["labels_queried"][i]),
                                            "label_budget": total_budget,
                                            "budget_respected": bool(strat["budget_respected"][i]),
                                            "realized_net_utility": float(
                                                strat["realized_utility"][i]
                                            ),
                                            "expected_net_utility": float(
                                                strat["expected_utility"][i]
                                            ),
                                            "alpha_weight_safe": float(weights[0]),
                                            "alpha_weight_harmful": float(weights[1]),
                                        }
                                    )
                            cell = pd.DataFrame(cell_rows)
                            all_caps &= bool(cell.budget_respected.all())
                            rows.extend(cell.to_dict(orient="records"))
                            wide = cell.pivot(
                                index="seed", columns="method", values="realized_net_utility"
                            )
                            method_comparisons = [
                                (method, reference)
                                for method in weights_by_method
                                for reference in ("global_gate", "continue")
                            ] + [
                                ("volume_weighted_alpha", "equal_alpha"),
                                ("rare_protected_alpha", "equal_alpha"),
                                ("rare_protected_alpha", "volume_weighted_alpha"),
                            ]
                            for method, reference in method_comparisons:
                                difference = (wide[method] - wide[reference]).to_numpy(float)
                                rng = np.random.default_rng(
                                    profile_seed
                                    + int(cost_multiplier * 11_000)
                                    + int(budget_rate * 1000)
                                    + len(contrasts)
                                )
                                sample_index = rng.integers(
                                    0, seeds, size=(bootstrap_replicates, seeds)
                                )
                                ci = np.quantile(
                                    difference[sample_index].mean(axis=1), [0.025, 0.975]
                                )
                                contrasts.append(
                                    {
                                        "scenario": scenario,
                                        "true_harmful_prevalence": prevalence,
                                        "proxy_error_rate": proxy_error,
                                        "cost_multiplier": cost_multiplier,
                                        "budget_rate": budget_rate,
                                        "method": method,
                                        "reference": reference,
                                        "paired_mean_realized_utility_difference": float(
                                            difference.mean()
                                        ),
                                        "seed_bootstrap_ci95_low": float(ci[0]),
                                        "seed_bootstrap_ci95_high": float(ci[1]),
                                        "seed_clusters": seeds,
                                    }
                                )
                profile_index += 1

    metrics = pd.DataFrame(rows)
    contrast_frame = pd.DataFrame(contrasts)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    contrast_frame.to_csv(output / "paired_contrasts.csv", index=False)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development factorial comparing global and predictable weighted-Bonferroni context gates under proxy noise, rarity, cost, and hard-budget variation",
        "status": "development_only_no_independent_calibration_or_confirmation",
        "scenarios": list(SCENARIOS),
        "seeds_per_cell": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "true_harmful_prevalences": list(true_harmful_prevalences),
        "proxy_error_rates": list(proxy_error_rates),
        "intervention_cost_multipliers": list(intervention_cost_multipliers),
        "budget_rates": list(budget_rates),
        "query_rate": QUERY_RATE,
        "label_price": LABEL_PRICE,
        "alpha_total_per_stage_family": ALPHA,
        "allocation_methods": list(weights_by_method),
        "alpha_weights_from_pre_stream_unlabeled_pilot": True,
        "all_alpha_weights_from_pre_stream_unlabeled_pilot": True,
        "pilot_size": PILOT_SIZE,
        "pilot_smoothing": 0.5,
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
        "statistical_claim_limit": "Weighted Bonferroni preserves the registered familywise false-escalation bound conditional on the independent outcome-free pilot and valid per-context e-process assumptions. This development grid does not calibrate that bound under every profile.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = _render_report(metrics, contrast_frame, manifest, device, bootstrap_replicates)
    (output / "report.md").write_text(report, encoding="utf-8")
    return metrics, contrast_frame, manifest


def _render_report(
    metrics: pd.DataFrame,
    contrasts: pd.DataFrame,
    manifest: dict,
    device: str,
    bootstrap_replicates: int,
) -> str:
    primary = contrasts.loc[
        contrasts.scenario.eq("heterogeneous_reversal")
        & contrasts.method.eq("rare_protected_alpha")
        & contrasts.reference.eq("global_gate")
    ]
    allocation_comparisons = contrasts.loc[
        contrasts.scenario.eq("heterogeneous_reversal")
        & contrasts.method.eq("volume_weighted_alpha")
        & contrasts.reference.eq("equal_alpha")
    ]
    subset = metrics.loc[
        metrics.scenario.eq("heterogeneous_reversal")
        & metrics.cost_multiplier.eq(1.0)
        & metrics.budget_rate.eq(0.4)
    ]
    summary = subset.groupby(
        ["true_harmful_prevalence", "proxy_error_rate", "method"], as_index=False
    ).agg(
        expected_utility=("expected_net_utility", "mean"),
        realized_utility=("realized_net_utility", "mean"),
        harmful_rollbacks=("harmful_proxy_groups_rolled_back", "mean"),
        safe_retained=("safe_proxy_groups_retained", "mean"),
        mean_labels=("labels_queried", "mean"),
    )
    table = summary.loc[
        summary.method.isin(
            ("global_gate", "equal_alpha", "volume_weighted_alpha", "rare_protected_alpha")
        )
    ]
    return (
        "\n".join(
            [
                "# Contextual weighted-alpha robustness development grid",
                "",
                f"Status: **{manifest['status']}**; {manifest['metric_rows']:,} stream-method rows; {manifest['contrast_rows']:,} paired contrasts; device {device}; {manifest['seeds_per_cell']} seeds per cell.",
                "",
                "The grid stresses context-local promotion and rollback as the harmful latent context becomes rare, the learner-visible proxy label becomes noisy, intervention costs vary, and the shared hard label budget changes. The learner sees only the proxy context. An independent pre-stream pilot contains proxy labels but no outcomes; alpha weights are fixed from that pilot before testing. The evaluator alone knows the latent context and scores expected utility.",
                "",
                "## Allocation method",
                "",
                "Each group runs the existing bounded anytime e-process. For fixed pilot-measurable weights `w_j >= 0` summing to one, group `j` receives `alpha*w_j`; promotion and rollback split each group's allocation in half. Ville's inequality and a union bound give familywise error at most alpha across groups within each stage. Pilot-based, outcome-independent weights preserve that guarantee conditional on the pilot, assuming each group's bounded conditional-mean null and predictable query mechanism. Equal, proxy-volume-weighted, and inverse-volume (rare-protected) allocations are standard weighted Bonferroni comparators, not new tests.",
                "",
                "## Heterogeneous reversal at unit intervention cost and 40% label cap",
                "",
                "The table reports means over seeds for each truth prevalence and proxy error. It is a development slice, not a selected confirmation result.",
                "",
                table.to_markdown(index=False, floatfmt=".3f"),
                "",
                "`harmful_rollbacks` and `safe_retained` are mean counts of proxy strata per stream (maximum two), not proportions.",
                "",
                "## Direct allocation comparison",
                "",
                (
                    "For volume-weighted alpha minus equal alpha in heterogeneous reversal, the unadjusted per-cell paired mean was positive in "
                    f"{(allocation_comparisons.paired_mean_realized_utility_difference > 0).mean():.1%} of cells, with median {allocation_comparisons.paired_mean_realized_utility_difference.median():.2f} and range [{allocation_comparisons.paired_mean_realized_utility_difference.min():.2f}, {allocation_comparisons.paired_mean_realized_utility_difference.max():.2f}]. The intervals are unadjusted across the grid, so they are exploratory rather than selection-adjusted superiority tests."
                ),
                "",
                (
                    "Across the full heterogeneous-reversal grid, the rare-protected allocation's paired contrast against the global gate ranged from "
                    f"{primary.paired_mean_realized_utility_difference.min():.2f} to {primary.paired_mean_realized_utility_difference.max():.2f} utility units (unadjusted per-cell seed-bootstrap intervals, {bootstrap_replicates} replicates). These exploratory intervals do not correct for grid selection."
                ),
                "",
                "No null calibration or independent confirmation is claimed. The global gate is a utility comparator under context-dependent gains; the per-context methods are the procedures whose stagewise familywise control follows from the stated weighted Bonferroni construction. A changed proxy model, context partition, or selected allocation requires fresh calibration on independent streams before error-control claims.",
                "",
                "No figure was generated. Any future research visual must be made with PaperBanana and checked against the saved metrics.",
            ]
        )
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument(
        "--true-harmful-prevalences", type=float, nargs="+", default=TRUE_HARMFUL_PREVALENCES
    )
    parser.add_argument("--proxy-error-rates", type=float, nargs="+", default=PROXY_ERROR_RATES)
    parser.add_argument(
        "--intervention-cost-multipliers",
        type=float,
        nargs="+",
        default=INTERVENTION_COST_MULTIPLIERS,
    )
    parser.add_argument("--budget-rates", type=float, nargs="+", default=BUDGET_RATES)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=1_000)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/contextual_weighted_alpha_grid")
    )
    args = parser.parse_args()
    metrics, contrasts, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        true_harmful_prevalences=tuple(args.true_harmful_prevalences),
        proxy_error_rates=tuple(args.proxy_error_rates),
        intervention_cost_multipliers=tuple(args.intervention_cost_multipliers),
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
