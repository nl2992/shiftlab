"""Evaluate fitted update policies using only timestamped arrived feedback."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from shiftlab.data.label_availability import labels_available_before
from shiftlab.data.provenance import commit, sha256, source_hash, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.streaming import Label, Request, replay
from shiftlab.data.synthetic import generate_chunks
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
POLICIES = ("frozen", "periodic", "triggered")


def initial_rows(frame: pd.DataFrame, split: str, cutoff: float) -> pd.DataFrame:
    """Select rows whose features and labels predate the first test request."""
    available = labels_available_before(frame, cutoff)
    features_known = frame.feature_available_time.notna() & (frame.feature_available_time < cutoff)
    return frame.loc[(frame.split == split) & available & features_known].sort_values(
        "prediction_time", kind="stable"
    )


class AuditedLearner(Learner):
    """Record the arrived-feedback boundary that caused each sequential refit."""

    def __init__(self, *args, **kwargs):
        self.current_feedback_time: int | float | None = None
        self.fit_audit: list[dict[str, int | float | str]] = []
        super().__init__(*args, **kwargs)

    def _fit(self, X, y):
        super()._fit(X, y)
        if self.current_feedback_time is not None:
            self.fit_audit.append(
                {
                    "fit_feedback_available_time": self.current_feedback_time,
                    "arrived_feedback_count": self.feedback_count,
                    "method": self.method,
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
    calibration = initial_rows(frame, "calibration", first_test)
    if len(train) < 20 or len(calibration) < 20:
        raise ValueError(f"Insufficient arrived initial data for {schedule}, seed {seed}")
    settings = SimpleNamespace(window=80, alpha=0.1, threshold=5.0, period=50, budget=4)
    test_ids = test.sample_id.to_numpy()
    targets = test.set_index("sample_id").target
    prediction_time_by_id = test.set_index("sample_id").prediction_time
    oracle_by_id = oracle.set_index(frame.sample_id).loc[test_ids]
    arrived_times = set(test.label_available_time.dropna().astype(float).tolist())
    records = []
    for policy in POLICIES:
        learner = AuditedLearner(
            np.stack(train.features.to_numpy()),
            train.target.to_numpy(dtype=float),
            np.stack(calibration.features.to_numpy()),
            calibration.target.to_numpy(dtype=float),
            settings,
            policy,
        )
        pending: dict[str, tuple[tuple[float, ...], float]] = {}
        predictions: dict[str, float] = {}
        for event in replay(test):
            if isinstance(event, Request):
                observation = Observation(int(event.prediction_time), event.features)
                prediction, _ = learner.predict(observation)
                pending[event.sample_id] = (event.features, prediction)
                predictions[event.sample_id] = prediction
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
        oracle_noise = oracle_by_id.sigma.to_numpy(dtype=float) ** 2
        known_change = oracle_by_id.weight.to_numpy(dtype=float) > 0
        fit_times = [float(row["fit_feedback_available_time"]) for row in learner.fit_audit]
        records.append(
            {
                "schedule": schedule,
                "seed": seed,
                "policy": policy,
                "test_n": len(test),
                "mse": float(np.mean(residual**2)),
                "oracle_irreducible_mse": float(np.mean(oracle_noise)),
                "excess_mse_over_oracle": float(np.mean(residual**2 - oracle_noise)),
                "shifted_or_transition_mse": float(np.mean(residual[known_change] ** 2))
                if known_change.any()
                else float("nan"),
                "update_count": len(learner.interventions),
                "update_times": [int(value) for value in learner.interventions],
                "update_budget": settings.budget,
                "feedback_received": learner.feedback_count,
                "feedback_missing_or_delayed_past_horizon": int(
                    test.target.notna().sum() - learner.feedback_count
                ),
                "trigger_alarm_count": len(learner.alarms["error_cusum"]),
                "fit_audit": learner.fit_audit,
                "protocol_passes": bool(
                    len(learner.interventions) <= settings.budget
                    and len(learner.fit_audit) == len(learner.interventions)
                    and all(value in arrived_times for value in fit_times)
                    and all(value <= float(test.prediction_time.max()) for value in fit_times)
                    and fit_times == sorted(fit_times)
                    and all(
                        row["arrived_feedback_count"] <= learner.feedback_count
                        for row in learner.fit_audit
                    )
                    and len(predictions) == len(test)
                    and test.target.notna().sum() >= learner.feedback_count
                    and all(
                        row["fit_feedback_available_time"] in learner.interventions
                        for row in learner.fit_audit
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
        )
        .reset_index()
    )
    expected = len(SCHEDULES) * len(SEEDS) * len(POLICIES)
    expected_keys = {
        (schedule, seed, policy) for schedule in SCHEDULES for seed in SEEDS for policy in POLICIES
    }
    observed_keys = {(row["schedule"], row["seed"], row["policy"]) for row in rows}
    rows_valid = (
        len(rows) == expected
        and observed_keys == expected_keys
        and all(
            row["protocol_passes"]
            and np.isfinite(row["mse"])
            and row["mse"] >= 0
            and row["update_count"] <= row["update_budget"]
            for row in rows
        )
    )
    return {
        "description": "Five-seed fitted online adaptation using frozen, periodic, and residual-CUSUM-triggered Ridge policies across four concept schedules.",
        "protocol": "Train and calibration labels are strictly available before the first test request. During the test stream, learners receive requests and only labels yielded by timestamp-ordered replay. Equal-time requests precede feedback. Refit history contains only arrived labels. Every policy has a four-update compute budget.",
        "limitations": [
            "The trigger threshold and review period are fixed in advance; no parameter tuning uses test outcomes.",
            "Only one fitted model family (Ridge) and synthetic squared loss are evaluated.",
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
            "policies": list(POLICIES),
            "update_budget": 4,
        },
        "schedule_overrides": SCHEDULES,
        "replicates": rows,
        "summary": summary.to_dict(orient="records"),
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
    pd.DataFrame(report["replicates"]).drop(columns="fit_audit").to_csv(csv_path, index=False)
    print(f"records={len(report['replicates'])} passed={report['checks_pass']}")
    print(output)
    if not report["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
