"""Reference coupling; the screened acquisition candidate is dominated in its contract.

See docs/switching_transport_acquisition_candidate_v1.md. This is neither a complete
switching learner nor a statistical safety certificate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product


def _fraction(value: F | int) -> F:
    if isinstance(value, bool) or not isinstance(value, (F, int)):
        raise ValueError("use exact fractions or integers")  # noqa: TRY004 - Preserve the validation exception contract.
    return F(value)


def _probability(value: F | int) -> F:
    result = _fraction(value)
    if not 0 <= result <= 1:
        raise ValueError("probability must lie in [0,1]")
    return result


def _distribution(values: Sequence[F | int]) -> tuple[F, ...]:
    result = tuple(_probability(value) for value in values)
    if not result or sum(result) != 1:
        raise ValueError("query probabilities must be a nonempty distribution")
    return result


@dataclass(frozen=True)
class QueryStratum:
    probability: F
    old_probability1: F
    # Conditional on this query: masses for (old,new)=(0,0),(0,1),(1,0),(1,1).
    joint: tuple[F, F, F, F]

    def transition_probability1(self, old_action: int) -> F:
        if type(old_action) is not int or old_action not in (0, 1):
            raise ValueError("old action must be integer 0 or 1")
        mass = self.old_probability1 if old_action else 1 - self.old_probability1
        if mass == 0:
            raise ValueError("old action is impossible in this query stratum")
        return self.joint[3 if old_action else 1] / mass


def query_strata(
    prior1: F | int,
    target1: F | int,
    query0: Sequence[F | int],
    query1: Sequence[F | int],
) -> tuple[QueryStratum, ...]:
    """Construct exact conditional transitions; zero-mass query slots are represented."""
    r, p = _probability(prior1), _probability(target1)
    a, b = _distribution(query0), _distribution(query1)
    if len(a) != len(b):
        raise ValueError("query rows must have the same number of slots")
    strata = []
    for aj, bj in zip(a, b, strict=True):
        marginal = (1 - r) * aj + r * bj
        if marginal == 0:
            strata.append(QueryStratum(F(0), F(0), (F(1), F(0), F(0), F(0))))
            continue
        posterior = r * bj / marginal
        joint = (
            min(1 - posterior, 1 - p),
            max(p - posterior, F(0)),
            max(posterior - p, F(0)),
            min(posterior, p),
        )
        strata.append(QueryStratum(marginal, posterior, joint))
    return tuple(strata)


def expected_switches(strata: Sequence[QueryStratum]) -> F:
    return sum((row.probability * (row.joint[1] + row.joint[2]) for row in strata), F(0))


@dataclass(frozen=True)
class TwoSlotChannel:
    query0: tuple[F, F]
    query1: tuple[F, F]
    score: F
    expected_switches: F


def choose_two_slot_channel(
    *,
    prior1: F | int,
    target1: F | int,
    gamma: F | int,
    value0: Sequence[F | int],
    value1: Sequence[F | int],
) -> TwoSlotChannel:
    """Maximize supplied predictable scores without excess expected switches.

    This exact vertex enumeration implements the registered two-slot polytope.
    Scores are not inferred from evaluator truth or claimed to equal continuation value.
    """
    r, p, floor = _probability(prior1), _probability(target1), _probability(gamma)
    if floor == 0:
        raise ValueError("gamma must be positive")
    v0, v1 = tuple(map(_fraction, value0)), tuple(map(_fraction, value1))
    if len(v0) != 2 or len(v1) != 2:
        raise ValueError("exactly two scores per action are required")
    lo, hi = floor / 2, 1 - floor / 2
    coefficient0, coefficient1 = p * (1 - r), (1 - p) * r
    delta = p - r
    candidates = set(product((lo, hi), repeat=2))
    for level in (F(0), delta):
        for edge in (lo, hi):
            if coefficient1:
                candidates.add((edge, (coefficient0 * edge - level) / coefficient1))
            if coefficient0:
                candidates.add(((level + coefficient1 * edge) / coefficient0, edge))

    def valid(x: F, y: F) -> bool:
        z = coefficient0 * x - coefficient1 * y
        return lo <= x <= hi and lo <= y <= hi and min(F(0), delta) <= z <= max(F(0), delta)

    def score(x: F, y: F) -> F:
        return (1 - r) * (x * v0[0] + (1 - x) * v0[1]) + r * (y * v1[0] + (1 - y) * v1[1])

    feasible = [(x, y) for x, y in candidates if valid(x, y)]
    assert feasible  # The uniform channel is feasible; a bounded polytope has a vertex.
    x, y = max(feasible, key=lambda xy: (score(*xy), -abs(xy[0] - xy[1]), xy))
    a, b = (x, 1 - x), (y, 1 - y)
    switching = expected_switches(query_strata(r, p, a, b))
    assert switching == abs(delta)
    return TwoSlotChannel(a, b, score(x, y), switching)
