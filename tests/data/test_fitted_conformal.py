import numpy as np

from scripts.validate_fitted_conformal import _adaptive_test_predictions, _arrived_prior_scores
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


def test_prequential_scores_require_prediction_and_label_to_precede_request():
    scores = _arrived_prior_scores(
        now=10.0,
        calibration_residual=np.array([1.0, 2.0, 3.0]),
        calibration_prediction_time=np.array([0.0, 0.0, 11.0]),
        calibration_available=np.array([4.0, 10.0, 5.0]),
        prior_test_residual=np.array([7.0, 8.0]),
        prior_test_prediction_time=np.array([8.0, 9.0]),
        prior_test_available=np.array([9.0, 10.0]),
    )
    assert np.array_equal(scores, np.array([1.0, 7.0]))


def test_adaptive_refits_use_only_strictly_arrived_train_and_prior_test_labels():
    frame, _ = next(
        generate_chunks(SyntheticConfig(n=1200, scenario="iid_regression", delay=5, seed=91))
    )
    y = frame.target.to_numpy(dtype=float)
    X = np.stack(frame.features.to_numpy())
    prediction_time = frame.prediction_time.to_numpy(dtype=float)
    available = frame.label_available_time.to_numpy(dtype=float)
    split = frame.split.to_numpy()
    test_indices = np.flatnonzero((split == "test") & np.isfinite(y))
    prediction, audit = _adaptive_test_predictions(
        X, y, prediction_time, available, split, test_indices, update_period=25
    )
    assert len(prediction) == len(test_indices)
    assert len(audit) == int(np.ceil(len(test_indices) / 25))
    for refit in audit:
        now = refit["fit_time"]
        fitted = np.asarray(refit["fit_row_indices"], dtype=int)
        assert len(fitted) == refit["n_fit_rows"]
        assert np.all(prediction_time[fitted] < now)
        assert np.all(available[fitted] < now)
        assert np.all(np.isin(split[fitted], ["train", "test"]))
        assert refit["max_label_available_time"] < now
