import json

import numpy as np
import pytest
from test_bounds_v2 import REC
from test_shield import (
    REGIMES,
    K,
    T,
    _inners,
    hand_spec,
    hand_tape,
    hand_tapes,
)

from shiftlab.paper3.baselines import AlwaysChallenger, NeverSwitch
from shiftlab.paper3.contracts import ProblemSpec
from shiftlab.paper3.riskbudget import RiskBudgetShield, harm_path, harm_summary
from shiftlab.paper3.riskbudget.shield_v2 import RiskBudgetShieldV2
from shiftlab.paper3.simulation import generate_tape, make_spec, run_policy, seeds_for

RS = (8, 12, 20)


def _record(name, obj):
    try:
        REC.mkdir(parents=True, exist_ok=True)
        (REC / name).write_text(json.dumps(obj, indent=1, default=float))
    except OSError:
        pass


def v1_det(inner, R, **kw):
    return RiskBudgetShield(inner, R, pi_menu=(1.0,), delta=0.0, **kw)


def v2_det(inner, R, **kw):
    return RiskBudgetShieldV2(inner, R, pi_min=1.0, paced=False, **kw)


# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("inner", ["always", "wald"])
def test_reduces_to_v1_pi1(inner):
    """Identical action and query sequences to v1 f3_pi1 (delta=0, menu (1,)) on several tapes."""
    n_cmp = 0
    for rid in ("stationary_better", "abrupt_harmful", "label_dropout", "bait_reversal"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T)
        for s in seeds_for("smoke", 3):
            tape, _ = generate_tape(reg, s, T)
            for R in RS:
                for ride in (True, False):
                    a = v1_det(_inners()[inner], R, ride_out=ride)
                    b = v2_det(_inners()[inner], R, ride_out=ride)
                    ra, rb = run_policy(a, tape, spec, s), run_policy(b, tape, spec, s)
                    assert np.array_equal(ra.a, rb.a), (rid, s, R, ride)
                    assert np.array_equal(ra.q, rb.q), (rid, s, R, ride)
                    assert a.n_forced_rollbacks == b.n_forced_rollbacks
                    assert a.n_vetoed_promotions == b.n_vetoed_promotions
                    assert a.rode_out == b.rode_out
                    assert b.n_sampled == 0
                    n_cmp += 1
    for name, tape in hand_tapes().items():
        for R in RS:
            a, b = v1_det(_inners()[inner], R), v2_det(_inners()[inner], R)
            ra, rb = run_policy(a, tape, hand_spec(), 1), run_policy(b, tape, hand_spec(), 1)
            assert np.array_equal(ra.a, rb.a) and np.array_equal(ra.q, rb.q), (name, R)
            n_cmp += 1
    assert n_cmp > 50


@pytest.mark.parametrize("inner", ["always", "wald"])
def test_pi1_deterministic_guarantee_all_regimes(inner):
    seeds = seeds_for("smoke", 5)
    worst = {R: 0.0 for R in RS}
    for reg in REGIMES.values():
        spec = make_spec(reg, T)
        for s in seeds:
            tape, _ = generate_tape(reg, s, T)
            for R in RS:
                sh = v2_det(_inners()[inner], R)
                rec = run_policy(sh, tape, spec, s)
                hs = harm_summary(tape, rec, reg.costs.k)
                worst[R] = max(worst[R], hs["sup_harm"])
                assert hs["sup_harm"] <= R + 1e-9, (reg.id, s, R, hs)
                assert sh.I_max <= R + 1e-9
    assert max(worst.values()) > 0


@pytest.mark.parametrize("inner", ["always", "wald"])
def test_pi1_deterministic_guarantee_hand_tapes(inner):
    for name, tape in hand_tapes().items():
        for R in RS:
            for ride in (True, False):
                sh = v2_det(_inners()[inner], R, ride_out=ride)
                rec = run_policy(sh, tape, hand_spec(), 1)
                hs = harm_summary(tape, rec, K)
                assert hs["sup_harm"] <= R + 1e-9, (name, R, ride, hs)


def _adv_tapes():
    rng = np.random.default_rng(0)
    dense = np.where(rng.random(T) < 0.5, -1.0, 0.0)
    bait = np.r_[np.ones(40), -np.ones(T - 40)]
    return {
        "all_harm_d3": hand_tape(-np.ones(T), 3),
        "dense_harm_d4": hand_tape(dense, 4),
        "bait_then_harm_d5": hand_tape(bait, 5),
        "bait_then_harm_d30": hand_tape(bait, 30),
        "harm_never_arrive": hand_tape(-np.ones(T), T + 1),
    }


def _cell(args):
    """One (tape, B, pi_min, R) cell over n_seeds policy seeds -> (violations, sampled, det_viol)."""
    tname, B, pm, R, delta, n_seeds = args
    tape = _adv_tapes()[tname]
    base = hand_spec(B=B)
    spec = ProblemSpec(T=T, B=B, costs=base.costs, delay_known=5)
    viol = samp = det_viol = inner_viol = 0
    for s in range(n_seeds):
        sh = RiskBudgetShieldV2(AlwaysChallenger(), R, delta=delta, pi_min=pm, window=6)
        rec = run_policy(sh, tape, spec, s)
        v = harm_summary(tape, rec, K)["sup_harm"] > R + 1e-9
        viol += v
        samp += sh.n_sampled > 0
        det_viol += v and sh.n_sampled == 0
        inner_viol += bool(np.any(harm_path(tape, rec, K) > sh.Hb + 1e-9))  # nan compares False
    return args, viol, samp, det_viol, inner_viol


def test_paced_sampling_violation_rate():
    """pi_min in {.25,.5}, delta=.1, small B: violation rate <= delta + 3 se, over 2000 seeds."""
    from multiprocessing import Pool

    delta, n_seeds = 0.1, 2000
    tol = 3 * np.sqrt(delta * (1 - delta) / n_seeds)
    cells = [
        ("all_harm_d3", 15, 0.25, 12, delta, n_seeds),
        ("bait_then_harm_d5", 15, 0.5, 12, delta, n_seeds),
        ("bait_then_harm_d30", 30, 0.25, 12, delta, n_seeds),
        ("bait_then_harm_d5", 30, 0.25, 20, delta, n_seeds),
        ("dense_harm_d4", 15, 0.25, 12, delta, n_seeds),
        ("all_harm_d3", 30, 0.5, 20, delta, n_seeds),
    ]
    with Pool(6) as pool:
        res = pool.map(_cell, cells)
    rates = {}
    for (tn, B, pm, R, _, _), viol, samp, det_viol, inner_viol in res:
        key = f"{tn}|B={B}|pi_min={pm}|R={R}"
        rates[key] = {
            "violation": viol / n_seeds,
            "internal_bound_violation": inner_viol / n_seeds,
            "frac_runs_sampled": samp / n_seeds,
        }
        assert inner_viol / n_seeds <= delta + tol, (key, "H_t exceeded the verified bound")
        assert det_viol == 0, key  # no sampled round => deterministic guarantee
        assert viol / n_seeds <= delta + tol, (key, viol / n_seeds)
    _record("shield_v2_paced_violation.json", {"delta": delta, "seeds": n_seeds, "cells": rates})
    print("max paced violation rate:", max(v["violation"] for v in rates.values()))


def test_internal_bound_holds_on_regimes():
    """H_t <= verified bound at every deployed round, paced sampling, real regimes (smoke seeds)."""
    bad = tot = 0
    for rid in ("stationary_better", "abrupt_harmful", "bait_reversal", "label_dropout"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T)
        for s in seeds_for("smoke", 15):
            tape, _ = generate_tape(reg, s, T)
            for pm in (0.25, 0.5):
                sh = RiskBudgetShieldV2(_inners()["wald"], 12, delta=0.05, pi_min=pm)
                rec = run_policy(sh, tape, spec, s)
                bad += bool(np.any(harm_path(tape, rec, reg.costs.k) > sh.Hb + 1e-9))
                tot += 1
    assert bad / tot <= 0.05, (bad, tot)


def test_paced_sampling_actually_samples_and_saves_labels():
    reg = REGIMES["stationary_better"]
    spec = make_spec(reg, T)
    ns, nq1, nq2 = [], [], []
    for s in seeds_for("smoke", 10):
        tape, _ = generate_tape(reg, s, T)
        sh = RiskBudgetShieldV2(_inners()["wald"], 20, pi_min=0.25, label_reserve_frac=0.25)
        r2 = run_policy(sh, tape, spec, s)
        r1 = run_policy(v2_det(_inners()["wald"], 20), tape, spec, s)
        ns.append(sh.n_sampled)
        nq1.append(r1.q.sum())
        nq2.append(r2.q.sum())
        assert 0.25 <= sh.mean_pi <= 1.0
    assert np.mean(ns) > 0
    print(
        f"[v2] sampled rounds {np.mean(ns):.1f}, labels pi1 {np.mean(nq1):.1f} vs paced {np.mean(nq2):.1f}"
    )


@pytest.mark.parametrize("B", [0, 6])
def test_budget_semantics(B):
    for rid in ("stationary_better", "abrupt_harmful", "label_dropout"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T)
        spec = ProblemSpec(
            T=T, B=B, costs=spec.costs, delay_known=spec.delay_known, delay_kind=spec.delay_kind
        )
        for pm in (1.0, 0.25):
            for iname in ("always", "wald"):
                for bm in (None, 4.0):
                    tape, _ = generate_tape(reg, seeds_for("smoke", 1)[0], T)
                    sh = RiskBudgetShieldV2(
                        _inners()[iname], 12, delta=0.05, pi_min=pm, blind_margin=bm
                    )
                    rec = run_policy(sh, tape, spec, 3)  # raises BudgetError on violation
                    assert rec.q.sum() <= B
                    if B == 0:
                        assert sh.n_sampled == 0  # no labels: every exposed round is blind
                        assert harm_summary(tape, rec, spec.costs.k)["sup_harm"] <= 12 + 1e-9


def test_no_promotion_when_budget_below_two_fees():
    for name, tape in hand_tapes().items():
        for R in (0, 3, 5.99):
            sh = RiskBudgetShieldV2(AlwaysChallenger(), R, delta=0.05)
            rec = run_policy(sh, tape, hand_spec(), 1)
            assert rec.a.sum() == 0, (name, R)
            assert sh.n_vetoed_promotions > 0


def test_blind_margin_and_ride_out_flags():
    tape = hand_tape(np.ones(80), 1, T=80)
    spec = hand_spec(T=80, d=1)

    class Leave(AlwaysChallenger):
        def act(self, view):
            d = super().act(view)
            return type(d)(int(view.t <= 74), d.query, d.compute, d.retrain)

    a = RiskBudgetShieldV2(Leave(), 12, delta=0.05, ride_out=True)
    b = RiskBudgetShieldV2(Leave(), 12, delta=0.05, ride_out=False)
    ra, rb = run_policy(a, tape, spec, 1), run_policy(b, tape, spec, 1)
    assert a.rode_out and not b.rode_out
    assert ra.ledger["n_switches"] == 1 and rb.ledger["n_switches"] == 2
    # optional blind rounds with a huge margin never fire; with margin 0 they fire when W <= R
    c = RiskBudgetShieldV2(AlwaysChallenger(), 20, delta=0.05, blind_margin=0.0)
    run_policy(c, hand_tape(np.ones(80), 1, T=80), spec, 1)
    assert c.n_blind > 0


def test_shield_useful_and_diagnostics():
    seeds = seeds_for("smoke", 12)
    reg = REGIMES["stationary_better"]
    spec = make_spec(reg, T)
    dj, frac = [], []
    for s in seeds:
        tape, _ = generate_tape(reg, s, T)
        sh = RiskBudgetShieldV2(_inners()["wald"], 20, pi_min=0.5)
        rec = run_policy(sh, tape, spec, s)
        dj.append(rec.J - run_policy(NeverSwitch(), tape, spec, s).J)
        frac.append(rec.a.mean())
        assert sh.n_blind >= 0 and sh.n_sampled >= 0
    assert np.mean(dj) < 0 and np.mean(frac) > 0.3
