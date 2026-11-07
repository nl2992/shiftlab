"""COMMON_CONTRACT_PORT tests for RAR and Cost-Aware Binary (src/shiftlab/bench/contract/adapters_rar.py)."""

from __future__ import annotations

import inspect
import time

import numpy as np
import pytest

pytest.importorskip("river")

from shiftlab.bench.contract import (
    BudgetSpec,
    CostVector,
    DelaySpec,
    EnvSpec,
    Simulator,
    StreamSpec,
    make_stream,
    run_paired,
    verify_run,
)
from shiftlab.bench.contract import adapters_rar as M
from shiftlab.bench.contract.adapters_rar import (
    BinaryAdapter,
    CostAwareBinaryAdapter,
    RARAdapter,
    canary_clocks,
)
from shiftlab.bench.contract.types import INCUMBENT, RETRAINED
from shiftlab.sota.rar.components import FractionLabelPolicy

COSTS = CostVector("balanced_test", c_q=0.05, c_s=2.0, c_r=30.0, c_b=5.0, c_a=0.2, c_h=0.1)
T = 700


def env_of(cap=T, costs=COSTS, **kw) -> EnvSpec:
    clocks = kw.pop("clocks", canary_clocks(retrain_duration=20, w_train=100))
    return EnvSpec(T=T, costs=costs, budget=BudgetSpec(label_cap=cap), clocks=clocks, **kw)


SPEC = StreamSpec(
    family="rar_drift",
    T=T,
    onset_frac=0.3,
    onset_jitter=0.0,
    duration_frac=1.0,
    p_before=0.25,
    p_during=0.9,
    delay=DelaySpec("fixed", d=10),
)


def run(obj, seed=1, env=None, spec=SPEC):
    env = env or env_of()
    stream = make_stream(spec, seed)
    if hasattr(obj, "build"):
        pol = obj.build(env)
    else:
        pol = obj
        pol.reset(env)
    res = Simulator(stream, env).run(pol)
    verify_run(res, stream)
    return res, pol, stream


def events(pol, name):
    return [e for e in pol.log if e["event"] == name]


def test_adapter_metadata_and_vocabulary_subset():
    assert RARAdapter.claimed_null == "none" and RARAdapter.port_status == "COMMON_CONTRACT_PORT"
    assert CostAwareBinaryAdapter.claimed_null == "none"
    env = env_of(allowed_actions=RARAdapter.vocabulary)  # any other action kind would raise
    res, _, _ = run(RARAdapter, env=env)
    assert res.counts["N_r"] == 1
    env_b = env_of(allowed_actions=CostAwareBinaryAdapter.vocabulary)
    run(CostAwareBinaryAdapter, env=env_b)


def test_no_evaluator_imports_in_adapter_source():
    code = inspect.getsource(M).split('"""', 2)[2]
    assert "from .streams" not in code and "EvaluatorTruth" not in code
    assert ".value" not in code  # never reads PendingView.value


def test_canary_is_routed_then_committed_with_clean_audit():
    res, pol, _ = run(RARAdapter, seed=1)
    assert res.audit.of("leak") == [] and res.leak_attempts == []
    routes = res.audit.of("route")
    assert routes and all(r["target"] == RETRAINED and r["fraction"] == 0.2 for r in routes)
    n_routed = int(((res.served_path == RETRAINED) & (res.model_path == INCUMBENT)).sum())
    assert 0.1 * len(routes) < n_routed < 0.3 * len(routes)  # about p1 of stage-1 rounds
    assert [e["event"] for e in pol.log if e["event"] in ("stage1_pass", "commit")] == [
        "stage1_pass",
        "commit",
    ]
    assert res.counts["N_r"] == 1 and res.counts["N_s"] == 1 and res.counts["N_b"] == 0
    assert res.model_path[-1] == RETRAINED
    first = events(pol, "retrain_issued")[0]["t"]
    assert first >= events(pol, "detector_flag")[0]["t"] >= int(0.3 * T)
    g = next(e for e in events(pol, "gates") if e["t"] == first)
    assert g["g2"] and g["g3"] and g["win"] >= 0.7 * 100 - 1e-9


def test_failed_stage2_triggers_rollback_and_hold():
    pol = M.RARPolicy(cfg_overrides={"z_commit": 99.0})  # unreachable commit threshold
    res, pol, _ = run(pol, seed=1)
    assert events(pol, "stage2_fail")[0]["cause"] == "dead_band"
    n_fail = len(events(pol, "stage2_fail"))  # emergency override may start a second cycle
    assert n_fail >= 1 and res.counts["N_b"] == n_fail and res.counts["N_s"] == n_fail
    assert res.model_path[-1] == INCUMBENT  # rolled back and held
    assert events(pol, "hold_enter") and events(pol, "commit") == []
    assert events(pol, "retrain_issued")  # the retrain stays paid for (sunk cost)


def test_failed_stage1_clears_route_without_charging_rollback():
    pol = M.RARPolicy(cfg_overrides={"delta": -1.0})  # margin screen always fails (R1_interim)
    res, pol, _ = run(pol, seed=1)
    ab = events(pol, "stage1_abort")
    assert ab and ab[0]["cause"].startswith("R1")
    assert res.counts["N_b"] == 0 and res.counts["N_s"] == 0
    assert (res.model_path == INCUMBENT).all()
    assert max(r["t"] for r in res.audit.of("route")) <= ab[0]["t"]  # route cleared at abort


def test_label_budget_respected():
    res, _, _ = run(RARAdapter, seed=2, env=env_of(cap=90))
    assert res.counts["N_q"] == 90  # AllLabelsPolicy spends the cap and stops (no BudgetExceeded)
    assert res.breakdown["cost_N_q"] == pytest.approx(90 * COSTS.c_q)


def test_gate_and_label_hooks_swap_only_the_gated_component():
    base, pol0, _ = run(RARAdapter, seed=1)

    class NeverG3:
        def passes(self, ctx):
            return False

    swapped, pol1, _ = run(M.RARPolicy(gate3=NeverG3()), seed=1)
    # same detector history up to the gate, same label spending; only the gated decision differs
    assert events(pol0, "detector_flag")[0] == events(pol1, "detector_flag")[0]
    assert base.counts["N_q"] == swapped.counts["N_q"] == T
    assert base.counts["N_r"] == 1 and swapped.counts["N_r"] == 0
    assert any(e["kind"] == "A2" for e in events(pol1, "alert"))
    t_g = events(pol0, "retrain_issued")[0]["t"]
    assert (base.served_path[: t_g - 1] == swapped.served_path[: t_g - 1]).all()

    seen = {}

    class CostAwareG3:
        def passes(self, ctx):
            seen["rho"] = ctx.rho
            return (ctx.acc_pre - ctx.acc_cur) * 100 >= ctx.rho

    run(M.RARPolicy(gate3=CostAwareG3()), seed=1)
    assert seen["rho"] == COSTS.c_r

    half, _, _ = run(M.RARPolicy(label_policy=FractionLabelPolicy(2)), seed=1)
    assert half.counts["N_q"] == T // 2


def test_deployed_mode_uses_unpaired_commit_rule():
    _, pol, _ = run(RARAdapter, seed=1, env=env_of(obs_mode="deployed"))
    commit = events(pol, "commit")
    assert commit and commit[0]["unpaired"] is True and commit[0]["z"] is None


def test_cost_aware_binary_is_cost_sensitive_and_binary_always_retrains():
    cheap = CostVector("cheap", c_q=0.05, c_s=0.0, c_r=1.0)
    dear = CostVector("dear", c_q=0.05, c_s=0.0, c_r=5000.0)
    r_cheap, _, _ = run(CostAwareBinaryAdapter, env=env_of(costs=cheap))
    r_dear, p_dear, _ = run(CostAwareBinaryAdapter, env=env_of(costs=dear))
    assert r_cheap.counts["N_r"] == 1 and r_dear.counts["N_r"] == 0
    assert events(p_dear, "cost_gate")[0]["passes"] is False
    r_bin, _, _ = run(BinaryAdapter, env=env_of(costs=dear))
    assert r_bin.counts["N_r"] == 1 and r_bin.counts["N_b"] == 0 and r_bin.counts["N_a"] == 0


def test_paired_run_all_policies_and_speed():
    t0 = time.time()
    pr = run_paired(
        {
            "rar": lambda: RARAdapter.build(env_of()),
            "cost_aware_binary": lambda: CostAwareBinaryAdapter.build(env_of()),
            "binary": lambda: BinaryAdapter.build(env_of()),
        },
        SPEC,
        env_of(),
        seeds=[1, 2, 3],
        verify=True,
    )
    assert pr.diff("rar", "binary").shape == (3,)
    assert np.isfinite(pr.J("rar")).all()
    assert time.time() - t0 < 20
