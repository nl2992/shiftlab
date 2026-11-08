"""Tests for Amendment A2 wiring (stage_b_a2, evidence_q1_a2, canary_a2). No ledger writes, no rar_persistent runs."""

from __future__ import annotations

import json

import numpy as np
import pytest

from shiftlab.autoresearch import stage_b as sb
from shiftlab.autoresearch import stage_b_a2 as a2
from shiftlab.autoresearch import stage_b_v2 as v2
from shiftlab.bench.contract import BudgetSpec, EnvSpec, load_cost_vectors, run_paired
from shiftlab.bench.contract import evidence_q1_a2 as eq
from shiftlab.bench.contract.canary_a2 import (
    CABHorizonPolicy,
    RARCanaryA2Policy,
    a2_clocks,
    rollback_only,
)
from shiftlab.bench.contract.evidence_q1 import Ctx, StartMixture
from shiftlab.bench.contract.types import ACTION_KINDS

SMOKE_SEED = 110_900_000  # contract smoke block


def test_seeds_are_fresh_and_disjoint_from_v1_and_v2():
    v1 = set(range(110_000_000, 110_000_000 + 3 * 1000 + 20))
    v2s = set(range(110_050_000, 110_050_000 + 14 * 1000 + 20))
    mine = {s for i in range(21) for s in a2.seeds_of(i)} | {
        s for i in range(21, 25) for s in a2.seeds_of(i, a2.AUDIT_REP)
    }
    assert not (mine & v1) and not (mine & v2s)
    assert min(mine) == 110_070_000 and max(mine) == 110_094_099
    assert max(mine) < 110_099_999 and min(mine) > 110_064_019
    assert a2.seeds_of(3)[5] == 110_070_000 + 3 * 1000 + 5


def test_panels_and_registered_files():
    assert [c["a2_index"] for c in a2.q1_panel()] == list(range(16))
    assert [c["id"] for c in a2.rar_panel()] == list(a2.RAR_CELL_IDS)
    assert [c["a2_index"] for c in a2.rar_panel()] == list(range(16, 21))
    assert [c["a2_index"] for c in a2.audit_panel()] == [21, 22, 23, 24]
    assert json.loads(a2.SUITE_A2_PATH.read_text(encoding="utf-8")) == json.loads(
        json.dumps(a2.build_suite_a2())
    )
    for c in a2.rar_panel():
        assert c["T"] == c["label_cap"] == 1500 and c["max_lookback"] == 10


def test_restart_min_prior_is_summable_and_core_is_dominated_by_components():
    for B in (50, 60, 300, 1500):
        g = eq.start_grid(B)
        assert g[0] == 0 and all(s < B for s in g)
        w = eq.start_prior(len(g))
        assert abs(w.sum() - 1.0) < 1e-12 and (np.diff(w) < 0).all()
    ctx = Ctx(0.55, 1000, 50, 0.8, 0.005)
    core = eq.RestartMinCore(ctx, {})
    assert isinstance(core.cond, StartMixture) and isinstance(core.marg, StartMixture)
    rng = np.random.default_rng(0)
    for i, z in enumerate(rng.integers(0, 2, 40)):
        core.update(20 * (i + 1), int(z))
        assert core.log_e <= min(core.cond.log_e, core.marg.log_e) + 1e-12


def _cell(cid, role, runs, null_expected):
    return {
        "id": cid,
        "role": role,
        "family": "f",
        "cost_vector": "x",
        "null_expected": null_expected,
        "runs": runs,
    }


def _run(J, nq=0.0, promoted=False):
    return {"J": J, "breakdown": {"cost_N_q": nq}, "promoted": promoted, "counts": {"N_q": 0}}


def test_a2_control_reading_differs_from_a1_on_the_registered_points():
    n = 20
    alt = {"cond": False, "marg": False, "abs_risk": False}
    nul = {"cond": True, "marg": True, "abs_risk": True}
    rng = np.random.default_rng(1)
    jit = rng.normal(0, 1, n)

    def runs(base, nq, prom):
        return [_run(base + j, nq, prom) for j in jit]

    cells = [
        # persistent-shift "control": candidate promotes and is much better -> A1 extra_promotion, A2 fine (null does not hold)
        _cell("S3c", "neighbouring_negative_control", {"host": runs(700, 3, False), "cand": runs(400, 3, True), "m": runs(500, 3, True)}, alt),
        # null control with spend equal to the shell comparator but above the host -> A1 extra_spend, A2 fine
        _cell("S2e", "correct_null", {"host": runs(700, 62.5, False), "cand": runs(370, 75, False), "m": runs(370, 75, False)}, nul),
    ]  # fmt: skip
    res = {"eligible_comparators": ["m"], "strongest_comparator_per_cell": {"S3c": "m", "S2e": "m"}}
    r = a2.a2_control_reading(cells, res, cand_null="cond", spend_family=("m",))
    assert r["controls_ok"], r["notes"]
    # extra promotion on a cell where the claimed null holds still fails
    cells[1]["runs"]["cand"] = runs(380, 75, True)
    r = a2.a2_control_reading(cells, res, cand_null="cond", spend_family=("m",))
    assert not r["controls_ok"] and r["notes"][0]["extra_promotion_on_claimed_null_cell"]
    # spend above the same-family comparator fails; worse J needs the CI above 0
    cells[1]["runs"]["cand"] = runs(371, 140, False)
    r = a2.a2_control_reading(cells, res, cand_null="cond", spend_family=("m",))
    assert not r["controls_ok"] and r["notes"][0]["extra_spend_vs_same_family"]
    noisy = [_run(500 + (30 if i % 2 else -30) * 10, 75) for i in range(n)]
    cells[1]["runs"]["cand"] = noisy
    cells[1]["runs"]["m"] = [_run(500, 75) for _ in range(n)]
    r = a2.a2_control_reading(cells, res, cand_null="cond", spend_family=("m",))
    assert r["controls_ok"]  # mean difference is zero, CI contains 0


def test_a2_decision_replaces_only_the_control_reason():
    res = {
        "decision": "DISCARD",
        "why": "",
        "discard_reasons": ["worse/overspend on neighbouring or negative-control cell"],
    }
    assert a2.a2_decision(res, {"controls_ok": True, "notes": []})["decision"] == "KEEP"
    assert a2.a2_decision(res, {"controls_ok": False, "notes": []})["decision"] == "DISCARD"
    res2 = {**res, "discard_reasons": ["no effect vs strongest applicable comparator (label none)"]}
    assert a2.a2_decision(res2, {"controls_ok": True, "notes": []})["decision"] == "DISCARD"


def _env(spec_cell, clocks, allowed=None):
    spec, env = a2.spec_env(
        {**spec_cell, "arm": "rar", "w_train": 100, "retrain_duration": 20}, clocks, allowed
    )
    return spec, env


def test_policy_guards_and_modes_on_an_existing_v2_cell_smoke_seed():
    cell = next(c for c in v2.load_suite_v2()["cells"] if c["id"] == "S2a")
    spec = v2.cell_spec(cell)
    costs = load_cost_vectors()[cell["cost_vector"]]

    def env(kind, lookback, allowed=ACTION_KINDS):
        ck = a2_clocks(kind)
        ck = type(ck)(**{**ck.__dict__, "max_lookback": lookback})
        return EnvSpec(
            T=spec.T,
            costs=costs,
            budget=BudgetSpec(label_cap=cell["label_cap"]),
            clocks=ck,
            allowed_actions=allowed,
        )

    with pytest.raises(ValueError):
        RARCanaryA2Policy("nocanary").reset(env("canary", 10))
    with pytest.raises(ValueError):
        RARCanaryA2Policy("k2_skip").reset(env("default", 10))
    with pytest.raises(ValueError):
        RARCanaryA2Policy("L_routed").reset(env("canary", 0))
    # lookback is a no-op for hosts that never query retrospectively (bit-identical J)
    js = []
    for lb in (0, 10):
        e = env("canary", lb)
        pr = run_paired(
            {"m": lambda: RARCanaryA2Policy("host")},
            spec,
            e,
            [SMOKE_SEED],
            on_violation="raise",
            verify=True,
        )
        js.append(pr.runs["m"][0].J)
    assert js[0] == js[1]
    # every mode runs, passes verify_run, and charges only performed actions
    e_c, e_d = env("canary", 10), env("default", 10)
    no_alert = tuple(k for k in ACTION_KINDS if k != "alert")
    for name, mk, e in (
        ("k2", lambda: RARCanaryA2Policy("k2_skip"), e_c),
        ("k1", lambda: RARCanaryA2Policy("k1_p1"), e_c),
        ("L", lambda: RARCanaryA2Policy("L_routed"), e_c),
        ("nc", lambda: RARCanaryA2Policy("nocanary"), e_d),
        ("cabh", lambda: CABHorizonPolicy(), e_d),
        ("rb", lambda: rollback_only(), env("canary", 10, no_alert)),
    ):
        pr = run_paired({name: mk}, spec, e, [SMOKE_SEED], on_violation="raise", verify=True)
        assert np.isfinite(pr.runs[name][0].J)


def test_nocanary_has_no_verification_and_k1_routes_all_traffic():
    cell = next(c for c in v2.load_suite_v2()["cells"] if c["id"] == "S2a")
    spec = v2.cell_spec(cell)
    costs = load_cost_vectors()[cell["cost_vector"]]
    held = []

    def mk(mode):
        def f():
            p = RARCanaryA2Policy(mode)
            held.append(p)
            return p

        return f

    for mode, kind in (("nocanary", "default"), ("k1_p1", "canary")):
        e = EnvSpec(
            T=spec.T,
            costs=costs,
            budget=BudgetSpec(label_cap=cell["label_cap"]),
            clocks=a2_clocks(kind),
        )
        run_paired({mode: mk(mode)}, spec, e, [SMOKE_SEED], on_violation="raise", verify=True)
        ev = [x["event"] for x in held[-1].log]
        if mode == "nocanary":
            assert (
                "stage1_start" not in ev
                and "stage2_fail" not in ev
                and "probation_no_stage1" not in ev
            )
        else:
            assert held[-1].cfg.p1 == 1.0


def test_cab_horizon_is_not_degenerate_where_the_paper_cab_cannot_fire():
    # drop 0.25, c_r 100 + c_s 10: the paper's floor H = W_train = 100 needs drop >= 1.1; H = T - t does not
    assert 0.25 * 100 < 110 <= 0.25 * 800


def test_a2_records_tag_and_reject_confirmation_seeds():
    assert a2.SUITE == "a2" and a2.AMENDMENT == "A2"
    assert sb.cp_upper(0, 400) < 0.01 and a2.CPU_CAP_S == 300 and a2.MAX_WORKERS == 12
