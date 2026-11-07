import dataclasses

import numpy as np
import pytest

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import Stream
from shiftlab.gaver import gapmix as gm


def test_envelope_worked_numbers():
    assert gm.envelope_u(0.55, 0.8, 1, 1) == pytest.approx(0.91)
    assert gm.envelope_u(0.55, 0.8, 4, 1) == pytest.approx(0.73432)
    assert gm.envelope_u(0.55, 0.8, 10, 1) == pytest.approx(0.598318, abs=1e-6)
    assert gm.envelope_u(0.55, 0.95, 4, 1) == pytest.approx(0.91653, abs=1e-5)
    assert gm.envelope_u(0.55, 0.8, 4, 0) == 0.55


def test_envelope_factor_expectation_leq_one_on_grid():
    worst = 0.0
    for q0 in (0.5, 0.55, 0.7):
        for rb in (0.3, 0.8, 0.95):
            for g in (1, 2, 4, 10):
                for prev in (0, 1):
                    u = gm.envelope_u(q0, rb, g, prev)
                    for v in np.linspace(0.0, u, 25):
                        for r in np.linspace(0.001, 0.999, 60):
                            worst = max(worst, gm.envelope_expectation(v, r, u))
    assert worst <= 1.0 + 1e-12


def _markov_labels(rng, n, gap, p, rho, jitter=False):
    """Round-level stationary chain observed every ``gap`` rounds (events 1, 1+gap, ...)."""
    z = int(rng.random() < p)
    out, ev = [], 1
    for _ in range(n):
        out.append((ev, z))
        g = gap + (int(rng.integers(0, 2)) if jitter else 0)
        for _ in range(g):
            z = int(rng.random() < p + (z - p) * rho)
        ev += g
    return out


@pytest.mark.parametrize("cls", ["env", "exact"])
def test_null_mean_evalue_leq_one(cls):
    rng = np.random.default_rng(5)
    q0 = 0.55
    vals = []
    for _ in range(300):
        st = gm.EnvelopeStart(q0, 0.8) if cls == "env" else gm.ExactGapStart(q0, 0.8)
        for ev, z in _markov_labels(rng, 40, 4, q0, 0.8, jitter=True):
            st.update(ev, z)
        vals.append(np.exp(st.log_e))
    m, se = np.mean(vals), np.std(vals) / np.sqrt(len(vals))
    assert m <= 1.0 + 3 * se + 0.02


def test_certified_sup_dominates_pointwise_sup_and_is_tight():
    rng = np.random.default_rng(1)
    q0 = 0.55
    edges = gm.rho_cell_edges(0.9)
    ps = np.linspace(0.0, q0, 111)[1:]
    rhos = np.linspace(0.0, 0.9, 181)
    for _ in range(6):
        counts = {g: rng.integers(0, 40, 4).astype(float) for g in (3, 4)}
        brute = max(gm.exact_loglik(counts, p, r) for p in ps for r in rhos)
        cert = gm.certified_null_sup_loglik(counts, q0, edges)
        assert cert >= brute - 1e-9
        assert cert - brute < 2.0  # conservatism (measured, not proven) stays small here


def _null_stream_cell():
    return fa.Family3CellSpec(0.5, 0.3, 0.6, "strong", "harmful", 3, 0.1, T=400).null_twin()


def test_gate_never_reads_unreleased_labels():
    cell = _null_stream_cell()
    cfg = cell.config(11)
    st = fa.make_stream(cell, 11)
    # flip every label whose release would fall after T (queried in the last d rounds)
    loss0 = st.loss0.copy()
    loss0[-cfg.d :] = 1.0 - loss0[-cfg.d :]
    st2 = Stream(loss0, 1.0 - loss0, st.truth)
    for name in ("exact0.8_s4", "env0.8_s4", "mlr_s4"):
        a = fa.run_for(cell, st, gm.build_gate(name), cfg)
        b = fa.run_for(cell, st2, gm.build_gate(name), cfg)
        assert (a.actions == b.actions).all()
        assert a.queries <= cfg.B


def test_gate_runs_all_methods_and_counts_used_labels():
    cell = _null_stream_cell()
    cfg = dataclasses.replace(cell.config(2))
    st = fa.make_stream(cell, 2)
    for name in gm.METHOD_NAMES:
        g = gm.build_gate(name)
        fa.run_for(cell, st, g, cfg)
        assert 0 <= g.n_used <= cfg.B
