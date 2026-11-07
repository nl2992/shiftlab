"""COMMON_CONTRACT_PORT of Drift2Act: integrity tests (audit, leakage, budget, Q2 hook). No performance claims."""

from __future__ import annotations

from shiftlab.bench.contract import (
    BudgetSpec,
    ClockSpec,
    DelaySpec,
    EnvSpec,
    StreamSpec,
    load_cost_vectors,
    run_paired,
)
from shiftlab.bench.contract.adapters_drift2act import Drift2ActAdapter, Drift2ActContractPolicy

SEEDS = (110_900_000, 110_900_001)
T, CAP = 300, 60
SPEC = StreamSpec(family="d2a_smoke", T=T, delay=DelaySpec("fixed", d=10), tau=0.5)


def make_env(cap=CAP, lookback=100) -> EnvSpec:
    return EnvSpec(
        T=T,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=cap),
        clocks=ClockSpec(retrain_duration=20, max_lookback=lookback),
    )


class FixedSize:
    """Q2-style request policy: only the size changes (k labels every 5th round)."""

    def __init__(self, k):
        self.k = k

    def request_size(self, ctx):
        return self.k if ctx.t % 5 == 0 else 0


def test_adapter_declares_port_and_null():
    assert Drift2ActAdapter.port_status == "COMMON_CONTRACT_PORT"
    assert Drift2ActAdapter.claimed_null == "abs_risk"
    assert set(Drift2ActAdapter.vocabulary) <= set(make_env().allowed_actions)
    assert "A1_recalibrate" in Drift2ActAdapter.unmapped_native_actions


def test_paired_episode_passes_audit_no_leak_budget_respected():
    env = make_env()
    pr = run_paired(
        {"d2a": lambda: Drift2ActAdapter.build(env)}, SPEC, env, seeds=SEEDS
    )  # verify_run inside; on_violation='raise' => any leak/budget breach raises
    for r in pr.runs["d2a"]:
        assert r.leak_attempts == []
        assert r.counts["N_q"] <= CAP
        assert r.counts["N_q"] > 0
        assert r.J > 0 and abs(r.breakdown["cost_N_q"] - env.costs.c_q * r.counts["N_q"]) < 1e-9
        qrounds = [
            a["label_round"]
            for a in r.audit.of("action")
            if a["kind"] == "query" and a["performed"]
        ]
        assert len(qrounds) == len(set(qrounds))  # one query per round
        assert all(1 <= s <= T for s in qrounds)


def test_budget_cap_binding_is_refused_not_overspent():
    env = make_env(cap=5)
    pr = run_paired({"d2a": lambda: Drift2ActAdapter.build(env)}, SPEC, env, seeds=SEEDS[:1])
    assert pr.runs["d2a"][0].counts["N_q"] <= 5


def test_request_size_hook_swap_changes_only_label_counts():
    env = make_env(cap=200)

    def build(k):
        p = Drift2ActContractPolicy(request_policy=FixedSize(k))
        p.reset(env)
        return p

    pr = run_paired({"k1": lambda: build(1), "k3": lambda: build(3)}, SPEC, env, seeds=SEEDS)
    for a, b in zip(pr.runs["k1"], pr.runs["k3"], strict=True):
        assert a.stream_fingerprint == b.stream_fingerprint
        assert b.counts["N_q"] > a.counts["N_q"]
        assert b.breakdown["cost_N_q"] > a.breakdown["cost_N_q"]

        def non_query_before_release(r):
            # before the first label can be released (fixed delay 10) nothing but the request size differs
            return [
                (e["t"], e["kind"])
                for e in r.audit.of("action")
                if e["t"] <= 10 and e["kind"] != "query"
            ]

        assert non_query_before_release(a) == non_query_before_release(b)
