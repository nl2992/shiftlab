import numpy as np
import torch

import scripts.evaluate_eia_retraining_frontier as runner
from scripts.evaluate_eia_retraining_frontier import (
    _fit_ridge,
    _predict,
    _simulate_policy,
)


def test_gpu_or_cpu_ridge_reproduces_a_linear_signal():
    rng = np.random.default_rng(12)
    x = rng.normal(size=(200, 4))
    y = 3.0 + x @ np.array([2.0, -1.0, 0.5, 4.0])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _fit_ridge(x, y, device)
    prediction = _predict(model, x)
    assert np.sqrt(np.mean(np.square(y - prediction))) < 0.1


def test_test_labels_enter_feedback_only_after_target_time_plus_delay():
    rng = np.random.default_rng(15)
    x_train = rng.normal(size=(80, 4))
    weights = np.array([1.5, -0.5, 0.75, 2.0])
    y_train = 1.0 + x_train @ weights + rng.normal(scale=0.01, size=80)
    x_cal = rng.normal(size=(80, 4))
    y_cal = 1.0 + x_cal @ weights + rng.normal(scale=0.01, size=80)
    test_n = 50
    x_test = rng.normal(size=(test_n, 4))
    y_test = 1.0 + x_test @ weights + rng.normal(scale=0.01, size=test_n)
    first_test_time = 2_000_000.0
    test_time = first_test_time + np.arange(test_n) * 3600
    label_time = test_time + 3600
    cal_time = first_test_time - (np.arange(80, 0, -1) + 200) * 3600
    train_label_time = first_test_time - (np.arange(80, 0, -1) + 200) * 3600
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _, no_delay = _simulate_policy(
        policy="frozen",
        delay_hours=0,
        x=x_test,
        y=y_test,
        event_time=test_time,
        label_event_time=label_time,
        train_x=x_train,
        train_y=y_train,
        train_label_event_time=train_label_time,
        calibration_x=x_cal,
        calibration_y=y_cal,
        calibration_time=cal_time,
        device=device,
    )
    _, one_day = _simulate_policy(
        policy="frozen",
        delay_hours=24,
        x=x_test,
        y=y_test,
        event_time=test_time,
        label_event_time=label_time,
        train_x=x_train,
        train_y=y_train,
        train_label_event_time=train_label_time,
        calibration_x=x_cal,
        calibration_y=y_cal,
        calibration_time=cal_time,
        device=device,
    )
    assert no_delay["matured_test_feedback_by_test_end"] == 49
    assert one_day["matured_test_feedback_by_test_end"] == 25


def test_weekly_refit_uses_only_feedback_matured_by_the_refit_time(monkeypatch):
    rng = np.random.default_rng(22)
    x_train = rng.normal(size=(80, 4))
    y_train = 2.0 + x_train[:, 0] - x_train[:, 2]
    x_cal = rng.normal(size=(80, 4))
    y_cal = 2.0 + x_cal[:, 0] - x_cal[:, 2]
    test_n = 200
    x_test = rng.normal(size=(test_n, 4))
    y_test = 2.0 + x_test[:, 0] - x_test[:, 2]
    first_test_time = 4_000_000.0
    test_time = first_test_time + np.arange(test_n) * 3600
    label_time = test_time + 3600
    old_time = first_test_time - (np.arange(80, 0, -1) + 300) * 3600
    fit_sizes = []
    original_fit = runner._fit_ridge

    def recording_fit(x, y, device):
        fit_sizes.append(len(y))
        return original_fit(x, y, device)

    monkeypatch.setattr(runner, "_fit_ridge", recording_fit)
    for delay, expected_new_rows in ((0, 168), (24, 144)):
        fit_sizes.clear()
        runner._simulate_policy(
            policy="weekly",
            delay_hours=delay,
            x=x_test,
            y=y_test,
            event_time=test_time,
            label_event_time=label_time,
            train_x=x_train,
            train_y=y_train,
            train_label_event_time=old_time,
            calibration_x=x_cal,
            calibration_y=y_cal,
            calibration_time=old_time,
            device=torch.device("cpu"),
        )
        assert fit_sizes == [80, 80 + expected_new_rows]
