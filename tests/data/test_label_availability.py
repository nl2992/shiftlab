import numpy as np
import pandas as pd

from shiftlab.data.chronological_splits import purge_unavailable_labels as legacy_purge
from shiftlab.data.label_availability import (
    labels_available_before,
    labels_available_by,
    purge_unavailable_labels,
)


def test_label_cutoffs_distinguish_strict_arrival_from_same_time_feedback():
    frame = pd.DataFrame(
        {
            "label_available_time": [np.nan, 3.0, 4.0, 5.0, 6.0],
            "target": [1.0, 1.0, np.nan, 1.0, 0.0],
        }
    )
    assert labels_available_before(frame, 5.0).tolist() == [False, True, False, False, False]
    assert labels_available_by(frame, 5.0).tolist() == [False, True, False, True, False]


def test_purge_remains_import_compatible_and_preserves_unknown_availability():
    frame = pd.DataFrame(
        {
            "split": ["train", "train", "validation", "calibration", "test"],
            "prediction_time": [1.0, 2.0, 3.0, 4.0, 5.0],
            "label_available_time": [np.nan, 3.0, 4.0, 5.0, 5.0],
        }
    )
    result = purge_unavailable_labels(frame)
    assert result.equals(legacy_purge(frame))
    assert result.split.tolist() == ["train", "unassigned", "unassigned", "unassigned", "test"]
    assert np.isnan(result.label_available_time.iloc[0])
