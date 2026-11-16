"""v3 (03F section 7): option defaults unchanged, scarce regimes file, validity at T = 2000."""

import hashlib
import json
from multiprocessing import Pool

import numpy as np
import pytest
from test_bounds_v2 import _record
from test_shield import REGIMES, _inners, hand_spec, hand_tape
from test_shield import T as T300

from shiftlab.paper3.baselines import AlwaysChallenger
from shiftlab.paper3.contracts import ProblemSpec
from shiftlab.paper3.riskbudget import harm_path, harm_summary
from shiftlab.paper3.riskbudget.bounds_v2 import V_TARGETS, CoinMixture
from shiftlab.paper3.riskbudget.harness_v3 import (
    FROZEN_V3,
    SCARCE_CFG,
    V_TARGETS_V3,
    candidate_grid,
    scarce_regimes,
)
from shiftlab.paper3.riskbudget.shield_v2 import RiskBudgetShieldV2
from shiftlab.paper3.simulation import generate_tape, make_spec, run_policy, seeds_for

# Recorded with the code as it was BEFORE the v_targets option existed (2026-11-16).
GOLDEN_LAMS = [
    1.5174271293851465,
    0.7587135646925732,
    0.3793567823462866,
    0.1896783911731433,
    0.09483919558657165,
]
GOLDEN_SHA = "12a45351359802fdd22b08aab5b2720691ca0a306b3bb852cabfefe72460c178"


def _hash_runs(**kw):
    h = hashlib.sha256()
    for rid in ("stationary_better", "abrupt_harmful", "bait_reversal", "label_dropout"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T300)
        for s in seeds_for("smoke", 2):
            tape, _ = generate_tape(reg, s, T300)
            for pm in (0.25, 0.5):
                for R in (12, 20):
                    sh = RiskBudgetShieldV2(_inners()["wald"], R, pi_min=pm, **kw)
                    rec = run_policy(sh, tape, spec, s)
                    h.update(np.asarray(rec.a, np.int8).tobytes())
                    h.update(np.asarray(rec.q, np.int8).tobytes())
    return h.hexdigest()


def test_default_grid_unchanged():
    assert V_TARGETS == (4.0, 16.0, 64.0, 256.0, 1024.0)
    assert CoinMixture(0.05).lams.tolist() == GOLDEN_LAMS
    assert CoinMixture(0.05, v_targets=V_TARGETS).lams.tolist() == GOLDEN_LAMS
    ext = CoinMixture(0.05, v_targets=V_TARGETS_V3)
    assert len(ext.lams) == 6 and np.all(np.diff(ext.lams) < 0)


def test_default_action_sequences_unchanged():
    """Identical action and query sequences to the code before the option existed."""
    assert _hash_runs() == GOLDEN_SHA
    assert _hash_runs(v_targets=None) == GOLDEN_SHA
    assert _hash_runs(v_targets=V_TARGETS) == GOLDEN_SHA


def test_scarce_regimes_file():
    regs = scarce_regimes()
    assert len(regs) == 47 and SCARCE_CFG.exists()
    for r in regs.values():
        assert r.B == 200 and r.costs.k == 5.0 and r.costs.c_q == 0.05 and r.costs.c_compute == 0.0
        assert r.params["delay"]["kind"] == "fixed" and r.params["delay"]["d"] in (24, 100, 144)
        assert r.params["e_both"] == 0.1 and r.params["x_scale"] == 1.0
    assert sum(r.params["rho"] == 0.8 for r in regs.values()) == 2
    assert "sc_r25_d100_benstrong" in regs and "sc_r25_d100_reversal_rho80" in regs
    reg = regs["sc_r25_d100_benstrong"]
    spec = make_spec(reg, 2000)
    tape, _ = generate_tape(reg, seeds_for("smoke", 1)[0], 2000)
    assert tape.T == 2000 and spec.delay_known == 100
    assert abs(tape.disagree.mean() - 0.25) < 0.04
    assert len(candidate_grid()) == 12


# ------------------------------------------------------------------ validity at T = 2000, B = 200
T2, K2, B2 = 2000, 5.0, 200


def _tapes():
    rng = np.random.default_rng(1)
    dense = np.where(rng.random(T2) < 0.25, -1.0, 0.0)
    bait = np.r_[np.ones(200), -np.ones(T2 - 200)]
    bait_sparse = np.where(rng.random(T2) < 0.25, bait, 0.0)
    return {
        "all_harm_d24": hand_tape(-np.ones(T2), 24, T=T2),
        "dense_harm_d100": hand_tape(dense, 100, T=T2),
        "bait_sparse_d144": hand_tape(bait_sparse, 144, T=T2),
        "harm_never_arrive": hand_tape(-np.ones(T2), T2 + 1, T=T2),
    }


def _cell(args):
    tname, pm, R, lo, hi = args
    tape = _tapes()[tname]
    base = hand_spec(T=T2, B=B2, k=K2)
    spec = ProblemSpec(T=T2, B=B2, costs=base.costs, delay_known=5)
    viol = samp = det_viol = inner_viol = over_budget = 0
    for s in range(lo, hi):
        sh = RiskBudgetShieldV2(
            AlwaysChallenger(),
            R,
            delta=0.05,
            pi_min=pm,
            window=24,
            v_targets=V_TARGETS_V3,
            label_reserve_frac=0.1,
        )
        rec = run_policy(sh, tape, spec, s)
        v = harm_summary(tape, rec, K2)["sup_harm"] > R + 1e-9
        viol += v
        samp += sh.n_sampled > 0
        det_viol += v and sh.n_sampled == 0
        inner_viol += bool(np.any(harm_path(tape, rec, K2) > sh.Hb + 1e-9))
        over_budget += int(rec.q.sum()) > B2
    return args, viol, samp, det_viol, inner_viol, over_budget


def test_v3_validity_T2000_pimin_05():
    """2000 policy seeds on two adversarial tapes (600 / 300 on two more, for run time)."""
    delta = 0.05
    plan = {
        "all_harm_d24": 2000,
        "bait_sparse_d144": 2000,
        "dense_harm_d100": 600,
        "harm_never_arrive": 300,
    }
    chunks = []
    for t, n in plan.items():
        step = 667 if n == 2000 else n
        chunks += [(t, 0.05, 60, lo, min(lo + step, n)) for lo in range(0, n, step)]
    with Pool(6) as pool:
        res = pool.map(_cell, chunks)
    tot: dict = {}
    for (tn, pm, R, lo, hi), viol, samp, det_viol, inner_viol, over in res:
        e = tot.setdefault(tn, [0, 0, 0, 0, 0, 0])
        for i, v in enumerate((hi - lo, viol, samp, det_viol, inner_viol, over)):
            e[i] += v
    rates = {}
    for tn, (n, viol, samp, det_viol, inner_viol, over) in tot.items():
        tol = 3 * np.sqrt(delta * (1 - delta) / n)
        key = f"{tn}|pi_min=0.05|R=60"
        rates[key] = {
            "violation": viol / n,
            "internal_bound_violation": inner_viol / n,
            "frac_runs_sampled": samp / n,
            "n_seeds": n,
        }
        assert over == 0, key  # label budget never exceeded
        assert det_viol == 0, key  # no sampled round => deterministic guarantee
        assert inner_viol / n <= delta + tol, key
        assert viol / n <= delta + tol, (key, viol / n)
    _record("shield_v3_T2000_violation.json", {"delta": delta, "cells": rates})
    print("max v3 violation rate:", max(v["violation"] for v in rates.values()))


def test_v3_deterministic_when_unsampled_on_scarce_regimes():
    regs = scarce_regimes()
    for rid in ("sc_r25_d100_harmful", "sc_r10_d24_reversal", "sc_r40_d144_benstrong"):
        reg = regs[rid]
        spec = make_spec(reg, T2)
        for s in seeds_for("smoke", 2):
            tape, _ = generate_tape(reg, s, T2)
            sh = RiskBudgetShieldV2(
                _inners()["wald"],
                60,
                pi_min=0.05,
                label_reserve_frac=0.1,
                v_targets=V_TARGETS_V3,
                blind_margin=8.0,
            )
            rec = run_policy(sh, tape, spec, s)
            assert rec.q.sum() <= 200
            sup = harm_summary(tape, rec, 5.0)["sup_harm"]
            if sh.n_sampled == 0:
                assert sup <= 60 + 1e-9 and sh.I_max <= 60 + 1e-9, (rid, s)


def test_frozen_json_consistent_if_present():
    if not FROZEN_V3.exists():
        pytest.skip("not frozen yet")
    sh = json.loads(FROZEN_V3.read_text())["shield"]
    assert sh["delta"] == 0.05 and sh["paced"] and sh["ride_out"]
    assert tuple(sh["v_targets"]) == V_TARGETS_V3
    assert sh in candidate_grid()
