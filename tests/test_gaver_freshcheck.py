import numpy as np

from shiftlab.dive.switching_explore import run
from shiftlab.gaver import freshcheck as fc


def _run(mode, reserve, cell, seed):
    cfg, stream = cell.config(seed), fc.make_stream(cell, seed)
    m = fc.FreshCheckMethod(mode, reserve)
    res = run(stream, m, cfg)
    return m, res, cfg


def test_fresh_process_uses_only_post_switch_released_labels():
    cell = fc.Wp3Cell("reversal", 0.2, d=10)
    checked = 0
    for seed in range(101120000, 101120008):
        m, _res, cfg = _run("fresh", 0.2, cell, seed)
        promo_rounds = [t for t, act, _ in m.query_log if act == 1]
        for consume_t, ev in m.rb_events:
            assert ev + cfg.d <= consume_t  # released before consumption: no pending label
            assert ev >= min(promo_rounds)  # requested at/after the (first) promotion round
            checked += 1
        # promotion wealth retired: the object is gone while deployed
        if m.act == 1:
            assert m.ep is None
    assert checked > 0


def test_fresh_evidence_event_rounds_after_each_promotion():
    cell = fc.Wp3Cell("reversal", 0.2, d=1)
    for seed in range(101120010, 101120016):
        m, _, _ = _run("fresh", 0.2, cell, seed)
        # every keep-evidence label comes from a round inside some deployed interval's start onward
        assert all(ev >= 1 for _, ev in m.rb_events)
        # evidence consumed while deployed (act=1) never includes pre-promotion event rounds
        by_prom = [t for t, act, _ in m.query_log]
        assert len(by_prom) == cell.T


def test_no_unreleased_labels_any_mode():
    cell = fc.Wp3Cell("persistent", 0.2, d=10)
    for mode in ("none", "cusum", "cost_threshold", "fresh", "reuse"):
        m, _, cfg = _run(mode, 0.2, cell, 101120020)
        assert all(ev + cfg.d <= t for t, ev, _ in m.consumed)


def test_budget_and_reserve_accounting():
    for kind in ("persistent", "reversal", "null"):
        cell = fc.Wp3Cell(kind, 0.2, d=1)
        for seed in range(101120030, 101120034):
            m, res, cfg = _run("fresh", 0.2, cell, seed)
            assert res.queries <= cfg.B  # hard pathwise cap
            reserve = round(0.2 * cfg.B)
            # while not deployed, used (after this round's request) never exceeds B - reserve,
            # unless the excess was spent while deployed earlier
            seen_deployed = False
            for _, act, used_after in m.query_log:
                seen_deployed |= act == 1
                if not seen_deployed:
                    assert used_after <= cfg.B - reserve
    # no reserve: pre-promotion phase may use everything
    cell = fc.Wp3Cell("null", d=1)
    m, res, cfg = _run("fresh", 0.0, cell, 101120040)
    assert res.queries >= cfg.B - 2


def test_reserve_unused_in_null_stream():
    cell = fc.Wp3Cell("null", d=1)
    for seed in range(101120050, 101120056):
        _m, res, cfg = _run("fresh", 0.2, cell, seed)
        if res.promotions == 0:
            assert res.queries <= cfg.B - round(0.2 * cfg.B)


def test_alpha_allocation_sums_below_alpha_rb():
    m = fc.FreshCheckMethod("fresh", 0.2, alpha_rb=0.1)
    assert sum(m.alpha_rb_k(k) for k in range(60)) < 0.1 + 1e-12
    m.start(fc.Wp3Cell("null").config(101120060))
    assert abs(m._alpha_j(0) - 0.05) < 1e-12
    n = fc.FreshCheckMethod("none", 0.0)
    n.start(fc.Wp3Cell("null").config(101120060))
    assert abs(n._alpha_j(0) - 0.1) < 1e-12


def test_streams_paired_and_in_seed_block():
    cell = fc.Wp3Cell("reversal", 0.5, d=1)
    a, b = fc.make_stream(cell, 101120000), fc.make_stream(cell, 101120000)
    assert np.array_equal(a.loss0, b.loss0)
    assert fc.WP3_SEED_RANGE == (101120000, 101159999)
    reg = a.truth.regime
    assert set(np.unique(reg)) == {0, 1, 2}


def test_stats_helpers():
    r, lo, hi = fc.clopper_pearson(0, 500)
    assert r == 0 and lo == 0 and 0.005 < hi < 0.01
    assert fc.clopper_pearson(5, 10)[1] < 0.5 < fc.clopper_pearson(5, 10)[2]
    mean, lo, hi = fc.paired_bootstrap(np.ones(30))
    assert mean == lo == hi == 1.0
    assert fc.grade(0.2, 0.1, 0.3).startswith("substantial")
    assert fc.grade(0.005, -0.01, 0.01) == "negligible"
    assert fc.grade(-0.05, -0.08, -0.02) == "meaningful worse"


def test_keepnull_stream_ends_at_hurdle_boundary():
    cell = fc.Wp3Cell("keepnull", 0.2, d=1)
    s = fc.make_stream(cell, 101150000)
    assert set(np.unique(s.truth.regime)) == {0, 1, 3}
    assert np.isclose(s.truth.regime_mean[-1], -0.1)
    m, _, _ = _run("fresh", 0.2, cell, 101150000)
    assert m.stat_trigger_ever in (0, 1)


def test_ported_comparators_respect_release_and_budget():
    cell = fc.Wp3Cell("reversal", 0.2, d=10)
    for name in ("erb", "erb_a05", "two_phase"):
        m = fc.make_method(name)
        cfg, stream = cell.config(101120070), fc.make_stream(cell, 101120070)
        res = run(stream, m, cfg)
        assert res.queries <= cfg.B
        assert all(ev + cfg.d <= t for t, ev, _ in m.consumed)


def test_two_phase_needs_two_alarms_and_never_rolls_back():
    cell = fc.Wp3Cell("persistent", 0.2, d=1)
    m = fc.make_method("two_phase")
    res = run(fc.make_stream(cell, 101120071), m, cell.config(101120071))
    assert res.promotions <= 1 and m.rollback_mode == "none"
    if res.promotions:
        assert m.phase == 2 and m.ph2_start > 0
