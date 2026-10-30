import numpy as np

from shiftlab.sota_search import detectors as d
from shiftlab.sota_search import generators as g


def test_time_shift_and_feedback_delay_are_causal():
    a = np.arange(10.0)[None, :]
    assert np.array_equal(d.shift_time(a, 3)[0], [0, 0, 0, 0, 1, 2, 3, 4, 5, 6])
    # the evidence at time t must not depend on events later than t - delay
    sim = g.simulate(g.World(kind="concept", delta=2.0, t0=100, T=400), 20, 2)
    base = d.pp_cost(sim, frac=0.2, delay=5, lseed=3)
    sim2 = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in sim.items()}
    for key in ("y", "loss", "brier", "p"):
        sim2[key][:, 300:] = sim2[key][:, 300:][:, ::-1]
    pert = d.pp_cost(sim2, frac=0.2, delay=5, lseed=3)
    assert np.allclose(base[:, :305], pert[:, :305])


def test_theory_threshold_methods_hold_alpha_under_null():
    sim = g.simulate(g.World(kind="none", T=1500), 300, 11)
    for name, thr in d.THEORY_THRESHOLD.items():
        stat = d.DETECTORS[name](sim, frac=0.2, delay=5, lseed=1)
        rate = (d.first_cross(stat, thr) < stat.shape[1]).mean()
        assert rate <= 0.08, (name, rate)


def test_harmful_concept_shift_is_detected_by_cost_eprocess_but_benign_is_not():
    harm = g.simulate(g.World(kind="concept", delta=2.0, t0=300, T=1500), 80, 5)
    benign = g.simulate(g.World(kind="cov_benign", delta=3.0, t0=300, T=1500), 80, 6)
    thr = d.THEORY_THRESHOLD["pp_cost"]
    hit_h = (d.first_cross(d.pp_cost(harm, frac=0.3, delay=5, lseed=2), thr) < 1500).mean()
    hit_b = (d.first_cross(d.pp_cost(benign, frac=0.3, delay=5, lseed=2), thr) < 1500).mean()
    assert hit_h > 0.5 and hit_b < 0.1
