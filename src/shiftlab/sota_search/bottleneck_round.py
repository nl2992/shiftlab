"""Round-two compositions targeting observed late-budget and guidance failures."""

from dataclasses import dataclass
from itertools import product

from .combination_screen import Combination


@dataclass(frozen=True)
class PacedCombination(Combination):
    pace: str
    guard: str


def bottleneck_combinations():
    values = []
    for guidance, gamma, cap, allocation, restart, pace in product(
        (0.0, 0.25, 1.0),
        (0.9, 0.98, 0.995),
        (0.5, 0.75),
        ("uniform", "uncertainty", "boundary"),
        (False, True),
        ("remaining", "reserve", "evidence"),
    ):
        for guard in ("off",) if guidance == 0 else ("off", "agreement", "cost_floor"):
            values.append(PacedCombination(guidance, gamma, cap, allocation, restart, pace, guard))
    return values


def effective_config_key(config):
    """Canonicalize a guard that cannot change the convexly blended bet.

    With guidance<=.5, the blend already has >=.5 times the cost-only bet.
    Applying that same lower floor is an exact no-op, not another algorithm.
    Keep original registration entries intact and audit their aliases separately.
    """
    from dataclasses import asdict

    value = asdict(config)
    if config.guard == "cost_floor" and config.guidance <= 0.5:
        value["guard"] = "off"
    return tuple(sorted(value.items()))
