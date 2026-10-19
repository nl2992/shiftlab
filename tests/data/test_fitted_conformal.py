import numpy as np

from scripts.validate_fitted_conformal import _arrived_prior_scores


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
