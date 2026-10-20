import numpy as np
import pandas as pd

from scripts.evaluate_sequential_adaptation import initial_rows


def test_initial_adaptation_labels_require_strictly_earlier_known_availability():
    frame = pd.DataFrame(
        {
            "split": ["train", "train", "train", "calibration"],
            "prediction_time": [0, 1, 2, 3],
            "feature_available_time": [0, 1, 5, np.nan],
            "label_available_time": [4, 5, np.nan, 5],
            "target": [1.0, 2.0, 3.0, 4.0],
        }
    )
    eligible = initial_rows(frame, "train", cutoff=5)
    assert eligible.prediction_time.tolist() == [0]

    eligible_calibration = initial_rows(frame, "calibration", cutoff=5)
    assert eligible_calibration.empty
