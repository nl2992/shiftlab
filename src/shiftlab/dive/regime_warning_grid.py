"""Compare fixed abstention and a visible warning-feature fallback on synthetic streams.

This is an exploratory comparator study, not a new monitor or a guarantee. The warning
feature is a learner-visible covariate whose deployment distribution shifts only in the
registered reversal scenario. All true expected costs remain evaluator-only.
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
from scipy.stats import norm

from ..data.gpu.environment import environment
from .closed_loop_intervention import _evaluate_methods
from .feature_intervention import (
    SCENARIOS,
    generate_feature_cost_streams,
)

SEED_OFFSET = 79_102_024
SIGNAL_STRENGTHS = (0.0, 0.5, 1.0, 2.0)
WARNING_FALSE_POSITIVE_RATES = (0.01, 0.05, 0.10)
WARNING_MISSINGNESS_RATES = (0.0, 0.10, 0.30)
WARNING_EVENT_COSTS = (0.0, 0.0005, 0.002)
STATIC_COVERAGES = (0.25, 0.50, 0.75)
PROMOTION_COST = 0.05
ROLLBACK_COST = 0.05
LABEL_PRICE = 0.01


def warning_active_probability(
    false_positive_rate: float, signal_strength: float, missingness_rate: float = 0.0
) -> float:
    """Candidate-use probability with MCAR missing warnings treated as fallback."""
    if not 0 < false_positive_rate < 1 or signal_strength < 0 or not 0 <= missingness_rate < 1:
        raise ValueError("invalid false-warning, signal-strength or missingness parameter")
    threshold = float(norm.isf(false_positive_rate))
    return float((1 - missingness_rate) * norm.cdf(threshold - signal_strength))


def _policy_metrics(
    *,
    scenario: str,
    seed_offset: int,
    signal_strength: float,
    warning_false_positive_rate: float,
    warning_missingness_rate: float,
    warning_event_cost_per_event: float,
    missing_uniforms: np.ndarray,
    coverage_uniforms: np.ndarray,
    features: np.ndarray,
    gains: np.ndarray,
    expected_gains: np.ndarray,
    horizon: int,
    include_static_baselines: bool = False,
) -> list[dict]:
    streams = len(gains)
    deployment_features = features[:, horizon:, 7]
    deployment_gains = gains[:, horizon:]
    deployment_expected_gains = expected_gains[horizon:]
    threshold = float(norm.isf(warning_false_positive_rate))
    active_probability = warning_active_probability(
        warning_false_positive_rate, signal_strength, warning_missingness_rate
    )
    available = missing_uniforms < 1 - warning_missingness_rate
    warning_mask = available & (deployment_features > threshold)
    active_mask = available & (deployment_features <= threshold)
    policies: list[tuple[str, np.ndarray, float, float, bool, bool]] = []
    if include_static_baselines:
        for coverage in STATIC_COVERAGES:
            gate_rng = np.random.default_rng(seed_offset + int(coverage * 1000) + 19_102_024)
            active = gate_rng.random((streams, horizon)) < coverage
            policies.append(
                (f"static_coverage_{coverage:.2f}", active, coverage, 0.0, False, False)
            )
    name = (
        f"warning_gate_fpr_{warning_false_positive_rate:.2f}"
        f"_miss_{warning_missingness_rate:.2f}_cost_{warning_event_cost_per_event:.4f}"
    )
    policies.append(
        (name, active_mask, active_probability, warning_event_cost_per_event, True, True)
    )
    matched_active = coverage_uniforms < active_probability
    policies.append(
        (
            "matched_coverage_oracle",
            matched_active,
            active_probability,
            0.0,
            True,
            False,
        )
    )

    rows = []
    for policy, active, theoretical_coverage, event_cost, cell_specific, warning_policy in policies:
        expected_active = np.full(horizon, theoretical_coverage)
        utility_realized = (deployment_gains * active).sum(axis=1) - PROMOTION_COST
        if event_cost:
            utility_realized -= event_cost * horizon
        utility_expected = (
            float(np.dot(deployment_expected_gains, expected_active)) - PROMOTION_COST
        )
        if event_cost:
            utility_expected -= event_cost * horizon
        for i in range(streams):
            rows.append(
                {
                    "scenario": scenario,
                    "signal_strength": signal_strength if cell_specific else None,
                    "warning_false_positive_rate": warning_false_positive_rate
                    if cell_specific
                    else None,
                    "warning_missingness_rate": warning_missingness_rate if cell_specific else None,
                    "warning_event_cost_per_event": warning_event_cost_per_event
                    if cell_specific
                    else None,
                    "warning_feature_threshold": threshold if warning_policy else None,
                    "warning_feature_used": warning_policy,
                    "evaluator_oracle_reference_only": policy == "matched_coverage_oracle",
                    "policy": policy,
                    "seed": seed_offset + i,
                    "candidate_events_deployed": int(active[i].sum()),
                    "warning_events": int(warning_mask[i].sum()) if warning_policy else 0,
                    "warning_missing_events": int((~available[i]).sum()) if warning_policy else 0,
                    "labels_queried": 0,
                    "warning_event_cost": event_cost * horizon,
                    "switching_cost": PROMOTION_COST,
                    "realized_net_utility": float(utility_realized[i]),
                    "expected_net_utility": utility_expected,
                    "evaluator_expected_candidate_gain": float(
                        np.dot(deployment_expected_gains, expected_active)
                    ),
                    "theoretical_candidate_coverage": theoretical_coverage,
                    "empirical_candidate_coverage": float(active.mean()),
                }
            )
    return rows


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 500,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 400,
    signal_strengths: tuple[float, ...] = SIGNAL_STRENGTHS,
    warning_false_positive_rates: tuple[float, ...] = WARNING_FALSE_POSITIVE_RATES,
    warning_missingness_rates: tuple[float, ...] = WARNING_MISSINGNESS_RATES,
    warning_event_costs: tuple[float, ...] = WARNING_EVENT_COSTS,
    device: str = "cuda",
    bootstrap_replicates: int = 2_000,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run a paired development grid over cue strength and warning thresholds."""
    if seeds < 2 or horizon < 100 or bootstrap_replicates < 100:
        raise ValueError("seeds >= 2, horizon >= 100 and bootstrap_replicates >= 100 required")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")
    if tuple(sorted(set(signal_strengths))) != signal_strengths or any(
        value < 0 or not np.isfinite(value) for value in signal_strengths
    ):
        raise ValueError("signal strengths must be sorted, unique and nonnegative")
    if tuple(sorted(set(warning_false_positive_rates))) != warning_false_positive_rates or any(
        not 0 < value < 1 for value in warning_false_positive_rates
    ):
        raise ValueError("warning false-positive rates must be sorted, unique and in (0,1)")
    if tuple(sorted(set(warning_missingness_rates))) != warning_missingness_rates or any(
        not 0 <= value < 1 for value in warning_missingness_rates
    ):
        raise ValueError("warning missingness rates must be sorted, unique and in [0,1)")
    if tuple(sorted(set(warning_event_costs))) != warning_event_costs or any(
        value < 0 or not np.isfinite(value) for value in warning_event_costs
    ):
        raise ValueError("warning event costs must be sorted, unique and nonnegative")

    rows: list[dict] = []
    sources = {
        "regime_warning_grid.py": Path(__file__),
        "feature_intervention.py": Path(__file__).with_name("feature_intervention.py"),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
    }
    for scenario_index, scenario in enumerate(SCENARIOS):
        features, outcomes, gains, oracle = generate_feature_cost_streams(
            scenario=scenario,
            seeds=seeds,
            horizon=horizon,
            seed=seed_offset + scenario_index * 101_009,
            device=device,
            rollback_cost=ROLLBACK_COST,
        )
        # The existing nuisance-only stress shifts dimensions 1:8. Remove its effect from
        # the dedicated warning coordinate so the warning's null distribution remains N(0,1).
        if scenario == "benign_nuisance":
            features[:, horizon:, 7] -= 3.0
        query_generator = torch.Generator(device=device).manual_seed(
            seed_offset + scenario_index * 101_009 + 31_102_024
        )
        query_uniforms = (
            torch.rand((seeds, 2 * horizon), generator=query_generator, device=device).cpu().numpy()
        )
        baseline = _evaluate_methods(
            scenario=scenario,
            budget_rate=0.40,
            seed_offset=seed_offset,
            gains=gains,
            benefit=oracle["expected_incumbent_minus_candidate_cost"],
            query_uniforms=query_uniforms,
            query_rate=0.80,
            promotion_cost=PROMOTION_COST,
            rollback_cost=ROLLBACK_COST,
            label_price=LABEL_PRICE,
            alpha=0.05,
            horizon=horizon,
            gain_bound=5.0,
        )
        for record in baseline.to_dict(orient="records"):
            record.update(
                {
                    "signal_strength": 0.0,
                    "warning_false_positive_rate": None,
                    "warning_missingness_rate": None,
                    "warning_event_cost_per_event": None,
                    "warning_feature_threshold": None,
                    "policy": record.pop("method"),
                    "warning_events": 0,
                    "warning_missing_events": 0,
                    "warning_event_cost": 0.0,
                    "theoretical_candidate_coverage": None,
                    "empirical_candidate_coverage": None,
                }
            )
            rows.append(record)
        del outcomes

        expected_gains = np.asarray(oracle["expected_incumbent_minus_candidate_cost"], dtype=float)
        scenario_signal_strengths = signal_strengths if scenario == "harmful_adaptation" else (0.0,)
        missing_generator = torch.Generator(device=device).manual_seed(
            seed_offset + scenario_index * 101_009 + 41_102_024
        )
        missing_uniforms = (
            torch.rand((seeds, horizon), generator=missing_generator, device=device).cpu().numpy()
        )
        coverage_generator = torch.Generator(device=device).manual_seed(
            seed_offset + scenario_index * 101_009 + 51_102_024
        )
        coverage_uniforms = (
            torch.rand((seeds, horizon), generator=coverage_generator, device=device).cpu().numpy()
        )
        static_rows = _policy_metrics(
            scenario=scenario,
            seed_offset=seed_offset,
            signal_strength=0.0,
            warning_false_positive_rate=warning_false_positive_rates[0],
            warning_missingness_rate=0.0,
            warning_event_cost_per_event=0.0,
            missing_uniforms=missing_uniforms,
            coverage_uniforms=coverage_uniforms,
            features=features,
            gains=gains,
            expected_gains=expected_gains,
            horizon=horizon,
            include_static_baselines=True,
        )
        rows.extend(row for row in static_rows if row["policy"].startswith("static_coverage"))
        for signal_strength in scenario_signal_strengths:
            signal_features = features.copy()
            if scenario == "harmful_adaptation":
                signal_features[:, horizon:, 7] += signal_strength
            for missingness in warning_missingness_rates:
                for fpr in warning_false_positive_rates:
                    for event_cost in warning_event_costs:
                        cell_rows = _policy_metrics(
                            scenario=scenario,
                            seed_offset=seed_offset,
                            signal_strength=signal_strength
                            if scenario == "harmful_adaptation"
                            else 0.0,
                            warning_false_positive_rate=fpr,
                            warning_missingness_rate=missingness,
                            warning_event_cost_per_event=event_cost,
                            missing_uniforms=missing_uniforms,
                            coverage_uniforms=coverage_uniforms,
                            features=signal_features,
                            gains=gains,
                            expected_gains=expected_gains,
                            horizon=horizon,
                        )
                        rows.extend(cell_rows)
            del signal_features

    metrics = pd.DataFrame(rows)
    # Paired stream bootstrap contrasts compare warning rules against operational
    # baselines and a diagnostic oracle-matched-coverage reference on common seeds.
    contrast_rows = []
    baseline_names = ("continue", "unconditional_promote", "promotion_only", "promotion_rollback")
    group_columns = [
        "scenario",
        "signal_strength",
        "warning_false_positive_rate",
        "warning_missingness_rate",
        "warning_event_cost_per_event",
    ]
    static_names = tuple(f"static_coverage_{coverage:.2f}" for coverage in STATIC_COVERAGES)
    for (scenario, signal_strength, fpr, missingness, event_cost), group in metrics[
        metrics.warning_false_positive_rate.notna()
    ].groupby(group_columns, sort=True):
        baselines = metrics.loc[
            metrics.scenario.eq(scenario) & metrics.policy.isin(baseline_names)
        ].set_index(["policy", "seed"])
        static_baselines = metrics.loc[
            metrics.scenario.eq(scenario) & metrics.policy.isin(static_names)
        ].set_index(["policy", "seed"])
        for policy, policy_group in group.groupby("policy", sort=True):
            candidate = policy_group.set_index("seed").sort_index()
            if policy == "matched_coverage_oracle":
                references = (
                    next(name for name in group.policy.unique() if name.startswith("warning_gate")),
                )
            else:
                references = (*baseline_names, *static_names, "matched_coverage_oracle")
            for reference in references:
                if reference in baseline_names:
                    comparator = baselines.loc[reference].sort_index()
                elif reference in static_names:
                    comparator = static_baselines.loc[reference].sort_index()
                else:
                    comparator = (
                        group.loc[group.policy.eq(reference)].set_index("seed").sort_index()
                    )
                differences = (
                    candidate.realized_net_utility.to_numpy()
                    - comparator.realized_net_utility.to_numpy()
                )
                rng = np.random.default_rng(
                    seed_offset
                    + int(signal_strength * 10_000)
                    + int(fpr * 1_000)
                    + len(contrast_rows)
                    + 22_102_024
                )
                samples = rng.integers(0, seeds, size=(bootstrap_replicates, seeds))
                interval = np.quantile(differences[samples].mean(axis=1), [0.025, 0.975])
                contrast_rows.append(
                    {
                        "scenario": scenario,
                        "signal_strength": signal_strength,
                        "warning_false_positive_rate": fpr,
                        "warning_missingness_rate": missingness,
                        "warning_event_cost_per_event": event_cost,
                        "policy": policy,
                        "reference": reference,
                        "paired_realized_utility_difference": float(differences.mean()),
                        "seed_bootstrap_ci95_low": float(interval[0]),
                        "seed_bootstrap_ci95_high": float(interval[1]),
                        "seed_clusters": seeds,
                    }
                )
    contrast_frame = pd.DataFrame(contrast_rows)
    cell_keys = [*group_columns, "seed"]
    warning_utility = metrics.loc[
        metrics.policy.str.startswith("warning_gate"),
        cell_keys
        + [
            "expected_net_utility",
        ],
    ]
    matched_utility = metrics.loc[
        metrics.policy.eq("matched_coverage_oracle"), cell_keys + ["expected_net_utility"]
    ]
    utility_check = warning_utility.merge(
        matched_utility, on=cell_keys, suffixes=("_warning", "_matched")
    )
    expected_sensor_cost = -(
        utility_check.warning_event_cost_per_event.to_numpy(dtype=float) * horizon
    )
    observed_utility_difference = utility_check.expected_net_utility_warning.to_numpy(
        dtype=float
    ) - utility_check.expected_net_utility_matched.to_numpy(dtype=float)
    if not np.allclose(observed_utility_difference, expected_sensor_cost, atol=1e-10):
        raise RuntimeError(
            "warning and oracle-matched coverage expected utilities do not reconcile"
        )
    metrics["budget_respected"] = metrics.get(
        "labels_queried", pd.Series(0, index=metrics.index)
    ) <= int(np.floor(0.40 * 2 * horizon))
    all_caps = bool(metrics.budget_respected.all())
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    contrast_frame.to_csv(output / "paired_contrasts.csv", index=False)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "exploratory regime-warning versus fixed abstention and promotion-rollback benchmark",
        "status": "development_only_no_independent_selection_or_confirmation",
        "scenarios": list(SCENARIOS),
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "signal_strengths": list(signal_strengths),
        "warning_false_positive_rates": list(warning_false_positive_rates),
        "static_coverages": list(STATIC_COVERAGES),
        "warning_missingness_rates": list(warning_missingness_rates),
        "warning_event_costs_per_event": list(warning_event_costs),
        "promotion_cost": PROMOTION_COST,
        "rollback_cost": ROLLBACK_COST,
        "query_rate": 0.80,
        "budget_rate": 0.40,
        "warning_feature_visible_at_prediction": True,
        "warning_policy_uses_evaluator_truth": False,
        "matched_coverage_is_evaluator_only_reference": True,
        "all_label_caps_respected": all_caps,
        "metric_rows": len(metrics),
        "contrast_rows": len(contrast_frame),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()
        },
        "environment": environment(),
        "command": sys.argv,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    reversal_warning = (
        metrics.loc[
            metrics.scenario.eq("harmful_adaptation")
            & metrics.policy.str.startswith("warning_gate")
            & metrics.warning_false_positive_rate.eq(0.05)
            & metrics.warning_event_cost_per_event.eq(0.0005)
        ]
        .groupby(["signal_strength", "warning_missingness_rate"], as_index=False)
        .agg(
            expected_utility=("expected_net_utility", "first"),
            realized_utility=("realized_net_utility", "mean"),
            candidate_coverage=("empirical_candidate_coverage", "mean"),
            mean_warnings=("warning_events", "mean"),
        )
    )
    null_warning = (
        metrics.loc[
            metrics.scenario.isin(["stationary", "benign_nuisance", "persistent_benefit"])
            & metrics.policy.str.startswith("warning_gate")
            & metrics.warning_event_cost_per_event.eq(0.0005)
        ]
        .groupby(
            ["scenario", "warning_missingness_rate", "warning_false_positive_rate"],
            as_index=False,
        )
        .agg(
            mean_warnings=("warning_events", "mean"),
            mean_missing=("warning_missing_events", "mean"),
        )
    )
    null_warning["observed_conditional_warning_rate"] = null_warning.mean_warnings / (
        horizon * (1 - null_warning.warning_missingness_rate)
    )
    focus_contrasts = contrast_frame.loc[
        contrast_frame.scenario.eq("harmful_adaptation")
        & contrast_frame.signal_strength.eq(2.0)
        & contrast_frame.warning_false_positive_rate.eq(0.05)
        & contrast_frame.warning_event_cost_per_event.eq(0.0005)
        & contrast_frame.policy.str.startswith("warning_gate")
        & contrast_frame.reference.isin(
            [
                "continue",
                "promotion_rollback",
                "static_coverage_0.25",
                "matched_coverage_oracle",
            ]
        )
    ].sort_values(["warning_missingness_rate", "reference"])
    report = [
        "# Regime-warning reliability and cost development grid",
        "",
        f"Status: **{manifest['status']}**.",
        "",
        f"Rows: {len(metrics):,}; paired contrasts: {len(contrast_frame):,}; seeds per scenario: {seeds}; device: {device}.",
        "",
        f"The warning cue is a prediction-time feature. Its measured distribution is N(0,1) in the controls and N(delta,1) in harmful-adaptation deployment. Missing reads are MCAR and trigger incumbent fallback. The run varies signal strength {list(signal_strengths)}, conditional per-read false-warning target {list(warning_false_positive_rates)}, missingness {list(warning_missingness_rates)}, and acquisition cost per attempted event {list(warning_event_costs)}. Static coverage is an independent randomized incumbent mixture. Evaluator truth is used only to score utility.",
        "",
        "## Harmful adaptation: warning-rule operating points",
        "",
        "The table fixes the conditional false-warning target at 5% and sensor cost at 0.0005 per attempted event; missing reads trigger fallback.",
        "",
        "| Signal shift delta | Missing reads | Expected net utility | Mean realized utility | Candidate coverage | Mean warnings / 400 events |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in reversal_warning.itertuples(index=False):
        report.append(
            f"| {row.signal_strength:.2f} | {row.warning_missingness_rate:.0%} | {row.expected_utility:.2f} | {row.realized_utility:.2f} | {row.candidate_coverage:.3f} | {row.mean_warnings:.1f} |"
        )
    report.extend(
        [
            "",
            "The regime-warning feature does not beat continuing with the incumbent in the harmful-reversal scenario at any tested signal strength. Its best utility can still improve on promotion/rollback or a similarly low static coverage in some cells.",
            "",
            "The `matched_coverage_oracle` row is evaluator-only and cannot be selected by the learner. For every grid cell, expected warning-rule utility minus expected oracle-matched-coverage utility equals exactly `-H * warning_event_cost`; the runner checks this identity. Since the warning and missingness are independent of event-level gain in this DGP, the warning feature adds no expected utility beyond reducing candidate coverage, and positive sensing cost lowers utility further.",
            "",
            "## No-warning controls",
            "",
            "Observed conditional warning rates divide warning events by available reads. They are marginal per-event rates, not run-level false-alarm probabilities.",
            "",
            "| Scenario | Missing reads | Target conditional rate | Observed conditional rate |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in null_warning.itertuples(index=False):
        report.append(
            f"| {row.scenario} | {row.warning_missingness_rate:.0%} | {row.warning_false_positive_rate:.0%} | {row.observed_conditional_warning_rate:.2%} |"
        )
    report.extend(
        [
            "",
            "## Paired utility contrasts at delta=2, 5% warning target, 0.0005 sensor cost",
            "",
            "Intervals are seed-cluster bootstrap 95% intervals, unadjusted across this development grid.",
            "",
            "| Missing reads | Reference policy | Mean paired utility difference | 95% interval |",
            "|---:|---|---:|---:|",
        ]
    )
    for row in focus_contrasts.itertuples(index=False):
        report.append(
            f"| {row.warning_missingness_rate:.0%} | {row.reference} | {row.paired_realized_utility_difference:.2f} | [{row.seed_bootstrap_ci95_low:.2f}, {row.seed_bootstrap_ci95_high:.2f}] |"
        )
    report.extend(
        [
            "",
            "This is an exploratory sensitivity grid with a deliberately informative feature shift and MCAR missingness. It does not show that warning reliability is known in real deployment. The warning and fixed-coverage policies use no labels and incur different information costs from the queried promotion/rollback gate; utility and resource use must be interpreted together. Contrasts are unadjusted across the development grid. Do not select a policy from these intervals. Any selected rule requires a fresh calibration and disjoint confirmation block.",
            "",
            "No figure was generated because PaperBanana is unavailable in this session; no substitute visual generator was used.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "uv run shiftlab-dive-regime-warning-grid --seeds 500 --horizon 400 --device cuda --output-dir outputs/regime_warning_grid_500",
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
    parser.add_argument("--signal-strengths", type=float, nargs="+", default=SIGNAL_STRENGTHS)
    parser.add_argument(
        "--warning-false-positive-rates",
        type=float,
        nargs="+",
        default=WARNING_FALSE_POSITIVE_RATES,
    )
    parser.add_argument(
        "--warning-missingness-rates",
        type=float,
        nargs="+",
        default=WARNING_MISSINGNESS_RATES,
    )
    parser.add_argument(
        "--warning-event-costs",
        type=float,
        nargs="+",
        default=WARNING_EVENT_COSTS,
    )
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=2_000)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/regime_warning_grid"))
    args = parser.parse_args()
    metrics, contrasts, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        signal_strengths=tuple(args.signal_strengths),
        warning_false_positive_rates=tuple(args.warning_false_positive_rates),
        warning_missingness_rates=tuple(args.warning_missingness_rates),
        warning_event_costs=tuple(args.warning_event_costs),
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
