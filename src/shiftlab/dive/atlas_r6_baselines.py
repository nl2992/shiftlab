"""R6 literature baselines for the Failure Atlas (Amendment 2, item 2).

Four :class:`~shiftlab.dive.switching_explore.Method` adaptations of recent close methods. Each is
an *adaptation* to the harness contract (paired difference ``D`` revealed at ``t + d`` only if
queried, hard request-time budget ``B``, query cost ``c``, switch cost ``s``), not a reproduction;
the source guarantees (regret bounds) do not transfer. Departures are listed in ``R6_METHODS``.

All methods are predictable: ``decide`` uses only labels released by round ``t`` and the method's
own past queries (seeded private RNG). Nothing here is a novelty or efficacy claim.
"""

from __future__ import annotations

import math

import numpy as np

from shiftlab.dive.switching_explore import (
    Config,
    Method,
    Released,
    started_gate,
    uniform_calendar,
)


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


class _PacedIW(Method):
    """Bernoulli-paced querying; remembers q_t of every queried round for importance weighting."""

    rng_tag = 0

    def _init_pacing(self) -> None:
        self.rng = np.random.default_rng([self.cfg.seed, 6006, self.rng_tag])
        self.q_at: dict[int, float] = {}

    def _pace_query(self, t: int) -> bool:
        c = self.cfg
        rem = c.B - self.used
        span = c.T - c.d - t + 1  # queryable rounds left (t + d <= T)
        if rem <= 0 or span <= 0:
            return False
        q = min(1.0, rem / span)
        if self.rng.random() < q:
            self.q_at[t] = q  # q_t fixed before the draw; the draw is independent of D
            return True
        return False


class GongZhangPaidObs(_PacedIW):
    """Paid-observation controller with free-observation allowance, delayed wrapper.

    Importance-weighted discounted estimate of the per-round benefit ``-D`` (released labels only);
    the switching penalty enters the action choice: switch only if the estimated gain over the
    remaining horizon exceeds ``s``.
    """

    name = "gong_zhang_paid_obs"
    rng_tag = 1

    def _init(self) -> None:
        c = self.cfg
        self._init_pacing()
        self.gamma = 1.0 - 1.0 / max(c.d + 1, c.T / 5.0)
        self.act = 0
        self.num: list[tuple[int, float]] = []  # (event, -D / q_event)

    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        c = self.cfg
        for ev, x in released:
            self.num.append((ev, -x / self.q_at[ev]))
        if len(self.num) >= 3:
            g = self.gamma
            s_hat = sum(v * g ** (t - ev) for ev, v in self.num)
            last = t - c.d  # rounds whose labels could have been released by t
            den = (1.0 - g**last) / (1.0 - g) if last > 0 else 1.0
            ben = s_hat / den  # estimated discounted mean benefit of action 1 over action 0
            gain_left = (c.T - t + 1) * ben
            if self.act == 0 and gain_left > c.s:
                self.act = 1
            elif self.act == 1 and -gain_left > c.s:
                self.act = 0
        return self.act, self._pace_query(t)


class QiuDelayedMovement(_PacedIW):
    """Blocked (lazy) fixed-share Hedge, importance-weighted over a paced query schedule.

    The action may change only at block boundaries (block >= d + 1 mimics the delayed-gradient
    aggregation + movement-cost reduction). Fixed share targets dynamic regret against a
    switching comparator with ~sqrt(N) switches; the step size follows the sqrt(K/N) rate scaled
    by the block length.
    """

    name = "qiu_delayed_movement"
    rng_tag = 2

    def _init(self) -> None:
        c = self.cfg
        self._init_pacing()
        self.L = max(c.d + 1, math.ceil(c.T / 20))
        n_blocks = math.ceil(c.T / self.L)
        k_sw = max(1.0, math.sqrt(n_blocks))
        self.eta = 3.0 * math.sqrt(k_sw / n_blocks) / self.L
        self.share = min(0.5, k_sw / n_blocks)
        self.z = 0.0  # log-odds of action 1
        self.buf = 0.0
        self.act = 0

    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        for ev, x in released:
            self.buf += x / self.q_at[ev]  # estimated loss difference (action 1 minus action 0)
        if (t - 1) % self.L == 0:
            self.z = float(np.clip(self.z - self.eta * self.buf, -30, 30))
            self.buf = 0.0
            p = _sigmoid(self.z)
            p = (1.0 - self.share) * p + self.share / 2.0
            self.z = math.log(p / (1.0 - p))
            self.act = int(p > 0.5)
        return self.act, self._pace_query(t)


class RyabchenkoCapacity(Method):
    """Fixed-delay batch-representative scheduling, block length ``b = ceil(T/B)``.

    One query at a uniformly random round of each block (its representative). Delayed Hedge on the
    representative scores, updated at block starts from labels released so far, with a single
    coupled deployment uniform per run (as ``DelayedBudgetHedge``). Mapping: ``D`` becomes losses
    ``loss0=(1-D)/2``, ``loss1=(1+D)/2`` in [0,1], so ``loss0-loss1 = -D`` is the
    ``DelayedBudgetHedge`` score. DelayedBudgetHedge is re-implemented here because the harness
    needs ``T`` not divisible by ``b`` and request-time refusals for ``t + d > T``.
    """

    name = "ryabchenko_capacity"

    def _init(self) -> None:
        c = self.cfg
        self.rng = np.random.default_rng([c.seed, 6006, 3])
        self.b = max(1, math.ceil(c.T / max(c.B, 1)))
        self.n_blocks = math.ceil(c.T / self.b)
        self.u = float(self.rng.random())
        delay_blocks = math.ceil(c.d / self.b)
        self.eta = math.sqrt(8.0 * math.log(2.0) / self.n_blocks) / math.sqrt(1.0 + delay_blocks)
        self.score = 0.0
        self.ready = 0.0
        self.act = 0
        self.qt = -1

    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        for _ev, x in released:
            self.ready += -x
        if (t - 1) % self.b == 0:
            self.score += self.ready
            self.ready = 0.0
            self.act = int(self.u < _sigmoid(self.eta * self.score))
            size = min(self.b, self.cfg.T - t + 1)
            self.qt = t + int(self.rng.integers(size))
        return self.act, (t == self.qt and self.cfg.B > 0)


class OnlineFWERSpending(Method):
    """Repeated promotion tests with online alpha spending + fallback (Tian-Ramdas), gated.

    Episode ``j`` tests the boundary null ``E[-D] <= h`` with a started-mixture e-process at level
    ``alpha_j = alpha * gamma_j + (alpha_{j-1} if episode j-1 rejected)``,
    ``gamma_j = 1/((j+1)(j+2))`` (sums to 1, so ``alpha_j <= alpha``). Promotion needs rejection
    and ``econ_ok``. Rollback by window mean as in ``EpisodeComposition``; an ended episode had
    been rejected (promotion requires it), so its level is carried forward.
    """

    name = "online_fwer_spending"

    @staticmethod
    def _gamma(j: int) -> float:
        return 1.0 / ((j + 1) * (j + 2))

    def _new_episode(self, j: int, start: int, carry: float) -> None:
        self.j, self.ep_start = j, start
        self.level = self.cfg.alpha * self._gamma(j) + carry
        self.ep = started_gate(1 + self.cfg.h, self.level, self.cfg.B)
        self.ep_labels: list[float] = []

    def _init(self) -> None:
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.m = max(3, c.B // 8)
        self.act = 0
        self.promo_t = 0
        self.post: list[float] = []
        self._new_episode(0, 0, 0.0)

    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        c = self.cfg
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start:
                    self.ep.update(-x - c.h)
                    self.ep_labels.append(x)
            elif ev >= self.promo_t:
                self.post.append(x)
        if self.act == 0:
            if self.ep.alarm and self.ep_labels:
                ben = -float(np.mean(self.ep_labels[-10:]))
                if self.econ_ok(t, ben):
                    self.act, self.promo_t, self.post = 1, t, []
        elif len(self.post) >= 3 and -float(np.mean(self.post[-self.m :])) <= c.h:
            self.act = 0
            self._new_episode(self.j + 1, t, self.level)  # rejected -> carry level forward
        return self.act, t in self.cal


R6_METHODS: dict[str, tuple] = {
    "gong_zhang_paid_obs": (
        lambda cfg: GongZhangPaidObs(),
        False,
        (
            "Gong-Zhang ICML26 paid observations + free allowance. Departures: source is contextual "
            "bandit regret with per-action loss subsets and immediate feedback; here one paired D, "
            "delayed, hard budget B as the free allowance (query cost c only charged by the harness, "
            "not traded off in the controller), pacing q=B_rem/queryable-rounds-left, discounted IW "
            "estimate, switch-penalty threshold s on remaining-horizon gain. No false-promotion "
            "guarantee (regret only); no regret guarantee claimed for this adaptation."
        ),
    ),
    "qiu_delayed_movement": (
        lambda cfg: QiuDelayedMovement(),
        False,
        (
            "Qiu et al. ICML26 delayed dynamic regret with movement cost. Departures: source is "
            "parameter-free unconstrained OCO with full gradients; here a 2-expert blocked fixed-share "
            "Hedge (block max(d+1,T/20), fixed share ~sqrt(N)/N, hand-set step) with IW estimates over "
            "a Bernoulli-paced query schedule (no hard-budget handling in the source). Guarantee is "
            "dynamic regret, not false-promotion; not parameter-free here."
        ),
    ),
    "ryabchenko_capacity": (
        lambda cfg: RyabchenkoCapacity(),
        False,
        (
            "Ryabchenko et al. COLT25 capacity-constrained delay scheduling. Departures: source "
            "bounds concurrent tracked rounds (capacity frees on arrival), here a total query budget "
            "B sets b=ceil(T/B), one random representative query per block, delayed Hedge on "
            "D mapped to losses (1-D)/2,(1+D)/2 (as DelayedBudgetHedge), oblivious-adversary regret "
            "only; no paid-query choice, switching cost or false-promotion control."
        ),
    ),
    "online_fwer_spending": (
        lambda cfg: OnlineFWERSpending(),
        True,
        (
            "Tian-Ramdas online FWER (alpha spending + fallback). Departures: the per-promotion "
            "test is the repo started-mixture e-process on -D-h (not the source's p-values); episodes "
            "overlap in data dependence so only the arbitrary-dependence Bonferroni/fallback argument "
            "applies and its composition with delayed adaptive sampling is NOT proved here (audit "
            "caveat); ADDIS not included; gamma_j=1/((j+1)(j+2)); econ_ok and window-mean rollback "
            "are ours, not the source's."
        ),
    ),
}


def build_r6(name: str, cfg: Config | None = None) -> Method:
    """Instantiate an R6 method (``cfg`` accepted for factory symmetry; ``start`` binds it)."""
    if name not in R6_METHODS:
        raise ValueError(f"unknown R6 method {name}")
    return R6_METHODS[name][0](cfg)


__all__ = [
    "R6_METHODS",
    "GongZhangPaidObs",
    "OnlineFWERSpending",
    "QiuDelayedMovement",
    "RyabchenkoCapacity",
    "build_r6",
]
