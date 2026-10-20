"""Structural integrity checks for replicated experiment reports."""

from collections import Counter
from collections.abc import Iterable, Mapping


def replicate_grid_integrity(
    records: Iterable[Mapping],
    expected_presets: Iterable[str],
    expected_seeds: Iterable[int],
    *,
    preset_field: str = "preset",
    seed_field: str = "seed",
) -> dict:
    """Check that a report has exactly one row for every preset/seed pair."""
    presets = tuple(sorted(set(expected_presets)))
    seeds = tuple(sorted(set(expected_seeds)))
    expected = Counter((preset, seed) for preset in presets for seed in seeds)
    observed = Counter(
        (str(row.get(preset_field)), int(row[seed_field]))
        for row in records
        if preset_field in row and seed_field in row
    )
    missing = sorted(expected - observed)
    duplicates = sorted(pair for pair, count in observed.items() if count > 1)
    unexpected = sorted(pair for pair in observed if pair not in expected)
    return {
        "expected_presets": list(presets),
        "expected_seeds": list(seeds),
        "expected_records": sum(expected.values()),
        "observed_records": sum(observed.values()),
        "missing_pairs": [{"preset": p, "seed": s} for p, s in missing],
        "duplicate_pairs": [{"preset": p, "seed": s} for p, s in duplicates],
        "unexpected_pairs": [{"preset": p, "seed": s} for p, s in unexpected],
        "passes": not missing and not duplicates and not unexpected,
    }
