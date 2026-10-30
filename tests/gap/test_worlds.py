import numpy as np
import pytest

from shiftlab.gap import worlds as W

R = W.Regime


def test_markov_path_stationary_and_persistence():
    P = W.transition(3, 0.9)
    assert np.allclose(P.sum(1), 1.0) and np.allclose(np.diag(P), 0.9)
    z = W.markov_path(P, 400, 3000, t0=100, rng=np.random.default_rng(1))
    assert (z[:, :100] == 0).all()
    stay = (z[:, 101:] == z[:, 100:-1]).mean()
    assert abs(stay - 0.9) < 0.01
    occ = np.bincount(z[:, 1000:].ravel(), minlength=3) / z[:, 1000:].size
    assert np.allclose(occ, 1 / 3, atol=0.03)  # symmetric jump chain -> uniform stationary law


def test_cycle_structure_is_recurrent():
    P = W.transition(3, 0.95, "cycle")
    assert P[0, 1] == pytest.approx(0.05) and P[0, 2] == 0.0


def test_delay_models():
    S, T = 50, 400
    loss = (np.random.default_rng(0).random((S, T)) < 0.3).astype(float)
    assert (W.delays("fixed", S, T, d=5) == 5).all()
    u = W.delays("uniform", S, T, d=5)
    assert 0 <= u.min() and u.max() <= 10 and abs(u.mean() - 5) < 0.3
    o = W.delays("outcome", S, T, loss=loss, d=5)
    assert (o[loss > 0] == 2).all() and (o[loss == 0] == 30).all()  # outcome-dependent
    b = W.delays("burst", S, T, d=5)
    arrivals = np.arange(T)[None] + b
    assert (arrivals % 20 == 0).all()  # released in batches
    assert W.delays("heavy", S, T, d=5).max() > 50  # long pending queues


def test_proxy_modes_respect_declared_range_and_do_not_touch_losses():
    w = W.LogitWorld(regimes=(R(), R("concept", 2.0)), t0=0)
    st = W.make_stream(w, 20, 3, z=np.repeat(W.scheduled_regimes("abrupt", 2000, 800)[None], 20, 0))
    for mode in (
        "static_bias",
        "bias_after_shift",
        "anti",
        "subgroup",
        "calibration",
        "recover",
        "oracle_adapt",
        "blend0.5",
    ):
        p = W.apply_proxy(st, mode)
        assert p["proxy_brier"].min() >= 0 and p["proxy_brier"].max() <= st["pmax"]["brier"] + 1e-12
        assert p["proxy_cost"].max() <= st["pmax"]["cost"] + 1e-12
        assert np.array_equal(
            p["loss"], st["loss"]
        )  # the proxy is a property of the model, outcomes unchanged
    anti = W.apply_proxy(st, "anti")
    assert np.allclose(anti["proxy_brier"][:, :800], st["proxy_brier"][:, :800])
    assert not np.allclose(anti["proxy_brier"][:, 1000:], st["proxy_brier"][:, 1000:])


def test_finance_world_bounded_and_regime_dependent():
    fw = W.FinWorld()
    st = W.make_fin_stream(fw, 30, 4, W.transition(3, 0.995))
    assert st["loss"].min() >= 0 and st["loss"].max() <= 1 and st["brier"].max() <= 1
    eff = W.fin_effects(fw)
    assert eff[2, 2] > eff[1, 2] > 0.03  # signal reversal harms more than attenuation


def test_dependence_in_latent_noise_inflates_block_mean_variance():
    iid = W.LogitWorld(regimes=(R(),), name="iid")
    cl = W.LogitWorld(regimes=(R(),), cluster_len=200, cluster_sigma=1.5, name="cluster")
    a, b = W.make_stream(iid, 300, 1), W.make_stream(cl, 300, 1)
    vr = lambda s: s["loss"].reshape(300, 10, 200).mean(2).var()
    assert vr(b) > 1.5 * vr(a)  # clustered outcomes: long-run variance well above the iid value
    assert abs(a["r0"]["cost"] - 0.409) < 0.03


def test_three_truth_dimensions_disagree_by_design():
    w = W.LogitWorld(regimes=(R(), R("cov_benign", 3.0), R("concept", 2.0), R("cost", fn=20.0)))
    eff = W.regime_effects(w)
    assert eff[1, 0] > 0.1 > abs(eff[1, 2])  # discrepancy without harm
    assert eff[3, 0] < 0.01 < eff[3, 2]  # harm without discrepancy
    assert eff[2, 1] > 0.05 and eff[2, 2] > 0.1  # predictive degradation and harm


def test_seed_reproducibility():
    w = W.LogitWorld(regimes=(R(), R("concept", 2.0)), t0=500)
    P = W.transition(2, 0.99)
    a, b = W.make_stream(w, 10, 5, P=P), W.make_stream(w, 10, 5, P=P)
    assert np.array_equal(a["loss"], b["loss"]) and np.array_equal(
        a["truth"]["regime"], b["truth"]["regime"]
    )
