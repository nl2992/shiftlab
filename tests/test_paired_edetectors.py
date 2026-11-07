import numpy as np

from shiftlab.dive.horizon_edetectors import HorizonCalibratedEDetector
from shiftlab.sota_search.paired_edetectors import paired_edetectors


def test_matches_existing_scalar_engine_with_delayed_skips():
    T = 30
    loss = np.random.default_rng(13).random((1, T))
    cand = 1 - loss
    stream = {"loss": loss, "candidate_loss": cand}
    result = paired_edetectors(stream, seed=17, frac=0.4, budget=8, delay=3, return_statistics=True)
    q = np.random.default_rng(17).random((1, T)) < 0.4
    q &= np.cumsum(q, axis=1) <= 8
    active = np.pad(q.cumsum(1), ((0, 0), (1, 0)))[:, :-1] < 8
    x = np.where(active, q / 0.4 * (loss - cand) - 0.01, 0)
    for kind, offset in [("sr", 0), ("cusum", 4)]:
        engine = HorizonCalibratedEDetector(
            bound=2.51, horizon=T, kind=kind, stakes=(0.2, 0.5, 0.8)
        )
        for t in range(T):
            value = engine.update(skip=True) if t < 3 else engine.update(float(x[0, t - 3]))
            np.testing.assert_allclose(
                np.exp(value), result["statistics"][offset + 3, 0, t], rtol=1e-12
            )


def test_arl_threshold_does_not_control_finite_horizon_false_promotion():
    # Null factor1 gives SR statistic t deterministically: ARL threshold20
    # necessarily crosses within this horizon. This is not an e-process claim.
    s = {"loss": np.zeros((1, 100)), "candidate_loss": np.zeros((1, 100))}
    r = paired_edetectors(s, margin=0, switch_cost=0, budget=0)
    assert np.all(r["first"][:8] == 100)
    assert np.all(r["first"][8:12] == 19)
    assert np.all(r["labels"] == 0)
