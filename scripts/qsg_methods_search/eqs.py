"""EQS: economic query-conditional switching (QSG methods search, candidate D1).

Decision problem: incumbent (0) vs frozen challenger (1), paid delayed labels under a hard budget,
per-switch cost ``cs``. Target: low net cost over a portfolio of persistent stationary regimes
(better / near / null / worse), not alpha-certified promotion. **No false-promotion guarantee is
claimed.**

Evidence. Queried disagreement outcomes ``z = 1[challenger correct]`` (QCE, as in QSG), counted
within the current segment. The disagreement rate ``r`` is estimated from model predictions alone
(no labels). Per-event advantage of the challenger is ``(2p - 1) r``.

Rules, evaluated when a label is released at time ``t`` (all quantities are available to the
policy at ``t``; the propensity is set before the query draw):

* promote  if ``(2 p_lo - 1) r (T - t) > cs``, ``p_lo`` the ``gamma`` quantile of Beta(k+1, n-k+1);
* discard  if ``(2 p_hi - 1) r (T - t) < cs``, ``p_hi`` the ``1-gamma`` quantile: even an
  optimistic estimate cannot repay a switch, so stop front-loading and drop acquisition to
  ``monitor_frac`` of the paced rate (economic acquisition stop);
* rollback (after promotion, counts since promotion only) if ``(1 - 2 p_hi) r (T - t) > cs``;
  counts reset and front-loading resumes.

Acquisition: query every disagreement while undecided (front-loading); paced afterwards.

Mechanisms vs the closest construction (horizon-pays promotion; Wan et al. 2023, Chick et al.
2017; the repo's ``economic_replacement`` control): confidence-bounded payback, the economic
acquisition stop, front-loading under a hard label budget, and economic rollback.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scipy.stats import beta as _beta

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for _p in (SOTA, SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import EconomicReplacement, PacedDisagreementAcquisition
from simulator import QueryRequest


class EQS:
    def __init__(
        self,
        horizon,
        budget,
        switch_cost,
        *,
        rng,
        gamma=0.1,
        gamma_r=None,
        front=True,
        stop=True,
        rollback=True,
        monitor_frac=0.25,
        name="EQS",
    ):
        self.name = name
        self.T, self.B, self.cs = int(horizon), int(budget), float(switch_cost)
        self.rng = rng
        self.gamma = float(gamma)
        self.gamma_r = float(gamma if gamma_r is None else gamma_r)
        self.front, self.stop, self.rollback = front, stop, rollback
        self.monitor_frac = float(monitor_frac)
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.deployed = 0
        self.decided = False  # promoted, or discarded in the current segment
        self.n = self.k = 0
        self.seg = 0  # labels issued before seg are ignored (new segment after a switch)
        self.t = 0

    # ------------------------------------------------------------------ helpers
    def _rate(self):
        a = self.acq
        return (a.n_disagree + a.prior_rate * a.prior_w) / (self.t + a.prior_w)

    def _q(self, lo):
        return float(_beta.ppf(lo, self.k + 1, self.n - self.k + 1))

    # ------------------------------------------------------------------ policy API
    def predict(self, event):
        self.t = event.t
        return self.deployed

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if not self.decided and self.front:
            q = 1.0
        elif self.decided and self.deployed == 0:
            q = q * self.monitor_frac  # discarded: economic acquisition stop
        if q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            if fb.event_id < self.seg:
                continue
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n += 1
            self.k += int(d > 0)
            t = fb.t_released
            pay = self._rate() * (self.T - t)
            if self.deployed == 0:
                if (2 * self._q(self.gamma) - 1) * pay > self.cs:
                    self._switch(1, t)
                elif (
                    self.stop
                    and not self.decided
                    and (2 * self._q(1 - self.gamma) - 1) * pay < self.cs
                ):
                    self.decided = True
            elif self.rollback and (1 - 2 * self._q(1 - self.gamma_r)) * pay > self.cs:
                self._switch(0, t)

    def _switch(self, to, t):
        self.deployed = to
        self.decided = to == 1  # after promotion: paced monitoring; after rollback: front-load
        self.n = self.k = 0
        self.seg = t

    def decision_state(self):
        return f"dep={self.deployed};dec={self.decided};k={self.k}/{self.n}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


class EconFront(EconomicReplacement):
    """Straightforward composition: the economic control with front-loaded acquisition."""

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if self.deployed == 0:
            q = 1.0
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)


def _econ(cls, mo, mg, nm):
    return lambda T, B, cs, cq, a, d, r: cls(
        T, B, cs, rng=r("econ"), min_obs=mo, margin=mg, name=nm
    )


def _eqs(nm, **kw):
    return lambda T, B, cs, cq, a, d, r: EQS(T, B, cs, rng=r("EQS"), name=nm, **kw)


EXTRA = {}
for _mo in (5, 10, 15, 25, 40):
    for _mg in (0, 5, 10, 20):
        EXTRA[f"econ_mo{_mo}_m{_mg}"] = _econ(EconomicReplacement, _mo, _mg, f"econ_mo{_mo}_m{_mg}")
        EXTRA[f"econF_mo{_mo}_m{_mg}"] = _econ(EconFront, _mo, _mg, f"econF_mo{_mo}_m{_mg}")
for _g in (0.05, 0.1, 0.2, 0.3):
    for _mf in (0.0, 0.25):
        EXTRA[f"EQS_g{_g}_mf{_mf}"] = _eqs(f"EQS_g{_g}_mf{_mf}", gamma=_g, monitor_frac=_mf)
        EXTRA[f"EQS_g{_g}_mf{_mf}_gr.02"] = _eqs(
            f"EQS_g{_g}_mf{_mf}_gr.02", gamma=_g, monitor_frac=_mf, gamma_r=0.02
        )
    EXTRA[f"EQS_g{_g}-no_front"] = _eqs(f"EQS_g{_g}-no_front", gamma=_g, front=False)
    EXTRA[f"EQS_g{_g}-no_stop"] = _eqs(f"EQS_g{_g}-no_stop", gamma=_g, stop=False)
    EXTRA[f"EQS_g{_g}-no_rollback"] = _eqs(f"EQS_g{_g}-no_rollback", gamma=_g, rollback=False)
EXTRA["EQS_point"] = _eqs("EQS_point", gamma=0.5)  # point-estimate payback, all other parts on
