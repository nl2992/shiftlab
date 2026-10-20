import numpy as np
import pandas as pd

from scripts.time_series_real_diagnostics import _diagnostic_partitions


def _frame():
    return pd.DataFrame(
        {
            "split": [
                "train",
                "train",
                "calibration",
                "calibration",
                "calibration",
                "test",
                "test",
            ],
            "target": np.arange(7, dtype=float),
            "event_time": np.arange(7, dtype=float),
            "feature_available_time": [0, 1, 2, 4, 4, 5, 7],
            "prediction_time": [0, 1, 2, 3, 4, 5, 6],
            "label_available_time": [1, 2, 3, 4, 5, 8, 9],
        }
    )


def test_known_calibration_and_preprocessing_inputs_respect_strict_availability():
    train, calibration, test, protocol = _diagnostic_partitions(_frame())
    assert train.index.tolist() == [0]
    assert calibration.index.tolist() == [2]
    assert test.index.tolist() == [5]
    assert protocol["mode"] == "strict_known_availability"
    assert protocol["train_fit_cutoff"] == 2
    assert protocol["test_prediction_cutoff"] == 5
    assert protocol["strict_label_availability_filter"] is True


def test_unknown_calibration_times_are_explicitly_retrospective():
    frame = _frame()
    frame["label_available_time"] = np.nan
    train, calibration, test, protocol = _diagnostic_partitions(frame)
    assert train.index.tolist() == [0, 1]
    assert calibration.index.tolist() == [2, 3, 4]
    assert test.index.tolist() == [5, 6]
    assert protocol["mode"] == "retrospective_event_time_splits"
    assert protocol["strict_label_availability_filter"] is False
    assert "unknown" in protocol["reason"]
