"""Extra baseline used by the frozen EIA F8 synthetic follow-up."""

from controls import FixedModel


def _fixed_challenger(T, budget, cs, cq, alpha, delay, rng):
    del T, budget, cs, cq, alpha, delay, rng
    return FixedModel(1, name="fixed_challenger")


EXTRA = {"fixed_challenger": _fixed_challenger}
