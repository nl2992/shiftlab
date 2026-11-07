"""Ports of two comparators found elsewhere in the repository (GAVE-R WP3 follow-up).

E_rb (certified rollback of the Recovery Monitor)
    Source: remote branch ``origin/codex/sprint2-leaderboards`` @ 297a706e,
    ``scripts/sota_sprint/fam_b.py`` (``GridMixtureDetector``, ``host_detector``,
    ``RecoveryMonitor`` with ``rollback=True``, ``_switch``) wrapped by
    ``scripts/sota_sprint/fam_e.py`` (``_rb``; variants ``-a05``).
    Ported logic: after a promotion the rollback detector is a restart-mixture SR e-detector
    (product started before every ``gap``-th label, ``ceil(m/gap)`` starts with equal prior mass,
    bets lambda in (.15,.3,.5), total prior mass one) at ``alpha_rb = .10`` on the signed outcome
    x (+ = incumbent better), with ``m = max(budget left at promotion, 20)``; it alarms when
    ``stat >= 1/alpha_rb``; a rollback is vetoed (and testing stops) when fewer than
    ``h_min = ceil(c_s / g_ref)`` rounds remain; re-promotions spend halving shares (the
    promotion alpha of episode j is alpha * 2^-(j+1), as in the repository gate).
    Adaptations (my choices, not the source's): (1) the source works on event streams with label-clock
    disagreement outcomes x in {-1,+1}; here x = D in [-1,1] for requested rounds, which keeps
    x <= 1 so ``1 + lambda x`` stays a nonnegative factor and the null is ``E[D | past] <= 0``
    (challenger not worse than the incumbent). (2) acquisition is this module's credit pacing (no
    reserve), not the source's RMM pacer. (3) the source's promotion host (a gated certificate
    stop) is replaced by the repository started-mixture promotion gate used by every method here.
    (4) ``g_ref`` is set to ``h`` (0.1), giving ``h_min = ceil(s / h)``; with s = 0.1 this is 1 round,
    so the horizon gate is essentially inactive here (the source's c_s = 5 gives 50).
    No economic gate (faithful: the source has none).

Two-phase persistence promotion
    Source: ``src/shiftlab/dive/persistence_promotion.py`` (``_two_phase_decisions``,
    ``PersistencePromotionConfig``): intersection-union of one e-process in a fixed discovery window
    and a second e-process in a disjoint fixed persistence window; promote only on both.
    Adaptation: the source splits an offline shadow window at a prespecified fraction. Online there is
    no fixed shadow window, so phase 2 starts at the (stopping-time) round at which the phase-1
    e-process alarms and uses a fresh e-process on labels with event round >= that round; promotion
    needs the phase-2 alarm (plus the repository economic check). Each phase is run at the full
    promotion level (intersection-union keeps the promotion level at that level). It has no
    rollback (the source is a promotion gate only).
"""

from __future__ import annotations

import math

import numpy as np

from shiftlab.dive.switching_explore import started_gate
from shiftlab.gaver.freshcheck import FreshCheckMethod

HOST_LAMBDAS = (0.15, 0.3, 0.5)


class GridMixtureDetector:
    """Restart-mixture SR e-detector (single component of the source's GridMixtureDetector)."""

    def __init__(self, alpha: float, gap: int, n_starts: int, lambdas=HOST_LAMBDAS):
        self.alpha, self.gap, self.ns = float(alpha), int(gap), max(1, int(n_starts))
        self.lams = np.asarray(lambdas, float)
        self.sr = np.zeros(len(self.lams))
        self.n = 0

    def update(self, x: float) -> bool:
        if self.n % self.gap == 0 and self.n // self.gap < self.ns:
            self.sr += 1.0 / self.ns
        self.sr *= 1.0 + self.lams * x
        self.n += 1
        return self.stat >= 1.0 / self.alpha

    @property
    def stat(self) -> float:
        return float(self.sr.mean())


class ErbMethod(FreshCheckMethod):
    def __init__(self, alpha_rb: float = 0.10, gap: int = 10, g_ref: float | None = None):
        super().__init__("ext", 0.0, alpha_rb=alpha_rb)
        self.gap, self.g_ref = gap, g_ref
        self.name = f"erb_a{alpha_rb:g}"

    def _ext_promote(self, t: int) -> None:
        m = max(self.cfg.B - self.used, 20)
        self.det = GridMixtureDetector(self.alpha_rb, self.gap, math.ceil(m / self.gap))
        self.det_alarm = False
        self.vetoed = False

    def _ext_feed(self, x: float) -> None:
        if not self.vetoed and self.det.update(x):
            self.det_alarm = True
            self.stat_trigger_ever = 1

    def _ext_rollback(self, t: int) -> bool:
        if not self.det_alarm:
            return False
        g = self.cfg.h if self.g_ref is None else self.g_ref
        h_min = math.ceil(self.cfg.s / g)
        if self.cfg.T - t < h_min:
            self.vetoed, self.det_alarm = True, False  # too late to repay the switch cost
            return False
        return True


class TwoPhaseMethod(FreshCheckMethod):
    """Promotion needs a phase-1 alarm and then a fresh phase-2 alarm; no rollback."""

    def __init__(self):
        super().__init__("none", 0.0)
        self.name = "two_phase"

    def _init(self) -> None:
        super()._init()
        self.phase, self.ph2_start, self.ep2 = 1, 0, None

    def _promo_feed(self, ev: int, x: float) -> None:
        self.ep_labels.append(x)
        if self.phase == 1:
            self.ep.update(x)
        elif ev >= self.ph2_start:
            self.ep2.update(-x - self.cfg.h)

    def _promo_alarm(self, t: int) -> bool:
        if self.phase == 1 and self.ep.alarm:
            self.phase, self.ph2_start = 2, t
            self.ep2 = started_gate(1.0 + self.cfg.h, self._alpha_j(self.j), self.cfg.B)
            return False
        return self.phase == 2 and bool(self.ep2.alarm)


def make(name: str):
    if name == "erb":
        return ErbMethod(0.10)
    if name == "erb_a05":
        return ErbMethod(0.05)
    if name == "two_phase":
        return TwoPhaseMethod()
    raise KeyError(name)
