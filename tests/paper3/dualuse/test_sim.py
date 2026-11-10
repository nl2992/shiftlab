import numpy as np

from shiftlab.paper3.dualuse.sim import KillCfg, forward_gap, run_chunk


def test_prequential_valid_and_resub_inflated_under_boundary_null():
    cfg = KillCfg(gamma=0.0, T=200, gates=("preq", "resub"))
    out = run_chunk(cfg, 1500, np.random.default_rng(9000001))
    assert (out["promo"]["preq"] >= 0).mean() <= 0.05 + 0.02  # Ville bound, MC slack
    assert (out["promo"]["resub"] >= 0).mean() > 0.9


def test_periodic_forward_value_zero_over_full_period():
    cfg = KillCfg(periodic_L=50, w0_cos=0.3, T=300, horizons=(100,), gates=("preq",))
    rng = np.random.default_rng(9000002)
    out = run_chunk(cfg, 400, rng)
    bank = rng.standard_normal((4000, cfg.d)).astype(np.float32)
    v = forward_gap(cfg, out, bank)[100]
    assert (out["promo"]["preq"] >= 0).mean() > 0.05
    assert np.nanmax(np.abs(v)) < 1e-3
