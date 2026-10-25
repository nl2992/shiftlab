"""Independent calibration and confirmation for volume-weighted context alpha."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

from ..data.gpu.environment import environment
from .contextual_weighted_alpha_grid import (
    BASE_PROMOTION_COST,
    BASE_ROLLBACK_COST,
    BUDGET_RATES,
    HORIZON,
    LABEL_PRICE,
    PROXY_ERROR_RATES,
    QUERY_RATE,
    SCENARIOS,
    TRUE_HARMFUL_PREVALENCES,
    _alpha_weights,
    _score_stratified,
    generate_proxy_streams,
)

CALIBRATION_OFFSET = 103_102_024
CONFIRMATION_OFFSET = 113_102_024
DEVELOPMENT_OFFSET = 92_102_024
CALIBRATION_SEEDS = 2_000
CONFIRMATION_SEEDS = 2_000
INTERVENTION_COST_MULTIPLIERS = (0.0, 1.0, 2.0, 4.0)
PRIMARY_MINIMUM_GAIN = 1.0
PILOT_SIZE = 500
CALIBRATION_TYPES = ("promotion_null", "rollback_boundary", "persistent_benefit")
CALIBRATION_METHODS = ("equal_alpha", "volume_weighted_alpha")
CALIBRATION_CELLS = (
    len(TRUE_HARMFUL_PREVALENCES)
    * len(PROXY_ERROR_RATES)
    * len(CALIBRATION_TYPES)
    * len(CALIBRATION_METHODS)
)
DEVELOPMENT_PROFILE_COUNT = len(SCENARIOS) * len(TRUE_HARMFUL_PREVALENCES) * len(PROXY_ERROR_RATES)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("Clopper-Pearson inputs require 0 <= events <= trials and trials > 0")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def _profile_inputs(
    *,
    prevalence: float,
    error: float,
    horizon: int,
    seed: int,
    device: str,
) -> tuple[np.ndarray, np.ndarray]:
    _, _, _, contexts, pilot_counts = generate_proxy_streams(
        scenario="heterogeneous_reversal",
        seeds=1,
        horizon=horizon,
        true_harmful_prevalence=prevalence,
        proxy_error_rate=error,
        seed=seed,
        device=device,
    )
    return contexts, pilot_counts


def _generate_calibration_gains(
    *,
    contexts: np.ndarray,
    seeds: int,
    horizon: int,
    calibration_type: str,
    rollback_cost: float,
    seed: int,
    device: str,
) -> np.ndarray:
    generator = torch.Generator(device=device).manual_seed(seed)
    gains = torch.empty((seeds, 2 * horizon), dtype=torch.float32, device=device)
    for group in range(2):
        indices_np = np.flatnonzero(contexts == group)
        if len(indices_np) % 2:
            raise ValueError("each proxy group must have equal shadow/deployment counts")
        group_horizon = len(indices_np) // 2
        if calibration_type == "promotion_null":
            shadow_mean = deployment_mean = 0.0
        elif calibration_type == "rollback_boundary":
            shadow_mean = 2.0
            deployment_mean = -rollback_cost / group_horizon
        elif calibration_type == "persistent_benefit":
            shadow_mean, deployment_mean = 2.0, 0.40
        else:
            raise ValueError(f"unknown calibration type {calibration_type!r}")
        probabilities = torch.tensor(
            ((shadow_mean + 1) / 6, (deployment_mean + 1) / 6),
            dtype=torch.float32,
            device=device,
        )
        uniforms = torch.rand((seeds, 2 * group_horizon), generator=generator, device=device)
        phase = torch.arange(2 * group_horizon, device=device) >= group_horizon
        outcome_one = uniforms < probabilities[phase.long()].unsqueeze(0)
        group_gains = torch.where(outcome_one, 5.0, -1.0)
        gains[:, torch.as_tensor(indices_np, dtype=torch.long, device=device)] = group_gains
    return gains.cpu().numpy().astype(float)


def run_calibration(
    output_dir: str | Path,
    *,
    seeds: int = CALIBRATION_SEEDS,
    seed_offset: int = CALIBRATION_OFFSET,
    horizon: int = HORIZON,
    device: str = "cuda",
) -> tuple[pd.DataFrame, dict]:
    """Calibrate both alpha allocations over nondegenerate null profiles."""
    if seeds < 1 or horizon < 200 or horizon % 2:
        raise ValueError("seeds >=1 and even horizon >=200 required")
    if seed_offset <= DEVELOPMENT_OFFSET + (DEVELOPMENT_PROFILE_COUNT - 1) * 211_019 + 199:
        raise ValueError("calibration seed block must be disjoint from development")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    caps_ok = True
    cell_alpha = 0.05 / CALIBRATION_CELLS
    profile_idx = 0
    for prevalence in TRUE_HARMFUL_PREVALENCES:
        for error in PROXY_ERROR_RATES:
            profile_seed = seed_offset + profile_idx * 1_000_003
            contexts, pilot_counts = _profile_inputs(
                prevalence=prevalence,
                error=error,
                horizon=horizon,
                seed=profile_seed,
                device=device,
            )
            allocations = _alpha_weights(pilot_counts)
            for type_idx, calibration_type in enumerate(CALIBRATION_TYPES):
                gains = _generate_calibration_gains(
                    contexts=contexts,
                    seeds=seeds,
                    horizon=horizon,
                    calibration_type=calibration_type,
                    rollback_cost=BASE_ROLLBACK_COST,
                    seed=profile_seed + (type_idx + 1) * 97_409,
                    device=device,
                )
                query_generator = torch.Generator(device=device).manual_seed(
                    profile_seed + (type_idx + 1) * 181_081
                )
                query_uniforms = (
                    torch.rand((seeds, 2 * horizon), generator=query_generator, device=device)
                    .cpu()
                    .numpy()
                )
                expected = np.zeros(2 * horizon, dtype=float)
                for method in CALIBRATION_METHODS:
                    gate = _score_stratified(
                        gains=gains,
                        expected=expected,
                        contexts=contexts,
                        query_uniforms=query_uniforms,
                        horizon=horizon,
                        budget_rate=0.40,
                        alpha_weights=allocations[method],
                        promotion_cost=BASE_PROMOTION_COST,
                        rollback_cost=BASE_ROLLBACK_COST,
                        label_price=LABEL_PRICE,
                        query_rate=QUERY_RATE,
                    )
                    caps_ok &= bool(gate["budget_respected"].all())
                    if calibration_type == "promotion_null":
                        risk = np.ones(seeds, dtype=bool)
                        event = gate["promoted"].any(axis=1)
                        endpoint = "familywise_false_promotion"
                    else:
                        risk = gate["promoted"].any(axis=1)
                        event = gate["rolled_back"].any(axis=1)
                        endpoint = "familywise_false_rollback"
                    trials = int(risk.sum())
                    events = int((event & risk).sum())
                    upper = _cp_upper(events, trials, cell_alpha) if trials else 1.0
                    rows.append(
                        {
                            "prevalence": prevalence,
                            "proxy_error": error,
                            "calibration_type": calibration_type,
                            "method": method,
                            "endpoint": endpoint,
                            "events": events,
                            "trials": trials,
                            "simultaneous_alpha": cell_alpha,
                            "upper_exact_bound": upper,
                            "cell_pass": trials >= 1_000 and upper <= 0.05,
                            "all_caps_respected": bool(gate["budget_respected"].all()),
                        }
                    )
            profile_idx += 1
    table = pd.DataFrame(rows)
    table.to_csv(output / "calibration.csv", index=False)
    passed = bool(table.cell_pass.all() and caps_ok)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "failed",
        "purpose": "independent simultaneous calibration for equal and pilot-volume-weighted context alpha allocations",
        "seed_offset": seed_offset,
        "seeds_per_cell": seeds,
        "development_seed_offset": DEVELOPMENT_OFFSET,
        "horizon_per_phase": horizon,
        "query_rate": QUERY_RATE,
        "budget_rate": 0.40,
        "promotion_cost": BASE_PROMOTION_COST,
        "rollback_cost": BASE_ROLLBACK_COST,
        "familywise_alpha": 0.05,
        "simultaneous_cells": CALIBRATION_CELLS,
        "cell_alpha": cell_alpha,
        "prevalences": list(TRUE_HARMFUL_PREVALENCES),
        "proxy_errors": list(PROXY_ERROR_RATES),
        "calibration_types": list(CALIBRATION_TYPES),
        "methods": list(CALIBRATION_METHODS),
        "all_cells_pass": bool(table.cell_pass.all()),
        "all_label_caps_respected": caps_ok,
        "calibration_sha256": _sha256(output / "calibration.csv"),
        "code_sha256": {
            "contextual_weighted_alpha_validation.py": _sha256(Path(__file__)),
            "contextual_weighted_alpha_grid.py": _sha256(
                Path(__file__).with_name("contextual_weighted_alpha_grid.py")
            ),
            "closed_loop_intervention.py": _sha256(
                Path(__file__).with_name("closed_loop_intervention.py")
            ),
        },
        "environment": environment(),
        "limitation": "Finite-sample calibration for the registered bounded synthetic profiles; the validity argument remains conditional on the predictable pilot weights, per-context nulls, and randomized query assumptions.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Volume-weighted context-alpha independent calibration",
        "",
        f"Status: **{manifest['status']}**; {seeds} streams per cell; seed root {seed_offset}; device {device}.",
        "",
        f"The simultaneous family has {CALIBRATION_CELLS} cells across nine prevalence/noise profiles, three endpoints, and two alpha allocations. Each one-sided exact Clopper-Pearson upper bound uses alpha 0.05/{CALIBRATION_CELLS}={cell_alpha:.6f}. False rollback is evaluated among streams where at least one context was promoted; events count any rollback among those promoted contexts.",
        "",
        table.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The promotion null has zero paired-gain mean in both contexts. The rollback-boundary profile has shadow mean +2 and deployment mean exactly `-rollback_cost/n_j` in each context with `n_j` events per phase. The persistent-benefit profile has deployment mean +0.40 in both groups. Every profile has nonzero outcome variance.",
        "",
        "This simulation checks implementation and finite-sample behavior; it does not replace the conditional-supermartingale proof or extend validity beyond the assumptions in the protocol.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return table, manifest


def _bootstrap_profile_means(
    profile_differences: list[np.ndarray], *, replicates: int, seed: int
) -> tuple[float, float, float, np.ndarray]:
    seeds = len(profile_differences[0])
    point = float(np.mean([difference.mean() for difference in profile_differences]))
    bootstrap = np.zeros(replicates, dtype=float)
    for index, differences in enumerate(profile_differences):
        rng = np.random.default_rng(seed + index * 73_121)
        sample_idx = rng.integers(0, seeds, size=(replicates, seeds))
        bootstrap += differences[sample_idx].mean(axis=1) / len(profile_differences)
    lower, upper = np.quantile(bootstrap, [0.025, 0.975])
    return point, float(lower), float(upper), bootstrap


def run_confirmation(
    output_dir: str | Path,
    calibration_manifest: str | Path,
    *,
    seeds: int = CONFIRMATION_SEEDS,
    seed_offset: int = CONFIRMATION_OFFSET,
    horizon: int = HORIZON,
    bootstrap_replicates: int = 5_000,
    device: str = "cuda",
) -> tuple[pd.DataFrame, dict]:
    """Fresh-seed confirmation of volume-weighted versus equal alpha."""
    calibration_path = Path(calibration_manifest)
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if calibration.get("status") != "passed":
        raise ValueError("confirmation requires a passed independent calibration manifest")
    if seeds < 2 or horizon != int(calibration["horizon_per_phase"]):
        raise ValueError("confirmation seed count and horizon are incompatible with calibration")
    last_calibration_seed = (
        int(calibration["seed_offset"]) + 8 * 1_000_003 + int(calibration["seeds_per_cell"]) - 1
    )
    if seed_offset <= last_calibration_seed:
        raise ValueError("confirmation seed block must follow and be disjoint from calibration")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    profile_differences = []
    profile_summary = []
    all_caps = True
    n_settings = len(INTERVENTION_COST_MULTIPLIERS) * len(BUDGET_RATES)
    profile_idx = 0
    for prevalence in TRUE_HARMFUL_PREVALENCES:
        for error in PROXY_ERROR_RATES:
            profile_seed = seed_offset + profile_idx * 1_000_003
            features, gains, expected, contexts, pilot_counts = generate_proxy_streams(
                scenario="heterogeneous_reversal",
                seeds=seeds,
                horizon=horizon,
                true_harmful_prevalence=prevalence,
                proxy_error_rate=error,
                seed=profile_seed,
                device=device,
            )
            del features
            observed_prevalence = float(contexts[horizon:].mean())
            allocations = _alpha_weights(pilot_counts)
            query_generator = torch.Generator(device=device).manual_seed(profile_seed + 38_102_024)
            query_uniforms = (
                torch.rand((seeds, 2 * horizon), generator=query_generator, device=device)
                .cpu()
                .numpy()
            )
            profile_difference = np.zeros(seeds, dtype=float)
            cell_rows = []
            cell_contrasts = []
            for cost_multiplier in INTERVENTION_COST_MULTIPLIERS:
                promotion_cost = BASE_PROMOTION_COST * cost_multiplier
                rollback_cost = BASE_ROLLBACK_COST * cost_multiplier
                for budget_rate in BUDGET_RATES:
                    gate_outcomes = {}
                    for method in CALIBRATION_METHODS:
                        gate = _score_stratified(
                            gains=gains,
                            expected=expected,
                            contexts=contexts,
                            query_uniforms=query_uniforms,
                            horizon=horizon,
                            budget_rate=budget_rate,
                            alpha_weights=allocations[method],
                            promotion_cost=promotion_cost,
                            rollback_cost=rollback_cost,
                            label_price=LABEL_PRICE,
                            query_rate=QUERY_RATE,
                        )
                        all_caps &= bool(gate["budget_respected"].all())
                        gate_outcomes[method] = gate
                        for stream in range(seeds):
                            cell_rows.append(
                                {
                                    "scenario": "heterogeneous_reversal",
                                    "prevalence": prevalence,
                                    "proxy_error": error,
                                    "observed_proxy_prevalence": observed_prevalence,
                                    "cost_multiplier": cost_multiplier,
                                    "budget_rate": budget_rate,
                                    "method": method,
                                    "seed": profile_seed + stream,
                                    "promoted_groups": int(gate["promoted"][stream].sum()),
                                    "rolled_back_groups": int(gate["rolled_back"][stream].sum()),
                                    "harmful_proxy_groups_rolled_back": int(
                                        (
                                            gate["rolled_back"][stream]
                                            & (
                                                np.array(
                                                    [
                                                        expected[horizon:][
                                                            contexts[horizon:] == j
                                                        ].mean()
                                                        for j in range(2)
                                                    ]
                                                )
                                                < 0
                                            )
                                        ).sum()
                                    ),
                                    "safe_proxy_groups_retained": int(
                                        (
                                            gate["promoted"][stream]
                                            & ~gate["rolled_back"][stream]
                                            & (
                                                np.array(
                                                    [
                                                        expected[horizon:][
                                                            contexts[horizon:] == j
                                                        ].mean()
                                                        for j in range(2)
                                                    ]
                                                )
                                                >= 0
                                            )
                                        ).sum()
                                    ),
                                    "labels_queried": int(gate["labels_queried"][stream]),
                                    "label_budget": int(np.floor(budget_rate * 2 * horizon)),
                                    "budget_respected": bool(gate["budget_respected"][stream]),
                                    "realized_net_utility": float(gate["realized_utility"][stream]),
                                    "expected_net_utility": float(gate["expected_utility"][stream]),
                                    "alpha_weight_safe": float(allocations[method][0]),
                                    "alpha_weight_harmful": float(allocations[method][1]),
                                    "pilot_safe_count": int(pilot_counts[0]),
                                    "pilot_harmful_count": int(pilot_counts[1]),
                                }
                            )
                    difference = (
                        gate_outcomes["volume_weighted_alpha"]["realized_utility"]
                        - gate_outcomes["equal_alpha"]["realized_utility"]
                    )
                    profile_difference += difference / n_settings
                    cell_contrasts.append(
                        {
                            "cost_multiplier": cost_multiplier,
                            "budget_rate": budget_rate,
                            "paired_mean_utility_difference": float(difference.mean()),
                        }
                    )
            profile_differences.append(profile_difference)
            profile_summary.append(
                {
                    "prevalence": prevalence,
                    "proxy_error": error,
                    "observed_proxy_prevalence": observed_prevalence,
                    "paired_mean_over_cost_budget_grid": float(profile_difference.mean()),
                    "cells": cell_contrasts,
                }
            )
            rows.extend(cell_rows)
            profile_idx += 1

    point, lower, upper, _ = _bootstrap_profile_means(
        profile_differences, replicates=bootstrap_replicates, seed=seed_offset + 60_102_024
    )
    metrics = pd.DataFrame(rows)
    metrics_path = output / "metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    primary = pd.DataFrame(
        [
            {
                "estimand": "equal-weight average over 9 prevalence/noise profiles and 12 cost/budget settings",
                "method": "volume_weighted_alpha",
                "reference": "equal_alpha",
                "paired_mean_realized_utility_difference": point,
                "bootstrap_ci95_low": lower,
                "bootstrap_ci95_high": upper,
                "minimum_practical_gain": PRIMARY_MINIMUM_GAIN,
                "primary_gate_passed": lower > PRIMARY_MINIMUM_GAIN,
                "profile_count": len(profile_differences),
                "settings_per_profile": n_settings,
                "seed_clusters_per_profile": seeds,
                "bootstrap_replicates": bootstrap_replicates,
            }
        ]
    )
    primary.to_csv(output / "primary_contrast.csv", index=False)
    pd.DataFrame(
        [
            {
                "prevalence": profile["prevalence"],
                "proxy_error": profile["proxy_error"],
                "observed_proxy_prevalence": profile["observed_proxy_prevalence"],
                "paired_mean_over_cost_budget_grid": profile["paired_mean_over_cost_budget_grid"],
            }
            for profile in profile_summary
        ]
    ).to_csv(output / "profile_contrasts.csv", index=False)
    contrast_by_cell = []
    for profile in profile_summary:
        for cell in profile["cells"]:
            contrast_by_cell.append(
                {
                    "prevalence": profile["prevalence"],
                    "proxy_error": profile["proxy_error"],
                    **cell,
                }
            )
    pd.DataFrame(contrast_by_cell).to_csv(output / "cell_contrasts.csv", index=False)
    calibration_sha = _sha256(calibration_path)
    passed = bool(lower > PRIMARY_MINIMUM_GAIN and all_caps)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "minimum_gain_not_confirmed",
        "purpose": "fresh-seed confirmation of volume-weighted versus equal context-alpha allocation",
        "seed_offset": seed_offset,
        "seeds_per_profile": seeds,
        "calibration_seed_offset": calibration["seed_offset"],
        "calibration_manifest_sha256": calibration_sha,
        "horizon_per_phase": horizon,
        "query_rate": QUERY_RATE,
        "cost_multipliers": list(INTERVENTION_COST_MULTIPLIERS),
        "budget_rates": list(BUDGET_RATES),
        "primary_minimum_gain_per_800_event_stream": PRIMARY_MINIMUM_GAIN,
        "primary_mean_difference": point,
        "primary_ci95": [lower, upper],
        "primary_gate_passed": lower > PRIMARY_MINIMUM_GAIN,
        "profile_count": len(profile_differences),
        "settings_per_profile": n_settings,
        "all_label_caps_respected": all_caps,
        "metric_rows": len(metrics),
        "metrics_sha256": _sha256(metrics_path),
        "primary_contrast_sha256": _sha256(output / "primary_contrast.csv"),
        "code_sha256": {
            "contextual_weighted_alpha_validation.py": _sha256(Path(__file__)),
            "contextual_weighted_alpha_grid.py": _sha256(
                Path(__file__).with_name("contextual_weighted_alpha_grid.py")
            ),
            "closed_loop_intervention.py": _sha256(
                Path(__file__).with_name("closed_loop_intervention.py")
            ),
        },
        "environment": environment(),
        "interpretation_limit": "Confirmation targets only the equal-weight synthetic factor-grid average; it is not a claim of superiority for every prevalence/noise/cost/budget cell or an application-grounded utility gain.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Volume-weighted context-alpha independent confirmation",
        "",
        f"Status: **{manifest['status']}**; {seeds} seeds per prevalence/noise profile; seed root {seed_offset}; device {device}.",
        "",
        "The primary estimand is the equally weighted mean realized-utility difference between volume-weighted and equal alpha across the nine registered prevalence/noise profiles and all twelve intervention-cost/label-cap settings. The utility margin was fixed at +1.0 per 800-event stream, equal to one false-positive cost unit in the simulator. The paired seed bootstrap resamples streams within each fixed profile and averages profiles equally.",
        "",
        primary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Profile-level means",
        "",
        pd.DataFrame(
            [
                {
                    "prevalence": profile["prevalence"],
                    "proxy_error": profile["proxy_error"],
                    "paired_mean": profile["paired_mean_over_cost_budget_grid"],
                }
                for profile in profile_summary
            ]
        ).to_markdown(index=False, floatfmt=".4f"),
        "",
        f"All per-context label caps respected: {all_caps}.",
        "",
        "The independent calibration covers stationary promotion nulls, least-favourable per-context rollback boundaries, and persistent-benefit rollback controls for both allocations. This confirmation evaluates only the preselected heterogeneous-reversal utility comparison; the result does not imply cellwise superiority or external validity.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return primary, manifest


def main_calibration() -> None:
    parser = argparse.ArgumentParser(description="Calibrate context alpha allocations")
    parser.add_argument("--seeds", type=int, default=CALIBRATION_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=CALIBRATION_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/contextual_weighted_alpha_calibration_2000"),
    )
    args = parser.parse_args()
    _, manifest = run_calibration(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
    )
    print(json.dumps(manifest, indent=2))


def main_confirmation() -> None:
    parser = argparse.ArgumentParser(description="Confirm volume-weighted context alpha")
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path("outputs/contextual_weighted_alpha_calibration_2000/manifest.json"),
    )
    parser.add_argument("--seeds", type=int, default=CONFIRMATION_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=CONFIRMATION_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--bootstrap-replicates", type=int, default=5_000)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/contextual_weighted_alpha_confirmation_2000"),
    )
    args = parser.parse_args()
    _, manifest = run_confirmation(
        args.output_dir,
        args.calibration_manifest,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        bootstrap_replicates=args.bootstrap_replicates,
        device=args.device,
    )
    print(json.dumps(manifest, indent=2))
