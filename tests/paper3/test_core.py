"""Paper 3 core contract tests: release timing, budgets, tapes, boundaries, accounting."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from shiftlab.paper3.baselines import NeverSwitch, WaldEconomic, default_baselines
from shiftlab.paper3.budgets import BudgetError, BudgetLedger
from shiftlab.paper3.contracts import Costs, Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec
from shiftlab.paper3.feedback_queue import PendingFeedbackQueue
from shiftlab.paper3.simulation import (
    SimulationEvaluator,
    Tape,
    generate_tape,
    hindsight_oracle_cost,
    load_regimes,
    make_spec,
    run_policy,
    seed_blocks,
    seeds_for,
)

T = 120
REG = load_regimes()


def _tape(regime="abrupt_beneficial", seed=1, T=T):
    return generate_tape(REG[regime], seed, T)


class RandomPolicy(PolicyAdapter):
    name = "random"

    def reset(self, spec, rng):
        self.rng = rng

    def act(self, view: PolicyView):
        q = int(view.labels_remaining > 0 and self.rng.random() < 0.7)
        return Paper3Decision(int(self.rng.random() < 0.5), q)


class Recorder(PolicyAdapter):
    name = "rec"

    def __init__(self, qat):
        self.qat, self.seen = set(qat), []

    def reset(self, spec, rng):
        self.seen = []

    def act(self, view):
        self.seen.append((view.t, tuple((x.t_request, x.t_release) for x in view.released)))
        return Paper3Decision(0, int(view.t in self.qat and view.labels_remaining > 0))


def test_regime_count_and_seed_blocks_disjoint():
    assert len(REG) == 24
    blocks = sorted(seed_blocks().values())
    assert all(a[1] < b[0] for a, b in itertools.pairwise(blocks))
    assert blocks[0][0] > 3_200_000_000
    assert len(seeds_for("smoke", 5)) == 5
    with pytest.raises(ValueError):
        seeds_for("smoke", 10**7)


def test_queue_never_releases_early_and_clock_monotone():
    q2 = PendingFeedbackQueue()
    q2.request(3, "a", 4)
    q2.request(4, "b", 1)
    assert q2.release(4) == []
    assert q2.release(5) == [(5, 4, "b")]
    assert q2.release(6) == []
    assert q2.release(7) == [(7, 3, "a")]
    with pytest.raises(ValueError):
        q2.release(6)
    with pytest.raises(ValueError):
        q2.request(8, "x", 0)
    assert q2.delay_log == [(3, 4, 7), (4, 1, 5)]


def test_release_timing_in_loop_and_no_unreleased_in_view():
    tape, _ = _tape("random_delay")
    spec = make_spec(REG["random_delay"], T)
    pol = Recorder(range(1, 30))
    run_policy(pol, tape, spec, 0)
    for t, rel in pol.seen:
        for treq, trel in rel:
            assert trel == t and treq + tape.delay[treq - 1] == t
    # delay_known absent for random delays; every label arrives exactly delay later
    n_rel = sum(len(r) for _, r in pol.seen)
    assert n_rel == sum(1 for t in range(1, 30) if t + tape.delay[t - 1] <= T)


def test_view_has_no_future_access():
    tape, _ = _tape()
    spec = make_spec(REG["abrupt_beneficial"], T)

    class Cheat(PolicyAdapter):
        name = "cheat"

        def reset(self, spec, rng):
            pass

        def act(self, view):
            for attr in ("tape", "ell", "truth", "future", "queue"):
                with pytest.raises(AttributeError):
                    getattr(view, attr)
            with pytest.raises(AttributeError):
                view.t = 99  # frozen
            return Paper3Decision(0)

    run_policy(Cheat(), tape, spec, 0)
    with pytest.raises(ValueError):  # the tape arrays are read-only
        tape.ell[0, 0] = 5.0


def test_pending_reservation_at_request_time():
    tape, _ = _tape()
    spec = ProblemSpec(T=T, B=3, costs=Costs())

    class Q(PolicyAdapter):
        name = "q"

        def reset(self, spec, rng):
            self.log = []

        def act(self, view):
            self.log.append((view.t, view.labels_remaining, view.labels_pending))
            return Paper3Decision(0, int(view.t <= 5))

    p = Q()
    with pytest.raises(BudgetError):
        run_policy(p, tape, spec, 0)  # 5 requests > B=3
    # the 3rd request already reduced remaining to 0 while all 3 were still pending
    assert (4, 0, 3) in p.log


@pytest.mark.parametrize("seed", range(40))
def test_random_policy_never_exceeds_budget(seed):
    rname = list(REG)[seed % 24]
    tape, _ = generate_tape(REG[rname], 100 + seed, 80)
    spec = make_spec(REG[rname], 80)
    rec = run_policy(RandomPolicy(), tape, spec, seed)
    assert rec.q.sum() <= spec.B
    assert rec.ledger["n_queries"] == rec.q.sum()


def test_identical_tapes_across_policies_and_seeds_reproducible():
    t1, _ = _tape(seed=5)
    t2, _ = _tape(seed=5)
    t3, _ = _tape(seed=6)
    assert np.array_equal(t1.ell, t2.ell) and not np.array_equal(t1.ell, t3.ell)
    before = t1.ell.copy()
    spec = make_spec(REG["abrupt_beneficial"], T)
    for pol in default_baselines(T):
        run_policy(pol, t1, spec, 0)
    assert np.array_equal(t1.ell, before)
    ev = SimulationEvaluator(t1, _tape(seed=5)[1], spec.costs)
    a = run_policy(NeverSwitch(), t1, spec, 0)
    assert ev.evaluate(a)["J"] == ev.J_never  # same tape => identical never-switch J


def test_marginals_and_dependence():
    r = dict(REG["dep_rho_0.95"].params)
    tp, tr = generate_tape(REG["dep_rho_0.95"], 3, 20000)
    dis = tp.disagree
    z = (tp.ell[:, 0] - tp.ell[:, 1])[dis]
    late = tr.p[dis] > 0.6
    assert abs((z[late] > 0).mean() - 0.7) < 0.03
    zz = (tp.ell[:, 0] - tp.ell[:, 1]) * (tr.p > 0.6)
    c = np.corrcoef(zz[:-1], zz[1:])[0, 1]
    tp0, tr0 = generate_tape(REG["dep_rho_0.0"], 3, 20000)
    zz0 = (tp0.ell[:, 0] - tp0.ell[:, 1]) * (tr0.p > 0.6)
    assert c > np.corrcoef(zz0[:-1], zz0[1:])[0, 1] + 0.05
    assert r["rho"] == 0.95


def test_zero_query_boundary_and_never_switch_fallback():
    tape, truth = _tape()
    spec = make_spec(REG["abrupt_beneficial"], T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    out = ev.evaluate(run_policy(NeverSwitch(), tape, spec, 0))
    assert out["n_queries"] == 0 and out["n_switches"] == 0
    assert out["J"] == pytest.approx(tape.ell[:, 0].sum())
    # B=0: every baseline degrades to a no-label policy and still runs
    spec0 = ProblemSpec(T=T, B=0, costs=spec.costs, delay_known=5)
    for pol in default_baselines(T):
        assert run_policy(pol, tape, spec0, 0).q.sum() == 0


def test_full_feedback_boundary():
    tape, _ = _tape()
    spec = ProblemSpec(T=T, B=T, costs=Costs(c_q=0.0, k=0.0), delay_known=5)
    pol = Recorder(range(1, T + 1))
    rec = run_policy(pol, tape, spec, 0)
    assert rec.q.sum() == T
    assert rec.ledger["n_released"] == T - 5  # last d labels never arrive, still paid
    assert rec.ledger["n_pending_end"] == 5


def test_switch_cost_extremes():
    tape, _ = _tape("stationary_better")
    spec = make_spec(REG["stationary_better"], T)
    zero = ProblemSpec(T=T, B=spec.B, costs=Costs(c_q=0.0, k=0.0), delay_known=5)
    huge = ProblemSpec(T=T, B=spec.B, costs=Costs(c_q=0.05, k=1e6), delay_known=5)
    w = lambda: WaldEconomic(name="w")
    assert run_policy(w(), tape, huge, 0).ledger["n_switches"] == 0
    assert hindsight_oracle_cost(tape.ell, 0.0) == pytest.approx(
        np.minimum(tape.ell[:, 0], tape.ell[:, 1]).sum()
    )
    assert hindsight_oracle_cost(tape.ell, 1e6) == pytest.approx(tape.ell[:, 0].sum())
    run_policy(w(), tape, zero, 0)


def test_delay_longer_than_horizon():
    tape, _ = generate_tape(REG["abrupt_beneficial"], 1, 40)
    spec = ProblemSpec(T=40, B=10, costs=Costs(), delay_known=500)
    big = Tape(tape.ell, tape.disagree, tape.x, np.full(40, 500), tape.meta)
    rec = run_policy(Recorder(range(1, 10)), big, spec, 0)
    assert rec.ledger["n_released"] == 0 and rec.ledger["n_pending_end"] == 9
    assert rec.ledger["label_fee"] == pytest.approx(9 * 0.05)  # pending is not free at horizon


def test_accounting_identities_all_baselines_all_regimes():
    for rname, reg in REG.items():
        tape, truth = generate_tape(reg, 7, 100)
        spec = make_spec(reg, 100)
        ev = SimulationEvaluator(tape, truth, spec.costs)
        for pol in default_baselines(100):
            rec = run_policy(pol, tape, spec, 3)
            L = rec.ledger
            parts = (
                L["deploy_loss"]
                + L["label_fee"]
                + L["switch_fee"]
                + L["compute_fee"]
                + L["retrain_fee"]
            )
            assert L["J"] == pytest.approx(parts)
            assert L["deploy_loss"] == pytest.approx(tape.ell[np.arange(100), rec.a].sum())
            assert L["n_switches"] == int((np.r_[0, rec.a[:-1]] != rec.a).sum())
            out = ev.evaluate(rec)
            assert out["regret_hindsight_UNATTAINABLE"] >= -1e-9, (rname, pol.name)


def test_ledger_checks_detect_violations():
    led = BudgetLedger(2, Costs())
    led.request_query()
    led.request_query()
    with pytest.raises(BudgetError):
        led.request_query()
    led.released = 5
    with pytest.raises(AssertionError):
        led.check()
    led2 = BudgetLedger(5, Costs(), compute_budget=1)
    led2.use_compute()
    with pytest.raises(BudgetError):
        led2.use_compute()


def test_gate_blocks_promotion_under_null():
    from shiftlab.paper3.baselines import Gate

    reg = REG["stationary_null"]
    spec = make_spec(reg, 300)
    promos = 0
    for s in range(60):
        tape, _ = generate_tape(reg, 900 + s, 300)
        rec = run_policy(Gate(WaldEconomic(0.9, 0.5, name="w"), alpha=0.1), tape, spec, s)
        promos += int(rec.a.max() > 0)
    assert promos / 60 <= 0.2  # alpha=.1 with sampling slack (a guarantee check, not tuned)
