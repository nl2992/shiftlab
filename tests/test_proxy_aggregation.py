import numpy as np
import pytest

from shiftlab.dive.estimators import prediction_powered_bound, prediction_powered_estimate
from shiftlab.dive.proxy_aggregation import PredictableProxyHedge


def test_hedge_prediction_is_convex_and_weights_update_only_after_feedback():
    hedge = PredictableProxyHedge(n_experts=3, bound=2.0, min_propensity=0.2)
    experts = np.array([-1.0, 0.5, 2.0])
    assert hedge.weights == pytest.approx([1 / 3] * 3)
    assert hedge.predict(experts) == pytest.approx(0.5)
    hedge.observe(experts, observed_value=1.5, propensity=0.25)
    assert hedge.n_updates == 1
    assert hedge.weights.sum() == pytest.approx(1.0)
    assert np.all(hedge.weights > 0)
    assert hedge.predict(experts) == pytest.approx(np.dot(hedge.weights, experts))


def test_ipw_proxy_estimate_is_unbiased_for_each_fixed_outcome_and_hedge_state():
    q = 0.3
    truth = -0.7
    for proxy in (-1.0, 0.0, 0.8):
        expected = (1 - q) * prediction_powered_estimate(proxy, False, None, q)
        expected += q * prediction_powered_estimate(proxy, True, truth, q)
        assert expected == pytest.approx(truth)
        bound = prediction_powered_bound(1.0, q)
        assert abs(prediction_powered_estimate(proxy, False, None, q)) <= bound
        assert abs(prediction_powered_estimate(proxy, True, truth, q)) <= bound


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_experts": 0, "bound": 1.0, "min_propensity": 0.2},
        {"n_experts": 2, "bound": 0.0, "min_propensity": 0.2},
        {"n_experts": 2, "bound": 1.0, "min_propensity": 0.2, "learning_rate": 0.3},
    ],
)
def test_hedge_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        PredictableProxyHedge(**kwargs)


def test_hedge_rejects_unbounded_experts_and_invalid_propensity():
    hedge = PredictableProxyHedge(n_experts=2, bound=1.0, min_propensity=0.2)
    with pytest.raises(ValueError, match="inside the proxy bound"):
        hedge.predict(np.array([0.0, 1.1]))
    with pytest.raises(ValueError, match="propensity"):
        hedge.observe(np.array([0.0, 0.5]), 0.2, 0.1)
