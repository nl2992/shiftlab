"""Evaluator for frozen fitted binary policies on synthetic decision stress cases."""

import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .generators import generate_chunks
from .presets import DecisionStressPreset


def fit_frozen_binary_policy(
    frame: pd.DataFrame,
    *,
    first_prediction_time: float,
    fallback_fn_cost: float = 1.0,
    fallback_fp_cost: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Fit on arrived training outcomes and act using only features and declared context.

    The returned event probabilities and actions do not use test targets or evaluator fields.
    Missing decision context uses the declared fallback utility, which is useful for measuring
    non-identifiability when the true utility is deliberately hidden.
    """
    if fallback_fn_cost <= 0 or fallback_fp_cost <= 0:
        raise ValueError("Fallback costs must be positive")
    available = frame.label_available_time.notna() & (
        frame.label_available_time < first_prediction_time
    )
    train_mask = (frame.split == "train") & available & frame.target.notna()
    train = frame.loc[train_mask]
    test = frame.loc[(frame.split == "test") & frame.target.notna()]
    if not len(train) or not len(test):
        raise ValueError("Need arrived training outcomes and labeled test rows")

    X_train = np.stack(train.features.to_numpy())
    y_train = (train.target.to_numpy(dtype=float) > 0).astype(int)
    X_test = np.stack(test.features.to_numpy())
    unique = np.unique(y_train)
    if len(unique) == 1:
        # Laplace smoothing prevents a zero probability while preserving a train-only fit.
        event_probability = np.full(len(test), (y_train.sum() + 0.5) / (len(y_train) + 1))
        model_name = "laplace_smoothed_training_prevalence"
    else:
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=1.0, max_iter=500, random_state=0),
        )
        model.fit(X_train, y_train)
        event_probability = model.predict_proba(X_test)[:, 1]
        model_name = "training_only_standardized_logistic_regression"

    contexts = test.decision_context.to_numpy()
    fn_cost = np.full(len(test), fallback_fn_cost, dtype=float)
    fp_cost = np.full(len(test), fallback_fp_cost, dtype=float)
    feasible = np.ones(len(test), dtype=bool)
    context_observed = np.zeros(len(test), dtype=bool)
    for i, value in enumerate(contexts):
        if value is None or pd.isna(value):
            continue
        context = json.loads(value) if isinstance(value, str) else value
        fn_cost[i] = float(context.get("fn", fallback_fn_cost))
        fp_cost[i] = float(context.get("fp", fallback_fp_cost))
        feasible[i] = bool(context.get("action_1_feasible", True))
        context_observed[i] = True
    action = event_probability >= fp_cost / (fp_cost + fn_cost)
    action &= feasible
    audit = {
        "model": model_name,
        "n_train": len(train),
        "n_test": len(test),
        "first_test_prediction_time": float(first_prediction_time),
        "max_training_label_available_time": float(train.label_available_time.max()),
        "training_positive_rate": float(y_train.mean()),
        "test_ids": test.sample_id.to_numpy(),
        "test_target": test.target.to_numpy(dtype=float),
        "test_regime_id": test.regime_id.to_numpy(),
        "test_probability": event_probability,
        "test_action": action,
        "test_context_observed": context_observed,
        "test_policy_fn_cost": fn_cost,
        "test_policy_fp_cost": fp_cost,
        "test_feasible": feasible,
    }
    return event_probability, action, audit


def evaluate_fitted_decision_preset(preset: DecisionStressPreset, *, seed: int) -> list[dict]:
    """Evaluate a single frozen policy, separating learner inputs from evaluator scoring."""
    config = preset.config.model_copy(update={"seed": seed, "device": "cpu"})
    frames, oracles = zip(*generate_chunks(config), strict=True)
    frame = pd.concat(frames, ignore_index=True)
    oracle = pd.concat(oracles, ignore_index=True)
    test_mask = frame.split.eq("test")
    if not test_mask.any():
        raise ValueError(f"{preset.name}: no test requests")
    first_test_time = float(frame.loc[test_mask, "prediction_time"].min())
    probability, action, audit = fit_frozen_binary_policy(
        frame, first_prediction_time=first_test_time
    )
    oracle_test = oracle.set_index("sample_id").loc[audit["test_ids"]]
    # Regime annotations are joined only after fitted predictions are fixed; they are evaluator-only.
    audit["test_regime_id"] = oracle_test.regime_id.to_numpy()
    target = audit["test_target"]
    event = target > 0
    # Score against actual evaluator utilities, including those intentionally hidden from the policy.
    actual_fn_cost = oracle_test.fn_cost.to_numpy(dtype=float)
    actual_fp_cost = np.ones(len(action), dtype=float)
    policy_fn_cost = audit["test_policy_fn_cost"]
    risk = np.where(
        action,
        actual_fp_cost * (1 - oracle_test.probability_positive),
        actual_fn_cost * oracle_test.probability_positive,
    )
    realized = np.where(action, actual_fp_cost * ~event, actual_fn_cost * event).astype(float)
    oracle_action = oracle_test.oracle_action.to_numpy(dtype=bool)
    oracle_risk = oracle_test.oracle_risk.to_numpy(dtype=float)
    regime = audit["test_regime_id"]
    records = []
    for name in ["all", *sorted(set(regime))]:
        selected = np.ones(len(regime), dtype=bool) if name == "all" else regime == name
        p = oracle_test.probability_positive.to_numpy()[selected]
        records.append(
            {
                "preset": preset.name,
                "scenario": config.scenario,
                "seed": seed,
                "regime": name,
                "model": audit["model"],
                "n_train": audit["n_train"],
                "n_test": int(selected.sum()),
                "first_test_prediction_time": first_test_time,
                "max_training_label_available_time": audit["max_training_label_available_time"],
                "training_positive_rate": audit["training_positive_rate"],
                "test_positive_rate": float(event[selected].mean()),
                "fitted_action_rate": float(action[selected].mean()),
                "oracle_action_rate": float(oracle_action[selected].mean()),
                "brier_score": float(np.mean((probability[selected] - event[selected]) ** 2)),
                "mean_realized_cost": float(realized[selected].mean()),
                "mean_fitted_expected_cost": float(risk[selected].mean()),
                "mean_oracle_expected_cost": float(oracle_risk[selected].mean()),
                "mean_decision_regret": float(np.mean(risk[selected] - oracle_risk[selected])),
                "mean_actual_fn_cost": float(actual_fn_cost[selected].mean()),
                "mean_policy_fn_cost": float(policy_fn_cost[selected].mean()),
                "fraction_using_declared_context": float(
                    audit["test_context_observed"][selected].mean()
                ),
                "mean_oracle_positive_probability": float(p.mean()),
            }
        )
    return records
