"""Guard tests for the common operational contract (WP2).

Every test here is a detector: it either runs a deliberately defective policy / simulator and asserts
that the guard fires, or checks an invariant that such a defect would break.
"""
# ruff: noqa: B008, B017, RUF007

from __future__ import annotations

import copy
import time
from pathlib import Path

import numpy as np
import pytest
import yaml

from shiftlab.bench.contract import (
    Action,
    ActionNotAllowed,
    AlwaysContinue,
    AuditViolation,
    BudgetExceeded,
    BudgetSpec,
    ClockSpec,
    ConfirmationAccessError,
    DelaySpec,
    EnvSpec,
    LabelNotReleased,
    LeakError,
    Simulator,
    StreamSpec,
    UniformQueryNaiveSwitch,
    UnpairedError,
    list_families,
    load_cost_vectors,
    load_family,
    make_stream,
    paired_bootstrap_ci,
    run_paired,
    verify_run,
)
from shiftlab.bench.contract.paired import PairedRuns, assert_paired
from shiftlab.bench.contract.policies import (
    ActionSpamPolicy,
    BasePolicy,
    LeakyPendingPolicy,
    LeakyStreamPolicy,
    LeakyTruthPolicy,
    OverspendPolicy,
    SwallowingLeakPolicy,
)
from shiftlab.bench.contract.types import CANDIDATE, RETRAINED, cost_vector_fingerprint

ROOT = Path(__file__).resolve().parents[2]
COSTS = load_cost_vectors()["balanced"]


def env_of(T=200, cap=30, **kw) -> EnvSpec:
    clocks = kw.pop("clocks", ClockSpec(retrain_duration=10))
    budget = kw.pop("budget", BudgetSpec(label_cap=cap))
    return EnvSpec(T=T, costs=COSTS, budget=budget, clocks=clocks, **kw)


def spec_of(T=200, delay=DelaySpec("fixed", d=5), **kw) -> StreamSpec:
    return StreamSpec(family="t", T=T, delay=delay, **kw)


class Scripted(BasePolicy):
    """Plays a fixed {t: [actions]} script and records every observed state."""

    name = "scripted"

    def __init__(self, script):
        self.script, self.states = script, []

    def act(self, state):
        self.states.append(state)
        return self.script.get(state.t, Action("continue"))


# ---------------------------------------------------------------- label access before release
def test_labels_never_visible_before_release():
    spec = spec_of(delay=DelaySpec("uniform", lo=1, hi=25))
    stream = make_stream(spec, 1)
    pol = Scripted({t: Action("query") for t in range(1, 21)})
    res = Simulator(stream, env_of()).run(pol)
    for st in pol.states:
        for lab in st.H:
            assert lab.release_t <= st.t
            assert lab.release_t == lab.request_t + int(stream.delay[lab.request_t - 1])
    verify_run(res, stream)


def test_pending_label_value_is_a_trap():
    stream = make_stream(spec_of(delay=DelaySpec("fixed", d=50)), 2)
    with pytest.raises(LabelNotReleased):
        Simulator(stream, env_of()).run(LeakyPendingPolicy())


def test_early_release_fault_is_detected_by_audit():
    class EarlySim(Simulator):
        def _release_time(self, request_t, label_round=None):  # releases 3 rounds too early
            return request_t + int(self.stream.delay[request_t - 1]) - 3

    stream = make_stream(spec_of(), 3)
    res = EarlySim(stream, env_of()).run(Scripted({t: Action("query") for t in range(1, 11)}))
    with pytest.raises(AuditViolation, match="released at"):
        verify_run(res, stream)


def test_missing_label_must_never_release():
    spec = spec_of(
        missing=__import__("shiftlab.bench.contract", fromlist=["MissingSpec"]).MissingSpec(
            "bernoulli", p=1.0
        )
    )
    stream = make_stream(spec, 4)
    res = Simulator(stream, env_of()).run(Scripted({t: Action("query") for t in range(1, 11)}))
    assert res.audit.of("release") == []
    assert res.counts["N_q"] == 10  # still paid for
    verify_run(res, stream)

    class LeakyRelease(Simulator):
        def _release_time(self, request_t, label_round=None):
            return request_t + 2

    bad = LeakyRelease(stream, env_of()).run(Scripted({1: Action("query")}))
    with pytest.raises(AuditViolation):
        verify_run(bad, stream)


def test_out_of_order_release_is_delivered_in_release_order():
    stream = make_stream(spec_of(T=300, delay=DelaySpec("uniform", lo=1, hi=40)), 5)
    pol = Scripted({t: Action("query") for t in range(1, 31)})
    res = Simulator(stream, env_of(T=300, cap=30)).run(pol)
    labs = pol.states[-1].H
    inversions = [(a, b) for a, b in zip(labs, labs[1:]) if a.request_t > b.request_t]
    assert inversions, "uniform delays should reorder some labels"
    assert all(a.release_t <= b.release_t for a, b in zip(labs, labs[1:]))
    # a label requested earlier but released later is not visible before its release
    for st in pol.states:
        assert all(l.release_t <= st.t for l in st.H)
    verify_run(res, stream)


def test_label_beyond_horizon_is_charged_but_never_delivered():
    stream = make_stream(spec_of(T=50, delay=DelaySpec("fixed", d=100)), 6)
    res = Simulator(stream, env_of(T=50)).run(Scripted({1: Action("query")}))
    assert res.counts["N_q"] == 1 and not res.audit.of("release")
    assert res.breakdown["cost_N_q"] == COSTS.c_q
    verify_run(res, stream)


# ---------------------------------------------------------------- evaluator truth is unreachable
@pytest.mark.parametrize(
    "cls,arg",
    [(LeakyTruthPolicy, "truth"), (LeakyStreamPolicy, "stream"), (SwallowingLeakPolicy, "truth")],
)
def test_policy_reading_evaluator_truth_fails_the_run(cls, arg):
    stream = make_stream(spec_of(), 7)
    pol = cls(stream.truth if arg == "truth" else stream)
    with pytest.raises(LeakError):
        Simulator(stream, env_of()).run(pol)


def test_state_carries_no_evaluator_objects():
    stream = make_stream(spec_of(), 8)
    pol = Scripted({})
    Simulator(stream, env_of()).run(pol)
    st = pol.states[0]
    with pytest.raises(Exception):
        st.m = 1  # frozen
    assert not st.x_hist.flags.writeable
    for v in vars(st).values():
        assert type(v).__module__.split(".")[-1] != "streams"
    # outside a policy, evaluator access is allowed (evaluator code uses it)
    assert stream.truth.null_holds["marg"] in (True, False)


# ---------------------------------------------------------------- budgets
def test_label_budget_overspend_raises():
    stream = make_stream(spec_of(), 9)
    with pytest.raises(BudgetExceeded):
        Simulator(stream, env_of(cap=5)).run(OverspendPolicy())


def test_label_budget_refuse_mode_never_exceeds_and_never_charges_refusals():
    stream = make_stream(spec_of(), 10)
    res = Simulator(stream, env_of(cap=5), on_violation="refuse").run(OverspendPolicy())
    assert res.counts["N_q"] == 5
    refused = [a for a in res.audit.of("action") if a["reason"] == "budget_refused"]
    assert refused and all(a["charge"] == 0.0 and not a["performed"] for a in refused)
    verify_run(res, stream)


def test_pending_cap_and_intervention_caps():
    stream = make_stream(spec_of(delay=DelaySpec("fixed", d=50)), 11)
    env = env_of(budget=BudgetSpec(label_cap=50, pending_cap=3))
    with pytest.raises(BudgetExceeded, match="pending"):
        Simulator(stream, env).run(Scripted({t: Action("query") for t in range(1, 10)}))
    env2 = env_of(budget=BudgetSpec(label_cap=5, retrain_cap=1))
    pol = Scripted({1: Action("retrain"), 30: Action("retrain")})
    with pytest.raises(BudgetExceeded, match="retrain cap"):
        Simulator(stream, env2).run(pol)
    env3 = env_of(budget=BudgetSpec(label_cap=5, switch_cap=1))
    with pytest.raises(BudgetExceeded, match="switch cap"):
        Simulator(stream, env3).run(
            Scripted(
                {
                    1: Action("switch", target=CANDIDATE),
                    20: Action("rollback"),
                    30: Action("switch", target=CANDIDATE),
                }
            )
        )


def test_action_outside_declared_vocabulary_is_rejected():
    stream = make_stream(spec_of(), 12)
    env = env_of(allowed_actions=("query", "continue", "switch"))
    with pytest.raises(ActionNotAllowed):
        Simulator(stream, env).run(Scripted({3: Action("retrain")}))


# ---------------------------------------------------------------- cost accounting
def test_costs_only_for_performed_actions():
    stream = make_stream(spec_of(), 13)
    res = Simulator(stream, env_of(), on_violation="refuse").run(ActionSpamPolicy())
    refused = [a for a in res.audit.of("action") if not a["performed"]]
    assert refused and all(a["charge"] == 0.0 for a in refused)
    # per round at most one model-changing action, one retrain (only while none running), one alert
    changes = [
        a["t"]
        for a in res.audit.of("action")
        if a["performed"] and a["kind"] in ("switch", "rollback")
    ]
    assert len(changes) == len(set(changes)) == res.counts["N_s"] + res.counts["N_b"] > 0
    assert res.counts["N_r"] <= 200 // 10 + 1
    assert res.counts["N_a"] == 200  # one alert per round, in-round duplicates refused
    verify_run(res, stream)


def test_continue_is_free_and_always_continue_J_equals_incumbent_loss():
    stream = make_stream(spec_of(), 14)
    res = Simulator(stream, env_of()).run(AlwaysContinue())
    assert res.J == pytest.approx(stream.loss_inc.sum())
    assert all(v == 0 for k, v in res.counts.items())


def test_charging_fault_overcharge_is_detected():
    class Over(Simulator):
        def _charge(self, ledger, aid, kind):
            amt = self.env.costs.price(kind)
            ledger.charge(aid, kind, 2 * amt)
            return amt

    stream = make_stream(spec_of(), 15)
    res = Over(stream, env_of()).run(Scripted({1: Action("query"), 5: Action("alert")}))
    with pytest.raises(AuditViolation):
        verify_run(res, stream)


def test_charging_fault_phantom_charge_is_detected():
    class Phantom(Simulator):  # charges an action that was never performed
        def _charge(self, ledger, aid, kind):
            amt = super()._charge(ledger, aid, kind)
            ledger.charge(aid + 10**6, kind, amt)
            return amt

    stream = make_stream(spec_of(), 16)
    res = Phantom(stream, env_of()).run(Scripted({1: Action("query")}))
    with pytest.raises(AuditViolation):
        verify_run(res, stream)


def test_ledger_rejects_double_charge_of_one_action():
    class Twice(Simulator):
        def _charge(self, ledger, aid, kind):
            super()._charge(ledger, aid, kind)
            return super()._charge(ledger, aid, kind)

    stream = make_stream(spec_of(), 17)
    with pytest.raises(RuntimeError, match="charged twice"):
        Twice(stream, env_of()).run(Scripted({1: Action("alert")}))


def test_retrain_completion_deploy_is_free_and_not_a_second_switch():
    stream = make_stream(spec_of(), 18)
    pol = Scripted({1: Action("retrain"), 15: Action("switch", target=RETRAINED)})
    res = Simulator(stream, env_of(), on_violation="refuse").run(pol)
    assert res.counts["N_r"] == 1 and res.counts["N_s"] == 0
    deploys = res.audit.of("deploy")
    assert len(deploys) == 1 and deploys[0]["cause"] == "retrain_complete"
    assert res.breakdown["cost_N_r"] == COSTS.c_r and res.breakdown["cost_N_s"] == 0.0
    assert res.model_path[0] == 0 and res.model_path[-1] == RETRAINED
    verify_run(res, stream)


def test_manual_deploy_after_retrain_is_two_distinct_charged_actions():
    clocks = ClockSpec(retrain_duration=10, deploy_on_complete=False)
    stream = make_stream(spec_of(), 19)
    pol = Scripted({1: Action("retrain"), 15: Action("switch", target=RETRAINED)})
    res = Simulator(stream, env_of(clocks=clocks)).run(pol)
    assert res.counts["N_r"] == 1 and res.counts["N_s"] == 1
    verify_run(res, stream)


def test_one_payer_per_model_change_is_audited():
    stream = make_stream(spec_of(), 20)
    res = Simulator(stream, env_of()).run(
        Scripted({2: Action("switch", target=CANDIDATE), 30: Action("rollback")})
    )
    verify_run(res, stream)
    bad = copy.deepcopy(res)
    deps = bad.audit.of("deploy")
    deps[1]["charged_to"] = deps[0]["charged_to"]  # two changes billed to one action
    with pytest.raises(AuditViolation):
        verify_run(bad, stream)


def test_deploy_and_rollback_clocks():
    clocks = ClockSpec(deploy_lag=3, rollback_lag=2, retrain_duration=10)
    stream = make_stream(spec_of(), 21)
    res = Simulator(stream, env_of(clocks=clocks)).run(
        Scripted({10: Action("switch", target=CANDIDATE), 50: Action("rollback")})
    )
    mp = res.model_path
    assert mp[10 - 1] == 0 and mp[12 - 1] == 0 and mp[13 - 1] == 1  # effective t=13
    assert mp[51 - 1] == 1 and mp[52 - 1] == 0
    assert res.counts["N_s"] == 1 and res.counts["N_b"] == 1
    verify_run(res, stream)


def test_abstain_uses_fallback_loss_and_c_h():
    stream = make_stream(spec_of(), 22)
    res = Simulator(stream, env_of()).run(Scripted({5: Action("abstain")}))
    assert res.loss_path[4] == 0.5 and res.counts["N_h"] == 1
    verify_run(res, stream)


# ---------------------------------------------------------------- pairing
def test_paired_runs_share_streams_and_unpaired_is_rejected():
    spec, env = spec_of(), env_of()
    pol = {"a": AlwaysContinue, "b": lambda: UniformQueryNaiveSwitch()}
    pr = run_paired(pol, spec, env, seeds=range(6))
    assert pr.diff("a", "b").shape == (6,)
    other = run_paired(pol, spec, env, seeds=range(100, 106))
    with pytest.raises(UnpairedError, match="seed mismatch"):
        assert_paired(pr.runs["a"], other.runs["b"])
    with pytest.raises(UnpairedError):
        PairedRuns(pr.seeds, pr.fingerprints, {"a": pr.runs["a"], "b": other.runs["b"]}).diff(
            "a", "b"
        )
    # same seeds, different stream (spec) -> also unpaired
    other_spec = run_paired(pol, spec_of(p_during=0.6), env, seeds=range(6))
    with pytest.raises(UnpairedError):
        assert_paired(pr.runs["a"], other_spec.runs["b"])
    # reordered seeds
    with pytest.raises(UnpairedError):
        assert_paired(pr.runs["a"], list(reversed(pr.runs["b"])))


def test_stream_is_a_pure_function_of_spec_and_seed():
    a, b, c = make_stream(spec_of(), 5), make_stream(spec_of(), 5), make_stream(spec_of(), 6)
    assert a.fingerprint == b.fingerprint != c.fingerprint


def test_bootstrap_ci_brackets_known_mean_and_is_deterministic():
    rng = np.random.default_rng(0)
    d = rng.normal(2.0, 1.0, 200)
    m, lo, hi = paired_bootstrap_ci(d)
    assert lo < 2.0 < hi and (m, lo, hi) == paired_bootstrap_ci(d)


# ---------------------------------------------------------------- truth separation & families
def test_null_truth_flags_by_family():
    f = lambda n: make_stream(load_family(n), 1).truth.null_holds
    assert f("iid_null_boundary")["marg"] and f("iid_null_boundary")["cond"]
    mo = f("markov08_marg_null_only")
    assert mo["marg"] and not mo["cond"]  # Markov persistence breaks cond-null, not marg-null
    sh = f("iid_shift_d10")
    assert not sh["marg"] and not sh["cond"]


def test_all_dev_families_build_and_run():
    for name in list_families():
        spec = load_family(name)
        spec = StreamSpec(**{**spec.__dict__, "T": 120})
        stream = make_stream(spec, 3)
        res = Simulator(stream, env_of(T=120, cap=10)).run(UniformQueryNaiveSwitch())
        verify_run(res, stream)


def test_confirmation_families_are_held_out(monkeypatch):
    monkeypatch.delenv("D2A_CONFIRMATION_UNLOCK", raising=False)
    with pytest.raises(ConfirmationAccessError):
        load_family("anything", split="confirmation")
    with pytest.raises(ConfirmationAccessError):
        list_families("confirmation")


def test_seed_blocks_disjoint_and_unregistered_elsewhere():
    from shiftlab.bench.contract.streams import SEED_BLOCKS

    blocks = sorted(SEED_BLOCKS.values())
    assert all(a[1] < b[0] for a, b in zip(blocks, blocks[1:]))
    reg = yaml.safe_load((ROOT / "configs" / "seed_registry.yaml").read_text(encoding="utf8"))
    mine = {
        st["id"]: (st["start"], st["end"], st["status"])
        for st in reg["studies"]
        if st["id"].startswith("d2a_rar_")
    }
    assert mine == {
        "d2a_rar_contract_smoke": (*SEED_BLOCKS["smoke"], "smoke"),
        "d2a_rar_dev": (*SEED_BLOCKS["dev"], "development"),
        "d2a_rar_confirmation_reserved": (*SEED_BLOCKS["confirmation"], "confirmation"),
    }
    for st in reg["studies"]:
        if st["id"].startswith("d2a_rar_"):
            continue
        for lo, hi in blocks:
            assert hi < st["start"] or st["end"] < lo, st["id"]


# ---------------------------------------------------------------- frozen cost vectors
def test_cost_vectors_are_frozen_by_checksum(tmp_path):
    p = ROOT / "configs" / "d2a_rar" / "cost_vectors.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf8"))
    assert doc["frozen"] and len(doc["vectors"]) == 4
    assert cost_vector_fingerprint(doc["vectors"]) == doc["content_sha256"]
    doc["vectors"]["balanced"]["c_q"] = 0.06
    q = tmp_path / "cv.yaml"
    q.write_text(yaml.safe_dump(doc), encoding="utf8")
    with pytest.raises(ValueError, match="checksum"):
        load_cost_vectors(q)


# ---------------------------------------------------------------- smoke pair
def test_smoke_pair_end_to_end_under_30s():
    t0 = time.time()
    spec = load_family("iid_shift_d10")
    env = EnvSpec(
        T=spec.T,
        costs=COSTS,
        budget=BudgetSpec(label_cap=50),
        clocks=ClockSpec(retrain_duration=20),
    )
    pr = run_paired(
        {"always_continue": AlwaysContinue, "uniform_query_naive_switch": UniformQueryNaiveSwitch},
        spec,
        env,
        seeds=range(110_900_000, 110_900_020),
    )
    mean, lo, hi = pr.ci("uniform_query_naive_switch", "always_continue")
    assert np.isfinite([mean, lo, hi]).all() and lo <= mean <= hi
    for r in pr.runs["uniform_query_naive_switch"]:
        assert r.counts["N_q"] <= 50
    assert time.time() - t0 < 30


# ================================================================ WP2b
INCUMBENT_ID = 0


class Fn(BasePolicy):
    """Policy from a function (state -> actions); records states."""

    name = "fn"

    def __init__(self, fn):
        self.fn, self.states = fn, []

    def act(self, state):
        self.states.append(state)
        return self.fn(state)


# ---------------------------------------------------------------- retrospective queries
def test_retrospective_query_release_cost_and_served_model():
    clocks = ClockSpec(max_lookback=20, retrain_duration=10)
    env = env_of(T=100, cap=10, clocks=clocks, obs_mode="deployed")
    stream = make_stream(spec_of(T=100, delay=DelaySpec("fixed", d=5)), 30)
    script = {
        3: Action("switch", target=CANDIDATE),
        10: [Action("query", round=1), Action("query", round=5), Action("query", round=10)],
    }
    pol = Fn(lambda st: script.get(st.t, Action("continue")))
    res = Simulator(stream, env).run(pol)
    # cost at request time (t=10); release at request + delay of the label's round (= 15)
    reqs = res.audit.of("request")
    assert [r["t"] for r in reqs] == [10, 10, 10] and [r["label_round"] for r in reqs] == [1, 5, 10]
    assert res.counts["N_q"] == 3 and res.breakdown["cost_N_q"] == pytest.approx(3 * COSTS.c_q)
    assert [r["release_t"] for r in res.audit.of("release")] == [15, 15, 15]
    labs = pol.states[15 - 1].H
    assert [(lab.label_round, lab.request_t) for lab in labs] == [(1, 10), (5, 10), (10, 10)]
    # served model of the label's round: incumbent before the switch, candidate after
    served = {lab.label_round: lab.model_at_request for lab in labs}
    assert served == {1: 0, 5: 1, 10: 1}
    assert all(len(lab.obs) == 1 and lab.obs[0][0] == lab.model_at_request for lab in labs)
    verify_run(res, stream)


def test_retrospective_query_refusals_are_free():
    clocks = ClockSpec(max_lookback=5)
    stream = make_stream(spec_of(), 31)
    script = {
        10: [
            Action("query", round=3),
            Action("query", round=11),
            Action("query", round=0),
            Action("query", round=8),
            Action("query", round=8),
        ]
    }
    res = Simulator(stream, env_of(clocks=clocks)).run(
        Fn(lambda st: script.get(st.t, Action("continue")))
    )
    reasons = [a["reason"] for a in res.audit.of("action") if a["kind"] == "query"]
    assert reasons.count("ok") == 1
    assert reasons.count("round_out_of_lookback") == 3
    assert reasons.count("round_already_requested") == 1
    assert res.counts["N_q"] == 1
    verify_run(res, stream)


def test_retrospective_queries_count_against_label_budget():
    clocks = ClockSpec(max_lookback=50)
    stream = make_stream(spec_of(), 32)

    def pol():
        return Fn(
            lambda st: (
                [Action("query", round=r) for r in range(1, 5)]
                if st.t == 20
                else Action("continue")
            )
        )

    with pytest.raises(BudgetExceeded):
        Simulator(stream, env_of(cap=3, clocks=clocks)).run(pol())
    res = Simulator(stream, env_of(cap=3, clocks=clocks), on_violation="refuse").run(pol())
    assert res.counts["N_q"] == 3
    assert sum(a["reason"] == "budget_refused" for a in res.audit.of("action")) == 1
    verify_run(res, stream)


def test_retrospective_query_no_early_visibility_and_fault_detected():
    clocks = ClockSpec(max_lookback=30)
    stream = make_stream(spec_of(delay=DelaySpec("fixed", d=8)), 33)

    def mk():
        return Fn(lambda st: Action("query", round=2) if st.t == 12 else Action("continue"))

    pol = mk()
    res = Simulator(stream, env_of(clocks=clocks)).run(pol)
    for st in pol.states:
        assert (len(st.H) == 1) == (st.t >= 20)  # not visible at 19, even though round 2 is old
    verify_run(res, stream)

    class EarlyRetro(Simulator):
        def _release_time(self, request_t, label_round=None):
            return label_round + 8  # ignores the request time: earlier than request + delay

    bad = EarlyRetro(stream, env_of(clocks=clocks)).run(mk())
    with pytest.raises(AuditViolation):
        verify_run(bad, stream)


# ---------------------------------------------------------------- canary routing
def _route_policy(frac, t0=1):
    return Fn(
        lambda st: (
            Action("route", target=CANDIDATE, fraction=frac) if st.t == t0 else Action("continue")
        )
    )


def test_canary_split_serves_mixture_and_charges_per_routed_model():
    stream = make_stream(spec_of(T=1000), 40)
    res = Simulator(stream, env_of(T=1000)).run(_route_policy(0.5))
    frac = (res.served_path == CANDIDATE).mean()
    assert 0.44 < frac < 0.56
    want = np.where(res.served_path == CANDIDATE, stream.loss_cand, stream.loss_inc)
    assert np.allclose(res.loss_path, want)
    assert set(res.model_path) == {0}  # primary unchanged
    assert sum(res.routed["rounds"].values()) == 1000
    assert all(v == 0 for v in res.counts.values()) and res.J == pytest.approx(want.sum())
    routes = res.audit.of("route")
    assert len(routes) == 1000 and all(r["fraction"] == 0.5 for r in routes)
    verify_run(res, stream)


def test_routing_draw_is_policy_independent_and_edges():
    stream = make_stream(spec_of(T=300), 41)
    a = Simulator(stream, env_of(T=300)).run(_route_policy(0.3))
    b = Simulator(stream, env_of(T=300)).run(
        Fn(
            lambda st: (
                [Action("route", target=CANDIDATE, fraction=0.3), Action("alert")]
                if st.t == 1
                else Action("continue")
            )
        )
    )
    assert (a.served_path == b.served_path).all()  # common random numbers
    full = Simulator(stream, env_of(T=300)).run(_route_policy(1.0))
    assert (full.served_path == CANDIDATE).all()

    def off_fn(st):
        if st.t == 1:
            return Action("route", target=CANDIDATE, fraction=0.5)
        if st.t == 50:
            return Action("route", target=CANDIDATE, fraction=0.0)
        return Action("continue")

    off = Simulator(stream, env_of(T=300)).run(Fn(off_fn))
    assert (off.served_path[49:] == INCUMBENT_ID).all() and (off.served_path[:49] == 1).any()
    verify_run(full, stream)
    verify_run(off, stream)


def test_routing_refusals_and_cancellation():
    stream = make_stream(spec_of(T=100), 42)
    script = {
        1: Action("route", target=CANDIDATE, fraction=1.5),
        2: Action("route", target=INCUMBENT_ID, fraction=0.5),  # target == primary
        3: Action("route", target=RETRAINED, fraction=0.5),  # not ready
        5: Action("route", target=CANDIDATE, fraction=0.5),
        20: Action("switch", target=CANDIDATE),
    }
    pol = Fn(lambda st: script.get(st.t, Action("continue")))
    res = Simulator(stream, env_of(T=100)).run(pol)
    reasons = {a["t"]: a["reason"] for a in res.audit.of("action") if a["kind"] == "route"}
    assert reasons == {1: "bad_fraction", 2: "already_deployed", 3: "retrained_not_ready", 5: "ok"}
    assert pol.states[10].route == (CANDIDATE, 0.5) and pol.states[25].route is None
    assert (res.served_path[20:] == CANDIDATE).all()  # primary now candidate
    verify_run(res, stream)


def test_routed_label_counts_per_model():
    env = env_of(T=400, cap=400, obs_mode="deployed")
    stream = make_stream(spec_of(T=400, delay=DelaySpec("fixed", d=3)), 43)
    script = {1: [Action("route", target=CANDIDATE, fraction=0.25), Action("query")]}
    pol = Fn(lambda st: script.get(st.t, Action("query")))
    res = Simulator(stream, env).run(pol)
    req, rel = res.routed["labels_requested"], res.routed["labels_released"]
    assert sum(req.values()) == res.counts["N_q"] == 400
    assert sum(rel.values()) == 400 - 3  # last 3 labels never release
    assert req[CANDIDATE] == int((res.served_path == CANDIDATE).sum())
    assert pol.states[-1].routed_labels == tuple(sorted(rel.items()))
    # labels observed in deployed mode carry the loss of the model that served that round
    for lab in pol.states[-1].H:
        ((m, loss),) = lab.obs
        assert m == lab.model_at_request == res.served_path[lab.label_round - 1]
        assert (
            loss == (stream.loss_cand if m == CANDIDATE else stream.loss_inc)[lab.label_round - 1]
        )
    verify_run(res, stream)


def test_tampered_routing_is_detected():
    stream = make_stream(spec_of(T=200), 44)
    res = Simulator(stream, env_of(T=200)).run(_route_policy(0.5))
    bad = copy.deepcopy(res)
    flip = int(np.flatnonzero(bad.served_path == CANDIDATE)[0])
    bad.served_path[flip] = 0
    with pytest.raises(AuditViolation):
        verify_run(bad, stream)
    bad2 = copy.deepcopy(res)
    bad2.audit.of("route")[3]["fraction"] = 0.01  # declared fraction no longer matches the draw
    with pytest.raises(AuditViolation):
        verify_run(bad2, stream)


# ---------------------------------------------------------------- retrain quality model
def _retrain_run(t_retrain, seed=50, query_until=None):
    T = 320
    spec = spec_of(T=T, onset_jitter=0.0, delay=DelaySpec("fixed", d=1))
    stream = make_stream(spec, seed)
    clocks = ClockSpec(retrain_duration=10, w_train=60)
    until = t_retrain if query_until is None else query_until

    def fn(st):
        acts = [Action("query")] if st.t < until else []
        if st.t == t_retrain:
            acts.append(Action("retrain"))
        return acts or Action("continue")

    res = Simulator(stream, env_of(T=T, cap=T, clocks=clocks)).run(Fn(fn))
    verify_run(res, stream)
    return stream, res


def test_early_retrain_on_few_clean_labels_is_worse_than_late_retrain():
    stream, early = _retrain_run(105)
    _, late = _retrain_run(200)
    qe = early.audit.of("retrain_start")[0]
    ql = late.audit.of("retrain_start")[0]
    assert qe["clean_fraction"] < 0.2 and ql["clean_fraction"] > 0.9
    assert ql["q"] == pytest.approx(stream.spec.retrain_rate)  # saturated: best attainable
    assert qe["q"] > ql["q"] + 0.2
    # common random numbers: pathwise, the poorly trained model never loses less
    sl = slice(230, 320)  # both retrained models are in force
    assert (early.model_path[sl] == 2).all() and (late.model_path[sl] == 2).all()
    assert (early.loss_path[sl] >= late.loss_path[sl]).all()
    assert early.loss_path[sl].sum() > late.loss_path[sl].sum()


def test_retrain_without_any_labels_gets_poor_rate_and_is_audited():
    stream, res = _retrain_run(100, query_until=0)
    rs = res.audit.of("retrain_start")[0]
    assert rs["clean_fraction"] == 0.0 and rs["q"] == pytest.approx(stream.spec.retrain_poor_rate)
    bad = copy.deepcopy(res)
    bad.audit.of("retrain_start")[0]["q"] = stream.spec.retrain_rate  # claim a better model
    with pytest.raises(AuditViolation):
        verify_run(bad, stream)


def test_pre_drift_labels_do_not_count_as_clean():
    # labels only from before the onset: clean fraction at a retrain after onset is 0
    T = 320
    stream = make_stream(spec_of(T=T, onset_jitter=0.0, delay=DelaySpec("fixed", d=1)), 51)
    clocks = ClockSpec(retrain_duration=10, w_train=60)

    def fn(st):
        acts = [Action("query")] if st.t < 80 else []
        if st.t == 120:
            acts.append(Action("retrain"))
        return acts or Action("continue")

    res = Simulator(stream, env_of(T=T, cap=T, clocks=clocks)).run(Fn(fn))
    rs = res.audit.of("retrain_start")[0]
    assert rs["clean_fraction"] == 0.0 and rs["q"] == pytest.approx(stream.spec.retrain_poor_rate)


# ---------------------------------------------------------------- propensities
def test_honest_randomised_queries_verify():
    stream = make_stream(spec_of(T=600), 60)
    pol = Fn(
        lambda st: (
            Action("query", propensity=0.3, u_index=2) if st.u[2] < 0.3 else Action("continue")
        )
    )
    res = Simulator(stream, env_of(T=600, cap=600)).run(pol)
    assert 100 < res.counts["N_q"] < 260
    verify_run(res, stream)


def test_dishonest_propensity_is_detected():
    stream = make_stream(spec_of(T=600), 61)
    # always queries but claims a 10% randomised design
    res = Simulator(stream, env_of(T=600, cap=600)).run(
        Fn(lambda st: Action("query", propensity=0.1) if st.t <= 100 else Action("continue"))
    )
    with pytest.raises(AuditViolation, match="propensity"):
        verify_run(res, stream)


def test_out_of_range_propensity_is_refused_and_free():
    stream = make_stream(spec_of(), 62)
    res = Simulator(stream, env_of()).run(
        Fn(lambda st: Action("query", propensity=1.5) if st.t == 5 else Action("continue"))
    )
    assert res.counts["N_q"] == 0
    reasons = [a["reason"] for a in res.audit.of("action") if a["kind"] == "query"]
    assert reasons == ["bad_propensity"]
    verify_run(res, stream)
