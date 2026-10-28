"""Machine-checked registry of experiment seed ranges (readiness-gate task T0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "configs" / "seed_registry.yaml"
ALLOCATION_BOUNDARY = 100_000
# Fresh blocks start above small ad hoc seeds and stay below 2**31 so any int32 or legacy NumPy seed API accepts them.
ALLOCATION_FLOOR = 100_000_000
ALLOCATION_CEILING = 2**31 - 1


@dataclass(frozen=True)
class SeedBlock:
    """One registered study block; ``start`` and ``end`` are inclusive seed ids."""

    id: str
    start: int
    end: int
    status: str
    source: str

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"seed block {self.id} has end {self.end} < start {self.start}")


@dataclass(frozen=True)
class Registry:
    blocks: tuple[SeedBlock, ...]
    disclosed: frozenset[frozenset[str]]


def load_registry(path: Path | str = DEFAULT_REGISTRY_PATH) -> Registry:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    blocks = tuple(
        SeedBlock(
            id=str(s["id"]),
            start=int(s["start"]),
            end=int(s["end"]),
            status=str(s["status"]),
            source=str(s["source"]),
        )
        for s in raw["studies"]
    )
    disclosed = frozenset(frozenset((str(o["a"]), str(o["b"]))) for o in raw["disclosed_overlaps"])
    return Registry(blocks=blocks, disclosed=disclosed)


def find_overlaps(blocks: tuple[SeedBlock, ...]) -> list[tuple[SeedBlock, SeedBlock, int, int]]:
    """Return every pair of blocks sharing at least one seed, with the shared interval."""
    found = []
    for a, b in combinations(blocks, 2):
        lo, hi = max(a.start, b.start), min(a.end, b.end)
        if lo <= hi:
            found.append((a, b, lo, hi))
    return found


def undisclosed_overlaps(registry: Registry) -> list[tuple[SeedBlock, SeedBlock, int, int]]:
    return [
        o
        for o in find_overlaps(registry.blocks)
        if frozenset((o[0].id, o[1].id)) not in registry.disclosed
    ]


def allocate(n: int, registry: Registry | None = None) -> tuple[int, int]:
    """Return the lowest fresh inclusive block of ``n`` seeds that overlaps no registered block.

    The start is a multiple of 100000 at or above ``ALLOCATION_FLOOR`` and the block ends below ``ALLOCATION_CEILING``. Some
    registered entries are wide envelopes of strided seeds, so searching gaps keeps fresh seeds
    in range. The block is not recorded; add it to ``configs/seed_registry.yaml`` before use.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    registry = registry or load_registry()
    start = ALLOCATION_FLOOR
    for block in sorted(registry.blocks, key=lambda b: b.start):
        if block.start > start + n - 1:
            break
        if block.end >= start:
            start = -(-(block.end + 1) // ALLOCATION_BOUNDARY) * ALLOCATION_BOUNDARY
    if start + n - 1 > ALLOCATION_CEILING:
        raise RuntimeError("no fresh aligned block below the allocation ceiling")
    return start, start + n - 1
