"""Artificial research utilities, never asserted to be application ground truth."""

import numpy as np


def binary_action(probability, false_negative=5.0, false_positive=1.0):
    if np.any(np.asarray(false_negative) <= 0) or np.any(np.asarray(false_positive) <= 0):
        raise ValueError("Costs must be positive")
    return np.asarray(probability) >= np.asarray(false_positive) / (
        np.asarray(false_positive) + false_negative
    )


def binary_risk(action, probability, false_negative=5.0, false_positive=1.0):
    return np.where(
        action,
        false_positive * (1 - np.asarray(probability)),
        false_negative * np.asarray(probability),
    )


def capacity_allocation(probabilities, capacity: int):
    if not 0 <= capacity <= len(probabilities):
        raise ValueError("Capacity outside [0,n]")
    result = np.zeros(len(probabilities), dtype=bool)
    if capacity:
        result[np.argsort(probabilities)[-capacity:]] = True
    return result


def selective_action(probabilities, abstention_cost=0.2):
    p = np.asarray(probabilities)
    action = (p >= 0.5).astype(int)
    return np.where(np.minimum(p, 1 - p) > abstention_cost, -1, action)
