"""Compare PPI reliance rules using matched block labels and exact design variance."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.decision_harm_experiment import (
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
)
from shiftlab.dive.estimators import (
    pprm_adaptive_reliance,
    pprm_block_design_variance,
    pprm_block_estimate,
)
from shiftlab.dive.experiment import _binary_cost, _synthetic_label_costs
from shiftlab.dive.hard_budget import HardBudgetConfig
from shiftlab.dive.proxy import DecisionLossProxy

SCENARIO_NAMES = ("stationary", "boundary_local_harm", "harmful_adaptation", "recurring_regimes")
STRATEGIES = ("eta_0", "eta_0p1", "eta_0p5", "eta_1", "plugin_cap_0p1", "plugin_cap_1")
FIXED_ETA = {"eta_0": 0.0, "eta_0p1": 0.1, "eta_0p5": 0.5, "eta_1": 1.0}


def _stream_rows(
    scenario: object,
    seed: int,
    config: HardBudgetConfig,
    common_uniforms: np.ndarray,
) -> list[dict[str, object]]:
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
        device=config.device,
    )
    _, frame, _oracle, _ = _generate(scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    fn, fp = scenario.fn_cost, scenario.fp_cost
    cost_bound = max(fn, fp)
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered = difference - config.harm_margin
    label_costs = _synthetic_label_costs(x)
    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    validation_start = max(100, int(config.n * 0.125))
    proxy = DecisionLossProxy(
        clip=cost_bound + config.harm_margin,
        seed=seed,
        update_every=20,
    ).fit(
        x[:train_end],
        centered[:train_end],
        x[train_end:monitor_start],
        centered[train_end:monitor_start],
    )
    proxy_raw = np.clip(
        proxy.predict(x[monitor_start:]) + config.harm_margin,
        -cost_bound,
        cost_bound,
    )
    z_stream = (difference[monitor_start:] + cost_bound) / (2 * cost_bound)
    h_stream = (proxy_raw + cost_bound) / (2 * cost_bound)
    proxy_rmse = float(np.sqrt(np.mean((proxy_raw - difference[monitor_start:]) ** 2)))
    proxy_corr = float(np.corrcoef(z_stream, h_stream)[0, 1])
    proxy_corr_squared = proxy_corr**2 if np.isfinite(proxy_corr) else float("nan")
    event_count = config.n - monitor_start
    budget_per_event = config.budget_rate * float(
        label_costs[validation_start:monitor_start].mean()
    )
    remaining = budget_per_event * event_count
    label_count = config.pprm_labels_per_block
    block_size = config.pprm_block_size
    fixed_eta = dict(FIXED_ETA)
    adaptive_eta = {"plugin_cap_0p1": 0.1, "plugin_cap_1": 1.0}
    history_z = {name: [] for name in adaptive_eta}
    history_h_labeled = {name: [] for name in adaptive_eta}
    history_h_unlabeled = {name: [] for name in adaptive_eta}
    estimate_errors = {name: [] for name in STRATEGIES}
    design_variances = {name: [] for name in STRATEGIES}
    reliance_values = {name: [] for name in STRATEGIES}
    oracle_eta_values: list[float] = []
    processed = 0

    for block_start in range(0, event_count - block_size + 1, block_size):
        if remaining + 1e-12 < label_count * config.max_label_cost:
            break
        block_end = block_start + block_size
        absolute_start = monitor_start + block_start
        absolute_end = monitor_start + block_end
        local_u = common_uniforms[absolute_start:absolute_end]
        labeled = np.argpartition(local_u, label_count - 1)[:label_count]
        unlabeled_mask = np.ones(block_size, dtype=bool)
        unlabeled_mask[labeled] = False
        z = z_stream[block_start:block_end]
        h = h_stream[block_start:block_end]
        proxy_variance = float(np.var(h, ddof=1))
        if proxy_variance > np.finfo(float).eps:
            covariance = float(np.cov(z, h, ddof=1)[0, 1])
            oracle_eta_values.append(
                float(np.clip(covariance * (len(h) - label_count) / len(h) / proxy_variance, 0, 1))
            )
        z_labeled = z[labeled]
        h_labeled = h[labeled]
        h_unlabeled = h[unlabeled_mask]
        block_truth = float(z.mean())
        etas = dict(fixed_eta)
        for name, cap in adaptive_eta.items():
            etas[name] = pprm_adaptive_reliance(
                np.asarray(history_z[name]),
                np.asarray(history_h_labeled[name]),
                np.asarray(history_h_unlabeled[name]),
                max_reliance=cap,
                fallback_reliance=cap,
            )
        for name, eta in etas.items():
            estimate = pprm_block_estimate(
                z_labeled,
                h_labeled,
                h_unlabeled,
                reliance=eta,
            )
            estimate_errors[name].append(estimate - block_truth)
            design_variances[name].append(
                pprm_block_design_variance(
                    z,
                    h,
                    n_labeled=label_count,
                    reliance=eta,
                )
            )
            reliance_values[name].append(eta)
        for name in adaptive_eta:
            history_z[name].extend(z_labeled.tolist())
            history_h_labeled[name].extend(h_labeled.tolist())
            history_h_unlabeled[name].extend(h_unlabeled.tolist())
        selected_spend = float(label_costs[absolute_start:absolute_end][labeled].sum())
        remaining -= selected_spend
        processed += block_size

    n_blocks = processed // block_size
    rows = []
    for name in STRATEGIES:
        errors = np.asarray(estimate_errors[name], dtype=float)
        variances = np.asarray(design_variances[name], dtype=float)
        rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "strategy": name,
                "n": config.n,
                "block_size": block_size,
                "labels_per_block": label_count,
                "blocks": n_blocks,
                "processed_events": processed,
                "labels_queried": n_blocks * label_count,
                "stream_error": float(errors.mean()) if len(errors) else np.nan,
                "conditional_design_sd": (
                    float(np.sqrt(variances.sum()) / n_blocks) if n_blocks else np.nan
                ),
                "mean_abs_block_error": float(np.mean(np.abs(errors))) if len(errors) else np.nan,
                "mean_eta": float(np.mean(reliance_values[name]))
                if reliance_values[name]
                else np.nan,
                "mean_design_variance_per_block": float(np.mean(variances))
                if len(variances)
                else np.nan,
                "proxy_rmse": proxy_rmse,
                "proxy_corr_squared": proxy_corr_squared,
                "evaluator_oracle_eta_mean": float(np.mean(oracle_eta_values))
                if oracle_eta_values
                else np.nan,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/pprm_variance_diagnostic_v1"))
    parser.add_argument("--n", type=int, default=1600)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20372023)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = HardBudgetConfig(
        n=args.n,
        d=16,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        budget_rate=0.20,
        q_min=0.10,
        q_max=0.80,
        common_eprocess_bound=True,
        pprm_block_size=20,
        pprm_labels_per_block=4,
        pprm_max_reliance=1.0,
        pprm_initial_reliance=1.0,
        device=args.device,
        scenario_subset=SCENARIO_NAMES,
        method_subset=("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"),
    ).validate()
    config = HardBudgetConfig(
        **{
            **asdict(config),
            "device": resolve_device(config.device, n=config.n, d=config.d, chunk_size=2048),
        }
    )
    metrics_path = args.output / "block_variance_streams.csv"
    if metrics_path.exists():
        raise FileExistsError(f"refusing to overwrite {metrics_path}")
    scenarios = [scenario for scenario in SCENARIOS if scenario.name in SCENARIO_NAMES]
    rows = []
    for scenario in scenarios:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            uniforms = np.random.default_rng(seed + 9_173).random(config.n)
            print(
                f"variance diagnostic scenario={scenario.name} seed={seed} device={config.device}",
                flush=True,
            )
            rows.extend(_stream_rows(scenario, seed, config, uniforms))
    args.output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(metrics_path, index=False)
    summary = (
        frame.groupby(["scenario", "strategy"])
        .agg(
            streams=("seed", "nunique"),
            empirical_rmse=("stream_error", lambda x: float(np.sqrt(np.mean(x**2)))),
            empirical_bias=("stream_error", "mean"),
            empirical_error_sd=("stream_error", "std"),
            mean_predicted_design_sd=("conditional_design_sd", "mean"),
            mean_abs_block_error=("mean_abs_block_error", "mean"),
            mean_eta=("mean_eta", "mean"),
            mean_design_variance_per_block=("mean_design_variance_per_block", "mean"),
            proxy_rmse=("proxy_rmse", "mean"),
            proxy_corr_squared=("proxy_corr_squared", "mean"),
            evaluator_oracle_eta_mean=("evaluator_oracle_eta_mean", "mean"),
            mean_processed_events=("processed_events", "mean"),
            mean_labels=("labels_queried", "mean"),
        )
        .reset_index()
    )
    summary_path = args.output / "block_variance_summary.csv"
    summary.to_csv(summary_path, index=False)
    lines = [
        "# PPI block estimator variance diagnosis",
        "",
        f"This design-based diagnosis uses {config.seeds} stream seeds per scenario at n={config.n}, B=20, and 4 uniformly sampled labels per block. Every estimator strategy uses the exact same labeled subset in each block. The conditional finite-population design variance is calculated from the block's evaluator-known values as `(1/n_labeled - 1/B) * S²[z - eta * B/(B-n_labeled) * h]`. This is a conditional variance calculation for simple random sampling without replacement; it does not reveal the values to the learner.",
        "",
        "Strategies compare fixed eta values 0, 0.1, 0.5, and 1 with the existing plug-in rule capped at 0.1 or 1.0. The stream prediction is the equally weighted mean of block estimates. These are estimator diagnostics, not monitor power or calibration results.",
        "",
        "|Scenario|Strategy|Streams|Empirical stream RMSE|Mean stream error|Stream error SD|Mean predicted design SD|Mean eta|Evaluator oracle eta|Proxy RMSE|Proxy correlation squared|Mean block design variance|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        eta = "n/a" if pd.isna(row["mean_eta"]) else f"{row['mean_eta']:.3f}"
        oracle_eta = (
            "n/a"
            if pd.isna(row["evaluator_oracle_eta_mean"])
            else f"{row['evaluator_oracle_eta_mean']:.3f}"
        )
        lines.append(
            f"|{row['scenario']}|{row['strategy']}|{row['streams']}|{row['empirical_rmse']:.5f}|{row['empirical_bias']:.5f}|{row['empirical_error_sd']:.5f}|{row['mean_predicted_design_sd']:.5f}|{eta}|{oracle_eta}|{row['proxy_rmse']:.5f}|{row['proxy_corr_squared']:.4f}|{row['mean_design_variance_per_block']:.6f}|"
        )
    report_path = args.output / "block_variance_diagnostic.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "experiment": "pprm_block_finite_population_variance_diagnostic",
        "classification": "development_only_matched_label_assignments",
        "configuration": asdict(config),
        "requested_device": args.device,
        "environment": environment(),
        "sha256": {
            "source_files": {
                str(path): sha256(path)
                for path in (
                    Path(__file__),
                    Path("src/shiftlab/dive/estimators.py"),
                    Path("src/shiftlab/dive/hard_budget.py"),
                )
            },
            "artifacts": {
                path.name: sha256(path) for path in (metrics_path, summary_path, report_path)
            },
        },
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(report_path)


if __name__ == "__main__":
    main()
