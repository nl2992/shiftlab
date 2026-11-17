import itertools

import numpy as np

from shiftlab.paper3.baselines import AlwaysChallenger
from shiftlab.paper3.contracts import Costs, ProblemSpec
from shiftlab.paper3.riskbudget import harm_summary
from shiftlab.paper3.riskbudget.comparators import CusumRollback, StopLossPlugin
from shiftlab.paper3.riskbudget.comparators_cal import CusumRollbackBudget, StopLossMargin
from shiftlab.paper3.simulation import Tape, run_policy

T = 120


def tape(z, delay=3):
    z = np.asarray(z, float)
    ell = np.column_stack([np.where(z > 0, 1.0, 0.0), np.where(z < 0, 1.0, 0.0)])
    return Tape(ell, z != 0, np.zeros((T, 2)), np.full(T, delay), {})


def spec(B=60):
    return ProblemSpec(T=T, B=B, costs=Costs(c_q=0.05, k=3.0, c_compute=0.0), delay_known=3)


def _same(a, b):
    return np.array_equal(a.a, b.a) and a.ledger["n_queries"] == b.ledger["n_queries"]


def test_margin_zero_reproduces_stoploss():
    for z in (-np.ones(T), np.where(np.arange(T) % 7 < 3, -1.0, 1.0), np.ones(T)):
        tp = tape(z)
        old = run_policy_(StopLossPlugin(AlwaysChallenger(), 12), tp)
        new = run_policy_(StopLossMargin(AlwaysChallenger(), 12, 0.0), tp)
        assert _same(old, new)


def run_policy_(pol, tp):
    return run_policy(pol, tp, spec(), 0)


def test_margin_is_monotone_and_can_block_all():
    tp = tape(-np.ones(T))
    sup = [
        harm_summary(tp, run_policy_(StopLossMargin(AlwaysChallenger(), 12, c), tp), 3.0)[
            "sup_harm"
        ]
        for c in (0, 2, 4, 7, 12)
    ]
    assert all(x >= y for x, y in itertools.pairwise(sup))
    assert sup[-1] == 0.0  # c large enough: never promotes


def test_cusum_budget_stop_and_benign():
    tp = tape(-np.ones(T))
    free = run_policy_(CusumRollback(AlwaysChallenger(), 1e9), tp)
    pol = CusumRollbackBudget(AlwaysChallenger(), 1e9, 12)  # CUSUM never fires: budget stop only
    rec = run_policy_(pol, tp)
    assert pol.budget_stopped and rec.a[-1] == 0
    assert harm_summary(tp, rec, 3.0)["sup_harm"] < harm_summary(tp, free, 3.0)["sup_harm"]
    ok = tape(np.ones(T))
    pol = CusumRollbackBudget(AlwaysChallenger(), 2.0, 12)
    assert run_policy_(pol, ok).a.all() and not pol.budget_stopped


def test_cusum_budget_large_R_matches_cusum():
    tp = tape(-np.ones(T))
    old = run_policy_(CusumRollback(AlwaysChallenger(), 2.0), tp)
    new = run_policy_(CusumRollbackBudget(AlwaysChallenger(), 2.0, 1e9), tp)
    assert _same(old, new)
