# PORTED UNCHANGED -- WP1e, d2a_rar branch. RMM detector + pacers only (NOT the RestartMixtureMonitor wrapper).
# Source A: origin/codex/sprint2-leaderboards@a2dd04a1 path scripts/failure_atlas_v2/restart_monitor.py (last changed 3fa468f7): HorizonWeightedPacer, MixtureSRDetector (verbatim).
# Source B: origin/codex/sprint2-leaderboards@a2dd04a1 path scripts/promising_directions/sota/competitors/controls.py (last changed 5a714add): PacedDisagreementAcquisition (verbatim).
# Not ported: RestartMixtureMonitor/_View (need the sprint simulator Event/QueryRequest types and certificate-host base policies).
"""RMM building blocks (restart-mixture SR e-detector and horizon-weighted pacer)."""

from __future__ import annotations

import math

import numpy as np


class PacedDisagreementAcquisition:
    """Budget-paced, disagreement-gated querying with a positive propensity floor.

    This is the acquisition every control shares. It is the same functional form as the P3b
    pacer: spend the remaining budget evenly over the expected remaining disagreement events,
    floored at `p_min` so every eligible event keeps positive propensity.
    """

    def __init__(
        self,
        horizon: int,
        budget: int,
        p_min: float = 0.05,
        prior_rate: float = 0.25,
        prior_w: float = 20.0,
    ):
        self.T, self.B, self.p_min = int(horizon), int(budget), float(p_min)
        self.prior_rate, self.prior_w = float(prior_rate), float(prior_w)
        self.n_disagree = 0

    def propensity(self, t: int, remaining: int, disagree: bool) -> float:
        if not disagree or remaining <= 0:
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        expected_left = max(rate * (self.T - t), 1e-9)
        return float(min(max(remaining / expected_left, self.p_min), 1.0))

    def note_event(self, disagree: bool) -> None:
        self.n_disagree += int(disagree)


class HorizonWeightedPacer(PacedDisagreementAcquisition):
    """Spend density proportional to (T - t)^(k - 1): q_t = k * remaining / (rate * (T - t)).

    k = 1 is the shared uniform pacer; k = 2 spends in proportion to the remaining horizon, i.e.
    to the number of future events a decision made now will govern.
    """

    def __init__(self, horizon, budget, p_min=0.05, k: float = 2.0):
        super().__init__(horizon, budget, p_min=p_min)
        self.k = float(k)

    def propensity(self, t, remaining, disagree):
        if not disagree or remaining <= 0:
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        expected_left = max(rate * (self.T - t), 1e-9)
        return float(min(max(self.k * remaining / expected_left, self.p_min), 1.0))


class MixtureSRDetector:
    """Weighted Shiryaev-Roberts e-detector over a finite start grid; total prior mass one."""

    def __init__(
        self,
        alpha: float,
        max_labels: int,
        gap: int = 10,
        lambdas: tuple[float, ...] = (0.15, 0.3, 0.5),
        single_start: bool = False,
        w_first: float | None = None,
    ):
        self.alpha = float(alpha)
        self.gap = int(gap)
        self.n_starts = 1 if single_start else max(1, int(math.ceil(max_labels / self.gap)))  # noqa: RUF046 (ported verbatim)
        # prior mass of each start; total one. w_first puts extra mass on the first start.
        if self.n_starts == 1:
            self.pis = [1.0]
        elif w_first is None:
            self.pis = [1.0 / self.n_starts] * self.n_starts
        else:
            rest = (1.0 - w_first) / (self.n_starts - 1)
            self.pis = [float(w_first)] + [rest] * (self.n_starts - 1)
        self.lams = np.asarray(lambdas, float)
        self.sr = np.zeros(len(self.lams))
        self.n = 0

    def update(self, x: int) -> bool:
        if self.n % self.gap == 0 and self.n // self.gap < self.n_starts:
            self.sr += self.pis[self.n // self.gap]  # a start enters before its first label
        self.sr *= 1.0 + self.lams * x
        self.n += 1
        return self.stat >= 1.0 / self.alpha

    @property
    def stat(self) -> float:
        return float(self.sr.mean())
