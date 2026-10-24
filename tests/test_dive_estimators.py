from itertools import combinations

import numpy as np
import pytest

from shiftlab.dive.estimators import (
    AdaptiveReliance,
    pprm_adaptive_reliance,
    pprm_block_design_variance,
    pprm_block_estimate,
    prediction_powered_bound,
    prediction_powered_estimate,
)


def test_prediction_powered_estimate_is_unbiased_under_known_bernoulli_sampling():
    z, h, q = -0.4, 0.15, 0.2
    draws = np.random.default_rng(42).binomial(1, q, size=100_000)
    estimates = [
        prediction_powered_estimate(h, bool(indicator), z if indicator else None, q)
        for indicator in draws
    ]
    assert abs(np.mean(estimates) - z) < 0.015


@pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 1.0])
def test_prediction_powered_bound_covers_all_endpoint_combinations(q):
    bound = prediction_powered_bound(2.0, q)
    for z in (-2.0, 2.0):
        for h in (-2.0, 2.0):
            assert abs(h + (z - h) / q) <= bound + 1e-12
            assert abs(h) <= bound


def test_estimator_rejects_unobserved_outcome_and_nonpositive_propensity():
    with pytest.raises(ValueError, match="unqueried"):
        prediction_powered_estimate(0.0, False, 1.0, 0.5)
    with pytest.raises(ValueError, match="propensity"):
        prediction_powered_estimate(0.0, False, None, 0.0)


def test_adaptive_reliance_uses_only_past_pairs_and_updates_after_feedback():
    proxy = np.linspace(-1.0, 1.0, 20)
    observed = 0.5 * proxy + 0.01 * np.sin(np.arange(20))
    reliance = AdaptiveReliance(query_fraction=0.1).fit(proxy, observed)
    initial = reliance.reliance
    assert 0 <= initial <= reliance.max_reliance
    reliance.observe(proxy_value=0.9, observed_value=0.45)
    assert len(reliance.observed_values) == 21


def test_pprm_block_estimate_matches_labeled_mean_when_proxy_is_constant():
    labeled = np.array([0.2, 0.8, 0.4])
    estimate = pprm_block_estimate(
        labeled,
        np.full(3, 0.3),
        np.full(12, 0.3),
        reliance=0.75,
    )
    assert estimate == pytest.approx(labeled.mean())


def test_pprm_block_estimator_has_declared_support_and_rejects_bad_inputs():
    for reliance in (0.0, 0.25, 1.0, 3.5):
        estimate = pprm_block_estimate(
            np.array([0.0, 1.0]),
            np.array([1.0, 0.0]),
            np.array([0.0, 1.0, 0.5]),
            reliance=reliance,
        )
        assert -reliance <= estimate <= 1 + reliance
    with pytest.raises(ValueError, match="nonempty"):
        pprm_block_estimate(np.array([]), np.array([]), np.array([0.5]), reliance=1.0)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        pprm_block_estimate(np.array([1.1]), np.array([0.5]), np.array([0.5]), reliance=1.0)


def test_pprm_block_estimator_is_unbiased_under_identical_disjoint_sample_laws():
    # Exact enumeration for one independent labeled and one unlabeled draw from
    # the same finite population; no Monte Carlo tolerance is needed.
    values = np.array([0.0, 1.0, 0.25])
    proxies = np.array([0.2, 0.8, 0.6])
    probabilities = np.array([0.2, 0.5, 0.3])
    reliance = 1.4
    expected = 0.0
    for label_index, p_label in enumerate(probabilities):
        for unlabeled_index, p_unlabeled in enumerate(probabilities):
            estimate = pprm_block_estimate(
                np.array([values[label_index]]),
                np.array([proxies[label_index]]),
                np.array([proxies[unlabeled_index]]),
                reliance=reliance,
            )
            expected += p_label * p_unlabeled * estimate
    assert expected == pytest.approx(float(np.dot(probabilities, values)))


def test_pprm_adaptive_reliance_matches_predictable_variance_optimum_and_clips():
    labeled = np.array([0.5, 0.6, 0.4])
    labeled_proxy = np.array([0.1, 0.9, 0.4])
    unlabeled_proxy = np.array([0.2, 0.4, 0.6, 0.8])
    expected = np.cov(labeled, labeled_proxy, ddof=1)[0, 1] / (
        (1 + len(labeled) / len(unlabeled_proxy)) * np.var(unlabeled_proxy, ddof=1)
    )
    reliance = pprm_adaptive_reliance(
        labeled,
        labeled_proxy,
        unlabeled_proxy,
        max_reliance=1.0,
    )
    assert reliance == pytest.approx(expected)
    assert 0 <= reliance <= 1
    assert (
        pprm_adaptive_reliance(
            labeled,
            labeled_proxy,
            unlabeled_proxy,
            max_reliance=0.1,
        )
        == 0.1
    )


def test_pprm_adaptive_reliance_uses_fallback_without_historical_proxy_variation():
    reliance = pprm_adaptive_reliance(
        np.array([0.1, 0.9]),
        np.array([0.5, 0.5]),
        np.array([0.5, 0.5, 0.5]),
        max_reliance=1.0,
        fallback_reliance=0.25,
    )
    assert reliance == 0.25


@pytest.mark.parametrize("reliance", [0.0, 0.1, 0.75, 1.0])
def test_pprm_block_design_variance_matches_exact_label_subset_enumeration(reliance):
    values = np.array([0.05, 0.85, 0.2, 0.7, 0.4, 0.95])
    proxy = np.array([0.15, 0.75, 0.3, 0.6, 0.55, 0.8])
    n_labeled = 2
    estimates = []
    for chosen in combinations(range(len(values)), n_labeled):
        labeled = np.zeros(len(values), dtype=bool)
        labeled[list(chosen)] = True
        estimates.append(
            pprm_block_estimate(
                values[labeled],
                proxy[labeled],
                proxy[~labeled],
                reliance=reliance,
            )
        )
    assert pprm_block_design_variance(
        values,
        proxy,
        n_labeled=n_labeled,
        reliance=reliance,
    ) == pytest.approx(np.var(estimates, ddof=0))


def test_pprm_block_design_variance_rejects_invalid_sampling_design():
    with pytest.raises(ValueError, match="n_labeled"):
        pprm_block_design_variance(
            np.array([0.1, 0.9]), np.array([0.2, 0.8]), n_labeled=2, reliance=0.5
        )
