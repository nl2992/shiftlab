"""Reproducible, evaluator-separated benchmark for distribution shift and decision harm."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.special import ndtr

from .data.decision_tasks import binary_action, binary_risk
from .data.schemas import SyntheticConfig
from .data.streaming import (
    DecisionFeedback,
    DecisionRequest,
    PolicyDecision,
    replay_decision_stream,
)
from .data.synthetic.generators import generate_chunks, schedule
from .monitoring import (
    HoeffdingExcessEProcess,
    conformal_upper_threshold,
    one_sided_cusum,
    rbf_gamma,
    rbf_mmd_squared,
)


@dataclass(frozen=True)
class Scenario:
    name: str
    dgp: str
    pattern: str = "abrupt"
    severity: float = 1.0
    fn_cost: float = 5.0
    fp_cost: float = 1.0
    harmful_adaptation: bool = False
    description: str = ""


SCENARIOS = (
    Scenario("stationary", "iid_regression", description="No shift; false-alarm control."),
    Scenario(
        "benign_nuisance",
        "nuisance_shift",
        severity=3.0,
        description="Large shift in 14 nuisance coordinates; signal and conditional law fixed.",
    ),
    Scenario(
        "boundary_local_harm",
        "boundary_local_harm",
        severity=1.5,
        description="Adverse conditional-mean increase localized near the source decision boundary.",
    ),
    Scenario(
        "residual_variance",
        "target_variance",
        severity=1.5,
        description="Residual scale grows; the frozen source-cost challenger and classifier diverge near the boundary.",
    ),
    Scenario(
        "recurring_regimes",
        "boundary_local_harm",
        pattern="recurring",
        severity=1.5,
        description="Alternating source and adverse boundary-local regimes, four regimes total.",
    ),
    Scenario(
        "harmful_adaptation",
        "harmful_adaptation",
        severity=0.0,
        harmful_adaptation=True,
        description="Stationary outcomes; policy intervention sets every action to positive, increasing false-positive cost.",
    ),
)


@dataclass(frozen=True)
class ExperimentConfig:
    n: int = 3200
    d: int = 16
    evaluation_seeds: int = 30
    calibration_seeds: int = 60
    calibration_start: int = 800
    window: int = 64
    stride: int = 32
    alpha: float = 0.05
    eprocess_epsilon: float = 0.10
    seed_offset: int = 20261022
    device: str = "cpu"


def _generate(scenario: Scenario, seed: int, config: ExperimentConfig):
    cfg = SyntheticConfig(
        n=config.n,
        d=config.d,
        seed=seed,
        scenario=scenario.dgp,
        pattern=scenario.pattern,
        regimes=4 if scenario.pattern == "recurring" else 2,
        severity=scenario.severity,
        noise=0.3,
        train_fraction=0.15,
        validation_fraction=0.05,
        calibration_fraction=0.05,
        chunk_size=2048,
        device=config.device,
    )
    frames, oracles = zip(*generate_chunks(cfg), strict=True)
    frame, oracle = pd.concat(frames, ignore_index=True), pd.concat(oracles, ignore_index=True)
    if len(frame) != config.n or frame.sample_id.duplicated().any():
        raise RuntimeError("Generator returned malformed synthetic stream")
    if scenario.harmful_adaptation:
        weights = np.zeros(config.n)
        weights[config.n // 2 :] = 1.0
        timing = {"change_times": [config.n // 2], "transition_intervals": []}
    else:
        weights, timing = schedule(cfg)
    oracle = oracle.copy()
    oracle["weight"] = weights
    oracle["true_change_time"] = timing["change_times"][0] if timing["change_times"] else np.nan
    return cfg, frame, oracle, timing


def _source_action(features: np.ndarray, scenario: Scenario):
    score = features[:, 0] - 0.9 * features[:, 1]
    source_probability = ndtr(score / 0.3)
    return binary_action(source_probability, scenario.fn_cost, scenario.fp_cost).astype(int)


def _observed_run(scenario: Scenario, seed: int, cfg: ExperimentConfig, calibration: dict):
    _, frame, oracle, timing = _generate(scenario, seed, cfg)
    x = np.stack(frame.features.to_numpy())
    y = frame.target.to_numpy(dtype=float)
    p_truth = oracle.probability_positive.to_numpy(dtype=float)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    reference = _source_action(x, scenario)
    source_probability = ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3)
    # Deployed classifier uses a fixed 0.5 threshold; its explicit challenger is the
    # source cost-minimizing rule. This yields a nontrivial paired decision contrast.
    deployed = (source_probability >= 0.5).astype(int)
    intervention = cfg.n // 2
    if scenario.harmful_adaptation:
        deployed[intervention:] = 1

    # The learner sees only current features and delayed labels. DGP probabilities, costs and
    # schedules are kept in the evaluator below and are never passed into the replay API.
    requests, decisions, feedback = [], [], []
    for i in range(cfg.n):
        requests.append(
            DecisionRequest(
                sample_id=str(frame.sample_id.iloc[i]),
                event_time=i,
                feature_available_time=i,
                prediction_time=i,
                features=tuple(float(v) for v in x[i]),
                entity_id="synthetic-stream",
                domain_id="synthetic",
                decision_context=f"fn={fn:g};fp={fp:g}",
                policy_version=(
                    "intervened-policy-v1"
                    if scenario.harmful_adaptation and i >= intervention
                    else "deployed-classifier-v1"
                ),
                reference_policy_version="source-cost-optimal-policy-v1",
                decision_cost_version=f"fn-{fn:g}-fp-{fp:g}-v1",
            )
        )
        decisions.append(
            PolicyDecision(
                str(frame.sample_id.iloc[i]), i, int(deployed[i]), int(reference[i]), True, 1.0
            )
        )
        feedback.append(DecisionFeedback(str(frame.sample_id.iloc[i]), i, i, float(y[i])))
    # Consume the same stream contract available to online code; feedback records arrive only
    # after decisions. Build learner metrics from the emitted sequence.
    learner_rows = []
    for event in replay_decision_stream(requests, decisions, feedback):
        if isinstance(event, DecisionRequest):
            learner_rows.append(
                {
                    "sample_id": event.sample_id,
                    "time": event.prediction_time,
                    "features": event.features,
                }
            )
        elif isinstance(event, DecisionFeedback):
            learner_rows[-1]["target"] = event.target
    learner = pd.DataFrame(learner_rows)
    if learner.target.isna().any():
        raise RuntimeError("Full-feedback benchmark unexpectedly withheld a label")

    action_risk = binary_risk(deployed, p_truth, fn, fp)
    reference_risk = binary_risk(reference, p_truth, fn, fp)
    oracle_risk = np.minimum(
        binary_risk(np.zeros(cfg.n, dtype=int), p_truth, fn, fp),
        binary_risk(np.ones(cfg.n, dtype=int), p_truth, fn, fp),
    )
    observed_cost = np.where(deployed == 1, fp * (y <= 0), fn * (y > 0)).astype(float)
    reference_cost = np.where(reference == 1, fp * (y <= 0), fn * (y > 0)).astype(float)
    paired_observed = observed_cost - reference_cost
    prediction_loss = (y - (x[:, 0] - 0.9 * x[:, 1])) ** 2
    eval_start = cfg.calibration_start
    times = np.arange(eval_start, cfg.n)
    features_reference = calibration["features"]
    gamma = calibration["gamma"]
    mmd_scores, mse_cusum, harm_cusum, e_logs = [], [], [], []
    eprocess = HoeffdingExcessEProcess(
        epsilon=cfg.eprocess_epsilon,
        alpha=cfg.alpha,
        lower=-max(fn, fp),
        upper=max(fn, fp),
    )
    windows = []
    for end in range(eval_start + cfg.window, cfg.n + 1, cfg.stride):
        start = end - cfg.window
        mmd = rbf_mmd_squared(features_reference, x[start:end], gamma)
        # Baseline MSE moments come only from independent stationary calibration streams.
        mvals = prediction_loss[start:end]
        m_cusum = float(
            one_sided_cusum(
                mvals,
                baseline_mean=calibration["mse_mean"],
                baseline_scale=calibration["mse_scale"],
                slack=0.15,
            ).max(initial=0)
        )
        hvals = paired_observed[start:end]
        h_cusum = float(
            one_sided_cusum(
                hvals,
                baseline_mean=calibration["harm_mean"],
                baseline_scale=calibration["harm_scale"],
                slack=0.05,
            ).max(initial=0)
        )
        windows.append((end - 1, mmd, m_cusum, h_cusum))
    for index in times:
        e_logs.append(eprocess.update(float(paired_observed[index])))
    for end_time, mmd, m_cusum, h_cusum in windows:
        mmd_scores.append((end_time, mmd))
        mse_cusum.append((end_time, m_cusum))
        harm_cusum.append((end_time, h_cusum))
    threshold = calibration["thresholds"]
    alarms = {
        "mmd": next((t for t, v in mmd_scores if v > threshold["mmd"]), None),
        "predictive_cusum": next(
            (t for t, v in mse_cusum if v > threshold["predictive_cusum"]), None
        ),
        "paired_cost_cusum": next(
            (t for t, v in harm_cusum if v > threshold["paired_cost_cusum"]), None
        ),
        "paired_cost_eprocess": next(
            (t for t, v in zip(times, e_logs, strict=True) if v >= np.log(1 / cfg.alpha)), None
        ),
    }
    harm_start = (
        timing["change_times"][0]
        if timing["change_times"]
        else (intervention if scenario.harmful_adaptation else None)
    )
    harm_start = max(eval_start, harm_start) if harm_start is not None else None
    expected_contrast = action_risk - reference_risk
    harm_truth = float(np.mean(expected_contrast[eval_start:]))
    harm_tolerance = cfg.eprocess_epsilon
    onset = None
    if harm_start is not None:
        change_times = [int(value) for value in timing["change_times"] if int(value) >= eval_start]
        if scenario.harmful_adaptation:
            change_times = [intervention]
        for change_index, candidate_onset in enumerate(change_times):
            next_change = (
                change_times[change_index + 1] if change_index + 1 < len(change_times) else cfg.n
            )
            phase_harm = float(np.mean(expected_contrast[candidate_onset:next_change]))
            if next_change > candidate_onset and phase_harm > harm_tolerance:
                onset = max(eval_start, candidate_onset)
                break
    feature_onset = cfg.n // 2 if scenario.name == "benign_nuisance" else None
    mmd_alarm = alarms["mmd"]
    false_distribution_alarm = bool(
        mmd_alarm is not None and (feature_onset is None or mmd_alarm < feature_onset)
    )
    feature_detected = bool(
        mmd_alarm is not None and feature_onset is not None and mmd_alarm >= feature_onset
    )
    feature_delay = mmd_alarm - feature_onset if feature_detected else np.nan
    alarm_rows = []
    for monitor, alarm_time in alarms.items():
        is_harm_monitor = monitor != "mmd"
        false_alarm = (
            bool(alarm_time is not None and (onset is None or alarm_time < onset))
            if is_harm_monitor
            else False
        )
        delay = (
            max(0, alarm_time - onset)
            if alarm_time is not None and onset is not None and alarm_time >= onset
            else np.nan
        )
        detected = bool(alarm_time is not None and onset is not None and alarm_time >= onset)
        alarm_rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "monitor": monitor,
                "alarm_time": alarm_time,
                "harm_onset": onset,
                "false_harm_escalation": false_alarm,
                "harm_detected": detected,
                "detection_delay": delay,
                "feature_change_time": feature_onset,
                "false_distribution_alarm": false_distribution_alarm,
                "feature_shift_detected": feature_detected,
                "feature_detection_delay": feature_delay,
            }
        )

    summary = {
        "scenario": scenario.name,
        "seed": seed,
        "n": cfg.n - eval_start,
        "distribution_discrepancy_mmd_mean": float(np.mean([v for _, v in mmd_scores])),
        "predictive_loss_change": float(
            np.mean(prediction_loss[eval_start:]) - calibration["mse_mean"]
        ),
        "decision_harm_vs_reference": harm_truth,
        "oracle_expected_cost": float(np.mean(oracle_risk[eval_start:])),
        "deployed_expected_cost": float(np.mean(action_risk[eval_start:])),
        "reference_expected_cost": float(np.mean(reference_risk[eval_start:])),
        "cumulative_regret_vs_oracle": float(
            np.sum(action_risk[eval_start:] - oracle_risk[eval_start:])
        ),
        "cumulative_harm_vs_reference": float(
            np.sum(action_risk[eval_start:] - reference_risk[eval_start:])
        ),
        "true_change_time": harm_start,
        **{f"{name}_alarm_time": value for name, value in alarms.items()},
    }
    trace = []
    mmd_map, pred_map, harm_map = dict(mmd_scores), dict(mse_cusum), dict(harm_cusum)
    for t in sorted(set(mmd_map) | set(pred_map) | set(harm_map)):
        trace.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "time": t,
                "mmd": mmd_map.get(t),
                "predictive_cusum": pred_map.get(t),
                "paired_cost_cusum": harm_map.get(t),
                "threshold_mmd": threshold["mmd"],
                "threshold_predictive_cusum": threshold["predictive_cusum"],
                "threshold_paired_cost_cusum": threshold["paired_cost_cusum"],
            }
        )
    return summary, alarm_rows, trace


def _calibrate(config: ExperimentConfig):
    stationary = next(item for item in SCENARIOS if item.name == "stationary")
    maxima = {"mmd": [], "predictive_cusum": [], "paired_cost_cusum": []}
    feature_pool, mse_pool, harm_pool = [], [], []
    started = time.time()
    reference_replicates = max(2, config.calibration_seeds // 2)
    rank_replicates = config.calibration_seeds - reference_replicates
    if rank_replicates < 1:
        raise ValueError(
            "Need at least three calibration seeds to separate reference fit and rank calibration"
        )
    for replicate in range(reference_replicates):
        seed = config.seed_offset + replicate
        _, frame, _, _ = _generate(stationary, seed, config)
        x = np.stack(frame.features.to_numpy())
        y = frame.target.to_numpy(dtype=float)
        pred = (y - (x[:, 0] - 0.9 * x[:, 1])) ** 2
        source = _source_action(x, stationary)
        deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
        observed_deployed = np.where(deployed == 1, 1.0 * (y <= 0), 5.0 * (y > 0))
        observed_reference = np.where(source == 1, 1.0 * (y <= 0), 5.0 * (y > 0))
        paired = observed_deployed - observed_reference
        feature_pool.append(x[: config.calibration_start])
        mse_pool.extend(pred[: config.calibration_start].tolist())
        harm_pool.extend(paired[: config.calibration_start].tolist())
    all_reference = np.concatenate(feature_pool, axis=0)
    rng = np.random.default_rng(config.seed_offset + 999_991)
    reference = all_reference[rng.choice(len(all_reference), size=config.window, replace=False)]
    gamma = rbf_gamma(reference)
    for replicate in range(reference_replicates, config.calibration_seeds):
        seed = config.seed_offset + replicate
        _, frame, _, _ = _generate(stationary, seed, config)
        x = np.stack(frame.features.to_numpy())
        y = frame.target.to_numpy(dtype=float)
        pred = (y - (x[:, 0] - 0.9 * x[:, 1])) ** 2
        source = _source_action(x, stationary)
        deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
        observed_deployed = np.where(deployed == 1, 1.0 * (y <= 0), 5.0 * (y > 0))
        observed_reference = np.where(source == 1, 1.0 * (y <= 0), 5.0 * (y > 0))
        paired = observed_deployed - observed_reference
        windows = [
            (end - config.window, end)
            for end in range(config.calibration_start + config.window, config.n + 1, config.stride)
        ]
        mmd_vals = [rbf_mmd_squared(reference, x[a:b], gamma) for a, b in windows]
        maxima["mmd"].append(max(mmd_vals, default=0.0))
        mse_max = 0.0
        for start, end in windows:
            scores = one_sided_cusum(
                pred[start:end],
                baseline_mean=float(np.mean(mse_pool)),
                baseline_scale=max(float(np.std(mse_pool)), 1e-8),
                slack=0.15,
            )
            mse_max = max(mse_max, float(scores.max(initial=0)))
        maxima["predictive_cusum"].append(mse_max)
        harm_max = 0.0
        for start, end in windows:
            h_scores = one_sided_cusum(
                paired[start:end],
                baseline_mean=float(np.mean(harm_pool)),
                baseline_scale=max(float(np.std(harm_pool)), 0.05),
                slack=0.05,
            )
            harm_max = max(harm_max, float(h_scores.max(initial=0)))
        maxima["paired_cost_cusum"].append(harm_max)
    mse_mean, mse_scale = float(np.mean(mse_pool)), max(float(np.std(mse_pool)), 1e-8)
    harm_mean, harm_scale = float(np.mean(harm_pool)), max(float(np.std(harm_pool)), 0.05)
    thresholds = {
        key: conformal_upper_threshold(values, config.alpha) for key, values in maxima.items()
    }
    return {
        "features": reference,
        "gamma": gamma,
        "mse_mean": mse_mean,
        "mse_scale": mse_scale,
        "harm_mean": harm_mean,
        "harm_scale": harm_scale,
        "thresholds": thresholds,
        "calibration_null_maxima": maxima,
        "elapsed_seconds": time.time() - started,
    }


def _git_revision():
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _plot(metrics: pd.DataFrame, alarms: pd.DataFrame, traces: pd.DataFrame, output: Path):
    order = [scenario.name for scenario in SCENARIOS]
    labels = [name.replace("_", " ") for name in order]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, column, title in zip(
        axes,
        [
            "distribution_discrepancy_mmd_mean",
            "predictive_loss_change",
            "decision_harm_vs_reference",
        ],
        ["Mean RBF MMD²", "Predictive loss change", "Expected decision harm"],
        strict=True,
    ):
        vals = [metrics.loc[metrics.scenario == key, column].to_numpy() for key in order]
        ax.boxplot(vals, tick_labels=labels, showfliers=False)
        ax.axhline(0, color="black", linewidth=0.7)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "estimands_by_scenario.png", dpi=160)
    plt.close(fig)

    harm_alarms = alarms[alarms.monitor != "mmd"]
    grouped = (
        harm_alarms.groupby(["scenario", "monitor"])
        .agg(
            false_alarm_rate=("false_harm_escalation", "mean"), delay=("detection_delay", "median")
        )
        .reset_index()
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for monitor, group in grouped.groupby("monitor"):
        axes[0].plot(group.scenario, group.false_alarm_rate, marker="o", label=monitor)
        axes[1].plot(group.scenario, group.delay, marker="o", label=monitor)
    for ax, title in zip(
        axes, ["False harm escalation rate", "Median detection delay (rounds)"], strict=True
    ):
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / "alarms_and_delay.png", dpi=160)
    plt.close(fig)

    grouped = (
        metrics.groupby("scenario").cumulative_regret_vs_oracle.agg(["mean", "std"]).reindex(order)
    )
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(labels, grouped["mean"], yerr=grouped["std"], capsize=3)
    ax.set_ylabel("Cumulative expected regret")
    ax.set_title("Regret vs evaluator-known optimal action")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "cumulative_regret.png", dpi=160)
    plt.close(fig)


def run_experiment(config: ExperimentConfig, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    calibration = _calibrate(config)
    metrics_rows, alarm_rows, trace_rows = [], [], []
    for scenario in SCENARIOS:
        for replicate in range(config.evaluation_seeds):
            seed = config.seed_offset + 100_000 + replicate
            summary, alarms, trace = _observed_run(scenario, seed, config, calibration)
            metrics_rows.append(summary)
            alarm_rows.extend(alarms)
            trace_rows.extend(trace)
    metrics, alarms, traces = (
        pd.DataFrame(metrics_rows),
        pd.DataFrame(alarm_rows),
        pd.DataFrame(trace_rows),
    )
    metrics.to_parquet(output / "metrics.parquet", index=False)
    alarms.to_parquet(output / "alarm_metrics.parquet", index=False)
    traces.to_parquet(output / "monitor_trace.parquet", index=False)
    _plot(metrics, alarms, traces, output)
    source_hashes = {}
    for filename in [
        "decision_harm_experiment.py",
        "monitoring.py",
        "data/synthetic/generators.py",
        "data/synthetic/oracle_spec.py",
    ]:
        path = Path(__file__).parent / filename
        source_hashes[str(path.relative_to(Path(__file__).parent))] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    manifest = {
        "experiment": "shiftlab_decision_harm_phase2",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "schema_version": "decision-harm-benchmark-1.0.0",
        "config": asdict(config),
        "evaluation_seed_ids": [
            config.seed_offset + 100_000 + i for i in range(config.evaluation_seeds)
        ],
        "calibration_seed_ids": [config.seed_offset + i for i in range(config.calibration_seeds)],
        "reference_fit_seed_ids": [
            config.seed_offset + i for i in range(max(2, config.calibration_seeds // 2))
        ],
        "rank_calibration_seed_ids": [
            config.seed_offset + i
            for i in range(max(2, config.calibration_seeds // 2), config.calibration_seeds)
        ],
        "scenario_definitions": [asdict(scenario) for scenario in SCENARIOS],
        "thresholds": {
            key: value if np.isfinite(value) else "infinity (insufficient calibration rank)"
            for key, value in calibration["thresholds"].items()
        },
        "stationary_reference_expected_cost_contrast": calibration["harm_mean"],
        "eprocess_harm_tolerance": config.eprocess_epsilon,
        "calibration_null_maxima": calibration["calibration_null_maxima"],
        "kernel": {"name": "RBF", "gamma": calibration["gamma"], "reference_size": config.window},
        "assumptions": [
            "Synthetic stationary independent observations for finite-rank calibration; evaluation seeds are disjoint from calibration seeds.",
            "CUSUM and MMD thresholds are empirical full-horizon null-rank thresholds, not universal guarantees under dependence or adaptation.",
            "Hoeffding paired-cost e-process requires pre-outcome actions, full paired outcomes, known costs and bounded increments; theorem null is conditional mean excess cost <= epsilon each round.",
            "Benchmark uses immediate complete labels, deterministic policies and imposed synthetic costs; no adaptive sampling, counterfactual identification or real-world utility validation.",
            "Evaluator probabilities, schedules and oracle costs are separate from learner-visible request/decision/feedback stream.",
        ],
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "sklearn": sklearn.__version__,
        },
        "git_revision": _git_revision(),
        "source_sha256": source_hashes,
        "calibration_elapsed_seconds": calibration["elapsed_seconds"],
        "gpu": "Requested device is recorded; generator backend falls back to CPU if PyTorch/CUDA is unavailable.",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8"
    )
    grouped = (
        metrics.groupby("scenario")
        .agg(
            seeds=("seed", "count"),
            mmd=("distribution_discrepancy_mmd_mean", "mean"),
            predictive_change=("predictive_loss_change", "mean"),
            harm=("decision_harm_vs_reference", "mean"),
            regret=("cumulative_regret_vs_oracle", "mean"),
            regret_sd=("cumulative_regret_vs_oracle", "std"),
        )
        .reindex([s.name for s in SCENARIOS])
    )
    rates = (
        alarms[alarms.monitor != "mmd"]
        .groupby(["scenario", "monitor"])
        .false_harm_escalation.mean()
    )
    detection_rates = (
        alarms[alarms.monitor != "mmd"].groupby(["scenario", "monitor"]).harm_detected.mean()
    )
    delays = (
        alarms[alarms.monitor != "mmd"].groupby(["scenario", "monitor"]).detection_delay.median()
    )
    report = [
        "# ShiftLab Phase 2 decision-harm baseline",
        "",
        f"Run: `{output.name}`. This report is generated from {config.evaluation_seeds} independent evaluation seeds per scenario; calibration used {config.calibration_seeds} disjoint stationary seeds.",
        "",
        "## Scientific scope",
        "",
        "The benchmark separates feature-distribution discrepancy, predictive loss change, and expected deployed-versus-reference decision cost. The deployed classifier is an idealized fixed linear-signal rule at threshold 0.5; its explicit challenger is the fixed source cost-minimizing rule. Harmful adaptation deliberately intervenes by always taking action 1. Scenarios are controlled synthetic examples; imposed costs are research utilities, not validated application costs. This isolates monitor behavior and is not a learned-model comparison.",
        "",
        "## Aggregate metrics",
        "",
        "| Scenario | Mean MMD² | Predictive loss change | Expected harm vs reference | Mean cumulative regret (SD) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in grouped.iterrows():
        report.append(
            f"| {name} | {row.mmd:.5g} | {row.predictive_change:.5g} | {row.harm:.5g} | {row.regret:.4g} ({row.regret_sd:.3g}) |"
        )
    report += [
        "",
        "## Harm-monitor false escalation, detection and delay",
        "",
        "False escalation is an alarm before the known evaluator-defined harm onset or any alarm in a scenario whose expected harm does not exceed epsilon. Detection rates count alarms at or after onset; nondetections remain in the denominator and are right-censored at the horizon. Median delays are conditional on detection.",
        "",
        "| Scenario | Monitor | False escalation rate | Detection rate | Median delay |",
        "|---|---|---:|---:|---:|",
    ]
    for (scenario, monitor), rate in rates.items():
        delay = delays.get((scenario, monitor), np.nan)
        detected_rate = detection_rates.get((scenario, monitor), 0.0)
        report.append(
            f"| {scenario} | {monitor} | {rate:.3f} | {detected_rate:.3f} | {delay:.1f} |"
            if pd.notna(delay)
            else f"| {scenario} | {monitor} | {rate:.3f} | {detected_rate:.3f} | not detected |"
        )
    mmd_rows = alarms[alarms.monitor == "mmd"].groupby("scenario")
    report += [
        "",
        "## Distribution-change sentinel",
        "",
        "MMD alarm performance is evaluated against known feature-distribution changes, separately from decision harm. Only the nuisance scenario changes P(X); all other scenarios have fixed feature marginals.",
        "",
        "| Scenario | False distribution alarm rate | Feature-shift detection rate | Median delay |",
        "|---|---:|---:|---:|",
    ]
    for scenario, group in mmd_rows:
        delay = group.feature_detection_delay.median()
        detection_rate = group.feature_shift_detected.mean()
        false_rate = group.false_distribution_alarm.mean()
        report.append(
            f"| {scenario} | {false_rate:.3f} | {detection_rate:.3f} | {delay:.1f} |"
            if pd.notna(delay)
            else f"| {scenario} | {false_rate:.3f} | {detection_rate:.3f} | not applicable/detected |"
        )
    report += [
        "",
        "## Figures and data",
        "",
        "- `estimands_by_scenario.png` compares the three distinct estimands.",
        "- `alarms_and_delay.png` summarizes false harm escalations and detection delays.",
        "- `cumulative_regret.png` shows evaluator-oracle regret.",
        "- `metrics.parquet`, `alarm_metrics.parquet`, and `monitor_trace.parquet` contain seed-level results and traces.",
        "- `manifest.json` records configuration, seeds, thresholds, assumptions, software versions and source hashes.",
        "",
        "## Limitations",
        "",
        "The rank calibration is marginal under exchangeability of independent stationary calibration and evaluation streams, at a fixed horizon and scenario family; it is not robust to serial dependence, drift in the null, tuning on evaluation results, or post-selection. The paired e-process is only a valid example under the bounded full-feedback conditional null stated in the manifest and source, with the fixed prespecified epsilon=0.10 cost-unit threshold; it is not valid for selective missing labels or unknown counterfactuals. No asymptotic/finite-sample guarantee is claimed for discrepancy or CUSUM aside from the stated independent-run rank calibration. The benchmark does not settle adaptation selection, delayed or adaptively sampled labels, or utility misspecification.",
        "",
    ]
    (output / "baseline_report.md").write_text("\n".join(report), encoding="utf-8")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--calibration-seeds", type=int, default=60)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument(
        "--quick", action="store_true", help="Small smoke run, not paper-quality results."
    )
    args = parser.parse_args(argv)
    config = ExperimentConfig(
        evaluation_seeds=2 if args.quick else args.seeds,
        calibration_seeds=6 if args.quick else args.calibration_seeds,
        n=800 if args.quick else args.n,
        calibration_start=200 if args.quick else max(200, int(args.n * 0.25)),
        device=args.device,
    )
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.output
        or Path("data/reports/decision_harm_phase2") / f"{timestamp}-{config.seed_offset}"
    )
    result = run_experiment(config, output)
    # Python on Windows may use a legacy console encoding that cannot render a Unicode parent
    # directory; emit escaped JSON so completion is still observable from any terminal.
    print(json.dumps({"output": str(result.resolve())}, ensure_ascii=True))


if __name__ == "__main__":
    main()
