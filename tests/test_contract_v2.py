"""Tests for the v2 contract harness: delay, pending reservation, missing feedback, switching."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from shiftlab.contract import PublicEvent, TaskSpec
from shiftlab.contract.baselines import GatedHTFixed, GatedHTPaced, UniformHT
from shiftlab.contract.baselines_v2 import (
    AlarmThenSwitch,
    DelayedHT,
    OutOfOrderRelease,
    V1MonitorShim,
)
from shiftlab.contract.harness import run_monitor
from shiftlab.contract.harness_v2 import run_monitor_v2
from shiftlab.contract.interface import Feedback
from shiftlab.contract.interface_v2 import MissingFeedback, PendingQuery
from shiftlab.real_tasks import HoldoutAccessError
from shiftlab.real_tasks import opsd_reserve as op
from shiftlab.real_tasks.v2_smoke import run_task_v2


def _spec(n, budget=1000.0, price=(0.5, 2.5), alpha=0.05):
    return TaskSpec(5.0, 0.1, alpha, n, budget, price)


def _events(n, every=2):
    return [PublicEvent(i, np.zeros(2), int(i % every == 0), 0, False, 0.0, 0.0) for i in range(n)]


class _Spy:
    """Constant-q v2 monitor that records every call; log_e is a deterministic function of Z."""

    def __init__(self, q=0.5):
        self.q = q
        self.recv: list[tuple[int, tuple]] = []
        self.obs: list[tuple[PublicEvent, object]] = []
        self.log = 0.0

    def reset(self, spec):
        self.recv, self.obs, self.log = [], [], 0.0

    def receive(self, t, released):
        self.recv.append((t, tuple(released)))
        for item in released:
            if isinstance(item, Feedback):
                self.log += item.paired_cost

    def propensity(self, event):
        return self.q

    def observe(self, event, outcome):
        self.obs.append((event, outcome))
        if isinstance(outcome, Feedback):
            self.log += outcome.paired_cost

    @property
    def log_e_value(self):
        return self.log


def _stream(seed, n=300):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 3))
    active = rng.random(n) < 0.3
    paired = np.clip(rng.normal(0.3, 1.0, n), -5, 5)
    return x, active, paired, rng.random(n), rng.uniform(0.5, 2.5, n)


# ------------------------------------------------------------------ v1 parity


@pytest.mark.parametrize("seed", [1, 2])
@pytest.mark.parametrize("kind", ["fixed", "paced", "uniform"])
@pytest.mark.parametrize("wrap", ["shim", "delayed"])
def test_v1_parity_at_zero_delay_and_no_missing(seed, kind, wrap):
    n = 400
    x, active, paired, coins, tariffs = _stream(seed, n)
    val = _stream(seed + 50, 300)
    kwargs = {
        "validation_disagreement": val[1],
        "validation_tariffs": val[4],
        "budget_rate": 0.15,
    }

    def make():
        if kind == "fixed":
            return GatedHTFixed(**kwargs)
        if kind == "paced":
            return GatedHTPaced(**kwargs)
        return UniformHT(0.15)

    events = [PublicEvent(i, x[i], int(active[i]), 0, False, 0.0, 0.0) for i in range(n)]
    spec = TaskSpec(5.0, 0.1, 0.05, n, 0.15 * n * 1.5, (0.5, 2.5))
    v1 = run_monitor(make(), spec, events, paired, coins, tariffs)
    monitor = V1MonitorShim(make()) if wrap == "shim" else DelayedHT(make())
    v2 = run_monitor_v2(monitor, spec, events, paired, coins, tariffs, np.arange(n))
    for name in ("log_e", "propensities", "queried", "refused", "spend"):
        np.testing.assert_array_equal(getattr(v2, name), getattr(v1, name), err_msg=name)
    for name in ("total_spend", "budget", "first_alarm", "processed", "stopped_early"):
        assert getattr(v2, name) == getattr(v1, name), name
    assert v2.pending_at_end == 0 and v2.n_missing_delivered == 0
    assert v2.n_switches == 0 and set(v2.actions.tolist()) <= {0}


def test_shim_rejects_delay():
    n = 20
    with pytest.raises((TypeError, ValueError), match="v1 monitor"):
        run_monitor_v2(
            V1MonitorShim(UniformHT(1.0)),
            _spec(n),
            _events(n),
            np.zeros(n),
            np.zeros(n),
            np.ones(n),
            np.arange(n) + 2,
        )


# ------------------------------------------------------------------ delay semantics


def test_delay_never_early_and_feedback_carries_original_index():
    n = 300
    rng = np.random.default_rng(3)
    costs = rng.uniform(-1, 1, n)
    release = np.arange(n) + rng.integers(1, 9, n)  # varying delays: out-of-order arrivals
    spy = _Spy(0.6)
    res = run_monitor_v2(spy, _spec(n, 1e6), _events(n), costs, rng.random(n), np.ones(n), release)
    seen: dict[int, int] = {}
    for round_, items in spy.recv:
        for item in items:
            assert item.t not in seen  # delivered exactly once
            seen[item.t] = round_
            assert round_ >= release[item.t] and round_ > item.t  # never early
            assert round_ == release[item.t]  # and exactly at release
            assert isinstance(item, Feedback)
            want = costs[item.t] if item.t % 2 == 0 else 0.0
            assert item.paired_cost == want and item.propensity == 0.6
    # Within a round items are ordered by event index; across rounds order is the release order.
    order = [item.t for _, items in spy.recv for item in items]
    assert any(a > b for a, b in itertools.pairwise(order))  # genuinely out of order
    # Observe never carries a payload for a delayed query, only a PendingQuery receipt.
    for event, outcome in spy.obs:
        assert outcome is None or isinstance(outcome, PendingQuery)
    assert res.n_feedback_delivered == len(seen)
    assert res.pending_at_end == res.queried.sum() - len(seen)
    assert all(r == release[t] for r, t, _ in res.deliveries)


def test_zero_delay_is_delivered_same_round_in_observe():
    n = 50
    spy = _Spy(1.0)
    run_monitor_v2(
        spy, _spec(n, 1e6), _events(n), np.ones(n), np.zeros(n), np.ones(n), np.arange(n)
    )
    assert all(not items for _, items in spy.recv)
    assert all(isinstance(o, Feedback) and o.t == e.t for e, o in spy.obs)


def test_release_before_own_round_is_clamped_to_same_round():
    n = 10
    spy = _Spy(1.0)
    run_monitor_v2(
        spy, _spec(n, 1e6), _events(n), np.ones(n), np.zeros(n), np.ones(n), np.zeros(n, dtype=int)
    )
    assert all(not items for _, items in spy.recv)
    assert all(isinstance(o, Feedback) for _, o in spy.obs)


def test_label_value_cannot_leak_before_release():
    n = 120
    rng = np.random.default_rng(5)
    base = rng.uniform(-1, 1, n)
    coins = np.zeros(n)
    release = np.arange(n) + 4
    runs = []
    for tweak in (0.0, 3.0):
        costs = base.copy()
        costs[40] += tweak  # event 40 is a disagreement (even), released at round 44
        res = run_monitor_v2(
            DelayedHT(UniformHT(1.0)),
            _spec(n, 1e6),
            _events(n),
            costs,
            coins,
            np.ones(n),
            release,
        )
        runs.append(res.log_e)
    np.testing.assert_array_equal(runs[0][:44], runs[1][:44])
    assert runs[0][44] != runs[1][44]


# ------------------------------------------------------------------ pending reservation


def test_pending_queries_count_against_budget_and_never_overdraw():
    n = 60
    spy = _Spy(1.0)
    res = run_monitor_v2(
        spy,
        _spec(n, budget=10.0, price=(1.0, 1.0)),
        _events(n, 1),
        np.zeros(n),
        np.zeros(n),
        np.ones(n),
        np.arange(n) + 1000,  # nothing is ever released
        stop_when_reserve_below_max_price=False,
    )
    assert res.total_spend <= 10.0 + 1e-9
    assert res.queried.sum() == 10 and res.refused[10:].all() and not res.refused[:10].any()
    assert res.pending_at_end == 10 and res.pending_spend_at_end == 10.0  # never refunded
    assert res.n_feedback_delivered == 0 and res.max_pending == 10
    # The event the monitor sees already excludes pending reservations.
    seen = [e.remaining_budget for e, _ in spy.obs]
    assert seen[:3] == [10.0, 9.0, 8.0] and seen[10] == 0.0
    assert all(o is None for (_, o) in spy.obs[10:])


def test_budget_holds_with_random_prices_delays_and_reserve_stop():
    for seed in range(5):
        n = 400
        rng = np.random.default_rng(seed)
        spy = _Spy(0.8)
        res = run_monitor_v2(
            spy,
            _spec(n, 40.0),
            _events(n),
            rng.uniform(-1, 1, n),
            rng.random(n),
            rng.uniform(0.5, 2.5, n),
            np.arange(n) + rng.integers(0, 30, n),
        )
        assert res.total_spend <= 40.0 + 1e-9
        assert res.spend.sum() == pytest.approx(res.total_spend)
        # remaining budget is budget minus everything charged so far, pending included
        cum = np.concatenate([[0.0], np.cumsum(res.spend)[:-1]])
        got = np.array([e.remaining_budget for e, _ in spy.obs])
        np.testing.assert_allclose(got, 40.0 - cum)


def test_pending_info_reaches_switcher_context():
    n = 20
    ctx = []

    class Probe(_Spy):
        def choose(self, event, context):
            ctx.append(context)
            return 0

    run_monitor_v2(
        Probe(1.0),
        _spec(n, 1e6, (1.0, 1.0)),
        _events(n, 1),
        np.zeros(n),
        np.zeros(n),
        np.ones(n),
        np.arange(n) + 3,
        query_cost=0.2,
        switch_cost=0.7,
    )
    assert [c.pending_queries for c in ctx[:5]] == [
        0,
        1,
        2,
        2,
        2,
    ]  # query 0 is released before round 3 chooses
    assert ctx[4].pending_spend == 2.0 and ctx[4].query_cost == 0.2 and ctx[4].switch_cost == 0.7


# ------------------------------------------------------------------ missing feedback


def test_missing_feedback_is_delivered_at_release_and_charged():
    n = 40
    observed = np.ones(n, dtype=bool)
    observed[[4, 6, 7]] = False  # 4 and 6 are disagreements, 7 an agreement
    spy = _Spy(1.0)
    prices = np.full(n, 1.5)
    res = run_monitor_v2(
        spy,
        _spec(n, 1e6),
        _events(n),
        np.where(observed, 0.5, np.nan),  # NaN would raise if read for a missing label
        np.zeros(n),
        prices,
        np.arange(n) + 3,
        observed=observed,
    )
    miss = {i.t: r for r, items in spy.recv for i in items if isinstance(i, MissingFeedback)}
    assert miss == {4: 7, 6: 9}
    for _, items in spy.recv:
        for item in items:
            if isinstance(item, MissingFeedback):
                assert item.propensity == 1.0  # no paired_cost attribute: no Z
                assert not hasattr(item, "paired_cost")
    assert res.n_missing_delivered == 2
    assert res.queried[4] and res.spend[4] == 1.5 and res.queried[6] and res.spend[6] == 1.5
    # A queried agreement is Z = 0 by contract even if its label is missing.
    zero = [i for _, items in spy.recv for i in items if i.t == 7]
    assert zero == [Feedback(7, 0.0, 1.0)]
    assert res.total_spend == pytest.approx(1.5 * res.queried.sum())


def test_missing_on_agreement_option_and_same_round_missing():
    n = 8
    observed = np.ones(n, dtype=bool)
    observed[[1, 2]] = False
    spy = _Spy(1.0)
    res = run_monitor_v2(
        spy,
        _spec(n, 1e6),
        _events(n),
        np.zeros(n),
        np.zeros(n),
        np.ones(n),
        np.arange(n),
        observed=observed,
        missing_on_agreement=True,
    )
    outcomes = {e.t: o for e, o in spy.obs}
    assert outcomes[1] == MissingFeedback(1, 1.0) and outcomes[2] == MissingFeedback(2, 1.0)
    assert res.n_missing_delivered == 2 and res.queried[1] and res.queried[2]


def test_delayed_ht_handles_missing_and_matches_unobserved_term():
    n = 60
    rng = np.random.default_rng(1)
    costs = rng.uniform(-1, 1, n)
    observed = rng.random(n) > 0.3
    ref = run_monitor(
        UniformHT(1.0),
        _spec(n, 1e6),
        _events(n),
        np.where(observed, costs, 0.0),  # missing label contributes an HT term of 0
        np.zeros(n),
        np.ones(n),
    )
    res = run_monitor_v2(
        DelayedHT(UniformHT(1.0)),
        _spec(n, 1e6),
        _events(n),
        costs,
        np.zeros(n),
        np.ones(n),
        np.arange(n),
        observed=observed,
    )
    np.testing.assert_array_equal(res.log_e, ref.log_e)
    assert res.n_missing_delivered == int(((~observed) & (np.arange(n) % 2 == 0)).sum())


def _tap(mon):
    updates = []
    real = mon._inner._process.update

    def spy(value, bound=None):
        updates.append((round(value, 12), bound))
        return real(value, bound=bound)

    mon._inner._process.update = spy
    return updates


def test_delayed_ht_missing_label_applies_minus_epsilon_at_release_not_skip():
    """A queried disagreement with a missing label updates the e-process with -epsilon."""
    spec = TaskSpec(1.0, 0.1, 0.05, 10, 1000.0, (1.0, 1.0))
    mon = DelayedHT(UniformHT(1.0))
    mon.reset(spec)
    updates = _tap(mon)
    e0 = PublicEvent(0, np.zeros(1), 1, 0, True, 1.0, 0.0)
    assert mon.propensity(e0) == 1.0
    mon.observe(e0, PendingQuery(0, 1.0))
    assert updates == []  # nothing applied while pending
    mon.receive(1, (MissingFeedback(0, 1.0),))
    assert updates == [(-0.1, 1.1)]  # -epsilon at release, update not skipped
    e1 = PublicEvent(1, np.zeros(1), 1, 0, True, 1.0, 0.0)
    mon.propensity(e1)
    mon.observe(e1, MissingFeedback(1, 1.0))  # same-round missing feedback
    assert updates[-1][0] == -0.1 and len(updates) == 2


def test_delayed_ht_gated_missing_label_is_minus_epsilon():
    spec = TaskSpec(1.0, 0.1, 0.05, 10, 1000.0, (1.0, 1.0))
    mon = DelayedHT(
        GatedHTFixed(
            validation_disagreement=np.ones(5, bool),
            validation_tariffs=np.ones(5),
            budget_rate=0.5,
        )
    )
    mon.reset(spec)
    updates = _tap(mon)
    e0 = PublicEvent(0, np.zeros(1), 1, 0, True, 1.0, 0.0)
    q = mon.propensity(e0)
    mon.observe(e0, PendingQuery(0, q))
    mon.receive(2, (MissingFeedback(0, q),))
    assert [u[0] for u in updates] == [-0.1]


def _deliver(mon, order):
    mon.reset(TaskSpec(1.0, 0.0, 0.05, 10, 1000.0, (1.0, 1.0)))
    events = [PublicEvent(i, np.zeros(1), 1, 0, True, 1.0, 0.0) for i in range(3)]
    for e in events:
        mon.propensity(e)
        mon.observe(e, PendingQuery(e.t, 1.0))
    for t in order:
        mon.receive(5, (Feedback(t, 0.5, 1.0),))


def test_delayed_ht_rejects_out_of_order_release_unless_flagged():
    _deliver(DelayedHT(UniformHT(1.0)), [0, 1, 2])  # event order: fine
    with pytest.raises(OutOfOrderRelease):
        _deliver(DelayedHT(UniformHT(1.0)), [1, 0, 2])
    _deliver(DelayedHT(UniformHT(1.0), allow_out_of_order=True), [2, 0, 1])  # diagnostics only
    mon = DelayedHT(UniformHT(1.0))  # a same-round delivery followed by an earlier pending label
    mon.reset(TaskSpec(1.0, 0.0, 0.05, 10, 1000.0, (1.0, 1.0)))
    e0 = PublicEvent(0, np.zeros(1), 1, 0, True, 1.0, 0.0)
    e1 = PublicEvent(1, np.zeros(1), 1, 0, True, 1.0, 0.0)
    mon.propensity(e0)
    mon.observe(e0, PendingQuery(0, 1.0))
    mon.propensity(e1)
    mon.observe(e1, Feedback(1, 0.5, 1.0))
    with pytest.raises(OutOfOrderRelease):
        mon.receive(3, (Feedback(0, 0.5, 1.0),))


# ------------------------------------------------------------------ switching accounting


class _Scripted(_Spy):
    def __init__(self, plan, q=0.0):
        super().__init__(q)
        self.plan = plan

    def choose(self, event, context):
        return self.plan[event.t]


def test_switching_cost_and_net_utility_accounting():
    n = 12
    l0 = np.linspace(0.1, 0.9, n)
    l1 = l0[::-1].copy()
    plan = np.zeros(n, dtype=int)
    plan[3:7] = 1  # 0->1 at 3, 1->0 at 7
    plan[9:] = 1  # 0->1 at 9
    c, k = 0.03, 0.2
    spy = _Scripted(plan, q=0.0)
    res = run_monitor_v2(
        spy,
        _spec(n, 1e6),
        _events(n),
        np.zeros(n),
        np.ones(n) * 0.99,
        np.ones(n),
        np.arange(n),
        loss_incumbent=l0,
        loss_candidate=l1,
        query_cost=c,
        switch_cost=k,
    )
    assert res.switch_times == (3, 7, 9) and res.n_switches == 3 and res.n_queries == 0
    np.testing.assert_array_equal(res.actions, plan)
    deployed = np.where(plan == 0, l0, l1).sum()
    assert res.deployed_loss_sum == pytest.approx(deployed)
    assert res.net_utility == pytest.approx(-deployed - k * 3)
    assert res.net_cost == pytest.approx(deployed + 3 * k)
    assert res.loss_sum_always_incumbent == pytest.approx(l0.sum())
    assert res.loss_sum_always_candidate == pytest.approx(l1.sum())
    assert res.false_promotions is None  # no evaluator null indicator supplied


def test_query_cost_counts_bought_queries_and_switch_at_round_zero_counts():
    n = 10
    plan = np.ones(n, dtype=int)  # A_0 = 0 is the reference, so round 0 -> 1 is a switch
    spy = _Scripted(plan, q=1.0)
    res = run_monitor_v2(
        spy,
        _spec(n, 1e6),
        _events(n),
        np.zeros(n),
        np.zeros(n),
        np.ones(n),
        np.arange(n) + 2,
        loss_incumbent=np.full(n, 0.5),
        loss_candidate=np.full(n, 0.25),
        query_cost=0.01,
        switch_cost=0.3,
    )
    assert res.switch_times == (0,) and res.n_queries == n
    assert res.net_utility == pytest.approx(-0.25 * n - 0.01 * n - 0.3)
    # pending queries (released after the end) are still charged
    assert res.pending_at_end == 2 and res.total_spend == pytest.approx(n)


def test_false_promotions_use_evaluator_null_indicator():
    n = 12
    plan = np.zeros(n, dtype=int)
    plan[2:5] = 1
    plan[8:] = 1
    null = np.zeros(n, dtype=bool)
    null[:6] = True  # promotion at 2 is inside the null, the one at 8 is not
    res = run_monitor_v2(
        _Scripted(plan),
        _spec(n, 1e6),
        _events(n),
        np.zeros(n),
        np.ones(n) * 0.9,
        np.ones(n),
        np.arange(n),
        null_round=null,
    )
    assert res.switch_times == (2, 5, 8) and res.false_promotions == (2,)
    assert res.net_utility is None  # no losses supplied


def test_nan_losses_are_excluded_and_counted():
    n = 6
    l0 = np.array([0.1, np.nan, 0.3, 0.4, 0.5, 0.6])
    l1 = np.array([0.2, 0.2, np.nan, 0.1, 0.1, 0.1])
    plan = np.array([0, 0, 1, 1, 1, 1])
    res = run_monitor_v2(
        _Scripted(plan),
        _spec(n, 1e6),
        _events(n),
        np.zeros(n),
        np.ones(n) * 0.9,
        np.ones(n),
        np.arange(n),
        loss_incumbent=l0,
        loss_candidate=l1,
        switch_cost=0.1,
    )
    assert res.n_loss_missing == 2
    assert res.deployed_loss_sum == pytest.approx(0.1 + 0.1 * 3)
    assert res.net_utility == pytest.approx(-(0.1 + 0.3) - 0.1)


def test_invalid_switch_choice_raises_and_non_switcher_stays_incumbent():
    n = 5
    with pytest.raises(ValueError, match="expected 0 or 1"):
        run_monitor_v2(
            _Scripted([0, 2, 0, 0, 0]),
            _spec(n),
            _events(n),
            np.zeros(n),
            np.ones(n) * 0.9,
            np.ones(n),
            np.arange(n),
        )
    res = run_monitor_v2(
        _Spy(0.0),
        _spec(n),
        _events(n),
        np.zeros(n),
        np.ones(n) * 0.9,
        np.ones(n),
        np.arange(n),
        loss_incumbent=np.full(n, 0.5),
        loss_candidate=np.zeros(n),
        switch_cost=9.0,
    )
    assert res.n_switches == 0 and res.net_utility == pytest.approx(-0.5 * n)


def test_alarm_then_switch_switches_after_first_alarm_and_never_back():
    n = 80
    # Every event queried with constant positive Z: UniformHT crosses the threshold.
    mon = AlarmThenSwitch(DelayedHT(UniformHT(1.0)))
    res = run_monitor_v2(
        mon,
        _spec(n, 1e6),
        _events(n, 1),
        np.full(n, 1.0),
        np.zeros(n),
        np.ones(n),
        np.arange(n) + 2,
        loss_incumbent=np.full(n, 0.8),
        loss_candidate=np.full(n, 0.2),
        switch_cost=0.5,
    )
    assert res.first_alarm is not None
    assert res.n_switches == 1
    # The alarm is visible at the start of a round (after that round's releases), so the switch
    # happens at the first alarm round or the next one, never before the log e-value crosses.
    threshold = -np.log(0.05)
    assert res.switch_times[0] in (res.first_alarm, res.first_alarm + 1)
    assert res.log_e[res.switch_times[0] - 1] < threshold
    assert res.log_e[res.switch_times[0]] >= threshold
    assert (res.actions[: res.switch_times[0]] == 0).all()
    assert (res.actions[res.switch_times[0] :] == 1).all()
    # No alarm, no switch.
    quiet = run_monitor_v2(
        AlarmThenSwitch(DelayedHT(UniformHT(1.0))),
        _spec(n, 1e6),
        _events(n, 1),
        np.full(n, -1.0),
        np.zeros(n),
        np.ones(n),
        np.arange(n) + 2,
    )
    assert quiet.n_switches == 0


# ------------------------------------------------------------------ real-task adapter and holdout


def test_real_task_adapter_uses_declared_release_and_holdout_guard_intact():
    from test_real_tasks import _opsd_series

    tasks, _ = op.build_opsd_tasks(_opsd_series())
    task = tasks["development"]
    coins = np.random.default_rng(0).random(len(task))
    res = run_task_v2(task, DelayedHT(UniformHT(0.10)), 0.10, coins)
    out = task.outcomes
    assert set(out.delay_rounds()[out.released].tolist()) == {2}  # calendar d = 2, no other delay
    assert int((~out.released).sum()) == 2  # terminal labels are unreleased, never delivered
    assert len(res.deliveries) <= int(out.released.sum())
    for round_, t, _ in res.deliveries:
        assert round_ == task.outcomes.release_round[t]
    assert res.total_spend <= task.task_spec(0.10).label_budget + 1e-9
    assert res.net_utility is not None and res.n_switches == 0
    # The development window ends before the holdout, and the guards still refuse it.
    assert str(task.public.round_time.max().astype("datetime64[D]")) < "2020-01-01"
    series = _opsd_series()
    with pytest.raises(HoldoutAccessError):
        op.build_opsd_tasks(
            series, windows=(("holdout", np.datetime64("2020-01-01"), np.datetime64("2020-03-31")),)
        )
