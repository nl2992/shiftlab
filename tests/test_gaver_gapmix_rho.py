import numpy as np
import pytest

from shiftlab.gaver import gapmix as gm
from shiftlab.gaver import gapmix_rho as gr


def _chain(rng, n, gap, p, rho, jitter=False):
    z = int(rng.random() < p)
    out, ev = [], 1
    for _ in range(n):
        out.append((ev, z))
        g = gap + (int(rng.integers(0, 2)) if jitter else 0)
        for _ in range(g):
            z = int(rng.random() < p + (z - p) * rho)
        ev += g
    return out


def test_cell_sup_matches_gapmix_certified_sup():
    rng = np.random.default_rng(0)
    for rb in (0.5, 0.8, 0.95, 0.99):
        counts = {g: rng.integers(0, 12, 4).astype(float) for g in (3, 4, 5)}
        ref = gm.certified_null_sup_loglik(counts, 0.55, gm.rho_cell_edges(rb))
        mine = float(np.max(gr.cell_best_loglik(counts, 0.55)[: gr.n_cells_for(rb)])) + gm.EPS_SLACK
        assert mine == pytest.approx(ref, abs=1e-6)


def test_fast_reference_equals_wp1_exact_gap_start():
    rng = np.random.default_rng(1)
    labels = _chain(rng, 40, 4, 0.7, 0.4, jitter=True)
    ref, mine = gm.ExactGapStart(0.55, 0.8), gr.RhoStart(0.55)
    for ev, z in labels:
        ref.update(ev, z)
        mine.update(ev, z)
        assert mine.log_e(gr.n_cells_for(0.8)) == pytest.approx(ref.log_e, abs=1e-5)


def test_envelope_plugin_factor_expectation_leq_one_for_any_valid_bound():
    """For any rho_bar_t in [rho*, 0.99] the one-step factor has expectation <= 1 under rho*."""
    worst = 0.0
    q0 = 0.55
    for rho_true in (0.0, 0.5, 0.8, 0.95, 0.99):
        for rb in (r for r in (0.0, 0.5, 0.8, 0.95, 0.99) if r >= rho_true):
            for g in (1, 4, 10):
                u = gm.envelope_u(q0, rb, g, 1)
                v = q0 + (1.0 - q0) * rho_true**g  # worst-case true P(Z=1 | prev=1)
                for r in np.linspace(0.001, 0.999, 80):
                    worst = max(worst, gm.envelope_expectation(v, r, u))
    assert worst <= 1.0 + 1e-12


def test_cs_coverage_under_null():
    rng = np.random.default_rng(2)
    fails = 0
    n_sim = 120
    for _ in range(n_sim):
        rho = 0.9
        cs = gr.RhoCS(0.1)
        ok = True
        for ev, z in _chain(rng, 120, 4, 0.55, rho, jitter=True):
            cs.update(ev, z)
            ok &= cs.ub >= rho
        fails += not ok
    assert fails / n_sim <= 0.1 + 0.05  # nominal delta = 0.1 (CS is conservative; usually 0)


@pytest.mark.parametrize("mode", ["gate", "cs_sup", "env_cs"])
@pytest.mark.parametrize("rho", [0.5, 0.95])
def test_null_mean_evalue_leq_one(mode, rho):
    class Cfg:
        h, T = 0.1, 400

    rng = np.random.default_rng(7)
    vals = []
    for _ in range(80):
        ev_obj = gr.RhoEvidence(Cfg, 0.1, mode)
        for ev, z in _chain(rng, 60, 4, 0.55, rho, jitter=True):
            ev_obj.update(ev, -1.0 if z else 1.0)
        vals.append(np.exp(ev_obj.log_e_value))
    m, se = np.mean(vals), np.std(vals) / np.sqrt(len(vals))
    assert m <= 1.0 + 3 * se + 0.05


def test_gate_excludes_low_rungs_and_keeps_top():
    class Cfg:
        h, T = 0.1, 400

    e = gr.RhoEvidence(Cfg, 0.1, "gate")
    assert e.ub == gr.RHO_MAX  # nothing observed: only the top rung is read
    assert e.cs.ub == gr.RHO_MAX


def test_methods_build_and_names_unique():
    assert len(set(gr.METHOD_NAMES)) == len(gr.METHOD_NAMES)
    for n in gr.METHOD_NAMES:
        assert gr.build_gate(n).name == n


def test_shared_pool_gives_identical_evidence():
    class Cfg:
        h, T = 0.1, 400

    rng = np.random.default_rng(3)
    labels = _chain(rng, 50, 4, 0.7, 0.6, jitter=True)
    pool = gr.new_pool(Cfg.T)
    for mode in ("gate", "cs_sup", "mix"):
        a = gr.RhoEvidence(Cfg, 0.1, mode)
        b = gr.RhoEvidence(Cfg, 0.1, mode, pool=pool)
        for ev, z in labels:
            a.update(ev, -1.0 if z else 1.0)
            b.update(ev, -1.0 if z else 1.0)
            assert a.log_e_value == pytest.approx(b.log_e_value, abs=1e-12)
