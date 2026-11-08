"""EQS-D: change-aware economic switching with decision-at-stake acquisition (D2 candidate).

Evidence: discounted counts of queried disagreement outcomes, ``n <- lam n + 1``,
``k <- lam k + z`` with ``z = 1[challenger correct]``. Beta(k+1, n-k+1) quantiles.

Switching (symmetric, evaluated at each release time t, using only released labels):
  on 0: switch to 1 if (2 Q(gamma) - 1) r (T-t) > cs
  on 1: switch to 0 if (1 - 2 Q(1-gamma)) r (T-t) > cs
with r the prediction-only disagreement-rate estimate. No reset at a switch (discounting forgets).

Acquisition (decision-at-stake): the switch away from the deployed model is "at stake" while its
optimistic payback, using the (1-gamma) / gamma quantile, exceeds cs. Then every disagreement is
queried (q=1) as long as fewer than ``p_cap`` labels are pending. Otherwise the shared budget-paced
rate times ``mf``. The propensity is fixed before the draw and depends only on released labels,
pending counts and predictions.

No false-promotion guarantee is claimed.
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

from controls import PacedDisagreementAcquisition
from simulator import QueryRequest


class EQSD:
    def __init__(
        self,
        horizon,
        budget,
        switch_cost,
        *,
        rng,
        lam=0.98,
        gamma=0.2,
        p_cap=10,
        mf=1.0,
        stake=True,
        margin=0.0,
        name="EQSD",
    ):
        self.name = name
        self.T, self.B, self.cs = int(horizon), int(budget), float(switch_cost)
        self.rng = rng
        self.lam, self.gamma, self.p_cap, self.mf, self.stake = lam, gamma, p_cap, mf, stake
        self.margin = float(margin)  # D4 ablation: additive hurdle instead of a quantile
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.deployed = 0
        self.n = self.k = 0.0
        self.pending = 0
        self.t = 0

    def _rate(self):
        a = self.acq
        return (a.n_disagree + a.prior_rate * a.prior_w) / (self.t + a.prior_w)

    def _q(self, lev):
        return float(_beta.ppf(lev, self.k + 1.0, self.n - self.k + 1.0))

    def _gain_away(self, lev):
        """Payback of switching away from the deployed model at quantile ``lev`` of p."""
        p = self._q(lev if self.deployed == 0 else 1.0 - lev)
        adv = (2 * p - 1) if self.deployed == 0 else (1 - 2 * p)
        return adv * self._rate() * (self.T - self.t)

    def predict(self, event):
        self.t = event.t
        return self.deployed

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        at_stake = self.stake and self._gain_away(1.0 - self.gamma) > self.cs
        if at_stake and self.pending < self.p_cap:
            q = 1.0
        else:
            q = min(1.0, q * self.mf)
        if q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed

    def decision_state(self):
        return f"dep={self.deployed};k={self.k:.1f}/{self.n:.1f};pend={self.pending}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


def _mk(nm, **kw):
    return lambda T, B, cs, cq, a, d, r: EQSD(T, B, cs, rng=r("EQSD"), name=nm, **kw)


EXTRA = {}
for _lam in (0.95, 0.98):
    for _g in (0.2, 0.35):
        for _pc in (10, 10**9):
            for _mf in (0.5, 1.0):
                _n = f"EQSD_l{_lam}_g{_g}_pc{'inf' if _pc > 1e6 else _pc}_mf{_mf}"
                EXTRA[_n] = _mk(_n, lam=_lam, gamma=_g, p_cap=_pc, mf=_mf)
        _n = f"EQSD_l{_lam}_g{_g}-paced"
        EXTRA[_n] = _mk(_n, lam=_lam, gamma=_g, stake=False)
for _g in (0.2, 0.35):
    _n = f"EQSD_l1_g{_g}_pc10_mf1.0"
    EXTRA[_n] = _mk(_n, lam=1.0, gamma=_g, p_cap=10, mf=1.0)
