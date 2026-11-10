"""Small exact helpers for the Paper 4 counterexample library.

Nothing here is a new method.  The helpers are shared by
``tests/paper4/test_counterexample_library.py``; the tests check every helper against an
independent hand-derived value or a second computation that does not call this module.

* Boolean-event utilities on complete binary label tapes: the causal-null value recursion
  ``v(h) = max{v(h0), (v(h0) + v(h1)) / 2}``, the fair-IID value, and residual-subfunction
  (reduced-OBDD level width) counts for an arbitrary variable order.
* ``behavior_policy`` / ``deterministic_policy``: build a ``Policy`` for a
  ``CausalSwitchingGame`` from a function of the learner's own information
  ``(history, released outcomes)``.  A choice that is not in ``game.choices(history)``
  (for instance a query with zero remaining budget) raises ``ValueError``; such a policy cannot
  be expressed.
* ``alias_example``: the exact label tapes of the alternative-belief aliasing example.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction as F
from itertools import product

Tape = tuple[int, ...]
Event = set[Tape] | frozenset[Tape]

HALF = F(1, 2)


# --------------------------------------------------------------------------------------
# Boolean events on complete tapes
# --------------------------------------------------------------------------------------
def all_tapes(horizon: int) -> tuple[Tape, ...]:
    return tuple(product((0, 1), repeat=horizon))


def causal_risk(horizon: int, event: Event) -> F:
    """Exact ``sup`` over causal nulls (``p_t in [0, 1/2]`` after any prefix) of ``P(tape in event)``."""

    def value(prefix: Tape) -> F:
        if len(prefix) == horizon:
            return F(prefix in event)
        zero, one = value(prefix + (0,)), value(prefix + (1,))
        return max(zero, (zero + one) / 2)

    return value(())


def iid_risk(horizon: int, event: Event) -> F:
    """Fair-coin probability of the event."""
    return F(sum(tape in event for tape in all_tapes(horizon)), 2**horizon)


def residual_counts(
    function: Callable[[Tape], bool], horizon: int, order: Sequence[int]
) -> list[int]:
    """Distinct residual subfunctions after fixing the first ``k`` variables of ``order``.

    Entry ``k`` is the number of distinct truth tables over the remaining variables
    (taken in ``order``) as the first ``k`` variables range over all assignments.  This is the
    level width of the reduced OBDD for ``order`` (Myhill-Nerode classes of the event).
    """
    if sorted(order) != list(range(horizon)):
        raise ValueError("order must be a permutation of the variables")
    counts = []
    for k in range(horizon + 1):
        fixed, free = order[:k], order[k:]
        tables = set()
        for assignment in product((0, 1), repeat=k):
            table = []
            for rest in product((0, 1), repeat=horizon - k):
                tape = [0] * horizon
                for var, bit in zip(fixed, assignment, strict=True):
                    tape[var] = bit
                for var, bit in zip(free, rest, strict=True):
                    tape[var] = bit
                table.append(bool(function(tuple(tape))))
            tables.add(tuple(table))
        counts.append(len(tables))
    return counts


# --------------------------------------------------------------------------------------
# Policies for CausalSwitchingGame
# --------------------------------------------------------------------------------------
def behavior_policy(game, chooser: Callable[[tuple, tuple], Mapping[tuple[int, int], F]]):
    """Policy from ``chooser(history, released) -> {choice: probability}``.

    The chooser sees only ``game.information(history, outcomes)``, so pending outcomes are
    hidden.  Mass on a choice outside ``game.choices(history)`` raises ``ValueError``.
    """

    def policy(history, outcomes):
        _, released = game.information(history, outcomes)
        legal = game.choices(history)
        distribution = dict(chooser(history, released))
        illegal = [c for c, m in distribution.items() if m and c not in legal]
        if illegal:
            raise ValueError(f"illegal choice(s) {illegal}; legal choices are {legal}")
        weights = tuple(F(distribution.get(choice, 0)) for choice in legal)
        if sum(weights) != 1:
            raise ValueError("behavior probabilities must sum to one")
        return weights

    return policy


def deterministic_policy(game, chooser: Callable[[tuple, tuple], tuple[int, int]]):
    return behavior_policy(game, lambda history, released: {chooser(history, released): F(1)})


# --------------------------------------------------------------------------------------
# Alternative-belief aliasing (docs/switching_alt_belief_risk_alias_counterexample_v1.md)
# --------------------------------------------------------------------------------------
def alias_example(prior_state0: F = F(9, 10)) -> dict[Tape, tuple[F, F]]:
    """Joint alternative law of ``(Y1, Y2)`` and the posterior ``P(S_3 = 0 | tape)``.

    Hidden state ``S_1 = 0`` w.p. ``prior_state0``; ``S_2 = S_3 = 0`` surely; ``Y_t = 1{S_t = 0}``.
    Returns ``{tape: (probability, posterior of S_3 = 0)}`` for tapes of positive probability,
    by explicit enumeration of ``(S_1, S_2, S_3)``.
    """
    mass: dict[Tape, F] = {}
    state0: dict[Tape, F] = {}
    for s1 in (0, 1):
        weight = prior_state0 if s1 == 0 else 1 - prior_state0
        s2 = s3 = 0
        tape = (int(s1 == 0), int(s2 == 0))
        mass[tape] = mass.get(tape, F(0)) + weight
        state0[tape] = state0.get(tape, F(0)) + weight * (s3 == 0)
    return {tape: (m, state0[tape] / m) for tape, m in mass.items() if m}
