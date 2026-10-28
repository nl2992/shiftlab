"""Lemma L (Stage 0, T0.3): HT wealth is propensity-free given the ordered labelled losses.

For the zero-anchor gated HT increment at epsilon = 0 with fixed-fraction stakes, an agreement
contributes 0, an unqueried disagreement contributes 0, and a queried disagreement contributes
``(z / q) / (5 / q) = z / 5``. Every betting factor is therefore ``1 + stake * z / 5`` and the
wealth path, indexed by labels, depends only on the ordered labelled losses. The identity is
pathwise; it is not a validity statement. The PPI increment, a positive epsilon, and adaptive
engines whose state moves on zero updates are outside it, and the tests below show they differ.
"""

import numpy as np
import pytest

from shiftlab.dive.eprocess import (
    PredictableBoundMeanEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
)
from shiftlab.dive.gated_monitor_comparison import gated_increment

COST_BOUND = 5.0


def _replay(
    losses,
    propensities,
    disagreement,
    uniforms,
    *,
    epsilon=0.0,
    anchor=0.0,
    ppi=False,
    weights=None,
):
    """Replay one stream; the i-th queried disagreement reveals ``losses[i]``.

    Returns the log e-value after each label, so paths can be compared label by label.
    """
    process = PredictableBoundMeanEProcess(alpha=0.05, weights=weights)
    labelled = iter(losses)
    remaining = len(losses)
    path = []
    for q, active, u in zip(propensities, disagreement, uniforms, strict=True):
        if remaining == 0:
            break
        # The registered query rule; the identity is pathwise, so any mask would do.
        query = bool(active) and u < q
        observed = float(next(labelled)) if query else None
        value = gated_increment(
            disagreement=bool(active),
            observed_cost=observed,
            propensity=q,
            anchor=anchor + epsilon if ppi else 0.0,
            epsilon=epsilon,
        )
        bound = (COST_BOUND + epsilon) * (2 / q - 1) if ppi else COST_BOUND / q + epsilon
        log_e = process.update(value, bound=bound)
        if query:
            remaining -= 1
            path.append(log_e)
    assert remaining == 0, "stream too short to reveal every labelled loss"
    return np.asarray(path)


def _schedules(n, seed):
    rng = np.random.default_rng(seed)
    return {
        "constant_low": np.full(n, 0.1),
        "constant_high": np.full(n, 0.8),
        "paced_drift": np.clip(np.linspace(0.6, 0.03, n), 0.03, 1.0),
        "random_predictable": rng.uniform(0.02, 1.0, n),
    }


@pytest.fixture
def stream():
    rng = np.random.default_rng(20261028)
    n = 4_000
    losses = rng.uniform(-COST_BOUND, COST_BOUND, 60)
    disagreement = rng.random(n) < 0.4
    return losses, disagreement, rng.random(n), _schedules(n, 7)


@pytest.mark.parametrize("weights", [None, (0.5, 0.2, 0.1, 0.1, 0.1)])
def test_ht_wealth_is_propensity_free_at_zero_epsilon(stream, weights):
    losses, disagreement, uniforms, schedules = stream
    paths = {
        name: _replay(losses, q, disagreement, uniforms, weights=weights)
        for name, q in schedules.items()
    }
    reference = PredictableBoundMeanEProcess(alpha=0.05, weights=weights)
    expected = np.asarray([reference.update(z / COST_BOUND, bound=1.0) for z in losses])
    for name, path in paths.items():
        np.testing.assert_allclose(path, expected, rtol=0, atol=1e-12, err_msg=name)


def test_ht_wealth_ignores_where_unlabelled_events_fall(stream):
    losses, disagreement, uniforms, schedules = stream
    shuffled = np.random.default_rng(3).permutation(disagreement)
    q = schedules["random_predictable"]
    np.testing.assert_allclose(
        _replay(losses, q, disagreement, uniforms),
        _replay(losses, q, shuffled, uniforms),
        rtol=0,
        atol=1e-12,
    )


def test_positive_epsilon_breaks_propensity_invariance(stream):
    losses, disagreement, uniforms, schedules = stream
    low = _replay(losses, schedules["constant_low"], disagreement, uniforms, epsilon=0.1)
    high = _replay(losses, schedules["constant_high"], disagreement, uniforms, epsilon=0.1)
    assert np.max(np.abs(low - high)) > 1e-3


def test_ppi_increment_is_not_propensity_free(stream):
    losses, disagreement, uniforms, schedules = stream
    low = _replay(losses, schedules["constant_low"], disagreement, uniforms, anchor=1.0, ppi=True)
    high = _replay(losses, schedules["constant_high"], disagreement, uniforms, anchor=1.0, ppi=True)
    assert np.max(np.abs(low - high)) > 1e-3


def test_ppi_single_unqueried_factor_matches_closed_form():
    # An unqueried disagreement with anchor c contributes log(1 + s * c / (5 (2/q - 1))),
    # which equals log(1 + s * c q / (5 (2 - q))) and moves with q.
    for q in (0.05, 0.5, 0.9):
        process = PredictableBoundMeanEProcess(alpha=0.05, stakes=(0.4,))
        value = gated_increment(
            disagreement=True, observed_cost=None, propensity=q, anchor=1.0, epsilon=0.0
        )
        process.update(value, bound=COST_BOUND * (2 / q - 1))
        assert process.log_e_value == pytest.approx(np.log1p(0.4 * q / (COST_BOUND * (2 - q))))


def test_adaptive_engine_state_moves_on_zero_updates():
    # Empirical Bernstein updates its variance estimate on every event, so zero increments from
    # unqueried events change later factors; Lemma L does not cover adaptive engines.
    labelled = [0.6, -0.2, 0.8, 0.4]
    dense = PredictablePlugInEmpiricalBernsteinEProcess(bound=1.0, alpha=0.05)
    sparse = PredictablePlugInEmpiricalBernsteinEProcess(bound=1.0, alpha=0.05)
    for z in labelled:
        dense.update(z)
        for _ in range(5):
            sparse.update(0.0)
        sparse.update(z)
    assert abs(dense.log_e_value - sparse.log_e_value) > 1e-6
