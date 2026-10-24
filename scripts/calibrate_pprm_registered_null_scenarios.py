"""Calibrate PPRM block-mixture alarms on registered population-null generators."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr
from sklearn.linear_model import Ridge

from shiftlab.data.gpu.environment import environment
from shiftlab.decision_harm_experiment import (
    POPULATION_NULL_CONTROLS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from shiftlab.dive.experiment import _binary_cost, _material_harm_onset, _synthetic_label_costs
from shiftlab.dive.hard_budget import (
    HardBudgetConfig,
    _one_pprm_block_method,
)
from shiftlab.dive.proxy import DecisionLossProxy

NULL_SCENARIOS = ("stationary", "benign_nuisance")
CHECKPOINT_COLUMNS = (
    "scenario",
    "seed",
    "population_null_control",
    "pprm_mix_w0p1_false_escalation",
    "single_e_false_escalation",
    "processed_events",
    "monitor_fraction_processed",
    "labels_queried",
    "realized_label_spend",
    "hard_budget",
    "budget_respected",
    "pprm_reliance_mean",
    "sample_mean_expected_harm",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prediction_only_proxy(
    *, seed: int, clip: float, x_train: np.ndarray, z_train: np.ndarray
) -> DecisionLossProxy:
    """Fit the exact Ridge predictor used by the proxy, omitting its unused variance forest."""
    proxy = DecisionLossProxy(clip=clip, seed=seed)
    train_x = proxy._features(x_train)
    train_z = proxy._targets(z_train, len(train_x))
    proxy.model = Ridge(alpha=proxy.alpha).fit(train_x, train_z)
    return proxy


def _registered_null_run(
    *, scenario, seed: int, config: HardBudgetConfig, resolved_device: str
) -> dict[str, object]:
    base = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        window=64,
        stride=32,
        alpha=config.alpha,
        eprocess_epsilon=config.harm_margin,
        seed_offset=seed,
        change_fraction=config.change_fraction,
        device=resolved_device,
    )
    _, frame, oracle, timing = _generate(scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    label_costs = _synthetic_label_costs(x)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    reference = _source_action(x, scenario)
    paired_difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered_difference = paired_difference - config.harm_margin
    probability = oracle.probability_positive.to_numpy(dtype=float)
    current_expected = np.where(deployed == 1, fp * (1 - probability), fn * probability)
    reference_expected = np.where(reference == 1, fp * (1 - probability), fn * probability)
    expected_difference = current_expected - reference_expected

    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    proxy_template = _prediction_only_proxy(
        seed=seed,
        clip=max(fn, fp) + config.harm_margin,
        x_train=x[:train_end],
        z_train=centered_difference[:train_end],
    )
    sample_path_onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    harm_onset = statistical_harm_onset(scenario.name, sample_path_onset)
    row = _one_pprm_block_method(
        seed=seed,
        scenario=scenario,
        config=config,
        x=x,
        centered_cost_difference=centered_difference,
        expected_cost_difference=expected_difference,
        label_costs=label_costs,
        proxy_template=proxy_template,
        monitor_start=monitor_start,
        harm_onset=harm_onset,
        sample_path_material_harm=sample_path_onset is not None,
        sample_path_harm_onset=sample_path_onset,
        common_uniforms=np.random.default_rng(seed + 9_173).random(config.n),
    )
    if row["material_harm"] or not row["population_null_control"]:
        raise ValueError(f"{scenario.name} did not remain a registered population-null control")
    row["sample_mean_expected_harm"] = row["mean_expected_decision_harm"]
    return {column: row[column] for column in CHECKPOINT_COLUMNS}


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    rate = successes / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, float(center - radius))
    upper = 1.0 if successes == trials else min(1.0, float(center + radius))
    return lower, upper


def _vectorized_mixture_crossings(
    estimates: np.ndarray,
    active_masks: np.ndarray,
    *,
    max_reliance: float = 0.1,
    threshold: float = 0.51,
    alpha: float = 0.05,
    cm_eb_weight: float = 0.1,
    device: str = "cuda",
) -> tuple[np.ndarray, np.ndarray]:
    """Batch the production CM-EB and hedged-mixture recursions over streams."""
    import torch

    values = torch.as_tensor(estimates, dtype=torch.float64, device=device)
    active = torch.as_tensor(active_masks, dtype=torch.bool, device=device)
    if values.ndim != 2 or active.shape != values.shape:
        raise ValueError("estimates and active masks must be matching stream-by-block matrices")
    if (
        not torch.isfinite(values).all()
        or torch.any(values < -max_reliance - 1e-12)
        or torch.any(values > 1 + max_reliance + 1e-12)
    ):
        raise ValueError("PPI block estimate lies outside its support")
    stream_count, block_count = values.shape
    lambdas = torch.as_tensor(np.geomspace(1e-4, 0.99, 64), dtype=torch.float64, device=device)
    log_weights = torch.full_like(lambdas, -np.log(len(lambdas)))
    psi = -torch.log1p(-lambdas) - lambdas
    normalized_threshold = (threshold + max_reliance) / (1 + 2 * max_reliance)
    cm_sum = torch.zeros(stream_count, dtype=torch.float64, device=device)
    cm_sse = torch.zeros_like(cm_sum)
    cm_prediction = torch.full_like(cm_sum, 0.5)
    bet_bound = max(threshold + max_reliance, 1 + max_reliance - threshold)
    betting_observations = 0.5 * ((values - threshold) / bet_bound + 1)
    bet_sum = torch.zeros_like(cm_sum)
    bet_sse = torch.zeros_like(cm_sum)
    bet_prediction = torch.full_like(cm_sum, 0.5)
    bet_variance = torch.full_like(cm_sum, 0.25)
    bet_log_wealth = torch.zeros_like(cm_sum)
    times = torch.zeros(stream_count, dtype=torch.float64, device=device)
    threshold_log = -np.log(alpha)
    numerator = 2 * np.log(2 / alpha)
    log_cm_weight = np.log(cm_eb_weight)
    log_bet_weight = np.log1p(-cm_eb_weight)
    mixture_crossed = torch.zeros(stream_count, dtype=torch.bool, device=device)
    cm_crossed = torch.zeros_like(mixture_crossed)

    for block in range(block_count):
        mask = active[:, block]
        if not mask.any():
            continue
        normalized = (values[:, block] + max_reliance) / (1 + 2 * max_reliance)
        cm_sse = torch.where(mask, cm_sse + (normalized - cm_prediction).square(), cm_sse)
        cm_sum = torch.where(mask, cm_sum + normalized, cm_sum)
        times = times + mask.to(torch.float64)
        updated_prediction = cm_sum / times.clamp_min(1)
        cm_prediction = torch.where(mask, updated_prediction, cm_prediction)
        excess = cm_sum - times * normalized_threshold
        cm_log = torch.logsumexp(
            log_weights[None, :] + excess[:, None] * lambdas - cm_sse[:, None] * psi,
            dim=1,
        )

        t = times
        stake = torch.clamp(
            torch.sqrt(numerator / (bet_variance * t * torch.log1p(t).clamp_min(1e-300))),
            max=1.0,
        )
        bet_observation = betting_observations[:, block]
        factor = 1 + stake * (bet_observation - 0.5)
        bet_log_wealth = torch.where(mask, bet_log_wealth + torch.log(factor), bet_log_wealth)
        bet_sum = torch.where(mask, bet_sum + bet_observation, bet_sum)
        new_prediction = (0.5 + bet_sum) / (t + 1)
        residual = bet_observation - new_prediction
        bet_sse = torch.where(mask, bet_sse + residual.square(), bet_sse)
        bet_prediction = torch.where(mask, new_prediction, bet_prediction)
        new_variance = (0.25 + bet_sse) / (t + 1)
        bet_variance = torch.where(mask, new_variance, bet_variance)

        cm_crossed |= mask & (cm_log >= threshold_log)
        mixture_log = torch.logaddexp(
            cm_log + log_cm_weight,
            bet_log_wealth + log_bet_weight,
        )
        mixture_crossed |= mask & (mixture_log >= threshold_log)

    return cm_crossed.cpu().numpy(), mixture_crossed.cpu().numpy()


def _registered_null_batch(
    *,
    scenario_name: str,
    stream_start: int,
    batch_size: int,
    config: HardBudgetConfig,
    device: str,
) -> pd.DataFrame:
    """Generate and monitor independent null streams as one CUDA tensor batch."""
    import torch

    device_obj = torch.device(device)
    count = min(batch_size, config.seeds - stream_start)
    n, d = config.n, config.d
    scenario_salt = 0 if scenario_name == "stationary" else 100_000_000
    stream_seed = config.seed_offset + stream_start
    data_generator = torch.Generator(device=device_obj).manual_seed(
        stream_seed + scenario_salt + 1_000_000_007
    )
    latent = torch.randn(
        (count, n, d + 1), dtype=torch.float64, device=device_obj, generator=data_generator
    )
    x = latent[:, :, :d].clone()
    noise = latent[:, :, d]
    if scenario_name == "benign_nuisance":
        x[:, n // 2 :, 2:] += 3.0
    mean = x[:, :, 0] - 0.9 * x[:, :, 1]
    target = mean + 0.3 * noise
    label = target > 0
    probability = 0.5 * (1 + torch.erf(mean / (0.3 * np.sqrt(2))))
    source_action = probability >= (1 / 6)
    deployed_action = mean >= 0
    fp, fn, margin = 1.0, 5.0, config.harm_margin
    observed_cost = torch.where(deployed_action, fp * (~label), fn * label).to(torch.float64)
    observed_reference = torch.where(source_action, fp * (~label), fn * label).to(torch.float64)
    centered_difference = (observed_cost - observed_reference) - margin
    expected_cost = torch.where(deployed_action, fp * (1 - probability), fn * probability)
    expected_reference = torch.where(source_action, fp * (1 - probability), fn * probability)
    expected_difference = expected_cost - expected_reference
    cost_bound = max(fn, fp)
    normalized_truth = (observed_cost - observed_reference + cost_bound) / (2 * cost_bound)

    train_end, monitor_start = max(100, int(n * 0.125)), max(800, int(n * 0.25))
    x_train = x[:, :train_end]
    x_mean = x_train.mean(dim=1, keepdim=True)
    z_train = centered_difference[:, :train_end]
    z_mean = z_train.mean(dim=1, keepdim=True)
    centered_x = x_train - x_mean
    centered_z = z_train - z_mean
    gram = centered_x.transpose(1, 2) @ centered_x
    cross = centered_x.transpose(1, 2) @ centered_z.unsqueeze(2)
    identity = torch.eye(d, dtype=torch.float64, device=device_obj).expand(count, -1, -1)
    coefficient = torch.linalg.solve(gram + identity, cross).squeeze(2)
    predictions = torch.sum((x[:, monitor_start:] - x_mean) * coefficient[:, None, :], dim=2)
    predictions = torch.clamp(predictions, min=-cost_bound - margin, max=cost_bound + margin)
    predictions = torch.clamp(predictions + margin, min=-cost_bound, max=cost_bound)
    normalized_proxy = (predictions + cost_bound) / (2 * cost_bound)

    tariff_covariate = torch.clamp(x[:, :, -1], min=-30, max=30)
    label_costs = 0.5 + 2.0 / (1 + torch.exp(-tariff_covariate))
    validation_start = max(100, int(n * 0.125))
    budget = config.budget_rate * label_costs[:, validation_start:monitor_start].mean(dim=1)
    budget = budget * (n - monitor_start)
    remaining = budget.clone()
    block_size, labels_per_block = config.pprm_block_size, config.pprm_labels_per_block
    event_count = n - monitor_start
    block_count = event_count // block_size
    query_generator = torch.Generator(device=device_obj).manual_seed(
        stream_seed + scenario_salt + 2_000_000_019
    )
    query_uniforms = torch.rand(
        (count, block_count, block_size),
        dtype=torch.float64,
        device=device_obj,
        generator=query_generator,
    )
    selected = torch.topk(query_uniforms, labels_per_block, dim=2, largest=False).indices
    proxy_blocks = normalized_proxy.reshape(count, block_count, block_size)
    truth_blocks = normalized_truth[:, monitor_start:].reshape(count, block_count, block_size)
    cost_blocks = label_costs[:, monitor_start:].reshape(count, block_count, block_size)
    all_blocks_proxy_sum = proxy_blocks.sum(dim=2)

    active = torch.zeros((count, block_count), dtype=torch.bool, device=device_obj)
    estimates = torch.zeros((count, block_count), dtype=torch.float64, device=device_obj)
    processed_blocks = torch.zeros(count, dtype=torch.int64, device=device_obj)
    labels_queried = torch.zeros_like(processed_blocks)
    realized_spend = torch.zeros(count, dtype=torch.float64, device=device_obj)
    eta = torch.full((count,), config.pprm_initial_reliance, dtype=torch.float64, device=device_obj)
    labeled_count = torch.zeros_like(processed_blocks)
    unlabeled_count = torch.zeros_like(processed_blocks)
    sum_labeled_z = torch.zeros_like(eta)
    sum_labeled_proxy = torch.zeros_like(eta)
    sum_labeled_zproxy = torch.zeros_like(eta)
    sum_unlabeled_proxy = torch.zeros_like(eta)
    sum_unlabeled_proxy_sq = torch.zeros_like(eta)
    eta_sum = torch.zeros_like(eta)
    active_masks = np.zeros((count, block_count), dtype=bool)

    for block in range(block_count):
        can_query = remaining + 1e-12 >= labels_per_block * config.max_label_cost
        if not can_query.any():
            break
        active[:, block] = can_query
        active_masks[:, block] = can_query.cpu().numpy()
        block_indices = selected[:, block, :]
        labeled_z = torch.gather(truth_blocks[:, block, :], 1, block_indices)
        labeled_proxy = torch.gather(proxy_blocks[:, block, :], 1, block_indices)
        labeled_spend = torch.gather(cost_blocks[:, block, :], 1, block_indices).sum(dim=1)
        if torch.any(can_query & (labeled_spend > remaining + 1e-12)):
            raise RuntimeError("fixed-size block query exceeded its hard dollar reserve")
        unlabeled_proxy_sum = all_blocks_proxy_sum[:, block] - labeled_proxy.sum(dim=1)
        estimate = labeled_z.mean(dim=1) + eta * (
            unlabeled_proxy_sum / (block_size - labels_per_block) - labeled_proxy.mean(dim=1)
        )
        estimates[:, block] = estimate
        eta_sum += torch.where(can_query, eta, 0.0)
        remaining = torch.where(can_query, remaining - labeled_spend, remaining)
        realized_spend = torch.where(can_query, realized_spend + labeled_spend, realized_spend)
        labels_queried = torch.where(can_query, labels_queried + labels_per_block, labels_queried)
        processed_blocks = torch.where(can_query, processed_blocks + 1, processed_blocks)

        labeled_count = torch.where(can_query, labeled_count + labels_per_block, labeled_count)
        unlabeled_count = torch.where(
            can_query, unlabeled_count + block_size - labels_per_block, unlabeled_count
        )
        sum_labeled_z += torch.where(can_query, labeled_z.sum(dim=1), 0.0)
        sum_labeled_proxy += torch.where(can_query, labeled_proxy.sum(dim=1), 0.0)
        sum_labeled_zproxy += torch.where(can_query, (labeled_z * labeled_proxy).sum(dim=1), 0.0)
        unlabeled_mask = torch.ones((count, block_size), dtype=torch.bool, device=device_obj)
        unlabeled_mask.scatter_(1, block_indices, False)
        unlabeled_values = torch.where(unlabeled_mask, proxy_blocks[:, block, :], 0.0)
        sum_unlabeled_proxy += torch.where(can_query, unlabeled_values.sum(dim=1), 0.0)
        sum_unlabeled_proxy_sq += torch.where(can_query, unlabeled_values.square().sum(dim=1), 0.0)
        variance = (
            sum_unlabeled_proxy_sq - sum_unlabeled_proxy.square() / unlabeled_count.clamp_min(1)
        ) / (unlabeled_count - 1).clamp_min(1)
        covariance = (
            sum_labeled_zproxy - sum_labeled_z * sum_labeled_proxy / labeled_count.clamp_min(1)
        ) / (labeled_count - 1).clamp_min(1)
        ratio = labeled_count.to(torch.float64) / unlabeled_count.clamp_min(1)
        candidate_eta = covariance / (
            (1 + ratio) * variance.clamp_min(torch.finfo(torch.float64).tiny)
        )
        candidate_eta = torch.clamp(candidate_eta, min=0.0, max=config.pprm_max_reliance)
        valid = (labeled_count >= 2) & (unlabeled_count >= 2) & (variance > np.finfo(float).eps)
        updated_eta = torch.where(valid, candidate_eta, config.pprm_initial_reliance)
        eta = torch.where(can_query, updated_eta, eta)

    cm_crossed, mixture_crossed = _vectorized_mixture_crossings(
        estimates.cpu().numpy(),
        active_masks,
        max_reliance=config.pprm_max_reliance,
        threshold=(config.harm_margin + cost_bound) / (2 * cost_bound),
        alpha=config.alpha,
        cm_eb_weight=0.1,
        device=device,
    )
    stream_ids = np.arange(stream_seed, stream_seed + count, dtype=np.int64)
    return pd.DataFrame(
        {
            "scenario": scenario_name,
            "seed": stream_ids,
            "population_null_control": True,
            "pprm_mix_w0p1_false_escalation": mixture_crossed,
            "single_e_false_escalation": cm_crossed,
            "processed_events": processed_blocks.cpu().numpy() * block_size,
            "monitor_fraction_processed": processed_blocks.cpu().numpy() * block_size / event_count,
            "labels_queried": labels_queried.cpu().numpy(),
            "realized_label_spend": realized_spend.cpu().numpy(),
            "hard_budget": budget.cpu().numpy(),
            "budget_respected": (realized_spend <= budget + 1e-9).cpu().numpy(),
            "pprm_reliance_mean": (eta_sum / processed_blocks.clamp_min(1)).cpu().numpy(),
            "sample_mean_expected_harm": expected_difference[:, monitor_start:]
            .mean(dim=1)
            .cpu()
            .numpy(),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/pprm_registered_null_calibration_2000_v1")
    )
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=20374000)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--checkpoint-every", type=int, default=1)
    args = parser.parse_args()
    if args.replicates < 1 or args.checkpoint_every < 1 or args.batch_size < 1:
        parser.error("replicates, batch-size and checkpoint-every must be positive")
    if not POPULATION_NULL_CONTROLS.issuperset(NULL_SCENARIOS):
        raise RuntimeError("null scenario list disagrees with evaluator population-null registry")
    resolved_device = args.device
    if resolved_device == "cuda":
        import torch

        if not torch.cuda.is_available():
            resolved_device = "cpu"
    config = HardBudgetConfig(
        n=6400,
        d=16,
        seeds=args.replicates,
        seed_offset=args.seed_offset,
        alpha=0.05,
        harm_margin=0.10,
        budget_rate=0.20,
        q_min=0.10,
        q_max=0.80,
        common_eprocess_bound=True,
        pprm_block_size=20,
        pprm_labels_per_block=4,
        pprm_max_reliance=0.10,
        pprm_initial_reliance=0.10,
        device=resolved_device,
        scenario_subset=NULL_SCENARIOS,
        method_subset=("pprm_block_adaptive",),
    )
    config.validate()
    output = args.output
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_config = {
        "experiment": "pprm_block_mixture_registered_population_null_calibration",
        "classification": "independent_registered_scenario_null_calibration",
        "configuration": {
            "replicates_per_scenario": args.replicates,
            "batch_size": args.batch_size,
            "seed_offset": args.seed_offset,
            "seed_range": [args.seed_offset, args.seed_offset + args.replicates - 1],
            "null_scenarios": list(NULL_SCENARIOS),
            "n": config.n,
            "d": config.d,
            "alpha": config.alpha,
            "harm_margin": config.harm_margin,
            "budget_rate": config.budget_rate,
            "block_size": config.pprm_block_size,
            "labels_per_block": config.pprm_labels_per_block,
            "max_reliance": config.pprm_max_reliance,
            "mixture_cm_eb_weight": 0.1,
            "requested_device": args.device,
            "resolved_device": resolved_device,
            "randomness": "independent CUDA/CPU Torch generator batches for DGP noise and query randomization; batch size is part of the frozen config",
            "monitor": "GPU-vectorized algebraic recursion parity-tested against production PPIBlockMixtureEProcess",
            "proxy_prediction_optimization": "batched Ridge normal equations, algebraically equivalent to DecisionLossProxy.fit; skips only the unused residual-variance forest",
        },
    }
    config_path = output / "run_config.json"
    if config_path.exists() and json.loads(config_path.read_text(encoding="utf-8")) != run_config:
        raise ValueError("existing calibration output has a different frozen configuration")
    config_path.write_text(json.dumps(run_config, indent=2) + "\n", encoding="utf-8")

    all_frames = []
    for scenario_name in NULL_SCENARIOS:
        path = metrics_dir / f"{scenario_name}.csv"
        completed: set[int] = set()
        if path.exists():
            previous = pd.read_csv(path)
            if tuple(previous.columns) != CHECKPOINT_COLUMNS:
                raise ValueError(f"checkpoint schema mismatch: {path}")
            if previous.seed.duplicated().any():
                raise ValueError(f"duplicate seed in checkpoint: {path}")
            if not previous.seed.between(
                args.seed_offset, args.seed_offset + args.replicates - 1
            ).all():
                raise ValueError(f"checkpoint contains seeds outside the declared range: {path}")
            if not previous.population_null_control.astype(bool).all():
                raise ValueError(f"checkpoint contains a non-null scenario: {path}")
            completed = set(previous.seed.astype(int))
        batch_starts = range(0, args.replicates, args.batch_size)
        for batch_index, stream_start in enumerate(batch_starts, start=1):
            expected_batch_seeds = set(
                range(
                    args.seed_offset + stream_start,
                    min(
                        args.seed_offset + stream_start + args.batch_size,
                        args.seed_offset + args.replicates,
                    ),
                )
            )
            if expected_batch_seeds.issubset(completed):
                continue
            batch = _registered_null_batch(
                scenario_name=scenario_name,
                stream_start=stream_start,
                batch_size=args.batch_size,
                config=config,
                device=resolved_device,
            )
            batch = batch.loc[~batch.seed.isin(completed)]
            if not batch.empty:
                batch.loc[:, CHECKPOINT_COLUMNS].to_csv(
                    path,
                    mode="a" if path.exists() else "w",
                    header=not path.exists(),
                    index=False,
                )
                completed.update(batch.seed.astype(int))
            if batch_index % args.checkpoint_every == 0 or batch_index == len(batch_starts):
                print(
                    f"scenario={scenario_name} completed={len(completed)}/{args.replicates} device={resolved_device}",
                    flush=True,
                )
        final_frame = pd.read_csv(path)
        expected_seeds = set(range(args.seed_offset, args.seed_offset + args.replicates))
        if set(final_frame.seed.astype(int)) != expected_seeds:
            raise RuntimeError(f"incomplete calibration cell: {scenario_name}")
        all_frames.append(final_frame)

    metrics = pd.concat(all_frames, ignore_index=True)
    summary_rows = []
    for scenario_name, group in metrics.groupby("scenario", sort=False):
        for monitor, column in (
            ("fixed_mixture_w0p1", "pprm_mix_w0p1_false_escalation"),
            ("block_cm_eb", "single_e_false_escalation"),
        ):
            count = int(group[column].astype(bool).sum())
            low, high = _wilson(count, len(group))
            summary_rows.append(
                {
                    "scenario": scenario_name,
                    "monitor": monitor,
                    "streams": len(group),
                    "false_escalations": count,
                    "rate": count / len(group),
                    "wilson_95_low": low,
                    "wilson_95_high": high,
                }
            )
    summary = pd.DataFrame(summary_rows)
    summary_path = metrics_dir / "null_calibration_summary.csv"
    summary.to_csv(summary_path, index=False)
    report = [
        "# Registered scenario population-null calibration",
        "",
        f"This experiment evaluated {args.replicates} independent 6,400-event streams per registered population-null scenario, using a batched implementation of the PPRM block estimator and e-process recursion, block size 20, four queried labels per block, a 20% hard label-dollar budget, reliance cap 0.1, and a fixed 10% CM-EB / 90% positive-betting e-process mixture. The monitor recursion is checked against the scalar production class; the batched Ridge normal equations match the prediction component of DecisionLossProxy. CUDA was requested and resolved to {resolved_device}.",
        "",
        "| Scenario | Monitor | False escalations / streams | Rate | Wilson 95% interval |",
        "|---|---|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        report.append(
            f"| {row.scenario} | {row.monitor} | {row.false_escalations} / {row.streams} | {row.rate:.4f} | [{row.wilson_95_low:.4f}, {row.wilson_95_high:.4f}] |"
        )
    report.extend(
        [
            "",
            "These Monte Carlo rates test implementation behavior for the named synthetic generators. They do not prove the e-process assumptions, establish validity for arbitrary serial dependence or delayed feedback, or generalize to other distributions. Residual-variance shift is excluded: the evaluator marks it as harmful rather than a population null.",
            "",
        ]
    )
    report_path = reports_dir / "registered_null_calibration.md"
    report_path.write_text("\n".join(report), encoding="utf-8")
    source_paths = sorted(Path("src/shiftlab").rglob("*.py"))
    manifest = {
        **run_config,
        "environment": environment(),
        "complete": True,
        "rows": len(metrics),
        "sha256": {
            "script": _sha256(Path(__file__)),
            "run_config": _sha256(config_path),
            "source_files": {str(path): _sha256(path) for path in source_paths},
            "outputs": {
                str(path.relative_to(output)): _sha256(path)
                for path in (
                    metrics_dir / "stationary.csv",
                    metrics_dir / "benign_nuisance.csv",
                    summary_path,
                    report_path,
                )
            },
        },
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
