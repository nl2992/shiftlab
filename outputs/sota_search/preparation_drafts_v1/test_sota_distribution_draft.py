import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("distribution_draft", Path(__file__).with_name("sota_distribution_draft.py"))
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def test_random_feature_statistic_matches_explicit_feature_kernel():
    rng = np.random.default_rng(8)
    x, y = rng.normal(size=(20, 3)), rng.normal(size=(20, 3))
    result = draft.random_feature_mmd(x, y, gamma=0.4, components=32, permutations=9, seed=11)
    rng = np.random.default_rng(11)
    w = rng.normal(0, np.sqrt(0.8), size=(3, 32))
    phase = rng.uniform(0, 2 * np.pi, size=32)
    a, b = np.sqrt(2 / 32) * np.cos(x @ w + phase), np.sqrt(2 / 32) * np.cos(y @ w + phase)
    aa, bb, ab = a @ a.T, b @ b.T, a @ b.T
    np.fill_diagonal(aa, 0); np.fill_diagonal(bb, 0)
    expected = aa.sum() / (20 * 19) + bb.sum() / (20 * 19) - 2 * ab.mean()
    assert result["statistic"] == pytest.approx(expected)
    assert result["p_value"] >= 0.1


def test_dependent_samples_refuse_iid_calibration():
    x = np.ones((8, 2))
    for method, kwargs in (
        (draft.permutation_mmd, {"gamma": 1}),
        (draft.random_feature_mmd, {"gamma": 1}),
        (draft.c2st, {}), (draft.bbsd, {}),
    ):
        with pytest.raises(ValueError):
            method(x, x, independent=False, **kwargs)


def test_beta_bernoulli_change_branch_matches_bayes_formula():
    model = draft.BernoulliBOCPD(hazard=0.1)
    for _ in range(20):
        model.update(0)
    prior_predictive = 0.5
    old = np.exp(model.log_posterior)
    growth_predictive = model.a / (model.a + model.b)
    expected = 0.1 * prior_predictive / (0.1 * prior_predictive + 0.9 * (old @ growth_predictive))
    assert model.update(1) == pytest.approx(expected)
    assert np.exp(model.log_posterior).sum() == pytest.approx(1)


def test_c2st_keeps_training_and_test_rows_disjoint_and_detects_large_shift():
    rng = np.random.default_rng(6)
    result = draft.c2st(rng.normal(size=(100, 2)), rng.normal(4, size=(100, 2)))
    assert result["train_rows"] == result["test_rows"] == 100
    assert result["accuracy"] > 0.9 and result["p_value"] < 0.05
