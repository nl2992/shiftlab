"""K-model synthetic environments for budgeted, delayed multi-model replacement (02_ENVIRONMENTS.md).

Each event: label y ~ Bern(.5); optional observable context x in {0, 1} with P(x=1) = pi_t.
Model k is correct with probability a_k(t, x). Correctness is coupled: with probability ``rho``
all models share one uniform draw (comonotone: models of similar accuracy agree), otherwise each
model draws independently. Prediction = y if correct else 1 - y.

Evaluator-side only (never shown to a policy): the accuracy schedule, used for the
expected-loss oracle (DP over K deployment states with switching cost) and ranking metrics.
Model 0 is the incumbent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

T = 2000


@dataclass(frozen=True)
class Env:
    name: str
    acc: tuple  # per model: ((start, acc_x0, acc_x1), ...) piecewise constant
    pi: tuple = ((0, 0.5),)  # P(x=1): ((start, value), ...); "lin" handled by pi_lin
    pi_lin: tuple | None = None  # (p_start, p_end): linear drift of P(x=1) over the horizon
    rho: float = 0.7
    delay: int = 100
    tags: tuple = field(default=())

    @property
    def K(self):
        return len(self.acc)

    def _pw(self, spec, j):
        out = np.empty(T)
        for i, s in enumerate(spec):
            e = spec[i + 1][0] if i + 1 < len(spec) else T
            out[s[0] : e] = s[j]
        return out

    def schedule(self):
        """(a0, a1, pi): accuracy for x=0 and x=1, shape (K, T); pi shape (T,)."""
        a0 = np.stack([self._pw(s, 1) for s in self.acc])
        a1 = np.stack([self._pw(s, 2) for s in self.acc])
        if self.pi_lin is not None:
            pi = np.linspace(self.pi_lin[0], self.pi_lin[1], T)
        else:
            pi = self._pw(self.pi, 1)
        return a0, a1, pi

    def expected_loss(self):
        a0, a1, pi = self.schedule()
        return 1.0 - ((1 - pi) * a0 + pi * a1)  # (K, T)

    def sample(self, rng):
        a0, a1, pi = self.schedule()
        y = (rng.random(T) < 0.5).astype(np.int8)
        x = (rng.random(T) < pi).astype(np.int8)
        a = np.where(x[None, :] == 1, a1, a0)  # (K, T)
        common = rng.random(T) < self.rho
        u_c = rng.random(T)
        u_i = rng.random((self.K, T))
        u = np.where(common[None, :], u_c[None, :], u_i)
        correct = u < a
        preds = np.where(correct, y[None, :], 1 - y[None, :]).T.astype(np.int8)  # (T, K)
        return preds, y, x


def oracle_cost(el, cs, start=0):
    """Expected-loss oracle: min over deployment paths of sum el + cs * switches (start at 0)."""
    K, n = el.shape
    v = np.full(K, cs)
    v[start] = 0.0
    v = v + el[:, 0]
    for t in range(1, n):
        best = v.min()
        v = np.minimum(v, best + cs) + el[:, t]
    return float(v.min())


def _c(a):  # constant model, same accuracy on both contexts
    return ((0, a, a),)


def _ch(*segs):  # piecewise in time, same accuracy on both contexts
    return tuple((s, a, a) for s, a in segs)


ENVS = {
    e.name: e
    for e in [
        Env("E1_persist", (_c(0.70), _c(0.76), _c(0.72)), tags=("alt",)),
        Env("E2_late", (_c(0.72), _ch((0, 0.66), (800, 0.80)), _c(0.70)), tags=("change",)),
        Env("E3_reversal", (_c(0.70), _ch((0, 0.78), (1000, 0.62)), _c(0.74)), tags=("change",)),
        Env(
            "E4_specialist",
            (((0, 0.70, 0.70),), ((0, 0.82, 0.60),), ((0, 0.60, 0.82),)),
            pi_lin=(0.15, 0.85),
            tags=("change", "context"),
        ),
        Env("E5_ambiguous", (_c(0.70), _c(0.725), _c(0.73)), tags=("alt",)),
        Env("E6_null", (_c(0.72), _c(0.72), _c(0.72)), tags=("null",)),
        Env("E6_worse", (_c(0.72), _c(0.68), _c(0.66)), tags=("null",)),
        # K=5 variants
        Env(
            "E2_late_K5",
            (_c(0.72), _ch((0, 0.66), (800, 0.80)), _c(0.70), _c(0.71), _c(0.69)),
            tags=("change", "K5"),
        ),
        Env(
            "E5_ambiguous_K5",
            (_c(0.70), _c(0.725), _c(0.73), _c(0.72), _c(0.715)),
            tags=("alt", "K5"),
        ),
        Env("E6_null_K5", tuple(_c(0.72) for _ in range(5)), tags=("null", "K5")),
    ]
}
