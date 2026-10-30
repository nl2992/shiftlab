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


def test_tight_cap_keeps_betting_factors_positive_and_null_valid():
    sim = g.simulate(g.World(kind="concept", delta=2.0, t0=100, T=600), 60, 8)
    for risk in ("cost", "brier"):
        for frac in (0.05, 0.2):
            x, _qv, _loose, tight = d._pp_parts(sim, frac, 3, risk, None, None, 0.0)
            # the exact one-sided minimum of the increment is attained when a queried label has zero loss
            assert x.min() >= -tight.max() - 1e-9
            lam_max = 0.5 / tight
            assert (1.0 + lam_max * x).min() >= 0.5 - 1e-9
    null = g.simulate(g.World(kind="none", T=1500), 300, 12)
    for name in ("pprm_tight", "pp_cost_tight"):
        rate = (
            d.first_cross(
                d.DETECTORS[name](null, frac=0.2, delay=5, lseed=2), d.THEORY_THRESHOLD[name]
            )
            < 1500
        ).mean()
        assert rate <= 0.08, (name, rate)


def test_tight_cap_is_more_powerful_than_loose_cap():
    sim = g.simulate(g.World(kind="concept", delta=2.0, t0=300, T=1500), 80, 9)
    thr = d.THEORY_THRESHOLD["pp_cost"]
    loose = (d.first_cross(d.pp_cost(sim, frac=0.2, delay=5, lseed=4), thr) < 1500).mean()
    tight = (d.first_cross(d.pp_cost_tight(sim, frac=0.2, delay=5, lseed=4), thr) < 1500).mean()
    assert tight > loose + 0.2
