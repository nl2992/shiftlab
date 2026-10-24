"""Matched-budget development benchmark for prequential proxy aggregation."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import ndtr
from scipy.stats import beta, binomtest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge

from ..data.gpu.environment import environment
from ..decision_harm_experiment import (
    POPULATION_NULL_CONTROLS,
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from .eprocess import BoundedMeanEProcess
from .estimators import prediction_powered_bound, prediction_powered_estimate
from .experiment import _binary_cost, _material_harm_onset, _synthetic_label_costs
from .proxy_aggregation import PredictableProxyHedge

METHODS = ("zero", "ridge", "forest", "risk_model", "validation_best", "prequential_hedge")
REFERENCE_METHOD = "ridge"
MATERIAL_HARM_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
DEFAULT_SCENARIOS = tuple(scenario.name for scenario in SCENARIOS)
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20261026


@dataclass(frozen=True)
class ProxyHedgeBenchmarkConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 100
    seed_offset: int = 20401024
    query_rate: float = 0.20
    alpha: float = 0.05
    harm_margin: float = 0.10
    max_label_cost: float = 2.5
    train_fraction: float = 0.125
    validation_fraction: float = 0.125
    device: str = "cuda"
    scenario_subset: tuple[str, ...] = DEFAULT_SCENARIOS

    def validate(self) -> ProxyHedgeBenchmarkConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds positive")
        if not 0 < self.query_rate <= 1 or not 0 < self.alpha < 1:
            raise ValueError("query_rate and alpha must lie in (0,1]")
        if self.harm_margin < 0 or not np.isfinite(self.harm_margin):
            raise ValueError("harm_margin must be finite and nonnegative")
        if self.max_label_cost <= 0 or not np.isfinite(self.max_label_cost):
            raise ValueError("max_label_cost must be finite and positive")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        registered = {scenario.name for scenario in SCENARIOS}
        if not self.scenario_subset or not set(self.scenario_subset) <= registered:
            raise ValueError("scenario_subset must contain registered scenarios")
        if self.train_fraction <= 0 or self.validation_fraction <= 0:
            raise ValueError("training and validation fractions must be positive")
        if self.train_fraction + self.validation_fraction >= 1:
            raise ValueError("training and validation fractions must sum to less than one")
        train_end = max(100, int(self.n * self.train_fraction))
        monitor_start = max(800, int(self.n * (self.train_fraction + self.validation_fraction)))
        if train_end >= monitor_start - 50 or monitor_start >= self.n:
            raise ValueError("n is too small for disjoint training, validation, and monitor slices")
        return self


def _expert_predictions(
    *,
    x: np.ndarray,
    y: np.ndarray,
    centered_cost_difference: np.ndarray,
    contrast_zero: np.ndarray,
    contrast_one: np.ndarray,
    train_end: int,
    validation_end: int,
    monitor_end: int,
    seed: int,
    clip: float,
) -> tuple[dict[str, np.ndarray], str, dict[str, float]]:
    train_x = x[:train_end]
    train_y = y[:train_end]
    train_z = centered_cost_difference[:train_end]
    validation_x = x[train_end:validation_end]
    validation_z = centered_cost_difference[train_end:validation_end]
    monitor_x = x[validation_end:monitor_end]

    ridge = Ridge(alpha=1.0).fit(train_x, train_z)
    forest = RandomForestRegressor(
        n_estimators=64,
        max_depth=8,
        min_samples_leaf=5,
        max_features=1.0,
        n_jobs=1,
        random_state=seed,
    ).fit(train_x, train_z)
    if np.unique(train_y).size == 2:
        classifier = LogisticRegression(max_iter=500, random_state=seed).fit(train_x, train_y)
        validation_p = classifier.predict_proba(validation_x)[:, 1]
        monitor_p = classifier.predict_proba(monitor_x)[:, 1]
    else:
        rate = float(np.mean(train_y))
        validation_p = np.full(len(validation_x), rate)
        monitor_p = np.full(len(monitor_x), rate)

    def risk_proxy(probability: np.ndarray, indices: np.ndarray) -> np.ndarray:
        return (1 - probability) * contrast_zero[indices] + probability * contrast_one[indices]

    validation_indices = np.arange(train_end, validation_end)
    monitor_indices = np.arange(validation_end, monitor_end)
    validation_predictions = {
        "zero": np.zeros(len(validation_x)),
        "ridge": ridge.predict(validation_x),
        "forest": forest.predict(validation_x),
        "risk_model": risk_proxy(validation_p, validation_indices),
    }
    monitor_predictions = {
        "zero": np.zeros(len(monitor_x)),
        "ridge": ridge.predict(monitor_x),
        "forest": forest.predict(monitor_x),
        "risk_model": risk_proxy(monitor_p, monitor_indices),
    }
    validation_rmse = {
        name: float(np.sqrt(np.mean((np.clip(values, -clip, clip) - validation_z) ** 2)))
        for name, values in validation_predictions.items()
    }
    selected = min(validation_rmse, key=validation_rmse.get)
    monitor_predictions = {
        name: np.clip(values, -clip, clip) for name, values in monitor_predictions.items()
    }
    return monitor_predictions, selected, validation_rmse


def _monitor_one_stream(
    *,
    method: str,
    experts: np.ndarray,
    selected_expert: str,
    true_values: np.ndarray,
    expected_cost_difference: np.ndarray,
    query_mask: np.ndarray,
    label_costs: np.ndarray,
    harm_onset: int | None,
    scenario_name: str,
    config: ProxyHedgeBenchmarkConfig,
    clip: float,
    hard_budget: float,
) -> dict[str, object]:
    q = config.query_rate
    bound = prediction_powered_bound(clip, q)
    process = BoundedMeanEProcess(bound=bound, alpha=config.alpha)
    hedge = PredictableProxyHedge(n_experts=experts.shape[1], bound=clip, min_propensity=q)
    remaining = hard_budget
    spend = 0.0
    estimates: list[float] = []
    truths: list[float] = []
    alarm_time: int | None = None
    labels_at_alarm: int | None = None
    queried = 0
    processed = 0
    max_cost = config.max_label_cost

    for offset, truth in enumerate(true_values):
        cost = float(label_costs[offset])
        if remaining + 1e-12 < max_cost:
            break
        is_queried = bool(query_mask[offset])
        if is_queried:
            if cost > remaining + 1e-12:
                raise RuntimeError("reserve rule failed to protect the hard budget")
            remaining -= cost
            spend += cost
            queried += 1

        current_experts = experts[offset]
        if method == "zero":
            proxy = float(current_experts[0])
        elif method in {"ridge", "forest", "risk_model"}:
            proxy = float(current_experts[("zero", "ridge", "forest", "risk_model").index(method)])
        elif method == "validation_best":
            proxy = float(
                current_experts[("zero", "ridge", "forest", "risk_model").index(selected_expert)]
            )
        else:
            proxy = hedge.predict(current_experts)

        observed = float(truth) if is_queried else None
        estimate = prediction_powered_estimate(proxy, is_queried, observed, q)
        process_value = process.update(estimate)
        estimates.append(estimate)
        truths.append(float(truth))
        processed += 1
        if alarm_time is None and process_value >= -np.log(config.alpha):
            alarm_time = offset
            labels_at_alarm = queried
        if method == "prequential_hedge" and is_queried:
            hedge.observe(current_experts, float(truth), q)

    detected = alarm_time is not None and harm_onset is not None and alarm_time >= harm_onset
    false_escalation = alarm_time is not None and (harm_onset is None or alarm_time < harm_onset)
    errors = np.asarray(estimates) - np.asarray(truths)
    return {
        "scenario": scenario_name,
        "seed": int(config.seed_offset),
        "method": method,
        "selected_validation_expert": selected_expert,
        "harm_onset_relative": harm_onset,
        "material_harm": harm_onset is not None,
        "population_null_control": scenario_name in POPULATION_NULL_CONTROLS,
        "detected": bool(detected),
        "false_escalation": bool(false_escalation),
        "alarm_time": alarm_time,
        "detection_delay": alarm_time - harm_onset if detected else None,
        "labels_at_alarm": labels_at_alarm,
        "labels_queried": queried,
        "events_processed": processed,
        "hard_budget": hard_budget,
        "realized_label_spend": spend,
        "budget_respected": spend <= hard_budget + 1e-9,
        "estimator_rmse": float(np.sqrt(np.mean(errors**2))) if len(errors) else np.nan,
        "stream_mean_estimation_error": float(np.mean(errors)) if len(errors) else np.nan,
        "cumulative_expected_excess_cost": float(np.sum(expected_cost_difference[:processed])),
        "hedge_updates": hedge.n_updates if method == "prequential_hedge" else 0,
    }


def _run_stream(scenario, seed: int, config: ProxyHedgeBenchmarkConfig) -> list[dict[str, object]]:
    experiment_config = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        alpha=config.alpha,
        eprocess_epsilon=config.harm_margin,
        seed_offset=seed,
        device=config.device,
    )
    _, frame, oracle, timing = _generate(scenario, seed, experiment_config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    probability_truth = oracle.probability_positive.to_numpy(dtype=float)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[config.n // 2 :] = 1
    reference = _source_action(x, scenario)
    paired_difference = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered_difference = paired_difference - config.harm_margin
    contrast_zero = (
        _binary_cost(deployed, np.zeros_like(y), fn, fp)
        - _binary_cost(reference, np.zeros_like(y), fn, fp)
        - config.harm_margin
    )
    contrast_one = (
        _binary_cost(deployed, np.ones_like(y), fn, fp)
        - _binary_cost(reference, np.ones_like(y), fn, fp)
        - config.harm_margin
    )
    deployed_expected = np.where(
        deployed == 1, fp * (1 - probability_truth), fn * probability_truth
    )
    reference_expected = np.where(
        reference == 1, fp * (1 - probability_truth), fn * probability_truth
    )
    expected_difference = deployed_expected - reference_expected
    train_end = max(100, int(config.n * config.train_fraction))
    monitor_start = max(800, int(config.n * (config.train_fraction + config.validation_fraction)))
    monitor_end = config.n
    clip = float(max(fn, fp) + config.harm_margin)
    predictions, selected_expert, validation_rmse = _expert_predictions(
        x=x,
        y=y,
        centered_cost_difference=centered_difference,
        contrast_zero=contrast_zero,
        contrast_one=contrast_one,
        train_end=train_end,
        validation_end=monitor_start,
        monitor_end=monitor_end,
        seed=seed,
        clip=clip,
    )
    sample_harm_onset = _material_harm_onset(
        expected_difference,
        config.harm_margin,
        change_times=timing["change_times"],
        monitor_start=monitor_start,
    )
    harm_onset = statistical_harm_onset(scenario.name, sample_harm_onset)

    monitor_count = monitor_end - monitor_start
    costs = _synthetic_label_costs(x)
    validation_costs = costs[train_end:monitor_start]
    budget = config.query_rate * float(validation_costs.mean()) * monitor_count
    rng = np.random.default_rng(seed + 910_2026)
    uniforms = rng.random(monitor_count)
    remaining = budget
    query_mask = np.zeros(monitor_count, dtype=bool)
    process_count = 0
    for offset, index in enumerate(range(monitor_start, monitor_end)):
        if remaining + 1e-12 < config.max_label_cost:
            break
        process_count += 1
        if uniforms[offset] < config.query_rate:
            cost = float(costs[index])
            if cost > remaining + 1e-12:
                raise RuntimeError("query cost exceeded the pre-event reserve")
            query_mask[offset] = True
            remaining -= cost
    selected_costs = costs[monitor_start : monitor_start + process_count]
    # Use one shared observation path; every proxy method receives exactly the same labels.
    experts = np.column_stack(
        [predictions[name] for name in ("zero", "ridge", "forest", "risk_model")]
    )
    true_values = centered_difference[monitor_start : monitor_start + process_count]
    expected_values = expected_difference[monitor_start : monitor_start + process_count]
    rows = []
    for method in METHODS:
        row = _monitor_one_stream(
            method=method,
            experts=experts[:process_count],
            selected_expert=selected_expert,
            true_values=true_values,
            expected_cost_difference=expected_values,
            query_mask=query_mask[:process_count],
            label_costs=selected_costs,
            harm_onset=harm_onset,
            scenario_name=scenario.name,
            config=replace_seed(config, seed),
            clip=clip,
            hard_budget=budget,
        )
        row["seed"] = seed
        row["validation_rmse_by_expert"] = validation_rmse
        row["generator_device"] = experiment_config.device
        row["query_rate"] = config.query_rate
        row["eprocess_bound"] = prediction_powered_bound(clip, config.query_rate)
        row["monitor_horizon_available"] = monitor_count
        rows.append(row)
    if (
        len(
            {
                (row["labels_queried"], row["events_processed"], row["realized_label_spend"])
                for row in rows
            }
        )
        != 1
    ):
        raise RuntimeError("proxy methods did not receive a matched query and cost path")
    if not all(row["budget_respected"] for row in rows):
        raise RuntimeError("a proxy method exceeded the shared hard label-dollar cap")
    return rows


def replace_seed(config: ProxyHedgeBenchmarkConfig, seed: int) -> ProxyHedgeBenchmarkConfig:
    """Return the immutable run config with the current stream seed for metrics."""
    from dataclasses import replace

    return replace(config, seed_offset=seed)


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def _summarize(frame: pd.DataFrame, config: ProxyHedgeBenchmarkConfig):
    summaries = []
    for (scenario, method), group in frame.groupby(["scenario", "method"], sort=True):
        false_count = int(group.false_escalation.sum())
        n = len(group)
        lower = (
            0.0 if false_count == 0 else float(beta.ppf(0.025, false_count, n - false_count + 1))
        )
        upper = (
            1.0 if false_count == n else float(beta.ppf(0.975, false_count + 1, n - false_count))
        )
        summaries.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": n,
                "material_streams": int(group.material_harm.sum()),
                "detections": int(group.detected.sum()),
                "detection_rate": float(group.loc[group.material_harm, "detected"].mean())
                if group.material_harm.any()
                else np.nan,
                "false_escalations": false_count,
                "false_escalation_rate": false_count / n,
                "false_escalation_cp95_lower": lower,
                "false_escalation_cp95_upper": upper,
                "mean_labels": float(group.labels_queried.mean()),
                "mean_spend": float(group.realized_label_spend.mean()),
                "mean_events_processed": float(group.events_processed.mean()),
                "mean_delay_when_detected": float(
                    group.loc[group.detected, "detection_delay"].mean()
                )
                if group.detected.any()
                else np.nan,
                "mean_estimator_rmse": float(group.estimator_rmse.mean()),
                "mean_expected_excess_cost": float(group.cumulative_expected_excess_cost.mean()),
            }
        )
    summary = pd.DataFrame(summaries)

    paired = []
    alternatives = [name for name in MATERIAL_HARM_SCENARIOS if name in set(frame.scenario)]
    for scenario in alternatives:
        cell = frame[frame.scenario == scenario].pivot(
            index="seed", columns="method", values="detected"
        )
        hedge_only = int((cell.prequential_hedge & ~cell[REFERENCE_METHOD]).sum())
        reference_only = int((~cell.prequential_hedge & cell[REFERENCE_METHOD]).sum())
        p_value = (
            float(binomtest(hedge_only, hedge_only + reference_only, 0.5).pvalue)
            if hedge_only + reference_only
            else 1.0
        )
        paired.append(
            {
                "scenario": scenario,
                "hedge_detection_rate": float(cell.prequential_hedge.mean()),
                "ridge_detection_rate": float(cell[REFERENCE_METHOD].mean()),
                "difference": float(
                    (cell.prequential_hedge.astype(float) - cell[REFERENCE_METHOD]).mean()
                ),
                "hedge_only": hedge_only,
                "ridge_only": reference_only,
                "mcnemar_p": p_value,
            }
        )
    if paired:
        adjusted = _holm([row["mcnemar_p"] for row in paired])
        for row, p_adj in zip(paired, adjusted, strict=True):
            row["holm_adjusted_p"] = p_adj
    paired_frame = pd.DataFrame(paired)

    harm = frame[frame.scenario.isin(alternatives) & frame.material_harm]
    wide = harm.pivot(index=["seed", "scenario"], columns="method", values="detected")
    seed_differences = (
        (wide.prequential_hedge.astype(float) - wide[REFERENCE_METHOD].astype(float))
        .groupby("seed")
        .mean()
    )
    values = seed_differences.to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.empty(BOOTSTRAP_REPLICATES)
    batch = 500
    for start in range(0, BOOTSTRAP_REPLICATES, batch):
        size = min(batch, BOOTSTRAP_REPLICATES - start)
        indices = rng.integers(0, len(values), size=(size, len(values)))
        draws[start : start + size] = values[indices].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    macro = {
        "paired_macro_detection_difference_hedge_minus_ridge": float(values.mean()),
        "seed_cluster_bootstrap_95": [float(low), float(high)],
        "seed_clusters": len(values),
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
    return summary, paired_frame, macro


def run_proxy_hedge_benchmark(
    output_dir: str | Path, config: ProxyHedgeBenchmarkConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    rows = []
    for scenario_name in config.scenario_subset:
        scenario = scenarios[scenario_name]
        for seed in range(config.seed_offset, config.seed_offset + config.seeds):
            rows.extend(_run_stream(scenario, seed, config))
    metrics = pd.DataFrame(rows)
    summary, paired, macro = _summarize(metrics, config)
    metrics_path = output / "metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "scenario_summary.csv", index=False)
    paired.to_csv(output / "paired_detection_tests.csv", index=False)
    module_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "methods": list(METHODS),
        "reference_method": REFERENCE_METHOD,
        "proxy_experts": ["zero", "ridge", "forest", "risk_model"],
        "hedge_learning_rate": config.query_rate / 2,
        "alternative_scenarios": [
            name for name in MATERIAL_HARM_SCENARIOS if name in config.scenario_subset
        ],
        "population_null_scenarios": [
            name for name in POPULATION_NULL_CONTROLS if name in config.scenario_subset
        ],
        "metric_rows": len(metrics),
        "macro_primary": macro,
        "resolved_generator_device": config.device,
        "environment": environment(),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            "proxy_hedge_benchmark.py": hashlib.sha256(
                (module_dir / "proxy_hedge_benchmark.py").read_bytes()
            ).hexdigest(),
            "proxy_aggregation.py": hashlib.sha256(
                (module_dir / "proxy_aggregation.py").read_bytes()
            ).hexdigest(),
            "estimators.py": hashlib.sha256(
                (module_dir / "estimators.py").read_bytes()
            ).hexdigest(),
            "eprocess.py": hashlib.sha256((module_dir / "eprocess.py").read_bytes()).hexdigest(),
            "experiment.py": hashlib.sha256(
                (module_dir / "experiment.py").read_bytes()
            ).hexdigest(),
            "decision_harm_experiment.py": hashlib.sha256(
                (module_dir.parent / "decision_harm_experiment.py").read_bytes()
            ).hexdigest(),
        },
        "interpretation": "Development-only matched-budget comparison. The seed-cluster bootstrap is descriptive selection evidence; 100-stream null counts do not certify calibration.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Prequential proxy-Hedge development benchmark",
        "",
        f"Primary paired macro detection difference (Hedge minus ridge): **{macro['paired_macro_detection_difference_hedge_minus_ridge']:.4f}**; seed-cluster bootstrap 95% interval [{macro['seed_cluster_bootstrap_95'][0]:.4f}, {macro['seed_cluster_bootstrap_95'][1]:.4f}].",
        "",
        f"Streams: {len(metrics)} method-stream rows across {len(config.scenario_subset)} scenarios and {config.seeds} seeds; query probability {config.query_rate:.2f}; generator requested device {config.device}.",
        "",
        "## Scenario summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired detection tests: Hedge versus ridge",
        "",
        paired.to_markdown(index=False, floatfmt=".5g"),
        "",
        "This development screen is not a false-alarm calibration or a novelty result. Advance only under the registered criteria in `docs/prequential_proxy_hedge_protocol.md`; otherwise keep the negative result.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return metrics, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/prequential_proxy_hedge_development")
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--seed-offset", type=int, default=20401024)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--query-rate", type=float, default=0.20)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--scenarios", nargs="+", choices=DEFAULT_SCENARIOS, default=DEFAULT_SCENARIOS
    )
    args = parser.parse_args()
    config = ProxyHedgeBenchmarkConfig(
        n=args.n,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        query_rate=args.query_rate,
        device=args.device,
        scenario_subset=tuple(args.scenarios),
    )
    _metrics, summary, manifest = run_proxy_hedge_benchmark(args.output_dir, config)
    print(summary.to_string(index=False))
    print(f"primary={manifest['macro_primary']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
