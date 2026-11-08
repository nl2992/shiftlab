"""Post-confirmation hurdle comparators for EQSDp (novelty_audit.md section 5/7).

Every class below shares EQSDp's evidence (discounted disagreement-outcome counts, label clock),
its paced acquisition (``stake=False``) and its remaining-horizon payback. Only the switching
hurdle changes, so each is a matched replacement for the Beta-posterior quantile:

* ``WaldLCB``: p_hat -/+ z_gamma * sqrt(p_hat (1-p_hat) / n), clipped to [0, 1].
* ``HoeffdingLCB``: p_hat -/+ sqrt(log(1/gamma) / (2 n)).
* ``ScaledMargin``: point estimate; switch when (adv - kappa) r (T-t) > cs, i.e. the hurdle grows
  with the remaining payback horizon instead of being an additive constant.
* ``Dwell``: point estimate; switch only after the payback rule holds on ``k`` consecutive label
  releases (k-streak hysteresis, cf. ``src/shiftlab/dive/atlas_components.py``).

``n`` is the discounted effective count (the same quantity the Beta posterior uses).
"""

from __future__ import annotations

import math

from eqs_d import EQSD
from scipy.stats import norm


class WaldLCB(EQSD):
    def _q(self, lev):
        n = max(self.n, 1e-9)
        p = (self.k + 0.5) / (n + 1.0)  # light continuity correction keeps se > 0 at n small
        se = math.sqrt(p * (1 - p) / (n + 1.0))
        return min(1.0, max(0.0, p + norm.ppf(lev) * se))


class HoeffdingLCB(EQSD):
    def _q(self, lev):
        n = max(self.n, 1e-9)
        p = self.k / n if self.n > 0 else 0.5
        w = math.sqrt(math.log(1.0 / min(lev, 1.0 - lev)) / (2.0 * n))
        return min(1.0, max(0.0, p - w if lev < 0.5 else p + w))


class ScaledMargin(EQSD):
    def __init__(self, *a, kappa=0.1, **kw):
        super().__init__(*a, gamma=0.5, **kw)
        self.kappa = float(kappa)

    def _gain_away(self, lev):
        p = (self.k + 1.0) / (self.n + 2.0)  # posterior mean
        adv = (2 * p - 1) if self.deployed == 0 else (1 - 2 * p)
        return (adv - self.kappa) * self._rate() * (self.T - self.t)


class Dwell(EQSD):
    def __init__(self, *a, k_streak=5, **kw):
        super().__init__(*a, gamma=0.5, **kw)
        self.k_streak, self.streak = int(k_streak), 0

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            self.streak = self.streak + 1 if self._gain_away(0.5) > self.cs else 0
            if self.streak >= self.k_streak:
                self.deployed, self.streak = 1 - self.deployed, 0


class ChallengerGSE(HoeffdingLCB):
    """Challenger-style irreversible payback with a Hoeffding bound (after Digalakis Jr et al.,
    arXiv 2512.18390, GSE). Switch once when the Hoeffding lower bound of the advantage times
    r (T-t) exceeds cs; never switch back. Shares EQSDp's evidence clock and pacing (common-contract
    adaptation; the source has no label budget, delay, or disagreement-only labels)."""

    def _gain_away(self, lev):
        if self.deployed == 1:
            return -math.inf
        return super()._gain_away(lev)
