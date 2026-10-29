"""Exact root-mixture helpers for first-promotion behavioral policies."""

from __future__ import annotations

from fractions import Fraction as F

from cut_certificate_helpers import restore_policy


def never_policy(game):
    return lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))


def component_policy(game, records):
    return never_policy(game) if records is None else restore_policy(game, records)


def realization(game, policy):
    values = [None] * game.learner.count
    values[0] = F(1)
    for (history, released), (parent, children, choices) in game.learner.infos.items():
        if values[parent] is None:
            raise ValueError("Parent sequence not initialized")
        weights = policy(history, released)
        if len(weights) != len(choices) or sum(weights) != 1 or any(x < 0 for x in weights):
            raise ValueError("Invalid component behavior")
        for child, weight in zip(children, weights, strict=True):
            values[child] = values[parent] * weight
    if any(value is None for value in values):
        raise ValueError("Incomplete sequence flow")
    return values


def mixture_policy(game, first, second, weight):
    if not 0 <= weight <= 1:
        raise ValueError("Invalid mixture weight")
    flow1, flow2 = realization(game, first), realization(game, second)
    mixed = [weight * a + (1 - weight) * b for a, b in zip(flow1, flow2, strict=True)]
    records = []
    for (history, released), (parent, children, choices) in game.learner.infos.items():
        if mixed[parent]:
            weights = tuple(mixed[child] / mixed[parent] for child in children)
        else:
            weights = tuple(F(choice == (0, 0)) for choice in choices)
        records.append(
            {
                "history": history,
                "released": released,
                "choices": choices,
                "probabilities": [str(x) for x in weights],
            }
        )
    return restore_policy(game, records)


def candidates_for_pair(a, b, alpha):
    if a["risk"] <= alpha and b["risk"] <= alpha:
        return ((F(1), a["cost"]), (F(0), b["cost"]))
    if a["risk"] > alpha and b["risk"] > alpha:
        return ()
    if a["risk"] == b["risk"]:
        return ()
    weight = (alpha - b["risk"]) / (a["risk"] - b["risk"])
    if not 0 <= weight <= 1:
        return ()
    return ((weight, weight * a["cost"] + (1 - weight) * b["cost"]),)
