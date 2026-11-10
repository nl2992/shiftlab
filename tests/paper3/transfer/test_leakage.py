import copy

import numpy as np
import pytest

from shiftlab.paper3.transfer import data, sim, streams, synth
from shiftlab.paper3.transfer import methods as M


def _small_recs():
    rng = np.random.default_rng(0)
    out = []
    for i, fam in enumerate(["a", "a", "b", "b"]):
        K = 10
        l0 = (rng.random((K, 2000)) < 0.3).astype(np.int8)
        l1 = (rng.random((K, 2000)) < 0.2).astype(np.int8)
        o = sim.simulate(l0, l1, 50, sim.PRIMARY, grid=sim.GRID[::12], log_cfg=0)
        J = {
            s: np.tile(o["J"], 1)[:, :1].repeat(sim.NCFG, 1) + rng.normal(0, 1, (K, sim.NCFG))
            for s in sim.SCENARIOS
        }
        out.append(
            data.SRec(
                f"s{i}",
                fam,
                fam,
                True,
                50,
                K,
                3,
                J,
                J,
                o["rel"],
                (l0 != l1).astype(np.int8),
                l0.sum(1).astype(float),
            )
        )
    return out


def test_embedding_ignores_later_episodes():
    r = _small_recs()[0]
    x = data.embed(r, 0, r.n_early, sim.PRIMARY)
    r2 = copy.deepcopy(r)
    r2.rel[r.n_early :] = 1
    r2.dis[r.n_early :] = 1
    assert np.allclose(x, data.embed(r2, 0, r2.n_early, sim.PRIMARY))


def test_selectors_ignore_eval_window():
    rs = _small_recs()
    ctx = M.build_ctx(rs[1:], [], "all")
    r = rs[0]
    x = data.embed(r, 0, r.n_early, sim.PRIMARY)
    before = (
        M.per_stream_tuning(r, "primary"),
        M.hier_pool(ctx, r, "primary"),
        M.knn_meta(ctx, "primary", x),
        M.ess_heuristic(ctx, "primary", x),
        M.global_fixed(ctx, "primary"),
    )
    r2 = copy.deepcopy(r)
    r2.J["primary"][r.n_early :] += 1e4 * np.random.default_rng(1).random(
        (r.K - r.n_early, sim.NCFG)
    )
    x2 = data.embed(r2, 0, r2.n_early, sim.PRIMARY)
    after = (
        M.per_stream_tuning(r2, "primary"),
        M.hier_pool(ctx, r2, "primary"),
        M.knn_meta(ctx, "primary", x2),
        M.ess_heuristic(ctx, "primary", x2),
        M.global_fixed(ctx, "primary"),
    )
    assert before == after


def test_training_excludes_test_stream():
    rs = _small_recs()
    ctx = M.build_ctx(rs[2:], [], "all")
    assert all(s.name not in ("s0", "s1") for s in ctx.streams)


def test_sealed_guard():
    for n in streams.SEALED_STREAMS:
        with pytest.raises(streams.SealedAccessError):
            streams.load(n)
    assert not set(streams.dev_streams()) & set(streams.SEALED_STREAMS)


def test_sim_budget_cutoff_and_delay():
    rng = np.random.default_rng(1)
    l0 = (rng.random((4, 2000)) < 0.4).astype(np.int8)
    l1 = (rng.random((4, 2000)) < 0.2).astype(np.int8)
    g = np.array([[0.97, 0.2, 0.0], [0.97, 0.2, 1500.0]])
    o = sim.simulate(l0, l1, 100, grid=g, log_cfg=1)
    assert (o["labels"] <= 200).all()
    req = o["req"]
    assert not req[:, 2000 - 1500 - 100 + 1 :].any()  # t + delay > T - H -> never purchased
    # released outcomes appear exactly delay steps after purchase
    rel = o["rel"]
    assert (rel[:, :100] == 0).all()
    assert ((rel != 0).sum(1) == req[:, :1900].sum(1)).all()


def test_synthetic_hides_truth():
    l0, _l1, d = synth.make_stream("S2_markov_regime", 0, K=2)
    assert l0.shape == (2, 2000) and d in synth.DELAYS
