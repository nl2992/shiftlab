"""Shared computation for the mechanism figures: one deterministic tape run with the committed code."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shiftlab.paper3.baselines import AlwaysChallenger
from shiftlab.paper3.contracts import Costs, ProblemSpec
from shiftlab.paper3.riskbudget import RiskBudgetShield, harm_path
from shiftlab.paper3.riskbudget.comparators import StopLossPlugin
from shiftlab.paper3.simulation import Tape, run_policy

T, D, K, R, NPLUS = 60, 5, 3.0, 20.0, 10  # tape: Z=+1 for rounds 1..NPLUS, then Z=-1; all rounds disagree
z = np.r_[np.ones(NPLUS), -np.ones(T - NPLUS)]
tape = Tape(np.column_stack([(z > 0) * 1.0, (z < 0) * 1.0]), np.ones(T, bool), np.zeros((T, 2)), np.full(T, D), {})
spec = ProblemSpec(T=T, B=60, costs=Costs(c_q=0.05, k=K, c_compute=0.0), delay_known=D)


class Logged:
    """Read-only wrapper: records policy attributes after each act(); never changes behaviour."""
    def __init__(self, pol, probe):
        self.pol, self.probe, self.log = pol, probe, []
        self.name = pol.name
    def reset(self, spec, rng):
        self.log = []; self.pol.reset(spec, rng)
    def act(self, view):
        dec = self.pol.act(view)
        self.log.append(self.probe(self.pol, view.t))
        return dec


shield = Logged(RiskBudgetShield(AlwaysChallenger(), R=R, delta=0.0),
                lambda p, t: dict(I=p._I(t), P=p.P, kN=p.k * p.N, A=p.A))
stop = Logged(StopLossPlugin(AlwaysChallenger(), R),
              lambda p, t: dict(kNA=p.k * p.N + p.A))
res = {}
for key, pol in (("shield", shield), ("stop", stop)):
    rec = run_policy(pol, tape, spec, 0)
    h = harm_path(tape, rec, K)
    # labels in transit after round t: requested at s<=t, released at rtime > t
    rt = np.asarray(rec.release_t)
    pend = np.array([int(((rec.q == 1) & (rt > t) & (np.arange(1, T + 1) <= t)).sum()) for t in range(1, T + 1)])
    res[key] = dict(rec=rec, H=h, pend=pend, log={k: np.array([d[k] for d in pol.log]) for k in pol.log[0]})

t = np.arange(1, T + 1)
Hs, Hl = res["shield"]["H"], res["stop"]["H"]
assert abs(res["shield"]["log"]["P"] - res["shield"]["pend"]).max() < 1e-9  # shield P equals the in-transit count
roll_s = int(np.argmax(res["shield"]["rec"].a[1:] < res["shield"]["rec"].a[:-1]) + 2)
roll_l = int(np.argmax(res["stop"]["rec"].a[1:] < res["stop"]["rec"].a[:-1]) + 2)

