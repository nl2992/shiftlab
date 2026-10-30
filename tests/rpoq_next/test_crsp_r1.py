import numpy as np

from shiftlab.dive.rpoq_next import crsp_r1


def _fake(n=3000, dates=100, seed=0):
    rng = np.random.default_rng(seed)
    return {
        "z": rng.normal(0, 0.02, n),
        "h": np.zeros(n),
        "ctx_size": rng.integers(0, crsp_r1.NB, n),
        "date_index": np.sort(rng.integers(0, dates, n)),
        "n_events": n,
    }


def test_arms_hit_the_label_rate_and_respect_cap():
    c = _fake()
    p = np.bincount(c["ctx_size"], minlength=crsp_r1.NB) / c["n_events"]
    mu, h, r = np.linspace(0, 0.01, 8), np.zeros(8), np.full(8, 4e-4)
    for arm in crsp_r1.ARMS:
        q = crsp_r1.bin_propensities(arm, mu, h, r, p, 0.1, chosen=2)
        assert q.min() >= 0.0099 and q.max() <= 1.0
        if arm != "random_conc":
            assert abs(float(p @ q) - 0.1) < 5e-3, arm
        res = crsp_r1.run_monitor_ctx(c, q, 0.1, np.random.default_rng(1).random(3000), "ctx")
        assert res["spent"] <= round(0.1 * 3000)


def test_null_stream_rarely_crosses():
    hits = 0
    for s in range(60):
        c = _fake(seed=s)
        q = np.full(crsp_r1.NB, 0.2)
        hits += crsp_r1.run_monitor_ctx(c, q, 0.2, np.random.default_rng(s).random(3000), "ctx")[
            "crossed"
        ]
    assert hits <= 6
