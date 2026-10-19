"""Conventional diagnostics; repeated use has no anytime-valid guarantee."""

import numpy as np
from scipy.stats import ks_2samp


def ks_test(reference, current):
    """Bonferroni adjusted marginal KS p-value for independent observations."""
    a, b = np.asarray(reference), np.asarray(current)
    if a.ndim == 1:
        a, b = a[:, None], b[:, None]
    return min(1.0, a.shape[1] * min(ks_2samp(a[:, j], b[:, j]).pvalue for j in range(a.shape[1])))


class CUSUM:
    """One-sided standardized loss CUSUM with user-specified threshold."""

    def __init__(self, mean, scale, threshold=20.0, slack=0.5):
        self.mean, self.scale = mean, max(float(scale), 1e-8)
        self.threshold, self.slack, self.statistic = threshold, slack, 0.0

    def update(self, value):
        self.statistic = max(0.0, self.statistic + (value - self.mean) / self.scale - self.slack)
        alarm = self.statistic > self.threshold
        if alarm:
            self.statistic = 0.0
        return alarm
