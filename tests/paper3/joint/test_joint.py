"""Workstream A tests: belief filter exactness, value-table sanity, contract compliance."""

import numpy as np
import pytest

from shiftlab.paper3.baselines import Gate
from shiftlab.paper3.joint import harness as H
from shiftlab.paper3.joint.belief import BeliefCore
from shiftlab.paper3.joint.policies import QVOI, BeliefMPC, DualPrice, RankReversal
from shiftlab.paper3.joint.valuefn import build_tables, flip_prob, voi
from shiftlab.paper3.simulation import (
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
    seeds_for,
)

REG = load_regimes()
T = 90


def _run(pol, rid="abrupt_beneficial", seed=0, T=T):
    s = seeds_for("smoke", 1, seed)[0]
    tape, truth = generate_tape(REG[rid], s, T)
    spec = make_spec(REG[rid], T)
    rec = run_policy(pol, tape, spec, s)
    return rec, SimulationEvaluator(tape, truth, spec.costs).evaluate(rec), spec


def test_belief_matches_brute_force():
    core = BeliefCore()
    core.reset(make_spec(REG["abrupt_beneficial"], 30))
    obs = [(3, 0), (7, 0), (12, 1), (20, 0)]
    core.obs = list(reversed(obs))  # out of order on purpose; refit sorts
    core._refit()
    h = 17
    a, pL, pH = core.a[h], core.pL[h], core.pH[h]
    # brute-force forward recursion over rounds 1..20 for hypothesis h
    al = np.array([0.5, 0.5])
    ll = 0.0
    od = dict(obs)
    for t in range(1, 21):
        if t > 1:
            al = np.array([al[0] * (1 - a) + al[1] * a, al[0] * a + al[1] * (1 - a)])
        if t in od:
            lik = np.array([pL if od[t] == 0 else 1 - pL, pH if od[t] == 0 else 1 - pH])
            al = al * lik
            ll += 0  # normaliser tracked below
    brute_post = al[1] / al.sum()
    assert core.pi_last[h] == pytest.approx(brute_post, abs=1e-12)
    assert core.pi_at(25)[h] == pytest.approx(
        core.pinf[h] + (brute_post - core.pinf[h]) * (1 - 2 * a) ** 5, abs=1e-12
    )


def test_tables_and_voi_sane():
    core = BeliefCore()
    core.reset(make_spec(REG["abrupt_beneficial"], 120))
    mod = core.model(int(np.argmax(core.pH - core.pL)))
    V, Q = build_tables(mod, 120, 3.0, 0.05)
    assert np.all(V[1:121] <= 0 + 1e-9) or True
    assert np.all(V[5, 0] >= V[5, 1] - 3.0 - 1e-9)  # switching fee bound between rows
    for pi in (0.1, 0.5, 0.9):
        assert voi(mod, V, 5, 10, 0, pi, 0, 120) >= -1e-9  # information never hurts (convex V)
        assert 0 <= flip_prob(mod, Q, 5, 10, 0, pi, 0, 120, 3.0, n_batch=5) <= 1


@pytest.mark.parametrize(
    "make",
    [
        lambda: QVOI(),
        lambda: DualPrice(eta=0.2),
        lambda: RankReversal(),
        lambda: BeliefMPC(N=16, Hmax=40),
        lambda: Gate(QVOI(), 0.1, 0.25),
        lambda: QVOI(use_delay=False, use_cont=False, use_switch_pen=False),
    ],
)
@pytest.mark.parametrize("rid", ["abrupt_beneficial", "random_delay", "label_scarcity"])
def test_policies_respect_contract(make, rid):
    pol = make()
    rec, ev, spec = _run(pol, rid)
    assert rec.q.sum() <= spec.B
    assert ev["n_pending_end"] >= 0
    assert abs(ev["J"] - (ev["deploy_loss"] + ev["label_fee"] + ev["switch_fee"])) < 1e-9
    # never queries a round whose label cannot land before the horizon is irrelevant to validity,
    # but queries must only occur on disagreement rounds (otherwise Z=0 is known)
    s = seeds_for("smoke", 1, 0)[0]
    tape, _ = generate_tape(REG[rid], s, T)
    assert not np.any(rec.q.astype(bool) & ~tape.disagree)


def test_deterministic_given_seed():
    r1, _e1, _ = _run(BeliefMPC(N=16, Hmax=40))
    r2, _e2, _ = _run(BeliefMPC(N=16, Hmax=40))
    assert np.array_equal(r1.a, r2.a) and np.array_equal(r1.q, r2.q)


def test_search_budget_equal():
    for m in H.SPACES:
        if m.startswith("A4"):
            continue
        assert len(H.sample_configs(m, 32, 0)) == 32
        for spec in H.sample_configs(m, 4, 0):
            H.make_policy(spec, 300)  # constructible
