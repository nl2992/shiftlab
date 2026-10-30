import numpy as np

from shiftlab.dive.query import EvidenceDirectedQueryPolicy
from shiftlab.dive.rpoq_next import crsp_b1


def _fake(n=2000, dates=80, seed=0):
    rng = np.random.default_rng(seed)
    return {
        "z": rng.normal(0, 0.02, n),
        "h": np.zeros(n),
        "date_index": np.sort(rng.integers(0, dates, n)),
        "n_events": n,
    }


def test_both_arms_respect_cap_and_null_rarely_crosses():
    hits = 0
    for s in range(60):
        c = _fake(seed=s)
        u = np.random.default_rng(s).random(2000)
        ed = EvidenceDirectedQueryPolicy(q_min=0.025, q_max=0.25, alpha=0.05)
        for pol in (None, ed):
            r = crsp_b1.run(c, 0.1, u, pol)
            assert r["spent"] <= round(0.1 * 2000)
            hits += r["crossed"]
    assert hits <= 12
