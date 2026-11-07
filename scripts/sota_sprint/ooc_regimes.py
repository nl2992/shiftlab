"""Out-of-class null regimes (Amendment 2, reviewer objection O2). Registered before any validation row
was read. Marginal P(challenger right on a disagreement) = 1/2 in both, so they are marginal nulls, but
the sign process is NOT a first-order homogeneous Markov chain, i.e. outside A1/A5b's declared class.
Results on them are descriptive (they test robustness to misspecification, not the guarantee).

* O_null_semimarkov: sign runs in event time with discrete Pareto run lengths (tail index 1.5, min 1);
  each run's sign is a fresh fair coin.
* O_null_order2: s_t copies s_{t-1} w.p. .45, s_{t-2} w.p. .4, else a fresh fair coin.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bench import SPRINT_REGIMES


@dataclass(frozen=True)
class OOCNull:
    name: str
    kind: str
    dis: float = 0.25
    delay: int = 100
    err_agree: float = 0.1
    tags: tuple = ("null", "dep", "out_of_class")
    family: str = "out_of_class"

    def truth_gain(self, horizon: int = 2000) -> np.ndarray:
        return np.zeros(horizon)

    def sample(self, rng: np.random.Generator, horizon: int = 2000) -> np.ndarray:
        on = rng.random(horizon) < self.dis
        sign = np.empty(horizon, dtype=bool)
        if self.kind == "semimarkov":
            t = 0
            while t < horizon:
                run = int(np.floor(rng.pareto(1.5) + 1.0))
                sign[t:t + run] = rng.random() < 0.5
                t += run
        else:
            sign[:2] = rng.random(2) < 0.5
            for t in range(2, horizon):
                u = rng.random()
                sign[t] = sign[t - 1] if u < 0.45 else (sign[t - 2] if u < 0.85 else rng.random() < 0.5)
        both_wrong = rng.random(horizon) < self.err_agree
        l0 = np.where(on, sign, both_wrong).astype(np.int8)
        l1 = np.where(on, ~sign, both_wrong).astype(np.int8)
        return np.stack([l0, l1], axis=1)


OOC = {r.name: r for r in [OOCNull("O_null_semimarkov", "semimarkov"),
                           OOCNull("O_null_order2", "order2")]}
SPRINT_REGIMES.update(OOC)
