"""QSG: query-conditional started-mixture gate (Failure Atlas v2 standalone candidate).

Decision problem: incumbent (0) vs frozen challenger (1), paid delayed labels under a hard budget,
switching cost, false-promotion control at level alpha.

Evidence (QCE). Queried disagreement outcomes ``z_k = 1[challenger correct]`` in request order.
Promotion null ``H+ : p_t <= 1/2 for every t`` (challenger never better on a disagreement). For any
``p' > 1/2``, ``LR(z) = (2p')^z (2(1-p'))^(1-z)`` has ``E[LR | past] = 1 + (2p'-1)(2p-1) <= 1``
under H+, because the query decision is predictable and does not read the label.

Started mixture. ``E_k = sum_{p' in grid} pi(p') sum_{j <= k} w_j prod_{i=j..k} LR_{p'}(z_i)``
with ``w_j = 1/(j(j+1))`` and a fixed discrete grid ``pi``. ``E_k`` itself is not a
supermartingale (a new start adds ``w_k``), but ``E_k + 1/(k+1)`` is a nonnegative test
supermartingale starting at 1 under H+, since each started product is one and
``sum_{j > k} w_j = 1/(k+1)``; Ville then gives ``P(sup_k E_k >= 1/a) <= a``. Starting points let evidence that accrues after an early
unfavourable period count without an alpha reset (late improvement).

Rollback. After promotion, the mirrored started mixture tests ``H- : p_t >= 1/2`` on outcomes
issued after the promotion. A rejection rolls back. Cycle ``j = 1, 2, ...`` of promotion tests
runs at ``alpha / 2^j`` so total false-promotion probability under H+ is at most alpha; rollback
tests use ``alpha_r`` (a false rollback costs two switches, it is not a safety error).

Acquisition. While undecided, every disagreement is queried (q = 1) until the budget is gone;
after a verdict, the remaining budget is paced evenly over the expected remaining disagreements
(monitoring for reversal / late improvement). All propensities are predictable.

Parameters were set a priori (no tuning on discovery seeds): grid p' in {.55,.6,...,.95} uniform,
alpha_r = .05, discard verdict at the mirrored mixture reaching 1/alpha.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (SOTA, SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition  # noqa: E402
from simulator import QueryRequest  # noqa: E402

GRID = np.arange(0.55, 0.951, 0.05)


class StartedMixture:
    """Started-mixture e-process for ``H: P(z=1) <= 1/2`` (``side=+1``) or ``>= 1/2`` (``-1``)."""

    def __init__(self, side: int = 1, grid=GRID):
        self.side = side
        self.lr1 = np.log(2.0 * grid)  # log LR when the favoured outcome occurs
        self.lr0 = np.log(2.0 * (1.0 - grid))
        self.pi = np.full(len(grid), 1.0 / len(grid))
        self.S = np.zeros(len(grid))
        self.k = 0

    def update(self, z: int) -> float:
        self.k += 1
        w = 1.0 / (self.k * (self.k + 1))
        hit = z if self.side > 0 else 1 - z
        self.S = (self.S + w) * np.exp(self.lr1 if hit else self.lr0)
        return self.value

    @property
    def value(self) -> float:
        return float(self.pi @ self.S)


class QSG:
    def __init__(self, horizon, budget, alpha=0.05, *, rng, alpha_r=0.05, front=True,
                 started=True, rollback=True, monitor=True, reserve=0.0, name="QSG"):  # fmt: skip
        self.name = name
        self.T, self.B, self.alpha, self.alpha_r = horizon, budget, alpha, alpha_r
        self.rng = rng
        self.front, self.started, self.rollback, self.monitor = front, started, rollback, monitor
        self.reserve = int(round(reserve * budget))  # labels kept back from front-loading
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.deployed = 0
        self.cycle = 1
        self.decided = False  # a verdict in the current cycle (promote or discard)
        self.seg = 0  # outcomes issued before seg are ignored (new test after a decision)
        self._new_tests()

    def _new_tests(self):
        mk = (lambda s: StartedMixture(s)) if self.started else (lambda s: _Fixed(s))
        if self.deployed == 0:
            self.e_up, self.e_dn = mk(+1), mk(-1)  # promote / discard
        else:
            self.e_up, self.e_dn = None, mk(-1)  # rollback test

    def predict(self, event):
        return self.deployed

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if not self.decided and self.front and remaining_budget > self.reserve:
            q = 1.0
        elif self.decided and not self.monitor:
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
            z = int(d > 0)
            t = fb.t_released
            if self.deployed == 0:
                up = self.e_up.update(z)
                dn = self.e_dn.update(z)
                if up >= 2.0 ** self.cycle / self.alpha:
                    # a promotion is a verdict: the rollback test runs at the paced monitoring
                    # rate (dev-stage fix 2026-11-03; v0 kept front-loading here and exhausted
                    # the budget before any reversal could be seen)
                    self.deployed, self.decided, self.seg = 1, True, t
                    self._new_tests()
                elif dn >= 1.0 / self.alpha:
                    self.decided = True  # discard: keep incumbent, drop to monitoring rate
            elif self.rollback:
                if self.e_dn.update(z) >= 1.0 / self.alpha_r:
                    self.deployed, self.decided, self.seg = 0, False, t
                    self.cycle += 1
                    self._new_tests()

    def decision_state(self):
        return f"dep={self.deployed};cycle={self.cycle};decided={self.decided}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


class _Fixed(StartedMixture):
    """Ablation: plain (unstarted) mixture likelihood ratio, all mass on start 1."""

    def update(self, z):
        self.k += 1
        if self.k == 1:
            self.S = np.ones_like(self.S)
        hit = z if self.side > 0 else 1 - z
        self.S = self.S * np.exp(self.lr1 if hit else self.lr0)
        return self.value


EXTRA = {
    "QSG": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG")),
    "QSG-no_front": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG"), front=False,
                                                      name="QSG-no_front"),
    "QSG-no_started": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG"), started=False,
                                                        name="QSG-no_started"),
    "QSG-no_rollback": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG"), rollback=False,
                                                         name="QSG-no_rollback"),
    "QSG-r25": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG"), reserve=0.25,
                                                 name="QSG-r25"),
    "QSG-no_monitor": lambda T, B, cs, cq, a, d, r: QSG(T, B, a, rng=r("QSG"), monitor=False,
                                                        name="QSG-no_monitor"),
}


class EnvelopeMixture(StartedMixture):
    """Started mixture against a declared Markov-persistence envelope (Atlas v1 proposal).

    Null class: the disagreement-outcome sign is a Markov chain in event time with stationary
    P(z=1) <= 1/2 (side +1) and persistence <= rho_bar. Given the previous queried outcome and the
    event gap g, ``P(z=1 | past) <= u = 1/2 + rho_bar^g / 2`` after a favourable outcome and
    ``<= 1/2`` otherwise. Each grid component bets only where ``p' > u``, with
    ``LR = (p'/u)^z ((1-p')/(1-u))^(1-z)``, whose conditional mean is <= 1 for any v <= u.
    """

    def __init__(self, side=1, rho_bar=0.8, grid=GRID):
        super().__init__(side, grid)
        self.grid = np.asarray(grid)
        self.rho_bar = rho_bar
        self.prev = None  # (hit, event time)

    def update_at(self, z, t):
        self.k += 1
        w = 1.0 / (self.k * (self.k + 1))
        hit = z if self.side > 0 else 1 - z
        u = 0.5
        if self.prev is not None and self.prev[0] == 1:
            u = 0.5 + 0.5 * self.rho_bar ** max(t - self.prev[1], 1)
        active = self.grid > u
        lr = np.ones_like(self.grid)
        g = self.grid[active]
        lr[active] = (g / u) if hit else ((1.0 - g) / (1.0 - u))
        self.S = (self.S + w) * lr
        self.prev = (hit, t)
        return self.value


class QSGEnvelope(QSG):
    def __init__(self, *a, rho_bar=0.8, **kw):
        self.rho_bar = rho_bar
        super().__init__(*a, **kw)

    def _new_tests(self):
        mk = lambda s: EnvelopeMixture(s, self.rho_bar)  # noqa: E731
        if self.deployed == 0:
            self.e_up, self.e_dn = mk(+1), mk(-1)
        else:
            self.e_up, self.e_dn = None, mk(-1)

    def observe(self, feedback):
        # same as QSG.observe, but passes the issuing event time to the envelope
        for fb in sorted(feedback, key=lambda f: f.event_id):
            if fb.event_id < self.seg:
                continue
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z, t, e = int(d > 0), fb.t_released, fb.event_id
            if self.deployed == 0:
                up = self.e_up.update_at(z, e)
                dn = self.e_dn.update_at(z, e)
                if up >= 2.0 ** self.cycle / self.alpha:
                    self.deployed, self.decided, self.seg = 1, True, t
                    self._new_tests()
                elif dn >= 1.0 / self.alpha:
                    self.decided = True
            elif self.rollback and self.e_dn.update_at(z, e) >= 1.0 / self.alpha_r:
                self.deployed, self.decided, self.seg = 0, False, t
                self.cycle += 1
                self._new_tests()


EXTRA.update({
    "QSG-env8": lambda T, B, cs, cq, a, d, r: QSGEnvelope(T, B, a, rng=r("QSG"), rho_bar=0.8,
                                                          name="QSG-env8"),
    "QSG-env95": lambda T, B, cs, cq, a, d, r: QSGEnvelope(T, B, a, rng=r("QSG"), rho_bar=0.95,
                                                           name="QSG-env95"),
})
