"""Explicit supervised tasks constructed from evaluator-owned arrays."""

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np


@dataclass(frozen=True)
class TaskSpec:
    name: str
    kind: str
    definition: str
    label_availability_rule: str


TASKS = {
    "multi_step": TaskSpec(
        "multi_step",
        "regression",
        "vector of future values for every step in a prespecified forecast horizon",
        "all requested target steps plus their measured release lags",
    ),
    "regression": TaskSpec(
        "regression",
        "regression",
        "future value at fixed horizon",
        "target event plus measured release lag",
    ),
    "quantile": TaskSpec(
        "quantile",
        "regression",
        "same response, evaluated by pinball loss at a prespecified quantile",
        "target event plus measured release lag",
    ),
    "volatility": TaskSpec(
        "volatility",
        "regression",
        "RMS first differences over the entire future horizon",
        "last future outcome and all constituent observations available",
    ),
    "rare_magnitude": TaskSpec(
        "rare_magnitude",
        "regression",
        "positive excess above a fixed threshold at the target horizon; zero otherwise",
        "target event plus measured release lag",
    ),
    "binary": TaskSpec(
        "binary",
        "classification",
        "future value exceeds a fixed threshold",
        "target event plus measured release lag",
    ),
    "exceedance": TaskSpec(
        "exceedance",
        "classification",
        "future threshold exceedance",
        "target event plus measured release lag",
    ),
    "rare_event": TaskSpec(
        "rare_event",
        "classification",
        "exceedance of a threshold selected without test labels",
        "target event plus measured release lag",
    ),
    "multiclass": TaskSpec(
        "multiclass",
        "classification",
        "future value falls in prespecified ordered bins",
        "target event plus measured release lag",
    ),
}


def finite_real_parameter(value, name: str, *, positive=False, nonnegative=False) -> float:
    """Validate a scalar numeric configuration value before converting it to float."""
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Real)
        or not np.isfinite(float(value))
    ):
        raise ValueError(f"{name} must be a finite real number")
    value = float(value)
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def integer_parameter(value, name: str, *, minimum=None, maximum=None) -> int:
    """Validate an integer configuration value without bool/float/string coercion."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def dataset_task_specs(dataset: str, config: dict) -> list[dict]:
    """Return manifest-ready task, horizon, label-mask, metric, and utility contracts.

    These describe the exported target. They do not imply that source release or feature
    availability is known when a source only supplies retrospective timestamps.
    """
    none_utility = "No application-grounded decision utility; evaluate with named task metrics."
    finite_mask = "target is finite; rows with missing target are excluded from metric computation"
    if dataset == "opsd":
        frequency = config.get("frequency", "hourly")
        unit = {"hourly": "hours", "daily": "days"}.get(frequency)
        if unit is None:
            raise ValueError("OPSD task frequency must be hourly or daily")
        return [
            {
                "task_id": "next_period_load_regression",
                "task_kind": "regression",
                "target_definition": f"next-period value of {config.get('target_column', 'configured target column')}",
                "forecast_horizon": {
                    "value": 1,
                    "unit": unit,
                    "event_semantics": "target event is the end of the next hourly observation or complete UTC day",
                },
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["MAE", "RMSE", "pinball loss at prespecified quantiles"],
                "label_availability_rule": "unknown; retrospective event-time target only",
                "utility_provenance": none_utility,
            }
        ]
    if dataset == "noaa":
        return [
            {
                "task_id": "next_station_observation_temperature",
                "task_kind": "regression",
                "target_definition": "temperature at the next strictly later source report for the same station",
                "forecast_horizon": {
                    "value": "per row",
                    "unit": "seconds",
                    "event_semantics": "variable gap recorded in label_event_time minus event_time; not a fixed hourly horizon",
                },
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["MAE", "RMSE", "interval score at prespecified coverage"],
                "label_availability_rule": "unknown; target event time does not establish report release time",
                "utility_provenance": none_utility,
            }
        ]
    if dataset == "monash":
        dataset_name = config.get("dataset", "local_tsf")
        official_m4_horizons = {"m4_hourly": 48, "m4_daily": 14, "m4_weekly": 13}
        horizon = (
            integer_parameter(config["forecast_horizon"], "forecast_horizon", minimum=1)
            if "forecast_horizon" in config
            else official_m4_horizons.get(dataset_name, "per-series @horizon")
        )
        horizon_source = config.get("forecast_horizon_source", "TSF @horizon when declared")
        return [
            {
                "task_id": f"{dataset_name}_official_fixed_origin_forecast",
                "task_kind": "regression",
                "target_definition": "official final-horizon series values; one shared training-only origin per series",
                "forecast_horizon": {
                    "value": horizon,
                    "unit": "steps",
                    "event_semantics": f"fixed-origin holdout; forecast_step ranges from one to {horizon}; horizon source: {horizon_source}",
                },
                "valid_target_mask": "finite future target; missing holdout steps remain masked and are not imputed",
                "evaluation_metrics": ["MAE", "RMSE", "sMAPE when denominator is nonzero"],
                "label_availability_rule": "official retrospective holdout; publication time unknown",
                "utility_provenance": none_utility,
            }
        ]
    if dataset == "eia":
        raw_horizon = config.get("horizon", 1)
        if (
            isinstance(raw_horizon, (bool, np.bool_))
            or not isinstance(raw_horizon, (int, np.integer))
            or raw_horizon < 1
        ):
            raise ValueError("EIA horizon must be a positive integer number of hours")
        horizon = int(raw_horizon)
        return [
            {
                "task_id": "next_period_eia_regression",
                "task_kind": "regression",
                "target_definition": f"future value of configured EIA type {config.get('target', 'D')}",
                "forecast_horizon": {
                    "value": horizon,
                    "unit": "hours",
                    "event_semantics": "only exact calendar gaps of horizon hours are retained",
                },
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["MAE", "RMSE", "pinball loss at prespecified quantiles"],
                "label_availability_rule": "unknown; historical measurements or forecasts may be revised",
                "utility_provenance": none_utility,
            }
        ]
    if dataset == "binance":
        interval = config.get("interval", "1d")
        return [
            {
                "task_id": "next_bar_close_return",
                "task_kind": "regression",
                "target_definition": "next bar close divided by current bar close minus one",
                "forecast_horizon": {
                    "value": 1,
                    "unit": "bar",
                    "bar_interval": interval,
                    "event_semantics": "label_event_time is the next bar close; current OHLCV requires bar close",
                },
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["MAE", "RMSE", "directional accuracy as a secondary metric"],
                "label_availability_rule": "historical bar close time known; publication latency unknown",
                "utility_provenance": "No trading utility or transaction-cost model; returns are not profit or executable performance.",
            }
        ]
    if dataset in {"criteo", "criteo_attribution"}:
        window = finite_real_parameter(
            config.get("outcome_window_days", 30), "Criteo outcome_window_days", positive=True
        )
        target = "conversion" if dataset == "criteo_attribution" else "sale"
        return [
            {
                "task_id": (
                    "display_conversion_within_30_days"
                    if dataset == "criteo_attribution"
                    else "conversion_within_followup_window"
                ),
                "task_kind": "binary_classification",
                "target_definition": f"{target} within the configured outcome follow-up window",
                "forecast_horizon": {
                    "value": window,
                    "unit": "days",
                    "event_semantics": "positive conversion event time uses click plus delay; a negative requires complete follow-up",
                },
                "valid_target_mask": "label_available_time is finite; incomplete negative follow-up remains unlabeled",
                "evaluation_metrics": ["log loss", "Brier score", "AUROC", "AUPRC"],
                "label_availability_rule": "conversion event plus configured, README-verified delay unit; negative labels require full follow-up",
                "utility_provenance": none_utility,
            }
        ]
    if dataset == "gas_sensor":
        return [
            {
                "task_id": "gas_type_multiclass",
                "task_kind": "multiclass_classification",
                "target_definition": "source gas class label; ten batches are coarse domains, within-batch order is unknown",
                "forecast_horizon": None,
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["accuracy", "macro-F1", "multiclass log loss"],
                "label_availability_rule": "offline source label; no temporal release protocol",
                "utility_provenance": "No application decision costs; class errors are scored as classification metrics.",
            }
        ]
    if dataset == "folktables":
        task = config.get("tasks", ["ACSIncome"])[0]
        return [
            {
                "task_id": f"folktables_{task}",
                "task_kind": "binary_classification",
                "target_definition": f"official {task} target and transformation, captured with source code in acs_protocol.json",
                "forecast_horizon": None,
                "valid_target_mask": "rows retained by the official task preprocessing and target transform",
                "evaluation_metrics": ["accuracy", "balanced accuracy", "Brier score", "log loss"],
                "label_availability_rule": "annual ACS survey domain; unordered individual records and no release-time claim",
                "utility_provenance": "No application-grounded decision utility; any cost-weighted diagnostic is explicitly imposed and separate.",
            }
        ]
    if dataset == "wilds":
        name = config.get("dataset", "civilcomments")
        return [
            {
                "task_id": f"wilds_{name}_official_classification",
                "task_kind": "official_classification",
                "target_definition": f"official {name} label; authoritative task metric is dataset.eval",
                "forecast_horizon": None,
                "valid_target_mask": "officially labeled rows in retained official partitions",
                "evaluation_metrics": ["official dataset.eval metric and group breakdown"],
                "label_availability_rule": "official train/validation/test partition; no individual-time availability",
                "utility_provenance": "No temporal decision utility; use the official WILDS task metric.",
            }
        ]
    if dataset == "fred":
        return [
            {
                "task_id": "vintage_revision_event_table",
                "task_kind": "source_table_not_forecast_task",
                "target_definition": "dated FRED observation/revision with ALFRED realtime_start and realtime_end",
                "forecast_horizon": None,
                "valid_target_mask": finite_mask,
                "evaluation_metrics": [],
                "label_availability_rule": "conservative end-of-realtime_start UTC day; exact release instant unknown",
                "utility_provenance": "Not applicable until an explicit as-of forecasting task and utility are specified.",
            }
        ]
    if dataset == "licensed_local":
        return [
            {
                "task_id": config.get("task_id", "licensed_local_user_defined"),
                "task_kind": config.get("task_kind", "user_defined_numeric_target"),
                "target_definition": f"user-specified target column {config.get('target_column', 'unspecified')}",
                "forecast_horizon": config.get("forecast_horizon"),
                "valid_target_mask": finite_mask,
                "evaluation_metrics": config.get("evaluation_metrics", []),
                "label_availability_rule": "user-mapped; null where the source supplies no verified availability field",
                "utility_provenance": config.get(
                    "utility_provenance", "Not supplied; no application decision utility claimed."
                ),
            }
        ]
    if dataset == "synthetic":
        classification = config.get("scenario") in {
            "nonlinear_classification",
            "prior_shift",
            "imbalance",
            "label_corruption",
            "boundary_rotation",
            "small_decision_covariate",
            "rare_high_cost",
        }
        return [
            {
                "task_id": f"synthetic_{config.get('scenario', 'iid_regression')}",
                "task_kind": "classification" if classification else "regression",
                "target_definition": "known synthetic DGP target; exact evaluator oracle remains separate",
                "forecast_horizon": None,
                "valid_target_mask": finite_mask,
                "evaluation_metrics": ["oracle risk", "task-appropriate prediction metrics"],
                "label_availability_rule": "simulation feedback delay and missingness configuration",
                "utility_provenance": "Synthetic imposed utility only; not application-grounded.",
            }
        ]
    return [
        {
            "task_id": "unspecified_numeric_target",
            "task_kind": "unspecified",
            "target_definition": "No dataset task binding is registered for this source.",
            "forecast_horizon": None,
            "valid_target_mask": finite_mask,
            "evaluation_metrics": [],
            "label_availability_rule": "unknown",
            "utility_provenance": "Not specified.",
        }
    ]


def forecast_task(
    values, horizon=1, lookback=4, task="regression", threshold=0.0, class_boundaries=None
):
    """No future-valued features. Label index is returned for availability mapping.

    Volatility is future RMS first differences, not a claim about latent economic risk.
    Quantile forecasting uses the same response with a quantile loss at evaluation.
    ``task="multi_step"`` delegates to the fixed-origin vector builder and returns a target
    matrix with per-step outcome indices.
    """
    if task not in TASKS:
        raise ValueError(f"Unknown forecast task {task!r}; choices={list(TASKS)}")
    if task == "multi_step":
        return multi_step_forecast_task(values, horizon=horizon, lookback=lookback)
    values = np.asarray(values, dtype=float)
    if values.ndim != 1:
        raise ValueError("values must be a one-dimensional series")
    if np.isinf(values).any():
        raise ValueError("values must be finite or missing")
    if (
        isinstance(horizon, bool)
        or not isinstance(horizon, (int, np.integer))
        or horizon < 1
        or isinstance(lookback, bool)
        or not isinstance(lookback, (int, np.integer))
        or lookback < 1
    ):
        raise ValueError("horizon and lookback must be positive integers")
    if task in {"binary", "exceedance", "rare_event", "rare_magnitude"} and not np.isfinite(
        threshold
    ):
        raise ValueError("threshold must be finite")
    if len(values) < horizon + lookback:
        raise ValueError("Insufficient series for horizon and lookback")
    index = np.arange(lookback - 1, len(values) - horizon)
    X = np.stack([values[i - lookback + 1 : i + 1] for i in index])
    y = values[index + horizon]
    if task in ["binary", "exceedance", "rare_event"]:
        y = np.where(np.isnan(y), np.nan, (y > threshold).astype(float))
    elif task == "multiclass":
        bins = np.asarray(class_boundaries, dtype=float)
        if (
            bins.ndim != 1
            or not len(bins)
            or not np.isfinite(bins).all()
            or not np.all(np.diff(bins) > 0)
        ):
            raise ValueError(
                "Multiclass bins must be explicitly supplied, finite and strictly increasing; never fit them on test outcomes"
            )
        y = np.where(np.isnan(y), np.nan, np.digitize(y, bins).astype(float))
    elif task == "rare_magnitude":
        y = np.maximum(y - threshold, 0)
    elif task == "volatility":
        y = np.array([np.sqrt(np.mean(np.diff(values[i : i + horizon + 1]) ** 2)) for i in index])
    elif task not in ["regression", "quantile", "rare_magnitude"]:
        raise ValueError("Unsupported task")
    return X, y, index, index + horizon


def multi_step_forecast_task(values, horizon=3, lookback=4):
    """Construct fixed-origin forecasts for every step through ``horizon``.

    Returns past-only feature windows, an ``(n_samples, horizon)`` target matrix, origin
    indices, and matching per-target outcome indices. Missing target values remain NaN so
    callers can retain a per-step validity mask with ``np.isfinite(targets)``. The entire
    vector task is available only once its final requested outcome and release lag arrive.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1:
        raise ValueError("values must be a one-dimensional series")
    if np.isinf(values).any():
        raise ValueError("values must be finite or missing")
    if (
        isinstance(horizon, bool)
        or not isinstance(horizon, (int, np.integer))
        or horizon < 1
        or isinstance(lookback, bool)
        or not isinstance(lookback, (int, np.integer))
        or lookback < 1
    ):
        raise ValueError("horizon and lookback must be positive integers")
    if len(values) < horizon + lookback:
        raise ValueError("Insufficient series length for horizon and lookback")
    origin = np.arange(lookback - 1, len(values) - horizon)
    offsets = np.arange(1, horizon + 1)
    X = np.stack([values[i - lookback + 1 : i + 1] for i in origin])
    outcome_indices = origin[:, None] + offsets[None, :]
    targets = values[outcome_indices]
    return X, targets, origin, outcome_indices


def quantile_loss(target, prediction, quantile=0.9):
    if not 0 < quantile < 1:
        raise ValueError("quantile must lie in (0,1)")
    error = np.asarray(target) - np.asarray(prediction)
    return np.maximum(quantile * error, (quantile - 1) * error)
