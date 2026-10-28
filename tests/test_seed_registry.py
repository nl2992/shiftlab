from dataclasses import replace

import pytest

from shiftlab.seed_registry import (
    ALLOCATION_CEILING,
    ALLOCATION_FLOOR,
    Registry,
    SeedBlock,
    allocate,
    find_overlaps,
    load_registry,
    undisclosed_overlaps,
)


def _block(id_: str, start: int, end: int) -> SeedBlock:
    return SeedBlock(id=id_, start=start, end=end, status="development", source="test")


def test_registry_has_no_undisclosed_overlap():
    registry = load_registry()
    bad = [
        f"{a.id} [{a.start}-{a.end}] vs {b.id} [{b.start}-{b.end}] share {lo}-{hi}"
        for a, b, lo, hi in undisclosed_overlaps(registry)
    ]
    assert not bad, "undisclosed seed overlaps:\n" + "\n".join(bad)


def test_disclosures_are_not_stale():
    registry = load_registry()
    ids = {b.id for b in registry.blocks}
    assert len(ids) == len(registry.blocks), "duplicate study ids"
    actual = {frozenset((a.id, b.id)) for a, b, _, _ in find_overlaps(registry.blocks)}
    assert registry.disclosed <= actual, "disclosed pair that no longer overlaps or is unknown"


def test_known_overlaps_are_disclosed():
    registry = load_registry()
    by_id = {b.id: b for b in registry.blocks}
    small, large = by_id["harm_power_grid_30"], by_id["policy_bound_null_calibration_500"]
    assert (small.start, small.end) == (54000000, 54000029)
    assert (large.start, large.end) == (54000000, 54000499)
    assert frozenset((small.id, large.id)) in registry.disclosed
    assert any(b.start == 20290000 for b in registry.blocks)


def test_s2_null_calibration_records_actual_seeds():
    s2 = {b.id: b for b in load_registry().blocks}["gated_wp1_s2_null_calibration"]
    assert (s2.start, s2.end) == (58500000, 58501999)


def test_checker_detects_undisclosed_overlap():
    blocks = (_block("a", 0, 9), _block("b", 9, 20), _block("c", 21, 30))
    registry = Registry(blocks=blocks, disclosed=frozenset())
    found = undisclosed_overlaps(registry)
    assert [(a.id, b.id, lo, hi) for a, b, lo, hi in found] == [("a", "b", 9, 9)]
    registry = replace(registry, disclosed=frozenset({frozenset(("a", "b"))}))
    assert undisclosed_overlaps(registry) == []


def test_allocate_is_fresh_and_aligned():
    registry = load_registry()
    start, end = allocate(2000, registry)
    assert end - start + 1 == 2000
    assert ALLOCATION_FLOOR <= start and end <= ALLOCATION_CEILING
    assert start % 100_000 == 0
    extended = Registry(
        blocks=registry.blocks + (_block("new", start, end),), disclosed=registry.disclosed
    )
    assert undisclosed_overlaps(extended) == []
    start2, _ = allocate(1, extended)
    assert start2 > end


def test_allocate_rejects_empty_block():
    with pytest.raises(ValueError):
        allocate(0, load_registry())
