"""PFA-controlled weighted e-SR baseline from the non-partitioned e-detector construction.

The detector uses a summable prior over possible start labels. Its implementation is an
existing-method comparator, not a ShiftLab contribution.
"""

from __future__ import annotations

import math

import numpy as np
from fam_e import HOSTS, DetectorSwapMonitor


class PFASRDetector:
    """Weighted mixture of one-sided Bernoulli e-processes with PFA control.

    At informative label n, a new process starts with weight
    ``pi_n = 1 / (2 n log(e n)^2)``. The decreasing-series integral test gives
    ``sum_n pi_n <= 1``. Each start-specific product is a nonnegative supermartingale when
    ``E[X_n | past] <= 0``. The sum of active wealth plus unopened prior mass is therefore a
    nonnegative supermartingale starting at at most one; thresholding active wealth at ``1/alpha``
    controls probability of any alarm by alpha. The cap is the maximum number of labels.
    """

    def __init__(
        self, alpha: float, max_labels: int, lambdas: tuple[float, ...] = (0.15, 0.3, 0.5)
    ):
        self.alpha = float(alpha)
        self.max_labels = int(max_labels)
        self.lambdas = np.asarray(lambdas, dtype=float)
        self.weights = np.asarray(
            [0.5 / (n * math.log(math.e * n) ** 2) for n in range(1, self.max_labels + 1)],
            dtype=float,
        )
        self.products = np.zeros((self.max_labels, len(self.lambdas)), dtype=float)
        self.n = 0

    def update(self, x: int) -> bool:
        growth = 1.0 + self.lambdas * int(x)
        if self.n:
            self.products[: self.n] *= growth
        if self.n < self.max_labels:
            self.products[self.n] = growth
            self.n += 1
        stat = float((self.products[: self.n] * self.weights[: self.n, None]).sum(axis=0).mean())
        return stat >= 1.0 / self.alpha


class HeavyTailPFASRDetector(PFASRDetector):
    """Finite-budget PFA mixture that allocates more prior mass to later label starts.

    The q=1.2 power is fixed by the late-start hypothesis. We normalize the finite weight
    vector to the canonical PFA-SR total mass at the same budget, so this changes only the
    allocation over start labels. Since the total mass remains <= 1, the same e-process
    argument applies. This is a candidate prior choice, not a new general guarantee.
    """

    def __init__(self, alpha: float, max_labels: int, q: float = 1.2):
        super().__init__(alpha, max_labels)
        shape = np.asarray(
            [1.0 / (n * math.log(math.e * n) ** q) for n in range(1, self.max_labels + 1)],
            dtype=float,
        )
        self.weights = shape * (self.weights.sum() / shape.sum())


class PFASRMonitor(DetectorSwapMonitor):
    """Use the PFA-weighted SR detector in the existing host/restart wrapper."""

    def __init__(self, make_base, horizon, budget, alpha, *, rng):
        super().__init__(make_base, horizon, budget, alpha, rng=rng, detector="pfa_sr")

    def _new_detector(self):
        if self.deployed == 0:
            alpha = self.alpha_det / (2.0**self.n_promotions)
        else:
            alpha = self.alpha_rb
        return PFASRDetector(alpha, self.B)


class HeavyTailPFASRMonitor(PFASRMonitor):
    """Matched-host wrapper using the preregistered heavier-tailed PFA start prior."""

    def _new_detector(self):
        if self.deployed == 0:
            alpha = self.alpha_det / (2.0**self.n_promotions)
        else:
            alpha = self.alpha_rb
        return HeavyTailPFASRDetector(alpha, self.B)


def _make_pfa_srr(host: str):
    def factory(T, B, cs, cq, alpha, delay, r):
        make_base, _stream_name = HOSTS[host]
        return PFASRMonitor(make_base, T, B, alpha, rng=r(f"pfa_srr_{host}"))

    return factory


def _make_heavy_tail_pfa_srr(host: str):
    def factory(T, B, cs, cq, alpha, delay, r):
        make_base, _stream_name = HOSTS[host]
        return HeavyTailPFASRMonitor(make_base, T, B, alpha, rng=r(f"pfa_tail_{host}"))

    return factory


EXTRA = {f"PFA-SR:{host}": _make_pfa_srr(host) for host in HOSTS}
EXTRA.update({f"PFA-SR:q1.2:{host}": _make_heavy_tail_pfa_srr(host) for host in HOSTS})
