"""Evaluate fitted update policies using only timestamped arrived feedback."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

from shiftlab.data.label_availability import labels_available_before
from shiftlab.data.provenance import commit, sha256, source_hash, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.streaming import Label, Request, replay
from shiftlab.data.synthetic import generate_chunks
from shiftlab.data.synthetic.adaptation import pareto_frontier_mask
from shiftlab.learner import Learner
from shiftlab.streaming import Feedback, Observation

SCHEDULES = {
    "abrupt": {"pattern": "abrupt", "change_fraction": 0.65},
    "gradual": {
        "pattern": "linear",
        "change_fraction": 0.55,
        "transition_fraction": 0.15,
    },
    "temporary": {
        "pattern": "temporary",
        "change_fraction": 0.62,
        "transition_fraction": 0.2,
    },
    "recurring": {"pattern": "recurring", "regimes": 4},
}
SEEDS = (11, 23, 37, 53, 71)
RESOURCE_BUDGET = 12.0
RESOURCE_PRICE_GRID = (0.0, 0.1, 1.0, 5.0)
POLICY_VARIANTS = (
    ("ridge_frozen", "ridge", "frozen", "fixed"),
    ("ridge_periodic", "ridge", "periodic", "fixed"),
    ("ridge_periodic_recalibration", "ridge", "periodic_recalibration", "fixed"),
    ("ridge_triggered", "ridge", "triggered", "fixed"),
    ("ridge_validation_triggered", "ridge", "validation_triggered", "fixed"),
    ("ridge_recalibration", "ridge", "recalibration", "fixed"),
    ("ridge_partial_update", "ridge", "partial_update", "fixed"),
    ("ridge_triggered_rolling_radius", "ridge", "triggered", "rolling"),
    ("ridge_triggered_exponential_radius", "ridge", "triggered", "exponential"),
    ("forest_frozen", "random_forest", "frozen", "fixed"),
    ("forest_triggered", "random_forest", "triggered", "fixed"),
    ("boosted_tree_frozen", "hist_gradient_boosting", "frozen", "fixed"),
    ("boosted_tree_triggered", "hist_gradient_boosting", "triggered", "fixed"),
)


def initial_rows(frame: pd.DataFrame, split: str, cutoff: float) -> pd.DataFrame:
    """Select rows whose features and labels predate the first test request."""
    available = labels_available_before(frame, cutoff)
    features_known = frame.feature_available_time.notna() & (frame.feature_available_time < cutoff)
    return frame.loc[(frame.split == split) & available & features_known].sort_values(
        "prediction_time", kind="stable"
    )


class AuditedLearner(Learner):
    """Record the arrived-feedback boundary that caused each sequential refit."""

    def __init__(
        self,
        *args,
        model_family="ridge",
        model_seed=0,
        radius_method="fixed",
        cal_score_times=None,
        radius_half_life=None,
        resource_budget=12,
        action_resource_costs=None,
        **kwargs,
    ):
        self.current_feedback_time: int | float | None = None
        self.fit_audit: list[dict[str, int | float | str]] = []
        self.model_family = model_family
        self.model_seed = model_seed
        super().__init__(
            *args,
            radius_method=radius_method,
            cal_score_times=cal_score_times,
            radius_half_life=radius_half_life,
            resource_budget=resource_budget,
            action_resource_costs=action_resource_costs,
            **kwargs,
        )

    def _fit(self, X, y):
        if self.model_family == "ridge":
            super()._fit(X, y)
        elif self.model_family == "random_forest":
            import time

            started = time.perf_counter()
            self.model = RandomForestRegressor(
                n_estimators=32,
                max_depth=6,
                min_samples_leaf=5,
                random_state=self.model_seed,
                n_jobs=1,
            ).fit(X, y)
            self.training_seconds += time.perf_counter() - started
        elif self.model_family == "hist_gradient_boosting":
            import time

            started = time.perf_counter()
            self.model = HistGradientBoostingRegressor(
                max_iter=32,
                max_leaf_nodes=7,
                min_samples_leaf=10,
                l2_regularization=1.0,
                early_stopping=False,
                random_state=self.model_seed,
            ).fit(X, y)
            self.training_seconds += time.perf_counter() - started
        else:
            raise ValueError(f"Unknown model family: {self.model_family}")
        if self.current_feedback_time is not None:
            self.fit_audit.append(
                {
                    "fit_feedback_available_time": self.current_feedback_time,
                    "arrived_feedback_count": self.feedback_count,
                    "method": self.method,
                    "model_family": self.model_family,
                }
            )

    def observe(self, feedback):
        self.current_feedback_time = feedback.available_at
        super().observe(feedback)


def _frame_and_oracle(config: SyntheticConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = list(generate_chunks(config))
    return (
        pd.concat([part[0] for part in parts], ignore_index=True),
        pd.concat([part[1] for part in parts], ignore_index=True),
    )


def cost_frontier_summary(records: list[dict]) -> pd.DataFrame:
    """Summarize measured costs and loss/resource Pareto sets by schedule."""
    frame = pd.DataFrame(records).copy()
    frame["cumulative_squared_error"] = frame.mse * frame.test_n
    for price in RESOURCE_PRICE_GRID:
        frame[f"objective_at_resource_price_{price:g}"] = (
            frame.cumulative_squared_error + price * frame.resource_spent
        )
    aggregations = {
        "n": ("seed", "count"),
        "mean_mse": ("mse", "mean"),
        "mean_cumulative_squared_error": ("cumulative_squared_error", "mean"),
        "mean_resource_units": ("resource_spent", "mean"),
        "mean_training_seconds": ("training_seconds", "mean"),
        "mean_inference_seconds": ("inference_seconds", "mean"),
        "mean_adaptation_seconds": ("adaptation_seconds", "mean"),
        "mean_update_count": ("update_count", "mean"),
    }
    aggregations.update(
        {
            f"mean_objective_at_resource_price_{price:g}": (
                f"objective_at_resource_price_{price:g}",
                "mean",
            )
            for price in RESOURCE_PRICE_GRID
        }
    )
    summary = frame.groupby(["schedule", "policy"], sort=True).agg(**aggregations).reset_index()
    summary["pareto_efficient"] = False
    for indices in summary.groupby("schedule").groups.values():
        selected = summary.loc[indices]
        summary.loc[indices, "pareto_efficient"] = pareto_frontier_mask(
            selected.mean_mse.to_numpy(), selected.mean_resource_units.to_numpy()
        )
    return summary


def plot_cost_frontier(summary: pd.DataFrame, path: Path) -> None:
    """Plot aggregate test MSE against measured-imposed resource consumption."""
    schedules = list(SCHEDULES)
    families = {
        "ridge": "#0072B2",
        "random_forest": "#D55E00",
        "hist_gradient_boosting": "#009E73",
    }
    markers = {"ridge": "o", "random_forest": "s", "hist_gradient_boosting": "^"}
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), sharey=False)
    for ax, schedule in zip(axes.flat, schedules, strict=True):
        rows = summary.loc[summary.schedule == schedule]
        for row in rows.itertuples(index=False):
            family = row.policy.split("_")[0]
            if row.policy.startswith("boosted_tree"):
                family = "hist_gradient_boosting"
            elif row.policy.startswith("forest"):
                family = "random_forest"
            ax.scatter(
                row.mean_resource_units,
                row.mean_mse,
                color=families[family],
                marker=markers[family],
                alpha=1.0 if row.pareto_efficient else 0.45,
                edgecolor="black" if row.pareto_efficient else "none",
                linewidth=0.8,
                s=58,
            )
        efficient = rows.loc[rows.pareto_efficient].sort_values("mean_resource_units")
        ax.plot(
            efficient.mean_resource_units,
            efficient.mean_mse,
            color="#333333",
            linewidth=1.2,
            linestyle="--",
            label="Pareto frontier",
        )
        ax.set_title(schedule.capitalize())
        ax.set_xlabel("Mean imposed compute units per stream")
        ax.set_ylabel("Mean test MSE")
        ax.grid(alpha=0.25)
    from matplotlib.lines import Line2D

    legend = [
        Line2D(
            [0],
            [0],
            marker=markers[family],
            color="w",
            label=family.replace("_", " "),
            markerfacecolor=color,
            markeredgecolor="black",
            markersize=8,
        )
        for family, color in families.items()
    ]
    legend.append(Line2D([0], [0], color="#333333", linestyle="--", label="Pareto frontier"))
    fig.legend(handles=legend, loc="center left", bbox_to_anchor=(0.88, 0.5))
    fig.suptitle("Adaptation loss versus imposed compute cost (five seeds)")
    fig.tight_layout(rect=(0, 0, 0.86, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def evaluate_replicate(schedule: str, seed: int) -> list[dict]:
    config = SyntheticConfig(
        scenario="concept",
        n=1600,
        d=4,
        seed=seed,
        severity=2.0,
        noise=0.3,
        delay=8,
        missing=0.1,
        chunk_size=500,
        train_fraction=0.2,
        validation_fraction=0.1,
        calibration_fraction=0.2,
        **SCHEDULES[schedule],
    )
    frame, oracle = _frame_and_oracle(config)
    test = frame.loc[frame.split == "test"].copy()
    if test.empty:
        raise ValueError(f"No test observations for {schedule}, seed {seed}")
    first_test = float(test.prediction_time.min())
    train = initial_rows(frame, "train", first_test)
    validation = initial_rows(frame, "validation", first_test)
    calibration = initial_rows(frame, "calibration", first_test)
    if len(train) < 20 or len(validation) < 20 or len(calibration) < 20:
        raise ValueError(f"Insufficient arrived initial data for {schedule}, seed {seed}")
    settings = SimpleNamespace(window=80, alpha=0.1, threshold=5.0, period=50, budget=4)
    resource_budget = RESOURCE_BUDGET
    test_ids = test.sample_id.to_numpy()
    targets = test.set_index("sample_id").target
    prediction_time_by_id = test.set_index("sample_id").prediction_time
    oracle_by_id = oracle.set_index(frame.sample_id).loc[test_ids]
    arrived_times = set(test.label_available_time.dropna().astype(float).tolist())
    records = []
    for policy, model_family, method, radius_method in POLICY_VARIANTS:
        learner = AuditedLearner(
            np.stack(train.features.to_numpy()),
            train.target.to_numpy(dtype=float),
            np.stack(calibration.features.to_numpy()),
            calibration.target.to_numpy(dtype=float),
            settings,
            method,
            model_family=model_family,
            model_seed=seed,
            radius_method=radius_method,
            cal_score_times=calibration.label_available_time.to_numpy(dtype=float),
            radius_half_life=80,
            resource_budget=resource_budget,
            action_resource_costs={
                "residual_bias_recalibration": 1.0,
                "normalized_sgd_partial_update": 2.0,
                "refit": 4.0 if model_family == "ridge" else 8.0,
            },
            validation_X=np.stack(validation.features.to_numpy()),
            validation_y=validation.target.to_numpy(dtype=float),
        )
        pending: dict[str, tuple[tuple[float, ...], float]] = {}
        predictions: dict[str, float] = {}
        radii: dict[str, float] = {}
        for event in replay(test):
            if isinstance(event, Request):
                observation = Observation(int(event.prediction_time), event.features)
                prediction, radius = learner.predict(observation)
                pending[event.sample_id] = (event.features, prediction)
                predictions[event.sample_id] = prediction
                radii[event.sample_id] = radius
            elif isinstance(event, Label):
                features, prediction = pending[event.sample_id]
                learner.observe(
                    Feedback(
                        time=int(prediction_time_by_id.loc[event.sample_id]),
                        available_at=event.available_time,
                        features=features,
                        target=event.target,
                        prediction=prediction,
                    )
                )
        ordered_predictions = np.array([predictions[sample_id] for sample_id in test_ids])
        y = targets.loc[test_ids].to_numpy(dtype=float)
        residual = y - ordered_predictions
        ordered_radii = np.array([radii[sample_id] for sample_id in test_ids])
        oracle_noise = oracle_by_id.sigma.to_numpy(dtype=float) ** 2
        known_change = oracle_by_id.weight.to_numpy(dtype=float) > 0
        fit_times = [float(row["fit_feedback_available_time"]) for row in learner.fit_audit]
        coverage_by_block = []
        for block_index, start in enumerate(range(0, len(test), 100)):
            stop = min(start + 100, len(test))
            block_coverage = np.abs(residual[start:stop]) <= ordered_radii[start:stop]
            coverage_by_block.append(
                {
                    "block": block_index,
                    "n": stop - start,
                    "coverage": float(block_coverage.mean()),
                    "mean_width": float(2 * ordered_radii[start:stop].mean()),
                }
            )
        records.append(
            {
                "schedule": schedule,
                "seed": seed,
                "policy": policy,
                "model_family": model_family,
                "update_method": method,
                "radius_method": radius_method,
                "test_n": len(test),
                "mse": float(np.mean(residual**2)),
                "cumulative_squared_error": float(np.sum(residual**2)),
                "training_seconds": float(learner.training_seconds),
                "inference_seconds": float(learner.inference_seconds),
                "adaptation_seconds": float(
                    sum(action["elapsed_seconds"] for action in learner.intervention_audit)
                ),
                "oracle_irreducible_mse": float(np.mean(oracle_noise)),
                "excess_mse_over_oracle": float(np.mean(residual**2 - oracle_noise)),
                "shifted_or_transition_mse": float(np.mean(residual[known_change] ** 2))
                if known_change.any()
                else float("nan"),
                "coverage": float((np.abs(residual) <= ordered_radii).mean()),
                "mean_interval_width": float(2 * ordered_radii.mean()),
                "coverage_by_test_block": coverage_by_block,
                "update_count": len(learner.interventions),
                "update_times": [int(value) for value in learner.interventions],
                "update_budget": settings.budget,
                "resource_spent": learner.resource_spent,
                "resource_budget": resource_budget,
                "intervention_resource_costs": {
                    "residual_bias_recalibration": 1.0,
                    "normalized_sgd_partial_update": 2.0,
                    "refit": 4.0 if model_family == "ridge" else 8.0,
                },
                "feedback_received": learner.feedback_count,
                "feedback_missing_or_delayed_past_horizon": int(
                    test.target.notna().sum() - learner.feedback_count
                ),
                "trigger_alarm_count": len(learner.alarms["error_cusum"]),
                "fit_audit": learner.fit_audit,
                "intervention_audit": learner.intervention_audit,
                "final_bias_correction": learner.bias_correction,
                "validation_loss_threshold": learner.validation_loss_threshold,
                "protocol_passes": bool(
                    len(learner.interventions) <= settings.budget
                    and learner.resource_spent <= resource_budget
                    and len(learner.intervention_audit) == len(learner.interventions)
                    and all(value in arrived_times for value in fit_times)
                    and all(value <= float(test.prediction_time.max()) for value in fit_times)
                    and fit_times == sorted(fit_times)
                    and all(
                        row["arrived_feedback_count"] <= learner.feedback_count
                        for row in learner.fit_audit
                    )
                    and len(predictions) == len(test)
                    and (
                        method != "validation_triggered"
                        or (
                            learner.validation_loss_threshold is not None
                            and np.isfinite(learner.validation_loss_threshold)
                            and len(validation) >= 20
                        )
                    )
                    and test.target.notna().sum() >= learner.feedback_count
                    and np.isfinite(ordered_radii).all()
                    and (ordered_radii >= 0).all()
                    and all(20 <= block["n"] for block in coverage_by_block)
                    and all(
                        row["fit_feedback_available_time"] in learner.interventions
                        for row in learner.fit_audit
                    )
                    and all(
                        action["available_at"] in arrived_times
                        and action["available_at"] in learner.interventions
                        and action["arrived_feedback_count"] <= learner.feedback_count
                        for action in learner.intervention_audit
                    )
                    and all(
                        action["resource_spent"] <= resource_budget
                        and np.isfinite(action["elapsed_seconds"])
                        and action["elapsed_seconds"] >= 0
                        and np.isclose(
                            action["resource_cost"],
                            {
                                "residual_bias_recalibration": 1.0,
                                "normalized_sgd_partial_update": 2.0,
                                "refit": 4.0 if model_family == "ridge" else 8.0,
                            }[action["action"]],
                        )
                        for action in learner.intervention_audit
                    )
                    and all(
                        action["action"]
                        == {
                            "recalibration": "residual_bias_recalibration",
                            "periodic_recalibration": "residual_bias_recalibration",
                            "partial_update": "normalized_sgd_partial_update",
                        }.get(method, "refit")
                        for action in learner.intervention_audit
                    )
                ),
                "utility_origin": "synthetic squared prediction error; no application cost claim",
            }
        )
    return records


def evaluate() -> dict:
    rows = [
        record
        for schedule in SCHEDULES
        for seed in SEEDS
        for record in evaluate_replicate(schedule, seed)
    ]
    frame = pd.DataFrame(rows)
    summary = (
        frame.groupby(["schedule", "policy"], sort=True)
        .agg(
            n=("seed", "count"),
            mean_mse=("mse", "mean"),
            sd_mse=("mse", "std"),
            mean_excess_mse=("excess_mse_over_oracle", "mean"),
            mean_shifted_mse=("shifted_or_transition_mse", "mean"),
            mean_updates=("update_count", "mean"),
            mean_feedback=("feedback_received", "mean"),
            mean_coverage=("coverage", "mean"),
            sd_coverage=("coverage", "std"),
            mean_interval_width=("mean_interval_width", "mean"),
        )
        .reset_index()
    )
    frontier = cost_frontier_summary(rows)
    expected = len(SCHEDULES) * len(SEEDS) * len(POLICY_VARIANTS)
    expected_keys = {
        (schedule, seed, policy)
        for schedule in SCHEDULES
        for seed in SEEDS
        for policy, _, _, _ in POLICY_VARIANTS
    }
    observed_keys = {(row["schedule"], row["seed"], row["policy"]) for row in rows}
    frontier_valid = (
        len(frontier) == len(SCHEDULES) * len(POLICY_VARIANTS)
        and frontier.pareto_efficient.notna().all()
        and all(
            frontier.loc[frontier.schedule == schedule, "pareto_efficient"].any()
            for schedule in SCHEDULES
        )
        and all(
            np.isfinite(frontier[column]).all()
            for column in frontier.columns
            if column.startswith("mean_")
        )
    )
    rows_valid = (
        frontier_valid
        and len(rows) == expected
        and observed_keys == expected_keys
        and all(
            row["protocol_passes"]
            and np.isfinite(row["mse"])
            and row["mse"] >= 0
            and np.isfinite(row["cumulative_squared_error"])
            and np.isfinite(row["training_seconds"])
            and row["training_seconds"] >= 0
            and np.isfinite(row["inference_seconds"])
            and row["inference_seconds"] >= 0
            and np.isfinite(row["adaptation_seconds"])
            and row["adaptation_seconds"] >= 0
            and np.isfinite(row["coverage"])
            and 0 <= row["coverage"] <= 1
            and np.isfinite(row["mean_interval_width"])
            and row["mean_interval_width"] >= 0
            and all(
                block["n"] >= 20
                and np.isfinite(block["coverage"])
                and 0 <= block["coverage"] <= 1
                and np.isfinite(block["mean_width"])
                and block["mean_width"] >= 0
                for block in row["coverage_by_test_block"]
            )
            and row["update_count"] <= row["update_budget"]
            for row in rows
        )
    )
    return {
        "description": "Five-seed fitted online adaptation using Ridge, random-forest, and histogram-gradient-boosting predictors with frozen, periodic, feedback-triggered, or validation-loss-triggered refitting; periodic or triggered residual-bias recalibration; and triggered normalized-gradient partial updates, fixed/rolling/exponential radii, four action slots and an action-specific compute budget, across four concept schedules.",
        "protocol": "Train, validation, and calibration labels are strictly available before the first test request. The validation-trigger threshold is fixed at the initial model's validation squared-error mean plus two validation standard deviations; it triggers when the rolling mean of 80 arrived test-feedback squared errors exceeds that threshold. During the test stream, learners receive requests and only labels yielded by timestamp-ordered replay. Equal-time requests precede feedback. Refit history contains only arrived labels. Every variant has at most four action slots and a 12-unit imposed compute budget. Recalibration updates only a scalar prediction bias from arrived signed residuals; partial update applies one normalized stochastic-gradient step to Ridge coefficients and intercept. Per-action resource costs are 1 unit for recalibration, 2 for partial update, 4 for Ridge refit, and 8 for either tree refit. Wall-clock model-fit, predict, and intervention times are recorded separately and are descriptive of this host. Cumulative squared error plus a price-weighted resource charge is evaluated at prespecified sensitivity prices 0, 0.1, 1, and 5; these prices are imposed controls, not application costs. Each schedule has a nondominated loss/resource frontier. Rolling- and exponentially weighted-radius arms keep their Ridge predictor update schedule identical to the fixed-radius triggered arm; residual scores enter only when labels arrive and use the forecast made earlier for that sample. Exponential score weights use label-availability times and an 80-step half-life, with one unit of test-point mass. Random forests use 32 trees, depth 6, leaf size 5; histogram gradient boosting uses 32 iterations, at most seven leaves, and leaf size 10. Both use fixed seeds.",
        "limitations": [
            "The trigger threshold and review period are fixed in advance; no parameter tuning uses test outcomes.",
            "Ridge, fixed random-forest, and histogram-gradient-boosting configurations are evaluated; hyperparameters are not tuned on test outcomes.",
            "Residual-bias recalibration and one normalized stochastic-gradient step are simple prespecified baselines; other recalibration and partial-update methods remain unevaluated.",
            "Action resource units are imposed relative costs; measured wall-clock times do not generalize beyond this host. All policies also retain a four-action ceiling.",
            "Rolling prequential radii and 100-request coverage blocks are descriptive and do not establish conditional, simultaneous, or online validity.",
            "Oracle irreducible MSE is evaluator-only; it is not exposed to the learner.",
            "Five seeds are descriptive replicates, not confidence intervals.",
        ],
        "configuration": {
            "n": 1600,
            "d": 4,
            "severity": 2.0,
            "noise": 0.3,
            "label_delay": 8,
            "missing_label_rate": 0.1,
            "train_fraction": 0.2,
            "validation_fraction": 0.1,
            "calibration_fraction": 0.2,
            "seeds": list(SEEDS),
            "policies": [
                {
                    "name": name,
                    "model_family": family,
                    "update_method": method,
                    "radius_method": radius,
                    "radius_half_life": 80 if radius == "exponential" else None,
                }
                for name, family, method, radius in POLICY_VARIANTS
            ],
            "update_budget": 4,
            "resource_budget": RESOURCE_BUDGET,
            "resource_cost_units": {
                "residual_bias_recalibration": 1.0,
                "normalized_sgd_partial_update": 2.0,
                "ridge_refit": 4.0,
                "random_forest_refit": 8.0,
                "hist_gradient_boosting_refit": 8.0,
            },
        },
        "schedule_overrides": SCHEDULES,
        "replicates": rows,
        "summary": summary.to_dict(orient="records"),
        "cost_frontier_summary": frontier.to_dict(orient="records"),
        "resource_price_grid_squared_error_units": list(RESOURCE_PRICE_GRID),
        "resource_price_interpretation": "Sensitivity analysis: objective is cumulative squared error plus declared price times imposed resource units; prices are research controls, not application costs.",
        "runtime_environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "scikit_learn": sklearn.__version__,
            "timing_scope": "Wall-clock fit, predict, and intervention durations; descriptive and host-dependent.",
        },
        "expected_records": expected,
        "observed_unique_records": len(observed_keys),
        "rows_valid": rows_valid,
        "checks_pass": rows_valid,
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/fitted_adaptation_validation.json")
    write_json(output, report)
    csv_path = output.with_suffix(".csv")
    pd.DataFrame(report["replicates"]).drop(
        columns=[
            "fit_audit",
            "intervention_audit",
            "coverage_by_test_block",
            "intervention_resource_costs",
        ]
    ).to_csv(csv_path, index=False)
    coverage_rows = []
    for row in report["replicates"]:
        for block in row["coverage_by_test_block"]:
            coverage_rows.append(
                {
                    key: row[key]
                    for key in ["schedule", "seed", "policy", "model_family", "radius_method"]
                }
                | block
            )
    coverage_csv = pd.DataFrame(coverage_rows).to_csv(index=False, lineterminator="\n")
    output.with_name("fitted_adaptation_window_coverage.csv").write_bytes(
        coverage_csv.encode("utf-8")
    )
    frontier = pd.DataFrame(report["cost_frontier_summary"])
    frontier.to_csv(output.with_name("fitted_adaptation_cost_frontier.csv"), index=False)
    plot_cost_frontier(
        frontier,
        output.with_name("fitted_adaptation_cost_frontier.png"),
    )
    print(f"records={len(report['replicates'])} passed={report['checks_pass']}")
    print(output)
    if not report["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
