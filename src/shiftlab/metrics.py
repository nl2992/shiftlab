import numpy as np


def mse(y, pred):
    return float(np.mean((np.asarray(y) - np.asarray(pred)) ** 2))


def decision_cost(y, pred, threshold=0.0, fn_cost=5.0, fp_cost=1.0):
    actual = np.asarray(y) >= threshold
    chosen = np.asarray(pred) >= threshold
    return float(np.mean(fn_cost * (actual & ~chosen) + fp_cost * (~actual & chosen)))


def interval_coverage(y, lo, hi):
    return float(np.mean((np.asarray(y) >= lo) & (np.asarray(y) <= hi)))
