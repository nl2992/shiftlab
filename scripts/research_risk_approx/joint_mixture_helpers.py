"""Exact behavioral reconstruction for finite hidden root mixtures."""

from __future__ import annotations

from fractions import Fraction as F

from cut_certificate_helpers import restore_policy
from mixture_incumbent_helpers import realization


def mix_many(game, policies, weights):
    if len(policies) != len(weights) or sum(weights) != 1 or any(w < 0 for w in weights):
        raise ValueError("Invalid mixture")
    flows = [realization(game, policy) for policy in policies]
    mixed = [
        sum((w * flow[j] for w, flow in zip(weights, flows, strict=True)), F(0))
        for j in range(game.learner.count)
    ]
    records = []
    for (history, released), (parent, children, choices) in game.learner.infos.items():
        weights_here = (
            tuple(mixed[child] / mixed[parent] for child in children)
            if mixed[parent]
            else tuple(F(choice == (0, 0)) for choice in choices)
        )
        records.append(
            {
                "history": history,
                "released": released,
                "choices": choices,
                "probabilities": [str(v) for v in weights_here],
            }
        )
    return restore_policy(game, records)
