"""Gate-level benchmark for nested candidate-by-context alpha spending.

This simulator isolates the multiple-testing and hard-query-budget layer. The
13 candidates are frozen utility processes rather than fitted classifiers; it
does not replace the fitted-model promotion benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

from ..data.gpu.environment import environment

CANDIDATES = 13
CONTEXTS = 2
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
METHODS = ("rank_only", "nested_equal", "nested_volume")
PROFILES = ("null", "strict_negative", "homogeneous_benefit", "specialists", "reversal")
PREVALENCES = (0.1, 0.5, 0.9)
PROXY_ERRORS = (0.0, 0.05, 0.1)
BUDGET_RATES = (0.2, 0.4)
QUERY_RATE = 0.8
VALIDATION_HORIZON = 200
MONITOR_HORIZON = 400
DEPLOYMENT_HORIZON = 400
PILOT_HORIZON = 500
SWITCHING_COST = 0.2
LABEL_PRICE = 0.01
ALPHA = 0.05
DEVELOPMENT_SEED_OFFSET = 1_124_202_026
CALIBRATION_SEED_OFFSET = 2_124_102_026
CONFIRMATION_SEED_OFFSET = 3_124_302_026
CONFIRMATION_BOOTSTRAP_SEED = 9_982_303_019
PRIMARY_MARGIN = 1.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_block_end(seed_offset: int, cells: int, seeds_per_cell: int) -> int:
    return seed_offset + (cells - 1) * 1_000_019 + seeds_per_cell - 1


def candidate_rank_weights(order: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Return validation-rank weights in original candidate order.

    The rank sequence ``1/[r(r+1)]`` is summable and its finite-grid sum is
    below one, so it supports either a finite grid or candidates appended later.
    """
    order = np.asarray(order, dtype=int)
    if (
        order.ndim != 1
        or len(order) < 1
        or not np.array_equal(np.sort(order), np.arange(len(order)))
    ):
        raise ValueError("order must be a permutation of candidate indices")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    ranks = np.empty(len(order), dtype=int)
    ranks[order] = np.arange(1, len(order) + 1)
    return alpha / (ranks * (ranks + 1))


def nested_alpha_weights(
    order: np.ndarray, pilot_counts: np.ndarray, alpha: float = ALPHA
) -> dict[str, np.ndarray]:
    """Compose candidate-rank weights with outcome-free context weights."""
    order = np.asarray(order, dtype=int)
    counts = np.asarray(pilot_counts, dtype=float)
    if counts.shape != (CONTEXTS,) or not np.isfinite(counts).all() or np.any(counts < 0):
        raise ValueError("pilot_counts must be two finite nonnegative counts")
    if counts.sum() <= 0:
        raise ValueError("pilot must observe at least one context")
    candidate = candidate_rank_weights(order, alpha)
    context_volume = (counts + 0.5) / (counts.sum() + CONTEXTS * 0.5)
    equal = np.full(CONTEXTS, 1 / CONTEXTS)
    return {
        "rank_only": candidate,
        "nested_equal": candidate[:, None] * equal[None, :],
        "nested_volume": candidate[:, None] * context_volume[None, :],
    }


def _profile_means(profile: str, phase: str) -> np.ndarray:
    """Means by candidate and latent context; gains have support [-1, 1]."""
    if profile not in PROFILES or phase not in {"validation", "monitor", "deployment"}:
        raise ValueError("unknown profile or phase")
    means = np.zeros((CANDIDATES, CONTEXTS), dtype=np.float32)
    if profile == "strict_negative":
        means.fill(-0.15)
    elif profile == "homogeneous_benefit":
        means[0] = (0.34, 0.34)
        means[1] = (0.20, 0.20)
        means[2] = (0.08, 0.08)
        means[3:] = -0.05
    elif profile == "specialists":
        means[0] = (0.38, -0.16)
        means[1] = (-0.16, 0.38)
        means[2] = (0.10, 0.10)
        means[3:] = -0.08
    elif profile == "reversal":
        means[0] = (0.32, 0.32)
        means[1] = (0.14, 0.14)
        means[2:] = -0.05
        if phase == "deployment":
            means[0] = (-0.30, -0.30)
            means[1] = (-0.10, -0.10)
    return means


def _draw_contexts(
    seeds: int,
    horizon: int,
    prevalence: float,
    proxy_error: float,
    *,
    generator: torch.Generator,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    latent = torch.rand((seeds, horizon), generator=generator, device=device) < prevalence
    flip = torch.rand((seeds, horizon), generator=generator, device=device) < proxy_error
    observed = torch.logical_xor(latent, flip).to(torch.long)
    return latent.to(torch.long), observed


def _draw_gains(
    latent: torch.Tensor,
    means: np.ndarray,
    *,
    generator: torch.Generator,
    device: torch.device,
) -> torch.Tensor:
    mean_tensor = torch.as_tensor(means, dtype=torch.float32, device=device)
    conditional_means = torch.where(
        latent.unsqueeze(-1).bool(), mean_tensor[:, 1], mean_tensor[:, 0]
    )
    common_uniform = torch.rand(
        (*latent.shape, 1), generator=generator, device=device, dtype=torch.float32
    )
    return torch.where(
        common_uniform < (conditional_means + 1) / 2,
        torch.ones_like(conditional_means),
        -torch.ones_like(conditional_means),
    )


def _first_ranked(order: np.ndarray, crossings: np.ndarray) -> int | None:
    return next((int(index) for index in order if crossings[int(index)]), None)


def _log_e(log_wealth: torch.Tensor) -> torch.Tensor:
    return torch.logsumexp(log_wealth, dim=-1) - np.log(len(STAKES))


def simulate_block(
    *,
    profile: str,
    seeds: int,
    seed: int,
    prevalence: float,
    proxy_error: float,
    budget_rate: float,
    device: str = "cuda",
) -> pd.DataFrame:
    """Simulate paired allocation rules with shared outcomes and hard label cap."""
    if profile not in PROFILES or seeds < 1:
        raise ValueError("invalid profile or seed count")
    if not 0 < prevalence < 1 or not 0 <= proxy_error < 0.5:
        raise ValueError("invalid prevalence or proxy error")
    if budget_rate not in BUDGET_RATES:
        raise ValueError("budget_rate must be one of the registered rates")
    if device not in {"cpu", "cuda"} or (device == "cuda" and not torch.cuda.is_available()):
        raise ValueError("requested device is unavailable or unsupported")
    torch_device = torch.device(device)
    generator = torch.Generator(device=torch_device).manual_seed(seed)

    _, pilot_context = _draw_contexts(
        seeds,
        PILOT_HORIZON,
        prevalence,
        proxy_error,
        generator=generator,
        device=torch_device,
    )
    pilot_counts = torch.stack(
        ((pilot_context == 0).sum(dim=1), (pilot_context == 1).sum(dim=1)), dim=1
    )
    validation_latent, _ = _draw_contexts(
        seeds,
        VALIDATION_HORIZON,
        prevalence,
        proxy_error,
        generator=generator,
        device=torch_device,
    )
    monitor_latent, monitor_context = _draw_contexts(
        seeds,
        MONITOR_HORIZON,
        prevalence,
        proxy_error,
        generator=generator,
        device=torch_device,
    )
    deployment_latent, deployment_context = _draw_contexts(
        seeds,
        DEPLOYMENT_HORIZON,
        prevalence,
        proxy_error,
        generator=generator,
        device=torch_device,
    )
    validation_gains = _draw_gains(
        validation_latent,
        _profile_means(profile, "validation"),
        generator=generator,
        device=torch_device,
    )
    monitor_gains = _draw_gains(
        monitor_latent,
        _profile_means(profile, "monitor"),
        generator=generator,
        device=torch_device,
    )
    deployment_gains = _draw_gains(
        deployment_latent,
        _profile_means(profile, "deployment"),
        generator=generator,
        device=torch_device,
    )
    query_uniforms = torch.rand((seeds, MONITOR_HORIZON), generator=generator, device=torch_device)
    query_path = query_uniforms < QUERY_RATE

    # Candidate ranking sees independent, fully labelled validation outcomes;
    # context weights use only pre-monitor proxy counts, never their labels.
    order = torch.argsort(validation_gains.mean(dim=1), dim=1, descending=True, stable=True)
    ranks = torch.empty_like(order)
    ranks.scatter_(
        1,
        order,
        torch.arange(1, CANDIDATES + 1, device=torch_device)[None, :].expand(seeds, -1),
    )
    candidate_alpha = ALPHA / (ranks.float() * (ranks.float() + 1))
    context_volume = (pilot_counts.float() + 0.5) / (PILOT_HORIZON + 1.0)
    context_equal = torch.full_like(context_volume, 0.5)
    candidate_context_alpha = {
        "nested_equal": candidate_alpha[:, :, None] * context_equal[:, None, :],
        "nested_volume": candidate_alpha[:, :, None] * context_volume[:, None, :],
    }

    query_budget = int(np.floor(budget_rate * MONITOR_HORIZON))
    previous_queries = query_path.cumsum(dim=1) - query_path.long()
    active = previous_queries < query_budget
    switch_global = SWITCHING_COST / DEPLOYMENT_HORIZON
    q_min = budget_rate / 2
    global_bound = 1 / q_min + switch_global
    stakes = torch.tensor(STAKES, dtype=torch.float32, device=torch_device)
    rank_log_wealth = torch.zeros((seeds, CANDIDATES, len(STAKES)), device=torch_device)
    context_log_wealth = {
        method: torch.zeros((seeds, CANDIDATES, CONTEXTS, len(STAKES)), device=torch_device)
        for method in ("nested_equal", "nested_volume")
    }
    rank_crossed = torch.zeros((seeds, CANDIDATES), dtype=torch.bool, device=torch_device)
    context_crossed = {
        method: torch.zeros((seeds, CANDIDATES, CONTEXTS), dtype=torch.bool, device=torch_device)
        for method in ("nested_equal", "nested_volume")
    }
    labels = torch.zeros(seeds, dtype=torch.long, device=torch_device)
    processed = torch.zeros(seeds, dtype=torch.long, device=torch_device)

    for time_index in range(MONITOR_HORIZON):
        is_active = active[:, time_index]
        queried = query_path[:, time_index] & is_active
        labels += queried.long()
        processed += is_active.long()
        raw = monitor_gains[:, time_index, :]
        estimate = queried[:, None] * raw / QUERY_RATE

        net = estimate - switch_global
        normalized = net / global_bound
        log_increment = torch.log1p(stakes[None, None, :] * normalized[:, :, None])
        rank_log_wealth += log_increment * is_active[:, None, None]
        rank_crossed |= _log_e(rank_log_wealth) >= -torch.log(candidate_alpha)

        for method in ("nested_equal", "nested_volume"):
            method_log = context_log_wealth[method]
            for group in range(CONTEXTS):
                context_rate = SWITCHING_COST / (
                    DEPLOYMENT_HORIZON * context_volume[:, group].clamp_min(1 / PILOT_HORIZON)
                )
                bound = 1 / q_min + context_rate
                group_net = estimate - context_rate[:, None]
                group_normalized = group_net / bound[:, None]
                group_log_increment = torch.log1p(
                    stakes[None, None, :] * group_normalized[:, :, None]
                )
                update = is_active & monitor_context[:, time_index].eq(group)
                method_log[:, :, group, :] += group_log_increment * update[:, None, None]
            threshold = -torch.log(candidate_context_alpha[method])
            context_crossed[method] |= _log_e(method_log) >= threshold

    # The evaluator scores each stream on untouched deployment outcomes. These
    # arrays are never used by the monitor or alpha allocation.
    rows: list[dict[str, Any]] = []
    order_cpu = order.cpu().numpy()
    rank_crossed_cpu = rank_crossed.cpu().numpy()
    context_crossed_cpu = {key: value.cpu().numpy() for key, value in context_crossed.items()}
    labels_cpu = labels.cpu().numpy()
    processed_cpu = processed.cpu().numpy()
    dep_gains = deployment_gains.cpu().numpy()
    dep_latent_np = deployment_latent.cpu().numpy()
    dep_context_np = deployment_context.cpu().numpy()
    mean_tables = {phase: _profile_means(profile, phase) for phase in ("monitor", "deployment")}
    expected_deploy = np.where(
        dep_latent_np[:, :, None].astype(bool),
        mean_tables["deployment"][None, None, :, 1],
        mean_tables["deployment"][None, None, :, 0],
    )
    for stream in range(seeds):
        rank = order_cpu[stream]
        selected_rank = _first_ranked(rank, rank_crossed_cpu[stream])
        for method in METHODS:
            if method == "rank_only":
                picked = selected_rank
                if picked is None:
                    expected_utility = realized_utility = 0.0
                else:
                    expected_utility = float(expected_deploy[stream, :, picked].sum())
                    realized_utility = float(dep_gains[stream, :, picked].sum())
                    expected_utility -= SWITCHING_COST
                    realized_utility -= SWITCHING_COST
            else:
                by_group = {
                    group: _first_ranked(rank, context_crossed_cpu[method][stream, :, group])
                    for group in range(CONTEXTS)
                }
                expected_utility = realized_utility = 0.0
                for group, picked in by_group.items():
                    if picked is None:
                        continue
                    use = dep_context_np[stream] == group
                    expected_utility += float(expected_deploy[stream, use, picked].sum())
                    realized_utility += float(dep_gains[stream, use, picked].sum())
                    expected_utility -= SWITCHING_COST
                    realized_utility -= SWITCHING_COST
                picked = None
            promoted = (
                selected_rank is not None
                if method == "rank_only"
                else any(context_crossed_cpu[method][stream, :, g].any() for g in range(CONTEXTS))
            )
            if method != "rank_only":
                by_group = {
                    group: _first_ranked(rank, context_crossed_cpu[method][stream, :, group])
                    for group in range(CONTEXTS)
                }
                selected_value = json.dumps(by_group, sort_keys=True)
                promoted = any(value is not None for value in by_group.values())
                groups_promoted = sum(value is not None for value in by_group.values())
                exact_context_false = any(
                    value is not None
                    and abs(
                        float(
                            expected_deploy[stream, dep_context_np[stream] == group, value].mean()
                        )
                    )
                    < 1e-12
                    for group, value in by_group.items()
                    if np.any(dep_context_np[stream] == group)
                )
            else:
                selected_value = None if picked is None else f"candidate_{picked + 1}"
                groups_promoted = int(picked is not None)
                exact_context_false = False
            expected_utility -= labels_cpu[stream] * LABEL_PRICE
            realized_utility -= labels_cpu[stream] * LABEL_PRICE
            rows.append(
                {
                    "profile": profile,
                    "seed": seed + stream,
                    "prevalence": prevalence,
                    "proxy_error": proxy_error,
                    "budget_rate": budget_rate,
                    "method": method,
                    "promoted": bool(promoted),
                    "selected": selected_value,
                    "contexts_promoted": groups_promoted,
                    "false_certificate_null": bool(promoted)
                    if profile in {"null", "strict_negative"}
                    else False,
                    "harmful_deployment": bool(promoted and expected_utility <= 0),
                    "expected_deployment_utility": expected_utility,
                    "realized_deployment_utility": realized_utility,
                    "labels_queried": int(labels_cpu[stream]),
                    "label_budget": query_budget,
                    "hard_cap_respected": bool(labels_cpu[stream] <= query_budget),
                    "monitor_events_processed": int(processed_cpu[stream]),
                    "mean_monitor_context_null_diagnostic": exact_context_false,
                    "candidate_count": CANDIDATES,
                }
            )
    return pd.DataFrame(rows)


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("invalid binomial count")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def run_calibration(
    output_dir: str | Path,
    *,
    seeds: int = 2_000,
    seed_offset: int = 2_124_102_026,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Calibrate streamwise familywise crossings under nondegenerate nulls."""
    if seeds < 100:
        raise ValueError("calibration requires at least 100 independent streams per cell")
    cells = len(PREVALENCES) * len(PROXY_ERRORS) * len(BUDGET_RATES) * len(METHODS) * 2
    rows = []
    for profile_index, profile in enumerate(("null", "strict_negative")):
        for prevalence_index, prevalence in enumerate(PREVALENCES):
            for error_index, error in enumerate(PROXY_ERRORS):
                for budget_index, budget in enumerate(BUDGET_RATES):
                    base_seed = seed_offset + (
                        (
                            (profile_index * 9 + prevalence_index * 3 + error_index) * 2
                            + budget_index
                        )
                        * 1_000_019
                    )
                    frame = simulate_block(
                        profile=profile,
                        seeds=seeds,
                        seed=base_seed,
                        prevalence=prevalence,
                        proxy_error=error,
                        budget_rate=budget,
                        device=device,
                    )
                    rows.extend(frame.to_dict(orient="records"))
    detail = pd.DataFrame(rows)
    family_alpha = 0.05 / cells
    summary = detail.groupby(
        ["profile", "prevalence", "proxy_error", "budget_rate", "method"], as_index=False
    ).agg(
        false_families=("false_certificate_null", "sum"),
        streams=("seed", "count"),
        all_caps=("hard_cap_respected", "all"),
    )
    summary["familywise_rate"] = summary.false_families / summary.streams
    summary["simultaneous_cp_upper"] = [
        _cp_upper(int(row.false_families), int(row.streams), family_alpha)
        for row in summary.itertuples(index=False)
    ]
    summary["pass"] = summary.simultaneous_cp_upper <= 0.05
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    detail.to_parquet(output / "calibration_streams.parquet", index=False)
    summary.to_csv(output / "calibration_summary.csv", index=False)
    passed = bool(summary["pass"].all() and summary.all_caps.all())
    manifest = {
        "experiment": "nested_candidate_context_alpha_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "failed",
        "seed_offset": seed_offset,
        "seeds_per_cell": seeds,
        "familywise_cells": cells,
        "familywise_alpha": 0.05,
        "seed_block_end": _seed_block_end(seed_offset, 36, seeds),
        "candidate_count": CANDIDATES,
        "profiles": ["null", "strict_negative"],
        "prevalences": PREVALENCES,
        "proxy_errors": PROXY_ERRORS,
        "budget_rates": BUDGET_RATES,
        "methods": METHODS,
        "all_cells_pass": bool(summary["pass"].all()),
        "all_caps_respected": bool(summary.all_caps.all()),
        "environment": environment(),
        "limitation": "Monte Carlo calibration of the stated gate-level simulator; validity follows from bounded e-process assumptions, not empirical non-rejection. Candidate policies are utility processes, not fitted classifiers.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["artifacts_sha256"] = {
        name: _sha256(output / name)
        for name in ("calibration_streams.parquet", "calibration_summary.csv")
    }
    manifest["source_sha256"] = _sha256(Path(__file__))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return detail, summary, manifest


def run_development_grid(
    output_dir: str | Path,
    *,
    seeds: int = 200,
    seed_offset: int = DEVELOPMENT_SEED_OFFSET,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run a paired efficacy screen; no winner or error guarantee is claimed."""
    if seeds < 1:
        raise ValueError("seeds must be positive")
    rows = []
    profiles = ("homogeneous_benefit", "specialists", "reversal")
    for scenario_index, profile in enumerate(profiles):
        for prevalence_index, prevalence in enumerate(PREVALENCES):
            for error_index, error in enumerate(PROXY_ERRORS):
                for budget_index, budget in enumerate(BUDGET_RATES):
                    seed = seed_offset + (
                        (
                            (scenario_index * 9 + prevalence_index * 3 + error_index) * 2
                            + budget_index
                        )
                        * 1_000_019
                    )
                    frame = simulate_block(
                        profile=profile,
                        seeds=seeds,
                        seed=seed,
                        prevalence=prevalence,
                        proxy_error=error,
                        budget_rate=budget,
                        device=device,
                    )
                    rows.extend(frame.to_dict(orient="records"))
    detail = pd.DataFrame(rows)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    detail.to_parquet(output / "development_streams.parquet", index=False)
    paired = detail.pivot_table(
        index=["profile", "seed", "prevalence", "proxy_error", "budget_rate"],
        columns="method",
        values=["expected_deployment_utility", "realized_deployment_utility", "promoted"],
        aggfunc="first",
    ).reset_index()
    paired.to_parquet(output / "development_paired.parquet", index=False)
    summary = detail.groupby(
        ["profile", "prevalence", "proxy_error", "budget_rate", "method"], as_index=False
    ).agg(
        promotion_rate=("promoted", "mean"),
        mean_expected_utility=("expected_deployment_utility", "mean"),
        mean_realized_utility=("realized_deployment_utility", "mean"),
        mean_labels=("labels_queried", "mean"),
        cap_respected=("hard_cap_respected", "all"),
    )
    summary.to_csv(output / "development_summary.csv", index=False)
    manifest = {
        "experiment": "nested_candidate_context_alpha_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "development_only",
        "seed_offset": seed_offset,
        "seeds_per_cell": seeds,
        "seed_block_end": _seed_block_end(seed_offset, 54, seeds),
        "candidate_count": CANDIDATES,
        "profiles": profiles,
        "prevalences": PREVALENCES,
        "proxy_errors": PROXY_ERRORS,
        "budget_rates": BUDGET_RATES,
        "query_rate": QUERY_RATE,
        "methods": METHODS,
        "environment": environment(),
        "limitation": "Gate-level utility-process simulator; no fitted classifier, delayed labels, adaptive query policy, or application-grounded utility. Results are exploratory and do not establish type-I control or novelty.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["artifacts_sha256"] = {
        name: _sha256(output / name)
        for name in (
            "development_streams.parquet",
            "development_paired.parquet",
            "development_summary.csv",
        )
    }
    manifest["source_sha256"] = _sha256(Path(__file__))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return detail, summary, manifest


def _hierarchical_paired_bootstrap(
    detail: pd.DataFrame, *, draws: int = 10_000, seed: int = CONFIRMATION_BOOTSTRAP_SEED
) -> pd.DataFrame:
    """Average profile cells equally, resampling streams within each cell."""
    if draws < 1:
        raise ValueError("draws must be positive")
    rng = np.random.default_rng(seed)
    rows = []
    for comparator in ("rank_only", "nested_equal"):
        cell_vectors = []
        for _, group in detail.groupby(["prevalence", "proxy_error", "budget_rate"], sort=True):
            paired = group.pivot(
                index="seed", columns="method", values="realized_deployment_utility"
            )
            cell_vectors.append(
                (paired["nested_volume"] - paired[comparator]).to_numpy(dtype=float)
            )
        boot = np.empty(draws, dtype=float)
        for replicate in range(draws):
            boot[replicate] = np.mean(
                [
                    rng.choice(values, size=len(values), replace=True).mean()
                    for values in cell_vectors
                ]
            )
        observed = float(np.mean([values.mean() for values in cell_vectors]))
        rows.append(
            {
                "primary_metric": "realized deployment utility per 400-event stream",
                "contrast": f"nested_volume_minus_{comparator}",
                "mean_difference": observed,
                "simultaneous_ci_low": float(np.quantile(boot, 0.0125)),
                "simultaneous_ci_high": float(np.quantile(boot, 0.9875)),
                "minimum_practical_gain": PRIMARY_MARGIN,
                "bootstrap_draws": draws,
                "bootstrap_seed": seed,
                "cell_count": len(cell_vectors),
                "streams_per_cell": len(cell_vectors[0]),
            }
        )
    return pd.DataFrame(rows)


def run_confirmation(
    output_dir: str | Path,
    *,
    calibration_manifest: str | Path,
    seeds: int = 2_000,
    seed_offset: int = CONFIRMATION_SEED_OFFSET,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Confirm the locked specialist-profile contrast on fresh streams."""
    if seeds < 100:
        raise ValueError("confirmation requires at least 100 independent streams per cell")
    calibration_path = Path(calibration_manifest)
    if not calibration_path.is_file():
        raise FileNotFoundError(calibration_path)
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if calibration.get("status") != "passed" or not calibration.get("all_cells_pass"):
        raise ValueError("independent calibration manifest has not passed")
    calibration_end = int(
        calibration.get(
            "seed_block_end",
            _seed_block_end(
                int(calibration["seed_offset"]),
                36,
                int(calibration["seeds_per_cell"]),
            ),
        )
    )
    confirmation_end = _seed_block_end(seed_offset, 18, seeds)
    if not (confirmation_end < int(calibration["seed_offset"]) or seed_offset > calibration_end):
        raise ValueError("confirmation seed block must be disjoint from calibration")

    rows = []
    for prevalence_index, prevalence in enumerate(PREVALENCES):
        for error_index, error in enumerate(PROXY_ERRORS):
            for budget_index, budget in enumerate(BUDGET_RATES):
                cell = (prevalence_index * len(PROXY_ERRORS) + error_index) * len(
                    BUDGET_RATES
                ) + budget_index
                cell_seed = seed_offset + cell * 1_000_019
                frame = simulate_block(
                    profile="specialists",
                    seeds=seeds,
                    seed=cell_seed,
                    prevalence=prevalence,
                    proxy_error=error,
                    budget_rate=budget,
                    device=device,
                )
                rows.extend(frame.to_dict(orient="records"))
    detail = pd.DataFrame(rows)
    primary = _hierarchical_paired_bootstrap(detail)
    caps_ok = bool(detail.hard_cap_respected.all())
    passed = bool(
        caps_ok
        and (primary.simultaneous_ci_low > PRIMARY_MARGIN).all()
        and calibration.get("status") == "passed"
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    detail.to_parquet(output / "confirmation_streams.parquet", index=False)
    primary.to_csv(output / "primary_contrasts.csv", index=False)
    profiles = detail.groupby(
        ["prevalence", "proxy_error", "budget_rate", "method"], as_index=False
    ).agg(
        promotion_rate=("promoted", "mean"),
        mean_expected_utility=("expected_deployment_utility", "mean"),
        mean_realized_utility=("realized_deployment_utility", "mean"),
        mean_labels=("labels_queried", "mean"),
        harmful_deployment_rate=("harmful_deployment", "mean"),
        cap_respected=("hard_cap_respected", "all"),
    )
    profiles.to_csv(output / "profile_summary.csv", index=False)
    manifest = {
        "experiment": "nested_candidate_context_alpha_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "not_retained",
        "seed_offset": seed_offset,
        "seed_block_end": confirmation_end,
        "seeds_per_cell": seeds,
        "profile": "specialists",
        "prevalences": PREVALENCES,
        "proxy_errors": PROXY_ERRORS,
        "budget_rates": BUDGET_RATES,
        "methods": METHODS,
        "candidate_count": CANDIDATES,
        "primary_minimum_gain": PRIMARY_MARGIN,
        "primary_contrasts_passed": bool((primary.simultaneous_ci_low > PRIMARY_MARGIN).all()),
        "all_caps_respected": caps_ok,
        "calibration_manifest": calibration_path.as_posix(),
        "calibration_manifest_sha256": _sha256(calibration_path),
        "environment": environment(),
        "limitation": "Confirmation is limited to the frozen gate-level specialist simulator. It does not establish an end-to-end classifier benefit, validity under adaptive/delayed feedback, application utility, or algorithmic novelty.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["artifacts_sha256"] = {
        name: _sha256(output / name)
        for name in ("confirmation_streams.parquet", "primary_contrasts.csv", "profile_summary.csv")
    }
    manifest["source_sha256"] = _sha256(Path(__file__))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return detail, profiles, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("calibrate", "develop", "confirm"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=None)
    parser.add_argument("--seed-offset", type=int, default=None)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--calibration-manifest", type=Path, default=None)
    args = parser.parse_args()
    if args.mode == "calibrate":
        _, summary, manifest = run_calibration(
            args.output,
            seeds=args.seeds or 2_000,
            seed_offset=args.seed_offset or 2_124_102_026,
            device=args.device,
        )
    else:
        if args.mode == "develop":
            _, summary, manifest = run_development_grid(
                args.output,
                seeds=args.seeds or 200,
                seed_offset=args.seed_offset or DEVELOPMENT_SEED_OFFSET,
                device=args.device,
            )
        else:
            if args.calibration_manifest is None:
                parser.error("confirm mode requires --calibration-manifest")
            _, summary, manifest = run_confirmation(
                args.output,
                calibration_manifest=args.calibration_manifest,
                seeds=args.seeds or 2_000,
                seed_offset=args.seed_offset or CONFIRMATION_SEED_OFFSET,
                device=args.device,
            )
    if args.mode == "calibrate" and manifest["status"] != "passed":
        raise SystemExit("calibration failed one or more registered gates")
    print(json.dumps({"manifest": manifest, "summary_rows": len(summary)}, indent=2))


if __name__ == "__main__":
    main()
