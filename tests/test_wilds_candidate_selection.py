import numpy as np

from scripts.evaluate_wilds_candidate_selection import (
    _cluster_bootstrap,
    _cost,
    _holm,
    _metadata_float,
)


def test_imposed_cost_weights_false_positives_and_false_negatives():
    y = np.array([0, 1, 0, 1], dtype=np.int8)
    probability = np.array([0.9, 0.1, 0.1, 0.9])

    np.testing.assert_array_equal(_cost(y, probability, 0.5, fp=1.0, fn=2.0), [1.0, 2.0, 0.0, 0.0])


def test_holm_adjustment_restores_original_order():
    adjusted = _holm([0.01, 0.03, 0.001])

    np.testing.assert_allclose(adjusted, [0.02, 0.03, 0.003])


def test_article_cluster_bootstrap_is_reproducible_and_clustered():
    gains = np.array([1.0, 1.0, -1.0, -1.0, 1.0, -1.0])
    articles = np.array([10, 10, 20, 20, 30, 30])

    result_a = _cluster_bootstrap(gains, articles, replicates=500, seed=11)
    result_b = _cluster_bootstrap(gains, articles, replicates=500, seed=11)

    assert result_a == result_b
    assert result_a[0] == 0.0
    assert result_a[1] < 0.0 < result_a[2]


def test_missing_or_nonfinite_metadata_is_not_a_group_or_cluster_value():
    assert _metadata_float(None) == -1.0
    assert _metadata_float("not-a-number") == -1.0
    assert _metadata_float(float("nan")) == -1.0
    assert _metadata_float("0.75") == 0.75
