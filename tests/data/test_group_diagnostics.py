import numpy as np
import pandas as pd
import pytest

from shiftlab.data.group_diagnostics import (
    classification_group_evidence,
    fit_offline_classifier,
    group_summaries,
)


def fixture_frame():
    rng = np.random.default_rng(123)
    X = rng.normal(size=(100, 2))
    X[0, 1] = np.nan
    return pd.DataFrame(
        {
            "features": list(X),
            "target": (X[:, 0] > 0).astype(float),
            "domain_id": ["a"] * 60 + ["b"] * 40,
            "split": ["train"] * 60 + ["test"] * 40,
        }
    )


def test_train_only_fit_and_unseen_test_labels():
    frame = fixture_frame()
    before, classes = fit_offline_classifier(frame)
    modified = frame.copy()
    modified.loc[60:, "target"] = 42
    after, _ = fit_offline_classifier(modified)
    np.testing.assert_array_equal(before, after)
    evidence = classification_group_evidence(modified, after, classes)
    test = evidence[evidence.split == "test"].iloc[0]
    assert test.unseen_training_class_count == 40
    assert test.accuracy == 0
    assert pd.isna(test.decision_loss_known_classes)


def test_asymmetric_bayes_actions_and_source_summaries():
    frame = fixture_frame().iloc[:2].copy()
    frame["target"] = [1, 0]
    p = np.array([[0.8, 0.2], [0.9, 0.1]])
    evidence = classification_group_evidence(frame, p, [0, 1], [[0, 5], [1, 0]])
    assert evidence.iloc[0].accuracy == 0.5
    assert evidence.iloc[0].decision_loss_known_classes == 0
    features, labels = group_summaries(frame, ["x0", "x1"])
    assert features.loc[features.feature == "x1", "missing_rate"].iloc[0] == 0.5
    assert labels["count"].sum() == 2
    with pytest.raises(ValueError):
        classification_group_evidence(frame, [[1, 1], [0, 1]], [0, 1])
