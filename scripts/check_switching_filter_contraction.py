"""Exhaustively verify the registered two-state HMM filter contraction bound."""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product


def update(probability1: F, outcome: int | None) -> F:
    """Predict one symmetric-HMM step, then optionally condition on its binary label."""
    predicted = F(1, 4) + probability1 / 2
    if outcome is None:
        return predicted
    emission0 = F(1, 20) if outcome else F(19, 20)
    emission1 = F(19, 20) if outcome else F(1, 20)
    normalizer = (1 - predicted) * emission0 + predicted * emission1
    return predicted * emission1 / normalizer


def verify(max_length: int = 8) -> list[tuple[int, F, F, int]]:
    """Check every missing/zero/one string against the uniform 2**(-k) bound."""
    rows = []
    for length in range(1, max_length + 1):
        worst = F(0)
        for observations in product((None, 0, 1), repeat=length):
            left, right = F(0), F(1)
            for outcome in observations:
                left = update(left, outcome)
                right = update(right, outcome)
            worst = max(worst, abs(right - left))
        bound = F(1, 2**length)
        if worst > bound:
            raise AssertionError(f"length {length}: {worst} exceeds {bound}")
        rows.append((length, worst, bound, 3**length))
    return rows


if __name__ == "__main__":
    for length, worst, bound, sequence_count in verify():
        print(f"k={length} worst={worst} bound={bound} sequences={sequence_count} status=passed")
