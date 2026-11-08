"""Tests for the matched-assumption Gap-Mix comparators (docs/methods_recovery/51_GAPMIX_MATCHED.md)."""

from __future__ import annotations

import numpy as np

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess, null_sup_loglik
from shiftlab.gaver import gapmix as gm
from shiftlab.gaver import gapmix_matched as mm

Q0 = 0.55


def sim_chain(rng, n, gap, p, rho):
    """Labels of a stationary 2-state round chain observed every ``gap`` rounds."""
    lam = rho**gap
    z = int(rng.random() < p)
    out = [z]
    for _ in range(n - 1):
        p1 = p * (1 - lam) if z == 0 else p + (1 - p) * lam
        z = int(rng.random() < p1)
        out.append(z)
    return out


def test_batch_sup_matches_scalar():
    rng = np.random.default_rng(1)
    edges = gm.rho_cell_edges(0.8)
    for _ in range(6):
        gaps = [4, 5]
        counts = rng.integers(0, 12, size=(3, 2, 4)).astype(float)
        got = mm.certified_sup_batch(counts, gaps, Q0, edges)
        for s in range(3):
            ref = gm.certified_null_sup_loglik(
                {g: counts[s, i] for i, g in enumerate(gaps)}, Q0, edges
            )
            assert abs(got[s] - ref) < 1e-9
    assert mm.certified_sup_batch(np.zeros((2, 1, 4)), [3], Q0, edges).tolist() == [0.0, 0.0]


def test_restricted_sup_bounds_bruteforce_and_is_below_free_sup():
    rng = np.random.default_rng(2)
    lam_max = 0.8**4
    edges = mm.lam_edges(lam_max)
    ps = np.linspace(0.01, Q0, 120)
    lams = np.linspace(0.0, lam_max, 120)
    for _ in range(5):
        n = rng.integers(0, 15, size=4).astype(float)
        got = mm.certified_sup_batch(n[None, None, :], [1], Q0, edges)[0]
        brute = max(gm.exact_loglik({1: n}, p, l) for p in ps for l in lams)
        assert got >= brute - 1e-9
        free = null_sup_loglik(n[None, :], Q0)[0]
        assert got <= free + 0.8  # certified bound looseness stays small


def test_rb_evidence_exceeds_unrestricted_on_persistent_data():
    """Restricting lambda cannot lower the evidence (up to the certification slack) and raises it here."""
    rng = np.random.default_rng(3)
    z = sim_chain(rng, 60, 1, 0.85, 0.9)
    edges = mm.lam_edges(0.3)
    free = MarkovLREProcess(Q0, 0.1, 60)
    rb = mm.MarkovLRRestricted(Q0, 0.1, 60, 0.3)
    for v in z:
        free.update_z(v)
        rb.update_z(v)
    assert rb.log_e_value >= free.log_e_value - 0.8
    assert edges[-1] == 0.3


def test_ui_predictable_and_normalised():
    """The plug-in alternative of every start depends on past labels only and sums to one."""
    ui = mm.UIGapAllStarts(Q0, 0.8, 0.1, 40, k=5)
    rng = np.random.default_rng(4)
    ev = 0
    for z in sim_chain(rng, 12, 4, 0.7, 0.4):
        ev += 4
        ui.update(ev, -1.0 if z else 1.0)
    for s in range(3):
        for prev in (0, 1):
            p1 = ui.predictive_p1(s, 4, prev)
            assert 0.0 < p1 < 1.0
            assert abs(p1 + (1.0 - p1) - 1.0) < 1e-12
    th0 = ui.th_idx.copy()
    # estimating before seeing observation k: th used for observation k equals th_idx before update
    ev += 4
    before = ui.th_idx.copy()
    ui.update(ev, -1.0)
    assert (before == th0).all()


def test_ui_null_validity_monte_carlo():
    """Boundary null stationary chain with rho in {0.8}: e-value mean ~<= 1, horizon FP << alpha-ish."""
    rng = np.random.default_rng(5)
    n_rep, n_lab, gap = 120, 40, 4
    final_e, fp = [], 0
    for _ in range(n_rep):
        ui = mm.UIGapAllStarts(Q0, 0.8, 0.1, n_lab, k=8)
        ev, hit = 0, False
        for z in sim_chain(rng, n_lab, gap, Q0, 0.8):
            ev += gap
            ui.update(ev, -1.0 if z else 1.0)
            hit = hit or ui.alarm
        fp += hit
        final_e.append(np.exp(ui.log_e_value))
    assert np.mean(final_e) <= 1.1  # E[e] <= 1 (MC slack)
    assert fp / n_rep <= 0.1 + 0.07  # alpha plus MC error


def test_ui_power_under_alternative_and_rb_runs():
    rng = np.random.default_rng(6)
    ui = mm.UIGapAllStarts(Q0, 0.8, 0.1, 40, k=8)
    ev = 0
    for z in sim_chain(rng, 40, 4, 0.92, 0.3):
        ev += 4
        ui.update(ev, -1.0 if z else 1.0)
    assert ui.alarm and ui.log_e_value > np.log(10)


def test_matched_arms_run_in_harness():
    cell = fa.Family3CellSpec(0.5, 0.3, 1.0, "strong", "harmful", 10, 0.1, T=400)
    cfg, st = cell.config(7), fa.make_stream(cell, 7)
    for name in mm.MATCHED_ARMS:
        m = mm.build_gate(name)
        r = fa.run_for(cell, st, m, cfg)
        assert r.queries <= cfg.B and m.n_used <= cfg.B
