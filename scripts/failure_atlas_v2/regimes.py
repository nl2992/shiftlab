"""Failure Atlas v2 synthetic regimes: paired 0/1 loss streams for two frozen models.

Each regime is a generator of a (T, 2) 0/1 loss array (column 0 incumbent, column 1 challenger)
plus an evaluator-only truth record (the per-event challenger advantage G_t = E[l0 - l1]). The
truth is never passed to a policy: the runner replays losses through the common simulator, so a
policy sees only predictions and, after paying and waiting, labels.

Construction. At event t the models disagree with probability ``dis_t``. On a disagreement the
challenger is the correct one with probability ``p_t`` (so ``D = l0 - l1 = +1``), otherwise the
incumbent is (``D = -1``). On agreement both are right or both wrong (``err_agree``), giving
``D = 0``. Hence ``G_t = dis_t (2 p_t - 1)``. Serial dependence, where requested, is a two-state
Markov chain on the disagreement-outcome sign with stationary probability ``p_t`` and persistence
``rho``; it changes no marginal and so no ``G_t``.

The families mirror Failure Atlas v1 (late/transient improvement, regime change, serial
dependence, delay, near-indistinguishability, rare informative subpopulations) under the v2
contract T=2000, B=200, c_q=.05, c_s=5. Parameters were fixed before any competitor was run on
them; see ``docs/failure_atlas_v2_protocol.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

T = 2000


@dataclass(frozen=True)
class Regime:
    name: str
    family: str
    p: tuple[tuple[int, float], ...]  # piecewise-constant p_t: ((start, p), ...)
    dis: tuple[tuple[int, float], ...] = ((0, 0.2),)
    rho: float = 0.0  # Markov persistence of the disagreement-outcome sign
    burst: float = 0.0  # >0: disagreements arrive in Markov bursts with this persistence
    delay: int = 100
    err_agree: float = 0.1
    notes: str = ""
    tags: tuple[str, ...] = field(default=())

    def schedule(self, horizon: int = T) -> tuple[np.ndarray, np.ndarray]:
        def pw(spec):
            out = np.empty(horizon)
            for i, (s, v) in enumerate(spec):
                e = spec[i + 1][0] if i + 1 < len(spec) else horizon
                out[s:e] = v
            return out

        return pw(self.p), pw(self.dis)

    def truth_gain(self, horizon: int = T) -> np.ndarray:
        p, dis = self.schedule(horizon)
        return dis * (2.0 * p - 1.0)

    def sample(self, rng: np.random.Generator, horizon: int = T) -> np.ndarray:
        p, dis = self.schedule(horizon)
        u = rng.random(horizon)
        if self.burst > 0.0:
            # two-state on/off chain with stationary on-probability dis_t and persistence burst
            on = np.empty(horizon, dtype=bool)
            on[0] = u[0] < dis[0]
            for t in range(1, horizon):
                stay = rng.random() < self.burst
                on[t] = on[t - 1] if stay else (u[t] < dis[t])
        else:
            on = u < dis
        v = rng.random(horizon)
        sign = np.empty(horizon, dtype=bool)  # True => challenger correct on a disagreement
        sign[0] = v[0] < p[0]
        if self.rho > 0.0:
            for t in range(1, horizon):
                keep = rng.random() < self.rho
                sign[t] = sign[t - 1] if keep else (v[t] < p[t])
        else:
            sign = v < p
        both_wrong = rng.random(horizon) < self.err_agree
        # challenger correct on a disagreement <=> incumbent wrong: l0 = 1, l1 = 0, D = +1
        l0 = np.where(on, sign, both_wrong).astype(np.int8)
        l1 = np.where(on, ~sign, both_wrong).astype(np.int8)
        return np.stack([l0, l1], axis=1)


def _r(name, family, p, **kw) -> Regime:
    return Regime(name=name, family=family, p=tuple(p), **kw)


# Locked regime registry. Families F0-F9 follow the v1 failure families; the p values give a
# per-event stationary advantage of .2*(2p-1): p=.65 -> .06, p=.58 -> .032, p=.53 -> .012.
REGIMES: dict[str, Regime] = {
    r.name: r
    for r in [
        # F0: stationary references
        _r("F0_better", "stationary", [(0, 0.65)], tags=("alt",)),
        _r("F0_null", "stationary", [(0, 0.5)], tags=("null",)),
        _r("F0_worse", "stationary", [(0, 0.35)], tags=("null",)),
        # F1: late improvement (challenger worse, then better)
        _r("F1_late_400", "late", [(0, 0.4), (400, 0.68)], tags=("alt", "change")),
        _r("F1_late_800", "late", [(0, 0.4), (800, 0.7)], tags=("alt", "change")),
        _r("F1_late_1200", "late", [(0, 0.4), (1200, 0.75)], tags=("alt", "change")),
        # F2: transient improvement
        _r("F2_transient", "transient", [(0, 0.4), (300, 0.72), (1100, 0.4)], tags=("change",)),
        # F3: abrupt reversal after a genuine early advantage (rollback needed)
        _r("F3_reversal_800", "reversal", [(0, 0.7), (800, 0.3)], tags=("change",)),
        _r("F3_reversal_1200", "reversal", [(0, 0.7), (1200, 0.3)], tags=("change",)),
        # F4: recurrent regimes
        _r(
            "F4_recurrent",
            "recurrent",
            [(0, 0.7), (500, 0.32), (1000, 0.7), (1500, 0.32)],
            tags=("change",),
        ),
        # F5: serial dependence (Markov sign persistence)
        _r("F5_dep_null_r8", "dependence", [(0, 0.5)], rho=0.8, tags=("null", "dep")),
        _r("F5_dep_better_r8", "dependence", [(0, 0.65)], rho=0.8, tags=("alt", "dep")),
        _r("F5_dep_null_r95", "dependence", [(0, 0.5)], rho=0.95, tags=("null", "dep")),
        # F6: long label delay
        _r("F6_delay400_better", "delay", [(0, 0.65)], delay=400, tags=("alt",)),
        _r("F6_delay400_late", "delay", [(0, 0.4), (800, 0.7)], delay=400, tags=("alt", "change")),
        # F7: near-indistinguishable models
        _r("F7_near_better", "near", [(0, 0.58)], tags=("alt",)),
        _r("F7_near_tiny", "near", [(0, 0.53)], tags=("alt",)),
        # F8: rare informative subpopulation (rare disagreements, strong advantage)
        _r("F8_rare_better", "rare", [(0, 0.9)], dis=((0, 0.03),), tags=("alt",)),
        # F9: high-disagreement (budget pressure) and bursty disagreements
        _r("F9_highdis_better", "budget", [(0, 0.58)], dis=((0, 0.5),), tags=("alt",)),
        _r("F9_bursty_better", "budget", [(0, 0.65)], burst=0.95, tags=("alt",)),
    ]
}


# Validation-only neighbours (registered 2026-11-03 before development results were read).
VALIDATION_REGIMES: dict[str, Regime] = {
    r.name: r
    for r in [
        _r("V_late_600_p65", "late", [(0, 0.4), (600, 0.65)], tags=("alt", "change")),
        _r("V_late_1000_p72", "late", [(0, 0.4), (1000, 0.72)], tags=("alt", "change")),
        _r("V_late_1400_p72", "late", [(0, 0.38), (1400, 0.72)], tags=("alt", "change")),
        _r(
            "V_transient_500_1200",
            "transient",
            [(0, 0.4), (500, 0.7), (1200, 0.4)],
            tags=("change",),
        ),
        _r("V_reversal_1000", "reversal", [(0, 0.68), (1000, 0.32)], tags=("change",)),
        _r(
            "V_recurrent_400",
            "recurrent",
            [(0, 0.35), (400, 0.7), (800, 0.35), (1200, 0.7), (1600, 0.35)],
            tags=("change",),
        ),
        _r("V_better_p62", "stationary", [(0, 0.62)], tags=("alt",)),
        _r("V_better_p70", "stationary", [(0, 0.7)], tags=("alt",)),
        _r("V_null", "stationary", [(0, 0.5)], tags=("null",)),
        _r("V_worse_p40", "stationary", [(0, 0.4)], tags=("null",)),
        _r("V_dep_null_r8", "dependence", [(0, 0.5)], rho=0.8, tags=("null", "dep")),
        _r("V_late_1000_d50", "delay", [(0, 0.4), (1000, 0.7)], delay=50, tags=("alt", "change")),
        _r("V_late_1000_d250", "delay", [(0, 0.4), (1000, 0.7)], delay=250, tags=("alt", "change")),
    ]
}


def hindsight_oracle_cost(losses: np.ndarray, cs: float, start: int = 0) -> float:
    """Evaluator-only: minimum cost over all deployment paths given realised losses (DP).

    A hindsight bound, not a feasible policy: it sees every label for free.
    """
    INF = float("inf")
    c = [0.0 if m == start else INF for m in (0, 1)]
    for t in range(losses.shape[0]):
        c = [min(c[m], c[1 - m] + cs) + float(losses[t, m]) for m in (0, 1)]
    return float(min(c))


def expected_oracle_path(gain: np.ndarray, cs: float) -> np.ndarray:
    """Evaluator-only: deployment path minimising EXPECTED cost given true G_t (DP on means)."""
    T_ = len(gain)
    INF = float("inf")
    # cost of model 0 = 0, model 1 = -G_t (relative)
    val = np.zeros((T_ + 1, 2))
    choice = np.zeros((T_, 2), dtype=int)
    for t in range(T_ - 1, -1, -1):
        for m in (0, 1):
            best, arg = INF, m
            for n in (0, 1):
                v = (cs if n != m else 0.0) + (-gain[t] if n == 1 else 0.0) + val[t + 1, n]
                if v < best - 1e-12:
                    best, arg = v, n
            val[t, m], choice[t, m] = best, arg
    path = np.empty(T_, dtype=int)
    m = 0
    for t in range(T_):
        m = choice[t, m]
        path[t] = m
    return path
