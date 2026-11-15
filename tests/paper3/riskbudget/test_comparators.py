import numpy as np

from shiftlab.paper3.baselines import AlwaysChallenger
from shiftlab.paper3.contracts import Costs, ProblemSpec
from shiftlab.paper3.riskbudget import harm_summary
from shiftlab.paper3.riskbudget.comparators import CusumRollback, StopLossPlugin
from shiftlab.paper3.simulation import Tape, run_policy

T = 120


def tape(z, delay=3):
    z = np.asarray(z, float)
    ell = np.column_stack([np.where(z > 0, 1.0, 0.0), np.where(z < 0, 1.0, 0.0)])
    return Tape(ell, z != 0, np.zeros((T, 2)), np.full(T, delay), {})


def spec(B=60):
    return ProblemSpec(T=T, B=B, costs=Costs(c_q=0.05, k=3.0, c_compute=0.0), delay_known=3)


def test_stoploss_caps_persistent_harm():
    tp = tape(-np.ones(T))
    free = run_policy(AlwaysChallenger(), tp, spec(), 0)
    rec = run_policy(StopLossPlugin(AlwaysChallenger(), 12), tp, spec(), 0)
    assert harm_summary(tp, rec, 3.0)["sup_harm"] < harm_summary(tp, free, 3.0)["sup_harm"]
    assert rec.a[-1] == 0 and rec.ledger["n_queries"] <= 60


def test_cusum_rollback_and_block():
    tp = tape(-np.ones(T))
    pol = CusumRollback(AlwaysChallenger(), 2.0, allow_repromote=False)
    rec = run_policy(pol, tp, spec(), 0)
    assert pol.n_forced_rollbacks == 1 and rec.a[-1] == 0 and rec.a.sum() < 15


def test_benign_tape_not_rolled_back():
    tp = tape(np.ones(T))
    pol = CusumRollback(AlwaysChallenger(), 2.0)
    rec = run_policy(pol, tp, spec(), 0)
    assert pol.n_forced_rollbacks == 0 and rec.a.all()


def test_label_budget_respected():
    tp = tape(-np.ones(T))
    for pol in (CusumRollback(AlwaysChallenger(), 100.0), StopLossPlugin(AlwaysChallenger(), 1e6)):
        rec = run_policy(pol, tp, spec(B=5), 0)
        assert rec.ledger["n_queries"] <= 5
