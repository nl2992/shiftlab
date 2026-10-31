"""Fast tests for the decision-value engine (see docs/decision_value/05_EXPERIMENTAL_CONTRACT.md)."""

import inspect
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pytest

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value import evaluation as E
from shiftlab.decision_value import monitors as M
from shiftlab.decision_value import oracles as O
from shiftlab.decision_value import registry
from shiftlab.decision_value import statistics as S
from shiftlab.decision_value.calibration import calibrate_threshold, null_maxima
from shiftlab.decision_value.contracts import (
    CostContract,
    EpisodeBatch,
    EvaluatorTruth,
    FeedbackContract,
)
from shiftlab.decision_value.feedback import LabelQueue, make_mask
from shiftlab.decision_value.synthetic import Family

PKG = Path(registry.PKG)
SMALL = {"T": 400, "tau_lo": 100, "tau_hi": 200, "L": 100}


def det_batch(l0, l1, q=1.0):
    """Deterministic batch + truth (mu = realised loss), all events queried."""
    l0, l1 = np.atleast_2d(np.asarray(l0, float)), np.atleast_2d(np.asarray(l1, float))
    mask = np.ones(l0.shape, bool) if q == 1.0 else q
    z = np.zeros(l0.shape, np.int8)
    return EpisodeBatch(l0, l1, mask), EvaluatorTruth(
        l0.copy(), l1.copy(), z, np.full(len(l0), np.nan)
    )


class Scripted(C.Controller):
    def __init__(self, n, T, script, c_s=0.0):
        super().__init__(n, T, c_s)
        self.script = np.asarray(script, np.int8)

    def step(self, s, alarm, rel):
        return np.full(self.n, self.script[s], np.int8), np.zeros(self.n, bool)


def run(batch, truth, fb, cost, mon, ctrl):
    return E.run_episode_batch(batch, truth, fb, cost, mon, ctrl)


# ---------------------------------------------------------------- information flow
def test_operational_modules_have_no_truth_access():
    for f in ("monitors.py", "controllers.py", "feedback.py"):
        src = (PKG / f).read_text(encoding="utf8")
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("#", '"""')))
        assert not re.search(
            r"EvaluatorTruth|\bmu0\b|\bmu1\b|^\s*(from|import)\s+\S*synthetic", code, re.MULTILINE
        ), f
    assert "truth" not in inspect.signature(E.simulate).parameters
    for cls in C.CONTROLLERS.values():
        assert "truth" not in inspect.signature(cls.step).parameters


@pytest.mark.parametrize("name", list(M.MONITORS))
def test_future_perturbation_does_not_change_past_actions(name):
    fb = FeedbackContract(q=0.6, d=7)
    batch, _ = Family("s1", SMALL).generate(3, 60, fb)
    e0 = 150
    pert = EpisodeBatch(batch.l0.copy(), batch.l1.copy(), batch.mask.copy())
    pert.l0[:, e0:] = 1 - pert.l0[:, e0:]
    pert.l1[:, e0:] = 1 - pert.l1[:, e0:]
    outs, mons = [], []
    for b in (batch, pert):
        mon = M.monitor_factory(name, k=0.0)(60) if name == "cusum" else M.monitor_factory(name)(60)
        mon.threshold = 0.5 if name != "batch" else 0.3
        outs.append(E.simulate(b, fb, mon, C.Permanent(60, b.T)))
        mons.append(mon)
    cut = e0 + fb.d + 1  # decisions s <= e0+d see only events < e0
    assert np.array_equal(outs[0].actions[:, :cut], outs[1].actions[:, :cut])
    assert np.array_equal(outs[0].alarm[:, :cut], outs[1].alarm[:, :cut])
    assert not np.array_equal(
        mons[0].statistic, mons[1].statistic
    )  # perturbation does reach the monitor


def test_truth_perturbation_changes_scores_not_actions():
    fb, cost = FeedbackContract(q=0.5, d=3), CostContract(0.1, 1.0)
    batch, truth = Family("s1", SMALL).generate(4, 40, fb)
    mon = M.monitor_factory("cusum")(40)
    mon.threshold = 3.0
    r1 = run(batch, truth, fb, cost, mon, C.Permanent(40, 400))
    truth2 = EvaluatorTruth(truth.mu0 * 0.5, truth.mu1 * 2, truth.regime, truth.tau)
    mon = M.monitor_factory("cusum")(40)
    mon.threshold = 3.0
    r2 = run(batch, truth2, fb, cost, mon, C.Permanent(40, 400))
    assert np.array_equal(r1["N_s"], r2["N_s"]) and np.array_equal(
        r1["first_switch"], r2["first_switch"], equal_nan=True
    )
    assert not np.allclose(r1["cost_exp"], r2["cost_exp"])


def test_incumbent_reference_uses_only_calibration_window():
    n, cal = 3, 10
    rng = np.random.default_rng(0)
    l0 = rng.integers(0, 2, (n, 30)).astype(float)
    tg = M.Target("incumbent", n, cal)
    xs = []
    for l0_late in (
        l0,
        np.where(np.arange(30) >= cal + 5, 1 - l0, l0),
    ):  # change labels long after cal window
        b = EpisodeBatch(l0, l0, np.ones((n, 30), bool))
        b.l0 = l0_late
        q, tg = LabelQueue(b, 0), M.Target("incumbent", n, cal)
        xs.append([tg.transform(q.at(s)) for s in range(1, 17)])
    for s in range(15):  # early outputs equal; x = l0 - r0 where r0 from first cal events
        assert np.array_equal(xs[0][s][0], xs[1][s][0])
    r0 = l0[:, :cal].mean(axis=1)
    assert np.allclose(
        xs[0][cal][0], l0[:, cal] - r0
    )  # first post-calibration event is event `cal`
    assert not xs[0][5][1].any()  # nothing valid during calibration


# ---------------------------------------------------------------- feedback
@pytest.mark.parametrize("d", [0, 1, 5, 50])
def test_label_visible_exactly_at_t_plus_d_plus_1(d):
    T, e = 120, 20
    mask = np.zeros((2, T), bool)
    mask[:, e] = True
    mask[1, 30] = True
    l0 = np.zeros((2, T))
    l1 = np.zeros((2, T))
    l0[:, e] = 1
    b = EpisodeBatch(l0, l1, mask)
    q = LabelQueue(b, d)
    seen = [s for s in range(T) if q.at(s).valid[0]]
    assert seen == [e + d + 1]
    assert q.at(e + d + 1).event == e and q.at(e + d).valid.sum() == 0
    mon = M.monitor_factory("cusum")(2)
    mon.threshold = 0.5
    sim = E.simulate(b, FeedbackContract(0.5, d), mon, C.Permanent(2, T), trace_idx=(0,))
    assert sim.traces[0]["update_steps"] == [e + d + 1]
    assert sim.traces[0]["visible_decision"] == [e + d + 1]
    assert sim.actions[0, : e + d + 1].sum() == 0  # cannot act on it earlier


def test_event_order_preserved():
    b, _ = det_batch(np.arange(10)[None, :] / 10, np.zeros((1, 10)))
    q = LabelQueue(b, 3)
    ev = [q.at(s).event for s in range(14) if q.at(s).valid.any()]
    assert ev == sorted(ev) == list(range(10))


def test_query_budget_accounting():
    rng = np.random.default_rng(0)
    m = make_mask(rng, 50, 300, 0.3)
    assert m.shape == (50, 300) and 0.2 < m.mean() < 0.4
    mb = make_mask(np.random.default_rng(0), 50, 300, 0.9, max_queries=25)
    assert (mb.sum(axis=1) <= 25).all() and (mb.sum(axis=1) == 25).all()
    for bad in ({"q": -0.1}, {"q": 1.5}, {"d": -1}, {"max_queries": -1}):
        with pytest.raises(ValueError):
            FeedbackContract(**bad)
    with pytest.raises(ValueError):
        CostContract(c_q=-1)
    fb, cost = FeedbackContract(0.25, 5), CostContract(2.0, 0.0)
    batch, truth = Family("s1", SMALL).generate(1, 30, fb)
    mon = M.monitor_factory("cusum")(30)
    r = run(batch, truth, fb, cost, mon, C.Permanent(30, 400))
    assert np.array_equal(r["N_q"], batch.mask.sum(axis=1)) and (r["N_q"] >= 0).all()
    assert np.allclose(r["cost_exp"] - r["loss_exp"], 2.0 * r["N_q"])
    r0 = run(batch, truth, fb, cost, None, C.NeverSwitch(30, 400))
    assert (r0["N_q"] == 0).all() and np.allclose(r0["cost_exp"], truth.mu0.sum(axis=1))


# ---------------------------------------------------------------- cost accounting & oracles
def test_switch_cost_hand_computed():
    script = [0, 1, 1, 0, 0, 1]
    b, tr = det_batch([[1.0] * 6], [[0.5] * 6])
    cost = CostContract(c_q=0.25, c_s=3.0)
    r = run(b, tr, FeedbackContract(1.0, 0), cost, None, Scripted(1, 6, script))
    assert r["N_s"][0] == 3
    assert np.isclose(r["loss_exp"][0], 1 + 0.5 + 0.5 + 1 + 1 + 0.5)
    r = run(b, tr, FeedbackContract(1.0, 0), cost, None, Scripted(1, 6, [1] * 6))
    assert r["N_s"][0] == 1  # initial move to challenger costs one switch
    assert np.isclose(r["cost_exp"][0], 3.0 + 3.0 + 0.25 * 6)  # 6 queried events


def test_analytical_toy_known_optimal_schedule():
    T = 60
    l0 = np.zeros((1, T))
    l0[0, 20:40] = 1.0
    l1 = np.full((1, T), 0.2)
    b, tr = det_batch(l0, l1)
    cost = CostContract(0.0, 3.0)
    orc = O.oracle_costs(b, tr, cost)
    assert np.isclose(orc["never_exp"][0], 20) and np.isclose(orc["always_exp"][0], 0.2 * 60 + 3)
    assert np.isclose(orc["static_exp"][0], 15) and np.isclose(
        orc["dynamic_exp"][0], 0.2 * 20 + 2 * 3
    )  # = 10
    assert np.isclose(orc["headroom_exp"][0], 10)
    script = [1 if 20 <= t < 40 else 0 for t in range(T)]
    r = run(b, tr, FeedbackContract(1.0, 0), cost, None, Scripted(1, T, script))
    assert np.isclose(r["cost_exp"][0], orc["dynamic_exp"][0]) and r["N_s"][0] == 2
    assert np.isclose(
        r["harm_before_switch"][0], 0.0
    )  # no positive advantage before first switch except window
    assert r["t_chal_in_opp"][0] == 20 and r["t_chal_out_opp"][0] == 0


def test_dp_matches_brute_force_and_oracle_ordering():
    rng = np.random.default_rng(1)
    T, n, cs = 9, 6, 0.7
    m0, m1 = rng.random((n, T)), rng.random((n, T))
    best = np.full(n, np.inf)
    for path in itertools.product([0, 1], repeat=T):
        a = np.array(path)
        sw = (a[0] != 0) + (np.diff(a) != 0).sum()
        c = np.where(a == 1, m1, m0).sum(axis=1) + cs * sw
        best = np.minimum(best, c)
    assert np.allclose(O.dp_two_state(m0, m1, cs), best)
    fb = FeedbackContract(0.5, 2)
    for fam in ("s1", "s2", "s3"):
        batch, truth = Family(
            fam, {"T": 300, "tau_lo": 50, "tau_hi": 100, "L": 80, "rho": 0.97}
        ).generate(2, 40, fb)
        for cs in (0.0, 2.0, 8.0):
            o = O.oracle_costs(batch, truth, CostContract(0.1, cs))
            for tag in ("exp", "real"):
                assert (o[f"dynamic_{tag}"] <= o[f"static_{tag}"] + 1e-9).all()
                assert (o[f"static_{tag}"] <= o[f"never_{tag}"] + 1e-9).all()
                assert (o[f"headroom_{tag}"] >= -1e-9).all()
            assert (o["dynamic_exp"] <= o["clairvoyant_exp"] + 1e-9).all()


def test_regime_clairvoyant_s2():
    fb = FeedbackContract(0.5, 0)
    batch, truth = Family("s2", {"T": 500, "rho": 0.98, "challenger_bad": "useful"}).generate(
        5, 30, fb
    )
    o = O.oracle_costs(batch, truth, CostContract(0, 0.0))
    assert np.allclose(o["clairvoyant_exp"], o["dynamic_exp"])  # c_s = 0: pointwise min
    batch, truth = Family("s2", {"T": 500, "rho": 0.98, "challenger_bad": "harmful"}).generate(
        5, 30, fb
    )
    o = O.oracle_costs(batch, truth, CostContract(0, 1.0))
    assert np.allclose(o["clairvoyant_exp"], o["never_exp"])  # never deploys a harmful challenger


def test_deterministic_replay():
    def once(seed):
        fb, cost = FeedbackContract(0.3, 4), CostContract(0.01, 2.0)
        fam = Family("s1", SMALL)
        fac = M.monitor_factory("sr_betting")
        thr = calibrate_threshold(fac, fam, fb, 0.05, 200, 5_000_000)
        batch, truth = fam.generate(seed, 50, fb)
        mon = fac(50)
        mon.threshold = thr
        return thr, run(batch, truth, fb, cost, mon, C.Hold(50, 400, 2.0, H=60))

    t1, r1 = once(11)
    t2, r2 = once(11)
    _, r3 = once(12)
    assert t1 == t2
    for k, v in r1.items():
        if k != "_traces":
            assert np.array_equal(v, r2[k], equal_nan=v.dtype.kind == "f"), k
    assert not np.array_equal(r1["cost_exp"], r3["cost_exp"])


# ---------------------------------------------------------------- calibration
def test_calibrated_null_alarm_rate_matches_alpha_on_fresh_seeds():
    fb = FeedbackContract(0.5, 10)
    fam = Family("s1", SMALL)
    for name in ("cusum", "page_hinkley", "sr_betting"):
        fac = M.monitor_factory(name)
        thr = calibrate_threshold(fac, fam, fb, 0.05, 2000, 5_000_000)
        rates = [(null_maxima(fac, fam, fb, 1500, 5_000_100 + i) > thr).mean() for i in range(2)]
        assert abs(np.mean(rates) - 0.05) < 0.02, (name, rates)


def test_nominal_edetector_threshold_is_valid_under_null():
    fb = FeedbackContract(0.5, 10)
    fam = Family("s1", SMALL)
    thr = M.nominal_log_threshold(0.05)
    for name in ("kelly_h2c_inspired",):  # valid e-process from start 0 (bounded, predictable bets)
        mx = null_maxima(M.monitor_factory(name), fam, fb, 1500, 5_000_200)
        assert (mx > thr).mean() <= 0.05 + 0.015


# ---------------------------------------------------------------- monitors: textbook & fidelity
def feed(mon, xs):
    out = []
    for x in xs:
        mon.update(np.array([x]), np.array([True]))
        out.append(mon.statistic[0])
    return np.array(out)


def test_fidelity_cusum_vs_repo():
    from shiftlab.monitoring import one_sided_cusum

    xs = np.random.default_rng(0).uniform(-1, 1, 200)
    ref = one_sided_cusum(xs, baseline_mean=0.0, baseline_scale=1.0, slack=0.03)
    assert np.allclose(feed(M.CUSUM(1, k=0.03), xs), ref)


def test_fidelity_kelly_vs_repo_eprocess():
    from shiftlab.dive.eprocess import MultiTimescaleStartedKellyEProcess

    xs = np.random.default_rng(1).choice([-1.0, 0.0, 1.0], 300, p=[0.3, 0.3, 0.4])
    repo = MultiTimescaleStartedKellyEProcess(bound=1.0, alpha=0.05, starts=(0,))
    ref = np.array([repo.update(x) for x in xs])
    assert np.allclose(feed(M.KellyH2c(1), xs), ref, atol=1e-10)


def test_textbook_values_page_hinkley_sr_batch():
    ph = feed(M.PageHinkley(1, delta=0.1), [-1.0, -1.0, 1.0, 1.0])
    # running means -1,-1,-1/3,0 ; m = -.1,-.2,1.0333,1.9333 ; M = -.1,-.2,-.2,-.2 ; PH = m - M
    assert np.allclose(ph, [0.0, 0.0, 1.0 + 1 / 3 - 0.1, 2.0 + 1 / 3 - 0.2])
    sr = M.SRBetting(1, lambdas=(0.5,))
    assert np.allclose(np.exp(feed(sr, [1.0, 1.0])), [1.5, 3.75])
    with pytest.raises(ValueError):
        M.SRBetting(1, lambdas=(1.0,))
    bt = M.BatchTest(1, n_b=4)
    xs = [1.0, 0.0, 1.0, 0.0]
    z = feed(bt, xs)[-1]
    sd = np.std(xs, ddof=1)
    assert np.isclose(z, 0.5 / (sd / 2)) and np.isneginf(feed(M.BatchTest(1, n_b=4), xs[:3])[-1])


def test_valid_mask_and_reset_semantics():
    for name, cls in M.MONITORS.items():
        m = cls(3)
        m.update(np.array([1.0, 1.0, 1.0]), np.array([True, True, True]))
        s_before = m.statistic.copy()
        m.update(np.array([-1.0, 1.0, 1.0]), np.array([False, False, False]))
        assert np.array_equal(m.statistic, s_before), name  # invalid -> no change
        m.update(np.array([1.0, 1.0, 1.0]), np.array([True, True, True]))
        s2 = m.statistic.copy()
        m.reset(np.array([False, True, False]))
        fresh = cls(3).statistic
        assert m.statistic[1] == fresh[1] and m.statistic[0] == s2[0] and m.statistic[2] == s2[2], (
            name
        )


# ---------------------------------------------------------------- controllers
def switch_batch(T=16, flip=None):
    l0 = np.ones((1, T))
    l1 = np.zeros((1, T))
    if flip is not None:
        l0[:, flip:], l1[:, flip:] = 0.0, 1.0
    return det_batch(l0, l1)


def test_permanent_hold_reverse_references():
    fb, cost = FeedbackContract(1.0, 0), CostContract()
    fac = M.monitor_factory("cusum", k=0.02)
    b, tr = switch_batch(15)
    mon = fac(1)
    mon.threshold = 2.5
    a = E.simulate(b, fb, mon, C.Permanent(1, 15)).actions[0]
    assert a.tolist() == [0, 0, 0] + [1] * 12
    mon = fac(1)
    mon.threshold = 2.5
    a = E.simulate(b, fb, mon, C.Hold(1, 15, H=4)).actions[0]
    assert a.tolist() == [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0]
    b, tr = switch_batch(20, flip=8)
    mon = fac(1)
    mon.threshold = 2.5
    a = E.simulate(b, fb, mon, C.Reverse(1, 20, rev_factory=fac, rev_threshold=2.5)).actions[0]
    assert a.tolist() == [0, 0, 0] + [1] * 8 + [0] * 9  # back at s=11 (events 8,9,10 flipped)
    r = run(b, tr, fb, cost, None, C.AlwaysChallenger(1, 20))
    assert r["N_s"][0] == 1 and r["cost_exp"][0] == pytest.approx(8 * 0 + 12 * 1)
    # calendar: K=5 picks lower mean released loss over last window; labels of current step excluded
    b, tr = switch_batch(20)
    a = E.simulate(b, fb, None, C.CalendarBatch(1, 20, K=5)).actions[0]
    assert a.tolist() == [0] * 5 + [1] * 15
    # static: W=4 buffer, gap 1 per step: switch when 1*(T-s) > c_s
    a = E.simulate(b, fb, None, C.StaticThreshold(1, 20, c_s=10.0, W=4)).actions[0]
    first = int(np.argmax(a))
    assert first == 4 and 20 - first > 10  # buffer full after 4 released labels
    a = E.simulate(b, fb, None, C.StaticThreshold(1, 20, c_s=100.0, W=4)).actions[0]
    assert a.sum() == 0


# ---------------------------------------------------------------- generators & statistics
def test_generators_shapes_and_structure():
    fb = FeedbackContract(0.2, 0)
    b, t = Family("s1", SMALL).generate(0, 20, fb)
    assert b.l0.shape == t.mu0.shape == (20, 400) and set(np.unique(b.l0)) <= {0.0, 1.0}
    i = 0
    tau = int(t.tau[i])
    assert (
        t.mu0[i, tau] == pytest.approx(0.35)
        and t.mu0[i, tau + 100] == pytest.approx(0.2)
        and t.opportunity[i, tau]
    )
    _, tn = Family("s1", SMALL).generate(0, 20, fb, null=True)
    assert np.isnan(tn.tau).all() and not tn.opportunity.any()
    b2, _ = Family("s1", SMALL).generate(0, 20, fb, null=True)
    assert np.array_equal(b.mask, b2.mask)  # CRN: acquisition identical for null/non-null
    for ch, post0, post1 in (
        ("strong", 0.35, 0.25),
        ("common_shock", 0.35, 0.40),
        ("none", 0.35, 0.35),
    ):
        _, t = Family("s3", dict(SMALL, challenger=ch)).generate(0, 5, fb)
        k = int(t.tau[0]) + 10
        assert (t.mu0[0, k], t.mu1[0, k]) == pytest.approx((post0, post1))
    _, t = Family("s3", dict(SMALL, challenger="reversing")).generate(0, 5, fb)
    k = int(t.tau[0]) + 150
    assert t.mu1[0, k] > t.mu0[0, k]
    for ch, v in (("useful", 0.2), ("useless", 0.35), ("harmful", 0.40)):
        _, t = Family("s2", {"T": 300, "rho": 0.95, "challenger_bad": ch}).generate(0, 10, fb)
        bad = t.regime == 1
        assert bad.any() and np.allclose(t.mu1[bad], v)


def test_bootstrap_holm_reversal():
    rng = np.random.default_rng(0)
    a = rng.normal(1.0, 1, 400)
    b = rng.normal(0.0, 1, 400)
    r = S.paired_bootstrap_diff(a, b, B=2000, seed=1)
    assert r["lo"] < (a - b).mean() < r["hi"] and r["lo"] > 0 and r["p"] < 0.01
    assert S.paired_bootstrap_diff(a, a, B=500)["mean"] == 0
    rel = S.relative_diff(a + 10, b + 10, b + 10, B=1000, seed=2)
    assert abs(rel["mean"] - (a.mean() - b.mean()) / (b.mean() + 10)) < 1e-12
    assert np.allclose(S.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    n = 500
    pa = (rng.random(n) < 0.6).astype(float)
    pb = (rng.random(n) < 0.4).astype(float)
    da, db = rng.normal(100, 10, n), rng.normal(200, 10, n)
    ca, cb = rng.normal(10, 1, n), rng.normal(9, 1, n)
    out = S.classify_reversal(pa, pb, da, db, ca, cb, mme=0.5, B=2000)
    assert out["detection_advantage"] and out["cost_disadvantage"] and out["reversal"]
    out = S.classify_reversal(pa, pb, da, db, cb, ca, mme=0.5, B=2000)  # A cheaper: no reversal
    assert out["detection_advantage"] and not out["reversal"]
    out = S.classify_reversal(pa, pa, da, da, ca, cb, mme=0.5, B=2000)  # no detection advantage
    assert not out["detection_advantage"] and not out["reversal"]


def test_registry_append_only(tmp_path):
    reg = tmp_path / "r.jsonl"
    registry.append_run("a", {"x": 1}, {"s": 1}, 5, 0.1, ["o"], registry=reg)
    first = reg.read_text()
    registry.append_run("b", {"x": 2}, {"s": 2}, 5, 0.1, ["o"], confirmation=True, registry=reg)
    text = reg.read_text()
    assert text.startswith(first) and len(text.splitlines()) == 2
    e = json.loads(text.splitlines()[1])
    assert (
        e["stage"] == "confirmation" and e["git"]["commit"] and "monitors.py" in e["source_sha256"]
    )


def test_seed_guard_in_script():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "rs", Path(registry.ROOT) / "scripts/decision_value/run_synthetic.py"
    )
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    rs.check_seeds([1, 6_999_999], False, None)
    with pytest.raises(SystemExit):
        rs.check_seeds([7_000_000], False, None)
    with pytest.raises(SystemExit):
        rs.check_seeds([7_000_000], True, None)
    rs.check_seeds([7_000_000], True, "abc")


def test_s2_asymmetric_chain():
    import numpy as np

    from shiftlab.decision_value.contracts import FeedbackContract
    from shiftlab.decision_value.synthetic import Family

    fb = FeedbackContract(0.2, 0)
    # explicit symmetric rho_g = rho_b = rho reproduces the default path bit-identically
    a, ta = Family("s2", {"rho": 0.99}).generate(7, 50, fb)
    b, tb = Family("s2", {"rho": 0.99, "rho_g": 0.99, "rho_b": 0.99}).generate(7, 50, fb)
    assert (
        np.array_equal(a.l0, b.l0)
        and np.array_equal(a.l1, b.l1)
        and np.array_equal(ta.regime, tb.regime)
    )
    # asymmetric: stationary bad fraction ~ pi_b and mean bad-run length ~ 1/(1-rho_b)
    rb, pi = 0.99, 0.1
    rg = 1 - pi * (1 - rb) / (1 - pi)
    _, t = Family("s2", {"rho_g": rg, "rho_b": rb}).generate(3, 4000, fb)
    assert abs(t.regime.mean() - pi) < 0.01
    assert abs(t.regime[:, 0].mean() - pi) < 0.02  # stationary initial state
    reg = t.regime
    starts = ((reg[:, 1:] == 1) & (reg[:, :-1] == 0)).sum() + reg[:, 0].sum()
    assert abs(reg.sum() / starts - 1 / (1 - rb)) < 15
