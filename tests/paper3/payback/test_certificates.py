import numpy as np

from shiftlab.paper3.payback.certificates import B1Certificate, B2Certificate, plan_batch_size
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import SMOKE_BASE, Spec, make_stream, run_one


def _wrong_rate(spec, kind, factory, n=150, cls=0):
    rs = [run_one(spec, *make_stream(kind, spec, (SMOKE_BASE, cls, i)), factory) for i in range(n)]
    return np.mean([r["wrong"] for r in rs]), np.mean([r["certified"] for r in rs])


def test_b2_coverage_tight_adversaries_with_adaptive_horizon():
    env = Envelope(0.002)
    spec = Spec(T=300, B=150, d=5, h=30, k=3.0, alpha=0.1, env=env, h_grid=(10, 20, 30))
    for kind in ("null_flat", "null_decline:40", "null_decline:100"):
        w, _ = _wrong_rate(spec, kind, lambda: B2Certificate(env, spec.alpha))
        assert w <= spec.alpha, (kind, w)  # adaptive (t, h, batch) selection stays valid


def test_b2_refuses_honest_flip_class_and_drift_class_is_fooled():
    spec = Spec(T=500, B=150, d=5, h=100, k=3.0, alpha=0.1, env=Envelope(0.002))
    eh = Envelope(0.002, 1.8, 100)
    w_h, c_h = _wrong_rate(spec, "stress_flip", lambda: B2Certificate(eh, spec.alpha), n=40)
    w_d, _c_d = _wrong_rate(spec, "stress_flip", lambda: B2Certificate(spec.env, spec.alpha), n=40)
    assert c_h == 0.0 and w_h == 0.0  # refuses
    assert w_d > 0.2  # drift-class certificate is invalid when the class is violated (E case)


def test_batch_size_is_the_age_variance_tradeoff():
    n = plan_batch_size(Envelope(0.002), 0.05, 10_000)
    assert 60 < n < 400
    assert plan_batch_size(Envelope(0.0), 0.05, 77) == 77


def test_b1_ignores_incomplete_batches():
    env = Envelope(0.0)
    c = B1Certificate(env, 0.1)
    c.start_batch(1, 10)
    for s in range(1, 6):
        c.observe(s, 1.0, s + 1)
    assert c.lcb_sum(10, 5) == -np.inf
