import numpy as np

from shiftlab.paper3.payback.certificates import B2Certificate, plan_batch_size
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import Spec, make_stream
from shiftlab.paper3.payback.variance_adaptive import (
    B3Certificate,
    B3GatedCertificate,
    PrPl,
    make_sparse_stream,
    plan_batch_size_var,
    run_events,
)

ENV = Envelope(0.002)
SPEC = Spec(T=400, B=150, d=5, h=30, k=3.0, alpha=0.1, env=ENV)


def test_prpl_covers_varying_mean_time_uniformly():
    # iid +/-1 with mean .3 then a slow drift: weighted-average LCB must not exceed the weighted mean path
    rng = np.random.default_rng(1)
    bad, N, M = 0, 400, 300
    for _ in range(N):
        mu = np.clip(0.3 - 0.0005 * np.arange(M), -1, 1)
        z = np.where(rng.random(M) < (1 + mu) / 2, 1.0, -1.0)
        pr = PrPl(0.1)
        hit = False
        for i in range(M):
            lam = pr.update((z[i] + 1) / 2)
            wavg = (np.dot(pr.lams, mu[: i + 1]) / sum(pr.lams) + 1) / 2
            if pr.lo() > wavg + 1e-12:
                hit = True
                break
            _ = lam
        bad += hit
    assert bad / N <= 0.1


def test_events_only_equals_every_round():
    for i in range(12):
        for kind in ("drift", "boundary"):
            _mu, z = make_stream(kind, SPEC, (5301600000, 1, i))
            n = plan_batch_size(ENV, 0.05, 150)
            for mk in (lambda: B2Certificate(ENV, 0.1), lambda: B3Certificate(ENV, 0.1)):
                kw = {"h": 30, "d": 5, "B": 150, "k": 3.0, "n_plan": n, "truncate": False}
                a = run_events(z, mk(), every_round=True, **kw)
                b = run_events(z, mk(), **kw)
                assert a == b


def test_b2_events_matches_existing_driver():
    from shiftlab.paper3.payback.sim import run_one

    for i in range(8):
        mu, z = make_stream("drift", SPEC, (5301600000, 2, i))
        r0 = run_one(SPEC, mu, z, lambda: B2Certificate(ENV, 0.1))
        r1 = run_events(
            z,
            B2Certificate(ENV, 0.1),
            h=30,
            d=5,
            B=150,
            k=3.0,
            n_plan=plan_batch_size(ENV, 0.05, 150),
            truncate=False,
        )
        assert r0["certified"] == r1["certified"] and r0["t"] == r1["t"]


def test_gated_uses_known_zero_rounds_and_budget():
    _mu, z, dis = make_sparse_stream("sparse_in", SPEC, (5301600000, 3, 0), 0.3)
    assert np.all(z[~dis] == 0)
    r = run_events(z, B3GatedCertificate(ENV, 0.1), h=30, d=5, B=150, k=3.0, n_plan=400, dis=dis)
    assert r["labels"] <= 150
    # labels are only spent on disagreement rounds
    assert r["labels"] <= int(dis[1 : r["t"] + 1].sum())


def test_plan_matches_b2_at_sigma1():
    assert plan_batch_size_var(ENV, 0.05, 150, 1.0) == plan_batch_size(ENV, 0.05, 150)
